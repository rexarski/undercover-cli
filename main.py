#!/usr/bin/env python3
"""CLI version of the Undercover game."""

import csv
import json
import os
import random
import re
import shutil
import sys
import tempfile
import threading

# ─── ANSI Colors ──────────────────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORDS_FILE = os.path.join(BASE_DIR, "words.csv")
DATA_DIR = os.path.join(BASE_DIR, "data")
CHECKPOINT_FILE = os.path.join(DATA_DIR, "checkpoint.json")

RESERVED_FILENAMES = {"moderator", "checkpoint"}

VOTE_TIMER_SECONDS = 10


def start_vote_timer(voter: str, seconds: int = VOTE_TIMER_SECONDS) -> threading.Timer:
    """Start a per-voter background timer that prints a reminder when time is up."""

    def _remind():
        print(f"\n  {YELLOW}⏰ Time's up, {voter}! Please cast your vote.{RESET}")

    timer = threading.Timer(seconds, _remind)
    timer.daemon = True
    timer.start()
    return timer


# ─── Scoring ────────────────────────────────────────────────────────────────
# Civilians: 2 pts per win, Mr. White: 6 pts, Undercover: 10 pts

TITLE_ART = f"""{BOLD}{CYAN}
 ╔══════════════════════════════════════════════════════════════╗
 ║                                                              ║
 ║   ██╗   ██╗███╗   ██╗██████╗ ███████╗██████╗                 ║
 ║   ██║   ██║████╗  ██║██╔══██╗██╔════╝██╔══██╗                ║
 ║   ██║   ██║██╔██╗ ██║██║  ██║█████╗  ██████╔╝                ║
 ║   ██║   ██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗                ║
 ║   ╚██████╔╝██║ ╚████║██████╔╝███████╗██║  ██║                ║
 ║    ╚═════╝ ╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝                ║
 ║           ██████╗ ██████╗ ██╗   ██╗███████╗██████╗           ║
 ║          ██╔════╝██╔═══██╗██║   ██║██╔════╝██╔══██╗          ║
 ║          ██║     ██║   ██║██║   ██║█████╗  ██████╔╝          ║
 ║          ██║     ██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗          ║
 ║          ╚██████╗╚██████╔╝ ╚████╔╝ ███████╗██║  ██║          ║
 ║           ╚═════╝ ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝          ║
 ║                                                              ║
 ║                    ~ CLI Edition ~                           ║
 ║                                                              ║
 ╚══════════════════════════════════════════════════════════════╝{RESET}
"""

GAME_BANNER = f"""{BOLD}{YELLOW}
 ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
 ┃  ╔═╗╔═╗╔╦╗╔═╗  {{game_label:^44s}}  ┃
 ┃  ║ ╦╠═╣║║║║╣   {{subtitle:^44s}}  ┃
 ┃  ╚═╝╩ ╩╩ ╩╚═╝  {{blank:^44s}}  ┃
 ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{RESET}
"""

PHASE_ICONS = {
    "describe": f"{BOLD}{BLUE}🗣️  DESCRIPTION PHASE{RESET}",
    "discuss": f"{BOLD}{MAGENTA}💬  DISCUSSION PHASE{RESET}",
    "vote": f"{BOLD}{RED}🗳️  ELIMINATION PHASE{RESET}",
}

WINNER_ART = {
    "civilian": f"""{BOLD}{GREEN}
    ╔═══════════════════════════════════╗
    ║   🏆  CIVILIANS WIN!  🏆         ║
    ║   All infiltrators eliminated.    ║
    ╚═══════════════════════════════════╝{RESET}
""",
    "infiltrator": f"""{BOLD}{RED}
    ╔═══════════════════════════════════╗
    ║   🕵️  INFILTRATORS WIN!  🕵️      ║
    ║   Only 1 civilian remains.        ║
    ╚═══════════════════════════════════╝{RESET}
""",
    "mrwhite": f"""{BOLD}{MAGENTA}
    ╔═══════════════════════════════════╗
    ║   🎩  MR. WHITE WINS!  🎩        ║
    ║   Guessed the civilian word!      ║
    ╚═══════════════════════════════════╝{RESET}
""",
}

GOODBYE_ART = f"""{BOLD}{CYAN}
 ╔══════════════════════════════════════════════════════════════╗
 ║                                                              ║
 ║         Thanks for playing UNDERCOVER!                       ║
 ║         See you next time, agents.  🕵️                       ║
 ║                                                              ║
 ╚══════════════════════════════════════════════════════════════╝{RESET}
"""


