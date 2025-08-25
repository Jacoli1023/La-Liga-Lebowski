VALID_POSITIONS = ["QB", "RB", "WR", "TE", "K", "D/ST"]

NFL_TEAMS = ["ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE",
             "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAX", "KC",
             "MIA", "MIN", "NE", "NO", "NYG", "NYJ", "LV", "PHI",
             "PIT", "LAC", "SF", "SEA", "LAR", "TB", "TEN", "WAS"]

LEAGUE_SETTINGS = {
    # Basic league info
    'name': 'La Liga Lebowski',
    'teams': 12,
    'regular_season_weeks': 14,
    'playoff_weeks': 3,
    
    # Financial
    'salary_cap': 1006,
    'salary_cap_increase_rate': 0.05,
    'player_salary_increase_rate': 0.20,
    
    # Roster limits
    'max_roster_size': 26,
    'practice_squad_slots': 8,
    'injured_reserve_slots': 5,
    
    # Draft settings
    'rookie_draft_rounds': 5,
    'auction_draft': True,
}

# Salary multipliers for roster status
# TODO: Move this to future salary_cap module
SALARY_MULTIPLIERS = {
    'active': 1.00,
    'practice_squad': 0.25,
    'IR': 0.50,
    'free_agent': 0.00  # Free agents don't count against cap
}

SCORING_SETTINGS = {
    'passing_td': 4,
    'passing_yards': 1/25,
    'passing_2pt': 1,
    'interception': -2,
    'rushing_td': 6,
    'rushing_yards': 1/10,
    'rushing_2pt': 2,
    'receiving_td': 6,
    'receiving_yards': 1/10,
    'reception': 0.5,
    'receiving_2pt': 2,
    'fumble_lost': -2,
}

ROSTER_REQUIREMENTS = {
    'starting_lineup': {
        'QB': 1,
        'RB': 2,
        'WR': 3,
        'TE': 1,
        'FLEX_RB_WR': 1,
        'FLEX_WR_TE': 1,
    }
}
