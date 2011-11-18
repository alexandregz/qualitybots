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


"""A class that defines helper functions for processing Chrome channel info.

This class is derived from channel_util and supplies those functions needed by
the general process to update channel info.  See channel_util for more
information.
"""


import logging
import urllib2

from common import channel_util

_CHANNEL_MEMCACHE_KEY = 'chrome_channels'
_OMAHAPROXY_URL = 'http://omahaproxy.appspot.com'
_DOWNLOAD_INFO_URL = _OMAHAPROXY_URL + '/dl_urls'
_LOOKUP_RETRIES = 3

_BROWSER = 'chrome'
_CHANNEL_LIST = ['canary', 'dev', 'beta', 'stable']
# 'cf' is Chrome Frame, 'cros' is ChromeOS
_OS_LIST = ['cf', 'linux', 'mac', 'win', 'cros']
# Mapping used for mapping OS name to OS name (_os_list) used by OmahaProxy.
_OS_MAPPING = {'windows': 'win', 'chromeos': 'cros', 'macintosh': 'mac',
               'osx': 'mac'}

# Maps data keys from the Omaha proxy to those expected by channel_util.
_TRANSLATE_KEY = {'browser': channel_util.KEY_BROWSER,
                  'channel': channel_util.KEY_CHANNEL,
                  'dl_url': channel_util.KEY_DOWNLOAD_URL,
                  'os': channel_util.KEY_OS,
                  'current_version': channel_util.KEY_VERSION}


class ChromeChannelUtil(channel_util.ChannelUtil):
  """Defines helper functions for processing channel info."""

  def _GetCacheKey(self):
    """Returns the cache key for the specific browser.

    This function is intended to be overloaded by the derived class to provide
    the base class knowledge of its specific data.

    Returns:
      The cache key. (string)
    """
    return _CHANNEL_MEMCACHE_KEY

  def _GetChannelData(self):
    """Downloads and prepares the channel data.

    Look up the channel data from omahaproxy.appspot.com.

    Returns:
      A list of dictionaries where each dictionary represents a channel
      release and contains information about that release.  None is returned
      upon error.
    """
    for unused_i in range(_LOOKUP_RETRIES):
      try:
        channel_csv = urllib2.urlopen(_OMAHAPROXY_URL)
        return self._ParseChannelData(channel_csv.read())
      except (urllib2.URLError, urllib2.HTTPError):
        logging.exception('Exception on reading from the omahaproxy URL.')

    return None

  def _GetChannelList(self):
    """Returns a list of supported channels.

    This function is intended to be overloaded by the derived class to provide
    the base class knowledge of its specific data.

    Returns:
      The channel list. (list)
    """
    return _CHANNEL_LIST

  def _GetOSList(self):
    """Returns a list of supported OSs.

    This function is intended to be overloaded by the derived class to provide
    the base class knowledge of its specific data.

    Returns:
      The OS list. (dict)
    """
    return _OS_LIST

  def _GetOSMap(self):
    """Returns the OS map for the specific browser.

    This function is intended to be overloaded by the derived class to provide
    the base class knowledge of its specific data.

    Returns:
      The OS map. (dict)
    """
    return _OS_MAPPING

  def _ParseChannelData(self, data):
    """Parse a CSV string containing Chrome channel data from omahaproxy.

    The parsing will convert the csv string into the appropriate dictionaries
    as defined in channel_utils file overview.

    Args:
      data: A string of CSV data from omahaproxy.

    Returns:
      A list of dictionaries where each dictionary represents a channel
      release and contains information about that release.  None is returned
      upon error.
    """
    data = data.strip()
    rows = data.split('\n')
    keys = rows[0].split(',')
    rows = rows[1:]

    results = []
    for row in rows:
      entries = row.split(',')
      channel_data = {channel_util.KEY_BROWSER: _BROWSER}

      for i in range(len(keys)):
        key = keys[i]
        if not key in _TRANSLATE_KEY:
          logging.warn('chrome_channel_util could not convert %s into known '
                       'set of keys.', key)
          continue
        key = _TRANSLATE_KEY[key]
        channel_data[key] = entries[i]

      if not (channel_util.KEY_CHANNEL in channel_data and
              channel_util.KEY_DOWNLOAD_URL in channel_data and
              channel_util.KEY_OS in channel_data and
              channel_util.KEY_VERSION in channel_data):
        logging.error('chrome_channel_util failed to construct a complete '
                      'installer object.')
        return None

      results.append(channel_data)

    return results
