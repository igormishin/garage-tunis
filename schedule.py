"""
Beach volleyball 2v2 scheduler for 6 players.
Generates an optimal schedule maximizing partner/opponent diversity
and balancing play/rest across players.
"""

from itertools import combinations
import random
import math


def generate_all_games(players):
    """Generate all possible game configurations: (team1, team2, resting)."""
    games = []
    for rest in combinations(players, 2):
        active = [p for p in players if p not in rest]
        seen = set()
        for team1 in combinations(active, 2):
            team2 = tuple(p for p in active if p not in team1)
            key = frozenset([frozenset(team1), frozenset(team2)])
            if key not in seen:
                seen.add(key)
                games.append((team1, team2, rest))
    return games


def get_stats(schedule):
    """Compute all stats for a schedule."""
    partner_counts = {}
    opponent_counts = {}
    play_counts = {}
    rest_counts = {}

    for team1, team2, rest in schedule:
        p1 = frozenset(team1)
        p2 = frozenset(team2)
        partner_counts[p1] = partner_counts.get(p1, 0) + 1
        partner_counts[p2] = partner_counts.get(p2, 0) + 1

        for a in team1:
            for b in team2:
                opp = frozenset([a, b])
                opponent_counts[opp] = opponent_counts.get(opp, 0) + 1

        for p in team1 + team2:
            play_counts[p] = play_counts.get(p, 0) + 1
        for p in rest:
            rest_counts[p] = rest_counts.get(p, 0) + 1

    return partner_counts, opponent_counts, play_counts, rest_counts


def score_schedule(schedule, players):
    """Score a schedule — lower is better."""
    partner_counts, opponent_counts, play_counts, rest_counts = get_stats(schedule)

    score = 0

    # Partner diversity: each pair should partner at most once (16 slots, 15 pairs)
    for cnt in partner_counts.values():
        if cnt > 1:
            score += (cnt - 1) ** 2 * 100

    # Coverage bonus
    score += (15 - len(partner_counts)) * 50

    # Opponent diversity: 32 slots / 15 pairs = ~2.13 avg
    # Ideal: most pairs meet 2 times, a couple meet 3
    # Penalize variance from mean
    opp_values = [opponent_counts.get(frozenset(pair), 0) for pair in combinations(players, 2)]
    opp_mean = sum(opp_values) / len(opp_values)
    opp_variance = sum((x - opp_mean) ** 2 for x in opp_values) / len(opp_values)
    score += opp_variance * 80

    # Uncovered opponents
    score += opp_values.count(0) * 60

    # Play balance
    plays = [play_counts.get(p, 0) for p in players]
    play_mean = sum(plays) / len(plays)
    play_var = sum((x - play_mean) ** 2 for x in plays) / len(plays)
    score += play_var * 20

    # Consecutive rest penalty
    for p in players:
        consecutive = 0
        for team1, team2, rest in schedule:
            if p in rest:
                consecutive += 1
                if consecutive >= 2:
                    score += 60
            else:
                consecutive = 0

    return score


def simulated_annealing(players, num_games=8, max_iter=50000):
    """Find optimal schedule using simulated annealing."""
    all_games = generate_all_games(players)

    # Initial random schedule
    schedule = random.sample(all_games, num_games)
    best_score = score_schedule(schedule, players)
    best_schedule = list(schedule)

    temp = 100.0
    cooling = 0.9997

    for i in range(max_iter):
        # Mutate: replace one random game
        idx = random.randint(0, num_games - 1)
        old_game = schedule[idx]
        new_game = random.choice(all_games)
        schedule[idx] = new_game

        new_score = score_schedule(schedule, players)

        # Accept or reject
        delta = new_score - best_score
        if delta < 0 or random.random() < math.exp(-delta / max(temp, 0.01)):
            if new_score < best_score:
                best_score = new_score
                best_schedule = list(schedule)
        else:
            schedule[idx] = old_game  # revert

        temp *= cooling

    return best_schedule, best_score


def optimize(players, num_games=8, runs=20):
    """Run SA multiple times, return best."""
    best_schedule = None
    best_score = float('inf')

    for _ in range(runs):
        schedule, score = simulated_annealing(players, num_games)
        if score < best_score:
            best_score = score
            best_schedule = schedule

    return best_schedule, best_score


def print_schedule(schedule, players):
    """Pretty-print the schedule with stats."""
    partner_counts, opponent_counts, play_counts, rest_counts = get_stats(schedule)

    print("=" * 55)
    print("  РАСПИСАНИЕ ИГР — ПЛЯЖНЫЙ ВОЛЕЙБОЛ 2×2")
    print("=" * 55)

    for i, (team1, team2, rest) in enumerate(schedule, 1):
        t1 = f"{team1[0]}+{team1[1]}"
        t2 = f"{team2[0]}+{team2[1]}"
        r = f"{rest[0]}, {rest[1]}"
        print(f"  Игра {i:2d} │ {t1:>5s}  vs  {t2:<5s} │ отдых: {r}")

    print("\n" + "=" * 55)
    print("  СТАТИСТИКА")
    print("=" * 55)

    print("\n  Нагрузка на игрока:")
    for p in players:
        bar_play = "█" * play_counts.get(p, 0)
        bar_rest = "░" * rest_counts.get(p, 0)
        print(f"    {p}: {bar_play}{bar_rest}  ({play_counts.get(p,0)} игр, {rest_counts.get(p,0)} отд.)")

    print(f"\n  Уникальных пар партнёров: {len(partner_counts)}/15")
    repeats = {k: v for k, v in partner_counts.items() if v > 1}
    if repeats:
        for pair, cnt in repeats.items():
            names = sorted(pair)
            print(f"    ⚠ {names[0]}+{names[1]}: {cnt} раз")
    else:
        print("    ✓ Все уникальны!")

    print(f"\n  Уникальных пар противников: {len(opponent_counts)}/15")
    max_opp = max(opponent_counts.values()) if opponent_counts else 0
    if max_opp > 2:
        opp_repeats = {k: v for k, v in opponent_counts.items() if v > 2}
        for pair, cnt in sorted(opp_repeats.items(), key=lambda x: -x[1]):
            names = sorted(pair)
            print(f"    ⚠ {names[0]} vs {names[1]}: {cnt} раз")
    else:
        print("    ✓ Все пары встречаются ≤2 раз!")

    # Opponent distribution
    from collections import Counter
    dist = Counter(opponent_counts.values())
    uncovered = 15 - len(opponent_counts)
    if uncovered:
        dist[0] = uncovered
    print(f"\n  Распределение встреч противников:")
    for k in sorted(dist.keys()):
        print(f"    {k} встреч: {dist[k]} пар")


if __name__ == "__main__":
    players = [1, 2, 3, 4, 5, 6]

    print("Оптимизирую расписание (simulated annealing)...\n")
    schedule, score = optimize(players, num_games=8, runs=30)
    print(f"Скор: {score:.1f} (0 = идеально)\n")
    print_schedule(schedule, players)
