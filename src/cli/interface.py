#!/usr/bin/env python3
"""
La Liga Lebowski Fantasy Football Simulator CLI
Basic interface for testing league functionality
"""

import click
from rich.console import Console
from rich.table import Table
from rich import print

from src.models.player import Player
from src.models.team import Team
from src.models.league import League
from src.models.contract import Contract

console = Console()

@click.group()
@click.pass_context
def cli(ctx):
    """La Liga Lebowski Fantasy Football Simulator"""
    ctx.ensure_object(dict)
    # Initialize league
    ctx.obj['league'] = League(2025)

@cli.command()
@click.pass_context
def setup_demo(ctx):
    """Set up a demo league with sample teams and players"""
    league = ctx.obj['league']

    # Create some demo teams
    team_names = ["Team Alpha", "Team Beta", "Team Gamma", "Team Delta"]
    for i, name in enumerate(team_names):
        team = Team(name, draft_position=i+1)
        league.add_team(team)

    # Create some demo players
    demo_players = [
            ("Josh Allen", "BUF", "QB", 350.5),
            ("Christian McCaffrey", "SF", "RB", 280.2),
            ("Tyreek Hill", "MIA", "WR", 245.8),
            ("Travis Kelce", "KC", "TE", 220.1),
            ("Lamar Jackson", "BAL", "QB", 310.7),
            ("Derrick Henry", "TEN", "RB", 195.3),
    ]

    for i, (name, team, pos, points) in enumerate(demo_players):
        # Create player with contract
        player = Player(name, team, pos)
        contract = Contract(name, 50 + (i * 10), 3, is_rookie=False, start_year=2023)
        player.set_contract(contract)
        player.fantasy_points = points

        # Assign to teams
        target_team = league.teams[i % len(league.teams)]
        try:
            target_team.add_player(player)
            console.print(f"Added {name} to {target_team.name}")
        except Exception as e:
            console.print(f"Error adding {name}: {e}")

    console.print(f"\nDemo league setup complete with {len(league.teams)} teams!")


@cli.command()
@click.pass_context
def league_status(ctx):
    """Show current league status"""
    league = ctx.obj['league']
    stats = league.get_league_stats()

    console.print(f"\n[bold]La Liga Lebwoski - {stats['season_year']}[/bold]")
    console.print(f"Salary Cap: ${stats['salary_cap']:,.2f}")
    console.print(f"Teams: {stats['total_teams']}")
    console.print(f"Free Agents: {stats['free_agents']}")
    console.print(f"Phase: {stats['current_phase']}")

    # Team summary table
    if league.teams:
        table = Table(title="Team Summary")
        table.add_column("Team", style="cyan")
        table.add_column("Players", justify="right")
        table.add_column("Salary Used", justify="right")
        table.add_column("Cap Space", justify="right")
        table.add_column("Cap %", justify="right")

        for team in league.teams:
            salary_used = team.get_total_salary_used()
            cap_space = team.get_remainining_cap()
            cap_pct = (salary_used / team.salary_cap) * 100

            total_players = sum(len(roster) for roster in team.roster.values())

            table.add_row(
                    team.name,
                    str(total_players),
                    f"${salary_used:,.2f}",
                    f"${cap_space:,.2f}",
                    f"{cap_pct:.1f}%"
            )

        console.print(table)


@cli.command()
@click.argument('team_name')
@click.pass_context
def team_roster(ctx, team_name):
    """Show detailed roster for a specific team"""
    league = ctx.obj['league']
    team = league.get_team_by_name(team_name)

    if not team:
        console.print(f" Team '{team_name}' not found")
        return

    console.print(f"\n[bold]{team.name} Roster [/bold]")
    console.print(f"Salary Cap: ${team.salary_cap:,.2f}")
    console.print(f"Used: ${team.get_total_salary_used():,.2f}")
    console.print(f"Available: ${team.get_remaining_cap():,.2f}")

    for roster_type, players in team.roster.items():
        if players:
            table = Table(title=f"{roster_type.replace('_', ' ').title()} Roster ({len(players)} players)")
            table.add_column("Player", style="cyan")
            table.add_column("Position", style="magenta")
            table.add_column("NFL Team", style="yellow")
            table.add_column("Salary", justify="right", style="green")
            table.add_column("Contract", justify="right")
            table.add_column("Fantasy Pts", justify="right")

            for player in players:
                contract_info = f"{player.contract.years_remaining}yr" if player.contract else "N/A"
                salary_info = f"${player.get_current_salary():,.2f}" if player.contract else "$0.00"

                table.add_row(
                        player.name,
                        player.position,
                        player.nfl_team,
                        salary_info,
                        contract_info,
                        f"{player.fantasy_points:.1f}"
                )

            console.print(table)


