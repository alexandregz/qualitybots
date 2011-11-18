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


"""A class that defines helper functions for processing Firefox channel info.

This class is derived from channel_util and supplies those functions needed by
the general process to update channel info.  See channel_util for more
information.
"""



import ftplib
import logging
import re

from common import channel_util

_CHANNEL_MEMCACHE_KEY = 'firefox_channels'

# Defines the channel names.
_AURORA = 'aurora'
_STABLE = 'stable'

# Timestamp format: {numbers} {year}{month}{day}{numbers}.
_AURORA_REGEX_TIMESTAMP = r'\d{3} (\d{4})(\d{2})(\d{2})',
# Format: ^timestamp-xx-xx-xx-mozilla-aurora$
# The numbers in the middle are unknowns, but don't cares.
_AURORA_REGEX_TIMESTAMP_TO_PATH = r'-\d{2}-\d{2}-\d{2}-mozilla-aurora'
_DOMAIN = 'ftp.mozilla.org'
_FTP_PATH = {
    _AURORA: 'pub/firefox/nightly',
    _STABLE: 'pub/firefox/releases'}
_INSTALLER_PATTERN = {
    _AURORA: r'(firefox-(\S+)[.]%s[.]%s[.]installer[.]exe)',
    _STABLE: r'(Firefox Setup (\S+)[.]exe)[^.]?'}
_LATEST = {
    _AURORA: 'latest-mozilla-aurora',
    _STABLE: 'latest'}
_LOCALE = {_AURORA: 'en-US',
           _STABLE: 'en-US'}

_BROWSER = 'firefox'
_CHANNEL_LIST = [_AURORA, _STABLE]
_OS_LIST = ['win32']
_OS_MAPPING = {'windows': 'win32'}


