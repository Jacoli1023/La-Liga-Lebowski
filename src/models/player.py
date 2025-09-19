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
        return self.roster_status == "free_agent" and not self.is_retired


    def get_current_salary(self) -> float:
        """Get player's current salary"""
        return self.contract.current_salary if self.contract else 0.0


    def get_effective_salary(self):
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
        self.is_holdout = false
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
        return len(position_top_performers >= threshold and self in position_top_performers[:threshold])


    def calculate_holdout_demands(self, position_avg_salary: float) -> Optional[float]:
        """Calculate holdout contract demands"""
        if not self.contract:
            return None
        
