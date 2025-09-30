from datetime import date
from typing import List, Dict, Optional
from collections import defaultdict

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
        pass
