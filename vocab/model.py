import jsonpickle


class DocumentManager(object):
    """
    Manages a database document. Is able to update and insert documents in the database and fetch documents from the
    database.
    """
    def __init__(self, entity, doc_id, table):
        """
        Initialize an `DocumentManager`

        :param entity: An arbitrary tiny db document
        :param doc_id: Document id of the managed document (None, if not persistent)
        :param table: table object to be used
        """
        self.entity = entity
        self.doc_id = doc_id
        self.table = table

    @classmethod
    def from_document(cls, document, table):
        """
        Create an `DocumentManager` from a database document

        :param document: tiny db document
        :param table: table object
        :return: `DocumentManager` wrapping the tiny db document
        """
        u = jsonpickle.Unpickler()
        return DocumentManager(
            entity=u.restore(dict(document)),
            doc_id=document.doc_id,
            table=table)

    def update(self):
        """
        Insert or update the managed document
        """
        p = jsonpickle.Pickler()
        pickled_entry = p.flatten(self.entity)

        if self.doc_id is None:
            doc_id = self.table.insert(pickled_entry)
            self.doc_id = doc_id
        else:
            self.table.update(pickled_entry, doc_ids=[self.doc_id])

    def insert(self):
        """
        Insert or update the managed document
        """
        self.update()


class VocabEntry(object):
    """
    Represents a vocabulary entry for a database document
    """
    def __init__(self, word_jp, translations, sentences):
        self.word_jp = word_jp
        self.translations = translations
        self.sentences = sentences


class Sentence(object):
    """
    Represents a sentence for a `VocabEntry`
    """
    def __init__(self, jp, translation):
        self.jp = jp
        self.translation = translation
