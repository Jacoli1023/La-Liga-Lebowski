"""
Test suite for La Liga Lebowski models
Run with: python -m pytest tests/test_models.py -v
"""

import pytest
from src.models.player import Player
from src.models.team import Team
from src.models.league import League
from src.models.contract import Contract

class TestContract:
    """Test Contract model functionality"""

    def test_contract_creation(self):
        contract = Contract("Test Player", 50.0, 3, is_rookie=False)
        assert contract.player_name == "Test Player"
        assert contract.initial_salary == 50.0
        assert contract.current_salary == 50.0
        assert contract.years_remaining == 3
        assert not contract.is_rookie
        assert not contract.has_been_extended

    def test_advance_year(self):
        contract = Contract("Test Player", 50.0, 3)
        original_salary = contract.current_salary

        contract.advance_year()

        # Salary should increase by 20%
        assert contract.years_remaining == 2
        assert contract.current_salary == original_salary * 1.20

    def test_contract_extension(self):
        contract = Contract("Test Player", 50.0, 3)

        salary_increase = contract.extend_contract(2)

        # Should apply 20% raise with $10 salary minimum
        expected_new_salary = max(50.0 * 1.20, 10.0)
        assert contract.current_salary == expected_new_salary
        assert contract.years_remaining == 5 # 3 + 2
        assert contract.has_been_extended
        assert salary_increase == expected_new_salary - 50.0

    def test_extension_with_minimum_salary(self):
        """Test extension with low salary player receiving minimum"""
        contract = Contract("Cheap Player", 5.0, 3)

        contract.extend_contract(1)

        # Should be bumped to $10 minimum, not $6 (5 * 1.20)
        assert contract.current_salary == 10.0

    def test_extension_restrictions(self):
        """Test various extension restrictions"""
        # Cannot extend twice
        contract = Contract("Test Player", 50.0, 3)
        contract.extend_contract(1)

        with pytest.raises(ValueError, match="already been extended"):
            contract.extend_contract(1)

        # Cannot extend with 1 year remaining
        contract2 = Contract("Test Player", 50.0, 1)
        with pytest.raises(ValueError, match="1 or fewer years"):
            contract2.extend_contract(1)

    def test_dead_money_calculation(self):
        """Test dead money penalties"""
        contract = Contract("Test Player", 100.0, 4)

        # 4 years remaining = 100% penalty
        assert contract.calculate_dead_money_penalty() == 100.0

        contract.advance_year() # Now 3 years, $120 salary
        assert contract.calculate_dead_money_penalty() == 90.0 # 75% penalty

        contract.advance_year() # Now 2 years, $144 salary
        assert contract.calculate_dead_money_penalty() == 72.0 # 50% penalty

        contract.advance_year() # Now 1 year
        assert contract.calculate_dead_money_penalty() == 0.0 # No penalty

    def test_franchise_tag_calculation(self):
        contract = Contract("Test Player", 80.0, 1)

        # Should be higher of position average or 120% of current
        position_avg = 100.0
        # max(100, 96) = 100
        expected = max(position_avg, contract.current_salary * 1.20)
        assert contract.get_franchise_tag_minimum(position_avg) == expected

        # Test when 120% of current is higher
        position_avg = 80.0
        # max(80, 96) = 96
        expected = max(position_avg, contract.current_salary * 1.20) 
        assert contract.get_franchise_tag_minimum(position_avg) == expected
    
    def test_contract_expiration(self):
        contract = Contract("Test Player", 50.0, 2)
        assert not contract.is_expiring()

        contract.advance_year() # Now expiring
        assert contract.is_expiring()

        contract.advance_year() # Now expired
        with pytest.raises(ValueError, match="already expired"):
            contract.advance_year()


