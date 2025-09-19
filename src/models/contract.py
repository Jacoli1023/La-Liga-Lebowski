from datetime import date
from typing import Optional
from config.settings import LEAGUE_SETTINGS

class Contract:
    """Represents a player's contract with salary, duration, and cap implications"""

    def __init__(self, player_name: str, initial_salary: float, years: int, is_rookie: bool = False, start_year: int = None):
        self.player_name = player_name
        self.initial_salary = initial_salary
        self.total_years = years
        self.years_remaining = years
        self.is_rookie = is_rookie
        self.start_year = start_year or date.today().year
        self.current_salary = initial_salary
        self.has_been_extended = False
        self.is_franchise_tagged = False
        self.is_transition_tagged = False


    def advance_year(self):
        """Advance contract by one year, applying salary increases"""
        if self.years_remaining <= 0:
            raise ValueError("Contract has already expired")

        self.years_remaining -= 1
        if self.years_remaining > 0:
            # 20% salary increase each year per league rules
            self.current_salary *= LEAGUE_SETTINGS['player_salary_increase_rate']


    def extend_contract(self, additional_years: int) -> float:
        """Extend contract, applying immediate 20% raise and $10 minimum"""
        if self.has_been_extended:
            raise ValueError("Player has already been extended once")
        if self.years_remaining <= 1:
            raise ValueError("Cannot extend player with 1 or fewer years remaining")
        if not (1 <= additional_years <= 5):
            raise ValueError("Extension must be between 1-5 years")

        # Apply immediate 20% raise and $10 minimum per league rules
        old_salary = self.current_salary
        self.current_salary = max(self.current_salary * 1.20, 10)
        self.years_remaining += additional_years
        self.total_years += additional_years
        self.has_been_extended = True

        return self.current_salary - old_salary  # Return salary increase


    def calculate_dead_money_penalty(self) -> float:
        """Calculate dead money penalty for dropping player"""
        if self.years_remaining <= 1:
            return 0.0

        # Dead money penalties based on years remaining
        penalty_multipliers = {
                2: 0.50,
                3: 0.75,
                4: 1.00,
                5: 1.25
        }

        multiplier = penalty_multipliers.get(self.years_remaining, 1.25)
        return self.current_salary * multiplier


    def is_eligible_for_extension(self) -> bool:
        """Check if player is eligible for contract extension"""
        return (not self.has_been_extended and
                self.years_remaining > 1 and
                not self.is_franchise_tagged and
                not self.is_transition_tagged)


    def is_expiring(self) -> bool:
        """Check if contract expires after this season"""
        return self.years_remaining <= 1


    def get_franchise_tag_minimum(self, position_avg_salary: float) -> float:
        """Calculate minimum bid for franchise tag"""
        return max(position_avg_salary, self.current_salary * 1.20)


    def get_transition_tag_salary(self, position_avg_salary: float) -> float:
        """Calculate salary for transition tag"""
        return max(position_avg_salary, self.current_salary * 1.20)


    def __repr__(self):
        return f"Contract({self.player_name}: ${self.current_salary:.2f}, {self.years_remaining}yr remaining)"
