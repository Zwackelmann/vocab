import re
from flask import Markup


class JpRE:
    """
    Collection of japanese character regular expressions
    """
    hiragana_full = r'[ぁ-ゟ]'
    katakana_full = r'[゠-ヿ]'
    kanji = r'[㐀-䶵一-鿋豈-頻]'
    radicals = r'[⺀-⿕]'
    katakana_half_width = r'[｟-ﾟ]'


# used while parsing to indicate a space in the parsed sequence
SPACE = object()


class KanjiSequence(object):
    """
    Represents a sequence of `Kanji` objects with optional furigana attached

    :param kanji: list of `Kanji` objects
    :param furigana: string of kana characters
    """
    def __init__(self, kanji, furigana=None):
        self.kanji = kanji
        self.furigana = furigana

    def render(self):
        if self.furigana is None:
            return "".join([k.render() for k in self.kanji])
        else:
            return "<ruby>%s<rt>%s</rt><ruby>" % (
                "".join([k.render() for k in self.kanji]),
                self.furigana.text)


class Kanji(object):
    """
    Wraps a single kanji character
    """
    def __init__(self, character):
        self.character = character

    def jisho_link(self):
        return "https://jisho.org/search/%s%%20%%23kanji" % self.character


class Furigana(object):
    """
    Represents a furigana string sequence
    """
    def __init__(self, text):
        self.text = text


def is_kanji(c):
    """
    Returns `True` if supplied character is a kanji character
    """
    return re.match(JpRE.kanji, c) is not None


def is_whitespace(c):
    """
    Returns `True` if supplied character is a whitespace character
    """
    return re.match(r"\s", c) is not None


def charseq(buf):
    """
    Builds a string out of the supplied buffer by concatenating all characters in the buffer except whitespace
    :param buf: list of characters
    :return: concatenated string
    """
    return "".join([c for c in buf if not is_whitespace(c)])


def group(tokens):
    """
    Group a sequence of tokens.

    Tokens can be `Kanji`-objects, `Furigana`-objects, the `SPACE` object or `str`

    The grouping is done by applying the following rules:
        - Subsequent `Kanji` objects are grouped to a `KanjiSequence`
        - If a `Furigana` object follows a `KanjiSequence`, the `Furigana` is added to the `KanjiSequence`
        - Subsequent `str` characters are grouped to a single `str`
        - Invalid sequences are ignored without an error (e.g. sequence starting with `Furigana`)

    :param tokens: Sequence of tokens
    :return: Grouped Tokens
    """
    state = 'empty'
    groups = []
    buf = []
    for token in tokens:
        if state == 'empty':
            if type(token) is str:
                buf = [token]
                state = 'buffer str'
            elif type(token) is Kanji:
                buf = [token]
                state = 'buffer kan'
            elif token == SPACE:
                groups.append(SPACE)
            elif type(token) is Furigana:
                # furigana is invalid here: ignore
                pass
            else:
                raise ValueError("invalid state")
        elif state == 'buffer str':
            if type(token) is str:
                buf.append(token)
            elif type(token) is Kanji:
                groups.append(charseq(buf))
                buf = [token]
                state = 'buffer kan'
            elif token == SPACE:
                groups.append(charseq(buf))
                groups.append(SPACE)
                buf = []
                state = 'empty'
            elif type(token) is Furigana:
                # furigana is invalid here: ignore
                pass
            else:
                raise ValueError("invalid state")
        elif state == 'buffer kan':
            if type(token) is str:
                groups.append(KanjiSequence(buf, furigana=None))
                buf = [token]
                state = 'buffer str'
            elif type(token) is Kanji:
                buf.append(token)
            elif type(token) is Furigana:
                groups.append(KanjiSequence(buf, furigana=token))
                buf = []
                state = 'empty'
            elif token == SPACE:
                groups.append(KanjiSequence(buf, furigana=None))
                groups.append(SPACE)
                buf = []
                state = 'empty'
            else:
                raise ValueError("invalid state")
        else:
            raise ValueError("invalid state")

    if state == 'empty':
        pass
    elif state == 'buffer str':
        groups.append(charseq(buf))
    elif state == 'buffer kan':
        groups.append(KanjiSequence(buf, furigana=None))
    else:
        raise ValueError("invalid state")

    return groups


def parse(text):
    """
    Transforms a text into a sequence of `Kanji`-objects, `Furigana`-objects, the `SPACE` object and `str`s

    The following rules are applied to parse a text:

        - A `Kanji`-object is created for each `str` character that is a kanji (`is_kanji(s)` is `True`)
        - A `Furigana`-object is a sequence of hiragana characters after a "^" character. Any non-hiragana character
          terminates the furigana sequence
        - The `SPACE` object is created for each "~" character
        - All other characters are added as simple `str` characters

    :param text: text to be parsed
    :return: parsed text
    """
    parsed_sequence = []
    while len(text) != 0:
        if is_kanji(text[0]):
            parsed_sequence.append(Kanji(text[0]))
            text = text[1:]
        elif text[0] == "^":
            match = re.search(r"^\^(?P<furigana>[ぁ-ゟ]*)", text, 0)
            if match is not None:
                parsed_sequence.append(Furigana(match.group("furigana")))
                text = text[len(match.group(0)):]
                continue

            raise ValueError("no match")
        elif text[0] == "~":
            parsed_sequence.append(SPACE)
            text = text[1:]
        else:
            parsed_sequence.append(text[0])
            text = text[1:]

    return parsed_sequence


def render_obj(obj):
    """
    Render object by transforming it to HTML

    The supplied object must be one of:

        - `Kanji`
        - `KanjiSequence`
        - the `SPACE` object

    :param obj: object to be rendered
    :return: HTML used to render the object
    """
    if type(obj) is str:
        return obj
    elif type(obj) is Kanji:
        return """<a href="%s">%s</a>""" % (obj.jisho_link(), obj.character)
    elif type(obj) is KanjiSequence:
        if obj.furigana is None:
            return "".join([render_obj(k) for k in obj.kanji])
        else:
            return "<ruby>%s<rt>%s</rt><ruby>" % (
                "".join([render_obj(k) for k in obj.kanji]),
                obj.furigana.text)
    elif obj == SPACE:
        return "&nbsp;"
    else:
        raise ValueError("Cannot render object of type %s" % type(obj))


def render_jp(text):
    """
    Returns HTML for a given japanese sentence.

    :param text: text consisting of japanese characters

    :return: HTML representing the given text
    """
    return Markup("".join([render_obj(obj) for obj in group(parse(text))]))