class TestPlayer:
    """Test Player model functionality"""

    def test_player_creation(self):
        player = Player("Josh Allen", "BUF", "QB", rank=1)
        assert player.name == "Josh Allen"
        assert player.nfl_team == "BUF"
        assert player.position == "QB"
        assert player.rank == 1
        assert player.is_available()
        assert player.get_current_salary() == 0.0

    def test_player_validation(self):
        """Test input validation"""
        with pytest.raises(ValueError, match="Player name cannot be empty"):
            Player("", "BUF", "QB")

        with pytest.raises(ValueError, match="Invalid position"):
            Player("Test", "BUF", "INVALID")

        with pytest.raises(ValueError, match="Invalid NFL team"):
            Player("Test", "INVALID", "QB")

    def test_player_with_contract(self):
        contract = Contract("Josh Allen", 200.0, 4)
        player = Player("Josh Allen", "BUF", "QB", contract=contract)

        assert player.get_current_salary() == 200.0
        assert player.is_available() # Has contract, but not assigned team

    def test_holdout_calculation(self):
        """Test holdout demand calculations"""
        contract = Contract("Test RB", 20.0, 3)
        player = Player("Test RB", "KC", "RB", contract=contract)

        # Postion average $100, player makes $20 (< 50% of avg)
        demands = player.calculate_holdout_demands(100.0)

        assert player.is_holdout
        assert demands == 75.0 # 75% of position average
        assert player.holdout_demands == 75.0

    def test_no_holdout_if_well_paid(self):
        """Test that well-paid players don't hold out"""
        contract = Contract("Well Paid RB", 60.0, 3)
        player = Player("Well Paid RB", "KC", "RB", contract=contract)

        # Position average $100, player makes $60 (>= 50% of avg)
        demands = player.calculate_holdout_demands(100.0)

        assert demands is None
        assert not player.is_holdout

    def test_holdout_resolution_accept(self):
        """Test accepting holdout demands"""
        contract = Contract("Test RB", 20.0, 3)
        player = Player("Test RB", "KC", "RB", contract=contract)
        player.calculate_holdout_demands(100.0) # Sets holdout status

        salary_change = player.resolve_holdout("accept")

        assert not player.is_holdout
        assert player.holdout_demands is None
        assert player.contract.current_salary == 75.0
        assert salary_change == 55.0 # 75 - 20

    def test_holdout_resolution_reject(self):
        """Test rejecting holdout demands"""
        contract = Contract("Test RB", 20.0, 3)
        player = Player("Test RB", "KC", "RB", contract=contract)
        player.calculate_holdout_demands(100.0)
        player.roster_status = "active"
        
        salary_change = player.resolve_holdout("reject")

        assert player.is_holdout # Still holding out
        assert player.roster_status == "practice_squad"
        assert salary_change == 0.0

    def test_retirement(self):
        """Test player retirement mechanics"""
        contract = Contract("Old Player", 50.0, 2)
        player = Player("Old Player", "NE", "QB", contract=contract)

        player.retire()

        assert player.is_retired
        assert player.roster_status == "retired"

        # Test unretirement
        player.unretire()
        assert not player.is_retired
        assert player.roster_status == "free_agent" # No team assigned


