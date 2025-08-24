from config.settings import VALID_POSITIONS

class Player:
    def __init__(self, name, nfl_team, position, rank=None, salary=None):
        # Basic type checking
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        if not name or not name.strip():
            raise ValueError("Player name cannot be empty")
        if position is not None and position not in ["QB", "RB", "WR", "TE", "K", "D/ST"]:
            raise ValueError(f"Invalid position: {position}")

        # Rudimentary salary error handling
        if salary is not None:
            if not isinstance(salary, (int, float)):
                raise TypeError("Salary must be a number")
            elif salary < 0:
                raise ValueError("Salary cannot be negative")

        # Basic info
        self.name = name.strip()
        self.position = position
        self.nfl_team = nfl_team
        self.rank = rank

        # Contract info
        # TODO: Add logic for initializing a player with a salary
        #       (who owns them, contract duration, etc.)
        self.salary = salary if salary is not None else 0
        self.contract_years_remaining = 0
        self.contract_start_year = None
        self.is_rookie = False

        # Status tracking
        self.fantasy_team = None
        self.roster_status = "free_agent" # active, practice_squad, IR
        self.is_holdout = False

        # Stats for scoring/holdout calculation
        self.season_stats = {}
        self.fantasy_points = 0


    def __repr__(self):
        return f"{self.name} ({self.position} - {self.nfl_team})"


    def is_available(self):
        return self.roster_status == "free_agent"


    def get_effective_salary(self):
        multiplier = 1.00
        if self.roster_status == "practice_squad":
            multiplier = 0.25
        elif self.roster_status == "IR":
            multiplier = 0.5
        return self.salary * multiplier
