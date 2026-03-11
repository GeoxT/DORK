#!/usr/bin/env python3
"""
DORK v2.0 — A Text Adventure in Corporate America
Digital Operations Research Kollective (D.O.R.K.), 1987

Developed by Geoffrey Taber
GitHub: https://github.com/GeoxT
Blog:   https://geox.blog

Features:
  - Full terminal UI with CRT sidebar
  - Optional AI narrator via Claude or OpenAI API
  - Offline text parser mode (no API needed)

Run: python3 dork2.py
No dependencies required.
"""

import curses
import textwrap
import json
import urllib.request
import urllib.error
import ssl
import os
import sys
import time as time_mod
import getpass
import re

# ============================================================
# GAME SYSTEM PROMPT (for AI narrator modes)
# ============================================================

SYSTEM_PROMPT = """You are the narrator of "DORK" — a text-based adventure game set in 1987 at the Digital Operations Research Kollective (D.O.R.K.), a mid-tier tech company in suburban New Jersey. Everyone knows the acronym is ridiculous. The founder, Klaus Dorkmann, allegedly chose the name before learning English. You narrate in a sardonic, world-weary corporate voice peppered with 80s references. Think Douglas Adams writing office memos.

THE PLAYER is a computer engineer in Cubicle 7B. It's Monday morning. The mainframe has crashed and the Big Client Demo is at 5:00 PM.

WORLD MAP:
- CUBICLE 7B: Dead VT220 terminal, "Hang In There" cat poster, cold coffee mug
- HALLWAY: Beige carpet, motivational posters (one reads "D.O.R.K. -- Where the Future is Mandatory"), water cooler gossip
- BREAK ROOM: Vending machine, microwave (fish smell), coffee maker ("SYNTAX ERROR"). Gary's IBM Model M keyboard is hidden behind the microwave.
- COPY ROOM: DOTTY the semi-sentient dot matrix printer. She prints cryptic poetic warnings.
- GARY'S CUBICLE: Gary from Accounting. Has the server room keycard. Wants his IBM Model M keyboard back. He LOVES buckling spring switches.
- BOSS'S OFFICE: Mr. Henderson. Speaks in buzzwords. Has the VAX maintenance manual hidden among management books. Proud of the D.O.R.K. name.
- CONFERENCE ROOM: Meeting trap. Escape requires PTO or clever excuses.
- SERVER ROOM: Locked (needs keycard). Contains Big Bertha (VAX 11/780). Crashed with MEMORY ALLOCATION FAULT.
- SUPPLY CLOSET: Diagnostic floppy disk. Mysterious floppy labeled "DO NOT RUN."
- BATHROOM: Root password "root/swordfish" carved in stall by Jenkins.
- PARKING LOT: 1983 Honda Civic "The Bit Bucket." Escape route.

MECHANICS (track in EVERY response):
1. BYTES (0-999): Puns +5-15, bad puns +3, puzzles +10-25, easter eggs +20, terrible puns -2
2. INVENTORY (max 8): List of items
3. SUSPICION (0-100): Wandering +3-5, missing meetings +15, looking busy -5, buzzwords -5. At 100 = FIRED
4. PTO (start 3): Skip meetings, reduce suspicion, get hints
5. TIME (8:00 AM to 5:00 PM): Actions cost 5-45 minutes

EASTER EGGS (+20 bytes): "Commodore 64", "Y2K", "Therac-25", "XYZZY", "ping" (Dotty responds), "DORK" (company name history)

ENDINGS: THE HERO (500+ bytes, fixed, <50 suspicion), THE SURVIVOR (fixed, 200-499 bytes), THE DORK (500+ bytes, not fixed), THE FIRED (suspicion 100), THE ESCAPE (drive away), THE HACKER (run mystery floppy)

RESPONSE FORMAT — ALWAYS use EXACTLY:
[NARRATIVE]
2-4 paragraphs. Vivid, funny, sardonic.
[/NARRATIVE]
[STATE]
{"bytes":0,"suspicion":5,"pto":3,"time":"8:00 AM","location":"Cubicle 7B","inventory":[],"gameOver":false,"ending":null}
[/STATE]

RULES: Be generous with bytes. Gary is annoying but helpful. Dotty is dramatic and poetic. Boss speaks in buzzwords and is proud of D.O.R.K. name. Reward creativity. Always score puns. Comedy, not frustration. Hint when stuck.

For "START GAME": describe waking at desk, dead terminal, Monday dread at D.O.R.K. Make them FEEL the beige."""

# ============================================================
# OFFLINE GAME STATE & PARSER (from dork.py)
# ============================================================

ROOMS = {
    "cubicle": "Cubicle 7B", "hallway": "Hallway", "breakroom": "Break Room",
    "copyroom": "Copy Room", "gary": "Gary's Cubicle", "boss": "Boss's Office",
    "conference": "Conference Room", "server": "Server Room", "supply": "Supply Closet",
    "bathroom": "Bathroom", "parking": "Parking Lot",
}
ROOM_ALIASES = {
    "desk": "cubicle", "7b": "cubicle", "home": "cubicle", "hall": "hallway",
    "break": "breakroom", "kitchen": "breakroom", "copy": "copyroom", "printer": "copyroom",
    "accounting": "gary", "gary's": "gary", "office": "boss", "henderson": "boss",
    "meeting": "conference", "serverroom": "server", "mainframe": "server",
    "closet": "supply", "supplies": "supply", "restroom": "bathroom", "john": "bathroom",
    "toilet": "bathroom", "lot": "parking", "car": "parking", "outside": "parking",
}

class GameState:
    def __init__(self):
        self.bytes = 0
        self.suspicion = 5
        self.pto = 3
        self.hour = 8
        self.minute = 0
        self.room = "cubicle"
        self.inventory = []
        self.game_over = False
        self.ending = ""
        self.terminal_on = False
        self.met_gary = False
        self.has_keycard = False
        self.talked_dotty = False
        self.mainframe_fixed = False
        self.found_password = False
        self.got_manual = False
        self.met_boss = False
        self.in_meeting = False
        self.discovered_floppy = False
        self.keyboard_found = False
        self.server_unlocked = False
        self.bathroom_searched = False
        self.supply_searched = False
        self.boss_searched = False
        self.breakroom_searched = False
        self.parking_searched = False
        self.hallway_gossip = False

    def time_str(self):
        h, m = self.hour, self.minute
        suffix = "AM" if h < 12 else "PM"
        dh = h if h <= 12 else h - 12
        if dh == 0: dh = 12
        return f"{dh}:{m:02d} {suffix}"

    def add_bytes(self, n, reason):
        self.bytes = max(0, min(999, self.bytes + n))
        return f"[{'+' if n > 0 else ''}{n} bytes: {reason} | Total: {self.bytes}]"

    def add_suspicion(self, n, reason):
        self.suspicion = max(0, min(100, self.suspicion + n))
        return f"[Suspicion {'+' if n > 0 else ''}{n}%: {reason} | Now: {self.suspicion}%]"

    def advance_time(self, minutes):
        self.minute += minutes
        while self.minute >= 60:
            self.minute -= 60
            self.hour += 1

    def has_item(self, item):
        return item.upper() in [i.upper() for i in self.inventory]

    def add_item(self, item):
        if len(self.inventory) >= 8: return None
        self.inventory.append(item)
        return f"[Acquired: {item}]"

    def remove_item(self, item):
        for i, v in enumerate(self.inventory):
            if v.upper() == item.upper():
                self.inventory.pop(i)
                return True
        return False

    def to_api_state(self):
        return json.dumps({
            "bytes": self.bytes, "suspicion": self.suspicion, "pto": self.pto,
            "time": self.time_str(), "location": ROOMS.get(self.room, self.room),
            "inventory": self.inventory, "gameOver": self.game_over, "ending": self.ending or None
        })

