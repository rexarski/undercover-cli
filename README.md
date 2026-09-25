# Undercover

The party game **Undercover** (a.k.a. "Who Is the Spy?") in two flavours: a browser game for remote play (`index.html`, recommended) and the original CLI (`main.py`).

## Browser game (recommended)

No install, no server, no dependencies. Just open `index.html` in any modern browser (Edge/Chrome on a work laptop is fine). Keep `words.js` next to it.

How a session runs (designed for a remote team on a Teams call, with the moderator sharing their screen):

1. **Add players** (minimum 4), tweak the timers and the number of games per word list, hit **Start playing**.
2. **Send the word lists.** The game pre-assigns words and roles for the next batch of games (default 8). Each player gets one message covering all of them: press **Copy** and paste it into a private Teams chat, or **Download .txt** to attach. A `moderator.txt` answer key can be downloaded too. Lists stay hidden on screen so screen sharing is safe.
3. **Rounds**: Description, Discussion, Vote. Votes are cast one ballot at a time by clicking a name (with undo). Ties trigger a tie-break among the non-tied players, then a random pick if still tied.
4. **Mr. White's guess** is typed in and checked automatically. Matching is forgiving: case, spaces, punctuation and accents are ignored, and per-word aliases from `words.csv` count (e.g. `penalty` for `penalty shootout`). A moderator override button accepts a near miss.
5. **Next game** moves straight on, since everyone already has their words. When the batch is used up, new lists are dealt. Late joiners can be added and absent players unticked between games, which re-deals the remaining games and asks you to resend the lists.
6. **End session** at any time for the final standings.

Other bits: the scoreboard on the side updates live after every game, **Pause** freezes the timers (spacebar also works), and progress is auto-saved in the browser so a reload offers to resume.

### Editing the words

Edit `words.csv`, then regenerate `words.js`:

```bash
python build_words.py
```

`words.js` is committed, so this only matters after you change the CSV. As a fallback the setup screen can also load a `words.csv` directly.

## CLI version

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

Word pairs live in `words.csv` with columns `round`, `secret` (civilian word), `variation` (undercover word) and `aliases` (optional, `|`-separated alternative spellings of the civilian word accepted as a correct Mr. White guess in the browser game). Add or edit rows to customize the word pool, then run `python build_words.py` for the browser game. The CLI reads the CSV directly and caps the game count at the number of pairs.

## Recent Changes

- Added a browser version of the game for remote play.
- Refreshed word pairs with 2026 tech, world news, World Cup and new-dad themes.
- Fixed tie-breaking scoring and UTF-8 encoding on Windows.
- Improved game loop outcomes, voting UX, and endgame scoring.
