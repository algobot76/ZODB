##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
import unittest

def test_must_use_consistent_connections():
    """

It's important to use consistent connections.  References to
separate connections to the same database or multi-database won't
work.

For example, it's tempting to open a second database using the
database open function, but this doesn't work:


    >>> import transaction
    >>> from ZODB.db import DB
    >>> databases = {}
    >>> db1 = DB(None, databases=databases, database_name='1')
    >>> db2 = DB(None, databases=databases, database_name='2')

    >>> tm = transaction.TransactionManager()
    >>> conn1 = db1.open(transaction_manager=tm)

    >>> from ZODB.tests.crossrefs import MyClass
    >>> p1 = MyClass()
    >>> conn1.root()['p'] = p1
    >>> tm.commit()

    >>> conn2 = db2.open(transaction_manager=tm)

    >>> p2 = MyClass()
    >>> conn2.root()['p'] = p2
    >>> p2.p1 = p1
    >>> tm.commit() # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
    Traceback (most recent call last):
    ...
    InvalidObjectReference:
    ('Attempt to store a reference to an object from a separate connection to
    the same database or multidatabase',
    <Connection at ...>,
    <ZODB.tests.crossrefs.MyClass object at ...>)

    >>> tm.abort()

Even without multi-databases, a common mistake is to mix objects in
different connections to the same database.

    >>> conn2 = db1.open(transaction_manager=tm)

    >>> p2 = MyClass()
    >>> conn2.root()['p'] = p2
    >>> p2.p1 = p1
    >>> tm.commit() # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
    Traceback (most recent call last):
    ...
    InvalidObjectReference:
    ('Attempt to store a reference to an object from a separate connection
    to the same database or multidatabase',
    <Connection at ...>,
    <ZODB.tests.crossrefs.MyClass object at ...>)

    >>> tm.abort()

"""

def test_connection_management_doesnt_get_caching_wrong():
    """

If a connection participates in a multidatabase, then it's
connections must remain so that references between it's cached
objects remain sane.

    >>> import transaction
    >>> from ZODB.db import DB
    >>> databases = {}
    >>> db1 = DB(None, databases=databases, database_name='1')
    >>> db2 = DB(None, databases=databases, database_name='2')
    >>> tm = transaction.TransactionManager()
    >>> conn1 = db1.open(transaction_manager=tm)
    >>> conn2 = conn1.get_connection('2')

    >>> from ZODB.tests.crossrefs import MyClass
    >>> z = MyClass()
    >>> conn2.root()['z'] = z
    >>> tm.commit()
    >>> x = MyClass()
    >>> x.z = z
    >>> conn1.root()['x'] = x
    >>> y = MyClass()
    >>> y.z = z
    >>> conn1.root()['y'] = y
    >>> tm.commit()

    >>> conn1.root()['x'].z is conn1.root()['y'].z
    True

So, we have 2 objects in conn1 that point to the same object in conn2.
Now, we'll deactivate one, close and repopen the connection, and see
if we get the same objects:

    >>> x._p_deactivate()
    >>> conn1.close()
    >>> conn1 = db1.open(transaction_manager=tm)

    >>> conn1.root()['x'].z is conn1.root()['y'].z
    True
    
    >>> db1.close()
    >>> db2.close()
"""

def test_explicit_adding_with_savepoint():
    """

    >>> import transaction
    >>> from ZODB.db import DB
    >>> databases = {}
    >>> db1 = DB(None, databases=databases, database_name='1')
    >>> db2 = DB(None, databases=databases, database_name='2')
    >>> tm = transaction.TransactionManager()
    >>> conn1 = db1.open(transaction_manager=tm)
    >>> conn2 = conn1.get_connection('2')

    >>> from ZODB.tests.crossrefs import MyClass
    >>> z = MyClass()

    >>> conn1.root()['z'] = z
    >>> conn1.add(z)
    >>> s = tm.savepoint()
    >>> conn2.root()['z'] = z
    >>> tm.commit()
    >>> z._p_jar.db().database_name
    '1'
    
    >>> db1.close()
    >>> db2.close()

"""

def test_explicit_adding_with_savepoint2():
    """

    >>> import transaction
    >>> from ZODB.db import DB
    >>> databases = {}
    >>> db1 = DB(None, databases=databases, database_name='1')
    >>> db2 = DB(None, databases=databases, database_name='2')
    >>> tm = transaction.TransactionManager()
    >>> conn1 = db1.open(transaction_manager=tm)
    >>> conn2 = conn1.get_connection('2')

    >>> from ZODB.tests.crossrefs import MyClass
    >>> z = MyClass()

    >>> conn1.root()['z'] = z
    >>> conn1.add(z)
    >>> s = tm.savepoint()
    >>> conn2.root()['z'] = z
    >>> z.x = 1
    >>> tm.commit()
    >>> z._p_jar.db().database_name
    '1'
    
    >>> db1.close()
    >>> db2.close()

"""

def tearDownDbs(test):
    test.globs['db1'].close()
    test.globs['db2'].close()

def test_suite():
    import doctest
    from ZODB.tests.crossrefs import MyClass
    from ZODB.tests.crossrefs import MyClass_w_getnewargs

    return unittest.TestSuite((
        doctest.DocFileSuite('../cross-database-references.txt',
                             globs=dict(MyClass=MyClass),
                             tearDown=tearDownDbs,
                             ),
        doctest.DocFileSuite('../cross-database-references.txt',
                             globs=dict(MyClass=MyClass_w_getnewargs),
                             tearDown=tearDownDbs,
                             ),
        doctest.DocTestSuite(),
    ))
