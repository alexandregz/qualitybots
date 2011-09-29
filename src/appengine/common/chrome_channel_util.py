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


"""Utility functions to look up the versions associated with Chrome channels.

This common util provides functionality to perform lookups on Chrome channels
and platforms to determine which version is currently released.
"""



import logging
import urllib2

from google.appengine.api import memcache


_HOUR_IN_SECONDS = 60 * 60
_CHANNEL_MEMCACHE_KEY = 'chrome_channels'
_OMAHAPROXY_URL = 'http://omahaproxy.appspot.com'
_DOWNLOAD_INFO_URL = _OMAHAPROXY_URL + '/dl_urls'
_LOOKUP_RETRIES = 3

# 'cf' is Chrome Frame, 'cros' is ChromeOS
_OS_LIST = ['cf', 'linux', 'mac', 'win', 'cros']
_CHANNEL_LIST = ['canary', 'dev', 'beta', 'stable']

# Mapping used for mapping OS name to OS name (_os_list) used by OmahaProxy.
_OS_MAPPING = {'windows': 'win', 'chromeos': 'cros', 'macintosh': 'mac',
               'osx': 'mac'}


class InvalidParamChromeChannel(Exception):
  pass


def GetVersionForChannel(os, channel):
  """Return the version number string for the given OS and Chrome Channel.

  Args:
    os: A string indicating the operating system requested.
    channel: A string indicating the channel requested. This should be one of
      the following: canary, dev, beta, stable.

  Returns:
    A string indicating the Chrome version for the given OS and Channel.
    None is returned if the data cannot be found due to error in incorrect
    arguments.
  """
  # Verify that the arguments are acceptable.
  try:
    os = _CheckOsParam(os)
    channel = _CheckChannelParam(channel)
  except InvalidParamChromeChannel:
    return None

  # Get the necessary data.
  data = _RetrieveChannelData()

  for row in data:
    try:
      if row['os'] == os and row['channel'] == channel:
        return row['current_version']
    except KeyError:
      logging.error('The Chrome channel data is invalid.')
      return None


def IdentifyChannel(os, browser_version):
  """Return the channel name for a given Chrome version.

  Args:
    os: A string indicating the operating system requested.
    browser_version: String indicating Browser(Chrome) Version.

  Returns:
    A string indicating Channel.
    None if no matching channel found.
  """
  # Verify that the os argument is acceptable.
  try:
    os = _CheckOsParam(os)
  except InvalidParamChromeChannel:
    return None

  # Get the necessary data.
  data = _RetrieveChannelData()

  # Let's see if any channel has that version.
  for row in data:
    try:
      if row['os'] == os and row['current_version'] == browser_version:
        return row['channel']
    except KeyError:
      logging.error('The Chrome channel data is invalid.')
      return None


def GetAllChannelVersions(os):
  """Returns all channel versions for a given OS.

  Args:
    os: A string indicating the operating system requested.

  Returns:
    Key-value pair respresenting chrome channel(key) and current version.
    None otherwise.
  """
  # Verify that the os argument is acceptable.
  try:
    os = _CheckOsParam(os)
  except InvalidParamChromeChannel:
    return None

  # Get the necessary data.
  data = _RetrieveChannelData()

  channel_info = {}
  for row in data:
    try:
      if row['os'] == os:
        channel_info[row['channel']] = row['current_version']
    except KeyError:
      logging.error('The Chrome channel data is invalid.')
      return None

  return channel_info


def GetDownloadInfo():
  """Get the download info string from Omahaproxy.

  Returns:
    A string representing the info necessary to download versions of the Chrome
    browser. If the function fails, the empty string is returned.
  """
  for unused_attempt in range(_LOOKUP_RETRIES):
    try:
      download_info = urllib2.urlopen(_DOWNLOAD_INFO_URL)
      return download_info.read()
    except urllib2.URLError:
      continue

  return ''


def _RetrieveChannelData():
  """Retrieves necessary channel data from Omahaproxy.

  Returns:
    Retrieved data.
  """
  # Get the necessary data.
  data = memcache.get(_CHANNEL_MEMCACHE_KEY)
  if not data:
    data = _StoreNewChannelData()
  return data


def _CheckOsParam(os):
  """Verifies that os param is valid and maps appropriately (if needed).

  Args:
    os: A string indicating operating system.

  Returns:
    Verified and transformed os parameter.

  Raises:
    InvalidParamChromeChannel: os parameter is not supported.
  """
  os = os.lower()
  # Let's see if we have to map this OS to omaha based OS name.
  if os in _OS_MAPPING:
    os = _OS_MAPPING[os]
  # Check for valid parameter.
  if os not in _OS_LIST:
    raise InvalidParamChromeChannel('Invalid OS parameter.')
  else:
    return os


def _CheckChannelParam(channel):
  """Verifies that channel param is valid.

  Args:
    channel: A string indicating channel.
  Returns:
    Verified and transformed channel parameter.

  Raises:
    InvalidParamChromeChannel: channel parameter is not supported.
  """
  channel = channel.lower()
  # Check for valid parameter.
  if channel not in _CHANNEL_LIST:
    raise InvalidParamChromeChannel('Invalid Channel parameter.')
  else:
    return channel


def _StoreNewChannelData():
  """Load new Chrome channel data and store it in memcache.

  Returns:
    A list of dictionaries. Each dictionary represents a channel
    release and contains information about that release.
  """
  channel_csv = _GetChannelData()
  if not channel_csv:
    return None

  data = _ParseChannelData(channel_csv)
  memcache.set(_CHANNEL_MEMCACHE_KEY, data, time=_HOUR_IN_SECONDS)
  return data


def _GetChannelData():
  """Look up the channel data from omahaproxy.appspot.com.

  Returns:
    A string representing the CSV data describing the Chrome channels. None is
    returned if reading from the omahaproxy URL fails.
  """
  for unused_i in range(_LOOKUP_RETRIES):
    try:
      channel_csv = urllib2.urlopen(_OMAHAPROXY_URL)
      return channel_csv.read()
    except (urllib2.URLError, urllib2.HTTPError):
      logging.exception('Exception on reading from the omahaproxy URL.')

  return None


def _ParseChannelData(data):
  """Parse a CSV string containing Chrome channel data from omahaproxy.

  Args:
    data: A string of CSV data from omahaproxy.

  Returns:
    A list of dictionaries. Each dictionary represents a channel
    release and contains information about that release.
  """
  data = data.strip()
  rows = data.split('\n')
  keys = rows[0].split(',')
  rows = rows[1:]

  results = []
  for row in rows:
    entries = row.split(',')
    channel_data = {}

    for i in range(len(keys)):
      channel_data[keys[i]] = entries[i]

    results.append(channel_data)

  return results
