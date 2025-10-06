from config.settings import VALID_POSITIONS, NFL_TEAMS, SALARY_MULTIPLIERS
from typing import Optional, Dict, Any

class Player:
    def __init__(self, name: str, nfl_team: str, position:str, 
                 rank: Optional[int] = None, 
                 contract: Optional['Contract'] = None):

        # Input validation
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Player name cannot be empty")
        if position not in VALID_POSITIONS: 
            raise ValueError(f"Invalid position: {position}. Must be one of {VALID_POSITIONS}")
        if nfl_team not in NFL_TEAMS: 
            raise ValueError(f"Invalid NFL team: {nfl_team}. Must be one of {NFL_TEAMS}")

        # Basic info
        self.name = name.strip()
        self.position = position
        self.nfl_team = nfl_team
        self.rank = rank

        # Contract and team info
        self.contract = contract
        self.fantasy_team = None
        self.roster_status = "free_agent" # active, practice_squad, IR

        # Performance tracking for holdouts
        self.season_stats: Dict[str, Any] = {}
        self.fantasy_points = 0.0
        self.position_rank_end_of_season = None

        # Status flags
        self.is_holdout = False
        self.holdout_demands: Optional[float] = None
        self.is_retired = False


    def __repr__(self):
        contract_info = f", ${self.get_current_salary():.2f}" if self.contract else ""
        return f"{self.name} ({self.position} - {self.nfl_team}{contract_info})"


    def is_available(self) -> bool:
        """Check if player is available as free agent"""
        return self.roster_status == "free_agent" and not (self.is_retired or self.contract)


    def get_current_salary(self) -> float:
        """Get player's current salary"""
        return self.contract.current_salary if self.contract else 0.0


    def get_effective_salary(self) -> float:
        """Get salary counting against cap based on roster status"""
        if not self.contract:
            return 0.0

        base_salary = self.contract.current_salary
        multiplier = SALARY_MULTIPLIERS.get(self.roster_status, 1.00)
        return base_salary * multiplier


    def set_contract(self, contract: 'Contract'):
        """Assign a contract to this player"""
        self.contract = contract


    def advance_contract_year(self):
        """Advance player's contract by one year"""
        if self.contract:
            self.contract.advance_year()
            if self.contract.years_remaining <= 0:
                self._become_free_agent()


    def _become_free_agent(self):
        """Convert player to free agent status"""
        self.contract = None
        self.fantasy_team = None
        self.roster_status = "free_agent"
        self.is_holdout = False
        self.holdout_demands = None


    def check_holdout_eligibility(self, position_rankings: Dict[str, list]) -> bool:
        """Check if player is eligible for holdout based on performance"""
        if not self.contract or self.contract.is_expiring():
            return False

        # Define top performer thresholds by position
        thresholds = {"QB": 5, "TE": 5, "RB": 10, "WR": 15, "K": 0, "D/ST": 0}
        threshold = thresholds.get(self.position, 0)

        if threshold == 0:
            return False

        # Check if player finished in top group for their position
        position_top_performers = position_rankings.get(self.position, [])
        return len(position_top_performers) >= threshold and self in position_top_performers[:threshold]


    def calculate_holdout_demands(self, position_avg_salary: float) -> Optional[float]:
        """Calculate holdout contract demands"""
        if not self.contract:
            return None

        if self.contract.current_salary >= (position_avg_salary * 0.5):
            return None

        self.holdout_demands = position_avg_salary * 0.75
        self.is_holdout = True
        return self.holdout_demands


    def resolve_holdout(self, decision: str) -> float:
        """Resolve holdout with team decision

        Args:
            decision: 'accept', 'release', or 'reject'

        Returns:
            Salary change (positive for increase, negative for cap savings)
        """
        if not self.is_holdout or not self.holdout_demands:
            raise ValueError("Player is not currently holding out")

        old_salary = self.contract.current_salary

        if decision == 'accept':
            # Accept demands, bump salary to 75% of top position average
            self.contract.current_salary = self.holdout_demands
            self.is_holdout = False
            self.holdout_demands = None
            return self.contract.current_salary - old_salary

        elif decision == 'release':
            # Release player, they become free agent
            dead_money = self.contract.calculate_dead_money_penalty()
            self._become_free_agent()
            return dead_money # This will be added as dead money to team

        elif decision == 'reject':
            # Reject demands, player goes to practice squad
            if self.roster_status != 'practice_squad':
                self.roster_status = 'practice_squad'
            return 0.0 # No immediate salary change, but effective salary changes

        else:
            raise ValueError("Decision must be 'accept', 'release', or 'reject'")


    def retire(self):
        """Retire player from NFL"""
        self.is_retired = True
        self.roster_status = 'retired'


    def unretire(self):
        """Un-retire player (Brett Favre)"""
        if self.is_retired:
            self.is_retired = False
            if self.contract and self.fantasy_team:
                self.roster_status = 'active'
            else:
                self.roster_status = 'free_agent'


    def is_eligible_for_practice_squad(self) -> bool:
        """Check if player can be placed on practice squad"""
        # Only rookies can go on practice squad initially
        # OR holdout players can be placed there
        return (self.contract and self.contract.is_rookie) or self.is_holdout


    def can_be_extended(self) -> bool:
        """Check if player's contract can be extended"""
        return self.contract and self.contract.is_eligible_for_extension()


    def extend_contract(self, years: int) -> float:
        """Extend player's contract"""
        if not self.can_be_extended():
            raise ValueError(f"Cannot extend contract for {self.name}")
        return self.contract.extend_contract(years)
