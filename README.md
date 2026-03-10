# jazz_chords
A Randomized Jazz Chord Generator

% python3 jazz_chords.py -h
usage: jazz_chords.py [-h] [-k KEY] [-s STYLE] [-b BARS] [-t TRITONE] [-n] [-g]

Jazz Chord Sequence Generator

options:
  -h, --help            show this help message and exit
  -k, --key KEY         Root key, e.g. C, Bb, F# (default: run demo)
  -s, --style STYLE     Progression style (default: random)
  -b, --bars BARS       Target length in bars (default: 16)
  -t, --tritone TRITONE
                        Tritone-sub probability 0–1 (default: 0.2)
  -n, --notes           Print chord tones
  -g, --guitar          Show ASCII guitar chord diagrams

styles: ii_V_I, iii_VI_ii_V_I, rhythm_changes, jazz_blues, minor_ii_V_i, modal_dorian, modal_mixolydian, random

examples:
  jazz_chords.py                           # run full demo
  jazz_chords.py -k Bb -s rhythm_changes   # Bb rhythm changes
  jazz_chords.py -k F  -s jazz_blues -b 12 # F blues, 12 bars
  jazz_chords.py -k C  -s ii_V_I  --guitar # ii-V-I with chord diagrams
  jazz_chords.py -k D  -s minor_ii_V_i -g  # minor ii-V-i with diagrams
  
