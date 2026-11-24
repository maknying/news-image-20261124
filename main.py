#!/usr/bin/env python3
"""The World in One Page — Tuesday 24 November 2026.

Draws a single-page newspaper front page (1024x1024 PNG) summing up
the world's news of 24 November 2026: 45 real, source-checked stories
in 7 regions, with a masthead, a lead story (Jensen Huang's return
to Nvidia and the market surge it set off), four columns, a
day-in-numbers band and a source line.

Standard library only. All glyphs come from the pre-rendered atlas
(atlas.bin, built by build_atlas.py from DejaVu fonts), so the
program needs no network and no installed fonts at run time. Two
runs write byte-identical PNG files.

Usage:  python3 main.py            # writes out/entry.png
        MAKEFUN_OUTPUT_DIR=/output python3 main.py
"""

import binascii
import hashlib
import math
import os
import struct
import sys
import zlib

# ------------------------------------------------------------ geometry
PAGE_W = 1024
PAGE_H = 1024
MARGIN = 36
CONTENT = PAGE_W - 2 * MARGIN          # 952
COLUMNS = 4
COL_W = 229
COL_GAP = 12
TOP = 262
BOTTOM = 970

PAPER = (247, 243, 232)
INK = (24, 24, 24)
RED = (139, 26, 26)
RULE = (178, 168, 148)

# Face ids match build_atlas.py.
MASTHEAD = 0   # serif bold 44
LEAD = 1       # serif bold 26
DECK = 2       # serif 13
HEAD = 3       # serif bold 13
SECTION = 4    # sans bold 11
BODY = 5       # sans 10
FOOT = 6       # sans 9
DATE = 7       # sans bold 10