# ─── Helpers ────────────────────────────────────────────────────────────────


def hr(char="─", width=62):
    print(f" {char * width}")


def phase_header(phase: str):
    hr("━")
    print(f"  {PHASE_ICONS[phase]}")
    hr("━")


def load_word_pairs(path: str) -> list[tuple[str, str]]:
    pairs = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pairs.append((row["secret"].strip(), row["variation"].strip()))
    return pairs


def prompt_int(msg: str, minimum: int = 1) -> int:
    while True:
        try:
            val = int(input(msg))
            if val >= minimum:
                return val
            print(f"  Please enter at least {minimum}.")
        except ValueError:
            print("  Please enter a valid number.")


def is_valid_filename(name: str) -> bool:
    """Check that a player name is safe to use as a filename."""
    if name.lower() in RESERVED_FILENAMES:
        return False
    # Reject path separators, null bytes, and characters problematic on common OSes
    if re.search(r'[/\\<>:"|?*\x00]', name):
        return False
    # Reject names that are only dots (e.g. ".", "..")
    if re.fullmatch(r'\.+', name):
        return False
    return True


def prompt_names(count: int) -> list[str]:
    names: list[str] = []
    for i in range(1, count + 1):
        while True:
            name = input(f"  Player {i} name: ").strip()
            if not name:
                print("  Name cannot be empty.")
            elif name.lower() in [n.lower() for n in names]:
                print("  Name already taken (case-insensitive).")
            elif not is_valid_filename(name):
                print(f"  Invalid name. Avoid special characters and reserved words ({', '.join(RESERVED_FILENAMES)}).")
            else:
                names.append(name)
                break
    return names


def find_vote_match(choice: str, candidates: list[str]) -> str | None:
    """Case-insensitive vote matching. Returns the canonical name or None."""
    lookup = {c.lower(): c for c in candidates}
    return lookup.get(choice.lower())


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def cleanup_data_dir():
    if os.path.isdir(DATA_DIR):
        shutil.rmtree(DATA_DIR)
        print("  Data directory cleared.")
    else:
        print("  Nothing to clean up.")


# ─── Vertical Bar Chart ────────────────────────────────────────────────────


def print_leaderboard(scores: dict[str, int]):
    """Print a vertical bar chart of scores."""
    if not scores or all(v == 0 for v in scores.values()):
        hr("═")
        print(f"  {BOLD}{YELLOW}📊  LEADERBOARD{RESET}")
        hr("═")
        print("  No points scored yet.\n")
        return

    hr("═")
    print(f"  {BOLD}{YELLOW}📊  LEADERBOARD{RESET}")
    hr("═")

    max_score = max(scores.values())
    chart_height = 12
    names = list(scores.keys())
    vals = [scores[n] for n in names]

    bar_heights = [
        int((v / max_score) * chart_height) if max_score > 0 else 0 for v in vals
    ]

    col_width = max(len(n) for n in names) + 2
    col_width = max(col_width, 6)

    for row in range(chart_height, 0, -1):
        line = "  "
        for h in bar_heights:
            if h >= row:
                cell = f"{GREEN}██{RESET}".center(col_width + len(GREEN) + len(RESET))
            else:
                cell = "".center(col_width)
            line += cell
        score_at_row = round((row / chart_height) * max_score)
        print(f" {score_at_row:>3} │{line}")

    print(f"     └{'─' * (col_width * len(names) + 1)}")

    name_line = "      "
    for n in names:
        name_line += n.center(col_width)
    print(name_line)

    score_line = "      "
    for v in vals:
        score_line += f"({v})".center(col_width)
    print(score_line)
    print()


# ─── File I/O ──────────────────────────────────────────────────────────────


def assign_roles(
    players: list[str],
    secret: str,
    variation: str,
) -> dict[str, tuple[str, str]]:
    shuffled = players[:]
    random.shuffle(shuffled)
    assignments: dict[str, tuple[str, str]] = {}
    assignments[shuffled[0]] = ("Mr. White", "")
    assignments[shuffled[1]] = ("Undercover", variation)
    for p in shuffled[2:]:
        assignments[p] = ("Civilian", secret)
    return assignments


