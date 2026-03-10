"""
jazz_chords.py — Jazz Chord Sequence Generator
David Johnston https://github.com/dj-on-github/jazz_chords

Generates realistic jazz chord progressions using common jazz harmony rules:
  - ii–V–I, iii–VI–ii–V–I, rhythm changes, blues, modal, tritone substitutions
  - Chord extensions: 7ths, 9ths, 11ths, 13ths, alterations (#11, b9, #9, b13)
  - Key transposition, output as lead-sheet symbols or Roman numerals
"""

import random
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Music fundamentals
# ---------------------------------------------------------------------------

NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
FLAT_TO_SHARP = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
SHARP_TO_FLAT = {v: k for k, v in FLAT_TO_SHARP.items()}
ENHARMONIC = {**FLAT_TO_SHARP, **SHARP_TO_FLAT}

# Intervals in semitones from root
CHORD_TYPES = {
    # Triads
    "":        [0, 4, 7],           # major
    "m":       [0, 3, 7],           # minor
    "dim":     [0, 3, 6],           # diminished
    "aug":     [0, 4, 8],           # augmented
    # Seventh chords
    "maj7":    [0, 4, 7, 11],       # major 7
    "7":       [0, 4, 7, 10],       # dominant 7
    "m7":      [0, 3, 7, 10],       # minor 7
    "m(maj7)": [0, 3, 7, 11],       # minor major 7
    "dim7":    [0, 3, 6, 9],        # diminished 7
    "m7b5":    [0, 3, 6, 10],       # half-diminished (ø7)
    "7sus4":   [0, 5, 7, 10],       # dominant sus4
    # Extended / jazz voicings (interval set is representative)
    "9":       [0, 4, 7, 10, 14],   # dominant 9
    "maj9":    [0, 4, 7, 11, 14],   # major 9
    "m9":      [0, 3, 7, 10, 14],   # minor 9
    "13":      [0, 4, 7, 10, 14, 21],  # dominant 13
    "maj13":   [0, 4, 7, 11, 14, 21],  # major 13
    "7#11":    [0, 4, 7, 10, 18],   # Lydian dominant
    "7b9":     [0, 4, 7, 10, 13],   # altered (b9)
    "7#9":     [0, 4, 7, 10, 15],   # altered (#9, "Hendrix")
    "7alt":    [0, 4, 7, 10, 13, 15, 20],  # fully altered
    "6":       [0, 4, 7, 9],        # major 6
    "m6":      [0, 3, 7, 9],        # minor 6
    "6/9":     [0, 4, 7, 9, 14],    # six-nine
}

# Scale degrees → semitones for major key
MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]

# Typical chord quality per scale degree in major (index 0 = I)
DIATONIC_QUALITY = ["maj7", "m7", "m7", "maj7", "7", "m7", "m7b5"]

def note_to_index(note: str) -> int:
    # Resolve flat spellings to sharp equivalents (NOTES uses sharps)
    note = FLAT_TO_SHARP.get(note, note)
    if note not in NOTES:
        raise ValueError(f"Unknown note: {note!r}")
    return NOTES.index(note)

def index_to_note(idx: int, prefer_flat: bool = False) -> str:
    note = NOTES[idx % 12]
    if prefer_flat and note in SHARP_TO_FLAT:
        return SHARP_TO_FLAT[note]
    return note

def transpose(note: str, semitones: int, prefer_flat: bool = False) -> str:
    return index_to_note(note_to_index(note) + semitones, prefer_flat)

def scale_note(key: str, degree: int, prefer_flat: bool = False) -> str:
    """Return the note for scale degree (0-based) in the given major key."""
    root_idx = note_to_index(key)
    return index_to_note(root_idx + MAJOR_SCALE[degree % 7], prefer_flat)


# ---------------------------------------------------------------------------
# Chord dataclass
# ---------------------------------------------------------------------------

@dataclass
class Chord:
    root: str
    quality: str
    bass: Optional[str] = None       # slash chord bass note
    duration: float = 1.0            # in bars

    def __str__(self) -> str:
        s = f"{self.root}{self.quality}"
        if self.bass:
            s += f"/{self.bass}"
        return s

    def notes(self) -> list[str]:
        root_idx = note_to_index(self.root)
        intervals = CHORD_TYPES.get(self.quality, [0, 4, 7])
        return [index_to_note(root_idx + i) for i in intervals]