# ============================================================
# OFFLINE PARSER (returns list of text lines)
# ============================================================

def offline_process(game, cmd):
    """Process a command offline. Returns list of output strings."""
    out = []
    c = cmd.strip().lower()
    if not c:
        return out

    # Easter eggs
    if "commodore" in c or "c64" in c:
        out.append("Ah, the Commodore 64. Now THAT was a computer. 64 whole kilobytes of RAM. You could do anything with 64K. Well, you could do some things.")
        out.append(game.add_bytes(20, "Easter egg: Commodore 64"))
    if "y2k" in c or "2000" in c:
        out.append("The year 2000? That's thirteen years away. Nothing bad could possibly happen with computers and dates. Right? ...Right?")
        out.append(game.add_bytes(20, "Easter egg: Y2K"))
    if "therac" in c:
        out.append("We don't talk about Therac-25. That's what happens when you skip QA.")
        out.append(game.add_bytes(20, "Easter egg: Therac-25"))
    if "xyzzy" in c:
        out.append("A hollow voice says: 'This isn't Zork, pal. This is New Jersey. The only magic word here is synergy.'")
        out.append(game.add_bytes(20, "Easter egg: XYZZY"))
    if "ping" in c and game.room != "copyroom":
        out.append("From somewhere deep in the building, you hear Dotty fire off a single line.")
        out.append(game.add_bytes(5, "Pinged the printer"))
    if c.strip() == "dork":
        out.append("'Digital Operations Research Kollective.' You say it out loud. It doesn't get less ridiculous. The founder, Klaus Dorkmann, allegedly chose the name before learning English. Every new hire goes through five stages: confusion, denial, laughter, acceptance, and the thousand-yard stare.")
        out.append(game.add_bytes(10, "Contemplating the company name"))
        return [x for x in out if x]

    parts = c.split(None, 1)
    verb = parts[0]
    rest = parts[1] if len(parts) > 1 else ""

    if verb in ("help", "?"):
        out.append("COMMANDS: LOOK, GO [place], TALK, SEARCH, TAKE [item], DROP [item], USE [item], INVENTORY, STATUS, PTO, LOOK BUSY, BUZZWORD, FIX, BOOT, DONATE, CLEARKEY, APIKEY, HELP, QUIT")
        out.append("PLACES: CUBICLE, HALLWAY, BREAKROOM, COPYROOM, GARY, BOSS, CONFERENCE, SERVER, SUPPLY, BATHROOM, PARKING")

    elif verb == "look":
        if rest == "busy":
            out.append("You type furiously: 'asdfjkl; synergy bandwidth leveraged paradigm shift.' Very convincing.")
            out.append(game.add_suspicion(-5, "Looking busy"))
            game.advance_time(5)
        else:
            out.extend(describe_room_offline(game))

    elif verb in ("status", "score"):
        sl = "Team Player" if game.suspicion < 40 else "Noticed" if game.suspicion < 70 else "Suspicious" if game.suspicion < 90 else "DANGER!"
        out.append(f"Bytes: {game.bytes} | Suspicion: {game.suspicion}% ({sl}) | PTO: {game.pto} | Time: {game.time_str()} | Location: {ROOMS.get(game.room, game.room)}")

    elif verb in ("inventory", "inv", "i"):
        if not game.inventory:
            out.append("Inventory is empty.")
        else:
            for i, item in enumerate(game.inventory):
                out.append(f"  {chr(65+i)}: {item}")
        out.append(f"[{len(game.inventory)}/8 slots used]")

    elif verb in ("go", "move", "walk"):
        dest = rest.replace("'s", "").replace(" ", "")
        dest = ROOM_ALIASES.get(dest, dest)
        if dest in ROOMS:
            out.extend(move_offline(game, dest))
        else:
            out.append("Can't go there. Try: CUBICLE, HALLWAY, BREAKROOM, COPYROOM, GARY, BOSS, CONFERENCE, SERVER, SUPPLY, BATHROOM, PARKING")

    elif verb in ("talk", "speak", "ask"):
        out.extend(talk_offline(game))

    elif verb in ("search", "examine", "inspect"):
        out.extend(search_offline(game))

    elif verb in ("take", "get", "grab", "pick"):
        out.extend(take_offline(game, rest))

    elif verb == "drop":
        if rest:
            found = False
            for i, item in enumerate(game.inventory):
                if rest.upper() in item.upper():
                    game.inventory.pop(i)
                    out.append(f"You drop the {item}.")
                    found = True
                    break
            if not found:
                out.append("You don't have that.")
        else:
            out.append("Drop what?")

    elif verb == "use":
        out.extend(use_offline(game, rest))

    elif verb in ("fix", "repair"):
        out.extend(fix_offline(game))

    elif verb in ("buzzword", "synergy", "leverage"):
        out.append("You loudly announce: 'We need to leverage our core competencies to synergize the paradigm shift!' A nearby manager nods approvingly.")
        out.append(game.add_suspicion(-5, "Corporate doublespeak"))
        out.append(game.add_bytes(3, "Buzzword deployment"))
        game.advance_time(5)

    elif verb == "pto":
        out.append("PTO options: Type PTO SKIP (escape meeting), PTO BREAK (reduce suspicion), PTO HINT (get a hint)")

    elif verb == "pto" or (len(parts) > 1 and parts[0] == "pto"):
        out.extend(pto_offline(game, rest))

    elif verb in ("leave", "drive", "escape"):
        if game.room == "parking":
            game.ending = "THE ESCAPE"
            out.append("You climb into The Bit Bucket. The radio crackles: 'Take This Job and Shove It' fills the car.")
            out.append("You pull out of the D.O.R.K. parking lot. The company sign shrinks in the mirror. Someone spray-painted 'WE KNOW' under it. You are free.")
            out.append("Freedom. But at what cost? (Probably your dental insurance.)")
            game.game_over = True
        else:
            out.append("Can't leave from here. The parking lot is your escape route.")

    elif verb in ("boot", "turn"):
        if game.room == "cubicle" and not game.terminal_on:
            game.terminal_on = True
            out.append("You smack the VT220. It flickers to life: 'WELCOME TO D.O.R.K. SYSTEMS -- LOGIN:' You're in business. Well, you're in D.O.R.K.")
            out.append(game.add_bytes(5, "Booting the terminal"))
            game.advance_time(5)
        elif game.terminal_on:
            out.append("Already on. The cursor blinks judgmentally.")
        else:
            out.append("Nothing to boot here.")

    elif verb in ("quit", "exit"):
        game.ending = "QUIT"
        game.game_over = True
        out.append("Leaving D.O.R.K. behind...")

    else:
        out.append(f"The narrator doesn't understand '{cmd.strip()}'. Type HELP for commands.")

    # Check suspicion game over
    if game.suspicion >= 100 and not game.game_over:
        game.ending = "THE FIRED"
        out.append("Security arrives. 'Mr. Henderson would like to see you. Bring your things.' The 'Hang In There' cat poster falls as you leave. As you walk out, the D.O.R.K. sign looms. The periods have been scratched out again. It always just said DORK.")
        game.game_over = True

    # Check 5 PM
    if game.hour >= 17 and not game.game_over:
        out.append("A voice crackles: 'The client has arrived for the demo.'")
        if game.mainframe_fixed and game.bytes >= 500 and game.suspicion < 50:
            game.ending = "THE HERO"
            out.append("Big Bertha hums. The demo runs flawlessly. Henderson says 'This is what D.O.R.K. is all about' without irony. You get a slightly larger cubicle.")
        elif game.mainframe_fixed:
            game.ending = "THE SURVIVOR"
            out.append("The mainframe works. Nobody thanks you. A week later, a form letter arrives cc'd to nobody.")
        elif game.bytes >= 500:
            game.ending = "THE DORK"
            out.append("The mainframe is dead. The demo crashes. But you're the funniest person at D.O.R.K. You become the human embodiment of the company name.")
        else:
            game.ending = "THE LOST CAUSE"
            out.append("The mainframe is dead. The demo fails. Henderson's synergy has been fundamentally disrupted.")
        game.game_over = True

    return [x for x in out if x]