def write_player_files(
    players: list[str],
    num_games: int,
    all_assignments: list[dict[str, tuple[str, str]]],
) -> None:
    ensure_data_dir()
    for name in players:
        path = os.path.join(DATA_DIR, f"{name}.txt")
        with open(path, "w") as f:
            f.write(f"┌{'─'*40}┐\n")
            f.write(f"│{'Secret words for ' + name:^40s}│\n")
            f.write(f"└{'─'*40}┘\n\n")
            for game_idx in range(num_games):
                _, word = all_assignments[game_idx][name]
                display_word = word if word else "???"
                f.write(f"  Game {game_idx + 1}: {display_word}\n")
            f.write(f"\n  ⚠  Do NOT share this file!\n")


def write_moderator_file(
    players: list[str],
    num_games: int,
    all_assignments: list[dict[str, tuple[str, str]]],
    pairs_used: list[tuple[str, str]],
) -> None:
    ensure_data_dir()
    path = os.path.join(DATA_DIR, "moderator.txt")
    with open(path, "w") as f:
        f.write(f"╔{'═'*50}╗\n")
        f.write(f"║{'MODERATOR CHEAT SHEET':^50s}║\n")
        f.write(f"║{'Keep this file hidden from players!':^50s}║\n")
        f.write(f"╚{'═'*50}╝\n\n")
        for game_idx in range(num_games):
            secret, variation = pairs_used[game_idx]
            f.write(f"  ── Game {game_idx + 1} ──\n")
            f.write(f"  Civilian word  : {secret}\n")
            f.write(f"  Undercover word: {variation}\n")
            f.write("  Roles:\n")
            for name in players:
                role, word = all_assignments[game_idx][name]
                f.write(
                    f"    {name:20s} → {role:12s} (word: {word or '---'})\n"
                )
            f.write("\n")


# ─── Checkpoint ────────────────────────────────────────────────────────────


def save_checkpoint(state: dict) -> None:
    """Atomically write checkpoint: write to temp file then rename."""
    ensure_data_dir()
    fd, tmp_path = tempfile.mkstemp(dir=DATA_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp_path, CHECKPOINT_FILE)
    except BaseException:
        # Clean up temp file on any failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def load_checkpoint() -> dict | None:
    if not os.path.isfile(CHECKPOINT_FILE):
        return None
    try:
        with open(CHECKPOINT_FILE) as f:
            data = json.load(f)
        # Basic validation: must have expected keys
        required = {"players", "num_games", "selected_pairs", "all_assignments", "scores", "completed_games"}
        if not required.issubset(data.keys()):
            return None
        return data
    except (json.JSONDecodeError, ValueError, KeyError):
        print("  ⚠  Checkpoint file is corrupted. Starting fresh.")
        return None


def clear_checkpoint():
    if os.path.isfile(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)


def build_checkpoint(
    players: list[str],
    num_games: int,
    selected_pairs: list[tuple[str, str]],
    all_assignments: list[dict[str, tuple[str, str]]],
    scores: dict[str, int],
    completed_games: int,
) -> dict:
    return {
        "players": players,
        "num_games": num_games,
        "selected_pairs": selected_pairs,
        "all_assignments": [
            {name: list(rv) for name, rv in a.items()} for a in all_assignments
        ],
        "scores": scores,
        "completed_games": completed_games,
    }


def restore_assignments(raw: list[dict]) -> list[dict[str, tuple[str, str]]]:
    return [{name: tuple(rv) for name, rv in a.items()} for a in raw]


# ─── Game Loop ─────────────────────────────────────────────────────────────


def compute_scores(
    assignments: dict[str, tuple[str, str]],
    winner: str,
) -> dict[str, int]:
    """Return per-player score delta for a single game."""
    deltas: dict[str, int] = {}
    for name, (role, _) in assignments.items():
        if winner == "civilian" and role == "Civilian":
            deltas[name] = 2
        elif winner == "infiltrator" and role in ("Undercover", "Mr. White"):
            deltas[name] = 10 if role == "Undercover" else 6
        elif winner == "mrwhite" and role == "Mr. White":
            deltas[name] = 6
        else:
            deltas[name] = 0
    return deltas