# ---------------------------------------------------------------------------
# Progression builders
# ---------------------------------------------------------------------------

def use_flat_key(key: str) -> bool:
    """Determine whether to prefer flats for a given key center."""
    flat_keys = {"F", "Bb", "Eb", "Ab", "Db", "Gb"}
    return key in flat_keys

def ii_V_I(key: str, duration: float = 1.0, extended: bool = True) -> list[Chord]:
    """Classic ii–V–I in given key."""
    pf = use_flat_key(key)
    two   = scale_note(key, 1, pf)
    five  = scale_note(key, 4, pf)
    one   = scale_note(key, 0, pf)
    q2    = "m9" if extended else "m7"
    q5    = random.choice(["9", "13", "7#11", "7b9", "7alt"]) if extended else "7"
    q1    = random.choice(["maj9", "maj13", "6/9"]) if extended else "maj7"
    return [
        Chord(two,  q2,  duration=duration),
        Chord(five, q5,  duration=duration),
        Chord(one,  q1,  duration=duration),
    ]

def iii_VI_ii_V_I(key: str, extended: bool = True) -> list[Chord]:
    """iii–VI–ii–V–I turnaround."""
    pf = use_flat_key(key)
    three = scale_note(key, 2, pf)
    six   = scale_note(key, 5, pf)
    prog  = [Chord(three, "m7"), Chord(six, "7")] + ii_V_I(key, extended=extended)
    return prog

def tritone_sub(chord: Chord) -> Chord:
    """Replace a dominant chord with its tritone substitution."""
    if "7" not in chord.quality:
        return chord
    new_root = transpose(chord.root, 6)
    return Chord(new_root, chord.quality, duration=chord.duration)

def rhythm_changes(key: str, extended: bool = True) -> list[Chord]:
    """A-section of Rhythm Changes (I–VI–ii–V turnaround)."""
    pf = use_flat_key(key)
    one  = scale_note(key, 0, pf)
    six  = scale_note(key, 5, pf)
    two  = scale_note(key, 1, pf)
    five = scale_note(key, 4, pf)
    q1 = "6/9" if extended else "maj7"
    q6 = "7b9" if extended else "7"
    q2 = "m9"  if extended else "m7"
    q5 = "7#9" if extended else "7"
    return [
        Chord(one,  q1,  duration=1),
        Chord(six,  q6,  duration=1),
        Chord(two,  q2,  duration=1),
        Chord(five, q5,  duration=1),
    ]

def jazz_blues(key: str, extended: bool = True) -> list[Chord]:
    """12-bar jazz blues."""
    pf = use_flat_key(key)
    I   = scale_note(key, 0, pf)
    IV  = scale_note(key, 3, pf)
    V   = scale_note(key, 4, pf)
    ii  = scale_note(key, 1, pf)
    bVII = index_to_note(note_to_index(key) + 10, pf)

    def dom(n): return Chord(n, "9" if extended else "7")
    def m7(n):  return Chord(n, "m9" if extended else "m7")

    return [
        dom(I),  dom(IV), dom(I),  dom(I),
        dom(IV), dom(IV), dom(I),  dom(VI := scale_note(key, 5, pf)),
        m7(ii),  dom(V),  dom(I),  dom(V),
    ]

def modal_progression(mode: str = "dorian") -> list[Chord]:
    """Simple modal vamp / progression."""
    modal_presets = {
        "dorian":     [("D",  "m7"), ("G",   "7"),   ("D",  "m7"), ("E",  "m7b5")],
        "mixolydian": [("G",  "7"),  ("F",   "maj7"), ("C", "maj7"), ("G", "7")],
        "lydian":     [("F",  "maj7#11"), ("G", "maj7"), ("Em", "m7"), ("F", "maj7#11")],
        "phrygian":   [("E",  "m7"), ("F",   "maj7"), ("E", "m7"), ("F", "maj7")],
    }
    chords = modal_presets.get(mode, modal_presets["dorian"])
    return [Chord(r, q) for r, q in chords]

