from tinydb import TinyDB
import click
from flask import current_app, g
from flask.cli import with_appcontext

# reference to database object. Will be initialized on first call of `get_db`
_db = None


def get_db():
    """
    Initializes the database on first call and returns it.
    Each subsequent call returns the same database object.

    :return: database object
    """
    if 'db' not in g:
        g.db = TinyDB(current_app.config['DATABASE'])

    return g.db


def table(name):
    """
    Returns the table object with given name

    :param name: name of the table
    :return: table object
    """
    return get_db().table(name)


def close_db(_=None):
    """
    Closes the db connection
    """
    db = g.pop('db', None)

    if db is not None:
        db.close()


@click.command('reset-db')
@with_appcontext
def reset_db_command():
    get_db().purge()
    click.echo('Reset the database.')


def init_app(app):
    """
    Register database functions with the Flask app. This is called by the application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(reset_db_command)