def run_game_loop(
    players: list[str],
    assignments: dict[str, tuple[str, str]],
    secret_word: str,
    game_num: int,
) -> str:
    """Interactive loop for a single game. Returns winner: 'civilian', 'infiltrator', or 'mrwhite'."""
    alive = players[:]
    random.shuffle(alive)
    round_num = 0

    print(
        GAME_BANNER.format(
            game_label=f"GAME {game_num}",
            subtitle=f"{len(players)} players",
            blank="",
        )
    )

    # With exactly 4 players, warn that games will be short
    roles = {assignments[p][0] for p in players}
    civilians_count = sum(1 for p in players if assignments[p][0] == "Civilian")
    if civilians_count == 2:
        print(f"  {YELLOW}⚠  Only 2 civilians — one wrong elimination and infiltrators win!{RESET}")
        print()

    print("  Each player: open YOUR .txt file in data/ to see your word.")
    input("  Press Enter when everyone has seen their word... ")

    while True:
        round_num += 1
        hr("─")
        print(f"  {BOLD}{BLUE}📍 Round {round_num}{RESET}")
        print(f"  Players still in: {CYAN}{', '.join(alive)}{RESET}")

        # ── Description ──
        phase_header("describe")
        print(f"  Speaking order: {CYAN}{' → '.join(alive)}{RESET}")
        input("  Each player describes their word. Press Enter when done... ")

        # ── Discussion ──
        phase_header("discuss")
        input("  Discuss who the infiltrators are. Press Enter when done... ")

        # ── Elimination ──
        phase_header("vote")
        votes: dict[str, int] = {p: 0 for p in alive}
        for voter in alive:
            timer = start_vote_timer(voter)
            while True:
                raw_choice = input(f"  {voter}, vote to eliminate: ").strip()
                match = find_vote_match(raw_choice, alive)
                if match is None:
                    print(f"    {RED}Invalid. Choose from: {', '.join(alive)}{RESET}")
                elif match == voter:
                    print(f"    {RED}You can't vote for yourself.{RESET}")
                else:
                    votes[match] += 1
                    break
            timer.cancel()

        max_votes = max(votes.values())
        eliminated_candidates = [p for p, v in votes.items() if v == max_votes]

        if len(eliminated_candidates) > 1:
            # Check if any non-tied voters exist for the tie-break
            non_tied_voters = [v for v in alive if v not in eliminated_candidates]
            if not non_tied_voters:
                # Everyone is tied — no one can cast a tie-break. Random elimination.
                print(
                    f"\n  {YELLOW}⚖️  Tie between {', '.join(eliminated_candidates)}!{RESET}"
                )
                print(f"  {YELLOW}No neutral voters available — random elimination!{RESET}")
                eliminated = random.choice(eliminated_candidates)
            else:
                print(
                    f"\n  {YELLOW}⚖️  Tie between {', '.join(eliminated_candidates)}! Revote.{RESET}"
                )
                tie_votes: dict[str, int] = {p: 0 for p in eliminated_candidates}
                for voter in non_tied_voters:
                    timer = start_vote_timer(voter)
                    while True:
                        raw_choice = input(f"  {voter}, tie-break vote: ").strip()
                        match = find_vote_match(raw_choice, eliminated_candidates)
                        if match is None:
                            print(
                                f"    {RED}Choose from: {', '.join(eliminated_candidates)}{RESET}"
                            )
                        else:
                            tie_votes[match] += 1
                            break
                    timer.cancel()
                max_tie = max(tie_votes.values())
                final_candidates = [p for p, v in tie_votes.items() if v == max_tie]
                eliminated = random.choice(final_candidates)
        else:
            eliminated = eliminated_candidates[0]

        role, _ = assignments[eliminated]
        print(f"\n  {BOLD}{RED}❌ {eliminated} is eliminated!{RESET} They were: {YELLOW}{role}{RESET}")

        # Mr. White last chance
        if role == "Mr. White":
            guess = input(
                f"  🎩 {eliminated}, guess the Civilian word: "
            ).strip()
            if guess.lower() == secret_word.lower():
                print(WINNER_ART["mrwhite"])
                return "mrwhite"
            else:
                print(f"  {RED}Wrong!{RESET} The word was '{CYAN}{secret_word}{RESET}'.")

        alive.remove(eliminated)

        # Win conditions
        roles_alive = {p: assignments[p][0] for p in alive}
        civilians_left = sum(1 for r in roles_alive.values() if r == "Civilian")
        infiltrators_left = sum(
            1 for r in roles_alive.values() if r in ("Undercover", "Mr. White")
        )

        if infiltrators_left == 0:
            print(WINNER_ART["civilian"])
            return "civilian"

        if civilians_left <= 1:
            print(WINNER_ART["infiltrator"])
            return "infiltrator"


# ─── Final Scores ──────────────────────────────────────────────────────────


def print_final_scores(scores: dict[str, int]):
    hr("═")
    print(f"  {BOLD}{YELLOW}🏁  FINAL SCORES{RESET}")
    hr("═")
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    for i, (name, pts) in enumerate(ranked, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, "  ")
        print(f"  {medal} {name:20s} {pts} pts")
    print()
    print_leaderboard(scores)