def minor_ii_V_i(key: str, extended: bool = True) -> list[Chord]:
    """Minor ii–V–i (half-dim → altered dominant → minor)."""
    pf = use_flat_key(key)
    two  = scale_note(key, 1, pf)   # iiø
    five = scale_note(key, 4, pf)   # V7alt
    one  = scale_note(key, 0, pf)   # i
    q5   = "7alt" if extended else "7b9"
    q1   = "m(maj7)" if extended else "m7"
    return [
        Chord(two,  "m7b5", duration=1),
        Chord(five, q5,     duration=1),
        Chord(one,  q1,     duration=1),
    ]


# ---------------------------------------------------------------------------
# Guitar chord diagrams
# ---------------------------------------------------------------------------
#
# All shapes are defined for C with root on the A (5th) string at fret 3.
# Each entry is [E, A, D, G, B, e] fret numbers; -1 = muted string.
# Transposition shifts every fretted note by (target_root_fret_A - 3).
#
#  Verified chord tones (C = A-string fret 3):
#  maj7    x-3-5-4-5-3  →  C G B E G          (R 5 Δ7 3 5)
#  7       x-3-5-3-5-3  →  C G Bb E G         (R 5 b7 3 5)
#  m7      x-3-5-3-4-3  →  C G Bb Eb G        (R 5 b7 b3 5)
#  m(maj7) x-3-5-4-4-3  →  C G B  Eb G        (R 5 Δ7 b3 5)
#  dim7    x-3-4-2-4-2  →  C Gb A  Eb Gb      (R b5 dim7 b3)
#  m7b5    x-3-4-3-4-x  →  C Gb Bb Eb         (R b5 b7 b3)
#  7sus4   x-3-5-3-6-3  →  C G Bb F  G        (R 5 b7 4 5)
#  9       x-3-2-3-3-3  →  C E Bb D  G        (R 3 b7 9 5)
#  maj9    x-3-5-4-5-5  →  C G B  E  A        (R 5 Δ7 3 13)
#  m9      x-3-5-3-4-5  →  C G Bb Eb A        (R 5 b7 b3 13)
#  13      x-3-2-3-3-5  →  C E Bb D  A        (R 3 b7 9 13)
#  maj13   x-3-5-4-5-5  →  C G B  E  A        (same as maj9 — conventional)
#  7#11    x-3-4-3-5-3  →  C F# Bb E  G       (R #11 b7 3 5)
#  7b9     x-3-2-3-2-3  →  C E Bb Db G        (R 3 b7 b9 5)
#  7#9     x-3-2-3-4-3  →  C E Bb D# G        (R 3 b7 #9 5)
#  7alt    x-3-4-3-5-4  →  C F# Bb E  Ab      (R b5 b7 3 b13)
#  6       x-3-2-2-1-x  →  C E  A  C          (R 3 6 R)
#  m6      x-3-1-2-4-x  →  C Eb A  Eb         (R b3 6 b3)
#  6/9     x-3-2-2-3-3  →  C E  A  D  G       (R 3 6 9 5)
#  ""      x-3-5-5-5-3  →  C G  C  E  G       (major barre)
#  m       x-3-5-5-4-3  →  C G  C  Eb G       (minor barre)
#  aug     x-3-6-5-5-4  →  C Ab C  E  Ab      (R aug5 R 3 aug5)

