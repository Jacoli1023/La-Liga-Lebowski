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
        if roster_type == 'active':
            roster_max = LEAGUE_SETTINGS['max_roster_size']
        elif roster_type == 'practice_squad':
            roster_max = LEAGUE_SETTINGS['practice_squad_slots']
        elif roster_type == 'IR':
            roster_max = LEAGUE_SETTINGS['injured_reserve_slots']
        else:
            raise ValueError(f"Invalid roster type: {roster_type}")

        if self.get_roster_size(roster_type) >= roster_max:
            raise ValueError(f"Cannot add player: {roster_type} roster is full")

        if self.can_afford(player, roster_type):
            self.roster[roster_type].append(player)
            player.fantasy_team = self.name
            player.roster_status = roster_type

    
    def get_total_salary_used(self):
        total_sal = 0
        for roster_list in self.roster.values():
            for player in roster_list:
               total_sal += player.get_effective_salary() 
        return total_sal
        

    def can_afford(self, player, roster_type='active'):
        pass