# ------------------------------------------------------------ the news
# (section, headline, summary). The lead story sits apart, below.
ITEMS = [
    ("MIDDLE EAST",
     "Trump dares Iran to test blockade",
     "Iranian ships testing the blockade will end up 'at the bottom "
     "of the sea', Trump warns."),
    ("MIDDLE EAST",
     "14 Iranian tankers mass near Kharg",
     "Tankers gather at Iran's main export terminal as Tehran "
     "threatens to test the blockade."),
    ("MIDDLE EAST",
     "Israeli strike kills 3 in Gaza",
     "A strike hits a food truck in Gaza City's Tel al-Hawa; Israel "
     "says it hit militants."),
    ("MIDDLE EAST",
     "Iran unveils dual-missile launcher",
     "State TV shows a new underground site able to fire two "
     "liquid-fuelled missiles."),
    ("MIDDLE EAST",
     "Qatar mediates in US-Iran standoff",
     "A Qatari delegation reaches Tehran to mediate as blockade "
     "tensions rise."),
    ("MIDDLE EAST",
     "Gaza contamination 'toxic for decades'",
     "An Oxfam report finds Gaza's air, soil and water dangerously "
     "contaminated for decades."),
    ("EUROPE",
     "Denmark court backs 'ghetto law'",
     "The top court upholds ending 91 leases in Helsingor to avoid "
     "a 'hard ghetto' label."),
    ("EUROPE",
     "UN 'killer robot' talks end empty",
     "Geneva talks end with no binding treaty; states agree to two "
     "more years of work."),
    ("EUROPE",
     "SpaceX curbs 'dented trust', UK says",
     "Limits on SpaceX use by Ukraine's military have damaged trust "
     "in Europe, London says."),
    ("EUROPE",
     "V4 reject EU budget cut plan",
     "The Visegrad Four dismiss the proposed EU budget cut and urge "
     "an ETS delay."),
    ("EUROPE",
     "Search for 'lion' loose near Istanbul",
     "A large-scale search is launched for a lion reported on the "
     "loose near Istanbul."),
    ("EUROPE",
     "Dutch activist dies by euthanasia, 28",
     "Jason Bhugwandass dies by euthanasia at 28 after years of "
     "health struggles."),
    ("RUSSIA & UKRAINE",
     "Zelensky claims Libya ship sinking",
     "Kyiv says seven sea drones sank the corvette Merkury in "
     "Benghazi and hit MV Angara."),
    ("RUSSIA & UKRAINE",
     "15 killed in strikes near Kyiv",
     "Eleven die in flats in Dymer and three at a Vyshneve "
     "supermarket; five hurt in Kyiv."),
    ("RUSSIA & UKRAINE",
     "Russian missiles fell in Poland",
     "Three Kh-101 cruise missiles came down in Polish fields on "
     "20 Nov; NATO meets Monday."),
    ("RUSSIA & UKRAINE",
     "15 ships targeted off Nato states",
     "Suspected Russian drones have targeted 15 merchant ships off "
     "Bulgaria and Romania."),
    ("RUSSIA & UKRAINE",
     "Sparta II towed from Finnish waters",
     "The drone-struck cargo ship is towed out; her 16 crew are "
     "safe, one slightly hurt."),
    ("THE AMERICAS",
     "Trump halts Iowa explosives blast",
     "The lead-azide blast waits for the court and Governor-elect "
     "Rob Sand to agree."),
    ("THE AMERICAS",
     "Thanksgiving travel dips; fares +17%",
     "AAA sees 81.5m travellers; 5.96m will fly, with fares "
     "averaging $800 return."),
    ("THE AMERICAS",
     "O'Hare brief ground stop",
     "Chicago O'Hare halts departures 10:40 to 12:15 over a "
     "staffing shortage."),
    ("THE AMERICAS",
     "Trump attacks Newsom over 548 cases",
     "Trump targets the governor in a DOJ speech over 548 death "
     "sentences commuted."),
    ("THE AMERICAS",
     "Court gives Trump hush-money path",
     "A federal appeals court gives Trump a path to erasing his "
     "hush-money conviction."),
    ("THE AMERICAS",
     "FBI raids Minnesota child centres",
     "Federal agents raid child centres in Minnesota in a $41m "
     "fraud probe."),
    ("THE AMERICAS",
     "Ex-Jackson mayor jailed 37 months",
     "The ex-mayor pleads guilty in a hotel bribery scheme and "
     "must forfeit $50,000."),
    ("ASIA-PACIFIC",
     "Indonesia fire: 26 body bags found",
     "Rescuers recover 26 bags of remains in Cikande; 30 workers "
     "are still missing."),
    ("ASIA-PACIFIC",
     "Prabowo names two VP nominees",
     "Amran Sulaiman and Sugiono are put forward to replace Gibran; "
     "the MPR votes 11 Dec."),
    ("ASIA-PACIFIC",
     "Indonesia seizes missile-chemical ship",
     "The navy seizes MV Star Line with 405 tonnes of sodium "
     "perchlorate, enough for 100 missiles."),
    ("ASIA-PACIFIC",
     "EU-Indonesia sign landmark trade deal",
     "The deal eliminates nearly all tariffs on goods traded "
     "between the EU and Indonesia."),
    ("ASIA-PACIFIC",
     "Modi, Shah flag off Saryu-Kamala train",
     "The new express links Ayodhya with Janakpur Dham in Nepal."),
    ("ASIA-PACIFIC",
     "India-NZ Test ends in a draw",
     "New Zealand finish 239/5 in Wellington as Mitchell and "
     "Phillips bat out 43 overs."),
    ("ASIA-PACIFIC",
     "Gukesh defends chess crown in Geneva",
     "World champion Gukesh begins his title defence against "
     "Javokhir Sindarov today."),
    ("ASIA-PACIFIC",
     "India, China hold border talks",
     "Military commanders meet in Arunachal Pradesh to manage "
     "border tensions."),
    ("ASIA-PACIFIC",
     "Lahore tops world pollution ranking",
     "Lahore's AQI crosses 500, with eight Pakistan cities among "
     "the world's worst."),
    ("MARKETS, TECH & SPORT",
     "Nvidia China sales tripled to $11.05bn",
     "China revenue jumps from $2.97bn, but some customers now "
     "cancel orders amid the scandal."),
    ("MARKETS, TECH & SPORT",
     "Bitcoin back above $61,000",
     "Bitcoin rebounds from a Saturday low of $55,130; ETFs have "
     "lost nearly $3bn in November."),
    ("MARKETS, TECH & SPORT",
     "Alcaraz wins maiden ATP Finals",
     "Alcaraz beats world No. 1 Zverev 6-2, 7-6(7) in Turin on "
     "Sunday for his first title."),
    ("MARKETS, TECH & SPORT",
     "England beat All Blacks 37-12",
     "England defeat New Zealand 37-12 at Allianz Stadium on "
     "21 Nov."),
    ("MARKETS, TECH & SPORT",
     "Anthropic shares fall on Nvidia day",
     "Anthropic falls on Monday as Nvidia surges on Huang's "
     "return to the top job."),
    ("MARKETS, TECH & SPORT",
     "Kansas City win first NWSL title",
     "Kansas City Current beat Washington Spirit 2-1 to win their "
     "first championship."),
    ("AFRICA & SCIENCE",
     "64 killed in Nigeria's Niger state",
     "Fulani groups say 64 died in weekend attacks near Wawa; "
     "Reuters could not verify the toll."),
    ("AFRICA & SCIENCE",
     "Ebola toll: 11,613 cases, 5,678 deaths",
     "WHO counts 11,613 Ebola cases in DR Congo; the outbreak "
     "remains a global emergency."),
    ("AFRICA & SCIENCE",
     "Fighting traps Ebola responders",
     "Clashes near an Ituri hospital force health workers to "
     "shelter in a maternity ward."),
    ("AFRICA & SCIENCE",
     "COP31 flop sparks Bowen backlash",
     "Calls grow for minister Chris Bowen to quit after COP31 ends "
     "with no final deal."),
    ("AFRICA & SCIENCE",
     "Tiny flying frog found in Indonesia",
     "A tiny new species of Asian flying frog is found in a remote "
     "part of Indonesia."),
]

