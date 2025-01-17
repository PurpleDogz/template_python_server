def rank_players_simple(head_to_head_results):
    players_set = set()

    for r in head_to_head_results:
        players_set.add(r[0])
        players_set.add(r[1])

    map_players = {player: i for i, player in enumerate(players_set, start=1)}
    reverse_map_players = {i: player for player, i in map_players.items()}

    # print(map_players)
    # print(reverse_map_players)

    players = len(players_set)

    # Initialize player statistics
    player_stats = {
        player: {"wins": 0, "losses": 0, "games": 0} for player in range(1, players + 1)
    }

    # Update stats based on results
    for winner, loser in head_to_head_results:
        player_stats[map_players[winner]]["wins"] += 1
        player_stats[map_players[loser]]["losses"] += 1
        player_stats[map_players[winner]]["games"] += 1
        player_stats[map_players[loser]]["games"] += 1

    # Create a list of players with their stats
    players = [
        (reverse_map_players[player], stats["wins"], stats["losses"], stats["games"])
        for player, stats in player_stats.items()
    ]

    # Sort players by wins (and losses as a tiebreaker if needed)
    players.sort(key=lambda x: (-x[1], x[2]))

    return players


def rank_players_weighted(initial_rankings, head_to_head_results):
    players_set = set()

    for r in head_to_head_results:
        players_set.add(r[0])
        players_set.add(r[1])

    map_players = {player: i for i, player in enumerate(players_set, start=1)}
    reverse_map_players = {i: player for player, i in map_players.items()}

    # print(map_players)
    # print(reverse_map_players)

    players = len(players_set)

    # Reduce to unique head to heads
    head_to_head_results = summarize_head_to_head_results(
        players, map_players, reverse_map_players, head_to_head_results
    )

    # print(head_to_head_results)

    # Initialize player statistics
    player_stats = {
        player: {"weighted_wins": 0, "wins": 0, "losses": 0, "games": 0}
        for player in range(1, players + 1)
    }

    # Update stats based on results
    for winner, loser, _ in head_to_head_results:
        # Calculate win value based on loser's initial ranking
        # Higher value for beating higher-ranked players
        win_value = 1
        if loser in initial_rankings.keys():
            win_value = len(initial_rankings) - (initial_rankings[loser] - 1)

        player_stats[map_players[winner]]["weighted_wins"] += win_value
        player_stats[map_players[winner]]["wins"] += 1
        player_stats[map_players[loser]]["losses"] += 1

        player_stats[map_players[winner]]["games"] += 1
        player_stats[map_players[loser]]["games"] += 1

    # Create a list of players with their stats
    players = [
        (
            reverse_map_players[player],
            stats["wins"],
            stats["losses"],
            stats["games"],
            stats["weighted_wins"],
        )
        for player, stats in player_stats.items()
    ]

    # Sort players by weighted wins (descending), then by losses (ascending)
    players.sort(key=lambda x: (-x[4], x[2]))

    return players


def summarize_head_to_head_results(
    players, map_players, reverse_map_players, head_to_head_results
):
    # Initialize the head-to-head matrix
    head_to_head = [[0 for _ in range(players)] for _ in range(players)]

    # Process the head-to-head results
    for winner, loser in head_to_head_results:
        head_to_head[map_players[winner] - 1][map_players[loser] - 1] += 1

    # Summarize the overall head-to-head results
    overall_results = []
    for i in range(players):
        for j in range(i + 1, players):
            wins_i = head_to_head[i][j]
            wins_j = head_to_head[j][i]
            # print(f"Player {i + 1} vs Player {j + 1}: {wins_i} - {wins_j}")
            # allocate overall win to the player with the most wins
            if wins_i > wins_j:
                overall_results.append(
                    (reverse_map_players[i + 1], reverse_map_players[j + 1], wins_i)
                )
            elif wins_j > wins_i:
                overall_results.append(
                    (reverse_map_players[j + 1], reverse_map_players[i + 1], wins_j)
                )
            # If drawn, no wins for now
            # elif wins_i > 0 and wins_i == wins_j:
            #     overall_results.append((reverse_map_players[i + 1], reverse_map_players[j + 1], wins_i))
            #     overall_results.append((reverse_map_players[j + 1], reverse_map_players[i + 1], wins_j))

    return overall_results


if __name__ == "__main__":
    # Example head-to-head results (winner, loser)
    head_to_head_results = [
        (1, 2),
        (1, 2),
        (1, 2),
        (3, 4),
        (2, 3),
        (4, 5),
        (1, 3),
        (7, 8),
        (2, 5),
        (9, 10),
        (2, 4),
        (2, 3),
        (2, 3),
        (2, 3),
        (6, 8),
        (7, 10),
        (5, 2),
        (9, 6),
        (3, 4),
        (8, 2),
    ]

    head_to_head_results = [
        (11, 2),
        (11, 1),
        (1, 2),
        (3, 4),
        (2, 3),
        (4, 5),
        (1, 3),
        (7, 18),
        (2, 5),
        (9, 10),
        (2, 4),
        (2, 3),
        (4, 3),
        (2, 3),
        (6, 8),
        (7, 10),
        (5, 2),
        (9, 6),
        (3, 4),
        (8, 21),
    ]

    # head_to_head_results = [
    #     (1, 2), (1, 2), (1, 2)
    # ]

    # Display the overall head-to-head results
    # for result in head_to_head_results:
    #     print(f"Player {result[0]} beat Player {result[1]} ({result[2]} times)")

    # # Get ranked players
    # ranked_players = rank_players(head_to_head_results)

    ranked_players = rank_players_simple(head_to_head_results)

    print("\nSimple Ranking (1 point for win)\n")

    # Display the results
    for rank, (player, wins, losses, games) in enumerate(ranked_players, start=1):
        print(
            f"Rank {rank}: Player {player} - Wins: {wins}, Losses: {losses}, Games: {games}"
        )

    print(
        "\nWeighted Ranking (Winning points based on initial rank, higher is more valuable)\n"
    )

    players = 10
    initial_rankings = {
        player: i for i, player in enumerate(range(1, players + 1), start=1)
    }

    # head_to_head_results = [
    #     (1, 2)
    # ]

    # Get ranked players
    ranked_players = rank_players_weighted(initial_rankings, head_to_head_results)

    # Display the results
    for rank, (player, wins, losses, games, weighted_wins) in enumerate(
        ranked_players, start=1
    ):
        print(
            f"Rank {rank}: Player {player} - Weighted Wins: {weighted_wins}, Wins: {wins}, Losses: {losses}, Games: {games}"
        )
