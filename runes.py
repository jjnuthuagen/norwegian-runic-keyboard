"""The mapping. Single source of truth for every generated layout.

Level 1 is a strict 1:1 over the 29-letter Norwegian alphabet, so the
mapping is fully reversible. It is a cipher of Norwegian *spelling*, not
of Norwegian *sound* -- silent letters survive, clusters are not
collapsed. A medieval scribe would have written what they heard.

Level 2 (shift) carries runic punctuation and Younger Futhark variant
forms, because runes have no case of their own and the level would
otherwise be wasted.

Every key below is identified in four coordinate systems at once, since
each platform names the same physical key differently:

    xkb  -- X11/Wayland key name        (Linux)
    mac  -- Apple virtual key code      (macOS .keylayout)
    sc   -- PS/2 set-1 scan code, hex   (Windows .klc and AutoHotkey)
    vk   -- Windows virtual key name    (Windows .klc)

Positions are given for a Norwegian pc105 keyboard, which is why æ ø å
sit on the keys a Norwegian already presses for them.
"""

LAYOUT_NAME = "Norwegian (medieval runic)"
SHORT_NAME = "runic"

# latin, base rune, shift rune, xkb, mac, sc, vk, comment on the shift form
KEYS = [
    ("q", "ᛩ", "ᛢ", "AD01", 12, "10", "Q",          "cweorth"),
    ("w", "ᚥ", "ᚹ", "AD02", 13, "11", "W",          "wunjo"),
    ("e", "ᛂ", "ᛖ", "AD03", 14, "12", "E",          "ehwaz"),
    ("r", "ᚱ", "ᛦ", "AD04", 15, "13", "R",          "long-branch yr"),
    ("t", "ᛏ", "ᚦ", "AD05", 17, "14", "T",          "thorn"),
    ("y", "ᚤ", "ᚣ", "AD06", 16, "15", "Y",          "yr"),
    ("u", "ᚢ", "ᛳ", "AD07", 32, "16", "U",          "oo"),
    ("i", "ᛁ", "ᛇ", "AD08", 34, "17", "I",          "iwaz"),
    ("o", "ᚮ", "ᚬ", "AD09", 31, "18", "O",          "long-branch oss"),
    ("p", "ᛔ", "ᛈ", "AD10", 35, "19", "P",          "pertho"),
    ("å", "ᚭ", "ᚪ", "AD11", 33, "1a", "OEM_4",      "ac"),

    ("a", "ᛆ", "ᚨ", "AC01",  0, "1e", "A",          "ansuz"),
    ("s", "ᛋ", "ᛌ", "AC02",  1, "1f", "S",          "short-twig sol"),
    ("d", "ᛑ", "ᚧ", "AC03",  2, "20", "D",          "eth"),
    ("f", "ᚠ", "ᚸ", "AC04",  3, "21", "F",          "gar"),
    ("g", "ᚵ", "ᛜ", "AC05",  5, "22", "G",          "ingwaz, ng"),
    ("h", "ᚼ", "ᚽ", "AC06",  4, "23", "H",          "short-twig hagall"),
    ("j", "ᛃ", "ᛄ", "AC07", 38, "24", "J",          "ger"),
    ("k", "ᚴ", "ᚲ", "AC08", 40, "25", "K",          "kauna"),
    ("l", "ᛚ", "ᛛ", "AC09", 37, "26", "L",          "dotted-l"),
    ("ø", "ᚯ", "ᛟ", "AC10", 41, "27", "OEM_1",      "othalan"),
    ("æ", "ᛅ", "ᚫ", "AC11", 39, "28", "OEM_7",      "aesc"),

    ("z", "ᛎ", "ᛉ", "AB01",  6, "2c", "Z",          "algiz"),
    ("x", "ᛪ", "ᛣ", "AB02",  7, "2d", "X",          "calc"),
    ("c", "ᛍ", "ᚳ", "AB03",  8, "2e", "C",          "cen"),
    ("v", "ᚡ", "ᚷ", "AB04",  9, "2f", "V",          "gebo"),
    ("b", "ᛒ", "ᛓ", "AB05", 11, "30", "B",          "short-twig bjarkan"),
    ("n", "ᚿ", "ᚾ", "AB06", 45, "31", "N",          "long-branch naud"),
    ("m", "ᛘ", "ᛙ", "AB07", 46, "32", "M",          "short-twig madr"),
]

# Punctuation keys keep their Latin mark unshifted -- ordinary sentence
# punctuation has to keep working -- and put the runic dividers on shift.
PUNCT_KEYS = [
    (",", ",", "᛫", "AB08", 43, "33", "OEM_COMMA",  "single punctuation"),
    (".", ".", "᛬", "AB09", 47, "34", "OEM_PERIOD", "multiple punctuation"),
    ("-", "-", "᛭", "AB10", 44, "35", "OEM_2",      "cross punctuation"),
]

ALL_KEYS = KEYS + PUNCT_KEYS

# Convenience views for the CLI.
TABLE = {latin: rune for latin, rune, *_ in KEYS}
REVERSE = {rune: latin for latin, rune in TABLE.items()}
SHIFT_TABLE = {latin: shift for latin, _, shift, *_ in KEYS}

DIVIDER = "᛬"
PUNCTUATION = {"᛫", "᛬", "᛭"}


def check():
    """Guard the two invariants the whole project rests on."""
    if len(TABLE) != len(set(TABLE.values())):
        raise AssertionError("base runes are not distinct -- mapping is not reversible")
    if len(TABLE) != 29:
        raise AssertionError(f"expected 29 Norwegian letters, got {len(TABLE)}")
    seen = {}
    for latin, _, shift, *_ in KEYS:
        if shift in seen:
            raise AssertionError(f"shift rune {shift} used by both {seen[shift]} and {latin}")
        seen[shift] = latin
    return True


if __name__ == "__main__":
    check()
    print(f"{len(TABLE)} letters, all distinct, reversible.")