LEAD_TAG = "LEAD \u2014 NEW YORK \u2022 MARKETS"
LEAD_HEAD = "Huang is back: Nvidia soars 31.5%"
LEAD_DECK = ("Nvidia's board unanimously reinstates Jensen Huang as "
             "chief executive, less than two weeks after he resigned. "
             "Shares jump 31.5%, the Nasdaq gains 6.5% and the Dow "
             "rises 1,448 points.")

TITLE = "THE WORLD IN ONE PAGE"
DATE_LEFT = "TUESDAY, 24 NOVEMBER 2026"
DATE_RIGHT = "45 STORIES \u2022 7 REGIONS"

NUMBERS = ("THE DAY IN NUMBERS \u2014 +31.5% Nvidia \u2022 +6.5% "
           "Nasdaq \u2022 26 body bags in Banten \u2022 64 killed in "
           "Niger State \u2022 11,613 Ebola cases")

FOOT_LEFT = ("Sources: Reuters \u2022 AP \u2022 The Times \u2022 Fox "
             "News \u2022 CoinDesk \u2022 ANTARA \u2022 WHO \u2022 "
             "Investors.com \u2022 NDTV")
FOOT_RIGHT = "Compiled 24 Nov 2026 \u2022 No. 46"


# ------------------------------------------------------------ atlas
# Format written by build_atlas.py (magic ATLS0003):
#   header, face table, glyph table, pixel blob.
_GLYPH = struct.Struct("<IhhHHHHII")
_FACE = struct.Struct("<IIHHI")


class Atlas:
    """Glyph bitmaps loaded from atlas.bin."""

    def __init__(self, path):
        with open(path, "rb") as fh:
            raw = fh.read()
        if raw[:8] != b"ATLS0003":
            raise ValueError("bad atlas magic")
        pos = 8
        (nfaces,) = struct.unpack_from("<I", raw, pos)
        pos += 4
        self.faces = {}
        self.glyphs = {}
        counts = []
        for _ in range(nfaces):
            fid, size, asc, desc, count = _FACE.unpack_from(raw, pos)
            pos += _FACE.size
            self.faces[fid] = (size, asc, desc)
            counts.append(count)
        rows = []
        for count in counts:
            for _ in range(count):
                rows.append(_GLYPH.unpack_from(raw, pos))
                pos += _GLYPH.size
        blob0 = pos
        for fid, cp, left, top, adv, w, h, off, ln in rows:
            self.glyphs[(fid, cp)] = (
                left, top, adv, w, h,
                raw[blob0 + off: blob0 + off + ln])

    def glyph(self, face, ch):
        got = self.glyphs.get((face, ord(ch)))
        if got is None:
            got = self.glyphs.get((face, ord("?")))
        return got

    def width(self, face, text):
        return sum(self.glyph(face, ch)[2] for ch in text)

    def wrap(self, face, text, max_w, cap=None):
        """Greedy word wrap, with an optional line cap + ellipsis."""
        lines = []
        cur = ""
        for word in text.split(" "):
            trial = word if not cur else cur + " " + word
            if self.width(face, trial) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        out = []
        for line in lines:
            while self.width(face, line) > max_w and len(line) > 1:
                cut = len(line) - 1
                while cut > 0 and self.width(face, line[:cut]) > max_w:
                    cut -= 1
                out.append(line[:max(cut, 1)])
                line = line[max(cut, 1):]
            out.append(line)
        lines = out
        if cap is not None and len(lines) > cap:
            lines = lines[:cap]
            tail = lines[-1]
            while tail and self.width(face, tail + "\u2026") > max_w:
                tail = tail[:-1]
            lines[-1] = tail + "\u2026"
        return lines


