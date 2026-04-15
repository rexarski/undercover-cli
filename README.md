# Undercover CLI

A command-line version of the party game **Undercover** (a.k.a. "Who Is the Spy?").

## Setup

Requires Python 3.10+. No external dependencies.

```bash
python3 main.py
```

## How It Works

1. **Enter players** — The game asks for the number of players (minimum 4) and their names.
2. **Choose rounds** — Pick how many games to play. Word pairs are randomly sampled from `words.csv`.
3. **Read your word** — Each player gets a `.txt` file in the `data/` directory containing their secret word(s) for every game. Open only your own file. A `moderator.txt` with the full answer key is also generated.

## Roles

Every game, roles are randomly assigned:

| Role | Count | What you see |
|---|---|---|
| **Civilian** | Everyone else | The secret word |
| **Undercover** | 1 | A similar but different word (the variation) |
| **Mr. White** | 1 | `???` (no word at all) |

Players do **not** know their own role at the start.

## Game Phases

Each game repeats these three phases until a group wins:

### 1. Description Phase

A random player starts. One by one, each remaining player describes their word using a single word or phrase. Mr. White must improvise since they have no word.

**Tip:** Reveal enough to find allies, but not so much that Mr. White figures out the civilian word.

### 2. Discussion Phase

Players openly debate who they think the infiltrators (Undercover and Mr. White) are. Civilians and Undercovers can use this to figure out their own identity and build alliances. Mr. White should try to dig deeper into what the civilian word might be.

### 3. Elimination Phase

All remaining players vote to eliminate one person. The player with the most votes is ousted. Ties trigger a revote among tied candidates (with tied players abstaining); if still tied, one is eliminated at random.

**Special rule:** If the eliminated player is Mr. White, they get one chance to guess the civilian word. A correct guess wins the game for Mr. White immediately.

## Victory Conditions

- **Civilians win** if all Undercovers and Mr. Whites are eliminated.
- **Infiltrators win** (Undercover + Mr. White) if only 1 Civilian remains.
- **Mr. White wins** if they correctly guess the civilian word when eliminated.

## Scoring

| Role | Points on win |
|---|---|
| Civilian | 2 |
| Mr. White | 6 |
| Undercover | 10 |

After each game, a leaderboard with a vertical bar chart is displayed. At the end of the session, final standings are shown.

## Features

- **Auto-save / Resume** — Game state is checkpointed to `data/checkpoint.json` before each game. If the process is interrupted, you can resume from where you left off next time you run the game.
- **Early exit** — Declining to continue after any game skips to final scores instead of quitting silently.
- **Cleanup prompt** — At the end, the game offers to delete all generated files in `data/`.

## Word Pairs

Word pairs live in `words.csv` (columns: `round`, `secret`, `variation`). Add or edit rows to customize the word pool. If you request more games than available pairs, the count is automatically capped.