class TestTeam:
    """Test Team model functionality"""

    def test_team_creation(self):
        team = Team("Test Team", draft_position=1)
        assert team.name == "Test Team"
        assert team.draft_position == 1
        assert team.salary_cap == 1006 # From LEAGUE_SETTINGS
        assert team.get_total_salary_used() == 0.0

    def test_add_player(self):
        team = Team("Test Team")
        contract = Contract("Test Player", 50.0, 3)
        player = Player("Test Player", "KC", "RB", contract=contract)

        team.add_player(player)

        assert player.fantasy_team == team.name
        assert player.roster_status == "active"
        assert len(team.roster['active']) == 1
        assert player in team.roster['active']

    def test_add_unavailable_player(self):
        """Test that unavailable players cannot be added"""
        team = Team("Test Team")
        contract = Contract("Test Player", 50.0, 3)
        player = Player("Test Player", "KC", "RB", contract=contract)
        player.roster_status = "active" # Make unavailable

        with pytest.raises(ValueError, match="is not available"):
            team.add_player(player)

    def test_remove_player(self):
        """Test removing players and dead money"""
        team = Team("Test Team")
        contract = Contract("Test Player", 50.0, 4)
        player = Player("Test Player", "KC", "RB", contract=contract)

        team.add_player(player)
        original_dead_money = team.dead_money

        team.remove_player(player)

        assert player.is_available()
        assert player.fantasy_team is None
        assert len(team.roster['active']) == 0
        assert team.dead_money == original_dead_money + 50.0 # Player's salary

    def test_salary_calculations(self):
        """Test salary cap calculations"""
        team = Team("Test Team")

        # Add active player
        contract1 = Contract("Active Player", 100.0, 3)
        player1 = Player("Active Player", "KC", "RB", contract=contract1)
        team.add_player(player1, 'active')

        # Add practice squad player
        contract2 = Contract("PS Player", 40.0, 3, is_rookie=True)
        player2 = Player("PS Player", "DEN", "WR", contract=contract2)
        team.add_player(player2, 'practice_squad')

        # Active: $100 * 1.0 = $100
        # PS: $40 * 0.25 = $10
        expected_total = 100.0 + 10.0
        assert team.get_total_salary_used() == expected_total
        assert team.get_remaining_cap() == team.salary_cap - expected_total

    def test_roster_limits(self):
        """Test roster size limits"""
        team = Team("Test Team")

        # Try to exceed active roster limit (26 players)
        for i in range(27):
            contract = Contract(f"Player {i}", 10.0, 1)
            player = Player(f"Player {i}", "KC", "RB", contract=contract)

            if i < 26:
                team.add_player(player)
            else:
                with pytest.raises(ValueError, match="roster is full"):
                    team.add_player(player)


class TestLeague:
    """Test League model functionalit"""
    
    def test_league_creation(self):
        league = League(2025)
        assert league.season_year == 2025
        assert len(league.teams) == 0
        assert league.current_salary_cap == 1006

    def test_add_teams(self):
        league = League(2025)

        for i in range(12): # Max teams
            team = Team(f"Team {i+1}")
            league.add_team(team)

        assert len(league.teams) == 12

        # Try to add 13th team
        with pytest.raises(ValueError, match="League is full"):
            league.add_team(Team("Team 13"))

    def test_season_advancement(self):
        """Test advancing to next season"""
        league = League(2025)

        # Add team with player
        team = Team("Test Team")
        contract = Contract("Test Player", 100.0, 3)
        player = Player("Test Player", "KC", "RB", contract=contract)
        team.add_player(player)
        league.add_team(team)

        original_cap = league.current_salary_cap
        original_salary = player.contract.current_salary

        for i in range(11): # Add rest teams, for lottery validation
            team = Team(f"Team {i+1}")
            league.add_team(team)

        league.advance_season()

        # Check season advancement
        assert league.season_year == 2026
        assert league.current_salary_cap == original_cap * 1.05 # 5% increase
        assert player.contract.current_salary == original_salary * 1.20 # 20% increase
        assert player.contract.years_remaining == 2 # Decreased by 1

    def test_expired_contracts(self):
        """Test handling of expired contracts"""
        league = League(2025)
        team = Team("Test Team")

        # Create player with 1-year contract
        contract = Contract("Expiring Player", 50.0, 1)
        player = Player("Expiring Player", "KC", "RB", contract=contract)
        team.add_player(player)
        league.add_team(team)

        for i in range(11): # Add rest teams, for lottery validation
            team = Team(f"Team {i+1}")
            league.add_team(team)

        league.advance_season()

        # Player should become free agent
        assert player.is_available()
        assert player in league.free_agents
        assert len(team.roster['active']) == 0

    def test_draft_order_generation(self):
        """Test rookie draft order generation"""
        league = League(2025)

        # Add 12 teams
        for i in range(12):
            team = Team(f"Team {i+1}")
            team.wins = i # Simulate different records
            league.add_team(team)

        league._determine_rookie_draft_order()

        assert len(league.rookie_draft_order) == 12
        # First 6 should be from lottery (worst records)
        # Last should be champion (best record)
        assert league.rookie_draft_order[-1].wins == 11 # Highest wins


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