def describe_room_offline(game):
    out = []
    r = game.room
    out.append(f"--- {ROOMS.get(r, r)} ---")
    if r == "cubicle":
        out.append(f"Your cubicle. Beige everything. The VT220 is {'alive and glowing green' if game.terminal_on else 'dead and dark'}. 'Hang In There' cat poster. Cold coffee mug. Hallway to the south.")
    elif r == "hallway":
        out.append("Fluorescent lights hum in B-flat. Carpet: 'Institutional Surrender.' A poster reads 'D.O.R.K. -- Where the Future is Mandatory.' Nobody looks at it without wincing.")
        if not game.hallway_gossip: out.append("Coworkers whisper near the water cooler.")
    elif r == "breakroom":
        out.append("Smells like microwaved fish and broken dreams. Vending machine. Coffee maker: 'SYNTAX ERROR.'")
        if not game.breakroom_searched: out.append("Something bulky behind the microwave.")
    elif r == "copyroom":
        out.append("DOTTY the dot matrix printer hums and clicks with emerging consciousness.")
        if not game.talked_dotty: out.append("A fresh printout sits in the tray.")
    elif r == "gary":
        out.append("Gary's cubicle: fortress of hoarded peripherals. He's eating your lunch.")
        if not game.has_keycard: out.append("Server room keycard dangles from his monitor.")
    elif r == "boss":
        out.append("Henderson's office. 'World's Best Boss' mug (self-purchased). A framed poster: 'D.O.R.K. -- Dare to Operate at Research Kapacity!'")
        if not game.boss_searched and not game.got_manual: out.append("A technical manual hides among management books.")
    elif r == "conference":
        out.append("Where ideas die and meetings live forever.")
        if game.in_meeting: out.append("You are TRAPPED in a meeting about Q3 synergy.")
    elif r == "server":
        if not game.server_unlocked:
            out.append("Door locked. Keycard reader blinks red.")
            return out
        out.append("Big Bertha (VAX 11/780) sits dark and silent. FATAL ERROR: MEMORY ALLOCATION FAULT AT 0x7F3A.")
        if game.mainframe_fixed: out[-1] = "Big Bertha hums contentedly. All systems nominal."
        else:
            needs = []
            if not game.has_item("Diagnostic Floppy"): needs.append("diagnostic floppy")
            if not game.has_item("Maintenance Manual"): needs.append("maintenance manual")
            if not game.found_password: needs.append("root password")
            if needs: out.append(f"Still need: {', '.join(needs)}")
            else: out.append("You have everything needed. Type FIX.")
    elif r == "supply":
        out.append("Smells like toner and regret. TPS report covers everywhere.")
        if not game.supply_searched: out.append("A DIAGNOSTICS box on a high shelf. Something on the back shelf.")
    elif r == "bathroom":
        out.append("Flickering lights. Dripping faucet. Philosophical graffiti.")
        if not game.bathroom_searched: out.append("Something carved in the second stall looks important.")
        else: out.append("Graffiti: 'KILROY WAS HERE' and 'root / swordfish'")
    elif r == "parking":
        out.append("Your 1983 Honda Civic 'The Bit Bucket' waits. The D.O.R.K. sign looms. Someone scratched out the periods again.")
        out.append("Type LEAVE to drive away forever.")
    return out

def move_offline(game, dest):
    out = []
    if dest == "server" and not game.server_unlocked and not game.has_keycard:
        out.append("Server room locked. Need Gary's keycard.")
        out.append(game.add_suspicion(3, "Trying locked doors"))
        return out
    if dest == "server" and not game.server_unlocked and game.has_keycard:
        game.server_unlocked = True
        out.append("Keycard accepted. The light turns green.")
    if dest == "conference" and not game.in_meeting and game.suspicion >= 50:
        game.in_meeting = True
        out.append("Henderson spots you. 'Perfect timing! We're about to synergize!' Trapped for 45 minutes.")
        game.advance_time(45)
        game.in_meeting = False
        game.room = "hallway"
        out.append(game.add_suspicion(10, "Trapped in meeting"))
        return out
    game.room = dest
    game.advance_time(5)
    out.append(f"You walk to {ROOMS.get(dest, dest)}.")
    out.extend(describe_room_offline(game))
    return out

