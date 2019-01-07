from vocab.sentence_parser import is_hiragana, is_kanji
import itertools


class VerbType:
    ICHIDAN = object()
    GODAN = object()
    IRREGULAR = object()


class HiraganaLetter:
    rows = {
        "-": {"a": "あ", "i": "い", "u": "う", "e": "え", "o": "お"},
        "k": {"a": "か", "i": "き", "u": "く", "e": "け", "o": "こ"},
        "g": {"a": "が", "i": "ぎ", "u": "ぐ", "e": "げ", "o": "ご"},
        "s": {"a": "さ", "i": "し", "u": "す", "e": "せ", "o": "そ"},
        "z": {"a": "ざ", "i": "じ", "u": "ず", "e": "ぜ", "o": "ぞ"},
        "t": {"a": "た", "i": "ち", "u": "つ", "e": "て", "o": "と"},
        "d": {"a": "だ", "i": "ぢ", "u": "づ", "e": "で", "o": "ど"},
        "n": {"a": "な", "i": "に", "u": "ぬ", "e": "ね", "o": "の"},
        "h": {"a": "は", "i": "ひ", "u": "ふ", "e": "へ", "o": "ほ"},
        "b": {"a": "ば", "i": "び", "u": "ぶ", "e": "べ", "o": "ぼ"},
        "p": {"a": "ぱ", "i": "ぴ", "u": "ぷ", "e": "ぺ", "o": "ぽ"},
        "m": {"a": "ま", "i": "み", "u": "む", "e": "め", "o": "も"},
        "r": {"a": "ら", "i": "り", "u": "る", "e": "れ", "o": "ろ"},
        "y": {"a": "や", "u": "ゆ", "o": "よ"},
        "w": {"a": "わ", "o": "を"},
        "nn": {"n": "ん"}
    }

    small = {
        "ya": "ゃ", "yu": "ゅ", "yo": "ょ", "tsu": "っ"
    }

    # rules how a dakuten ('') or a handakuten (o) changes the row of a
    # hiragana letter
    dakuten_rules = {'k': 'g', 's': 'z', 't': 'd', 'h': 'b'}
    handakuten_rules = {'h': 'p'}

    # rules how the removal of a dakuten or handakuten changes the row of a
    # hiragana letter
    reverse_dakuten_rules = {v: k for k, v in itertools.chain(
        dakuten_rules.items(), handakuten_rules.items())}

    # returns the base row and ending of a hiragana letter
    by_letter = {}
    for row_name, row in rows.items():
        for ending, letter in row.items():
            by_letter[letter] = (row_name, ending)

    def __init__(self, c):
        self.c = c
        self.row, self.ending = HiraganaLetter.by_letter[c]

        if self.row in HiraganaLetter.dakuten_rules.values():
            self.dakuten = "dakuten"
        elif self.row in HiraganaLetter.handakuten_rules.values():
            self.dakuten = "handakuten"
        else:
            self.dakuten = None

    def __str__(self):
        return "HiraganaLetter(%s, row=%s, col=%s)" % (self.c, self.row, self.ending)

    @classmethod
    def from_str(cls, s):
        if len(s) == 1 and is_hiragana(s):
            return HiraganaLetter(s)
        else:
            romaji = s

            if romaji is None or len(romaji) == 0:
                raise ValueError("empty romaji")

            if romaji == "shi":
                row, ending = "s", "i"
            elif romaji == "chi":
                row, ending = "t", "i"
            elif romaji == "tsu":
                row, ending = "t", "u"
            elif romaji == "fu":
                row, ending = "h", "u"
            elif romaji == "ji":
                row, ending = "z", "i"
            elif romaji == "n":
                row, ending = "nn", "n"
            else:
                if len(romaji) == 1:
                    row, ending = '-', romaji
                elif len(romaji) == 2:
                    row, ending = romaji[0], romaji[1]
                else:
                    row, ending = None, None
            try:
                return HiraganaLetter(HiraganaLetter.rows[row][ending])
            except KeyError:
                raise ValueError("Cannot transform '%s' to a kana letter" % romaji)

    def with_ending(self, ending):
        if ending not in "aiueo":
            raise ValueError("Ending must be one of 'aiueo'")

        return HiraganaLetter(HiraganaLetter.rows[self.row][ending])

    def with_dakuten(self, dakuten):
        if dakuten == self.dakuten:
            return self

        if dakuten is None:
            new_row = HiraganaLetter.reverse_dakuten_rules.get(self.row)
            return HiraganaLetter(HiraganaLetter.rows[new_row][self.ending])
        else:
            # first get basic hiragana letter (without dakuten)
            basic_letter = self.with_dakuten(None)
            if dakuten is "dakuten":
                new_row = HiraganaLetter.dakuten_rules.get(basic_letter.row)
            elif dakuten is "handakuten":
                new_row = HiraganaLetter.handakuten_rules.get(basic_letter.row)
            else:
                raise ValueError("dakuten must either be 'dakuten' or 'handakuten'")

            if new_row is None:
                raise ValueError("the '%s' row has no %s rule" % (basic_letter.row, dakuten))
            else:
                return HiraganaLetter(HiraganaLetter.rows[new_row][basic_letter.ending])

    def romaji(self):
        if self.c == "し":
            return "shi"
        elif self.c == "ち":
            return "chi"
        elif self.c == "つ":
            return "tsu"
        elif self.c == "ふ":
            return "fu"
        elif self.c == "じ":
            return "ji"
        elif self.c == "ぢ":
            return "ji"
        elif self.c == "づ":
            return "zu"
        else:
            return "".join([self.row, self.ending])


