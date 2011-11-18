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


"""Base class for defining utility functions associated with browser channels.

The ChannelUtil class contains abstract functions and is intended to be used as
a base class and not instantiated.  Assume derived classes have implemented all
functionality and a try/except is not required when using these functions.

The base class defines a number of functions common to all channel utility
classes that define a general process of data retrieval.  Data retrieval is
defined in the following public functions:

    GetAllChannelUrls - Returns a dictionary of all valid channels mapped to
        their current download url for the given OS.
    GetAllChannelVersions - Returns a dictionary of all valid channels mapped
        to their current version for the given OS.
    GetUrlForChannel - Return the download url for the given channel and OS.
    GetVersionForChannel - Return the version for the given channel and OS.
    IdentifyChannel - Return the channel name for the given version and OS.

While the base class provides the general process, some data used in that
process is browser and will need to be supplied by the derived class.  The
following functions are not implemented and need to implemented in the derived
class:

    _GetCacheKey - Returns the cache key for the specific browser.
    _GetChannelData - Downloads and prepares the channel data.
    _GetChannelList - Return a list of supported channels.
    _GetOSList - Return a list of supported OSs.
    _GetOSMap - Return a dictionary that maps an OS name to the name used by
        the specific browser.

The format of channel information is expected to be:

    {'os': string, 'channel': string, 'browser': string, 'version': string,
     'download_url': string}

The cached data is stored as a list of channel information dictionaries.

TODO(user): Integrate the channel_util and derived classes with the
enumerations and name definitions in other files.
"""


import logging

from google.appengine.api import memcache

_HOUR_IN_SECONDS = 60 * 60

KEY_BROWSER = 'browser'
KEY_CHANNEL = 'channel'
KEY_DOWNLOAD_URL = 'download_url'
KEY_OS = 'os'
KEY_VERSION = 'version'


class InvalidParam(Exception):
  pass