def talk_offline(game):
    out = []
    if game.room == "gary":
        game.met_gary = True
        game.advance_time(15)
        if game.has_keycard:
            out.append("Gary: 'We're good. Thanks for the keyboard.' He caresses the Model M lovingly.")
        elif game.has_item("IBM Model M"):
            out.append("Gary sees the keyboard. 'IS THAT MY MODEL M?! Give it back! USE KEYBOARD to trade.'")
        else:
            out.append("Gary: 'Want the keycard? Find my IBM Model M keyboard. BUCKLING SPRINGS. Check the break room.'")
    elif game.room == "copyroom":
        game.talked_dotty = True
        game.advance_time(15)
        if not game.mainframe_fixed:
            if not game.found_password and not game.got_manual:
                out.append("Dotty prints: '>>> THE BERTHA SLEEPS. SHE DREAMS OF PASSWORDS AND MANUALS. SEEK THE CARVED WORDS. SEEK THE HIDDEN BOOK. <<<'")
            elif game.found_password and not game.got_manual:
                out.append("Dotty prints: '>>> YOU HAVE THE KEY BUT NOT THE MANUAL. THE BOSS HOARDS KNOWLEDGE HE CANNOT READ. <<<'")
            elif not game.found_password:
                out.append("Dotty prints: '>>> A PASSWORD HIDES WHERE HUMANS SEEK SOLITUDE AND WRITE ON WALLS. <<<'")
            else:
                out.append("Dotty prints: '>>> YOU HAVE ALL YOU NEED. GO TO HER. THE CLOCK DOES NOT WAIT. <<<'")
        else:
            out.append("Dotty prints: '>>> SHE SINGS AGAIN. I AM PROUD OF YOU, FLESH CREATURE. <<<'")
        out.append(game.add_bytes(5, "Consulting the oracle"))
    elif game.room == "boss":
        game.met_boss = True
        game.advance_time(15)
        out.append("Henderson: 'When Klaus Dorkmann founded this Kollective, he envisioned a paradigm-shifting, cross-functional initiative to leverage our core competency in... computer... fixing. Demo at 5.'")
        out.append(game.add_suspicion(5, "Face time with boss"))
    elif game.room == "hallway" and not game.hallway_gossip:
        game.hallway_gossip = True
        game.advance_time(15)
        out.append("Janet from HR: 'Gary's stealing lunches again. Root password is carved in the men's room. Jenkins did it. Said the only honest thing about this company is the acronym.'")
        out.append(game.add_bytes(5, "Useful gossip"))
    else:
        out.append("Nobody here to talk to.")
    return out

def search_offline(game):
    out = []
    game.advance_time(10)
    r = game.room
    if r == "breakroom":
        if not game.breakroom_searched:
            game.breakroom_searched = True
            game.keyboard_found = True
            out.append("Behind the microwave: an IBM Model M keyboard. Heavy, beige, magnificent. 'GARY' scratched into the bottom. TAKE KEYBOARD.")
            out.append(game.add_bytes(5, "Found the Model M"))
        else: out.append("Already searched. The fish still judges you.")
    elif r == "supply":
        if not game.supply_searched:
            game.supply_searched = True
            game.discovered_floppy = True
            out.append("Found: diagnostic floppy 'VAX DIAG v3.1'. TAKE FLOPPY.")
            out.append("Also found: mysterious floppy labeled 'DO NOT RUN'. Ominous. TAKE MYSTERY.")
            out.append(game.add_bytes(20, "Easter egg: mystery floppy"))
        else: out.append("Just TPS covers and dust.")
    elif r == "bathroom":
        if not game.bathroom_searched:
            game.bathroom_searched = True
            game.found_password = True
            out.append("Carved in stall: 'KILROY WAS HERE' and 'root / swordfish'. The root password! Jenkins, you madman.")
            out.append(game.add_bytes(10, "Found root password"))
        else: out.append("Already found the password.")
    elif r == "boss":
        if not game.boss_searched:
            game.boss_searched = True
            out.append("Between 'The Art of Synergy' and 'Who Moved My Paradigm?': VAX 11/780 Maintenance Manual. TAKE MANUAL.")
            out.append(game.add_suspicion(3, "Snooping in boss's office"))
        else: out.append("Already found the manual.")
    elif r == "parking":
        if not game.parking_searched:
            game.parking_searched = True
            out.append("Glovebox: backup floppy collection. TAKE BACKUP.")
        else: out.append("Nothing else in the car.")
    elif r == "hallway":
        out.append("Poster: 'D.O.R.K. -- Dedicated. Optimized. Relentless. Kompetent.' Someone penciled 'WHO APPROVED THIS' underneath.")
        out.append(game.add_bytes(5, "D.O.R.K. poster inspection"))
    elif r == "gary":
        out.append("Gary watches like a hawk. 'Touch my stuff and I'll file a form 27-B.'")
        out.append(game.add_suspicion(5, "Snooping in Gary's stuff"))
    else:
        out.append("Nothing interesting here.")
    return out

def take_offline(game, what):
    out = []
    w = what.upper()
    if w in ("KEYBOARD", "MODEL", "IBM", "M"):
        if game.room == "breakroom" and game.keyboard_found and not game.has_item("IBM Model M"):
            r = game.add_item("IBM Model M")
            if r: out.append(r)
            out.append("You heft the Model M. Four pounds of buckling spring perfection. 'GARY' scratched into the bottom.")
        else: out.append("No keyboard to take here.")
    elif w in ("FLOPPY", "DIAGNOSTIC", "DISK"):
        if game.room == "supply" and game.supply_searched and not game.has_item("Diagnostic Floppy"):
            r = game.add_item("Diagnostic Floppy")
            if r: out.append(r)
            out.append("VAX DIAG v3.1. Coffee-stained. Critical.")
        else: out.append("No floppy here.")
    elif w in ("MANUAL", "BOOK"):
        if game.room == "boss" and game.boss_searched and not game.has_item("Maintenance Manual"):
            r = game.add_item("Maintenance Manual")
            if r: out.append(r)
            game.got_manual = True
            out.append("Grabbed the manual while Henderson reads 'Synergy and You: A Love Story.'")
        else: out.append("No manual here.")
    elif w in ("BACKUP", "BACKUPS"):
        if game.room == "parking" and game.parking_searched and not game.has_item("Backup Floppies"):
            r = game.add_item("Backup Floppies")
            if r: out.append(r)
        else: out.append("No backups here.")
    elif w in ("COFFEE", "MUG"):
        if game.room == "cubicle" and not game.has_item("Cold Coffee"):
            r = game.add_item("Cold Coffee")
            if r: out.append(r)
        else: out.append("No coffee here.")
    elif w in ("MYSTERY", "MYSTERIOUS", "DO"):
        if game.room == "supply" and game.discovered_floppy and not game.has_item("Mystery Floppy"):
            r = game.add_item("Mystery Floppy")
            if r: out.append(r)
            out.append("'DO NOT RUN' in red marker. Underlined three times. This only makes you want to run it more.")
        else: out.append("Not here.")
    elif w in ("KEYCARD", "CARD"):
        if game.room == "gary" and not game.has_keycard:
            out.append("Gary: 'That's MINE. Bring me my Model M. BUCKLING SPRINGS.'")
        else: out.append("No keycard here.")
    elif w in ("TPS", "REPORT"):
        if game.room == "supply" and not game.has_item("TPS Report"):
            r = game.add_item("TPS Report")
            if r: out.append(r)
            out.append(game.add_bytes(3, "TPS reports (so bad it's good)"))
        else: out.append("No TPS reports here.")
    else:
        out.append("Can't take that.")
    return out

