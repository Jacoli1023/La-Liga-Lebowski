from datetime import date
from typing import List, Dict, Optional
from collections import defaultdict
import random

from config.settings import LEAGUE_SETTINGS
from src.models.team import Team
from src.models.player import Player

class League:
    """Manages the overall La Liga Lebowski league state and operations"""

    def __init__(self, season_year: int = None):
        self.season_year = season_year or date.today().year
        self.teams: List[Team] = []
        self.free_agents: List[Player] = []
        self.current_salary_cap = LEAGUE_SETTINGS['salary_cap']

        # League calendar state
        # TODO: add more phases according to the La Liga calendar
        self.current_phase = "offseason" # offseason, regular_season, playoffs
        self.current_week = 0

        # Draft and auction state
        self.rookie_draft_order: List[Team] = []
        self.auction_nomination_order: List[Team] = []

        # Season tracking
        self.season_stats: Dict[str, Dict] = defaultdict(dict)
        self.playoff_teams: List[Team] = []


    def add_team(self, team: Team):
        """Add a team to the league"""
        if len(self.teams) >= LEAGUE_SETTINGS['teams']:
            raise ValueError(f"League is full ({LEAGUE_SETTINGS['teams']} teams max)")

        team.salary_cap = self.current_salary_cap
        self.teams.append(team)


    def advance_season(self):
        """Advance to next season, handling all offseason tasks"""
        print(f"Advancing from {self.season_year} to {self.season_year + 1}!")

        # 1. Advance all player contracts
        self._advance_all_contracts()

        # 2. Increase salary cap by 5%
        self.current_salary_cap *= LEAGUE_SETTINGS['salary_cap_increase_rate']
        for team in self.teams:
            team.salary_cap = self.current_salary_cap

        # 3. Process holdouts
        self._process_holdouts()

        # 4. Handle expired contracts
        self._handle_expired_contracts()

        # 5. Validate team salary caps
        self._validate_salary_caps()

        # 6. Set up draft order
        self._determine_rookie_draft_order()

        # TODO: open bidding for franchise players, unrestricted free agent auction/blind bidding, contract extension deadline, trading deadline, practice squad activation deadline, salary cap removal


    def _advance_all_contracts(self):
        """Advance all player contracts by one year"""
        for team in self.teams:
            for roster_list in team.roster.values():
                for player in roster_list:
                    if player.contract:
                        player.advance_contract_year()


    def _process_holdouts(self):
        """Identify and process potential holdouts"""
        # Calculate position averages for top performers
        # TODO: Simplify this process by just scraping all this info from the sleeper API
        position_averages = self._calculate_position_averages()

        for team in self.teams:
            holdout_players = []
            for roster_list in team.roster.values():
                for player in roster_list:
                    # idk if this is right
                    if player.check_holdout_eligibility(self.season_stats):
                        pos_avg = position_averages.get(player.position, 0)
                        demands = player.calculate_holdout_demands(pos_avg)
                        if demands:
                            holdout_players.append(player)

            if holdout_players:
                print(f"{team.name} has {len(holdout_players)} potential holdouts")


    def _calculate_position_averages(self) -> Dict[str, float]:
        """Calculate average salaries for top performers at each position"""
        # TODO: this can also be simplified using the sleeper API
        position_averages = {}
        # TODO: Put this into the LEAGUE_SETTINGS config file
        thresholds = {"QB": 5, "TE": 5, "RB": 10, "WR": 15}

        for position, threshold in thresholds.items():
            top_players = []
            for team in self.teams:
                for roster_list in team.roster.values():
                    players = [p for p in roster_list
                               if p.position == position and p.contract]
                    top_players.extend(players)

            # Sory by fantasy points and take top performers
            top_players.sort(key=lambda p: p.fantasy_points, reverse=True)
            top_salaries = [p.contract.current_salary
                            for p in top_players[:threshold]
                            if p.contract]

            if top_salaries:
                position_averages[position] = sum(top_salaries) / len(top_salaries)

        return position_averages


    def _handle_expired_contracts(self):
        """Move players with expired contracts to free agency"""
        for team in self.teams:
            expired_players = []
            for roster_list in team.roster.values():
                for player in roster_list:
                    if player.contract and player.contract.years_remaining <= 0:
                        expired_players.append(player)

            for player in expired_players:
                team.remove_player(player)
                self.free_agents.append(player)


    def _validate_salary_caps(self):
        """Ensure all teams are under the salary cap (March 1st deadline)"""
        violations = []
        for team in self.teams:
            if team.get_total_salary_used() > team.salary_cap:
                violations.append(team)

        if violations:
            print(f"Salary cap violations: {[t.name for t in violations]}")

        return violations


    def _determine_rookie_draft_order(self):
        """Determine rookie draft order using weighted lottery system"""
        # TODO: Move this function into a rookie draft service
        # Sort teams by record (worst to best)
        sorted_teams = sorted(self.teams, key=lambda t: getattr(t, 'wins', 0))

        # Lottery for first 6 picks
        lottery_teams = sorted_teams[:6]
        lottery_balls = [30, 22, 18, 14, 10, 6] # ping pong balls per team

        lottery_order = []
        remaining_teams = lottery_teams.copy()
        remaining_balls = lottery_balls.copy()

        for pick in range(6):
            total_balls = sum(remaining_balls)
            winning_number = random.randint(1, total_balls)

            cumulative = 0
            for i, balls in enumerate(remaining_balls):
                cumulative += balls
                if winning_number <= cumulative:
                    lottery_order.append(remaining_teams[i])
                    remaining_teams.pop(i)
                    remaining_balls.pop(i)
                    break

        # Remaining picks by inverse standings (reigning champ picks last)
        remaining_picks = sorted_teams[6:]
        if len(remaining_picks) >= 2:
            # Champion picks last, runner-up second to last
            champion = remaining_picks[-1]
            runner_up = remaining_picks[-2] if len(remaining_picks) > 1 else None
            middle_teams = remaining_picks[:-2] if len(remaining_picks) > 2 else []

            final_order = middle_teams +([runner_up] if runner_up else []) + [champion]
        else:
            final_order = remaining_picks

        self.rookie_draft_order = lottery_order + final_order
        self.auction_nomination_order = self.rookie_draft_order.copy()


    def get_team_by_name(self, name: str) -> Optional[Team]:
        """Find team by name"""
        for team in self.teams:
            if team.name == name:
                return team
        return None


    def get_free_agents_by_position(self, position: str) -> List[Player]:
        """Get all free agents at a specific position"""
        return [p for p in self.free_agents if p.position == position]


    def get_league_stats(self) -> Dict:
        """Get current league statistics"""
        return {
                'season_year': self.season_year,
                'salary_cap': self.current_salary_cap,
                'total_teams': len(self.teams),
                'free_agents': len(self.free_agents),
                'current_phase': self.current_phase,
                'draft_order': [t.name for t in self.rookie_draft_order]
        }


    def simulate_season_stats(self):
        """Placeholder for simulating season performance"""
        for team in self.teams:
            for roster_list in team.roster.values():
                for player in roster_list:
                    # Simulate fantasy points based on position
                    if player.position == "QB":
                        player.fantasy_points = random.uniform(150, 400)
                    elif player.position in ["RB", "WR"]:
                        player.fantasy_points = random.uniform(50, 300)
                    elif player.position == "TE":
                        player.fantasy_points = random.uniform(30, 200)
                    else:
                        player.fantasy_points = random.uniform(0, 150)