class ChannelUtil(object):
  """The base class for the various browser's channel utilities."""

  def GetAllChannelUrls(self, os):
    """Returns all channel download urls for a given OS.

    Args:
      os: A string indicating the operating system requested.

    Returns:
      Key-value pair respresenting the channel(key) and the download url.
      None otherwise.
    """
    # Verify that the os argument is acceptable.
    try:
      os = self._CheckOsParam(os)
    except InvalidParam:
      return None

    # Get the necessary data.
    data = self._RetrieveChannelData()

    channel_info = {}
    for row in data:
      try:
        if row['os'] == os:
          channel_info[row['channel']] = row['download_url']
      except KeyError:
        logging.error('The channel data is invalid.')
        return None

    return channel_info

  def GetAllChannelVersions(self, os):
    """Returns all channel versions for a given OS.

    Args:
      os: A string indicating the operating system requested.

    Returns:
      Key-value pair respresenting the channel(key) and current version.
      None otherwise.
    """
    # Verify that the os argument is acceptable.
    try:
      os = self._CheckOsParam(os)
    except InvalidParam:
      return None

    # Get the necessary data.
    data = self._RetrieveChannelData()

    channel_info = {}
    for row in data:
      try:
        if row['os'] == os:
          channel_info[row['channel']] = row['version']
      except KeyError:
        logging.error('The channel data is invalid.')
        return None

    return channel_info

  def GetUrlForChannel(self, os, channel):
    """Return the download url string for the given OS and channel.

    Args:
      os: A string indicating the operating system requested.
      channel: A string indicating the channel requested.

    Returns:
      A string indicating the download url for the given OS and channel.
      None is returned if the data cannot be found due in incorrect arguments.
    """
    # Verify that the arguments are acceptable.
    try:
      os = self._CheckOsParam(os)
      channel = self._CheckChannelParam(channel)
    except InvalidParam:
      logging.error('Channel check failed (%s, %s).', os, channel)
      return None

    # Get the necessary data.
    data = self._RetrieveChannelData()
    if data is None:
      logging.error('Channel retrieval failed (%s, %s).', os, channel)
      return None

    for row in data:
      try:
        if row['os'] == os and row['channel'] == channel:
          return row['download_url']
      except KeyError:
        break

    logging.error('The channel data is invalid (%s, %s).', os, channel)
    return None

  def GetVersionForChannel(self, os, channel):
    """Return the version string for the given OS and channel.

    Args:
      os: A string indicating the operating system requested.
      channel: A string indicating the channel requested.

    Returns:
      A string indicating the version for the given OS and channel.
      None is returned if the data cannot be found due in incorrect arguments.
    """
    # Verify that the arguments are acceptable.
    try:
      os = self._CheckOsParam(os)
      channel = self._CheckChannelParam(channel)
    except InvalidParam:
      logging.error('Channel check failed (%s, %s).', os, channel)
      return None

    # Get the necessary data.
    data = self._RetrieveChannelData()
    if data is None:
      logging.error('Channel retrieval failed (%s, %s).', os, channel)
      return None

    for row in data:
      try:
        if row['os'] == os and row['channel'] == channel:
          return row['version']
      except KeyError:
        break

    logging.error('The channel data is invalid (%s, %s).', os, channel)
    return None

  def IdentifyChannel(self, os, browser_version):
    """Return the channel name for a given version.

    Args:
      os: A string indicating the operating system requested.
      browser_version: String indicating browser version.

    Returns:
      A string indicating Channel.
      None if no matching channel found.
    """
    # Verify that the os argument is acceptable.
    try:
      os = self._CheckOsParam(os)
    except InvalidParam:
      return None

    # Get the necessary data.
    data = self._RetrieveChannelData()

    # Let's see if any channel has that version.
    for row in data:
      try:
        if row['os'] == os and row['version'] == browser_version:
          return row['channel']
      except KeyError:
        logging.error('The channel data is invalid.')
        return None

  def _GetCacheKey(self):
    """Returns the cache key for the specific browser.

    This function is intended to be overloaded by the derived class to provide
    the base class knowledge of its specific data.

    Returns:
      The cache key. (string)

    Raises:
      NotImplementedError: Raised if derived class does not implement.
    """
    raise NotImplementedError

  def _GetChannelData(self):
    """Downloads and prepares the channel data.

    Returns:
      A list of dictionaries where each dictionary represents a channel
      release and contains information about that release.  None is returned
      upon error.

    Raises:
      NotImplementedError: Raised if derived class does not implement.
    """
    raise NotImplementedError

  def _GetChannelList(self):
    """Returns a list of supported channels.

    This function is intended to be overloaded by the derived class to provide
    the base class knowledge of its specific data.

    Returns:
      The channel list. (list)

    Raises:
      NotImplementedError: Raised if derived class does not implement.
    """
    raise NotImplementedError

  def _GetOSList(self):
    """Returns a list of supported OSs.

    This function is intended to be overloaded by the derived class to provide
    the base class knowledge of its specific data.

    Returns:
      The OS list. (list)

    Raises:
      NotImplementedError: Raised if derived class does not implement.
    """
    raise NotImplementedError

  def _GetOSMap(self):
    """Returns the OS map for the specific browser.

    This function is intended to be overloaded by the derived class to provide
    the base class knowledge of its specific data.

    Returns:
      The OS map. (dict)

    Raises:
      NotImplementedError: Raised if derived class does not implement.
    """
    raise NotImplementedError

  def _RetrieveChannelData(self):
    """Retrieves necessary channel data from Omahaproxy.

    Returns:
      Retrieved data.
    """
    # Get the necessary data.
    data = memcache.get(self._GetCacheKey())
    if not data:
      data = self._StoreNewChannelData()
    return data

  def _CheckOsParam(self, os):
    """Verifies that os param is valid and maps appropriately (if needed).

    Args:
      os: A string indicating operating system.

    Returns:
      Verified and transformed os parameter.

    Raises:
      InvalidParam: os parameter is not supported.
    """
    os = os.lower()
    # Let's see if we have to map this OS to omaha based OS name.
    if os in self._GetOSMap():
      os = self._GetOSMap()[os]
    # Check for valid parameter.
    if os not in self._GetOSList():
      raise InvalidParam('Invalid OS parameter.')
    else:
      return os

  def _CheckChannelParam(self, channel):
    """Verifies that channel param is valid.

    Args:
      channel: A string indicating channel.

    Returns:
      Verified and transformed channel parameter.

    Raises:
      InvalidParam: channel parameter is not supported.
    """
    channel = channel.lower()
    # Check for valid parameter.
    if channel in self._GetChannelList():
      return channel

    raise InvalidParam('Invalid Channel parameter.')

  def _StoreNewChannelData(self):
    """Retrieves new channel data and stores it in memcache.

    Returns:
      A list of dictionaries where each dictionary represents a channel
      release and contains information about that release.  None is returned
      upon error.
    """
    data = self._GetChannelData()
    if not data:
      return None

    memcache.set(self._GetCacheKey(), data, time=_HOUR_IN_SECONDS)
    return data