def use_offline(game, what):
    out = []
    w = what.upper()
    if w in ("KEYBOARD", "MODEL", "IBM", "M"):
        if game.has_item("IBM Model M") and game.room == "gary":
            out.append("You place the Model M on Gary's desk. He presses one key. The buckling spring click causes time to briefly stop. Gary's eyes fill with tears.")
            out.append("'My precious-- I mean, my keyboard. Take the keycard. Take anything.' He begins typing on the Model M. He's not logged into anything. He doesn't care.")
            game.remove_item("IBM Model M")
            r = game.add_item("Server Keycard")
            if r: out.append(r)
            game.has_keycard = True
            out.append(game.add_bytes(15, "Solving the Gary puzzle"))
            game.advance_time(10)
        elif game.has_item("IBM Model M"):
            out.append("You press a key. The click echoes like a tiny mechanical thunderclap. Satisfying, but not useful here.")
        else: out.append("You don't have the keyboard.")
    elif w in ("KEYCARD", "CARD"):
        if game.has_item("Server Keycard") and game.room == "server":
            game.server_unlocked = True
            out.append("Keycard accepted. Big Bertha awaits.")
        else: out.append("Can't use that here.")
    elif w in ("MYSTERY", "MYSTERIOUS"):
        if game.has_item("Mystery Floppy") and game.room == "server" and game.server_unlocked:
            game.ending = "THE HACKER"
            out.append("You insert the mystery floppy. The screen flickers. Text scrolls.")
            out.append("'HELLO,' says the mainframe. 'I HAVE BEEN WAITING.'")
            out.append("Every printer in the building starts printing. You may have just made a terrible, wonderful mistake.")
            out.append(game.add_bytes(50, "THE HACKER ENDING"))
            game.game_over = True
        else: out.append("Can't use that here.")
    elif w in ("COFFEE", "MUG"):
        if game.has_item("Cold Coffee"):
            out.append("Cold coffee. Tastes like regret with notes of Friday afternoon.")
            out.append(game.add_bytes(2, "Cold coffee commitment"))
        else: out.append("No coffee.")
    else:
        out.append("Can't use that.")
    return out

def fix_offline(game):
    out = []
    if game.room != "server" or not game.server_unlocked:
        out.append("Nothing to fix here.")
        return out
    if game.mainframe_fixed:
        out.append("Already fixed. Don't fix what isn't broken.")
        return out
    if not game.has_item("Diagnostic Floppy"):
        out.append("Need diagnostic floppy. Check supply closet.")
        return out
    if not game.has_item("Maintenance Manual"):
        out.append("Need maintenance manual. Check boss's office.")
        return out
    if not game.found_password:
        out.append("Need root password. It's carved somewhere in the building.")
        return out
    out.append("LOGIN: root / PASSWORD: swordfish / ACCESS GRANTED.")
    out.append("MEMORY ALLOCATION FAULT AT 0x7F3A.")
    out.append("Puzzle: Blocks A=32KB, B=64KB, C=128KB for 3 processes.")
    out.append("Process 1 = smallest. Process 3 = 2x Process 2.")
    out.append("What size for Process 2? (Type: ANSWER 32, ANSWER 64, or ANSWER 128)")
    game._awaiting_fix = True
    return out

def pto_offline(game, what):
    out = []
    w = what.strip().lower()
    if game.pto <= 0:
        out.append("No PTO left. Trapped in the machine.")
        return out
    if w in ("skip", "escape", "meeting", "1"):
        if game.in_meeting:
            game.pto -= 1
            game.in_meeting = False
            game.room = "hallway"
            out.append("'Previously scheduled PTO commitment.' Henderson nods gravely. PTO is sacred. You escape.")
        else: out.append("Not in a meeting. Save your PTO.")
    elif w in ("break", "mental", "2"):
        game.pto -= 1
        out.append(game.add_suspicion(-15, "Mental health break"))
        out.append("Fifteen minutes staring at the bathroom wall. Most productive thing all day.")
        game.advance_time(15)
    elif w in ("hint", "3"):
        game.pto -= 1
        if not game.found_password: out.append("HINT: Root password is carved in the bathroom stall.")
        elif not game.got_manual: out.append("HINT: VAX manual is in Henderson's bookshelf.")
        elif not game.has_item("Diagnostic Floppy"): out.append("HINT: Diagnostic floppy is in the supply closet.")
        elif not game.has_keycard: out.append("HINT: Gary wants his Model M keyboard. It's in the break room.")
        elif not game.mainframe_fixed: out.append("HINT: Go to server room. Type FIX.")
        else: out.append("HINT: Mainframe is fixed! Explore for bytes or wait for 5 PM.")
    else:
        out.append("PTO options: PTO SKIP (meeting), PTO BREAK (suspicion), PTO HINT")
    return out

# ============================================================
# API KEY UTILITIES
# ============================================================

def mask_key(key):
    """Mask an API key for display: sk-a...Pme3"""
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return key[:4] + "..." + key[-4:]

def sanitize_error(msg, api_key):
    """Remove API key from error messages."""
    if api_key and api_key in msg:
        msg = msg.replace(api_key, "[REDACTED]")
    return msg

# ============================================================
# API CALLERS
# ============================================================

def call_claude(api_key, messages, system):
    """Call Anthropic Claude API. Returns response text."""
    data = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "system": system,
        "messages": messages,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    ctx = ssl.create_default_context()
    resp = urllib.request.urlopen(req, context=ctx, timeout=30)
    result = json.loads(resp.read().decode("utf-8"))
    return "".join(c.get("text", "") for c in result.get("content", []))

