# D.O.R.K. v2.0

### A Text Adventure in Corporate America

**Digital Operations Research Kollective, 1987**

*"Synergizing Tomorrow's Solutions Today"*

---

You are a computer engineer in Cubicle 7B. It is Monday. The mainframe has crashed. The Big Client Demo is at 5:00 PM. Your lunch has been stolen by Gary from Accounting. The dot matrix printer may have achieved sentience. And you work at a company whose acronym spells exactly what you think it does.

Welcome to D.O.R.K.

## Play Now

**In your browser (no install):** Open `dork.html` or play at [geox.blog/dork](https://geox.blog)

**On your computer:**
```bash
git clone https://github.com/GeoxT/DORK.git
cd DORK
python3 dork.py
```

No dependencies. Python 3.6+ required. Make your terminal full screen.

## Game Versions

| File | Description | Best For |
|------|-------------|----------|
| `dork.html` | Browser version. Click and play. | Everyone. Share this link. |
| `dork.py` | Full terminal UI with curses sidebar. | Developers. Best experience. |

Both versions include the complete game with all rooms, puzzles, NPCs, endings, and easter eggs. Both support offline play and optional AI narrator.

## Narrator Modes

| Mode | What It Does | Requirements |
|------|-------------|--------------|
| **Play Free / Offline** | Classic text parser. No internet needed. | Nothing. Just play. |
| **Claude AI** | Dynamic AI narrator. Type anything. | Anthropic API key |
| **OpenAI GPT-4o** | Dynamic AI narrator. Type anything. | OpenAI API key |

Switch modes anytime mid-game. Type `APIKEY` to connect. Type `CLEARKEY` to remove.

## API Key Security

Your API key is protected at every step:

- **Never stored to disk** — keys live in memory only, gone when you close the game
- **Input is always masked** — password fields (browser) and getpass (terminal)
- **Masked in all displays** — shown as `sk-a...Pme3`, never the full key
- **CLEARKEY command** — instantly removes key from memory and wipes conversation history
- **Error messages sanitized** — API keys are redacted from any error output
- **No localStorage, cookies, or persistent storage** — zero trace after closing
- **Browser protections** — LastPass/1Password ignore attributes, autocomplete disabled

## Features

- **Full CRT terminal UI** with live sidebar (bytes, suspicion, PTO, clock, inventory)
- **Five game mechanics**: Byte Counter (pun scoring), Corporate Suspicion meter, PTO hours, ticking clock, 8-slot floppy disk inventory
- **11 explorable locations** across the D.O.R.K. office building
- **6 endings** based on your choices, score, and how much management trusts you
- **Easter eggs** referencing Zork, the Commodore 64, Y2K, and the company's ridiculous name
- **Zero dependencies** — Python standard library only / single HTML file

## The Story

You wake up face-down on your desk at the **Digital Operations Research Kollective**. Yes, everyone knows the acronym is ridiculous. The founder, Klaus Dorkmann, allegedly chose the name before learning English. Every new hire goes through five stages: confusion, denial, laughter, acceptance, and the thousand-yard stare.

The company's mainframe, a VAX 11/780 nicknamed **Big Bertha**, has crashed overnight. The **Big Client Demo** is at 5:00 PM. To fix Bertha, you need to:

1. Find the **root password** (carved somewhere private by a former employee)
2. Locate the **diagnostic floppy disk** (buried in the supply closet)
3. Retrieve the **maintenance manual** (hidden among the boss's management books)
4. Trade **Gary's IBM Model M keyboard** for the **server room keycard**
5. Solve a **memory allocation logic puzzle** to bring Bertha back online

All while managing your Corporate Suspicion level, hoarding your precious PTO hours, and earning Bytes through tech puns.

## The Cast

- **You** — Computer engineer, Cubicle 7B. Cold coffee. Dead terminal. Monday.
- **Gary from Accounting** — Your nemesis. Eats your lunch. Hoards peripherals. Will trade the server keycard for his beloved IBM Model M keyboard.
- **Dotty** — A semi-sentient dot matrix printer who communicates through cryptic, poetic printouts.
- **Mr. Henderson** — The boss. Speaks exclusively in buzzwords. Proud of the D.O.R.K. name.
- **Janet from HR** — Hallway gossip source. Knows where the password is hidden.

## Endings

| Ending | Condition |
|--------|-----------|
| **The Hero** | 500+ bytes, mainframe fixed, suspicion under 50% |
| **The Survivor** | Mainframe fixed, 200-499 bytes |
| **The Dork** | 500+ bytes, mainframe NOT fixed |
| **The Fired** | Suspicion hits 100% |
| **The Escape** | Drive away before 5 PM |
| **The Hacker** | Find and run the mysterious floppy labeled "DO NOT RUN" |

## Easter Eggs

- `XYZZY` — Classic Zork reference
- `COMMODORE 64` — Nostalgic aside
- `Y2K` — Prophetic warning
- `THERAC-25` — Dark QA joke
- `PING` — Dotty responds from across the building
- `DORK` — The full history of Klaus Dorkmann and the company name

## Commands

```
LOOK        Examine your surroundings       INVENTORY   Check your 8-slot floppy inventory
GO [place]  Move between rooms              STATUS      View bytes, suspicion, PTO, time
TALK        Talk to NPCs                    PTO         Use a PTO hour (SKIP/BREAK/HINT)
SEARCH      Search the room                 LOOK BUSY   Reduce suspicion
TAKE [item] Pick up an item                 BUZZWORD    Deploy corporate jargon
DROP [item] Drop an item                    FIX         Fix the mainframe (server room)
USE [item]  Use an item                     BOOT        Boot your terminal (cubicle)
DONATE      Support the developer           APIKEY      Connect an AI narrator
CLEARKEY    Remove API key from memory      HELP / QUIT
```

## Platform Notes

| Platform | How to Run |
|----------|-----------|
| **Any browser** | Open `dork.html` — works on desktop, tablet, phone |
| **macOS / Linux** | `python3 dork.py` in Terminal (full screen recommended) |
| **Windows** | `python dork.py` in Windows Terminal or PowerShell |
| **iPad** | Open `dork.html` in Safari. Or use Pythonista / a-Shell for `dork.py` |

## One-Liner Install

```bash
curl -sO https://raw.githubusercontent.com/GeoxT/DORK/main/dork.py && python3 dork.py
```

## Support the Project

Enjoyed D.O.R.K.? Buy the developer a floppy disk:

**BTC: `13P6c6t4Y2ZFpb7tTYB9J1y4YEABXqPme3`**

Or type `DONATE` anytime in-game.

## Author

**Geoffrey Taber**

- GitHub: [github.com/GeoxT](https://github.com/GeoxT)
- Blog: [geox.blog](https://geox.blog)

## License

MIT License. See [LICENSE](LICENSE) for details.

---

*D.O.R.K. — Digital Operations Research Kollective. Where the Future is Mandatory.*
