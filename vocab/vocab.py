from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)

from vocab.db import table
from vocab.model import DocumentManager, VocabEntry, Sentence
from wtforms import StringField, Form, validators, TextAreaField

bp = Blueprint('vocab', __name__)

VOCAB_PER_PAGE = 10


class VocabForm(Form):
    word_jp = StringField('Word', [validators.Length(min=1, max=100)])
    translations = TextAreaField('Translations', [validators.Length(min=1, max=255)])
    sentences = TextAreaField('Sentences')


@bp.route('/')
def index():
    """
    Route showing all Vocab
    """
    page = request.args.get('page', 1, type=int)
    documents = list(reversed([DocumentManager.from_document(d, table('vocab')) for d in table('vocab').all()]))

    return render_template('vocab/index.html',
                           vocab=documents[(page-1)*VOCAB_PER_PAGE: page*VOCAB_PER_PAGE],
                           next_page=page+1 if len(documents) > page*VOCAB_PER_PAGE else None,
                           prev_page=page-1 if page > 1 else None)


@bp.route('/delete/<doc_id>', methods=('GET', ))
def delete(doc_id):
    """
    Route to delete a given Vocab
    """
    try:
        table('vocab').remove(doc_ids=[int(doc_id)])
    except ValueError:
        pass
    except KeyError:
        pass

    return redirect(url_for('vocab.index'))


def parse_sentence(sentence):
    """
    Transforms a sentence written in the sentences box into a `Sentence` object by splitting the text into
    "japanese text" and "translation". The split is performed at the first "=" character.
    If no "=" character exists, the "translation" is `None`

    :param sentence: a `str` (single line from the sentences box)
    :return: `Sentence` object containing japanese sentence and translation
    """
    parts = sentence.split('=')
    if len(parts) == 1:
        return Sentence(parts[0].strip(), None)
    else:
        return Sentence(parts[0].strip(), ("=".join(parts[1:])).strip())


def parse_sentence_sequence(text):
    """
    Parse the content of the sentences box to a list of `Sentence` objects:

    Ignore empty lines and parse each non-empty line as described in `parse_sentence`

    :param text: a `str` (content of the sentence box as plane text characters)
    :return: list of `Sentence` objects
    """
    sentences = [s.strip() for s in text.splitlines()]
    return [parse_sentence(s) for s in sentences if len(s) != 0]


def render_sentence(sentence):
    """
    Transforms a `Sentence` object to a plain text to be put into a sentence box.

    Parsing the text returned by this function with (using `parse_sentence`) should return an equivalent `Sentence`
    object

    :param sentence: `Sentence` object
    :return: text to be put in sentences box
    """
    if sentence.translation is None:
        return sentence.jp
    else:
        return "%s = %s" % (sentence.jp, sentence.translation)


@bp.route('/edit/<doc_id>', methods=('GET', 'POST'))
def edit(doc_id):
    """
    Route called to edit a Vocab.

    When called as "GET" the edit template is being rendered.
    On "POST" the Vocab will be updated and the index template will be rendered
    If the payload of the "POST" is invalid, the edit template will be rendered again

    :param doc_id: doc id of Vocab to be edited
    :return: rendered HTML template
    """
    if request.method == 'POST':
        try:
            doc_id = int(doc_id)
        except ValueError:
            return redirect(url_for('vocab.index'))

        # read form content
        word_jp = request.form['word_jp']
        translations_string = request.form['translations']
        sentences_string = request.form['sentences']

        # ensure that a
        errors = []
        if word_jp is None or len(word_jp.strip()) == 0:
            errors.append('Word is required')
            word_jp = ""

        if translations_string is None or len(translations_string.strip()) == 0:
            errors.append('Translation is required')
            translations = []
        else:
            translations = [s.strip() for s in translations_string.splitlines()]

        sentences = parse_sentence_sequence(sentences_string)

        dm = DocumentManager(
            VocabEntry(word_jp=word_jp, translations=translations, sentences=sentences),
            doc_id=doc_id,
            table=table('vocab')
        )

        if len(errors) != 0:
            flash(", ".join(errors))
            sentences_string = "\n".join([render_sentence(sentence) for sentence in dm.entity.sentences])
            form = VocabForm(word_jp=dm.entity.word_jp, translations=translations_string, sentences=sentences_string)
            return render_template('vocab/edit.html', v=dm, form=form)
        else:
            dm.update()
            return redirect(url_for('vocab.index', _anchor="vocab_%d" % dm.doc_id))
    else:
        try:
            doc_id = int(doc_id)
        except ValueError:
            return redirect(url_for('vocab.index'))

        doc = table('vocab').get(doc_id=doc_id)
        dm = DocumentManager.from_document(doc, table('vocab'))

        if dm is not None:
            translations_string = "\n".join(dm.entity.translations)
            sentences_string = "\n".join([render_sentence(sentence) for sentence in dm.entity.sentences])
            form = VocabForm(word_jp=dm.entity.word_jp, translations=translations_string, sentences=sentences_string)
            return render_template('vocab/edit.html', v=dm, form=form)
        else:
            return redirect(url_for('vocab.index'))


@bp.route('/create', methods=('GET', 'POST'))
def create():
    """
    Route called to create a Vocab.

    When called as "GET" the create template is being rendered.
    On "POST" the Vocab will be created and the index template will be rendered
    If the payload of the "POST" is invalid, the create template will be rendered again

    :return: rendered HTML template
    """
    if request.method == 'POST':
        word_jp = request.form['word_jp']
        translations_string = request.form['translations']
        sentences_string = request.form['sentences']

        errors = []
        if word_jp is None or len(word_jp.strip()) == 0:
            errors.append('Word is required')
            word_jp = ""

        if translations_string is None or len(translations_string.strip()) == 0:
            errors.append('Translation is required')
            translations = []
        else:
            translations = [s.strip() for s in translations_string.splitlines()]

        sentences = parse_sentence_sequence(sentences_string)

        dm = DocumentManager(
            VocabEntry(word_jp=word_jp, translations=translations, sentences=sentences),
            doc_id=None,
            table=table('vocab')
        )

        if len(errors) != 0:
            flash(", ".join(errors))

            sentences_string = "\n".join([render_sentence(sentence) for sentence in dm.entity.sentences])
            form = VocabForm(word_jp=dm.entity.word_jp, translations=translations_string, sentences=sentences_string)
            return render_template('vocab/create.html', v=dm, form=form)
        else:
            dm.insert()
            return redirect(url_for('vocab.index', _anchor="vocab_%d" % dm.doc_id))

    form = VocabForm()
    return render_template('vocab/create.html', form=form)
