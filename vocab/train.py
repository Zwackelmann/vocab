from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from vocab.db import table
from vocab.model import DocumentManager, VocabEntry, Sentence
from wtforms import StringField, Form, validators, TextAreaField

bp = Blueprint('train', __name__)