class FirefoxChannelUtil(channel_util.ChannelUtil):
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

    This is a multi-step process as each channel involves different steps.

    TODO(user): Each OS should have a mapping of supported browser
    channels, but this function does not reflect that.  Update for correctness.

    Returns:
      A list of dictionaries where each dictionary represents a channel
      release and contains information about that release.  None is returned
      upon error.
    """
    results = []

    for os in _OS_MAPPING:
      for channel in _CHANNEL_LIST:
        data = self._GetChannelInfo(channel, os)
        if not data:
          return None
        results.append(data)

    return results

  def _GetChannelInfo(self, channel, os):
    """Determines the correct url for downloading the Firefox installer.

    Args:
      channel: The browser channel name. (string)
      os: The operating system name. (string)

    Returns:
      The dictionary of information related to the installer as specified in
      channel_util or None upon failure. (dict)
    """
    # Determine path and url to "latest" version.
    path = self._GetPath(channel, os)
    url = 'ftp://%s/%s' % (_DOMAIN, path)

    # Open ftp connection and read a specific directory.
    try:
      ftp = ftplib.FTP(_DOMAIN)
      ftp.login()
      ftp.cwd(path)
      files = ftp.nlst()
    except ftplib.all_errors, e:
      logging.exception('FTP error accessing Firefox installer directory: ', e)
      return None

    # Create match pattern for installer filename.
    regex = self._GetInstallerFilenameRegex(channel, os)

    # Process the filenames in the directory and check for the expected match.
    result = self._GetFilename(files, regex)
    if result is None:
      logging.error('Unable to locate installer for %s: %s.', channel, result)
      return None

    installer_name = result.group().strip()
    version = result.group(2)

    # Determine the full url instead of the reference url so it can be
    # downloaded later if the "latest" changes in the mean time.
    if channel == _AURORA:
      url = self._GetFullAuroraUrl(channel, ftp, installer_name)
    elif channel == _STABLE:
      url = self._GetFullStableUrl(channel, os, version, installer_name)
    else:
      logging.error('Unknown channel (%s) found for Firefox.', channel)
      return None

    try:
      ftp.quit()
    except ftplib.all_errors:
      ftp.close()

    return {channel_util.KEY_BROWSER: _BROWSER,
            channel_util.KEY_CHANNEL: channel,
            channel_util.KEY_DOWNLOAD_URL: url,
            channel_util.KEY_OS: os,
            channel_util.KEY_VERSION: version}

  def _GetChannelList(self):
    """Returns a list of supported channels.

    This function is intended to be overloaded by the derived class to provide
    the base class knowledge of its specific data.

    Returns:
      The channel list. (list)
    """
    return _CHANNEL_LIST

  def _GetFilename(self, filenames, pattern):
    """Searchs a list of filenames for the first one to contain the pattern.

    Args:
      filenames: A list of file names. (list of strings)
      pattern: A regular expression match pattern. (string)

    Returns:
      Returns the resulting match or None if a file was not found. (MatchObject)
    """
    for filename in filenames:
      try:
        result = re.search(pattern, filename)
      except (TypeError, IndexError, re.error), e:
        logging.exception('Failed to process filename (%s) failed: %s',
                          filename, e)
        return None
      if result is not None:
        return result

    logging.error('File with pattern (%s) not found.', pattern)
    return None

  def _GetFullAuroraUrl(self, channel, ftp, installer_name):
    """Get the full url path to the installer.

    Args:
      channel:  The browser channel name. (string)
      ftp: An open ftp connection.
      installer_name: The name of the installer. (string)

    Returns:
      The full url path or None upon failure. (string)
    """
    # Get timestamp for the installer file.
    timestamp = ftp.sendcmd('MDTM %s' % installer_name)

    # Change to the main Aurora folder
    ftp.cwd('/%s' % _FTP_PATH[channel])
    files = ftp.nlst()

    # Determine regular expression to match the latest aurora version's true
    # folder.
    # Timestamp format: {numbers} {year}{month}{day}{numbers}.
    result = re.search(_AURORA_REGEX_TIMESTAMP, timestamp)
    if result is None:
      logging.error('Unable to locate true installer path for %s.', channel)
      return None
    timestamp = '-'.join(result.groups())
    # Format: ^timestamp-xx-xx-xx-mozilla-aurora$
    # The numbers in the middle are unknowns, but don't cares.
    regex = '^(%s%s)$' % (timestamp, _AURORA_REGEX_TIMESTAMP_TO_PATH)

    # Process the filenames in the directory and check for the expected match.
    result = self._GetFilename(files, regex)
    if result is None:
      logging.error('Unable to locate true installer path for %s: %s.',
                    channel, result)
      return None

    return 'ftp://%s/%s/%s/%s' % (_DOMAIN, _FTP_PATH[channel],
                                  result.group(), installer_name)

  def _GetFullStableUrl(self, channel, os, version, installer_name):
    """Get the full url path to the installer.

    Args:
      channel:  The browser channel name. (string)
      os: The operating system name. (string)
      version: The version of the installer. (string)
      installer_name: The name of the installer. (string)

    Returns:
      The full url path. (string)
    """
    return 'ftp://%s/%s/%s/%s/%s/%s' % (_DOMAIN, _FTP_PATH[channel], version,
                                        _OS_MAPPING[os], _LOCALE[channel],
                                        installer_name)

  def _GetInstallerFilenameRegex(self, channel, os):
    """Create match pattern for installer filename.

    Args:
      channel:  The browser channel name. (string)
      os: The operating system name. (string)

    Returns:
      The pattern for the installer's filename. (string)
    """
    if channel == _AURORA:
      return _INSTALLER_PATTERN[channel] % (_LOCALE[channel], _OS_MAPPING[os])
    else:
      return _INSTALLER_PATTERN[channel]

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

  def _GetPath(self, channel, os):
    """Determine path to the "latest" version.

    Args:
      channel:  The browser channel name. (string)
      os: The operating system name. (string)

    Returns:
      The url path to the installer's directory. (string)
    """
    if channel == _STABLE:
      return '%s/%s/%s/%s' % (_FTP_PATH[channel], _LATEST[channel],
                              _OS_MAPPING[os], _LOCALE[channel])
    else:
      return '%s/%s' % (_FTP_PATH[channel], _LATEST[channel])
