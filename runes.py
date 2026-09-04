"""The mapping. Single source of truth for every generated layout.

ONE system: medieval Norwegian runes, c. 1100-1400. Nothing from Elder
Futhark and nothing from the Anglo-Saxon futhorc, which are different
traditions separated from medieval Norway by centuries and a sea.

Level 1 is a strict 1:1 over the 29-letter Norwegian alphabet, so the
mapping is fully reversible. It is a cipher of Norwegian *spelling*, not
of Norwegian *sound* -- silent letters survive, clusters are not
collapsed. A medieval scribe would have written what they heard.

Level 2 (shift) is deliberately NOT a second runic alphabet. Runes have
no case, and an earlier version filled the shift level with Younger
Futhark and Anglo-Saxon variant forms -- which made the layout two
character sets at once and much harder to learn. Shift now gives the
plain Latin letter, so a name or a URL can be typed without leaving the
layout. Only the three word-dividers stay runic, on , . and -

Every key is identified in four coordinate systems, since each platform
names the same physical key differently:

    xkb  -- X11/Wayland key name        (Linux)
    mac  -- Apple virtual key code      (macOS .keylayout)
    sc   -- PS/2 set-1 scan code, hex   (Windows .klc and AutoHotkey)
    vk   -- Windows virtual key name    (Windows .klc)

Positions are for a Norwegian pc105 keyboard, which is why æ ø å sit on
the keys a Norwegian already presses for them.
"""

LAYOUT_NAME = "Norwegian (medieval runic)"
SHORT_NAME = "runic"

# latin, rune, xkb, mac, sc, vk, rune name (Norwegian, for the cheat sheet)
KEYS = [
    ("q", "ᛩ", "AD01", 12, "10", "Q",     "q — seinmiddelaldersk tillegg"),
    ("w", "ᚥ", "AD02", 13, "11", "W",     "w — seinmiddelaldersk tillegg"),
    ("e", "ᛂ", "AD03", 14, "12", "E",     "prikket íss"),
    ("r", "ᚱ", "AD04", 15, "13", "R",     "reið"),
    ("t", "ᛏ", "AD05", 17, "14", "T",     "týr"),
    ("y", "ᚤ", "AD06", 16, "15", "Y",     "prikket úr"),
    ("u", "ᚢ", "AD07", 32, "16", "U",     "úr"),
    ("i", "ᛁ", "AD08", 34, "17", "I",     "íss"),
    ("o", "ᚮ", "AD09", 31, "18", "O",     "óss"),
    ("p", "ᛔ", "AD10", 35, "19", "P",     "prikket bjarkan"),
    ("å", "ᚭ", "AD11", 33, "1a", "OEM_4", "å — oppdiktet, se README"),

    ("a", "ᛆ", "AC01",  0, "1e", "A",     "ár"),
    ("s", "ᛋ", "AC02",  1, "1f", "S",     "sól"),
    ("d", "ᛑ", "AC03",  2, "20", "D",     "prikket týr"),
    ("f", "ᚠ", "AC04",  3, "21", "F",     "fé"),
    ("g", "ᚵ", "AC05",  5, "22", "G",     "prikket kaun"),
    ("h", "ᚼ", "AC06",  4, "23", "H",     "hagall"),
    ("j", "ᛃ", "AC07", 38, "24", "J",     "j — konsonantisk íss"),
    ("k", "ᚴ", "AC08", 40, "25", "K",     "kaun"),
    ("l", "ᛚ", "AC09", 37, "26", "L",     "lǫgr"),
    ("ø", "ᚯ", "AC10", 41, "27", "OEM_1", "ør"),
    ("æ", "ᛅ", "AC11", 39, "28", "OEM_7", "ær"),

    ("z", "ᛎ", "AB01",  6, "2c", "Z",     "z — seinmiddelaldersk tillegg"),
    ("x", "ᛪ", "AB02",  7, "2d", "X",     "x — seinmiddelaldersk tillegg"),
    ("c", "ᛍ", "AB03",  8, "2e", "C",     "c — seinmiddelaldersk tillegg"),
    ("v", "ᚡ", "AB04",  9, "2f", "V",     "prikket fé"),
    ("b", "ᛒ", "AB05", 11, "30", "B",     "bjarkan"),
    ("n", "ᚿ", "AB06", 45, "31", "N",     "nauð"),
    ("m", "ᛘ", "AB07", 46, "32", "M",     "maðr"),
]

# The only keys whose shift level stays runic.
PUNCT_KEYS = [
    (",", ",", "᛫", "AB08", 43, "33", "OEM_COMMA",  "enkelt skilletegn"),
    (".", ".", "᛬", "AB09", 47, "34", "OEM_PERIOD", "dobbelt skilletegn"),
    ("-", "-", "᛭", "AB10", 44, "35", "OEM_2",      "korsskilletegn"),
]

# XKB keysym names for the shift level, where it is not simply the
# uppercase ASCII letter.
XKB_SHIFT_NAME = {"æ": "AE", "ø": "Oslash", "å": "Aring"}

# Uniform records for the generators: (latin, base, shift, xkb, mac, sc, vk, name)
ALL_KEYS = [
    (latin, rune, latin.upper(), xkb, mac, sc, vk, name)
    for latin, rune, xkb, mac, sc, vk, name in KEYS
] + PUNCT_KEYS

TABLE = {latin: rune for latin, rune, *_ in KEYS}
REVERSE = {rune: latin for latin, rune in TABLE.items()}
RUNE_NAME = {latin: name for latin, _r, _x, _m, _s, _v, name in KEYS}

DIVIDER = "᛬"
PUNCTUATION = {"᛫", "᛬", "᛭"}


def shift_of(latin):
    """What the shift level produces for a letter key: the Latin capital."""
    return latin.upper()


def check():
    """Guard the invariants the whole project rests on."""
    if len(TABLE) != 29:
        raise AssertionError(f"expected 29 Norwegian letters, got {len(TABLE)}")
    if len(TABLE) != len(set(TABLE.values())):
        raise AssertionError("runes are not distinct -- mapping is not reversible")
    # One system only: every rune must sit in the Unicode Runic block, and
    # none of the Elder Futhark / Anglo-Saxon codepoints may creep back in.
    foreign = {
        "ᚨ", "ᚩ", "ᚪ", "ᚫ", "ᚲ", "ᚳ", "ᚷ", "ᚸ", "ᚹ", "ᚺ", "ᚻ", "ᛇ", "ᛈ",
        "ᛉ", "ᛊ", "ᛖ", "ᛗ", "ᛞ", "ᛟ", "ᛠ", "ᛡ", "ᛢ", "ᛣ", "ᛤ", "ᛥ", "ᛳ",
    }
    for latin, rune in TABLE.items():
        if not 0x16A0 <= ord(rune) <= 0x16FF:
            raise AssertionError(f"{latin} -> {rune} is outside the Runic block")
        if rune in foreign:
            raise AssertionError(
                f"{latin} -> {rune} is Elder Futhark or Anglo-Saxon, not medieval Norse"
            )
    return True


if __name__ == "__main__":
    check()
    print(f"{len(TABLE)} letters, all distinct, reversible, one system.")