# ─── Graceful exit ─────────────────────────────────────────────────────────


def graceful_exit(
    players: list[str],
    num_games: int,
    selected_pairs: list[tuple[str, str]],
    all_assignments: list[dict[str, tuple[str, str]]],
    scores: dict[str, int],
    completed_games: int,
):
    """Save checkpoint and show final scores on interrupt."""
    print("\n")
    hr("!")
    print(f"  {BOLD}{YELLOW}⚠  Game interrupted! Saving progress...{RESET}")
    hr("!")
    save_checkpoint(
        build_checkpoint(
            players, num_games, selected_pairs, all_assignments, scores, completed_games
        )
    )
    print(f"  {GREEN}💾 Checkpoint saved. Run the game again to resume.{RESET}\n")
    if any(v > 0 for v in scores.values()):
        print_final_scores(scores)
    print(GOODBYE_ART)


# ─── Main ──────────────────────────────────────────────────────────────────


def main() -> None:
    print(TITLE_ART)

    # ── Check for saved checkpoint ──
    checkpoint = load_checkpoint()
    need_new_game = True

    if checkpoint:
        print(f"  {GREEN}💾 Saved game found!{RESET}")
        while True:
            resume = input("  Resume previous game? (y/n): ").strip().lower()
            if resume in ("y", "n"):
                break
            print("  Please enter 'y' or 'n'.")
        if resume == "y":
            players = checkpoint["players"]
            num_games = checkpoint["num_games"]
            selected_pairs = [tuple(p) for p in checkpoint["selected_pairs"]]
            all_assignments = restore_assignments(checkpoint["all_assignments"])
            scores = checkpoint["scores"]
            start_game = checkpoint["completed_games"]
            print(f"  Resuming from game {start_game + 1}...")
            need_new_game = False
        else:
            clear_checkpoint()

    if need_new_game:
        num_players = prompt_int("\n  How many players? (minimum 4): ", minimum=4)
        print(f"\n  Enter {num_players} player names:")
        players = prompt_names(num_players)
        num_games = prompt_int("\n  How many games to play? ", minimum=1)

        all_pairs = load_word_pairs(WORDS_FILE)
        if num_games > len(all_pairs):
            print(
                f"  Only {len(all_pairs)} word pairs available. Capping at {len(all_pairs)}."
            )
            num_games = len(all_pairs)

        selected_pairs = random.sample(all_pairs, num_games)

        all_assignments: list[dict[str, tuple[str, str]]] = []
        for secret, variation in selected_pairs:
            all_assignments.append(assign_roles(players, secret, variation))

        scores = {p: 0 for p in players}
        start_game = 0

        write_player_files(players, num_games, all_assignments)
        write_moderator_file(players, num_games, all_assignments, selected_pairs)

        print(f"\n  📁 Generated files in data/ for: {', '.join(players)}")
        print("  📁 Generated: data/moderator.txt")
        print("\n  Each player should ONLY open their own .txt file.\n")

    # ── Play games (wrapped for graceful Ctrl+C handling) ──
    try:
        for game_idx in range(start_game, num_games):
            secret, _ = selected_pairs[game_idx]

            save_checkpoint(
                build_checkpoint(
                    players, num_games, selected_pairs, all_assignments, scores, game_idx
                )
            )

            winner = run_game_loop(
                players, all_assignments[game_idx], secret, game_idx + 1
            )

            deltas = compute_scores(all_assignments[game_idx], winner)
            for name, pts in deltas.items():
                scores[name] += pts

            print_leaderboard(scores)

            save_checkpoint(
                build_checkpoint(
                    players,
                    num_games,
                    selected_pairs,
                    all_assignments,
                    scores,
                    game_idx + 1,
                )
            )

            if game_idx < num_games - 1:
                cont = input("  Continue to next game? (y/n): ").strip().lower()
                if cont != "y":
                    print("\n  Ending session early. Here are the final standings:\n")
                    break

    except (KeyboardInterrupt, EOFError):
        graceful_exit(
            players, num_games, selected_pairs, all_assignments, scores,
            game_idx if 'game_idx' in dir() else start_game,
        )
        sys.exit(0)

    # ── Final scores ──
    print_final_scores(scores)
    clear_checkpoint()

    # ── Cleanup prompt ──
    cleanup = (
        input("  🗑️  Clear all generated files in data/? (y/n): ").strip().lower()
    )
    if cleanup == "y":
        cleanup_data_dir()

    print(GOODBYE_ART)


if __name__ == "__main__":
    main()
