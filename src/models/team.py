from config.settings import LEAGUE_SETTINGS
from src.models.player import Player
from typing import List, Dict, Optional

class Team:
    def __init__(self, name: str, draft_position: Optional[int] = None):
        self.name = name
        self.draft_position = draft_position
        self.salary_cap = LEAGUE_SETTINGS['salary_cap']
        self.dead_money = 0.0

        self.roster = {
                'active': [],
                'practice_squad': [],
                'IR': []
        }

        # Track team performance (for rookie draft order and standings)
        self.wins = 0
        self.losses = 0


    def add_player(self, player: Player, roster_type: str = 'active'):
        """Add contracted player to the roster"""
        self._validate_player_addition(player, roster_type)

        # All validations passed - add player and update status
        self.roster[roster_type].append(player)
        player.roster_status = roster_type
        player.fantasy_team = self.name


    def remove_player(self, player: Player):
        """Remove player and handle dead money penalties"""
        if player.fantasy_team != self.name:
            raise ValueError(f"Cannot remove player: {player.name} is not part of your team!")

        # Find and remove player from roster
        for roster_list in self.roster.values():
            if player in roster_list:
                roster_list.remove(player)
                break
        else:
            raise ValueError(f"Cannot remove player: {player.name} not found in roster!")

        # Handle dead money penalty if player has contract
        if player.contract:
            penalty = player.contract.calculate_dead_money_penalty()
            self.dead_money += penalty

        # Reset player status
        player._become_free_agent()


    def move_player(self, player: Player, new_roster_type: str):
        """Move player between roster types (active, PS, IR)"""
        if player.fantasy_team != self.name:
            raise ValueError(f"Cannot move player: {player.name} not on your team!")

        current_roster_type = player.roster_status

        # Validate roster move
        if current_roster_type == new_roster_type:
            raise ValueError(f"Player {player.name} is already on {new_roster_type} roster")

        if self._get_roster_size(new_roster_type) >= self._get_roster_max(new_roster_type):
            raise ValueError(f"Cannot move player: {new_roster_type} is full")

        # Special PS validation
        if new_roster_type == 'practice_squad' and not player.is_eligible_for_practice_squad():
            raise ValueError(f"{player.name} not eligible for practice squad")

        # Execute the move
        self.roster[current_roster_type].remove(player)
        self.roster[new_roster_type].append(player)
        player.roster_status = new_roster_type


    def can_afford(self, player: Player, roster_type: str = 'active') -> bool:
        """Check if team can afford to add this player"""
        # Change this later, when implementing acquisition services
        if not player.contract:
            return True # Free agents cost nothing until contracted

        # Calculate effective salary of roster type
        temp_status = player.roster_status
        player.roster_status = roster_type
        effective_salary = player.get_effective_salary()
        player.roster_status = temp_status # Reset

        return self.get_remaining_cap() >= effective_salary


    def get_total_salary_used(self) -> float:
        """Calculate total salary against cap"""
        total = 0.0

        # Add up effective salaries from all roster types
        for roster_list in self.roster.values():
            for player in roster_list:
               total += player.get_effective_salary() 

        # Add dead money from dropped players
        total += self.dead_money

        return total


    def get_remaining_cap(self) -> float:
        """Calculate remaining salary cap space"""
        return self.salary_cap - self.get_total_salary_used()


    def get_players_by_position(self, position: str) -> List[Player]:
        """Get all players at a position across all roster types"""
        players = []
        for roster_list in self.roster.values():
            players.extend([p for p in roster_list if p.position == position])
        return players


    def get_starting_lineup_players(self) -> List[Player]:
        """Get players who can start (active roster only)"""
        return self.roster['active'].copy()


    def is_salary_cap_compliant(self) -> bool:
        """Check if team is under salary cap"""
        return self.get_total_salary_used() <= self.salary_cap


    def _validate_player_addition(self, player: Player, roster_type: str):
        """Comprehensive valudation for adding players"""
        # Check if valid roster type
        if roster_type not in self.roster:
            raise ValueError(f"Invalid roster type: {roster_type}")

        # Checks if player has a contract
        if not player.contract:
            raise ValueError(f"{player.name} must have a contract")

        # Check if player is available
        if not player.is_available():
            raise ValueError(f"{player.name} is not available")

        # Check roster space
        if self._get_roster_size(roster_type) >= self._get_roster_max(roster_type):
            raise ValueError(f"{roster_type} roster is full")

        # Check salary cap
        if not self.can_afford(player, roster_type):
            raise ValueError(f"Cannot afford {player.name}")

        # PS validation
        if roster_type == 'practice_squad' and not player.is_eligible_for_practice_squad():
            raise ValueError(f"{player.name} not eligible for practice squad")
        

    def _get_roster_size(self, roster_type: str) -> int:
        """Get current roster size for give roster type"""
        return len(self.roster[roster_type])


    def _get_roster_max(self, roster_type: str) -> int:
        """Get maximum roster size for given type"""
        roster_limits = {
            'active': LEAGUE_SETTINGS['max_roster_size'],
            'practice_squad': LEAGUE_SETTINGS['practice_squad_slots'],
            'IR': LEAGUE_SETTINGS['injured_reserve_slots']
        }
        
        if roster_type not in roster_limits:
            raise ValueError(f"Invalid roster type: {roster_type}")
            
        return roster_limits[roster_type]


    def __repr__(self):
        return f"Team({self.name}: {self._get_roster_size('active')}/26 active, ${self.get_remaining_cap():.0f} cap)"
