# D.O.R.K. v2.0 — Setup & Distribution Guide

Complete instructions for publishing D.O.R.K. on GitHub, geox.blog, and itch.io.

---

## Part 1: GitHub

### Step 1: Create the Repository

1. Go to [github.com/new](https://github.com/new)
2. Fill in:
   - **Repository name**: `DORK`
   - **Description**: `D.O.R.K. v2.0 — A text adventure in corporate America. Play in browser or terminal. Optional AI narrator. Zero dependencies.`
   - **Visibility**: **Public**
   - Leave all checkboxes unchecked (no README, .gitignore, or license — we have our own)
3. Click **Create repository**

### Step 2: Push from Terminal

```bash
cd ~/Downloads/DORK

git init
git add .
git commit -m "D.O.R.K. v2.0 — Initial release"
git branch -M main
git remote add origin https://github.com/GeoxT/DORK.git
git push -u origin main
```

If git asks for a password, use a **Personal Access Token**:
- [github.com/settings/tokens](https://github.com/settings/tokens) → Generate new token (classic) → check **repo** scope

### Step 3: Configure About Section

On your repo page, click the **gear icon** next to "About":

- **Description**: `D.O.R.K. v2.0 — A text adventure in corporate America. Play free in browser or terminal. Optional AI narrator (Claude/OpenAI). Zero dependencies.`
- **Website**: `https://geox.blog`
- **Topics** (add each one):
  - `text-adventure`
  - `interactive-fiction`
  - `python`
  - `retro-gaming`
  - `1980s`
  - `adventure-game`
  - `terminal-game`
  - `browser-game`
  - `ai-powered`
  - `claude-ai`
  - `openai`
  - `comedy`
  - `corporate-humor`
- Click **Save changes**

### Step 4: Enable Features

**Settings** → **General**:
- ✅ Issues
- ✅ Discussions (optional)

### Step 5: Create a Release

1. **Releases** → **Create a new release**
2. Fill in:
   - **Tag**: `v2.0`
   - **Title**: `D.O.R.K. v2.0`
   - **Description**:

```
D.O.R.K. v2.0 — A Text Adventure in Corporate America
Digital Operations Research Kollective, 1987
By Geoffrey Taber | github.com/GeoxT | geox.blog

Play free in browser: open dork.html
Play in terminal: python3 dork.py

Features:
- Play free instantly — no account, no install
- Optional AI narrator (Claude / OpenAI)
- Full CRT terminal UI with live sidebar
- 11 rooms, 6 endings, easter eggs, IBM Model M keyboard trade
- API keys are masked, memory-only, never stored
- Zero dependencies

BTC: 13P6c6t4Y2ZFpb7tTYB9J1y4YEABXqPme3
```

3. Drag these into **Attach binaries**:
   - `dork.html`
   - `dork.py`
4. Check **Set as the latest release**
5. Click **Publish release**

### Step 6: Verify

- `https://github.com/GeoxT/DORK` — README renders, topics visible
- `https://github.com/GeoxT/DORK/releases` — v2.0 with downloads
- Test the one-liner:
  ```bash
  curl -sO https://raw.githubusercontent.com/GeoxT/DORK/main/dork.py && python3 dork.py
  ```

---

## Part 2: geox.blog

### Option A: Embed as a WordPress Page

1. In WordPress, create a new **Page** (not Post)
2. Set the slug to `dork` (so the URL is `geox.blog/dork`)
3. Add a **Custom HTML** block
4. Paste the entire contents of `dork.html` into the block
5. Publish

The game will render inline on the page. Make sure your theme allows full-width pages (no sidebar competing for space).

### Option B: Upload as Static File

1. Upload `dork.html` to your WordPress media library or via FTP to your web root
2. Access directly at `geox.blog/dork.html`
3. Create a redirect from `geox.blog/dork` to `geox.blog/dork.html` if desired

### Option C: iframe Embed

1. Upload `dork.html` to your server
2. Create a page with this HTML block:
```html
<iframe src="/dork.html" width="100%" height="800" style="border:none;background:#0a0600;"></iframe>
```

### Blog Post

Write an announcement post linking to the game. Suggested structure:
- Hook: "It is Monday. It is 1987. God help you."
- Brief description of the premise
- Screenshot of the game running
- Link to play: `geox.blog/dork`
- Link to GitHub: `github.com/GeoxT/DORK`
- BTC address for donations

---

## Part 3: itch.io

### Step 1: Create Account & Project

1. Sign up at [itch.io](https://itch.io) if needed
2. Go to [itch.io/game/new](https://itch.io/game/new)

### Step 2: Configure the Game Page

- **Title**: `D.O.R.K. — A Text Adventure in Corporate America`
- **Project URL**: `dork-game` (your-username.itch.io/dork-game)
- **Classification**: Game
- **Kind of project**: HTML
- **Upload**: Upload `dork.html`
  - Check **"This file will be played in the browser"**
- **Viewport dimensions**: Width `960`, Height `600`
- **Fullscreen button**: Enable
- **Mobile friendly**: Yes

### Step 3: Game Details

- **Short description**: `It is Monday. It is 1987. The mainframe is dead. Your lunch has been stolen. The printer may be sentient. Welcome to D.O.R.K.`
- **Genre**: Interactive Fiction
- **Tags**: `text-adventure`, `interactive-fiction`, `retro`, `comedy`, `1980s`, `corporate`, `browser`, `ai`
- **Pricing**: Free / Name your own price (with $0 minimum)
- **Donation**: Enable with suggested amount

### Step 4: Page Content

Write a description. Suggested:

```
D.O.R.K. v2.0 — A Text Adventure in Corporate America

You are a computer engineer at the Digital Operations Research Kollective.
Yes, the acronym spells exactly what you think it does.

It is Monday. It is 1987. The mainframe has crashed. The Big Client Demo 
is at 5:00 PM. Gary from Accounting has stolen your lunch. The dot matrix 
printer may have achieved sentience. And your boss just said "synergy" 
for the fourteenth time today.

Can you fix Big Bertha before 5 PM?

FEATURES:
- Play free instantly — no install, no account
- Optional AI narrator (bring your own Claude or OpenAI key)
- 11 rooms to explore across the D.O.R.K. office
- 6 different endings based on your choices
- Byte Counter that scores your tech puns
- A sentient printer named Dotty who speaks in poetry
- An IBM Model M keyboard subplot

Made by Geoffrey Taber
github.com/GeoxT | geox.blog
BTC: 13P6c6t4Y2ZFpb7tTYB9J1y4YEABXqPme3
```

### Step 5: Screenshots

Upload 3-4 screenshots:
1. Title screen with the ASCII art
2. In-game with the CRT sidebar visible
3. Dotty's poetic printout
4. Gary's dialogue about the Model M

### Step 6: Publish

Click **Save & view page**, verify everything works, then make it **Public**.

---

## Part 4: Sharing

### X/Twitter

Post with a screenshot of the title screen or in-game UI:

```
I built a text adventure set in 1987 corporate America.

You work at the Digital Operations Research Kollective. 
Yes, the acronym spells what you think.

The mainframe is dead. Gary stole your lunch. The printer is sentient.

Play free in your browser:
[link]

#textadventure #indiegame #retrogaming
```

### One-Liner for Developers

```
curl -sO https://raw.githubusercontent.com/GeoxT/DORK/main/dork.py && python3 dork.py
```

### Direct Links

- **GitHub**: `https://github.com/GeoxT/DORK`
- **Blog**: `https://geox.blog/dork`
- **itch.io**: `https://[username].itch.io/dork-game`
- **Play in browser**: `https://geox.blog/dork.html`

---

## Updating Later

```bash
cd ~/path/to/DORK
git add .
git commit -m "Description of changes"
git push
```

For new releases: **Releases** → **Create new release** → tag `v2.1`, etc.

For itch.io: Upload the new `dork.html` and replace the old file.

For geox.blog: Replace the HTML file or update the page content.

---

## File Structure

```
DORK/
├── dork.py              ← Terminal version (curses UI, all 3 modes)
├── dork.html            ← Browser version (play anywhere, all 3 modes)
├── README.md            ← GitHub project page
├── LICENSE              ← MIT License
├── .gitignore           ← Keeps junk out
└── GITHUB_SETUP.md      ← This file
```