VOICINGS_C: dict[str, list[int]] = {
    "":        [-1, 3, 5, 5, 5,  3],  # major barre
    "m":       [-1, 3, 5, 5, 4,  3],  # minor barre
    "dim":     [-1, 3, 4, 5, 4, -1],  # diminished triad
    "aug":     [-1, 3, 6, 5, 5,  4],  # augmented
    "maj7":    [-1, 3, 5, 4, 5,  3],
    "7":       [-1, 3, 5, 3, 5,  3],
    "m7":      [-1, 3, 5, 3, 4,  3],
    "m(maj7)": [-1, 3, 5, 4, 4,  3],
    "dim7":    [-1, 3, 4, 2, 4,  2],
    "m7b5":    [-1, 3, 4, 3, 4, -1],
    "7sus4":   [-1, 3, 5, 3, 6,  3],
    "9":       [-1, 3, 2, 3, 3,  3],
    "maj9":    [-1, 3, 5, 4, 5,  5],
    "m9":      [-1, 3, 5, 3, 4,  5],
    "13":      [-1, 3, 2, 3, 3,  5],
    "maj13":   [-1, 3, 5, 4, 5,  5],
    "7#11":    [-1, 3, 4, 3, 5,  3],
    "7b9":     [-1, 3, 2, 3, 2,  3],
    "7#9":     [-1, 3, 2, 3, 4,  3],
    "7alt":    [-1, 3, 4, 3, 5,  4],
    "6":       [-1, 3, 2, 2, 1, -1],
    "m6":      [-1, 3, 1, 2, 4, -1],
    "6/9":     [-1, 3, 2, 2, 3,  3],
    "maj7#11": [-1, 3, 5, 4, 6,  3],
}

# For qualities not in VOICINGS_C, try these fallbacks
_QUALITY_FALLBACKS: dict[str, str] = {
    "maj7#11": "maj7",
}


def get_guitar_voicing(root: str, quality: str) -> list[int] | None:
    """
    Return a list of 6 fret numbers [E, A, D, G, B, e] for the given chord.
    -1 means mute that string.  Returns None if no voicing is available.
    """
    template = VOICINGS_C.get(quality)
    if template is None:
        fallback = _QUALITY_FALLBACKS.get(quality)
        template = VOICINGS_C.get(fallback) if fallback else None
    if template is None:
        return None

    # A-string root fret for any note:  A is at fret 0; add 12 for A/Bb/B
    # so that those roots land at frets 12/13/14 (upper octave) rather than 0/1/2.
    c_idx = note_to_index("C")          # 0
    r_idx = note_to_index(root)
    offset = (r_idx - c_idx) % 12      # 0–11; C→0, Db→1, D→2 … B→11
    if offset <= 2:                     # A (offset 9→ nope), actually: A=9, Bb=10, B=11
        pass                            # already fine — let's recompute
    # Recompute: how many semitones above C is this root?
    offset = (r_idx - c_idx) % 12      # in range 0–11
    # C at A-string fret 3; target root at fret (3 + offset).
    # For roots A(+9), Bb(+10), B(+11) that gives frets 12, 13, 14 — playable.
    # (offset <= 2 would give frets 3,4,5 which are fine too.)

    return [f + offset if f >= 0 else -1 for f in template]


# ── ASCII fretboard renderer ────────────────────────────────────────────────

_STRING_NAMES = ["E", "A", "D", "G", "B", "e"]
_N = 6          # number of strings
_ROWS = 4       # fret rows to display


def _fretboard_lines(name: str, frets: list[int]) -> list[str]:
    """Build the lines of an ASCII chord diagram."""
    lines: list[str] = []

    # Title
    lines.append(f"  {name}")

    # String-name header — must align with grid cells
    # Grid row looks like:  │X│X│X│X│X│X│  (13 chars)
    # Cells sit at positions 1,3,5,7,9,11 inside the row string.
    # With "   " prefix, cells are at absolute cols 4,6,8,10,12,14.
    # Header "   " + "E A D G B e" puts E at col 3 — one off.
    # Use 4-space prefix so E aligns at col 4:  "    E A D G B e"
    lines.append("    " + " ".join(_STRING_NAMES))

    # Muted / open row above the grid
    indicators = [
        "×" if f == -1 else ("○" if f == 0 else " ")
        for f in frets
    ]
    lines.append("    " + " ".join(indicators))

    fretted = [f for f in frets if f > 0]
    if not fretted:
        return lines

    lo = min(fretted)
    hi = max(fretted)
    n_rows = max(_ROWS, hi - lo + 1)

    if lo > 9:
        pos_tag = f" ← {lo}fr"
    elif lo>1:
        pos_tag = f"  ← {lo}fr"
    else:
        pos_tag = ""
    
    #pos_tag = f"  ← {lo}fr" if lo > 1 else ""

    # Border characters
    if lo == 1:   # nut
        top_b = "  ╔" + "═╦" * (_N - 1) + "═╗"
    else:
        top_b = "  ┌" + "─┬" * (_N - 1) + "─┐" + pos_tag
    mid_b = "  ├" + "─┼" * (_N - 1) + "─┤"
    bot_b = "  └" + "─┴" * (_N - 1) + "─┘"

    lines.append(top_b)
    for i in range(n_rows):
        fn = lo + i
        cells = ["●" if f == fn else " " for f in frets]
        lines.append("  │" + "│".join(cells) + "│")
        if i < n_rows - 1:
            lines.append(mid_b)
    lines.append(bot_b)

    return lines


