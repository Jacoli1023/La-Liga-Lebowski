VALID_POSITION = ["QB", "RB", "WR", "TE", "K", "D/ST"]
NFL_TEAMS = ["ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE",
             "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAX", "KC",
             "MIA", "MIN", "NE", "NO", "NYG", "NYJ", "LV", "PHI",
             "PIT", "LAC", "SF", "SEA", "LAR", "TB", "TEN", "WAS"]

LEAGUE_SETTINGS = {
    # Basic league info
    'name': 'La Liga Lebowski',
    'teams': 12,
    'max_roster_size': 26,
    'regular_season_weeks': 14,
    'playoff_weeks': 3,
    
    # Financial
    'salary_cap': 1006,
    'salary_cap_increase_rate': 0.05,
    'player_salary_increase_rate': 0.20,
    
    # Roster limits
    'practice_squad_slots': 8,
    'injured_reserve_slots': 5,
    
    # Draft settings
    'rookie_draft_rounds': 5,
    'auction_draft': True,
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
