from src.models.contract import Contract
from src.models.player import Player
from src.models.team import Team

def test_basic_integration():
    print("=== Testing Player + Contract Integration ===")
    
    # Test 1: Create player with contract
    contract = Contract("Josh Allen", 100.0, 3, is_rookie=False)
    player = Player("Josh Allen", "BUF", "QB", contract=contract)
    
    print(f"Player created: {player}")
    print(f"Current salary: ${player.get_current_salary()}")
    print(f"Effective salary: ${player.get_effective_salary()}")
    
    # Test 2: Advance contract year
    print("\n--- Advancing contract year ---")
    player.advance_contract_year()
    print(f"After year advance: {player}")
    print(f"Years remaining: {player.contract.years_remaining}")
    
    # Test 3: Contract extension
    print("\n--- Testing extension ---")
    if player.can_be_extended():
        increase = player.extend_contract(2)
        print(f"Extended contract! Salary increase: ${increase}")
        print(f"Updated player: {player}")
    
    # Test 4: Free agent (no contract)
    print("\n--- Testing free agent ---")
    free_agent = Player("Free Agent", "KC", "RB")
    print(f"Free agent: {free_agent}")
    print(f"Free agent salary: ${free_agent.get_current_salary()}")

def test_team_salary_calculations():
    team = Team("Test Team")
    
    # Add a player
    contract = Contract("Test Player", 100.0, 3)
    player = Player("Test Player", "KC", "RB", contract=contract)
    team.add_player(player)
    
    print(f"Team salary used: ${team.get_total_salary_used()}")
    print(f"Remaining cap: ${team.get_remaining_cap()}")
    
    # Try moving to practice squad
    team.move_player(player, 'practice_squad')
    print(f"After PS move - salary used: ${team.get_total_salary_used()}")

    # Remove player (creates dead money)
    team.remove_player(player)
    print(f"Dead money after removal: ${team.dead_money}")

if __name__ == "__main__":
    test_team_salary_calculations()