def render_chord_diagram(chord: "Chord") -> str:
    """Return an ASCII chord diagram string, or a fallback message."""
    frets = get_guitar_voicing(chord.root, chord.quality)
    if frets is None:
        return f"  {chord}  (no guitar voicing available)\n"
    return "\n".join(_fretboard_lines(str(chord), frets)) + "\n"


def print_guitar_diagrams(seq: list["Chord"]) -> None:
    """Print guitar chord diagrams for a sequence, de-duplicating by chord name."""
    seen: set[str] = set()
    diagrams: list[str] = []
    for chord in seq:
        key = str(chord)
        if key not in seen:
            seen.add(key)
            diagrams.append(render_chord_diagram(chord))

    # Print in rows of 4 diagrams
    cols = 4
    # Each diagram is a block of lines; collect them, then print side-by-side
    _print_diagrams_grid(diagrams, cols)


def _diagram_to_lines(diagram_str: str) -> list[str]:
    return diagram_str.rstrip("\n").split("\n")


def _print_diagrams_grid(diagrams: list[str], cols: int = 4) -> None:
    """Lay out chord diagrams in a grid, cols per row."""
    col_width = 22   # characters wide per diagram column

    all_blocks = [_diagram_to_lines(d) for d in diagrams]

    print()
    for chunk_start in range(0, len(all_blocks), cols):
        chunk = all_blocks[chunk_start: chunk_start + cols]
        max_h = max(len(b) for b in chunk)
        # Pad each block to the same height
        padded = [b + [""] * (max_h - len(b)) for b in chunk]
        for row_idx in range(max_h):
            row_parts = [f"{padded[c][row_idx]:<{col_width}}" for c in range(len(chunk))]
            print("".join(row_parts))
        print()



# ---------------------------------------------------------------------------
# Full sequence generator
# ---------------------------------------------------------------------------

PROGRESSION_TYPES = [
    "ii_V_I",
    "iii_VI_ii_V_I",
    "rhythm_changes",
    "jazz_blues",
    "minor_ii_V_i",
    "modal_dorian",
    "modal_mixolydian",
]

def generate_sequence(
    key: str = "C",
    style: str = "random",
    bars: int = 16,
    extended: bool = True,
    tritone_prob: float = 0.15,
) -> list[Chord]:
    """
    Generate a jazz chord sequence.

    Args:
        key:          Root key (e.g. "C", "Bb", "F#")
        style:        One of PROGRESSION_TYPES, or "random"
        bars:         Target length in bars (approximate)
        extended:     Use 9ths, 11ths, 13ths, alterations
        tritone_prob: Probability of applying tritone substitution to dominants

    Returns:
        List of Chord objects.
    """
    if style == "random":
        style = random.choice(PROGRESSION_TYPES)

    # Build a unit progression
    if style == "ii_V_I":
        unit = ii_V_I(key, extended=extended)
    elif style == "iii_VI_ii_V_I":
        unit = iii_VI_ii_V_I(key, extended=extended)
    elif style == "rhythm_changes":
        unit = rhythm_changes(key, extended=extended)
    elif style == "jazz_blues":
        return _apply_tritone(jazz_blues(key, extended=extended), tritone_prob)
    elif style == "minor_ii_V_i":
        unit = minor_ii_V_i(key, extended=extended)
    elif style == "modal_dorian":
        unit = modal_progression("dorian")
    elif style == "modal_mixolydian":
        unit = modal_progression("mixolydian")
    else:
        unit = ii_V_I(key, extended=extended)

    # Repeat / pad to reach target bar count
    sequence = []
    total = 0.0
    while total < bars:
        sequence.extend(unit)
        total += sum(c.duration for c in unit)

    # Trim excess
    trimmed, total = [], 0.0
    for c in sequence:
        if total >= bars:
            break
        trimmed.append(c)
        total += c.duration
    sequence = trimmed

    return _apply_tritone(sequence, tritone_prob)

