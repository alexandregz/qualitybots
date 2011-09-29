#!/usr/bin/python2.4
#
# Copyright 2011 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Generic Python Enumeration Implementation.

Code inspired from: http://code.activestate.com/recipes/67107/
"""




class EnumException(Exception):
  pass


class Enum(object):
  """Class for representing enumerations in Python.

  Attributes:
    _lookup: Dictionary respresentation of enum key-value.
    _reverse_lookup: Dictionary respresentation of enum value-key. Used for
        reverse lookup of enum values.
  """

  def __init__(self, **kwargs):
    """Init method for Enum.

    Usage:
      browser = Enum(CHROME=0, FIREFOX=1).

    Args:
      kwargs: Key-value pair of enum name(upper case string) and value (int)

    Raises:
      TypeError: Enum key not string or value is not integer.
      EnumException: Enum key is not upper string or enum value is not unique.
    """
    self._lookup = {}
    self._reverse_lookup = {}
    for k, v in kwargs.iteritems():
      if not isinstance(k, str):
        raise TypeError('enum key is not a string: %s' % k)
      if k != k.upper():
        raise EnumException('enum key is not an upper case string: %s' % k)
      if not isinstance(v, int):
        raise TypeError('enum value is not an integer: %s' % v)
      if v in self._reverse_lookup.keys():
        raise EnumException('enum value is not unique for: %d' % v)
      self._lookup[k] = v
      self._reverse_lookup[v] = k

  def __getattr__(self, attr):
    """Method provides support so that keys can be accessed as attributes."""
    if attr not in self._lookup.keys():
      raise AttributeError('No such enum exist.')
    return self._lookup[attr]

  def LookupKey(self, value):
    """Reverse lookup of enum key using it's value.

    Args:
      value: Value for reverse lookup (int).

    Returns:
      Associated enum key.
    """
    return self._reverse_lookup[value]

  def ListEnumKeys(self):
    """Returns list of enum keys."""
    return self._lookup.keys()

  def ListEnumValues(self):
    """Returns list of enum values."""
    return self._lookup.values()


BROWSER = Enum(CHROME=0, FIREFOX=1)
BROWSERCHANNEL = Enum(STABLE=0, BETA=1, DEV=2, CANARY=3)
CASE_STATUS = Enum(QUEUED=0, IN_PROGRESS=1, FINISHED=2, UPLOAD_ERROR=3,
                        TIMEOUT_ERROR=4, UNKNOWN_ERROR=5, EXPIRED=6)
LAYOUT_ENGINE_FAMILY = Enum(WEBKIT=0, GECKO=1)
OS = Enum(WINDOWS=0, LINUX=1, MAC=2, CHROMEOS=3)
VM_SERVICE = Enum(EC2=0, SKYTAP=1)
MACHINE_STATUS = Enum(PROVISIONED=0, INITIALIZING=1, RUNNING=2, TERMINATED=3,
                      FAILED=4, EXPIRED=5)