def has_ichidan_ending(verb):
    if len(verb) < 2:
        return False
    else:
        if is_kanji(verb[-2]) and verb[-1] == "る":
            return None
        else:
            return HiraganaLetter(verb[-2]).ending in "ie" and verb[-1] == "る"


class Inflections(object):
    POLITE = object()
    PAST = object()
    TE = object()
    POTENTIAL = object()

    def __init__(self, base_verb, verb_type=VerbType.GODAN, applied_inflections=None, inflection=None):
        if base_verb is None or len(base_verb) <= 1:
            raise ValueError("Verb is empty or too short")

        if base_verb[-1] not in 'るつうくすぶむぬぐ':
            raise ValueError("Final kana letter is no valid verb ending")

        if verb_type is VerbType.ICHIDAN and not has_ichidan_ending(base_verb):
            raise ValueError("verb '%s' has no ichidan ending" % base_verb)

        self.base_verb = base_verb
        self.verb_type = verb_type

        if applied_inflections is None:
            self.applied_inflections = set([])
        else:
            self.applied_inflections = applied_inflections

        if len(self.applied_inflections) != 0 and inflection is not None:
            raise ValueError("`inflection` must be `None` when no inflections are applied")
        else:
            self.inflection = inflection

    def te(self):
        if self.verb_type == VerbType.ICHIDAN:
            return self.base_verb[:-1] + "て"
        elif self.verb_type == VerbType.GODAN:
            if self.base_verb[-1] in 'うつる':
                return self.base_verb[:-1] + "って"
            elif self.base_verb[-1] in 'く':
                return self.base_verb[:-1] + "いて"
            elif self.base_verb[-1] in 'す':
                return self.base_verb[:-1] + "して"
            elif self.base_verb[-1] in 'ぶむぬ':
                return self.base_verb[:-1] + "んで"
            elif self.base_verb[-1] in 'ぐ':
                return self.base_verb[:-1] + "いで"
            else:
                raise ValueError("invalid verb ending: %s" % self.base_verb[-1])
        else:
            raise NotImplementedError()

    def masu(self):
        if self.verb_type == VerbType.ICHIDAN:
            return self.base_verb[:-1] + "ます"
        elif self.verb_type == VerbType.GODAN:
            return self.base_verb[:-1] + \
                   HiraganaLetter.from_str(self.base_verb[-1]).with_ending("i").c + \
                   "ます"
        else:
            raise NotImplementedError()


def main():
    # print(Inflections("しる", verb_type=VerbType.GODAN).masu())
    print(HiraganaLetter.from_str("te").with_dakuten("dakuten"))


if __name__ == "__main__":
    main()