def _apply_tritone(sequence: list[Chord], prob: float) -> list[Chord]:
    return [tritone_sub(c) if "7" in c.quality and random.random() < prob else c
            for c in sequence]


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def print_sequence(seq: list[Chord], title: str = "Jazz Chord Sequence", guitar: bool = False) -> None:
    bar = 1
    print(f"\n{'─' * 52}")
    print(f"  {title}")
    print(f"{'─' * 52}")
    for chord in seq:
        dur = f"({chord.duration:.0f} bar{'s' if chord.duration != 1 else ''})"
        print(f"  Bar {bar:>2}  │  {str(chord):<16} {dur}")
        bar += int(chord.duration)
    print(f"{'─' * 52}\n")
    if guitar:
        print_guitar_diagrams(seq)
    else:
        print("GUITAR NOT SET")

def print_notes(seq: list[Chord]) -> None:
    print("  Notes in each chord:")
    for chord in seq:
        ns = ", ".join(chord.notes())
        print(f"    {str(chord):<18} → {ns}")
    print()


# ---------------------------------------------------------------------------
# Demo / CLI
# ---------------------------------------------------------------------------

def demo(guitar) -> None:
    examples = [
        dict(key="C",  style="ii_V_I",          bars=8,  title="ii–V–I in C (8 bars)"),
        dict(key="F",  style="iii_VI_ii_V_I",   bars=10, title="iii–VI–ii–V–I in F"),
        dict(key="Bb", style="rhythm_changes",  bars=8,  title="Rhythm Changes A-section in Bb"),
        dict(key="G",  style="jazz_blues",      bars=12, title="Jazz Blues in G (12 bars)"),
        dict(key="D",  style="minor_ii_V_i",    bars=6,  title="Minor ii–V–i in D minor"),
        dict(key="C",  style="modal_dorian",    bars=8,  title="Dorian Modal Vamp"),
        dict(key="C",  style="random",          bars=16, title="Random Extended Progression (16 bars)"),
    ]

    for ex in examples:
        seq = generate_sequence(
            key=ex["key"],
            style=ex["style"],
            bars=ex["bars"],
            extended=True,
            tritone_prob=0.2,
        )
        print_sequence(seq, title=ex["title"],guitar=guitar)

    # Show chord tones for the last sequence
    print_notes(seq)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Jazz Chord Sequence Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
styles: {', '.join(PROGRESSION_TYPES + ['random'])}

examples:
  %(prog)s                           # run full demo
  %(prog)s -k Bb -s rhythm_changes   # Bb rhythm changes
  %(prog)s -k F  -s jazz_blues -b 12 # F blues, 12 bars
  %(prog)s -k C  -s ii_V_I  --guitar # ii-V-I with chord diagrams
  %(prog)s -k D  -s minor_ii_V_i -g  # minor ii-V-i with diagrams
""")
    parser.add_argument("-k", "--key",    default=None,     help="Root key, e.g. C, Bb, F# (default: run demo)")
    parser.add_argument("-s", "--style",  default="random", help="Progression style (default: random)")
    parser.add_argument("-b", "--bars",   default=16, type=int, help="Target length in bars (default: 16)")
    parser.add_argument("-t", "--tritone",default=0.2, type=float, help="Tritone-sub probability 0–1 (default: 0.2)")
    parser.add_argument("-n", "--notes",  action="store_true", help="Print chord tones")
    parser.add_argument("-g", "--guitar", action="store_true", help="Show ASCII guitar chord diagrams")

    args = parser.parse_args()

    if args.key is None:
        demo(guitar=args.guitar)
    else:
        seq = generate_sequence(
            key=args.key, style=args.style, bars=args.bars,
            extended=True, tritone_prob=args.tritone,
        )

        print_sequence(seq, title=f"{args.style} in {args.key} ({args.bars} bars)", guitar=args.guitar)
        if args.notes:
            print_notes(seq)