# ------------------------------------------------------------ canvas
class Sheet:
    """An RGB pixel buffer with text and rule drawing."""

    def __init__(self, atlas):
        self.atlas = atlas
        self.buf = bytearray(PAPER * (PAGE_W * PAGE_H))

    def put(self, x, y, color, alpha=255):
        if 0 <= x < PAGE_W and 0 <= y < PAGE_H:
            i = (y * PAGE_W + x) * 3
            if alpha >= 255:
                self.buf[i:i + 3] = bytes(color)
            elif alpha:
                for c in range(3):
                    base = self.buf[i + c]
                    self.buf[i + c] = (color[c] * alpha
                                       + base * (255 - alpha)) // 255

    def fill(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(PAGE_W, x + w), min(PAGE_H, y + h)
        for yy in range(y0, y1):
            base = (yy * PAGE_W + x0) * 3
            self.buf[base:base + (x1 - x0) * 3] = bytes(color) * (x1 - x0)

    def hrule(self, x, y, w, color, thick=1):
        self.fill(x, y, w, thick, color)

    def vrule(self, x, y, h, color, thick=1):
        self.fill(x, y, thick, h, color)

    def text(self, x, y_top, face, s, color=INK):
        """Draw text with its ascender top at y_top; return end x."""
        cx = x
        for ch in s:
            left, top, adv, w, h, data = self.atlas.glyph(face, ch)
            if w and h:
                gx, gy = cx + left, y_top + top
                for row in range(h):
                    src = row * w
                    for col in range(w):
                        a = data[src + col]
                        if a:
                            self.put(gx + col, gy + row, color, a)
            cx += adv
        return cx

    def lines(self, x, y_top, face, wrapped, leading, color=INK):
        y = y_top
        for line in wrapped:
            self.text(x, y, face, line, color)
            y += leading
        return y

    def globe(self, cx, cy, r, color=INK):
        """Small line globe: circle, two meridians, three parallels."""
        def dot(px, py):
            self.put(px, py, color)
            self.put(px + 1, py, color)
        for i in range(720):
            t = 2.0 * math.pi * i / 720
            s, c = math.sin(t), math.cos(t)
            dot(int(cx + r * c), int(cy + r * s))
            dot(int(cx + r * 0.45 * c), int(cy + r * s))
            dot(int(cx + r * 0.8 * c), int(cy + r * s))
            for fy, fr in ((-0.55, 0.83), (0.0, 1.0), (0.55, 0.83)):
                dot(int(cx + r * fr * c), int(cy + r * fy + r * 0.22 * s))


# ------------------------------------------------------------ layout
def measure(atlas):
    """Wrap every story once; return (blocks, total height)."""
    blocks = []
    seen = None
    for section, head, summ in ITEMS:
        h_lines = atlas.wrap(HEAD, head, COL_W, cap=2)
        s_lines = atlas.wrap(BODY, summ, COL_W, cap=2)
        header = 20 if section != seen else 0
        seen = section
        height = header + 14 * len(h_lines) + 12 * len(s_lines) + 8
        blocks.append((section, header, h_lines, s_lines, height))
    return blocks, sum(b[4] for b in blocks)


def split_columns(blocks, total):
    """Balanced partition into 4 columns, minimising the tallest one.

    best[i][k] = smallest possible tallest column when the first i
    blocks are split into k columns; cut[i][k] remembers the split.
    """
    n = len(blocks)
    body_h = BOTTOM - TOP
    big = 10 ** 9
    best = [[big] * (COLUMNS + 1) for _ in range(n + 1)]
    cut = [[0] * (COLUMNS + 1) for _ in range(n + 1)]
    best[0][0] = 0
    for i in range(1, n + 1):
        for k in range(1, COLUMNS + 1):
            run = 0
            for j in range(i - 1, -1, -1):
                run += blocks[j][4]
                if run > body_h:
                    break
                cand = max(best[j][k - 1], run)
                if cand < best[i][k]:
                    best[i][k] = cand
                    cut[i][k] = j
    if best[n][COLUMNS] > body_h:
        raise SystemExit("OVERFLOW: stories do not fit in 4 columns")
    cuts = []
    i, k = n, COLUMNS
    while k > 0:
        j = cut[i][k]
        cuts.append(j)
        i, k = j, k - 1
    cuts.reverse()
    cuts.append(n)
    return cuts


def draw(sheet):
    at = sheet.atlas
    # --- masthead
    w = at.width(MASTHEAD, TITLE)
    sheet.text((PAGE_W - w) // 2, 20, MASTHEAD, TITLE)
    sheet.text(MARGIN, 82, DATE, DATE_LEFT)
    rw = at.width(DATE, DATE_RIGHT)
    sheet.text(PAGE_W - MARGIN - rw, 82, DATE, DATE_RIGHT)
    sheet.hrule(MARGIN, 100, CONTENT, INK, 2)
    sheet.hrule(MARGIN, 104, CONTENT, INK, 1)

    # --- lead story, globe on the right
    sheet.text(MARGIN, 114, SECTION, LEAD_TAG, RED)
    y = sheet.lines(MARGIN, 134, LEAD,
                    at.wrap(LEAD, LEAD_HEAD, 720, cap=2), 33)
    y = sheet.lines(MARGIN, y + 6, DECK,
                    at.wrap(DECK, LEAD_DECK, 720, cap=3), 17)
    sheet.globe(874, 176, 52)
    cap = "THE WORLD \u2014 24 NOV 2026"
    cw = at.width(FOOT, cap)
    sheet.text(874 - cw // 2, 236, FOOT, cap)
    sheet.hrule(MARGIN, 254, CONTENT, INK, 2)

    # --- column rules
    for c in range(1, COLUMNS):
        gx = MARGIN + c * COL_W + (c - 1) * COL_GAP + COL_GAP // 2
        sheet.vrule(gx, TOP, BOTTOM - TOP, RULE)

    # --- story columns
    blocks, total = measure(at)
    cuts = split_columns(blocks, total)
    counts = []
    for col in range(COLUMNS):
        x = MARGIN + col * (COL_W + COL_GAP)
        y = TOP
        n = 0
        for section, header, h_lines, s_lines, _h in \
                blocks[cuts[col]:cuts[col + 1]]:
            if header:
                sheet.text(x, y, SECTION, section, RED)
                sheet.hrule(x, y + 14, COL_W, INK, 1)
                y += header
            y = sheet.lines(x, y, HEAD, h_lines, 14)
            y = sheet.lines(x, y, BODY, s_lines, 12)
            y += 8
            n += 1
            if y > BOTTOM:
                raise SystemExit("OVERFLOW: column %d past body" % col)
        counts.append(n)

    # --- numbers band + footer
    sheet.hrule(MARGIN, 978, CONTENT, INK, 1)
    nw = at.width(SECTION, NUMBERS)
    sheet.text((PAGE_W - nw) // 2, 984, SECTION, NUMBERS)
    sheet.hrule(MARGIN, 1002, CONTENT, INK, 1)
    sheet.text(MARGIN, 1008, FOOT, FOOT_LEFT)
    fw = at.width(FOOT, FOOT_RIGHT)
    sheet.text(PAGE_W - MARGIN - fw, 1008, FOOT, FOOT_RIGHT)
    return counts


# ------------------------------------------------------------ png out
def chunk(tag, data):
    out = struct.pack(">I", len(data)) + tag + data
    out += struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)
    return out


def encode_png(sheet):
    raw = bytearray()
    for row in range(PAGE_H):
        raw.append(0)
        raw += sheet.buf[row * PAGE_W * 3:(row + 1) * PAGE_W * 3]
    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png += chunk(b"IHDR",
                 struct.pack(">IIBBBBB", PAGE_W, PAGE_H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return bytes(png)


def run():
    here = os.path.dirname(os.path.abspath(__file__))
    atlas = Atlas(os.path.join(here, "atlas.bin"))
    sheet = Sheet(atlas)
    counts = draw(sheet)
    png = encode_png(sheet)
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not outdir:
        outdir = "/output" if os.path.isdir("/output") else "out"
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(png)
    print("wrote %s (%d bytes, sha256 %s)"
          % (path, len(png), hashlib.sha256(png).hexdigest()))
    print("stories=%d columns=%s" % (len(ITEMS) + 1, counts))
    return 0


if __name__ == "__main__":
    sys.exit(run())