@cli.command()
@click.pass_context
def advance_season(ctx):
    """Advance the league to the next season"""
    league = ctx.obj['league']

    console.print(f"Advancing from {league.season_year} season...")

    # Simulate some season stats first
    league.simulate_season_stats()

    # Advance the season
    old_cap = league.current_salary_cap
    league.advance_season()
    new_cap = league.current_salary_cap

    console.print(f"Season advanced to {league.season_year}")
    console.print(f"Salary cap increased from ${old_cap:,.2f} to ${new_cap:,.2f}")

    # Show any cap violations
    violations = league._validate_salary_caps()
    if violations:
        console.print(f"Salary cap violations detected:")
        for team in violations:
            overage = team.get_total_salary_used() - team.salary_cap
            console.print(f"    {team.name}: ${overage:,.2f} over cap")


@cli.command()
@click.argument('team_name')
@click.argument('player_name')
@click.argument('years', type=int)
@click.pass_context
def extend_player(ctx, team_name, player_name, years):
    """Extend a player's contract"""
    league = ctx.obj['league']
    team = league.get_team_by_name(team_name)

    if not team:
        console.print(f"Team '{team_name}' not found")
        return

    # Find player on team
    player = None
    for roster_list in team.roster.values():
        for p in roster_list:
            if p.name.lower() == player_name.lower():
                player = p
                break
        if player:
            break
    
    if not player:
        console.print(f"Player '{player_name}' not found on {team_name}")
        return

    try:
        old_salary = player.get_current_salary()
        salary_increase = player.extend_contract(years)
        new_salary = player.get_current_salary()

        console.print(f"Extended {player.name} for {years} additional years")
        console.print(f"Salary: ${old_salary:.2f} -> ${new_salary:.2f} (+${salary_increase:.2f})")
        console.print(f"Contract: {player.contract.years_remaining} years remaining")

    except Exception as e:
        console.print(f"Cannot extend contract: {e}")


@cli.command()
@click.pass_context
def check_holdouts(ctx):
    """Check for potential holdouts across the league"""
    league = ctx.obj['league']

    console.print("Checking for potential holdouts...")

    # Calculate position averages
    position_averages = league._calculate_position_averages()

    holdouts_found = false
    for team in league.teams:
        team_holdouts = []

        for roster_list in team.roster.values():
            for player in roster_list:
                if player.contract:
                    pos_avg = position_averages.get(player.position, 0)
                    if pos_avg > 0:
                        # Check if player would hold out
                        current_salary = player.contract.current_salary
                        threshold = pos_avg * 0.5

                        if (current_salary < threshold and
                            player.fantasy_points > 0): # Has performance data
                            demands = pos_avg * 0.75
                            team_holdouts.append((player, demands))

        if team_holdouts:
            holdouts_found = True
            console.print(f"\n[bold]{team.name} Potential Holdouts:[/bold/")

            table = Table()
            table.add_column("Player", style="cyan")
            table.add_column("Position", style="magenta")
            table.add_column("Current Salary", justify="right", style="red")
            table.add_column("Demands", justify="right", style="yellow")
            table.add_column("Increase", justify="right", style="green")

            for player, demands in team_holdouts:
                increase = demands - player.contract.current_salary
                table.add_row(
                        player.name,
                        player.position,
                        f"${player.contract.current_salary:.2f}",
                        f"${demands:.2f}",
                        f"+${increase:.2f}"
                )

            console.print(table)

    if not holdouts_found:
        console.print("No holdout situations detected")


@cli.command()
@click.pass_context
def simulate_draft(ctx):
    """Simulate a basic rookie draft"""
    league = ctx.obj['league']

    if not league.rookie_draft_order:
        console.print("Draft order not set. Run 'advance_season' first.")
        return

    console.print("[bold]Rookie Draft Simulation[/bold]")
    console.print("Draft Order:")

    table = Table()
    table.add_column("Pick", justify="right", style="cyan")
    table.add_column("Team", style="magenta")
    
    for i, team in enumerate(league.rookie_draft_order, 1):
        table.add_row(str(i), team.name)
    
    console.print(table)
    console.print("\n(Full draft simulation coming soon!)")

if __name__ == '__main__':
    cli()
