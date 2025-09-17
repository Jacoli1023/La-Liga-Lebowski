from config.settings import LEAGUE_SETTINGS
from src.models.player import Player

class Team:
    def __init__(self, name, draft_position=None):
        self.name = name
        self.draft_position = draft_position
        self.salary_cap = LEAGUE_SETTINGS['salary_cap']
        self.dead_money = 0
        self.roster = {
                'active': [],
                'practice_squad': [],
                'IR': []
        }


    def add_player(self, player, roster_type='active'):
        """Add contracted player to this team's roster"""
        roster_max = self._get_roster_max(roster_type)

        # Checks if player is available
        if not player.is_available():
            raise ValueError(f"Cannot add player: {player.name} is unavailable")

        # Checks if there is enough room on the roster
        if self.get_roster_size(roster_type) >= roster_max:
            raise ValueError(f"Cannot add player: {roster_type} roster is full")

        # Adds player to specified roster, and updates player status
        self.roster[roster_type].append(player)
        player.roster_status = roster_type
        player.fantasy_team = self.name
        # TODO: Implement bids and contracts


    def remove_player(self, player):
        """Remove player from roster, handle salary cap consequences"""
        if not player.fantasy_team == self.name:
            raise ValueError(f"Cannot remove player: {player.name} is not part of your team!")

        for roster_list in self.roster.values():
            if player in roster_list:
                roster_list.remove(player)
                self.dead_money += player.salary
                player.roster_status = "free_agent"
                player.fantasy_team = None
                return
                # TODO: Future dead money penalties via ContractService
                #       Adjust player salary & contract after dropping
        else:
            raise ValueError(f"Cannot remove player: {player.name} not found in roster!")


    def move_player(self, player, new_roster_type):
        """Move player between roster types"""
        # Possibly move ownership check to own method, if logic becomes more obtuse
        if player.fantasy_team != self.name:
            raise ValueError(f"Cannot move player: {player.name} not on your team!")

        current_roster = player.roster_status

        # Validate roster move
        if current_roster == new_roster_type:
            raise ValueError(f"Player {player.name} is already on {new_roster_type} roster")

        roster_max = self._get_roster_max(new_roster_type) 
        if self.get_roster_size(new_roster_type) >= roster_max:
            raise ValueError(f"Cannot move player: {new_roster_type} is full")

    
    def get_total_salary_used(self):
        total_salary = 0

        # Add up effective salaries from all roster types
        for roster_list in self.roster.values():
            for player in roster_list:
               total_salary += player.get_effective_salary() 

        # Add dead money from dropped players
        total_salary += self.dead_money

        return total_salary


    def get_remaining_cap(self):
        return self.salary_cap - self.get_total_salary_used()


    def get_roster_size(self, roster_type):
        return len(self.roster[roster_type])
        

    def can_afford(self, player, roster_type='active'):
        pass


    def _get_roster_max(self, roster_type):
        """Get maximum roster size for given roster type"""
        if roster_type == 'active':
            return LEAGUE_SETTINGS['max_roster_size']
        elif roster_type == 'practice_squad':
            return LEAGUE_SETTINGS['practice_squad_slots']
        elif roster_type == 'IR':
            return LEAGUE_SETTINGS['injured_reserve_slots']
        else:
            raise ValueError(f"Invalid roster type: {roster_type}")
