'''
.. image:: https://travis-ci.org/josiahcarlson/rom.svg?branch=master
    :target: https://travis-ci.org/josiahcarlson/rom

Rom - the Redis object mapper for Python

Copyright 2013-2015 Josiah Carlson

Released under the LGPL license version 2.1 and version 3 (you can choose
which you'd like to be bound under).

Documentation
=============

Updated documentation can be found: http://pythonhosted.org/rom/

What
====

Rom is a package whose purpose is to offer active-record style data modeling
within Redis from Python, similar to the semantics of Django ORM, SQLAlchemy,
Google's Appengine datastore, and others.

Why
===

I was building a personal project, wanted to use Redis to store some of my
data, but didn't want to hack it poorly. I looked at the existing Redis object
mappers available in Python, but didn't like the features and functionality
offered.

What is available
=================

Data types:

* Strings (2.x: str/unicode, 3.3+: str), ints, floats, decimals, booleans
* datetime.datetime, datetime.date, datetime.time
* Json columns (for nested structures)
* OneToMany and ManyToOne columns (for model references)
* Non-rom ForeignModel reference support

Indexes:

* Numeric range fetches, searches, and ordering
* Full-word text search (find me entries with col X having words A and B)
* Prefix matching (can be used for prefix-based autocomplete)
* Suffix matching (can be used for suffix-based autocomplete)
* Pattern matching on string-based columns
* All indexing is available when using Redis 2.6.0 and later

Other features:

* Per-thread entity cache (to minimize round-trips, easy saving of all
  entities)
* The ability to cache query results and get the key for any other use (see:
  ``Query.cached_result()``)

Getting started
===============

1. Make sure you have Python 2.6, 2.7, or 3.3+ installed
2. Make sure that you have Andy McCurdy's Redis client library installed:
   https://github.com/andymccurdy/redis-py/ or
   https://pypi.python.org/pypi/redis
3. Make sure that you have the Python 2 and 3 compatibility library, 'six'
   installed: https://pypi.python.org/pypi/six
4. (optional) Make sure that you have the hiredis library installed for Python
5. Make sure that you have a Redis server installed and available remotely
6. Update the Redis connection settings for ``rom`` via
   ``rom.util.set_connection_settings()`` (other connection update options,
   including per-model connections, can be read about in the ``rom.util``
   documentation)::

    import redis
    from rom import util

    util.set_connection_settings(host='myhost', db=7)

.. warning:: If you forget to update the connection function, rom will attempt
 to connect to localhost:6379 .

7. Create a model::

    import rom

    # All models to be handled by rom must derived from rom.Model
    class User(rom.Model):
        email = rom.String(required=True, unique=True, suffix=True)
        salt = rom.String()
        hash = rom.String()
        created_at = rom.Float(default=time.time)

8. Create an instance of the model and save it::

    PASSES = 32768
    def gen_hash(password, salt=None):
        salt = salt or os.urandom(16)
        comp = salt + password
        out = sha256(comp).digest()
        for i in xrange(PASSES-1):
            out = sha256(out + comp).digest()
        return salt, out

    user = User(email='user@host.com')
    user.salt, user.hash = gen_hash(password)
    user.save()
    # session.commit() or session.flush() works too

9. Load and use the object later::

    user = User.get_by(email='user@host.com')
    at_gmail = User.query.endswith(email='@gmail.com').all()

Lua support
===========

From version 0.25.0 and on, rom assumes that you are using Redis version 2.6
or later, which supports server-side Lua scripting. This allows for the
support of multiple unique column constraints without annoying race conditions
and retries. This also allows for the support of prefix, suffix, and pattern
matching on certain column types.

If you are using a version of Redis prior to 2.6, you should upgrade Redis. If
you are unable or unwilling to upgrade Redis, but you still wish to use rom,
you should call ``rom._disable_lua_writes()``, which will prevent you from
using features that require Lua scripting support.
'''

from datetime import datetime, date, time as dtime
from decimal import Decimal as _Decimal
import warnings

import six

_skip = None
_skip = set(globals()) - set('__doc__')

from .columns import (Column, Integer, Boolean, Float, Decimal, DateTime,
    Date, Time, String, Text, Json, PrimaryKey, ManyToOne, OneToOne,
    ForeignModel, OneToMany, MODELS, MODELS_REFERENCED, SKIP_ON_DELETE)
from .exceptions import (ORMError, UniqueKeyViolation, InvalidOperation,
    QueryError, ColumnError, MissingColumn, InvalidColumnValue, RestrictError,
    DataRaceError, EntityDeletedError)
from .index import GeneralIndex, Pattern, Prefix, Suffix
from . import model
from .model import _ModelMetaclass, Model
from .query import NOT_NULL, Query
from .util import (ClassProperty, _connect, session,
    _prefix_score, _script_load, _encode_unique_constraint,
    FULL_TEXT, CASE_INSENSITIVE, SIMPLE, SIMPLE_CI, IDENTITY, IDENTITY_CI)

VERSION = '0.33.0'

COLUMN_TYPES = [Column, Integer, Boolean, Float, Decimal, DateTime, Date,
Time, String, Text, Json, PrimaryKey, ManyToOne, ForeignModel, OneToMany,
OneToOne]

NUMERIC_TYPES = six.integer_types + (float, _Decimal, datetime, date, dtime)

__all__ = [x for x in set(globals()) if x not in _skip and not x.startswith('_')]

# silence pyflakes
MODELS, MODELS_REFERENCED
SKIP_ON_DELETE
ColumnError, DataRaceError, EntityDeletedError, InvalidColumnValue,
InvalidOperation, MissingColumn, ORMError, QueryError, RestrictError,
UniqueKeyViolation
Pattern, Suffix, GeneralIndex, Prefix, Model, _ModelMetaclass, Query, NOT_NULL
IDENTITY, IDENTITY_CI, SIMPLE, SIMPLE_CI, CASE_INSENSITIVE, FULL_TEXT
ClassProperty
session, _connect, _encode_unique_constraint, _prefix_score, _script_load

USE_LUA = True
def _enable_lua_writes():
    from . import columns
    from . import util
    global USE_LUA
    util.USE_LUA = columns.USE_LUA = model.USE_LUA = USE_LUA = True

def _disable_lua_writes():
    from . import columns
    from . import util
    global USE_LUA
    util.USE_LUA = columns.USE_LUA = model.USE_LUA = USE_LUA = False
    warnings.warn("Lua writing is disabled, which disables a lot of useful "
                  "functionality. The ability to disable Lua writing will "
                  "be removed in some future version of rom.")
