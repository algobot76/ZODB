##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

"""Python implementation of persistent base types

$Id$"""

import persistent
from UserDict import UserDict

class PersistentMapping(UserDict, persistent.Persistent):
    """A persistent wrapper for mapping objects.

    This class allows wrapping of mapping objects so that object
    changes are registered.  As a side effect, mapping objects may be
    subclassed.

    A subclass of PersistentMapping or any code that adds new
    attributes should not create an attribute named _container.  This
    is reserved for backwards compatibility reasons.
    """

    # UserDict provides all of the mapping behavior.  The
    # PersistentMapping class is responsible marking the persistent
    # state as changed when a method actually changes the state.  At
    # the mapping API evolves, we may need to add more methods here.

    __super_delitem = UserDict.__delitem__
    __super_setitem = UserDict.__setitem__
    __super_clear = UserDict.clear
    __super_update = UserDict.update
    __super_setdefault = UserDict.setdefault

    def __delitem__(self, key):
        self.__super_delitem(key)
        self._p_changed = 1

    def __setitem__(self, key, v):
        self.__super_setitem(key, v)
        self._p_changed = 1

    def clear(self):
        self.__super_clear()
        self._p_changed = 1

    def update(self, b):
        self.__super_update(b)
        self._p_changed = 1

    def setdefault(self, key, failobj=None):
        # We could inline all of UserDict's implementation into the
        # method here, but I'd rather not depend at all on the
        # implementation in UserDict (simple as it is).
        if not self.has_key(key):
            self._p_changed = 1
        return self.__super_setdefault(key, failobj)

    try:
        __super_pop = UserDict.pop
    except AttributeError:
        pass
    else:
        def pop(self, i):
            self._p_changed = 1
            return self.__super_pop(i)

    try:
        __super_popitem = UserDict.popitem
    except AttributeError:
        pass
    else:
        def popitem(self):
            self._p_changed = 1
            return self.__super_popitem()

    # __iter__ was added in ZODB 3.4.2, but should have been added long
    # before.  We could inherit from Python's IterableUserDict instead
    # (which just adds __iter__ to Python's UserDict), but that class isn't
    # documented, and it would add another level of lookup for all the
    # other methods.
    def __iter__(self):
        return iter(self.data)

    # If the internal representation of PersistentMapping changes,
    # it causes compatibility problems for pickles generated by
    # different versions of the code.  Compatibility works in both
    # directions, because an application may want to share a database
    # between applications using different versions of the code.

    # Effectively, the original rep is part of the "API."  To provide
    # full compatibility, the getstate and setstate must read and
    # write objects using the old rep.

    # As a result, the PersistentMapping must save and restore the
    # actual internal dictionary using the name _container.

    def __getstate__(self):
        state = {}
        state.update(self.__dict__)
        state['_container'] = state['data']
        del state['data']
        return state

    def __setstate__(self, state):
        if state.has_key('_container'):
            self.data = state['_container']
            del state['_container']
        elif not state.has_key('data'):
            self.data = {}
        self.__dict__.update(state)