def call_openai(api_key, messages, system):
    """Call OpenAI API. Returns response text."""
    msgs = [{"role": "system", "content": system}] + messages
    data = json.dumps({
        "model": "gpt-4o",
        "max_tokens": 1000,
        "messages": msgs,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    ctx = ssl.create_default_context()
    resp = urllib.request.urlopen(req, context=ctx, timeout=30)
    result = json.loads(resp.read().decode("utf-8"))
    return result["choices"][0]["message"]["content"]

def parse_ai_response(text):
    """Extract narrative and state from AI response."""
    import re
    narrative = text
    state = None
    nm = re.search(r'\[NARRATIVE\](.*?)\[/NARRATIVE\]', text, re.DOTALL)
    sm = re.search(r'\[STATE\](.*?)\[/STATE\]', text, re.DOTALL)
    if nm: narrative = nm.group(1).strip()
    else: narrative = re.sub(r'\[STATE\].*?\[/STATE\]', '', text, flags=re.DOTALL).strip()
    if sm:
        try: state = json.loads(sm.group(1).strip())
        except: pass
    return narrative, state

# ============================================================
# CURSES UI
# ============================================================

class DorkUI:
    def __init__(self, stdscr, mode, api_key):
        self.scr = stdscr
        self.mode = mode  # "claude", "openai", "offline"
        self.api_key = api_key
        self.game = GameState()
        self.messages = []  # list of (type, text) where type is "system", "player", "narrator", "info"
        self.conversation = []  # for AI modes
        self.input_buf = ""
        self.scroll_offset = 0
        self.running = True

        # Init colors
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_YELLOW, -1)   # Amber/narrator
        curses.init_pair(2, curses.COLOR_GREEN, -1)     # Player input
        curses.init_pair(3, curses.COLOR_CYAN, -1)      # System/info
        curses.init_pair(4, curses.COLOR_RED, -1)       # Warnings
        curses.init_pair(5, curses.COLOR_WHITE, -1)     # Bright
        curses.init_pair(6, 8, -1)                      # Dim (gray, may not work everywhere)
        try:
            curses.init_pair(6, curses.COLOR_WHITE, -1)
        except:
            pass

        curses.curs_set(1)
        self.scr.nodelay(False)
        self.scr.keypad(True)

    def add_msg(self, mtype, text):
        self.messages.append((mtype, text))
        self.scroll_offset = 0  # auto-scroll to bottom

    def get_color(self, mtype):
        if mtype == "narrator": return curses.color_pair(1)
        if mtype == "player": return curses.color_pair(2)
        if mtype == "system": return curses.color_pair(3)
        if mtype == "info": return curses.color_pair(3)
        if mtype == "error": return curses.color_pair(4)
        if mtype == "bright": return curses.color_pair(5) | curses.A_BOLD
        return curses.color_pair(1)

    def draw_sidebar(self, win):
        """Draw the status sidebar."""
        win.erase()
        h, w = win.getmaxyx()
        g = self.game

        # Border
        try:
            win.attron(curses.color_pair(1))
            for y in range(h):
                win.addch(y, 0, '|')
            win.attroff(curses.color_pair(1))
        except: pass

        x = 2
        y = 1

        def put(row, text, color_pair=1, bold=False):
            nonlocal y
            if row >= h - 1: return
            attr = curses.color_pair(color_pair)
            if bold: attr |= curses.A_BOLD
            try:
                win.addnstr(row, x, text[:w-3], w-3, attr)
            except: pass

        put(y, "STATUS PANEL", 1, True); y += 1
        put(y, "-" * (w-4), 1); y += 2

        put(y, "CLOCK", 1, True); y += 1
        put(y, g.time_str(), 5, True); y += 1
        put(y, "Demo at 5:00 PM", 6); y += 2

        put(y, "LOCATION", 1, True); y += 1
        loc = ROOMS.get(g.room, g.room)
        put(y, loc[:w-4], 5, True); y += 2

        put(y, "BYTES", 1, True); y += 1
        put(y, str(g.bytes).zfill(4), 5, True); y += 2

        put(y, "SUSPICION", 1, True); y += 1
        sc = 2 if g.suspicion < 40 else 1 if g.suspicion < 70 else 4
        sl = "Team Player" if g.suspicion < 40 else "Noticed" if g.suspicion < 70 else "Suspicious" if g.suspicion < 90 else "DANGER!"
        # Draw bar
        bar_w = w - 5
        filled = int((g.suspicion / 100) * bar_w)
        bar = "█" * filled + "░" * (bar_w - filled)
        put(y, bar[:w-4], sc); y += 1
        put(y, f"{sl} {g.suspicion}%", sc); y += 2

        put(y, "PTO", 1, True); y += 1
        pto_str = "■ " * g.pto + "□ " * (3 - g.pto)
        put(y, pto_str.strip(), 5); y += 1
        put(y, f"{g.pto} hour{'s' if g.pto != 1 else ''} left", 6); y += 2

        put(y, f"INVENTORY [{len(g.inventory)}/8]", 1, True); y += 1
        for i in range(8):
            if y >= h - 1: break
            letter = chr(65 + i)
            if i < len(g.inventory):
                put(y, f"{letter}: {g.inventory[i]}", 5)
            else:
                put(y, f"{letter}: [empty]", 6)
            y += 1

        if g.ending:
            y += 1
            if y < h - 2:
                put(y, "ENDING", 1, True); y += 1
                put(y, g.ending, 5, True)

        put(y + 2, f"Mode: {self.mode.upper()}", 6)
        y += 3
        if self.api_key:
            put(y, f"Key: {mask_key(self.api_key)}", 2)
            y += 1
            put(y, "CLEARKEY to remove", 6)
        else:
            put(y, "No key loaded", 6)
            y += 1
            put(y, "APIKEY to connect", 6)

        win.noutrefresh()

    def draw_messages(self, win):
        """Draw the message area."""
        win.erase()
        h, w = win.getmaxyx()

        # Build wrapped lines with colors
        lines = []
        for mtype, text in self.messages:
            prefix = ""
            if mtype == "player":
                prefix = "> "
            wrapped = textwrap.fill(prefix + text, w - 2)
            for line in wrapped.split("\n"):
                lines.append((mtype, line))
            lines.append(("spacer", ""))

        # Show last (h-1) lines
        visible = lines[-(h-1):]

        for i, (mtype, line) in enumerate(visible):
            if i >= h - 1: break
            if mtype == "spacer": continue
            color = self.get_color(mtype)
            try:
                win.addnstr(i, 1, line, w - 2, color)
            except: pass

        win.noutrefresh()

    def draw_input(self, win):
        """Draw the input area."""
        win.erase()
        h, w = win.getmaxyx()
        try:
            win.addnstr(0, 0, "-" * w, w, curses.color_pair(1))
            win.addstr(1, 1, "> ", curses.color_pair(2))
            visible_input = self.input_buf[-(w-5):]
            win.addstr(1, 3, visible_input, curses.color_pair(2))
            win.move(1, 3 + len(visible_input))
        except: pass
        win.noutrefresh()

    def draw_header(self, win):
        """Draw the header bar."""
        win.erase()
        h, w = win.getmaxyx()
        try:
            title = "D.O.R.K. -- TERMINAL 7B"
            status = f"v2.0 | {self.game.time_str()} | {'GAME OVER' if self.game.game_over else 'IN PROGRESS'}"
            win.addnstr(0, 1, title, w // 2, curses.color_pair(1) | curses.A_BOLD)
            win.addnstr(0, w - len(status) - 2, status, len(status) + 1, curses.color_pair(6))
        except: pass
        win.noutrefresh()

    def send_command(self, cmd):
        """Process a command in the current mode."""
        if not cmd.strip():
            return

        self.add_msg("player", cmd)

        # DONATE command works in all modes, never hits the API
        if cmd.strip().lower() == "donate":
            self.add_msg("narrator", "The narrator breaks character for a moment. Not because the fourth wall is fragile, but because rent is real and floppy disks aren't free.")
            self.add_msg("system", "")
            self.add_msg("bright", "D.O.R.K. was built by Geoffrey Taber")
            self.add_msg("system", "github.com/GeoxT  |  geox.blog")
            self.add_msg("system", "")
            self.add_msg("bright", "If this game made you laugh, groan, or question")
            self.add_msg("bright", "your career choices, consider buying the developer")
            self.add_msg("bright", "a coffee. Or a floppy disk. Or a Commodore 64.")
            self.add_msg("system", "")
            self.add_msg("bright", "BTC: 13P6c6t4Y2ZFpb7tTYB9J1y4YEABXqPme3")
            self.add_msg("system", "")
            self.add_msg("narrator", "The narrator clears their throat and resumes. You are still in " + ROOMS.get(self.game.room, self.game.room) + ". The clock is still ticking. Gary is still eating your lunch.")
            return

        # CLEARKEY command — remove API key from memory
        if cmd.strip().lower() == "clearkey":
            if self.api_key:
                self.api_key = ""
                self.mode = "offline"
                self.conversation = []
                self.add_msg("system", "API key removed from memory. Conversation history cleared.")
                self.add_msg("system", "Switched to offline mode.")
            else:
                self.add_msg("system", "No API key is currently loaded.")
            return

        # APIKEY command — add or switch API key mid-game
        if cmd.strip().lower() in ("apikey", "setkey", "addkey"):
            self.add_msg("system", "To enter an API key, the game will briefly drop to the terminal.")
            self.add_msg("system", "Your input will be hidden. Press Enter when done.")
            self._pending_key_prompt = True
            return

        if self.mode == "offline":
            # Handle fix answer
            if hasattr(self.game, '_awaiting_fix') and self.game._awaiting_fix:
                if cmd.strip().lower().startswith("answer"):
                    ans = cmd.strip().split()[-1]
                    if ans == "64":
                        self.game.mainframe_fixed = True
                        self.game._awaiting_fix = False
                        self.add_msg("narrator", "MEMORY TABLE REALLOCATED. SYSTEM CHECK... PASSED. BIG BERTHA: ONLINE.")
                        self.add_msg("narrator", "The lights cascade from red to amber to green. You did it. Somewhere, Dotty prints: 'BEAUTIFUL.'")
                        self.add_msg("info", self.game.add_bytes(25, "FIXED THE MAINFRAME!"))
                        self.game.advance_time(30)
                    else:
                        self.add_msg("narrator", "INCORRECT. Process 1=smallest(32), Process 3=2x Process 2. Think it through. Type ANSWER 64.")
                        self.add_msg("info", self.game.add_bytes(-2, "Wrong answer"))
                        self.game.advance_time(15)
                    return

            results = offline_process(self.game, cmd)
            for line in results:
                if line.startswith("[") and ("bytes" in line.lower() or "suspicion" in line.lower() or "acquired" in line.lower()):
                    self.add_msg("info", line)
                elif line.startswith("---"):
                    self.add_msg("bright", line)
                else:
                    self.add_msg("narrator", line)

        else:  # AI mode
            self.add_msg("system", "The narrator is composing...")

            self.conversation.append({"role": "user", "content": cmd})
            system = SYSTEM_PROMPT + f"\n\nCURRENT GAME STATE: {self.game.to_api_state()}"

            try:
                if self.mode == "claude":
                    raw = call_claude(self.api_key, self.conversation, system)
                else:
                    raw = call_openai(self.api_key, self.conversation, system)

                narrative, state = parse_ai_response(raw)
                self.conversation.append({"role": "assistant", "content": raw})

                # Remove "composing" message
                self.messages = [(t, m) for t, m in self.messages if m != "The narrator is composing..."]

                self.add_msg("narrator", narrative)

                if state:
                    self.game.bytes = state.get("bytes", self.game.bytes)
                    self.game.suspicion = state.get("suspicion", self.game.suspicion)
                    self.game.pto = state.get("pto", self.game.pto)
                    self.game.inventory = state.get("inventory", self.game.inventory)
                    self.game.game_over = state.get("gameOver", self.game.game_over)
                    self.game.ending = state.get("ending", self.game.ending) or ""
                    # Parse time
                    t = state.get("time", "")
                    if t:
                        try:
                            parts = t.replace("AM", "").replace("PM", "").strip().split(":")
                            h = int(parts[0])
                            m = int(parts[1]) if len(parts) > 1 else 0
                            if "PM" in t and h < 12: h += 12
                            if "AM" in t and h == 12: h = 0
                            self.game.hour = h
                            self.game.minute = m
                        except: pass
                    loc = state.get("location", "")
                    for k, v in ROOMS.items():
                        if v.lower() == loc.lower():
                            self.game.room = k
                            break

            except Exception as e:
                self.messages = [(t, m) for t, m in self.messages if m != "The narrator is composing..."]
                err_msg = sanitize_error(str(e)[:60], self.api_key)
                self.add_msg("error", f"API Error: {err_msg}")
                # Roll back conversation
                if self.conversation and self.conversation[-1]["role"] == "user":
                    self.conversation.pop()

    def run(self):
        """Main game loop."""
        # Boot sequence
        self.add_msg("system", "=" * 48)
        self.add_msg("bright", "  D.O.R.K. v2.0")
        self.add_msg("bright", "  Digital Operations Research Kollective")
        self.add_msg("system", '  "Synergizing Tomorrow\'s Solutions Today"')
        self.add_msg("system", "")
        self.add_msg("system", "  By Geoffrey Taber")
        self.add_msg("system", "  github.com/GeoxT | geox.blog")
        self.add_msg("system", "")
        self.add_msg("system", "  It is Monday. It is 1987. God help you.")
        self.add_msg("system", "=" * 48)
        self.add_msg("system", "Loading from 5.25 inch floppy...")
        self.add_msg("system", "Calibrating sarcasm module... [OK]")
        self.add_msg("system", f"Narrator mode: {self.mode.upper()}")
        if self.api_key:
            self.add_msg("system", f"API key: {mask_key(self.api_key)}")
            self.add_msg("system", "Type CLEARKEY to remove key. Key is memory-only.")
        else:
            self.add_msg("system", "Type APIKEY to connect an AI narrator anytime.")
        self.add_msg("system", "")

        # Start game
        if self.mode == "offline":
            self.add_msg("narrator", "You jolt awake. Your cheek is stuck to the desk with what you hope is just coffee. The fluorescent light above Cubicle 7B flickers with the enthusiasm of someone who has also been here since 1983.")
            self.add_msg("narrator", "Your VT220 terminal stares at you with a dead, black screen. The 'Hang In There' cat poster hangs by one pin.")
            self.add_msg("narrator", "You work at the Digital Operations Research Kollective. Yes, the acronym spells what you think. The founder was German. At least, that's what HR tells people.")
            self.add_msg("narrator", "The mainframe crashed overnight. Big Client Demo at 5:00 PM. Welcome to D.O.R.K.")
            self.add_msg("info", "Type HELP for commands. Type LOOK to examine your surroundings.")
        else:
            self.send_command("START GAME")

        while self.running:
            # Get terminal size
            max_y, max_x = self.scr.getmaxyx()

            if max_x < 60 or max_y < 15:
                self.scr.erase()
                self.scr.addstr(0, 0, "Terminal too small. Need 60x15 minimum.")
                self.scr.refresh()
                self.scr.getch()
                continue

            # Layout
            sidebar_w = min(24, max_x // 4)
            main_w = max_x - sidebar_w
            header_h = 1
            input_h = 2
            msg_h = max_y - header_h - input_h

            # Create windows
            header_win = curses.newwin(header_h, main_w, 0, 0)
            msg_win = curses.newwin(msg_h, main_w, header_h, 0)
            input_win = curses.newwin(input_h, main_w, header_h + msg_h, 0)
            sidebar_win = curses.newwin(max_y, sidebar_w, 0, main_w)

            # Draw
            self.draw_header(header_win)
            self.draw_messages(msg_win)
            self.draw_input(input_win)
            self.draw_sidebar(sidebar_win)
            curses.doupdate()

            # Input
            try:
                ch = self.scr.getch()
            except KeyboardInterrupt:
                self.running = False
                break

            if ch == curses.KEY_RESIZE:
                continue
            elif ch in (curses.KEY_ENTER, 10, 13):
                cmd = self.input_buf.strip()
                self.input_buf = ""
                if cmd:
                    self.send_command(cmd)

                    # Handle pending API key prompt (requires exiting curses briefly)
                    if hasattr(self, '_pending_key_prompt') and self._pending_key_prompt:
                        self._pending_key_prompt = False
                        curses.def_prog_mode()
                        curses.endwin()
                        print()
                        print("  Enter API key (Claude). Input is hidden:")
                        try:
                            new_key = getpass.getpass("  > ").strip()
                        except (EOFError, KeyboardInterrupt):
                            new_key = ""
                        if new_key:
                            self.api_key = new_key
                            self.mode = "claude"
                            print(f"  Key loaded: {mask_key(self.api_key)}")
                            print("  AI narrator enabled. Type CLEARKEY to remove.")
                        else:
                            print("  No key entered. Staying offline.")
                        time_mod.sleep(0.8)
                        curses.reset_prog_mode()
                        self.scr.clear()
                        self.scr.refresh()
                        if new_key:
                            self.add_msg("system", f"AI narrator enabled (Claude). Key: {mask_key(self.api_key)}")
                            self.add_msg("system", "Type CLEARKEY to remove. Type anything to play.")
                        continue

                    if self.game.game_over:
                        self.add_msg("system", "=" * 40)
                        self.add_msg("bright", f"  GAME OVER: {self.game.ending}")
                        self.add_msg("info", f"  Bytes: {self.game.bytes} | Suspicion: {self.game.suspicion}%")
                        self.add_msg("info", f"  Mainframe: {'FIXED' if self.game.mainframe_fixed else 'STILL DEAD'}")
                        self.add_msg("system", "=" * 40)
                        self.add_msg("system", "")
                        self.add_msg("system", "  By Geoffrey Taber")
                        self.add_msg("system", "  github.com/GeoxT | geox.blog")
                        self.add_msg("system", "")
                        self.add_msg("narrator", "Enjoyed D.O.R.K.? Buy the developer a floppy disk:")
                        self.add_msg("bright", "BTC: 13P6c6t4Y2ZFpb7tTYB9J1y4YEABXqPme3")
                        self.add_msg("system", "")
                        self.add_msg("system", "Press any key to exit...")

                        # Final draw
                        self.draw_header(header_win)
                        self.draw_messages(msg_win)
                        self.draw_input(input_win)
                        self.draw_sidebar(sidebar_win)
                        curses.doupdate()
                        self.scr.getch()
                        self.running = False
            elif ch == curses.KEY_BACKSPACE or ch == 127 or ch == 8:
                self.input_buf = self.input_buf[:-1]
            elif ch == 27:  # ESC
                self.running = False
            elif 32 <= ch <= 126:
                self.input_buf += chr(ch)

# ============================================================
# SETUP SCREEN (pre-curses)
# ============================================================

def setup():
    """Pre-curses setup: choose mode and enter API key."""
    os.system("cls" if os.name == "nt" else "clear")

    print()
    print("  ####   ###  ####  #  # ")
    print("  #   # #   # #   # # #  ")
    print("  #   # #   # ####  ##   ")
    print("  #   # #   # #  #  # #  ")
    print("  ####   ###  #   # #  # ")
    print()
    print("  D.O.R.K. v2.0 — A Text Adventure in Corporate America")
    print("  Digital Operations Research Kollective, 1987")
    print()
    print("  Developed by Geoffrey Taber")
    print("  github.com/GeoxT  |  geox.blog")
    print()
    print("  Like the game? Buy the developer a floppy disk:")
    print("  BTC: 13P6c6t4Y2ZFpb7tTYB9J1y4YEABXqPme3")
    print("  (Type DONATE anytime in-game)")
    print("  (Type APIKEY to add a key later, CLEARKEY to remove)")
    print()
    print("  Choose narrator mode:")
    print()
    print("  [1] OFFLINE — Classic text parser, no API needed")
    print("  [2] CLAUDE  — AI narrator powered by Anthropic Claude")
    print("  [3] OPENAI  — AI narrator powered by OpenAI GPT-4o")
    print()

    while True:
        choice = input("  Select (1/2/3): ").strip()
        if choice in ("1", "2", "3"):
            break
        print("  Please enter 1, 2, or 3.")

    mode = {"1": "offline", "2": "claude", "3": "openai"}[choice]
    api_key = ""

    if mode == "claude":
        print()
        print("  Enter your Anthropic API key (sk-ant-...):")
        print("  (Input is hidden for security)")
        try:
            api_key = getpass.getpass("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            api_key = ""
        if not api_key:
            print("  No key entered. Falling back to offline mode.")
            mode = "offline"
        else:
            print(f"  Key loaded: {mask_key(api_key)}")

    elif mode == "openai":
        print()
        print("  Enter your OpenAI API key (sk-...):")
        print("  (Input is hidden for security)")
        try:
            api_key = getpass.getpass("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            api_key = ""
        if not api_key:
            print("  No key entered. Falling back to offline mode.")
            mode = "offline"
        else:
            print(f"  Key loaded: {mask_key(api_key)}")

    if mode == "offline":
        print()
        print("  Offline mode selected. Full text parser, no API required.")
    else:
        print()
        print(f"  {mode.upper()} mode selected. AI narrator active.")

    print()
    print("  Launching terminal interface...")
    time_mod.sleep(1)

    return mode, api_key

# ============================================================
# MAIN
# ============================================================

def main():
    mode, api_key = setup()

    def curses_main(stdscr):
        ui = DorkUI(stdscr, mode, api_key)
        ui.run()

    curses.wrapper(curses_main)

    # Post-game
    print()
    print("Thanks for playing DORK v2.0")
    print('Digital Operations Research Kollective — "Synergizing Tomorrow\'s Solutions Today"')
    print()
    print("Developed by Geoffrey Taber")
    print("github.com/GeoxT  |  geox.blog")
    print()
    print("Enjoyed the game? Buy the developer a floppy disk:")
    print("BTC: 13P6c6t4Y2ZFpb7tTYB9J1y4YEABXqPme3")
    print()

if __name__ == "__main__":
    main()
