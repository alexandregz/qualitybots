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


"""Browser User Agent (UA) Parser/detector."""




import re


WEBKIT = 'applewebkit'
GECKO = 'gecko'
CHROME = 'chrome'
CHROME_OS = 'cros'
FIREFOX = 'firefox'
LINUX = 'linux'
MAC = 'macintosh'
OS_X = 'os x'
UNKNOWN = 'unknown'
WIN = 'windows'
WIN_2000 = 'win_2000'
WIN_XP = 'win_xp'
WIN_VISTA = 'win_vista'
WIN_7 = 'win_7'
WIN_NT_VERSIONS = {'5.0': WIN_2000, '5.1': WIN_XP, '5.2': WIN_XP,
                   '6.0': WIN_VISTA, '6.1': WIN_7}
X11 = 'x11'

# Regular expressions.
BROWSER_INFO_REGEX = re.compile(r'(firefox|chrome)/([bpre0-9.]*)')
OS_INFO_REGEX = re.compile(r'\([^\)]*\)')
CROS_VERSION_REGEX = re.compile(r'cros\W+.*(\d+\.\d+\.\d+)')
WIN_VERSION_REGEX = re.compile(r'nt\W*(\d\.?\d?)')
MAC_VERSION_REGEX = re.compile(r'os\W+x\W+(\d+[._]\d+[._]?\d*)')
WEBKIT_ENGINE_REGEX = re.compile(r'applewebkit/([0-9.]*)')
GECKO_ENGINE_REGEX = re.compile(r'(rv:[bpre0-9.]*)\)\W+gecko')


class UAParserException(Exception):
  pass


class MissingUAException(Exception):
  pass


class UAParser(object):
  """Class for Parsing Browser's User Agent(UA) String.

  Only supports parsing UA for chrome and firefox at this time.

  Usage:
    ua_parser = UAParser(user_agent)
    # To get browser family.
    ua_parser.GetBrowserFamily()
    # To get browser version.
    ua_parser.GetBrowserVersion()
    Similarly OS and Layout family and version can be parsed.

  Attributes:
    user_agent_lowercase: User Agent String in Lowercase.
    __browser_family: Browser family (e.g. Chrome, Firefox).
    __browser_version: Browser version.
    __os_family: Operating system family (e.g. Linux, Windows, cros).
    __os_version: Operating system version.
    __layout_engine_family: Browser layout engine family (e.g. applewebkit,
        gecko)
    __layout_engine_version: Browser layout engine version.
  """

  def __init__(self, user_agent):
    """Init method for User Agent Parser.

    Args:
      user_agent: User Agent String.

    Raises:
      MissingUAException: Missing user agent string parameter.
    """
    if not user_agent:
      raise MissingUAException('Missing User agent parameter.')
    self.user_agent_lowercase = user_agent.lower()
    self.__browser_family = None
    self.__browser_version = None
    self.__os_family = None
    self.__os_version = None
    self.__layout_engine_family = None
    self.__layout_engine_version = None

  def _ParseBrowserInfo(self):
    """Parses browser family and version information from UA."""
    browser_info = BROWSER_INFO_REGEX.search(self.user_agent_lowercase).groups()
    if not browser_info:
      raise UAParserException('Could not parse browser family from user agent.')
    self.__browser_family = browser_info[0]
    self.__browser_version = browser_info[1]

  def GetBrowserFamily(self):
    """Parses browser family from UA.

    Returns:
      Browser family.
    """
    if not self.__browser_family:
      self._ParseBrowserInfo()
    return self.__browser_family

  def GetBrowserVersion(self):
    """Parses browser version from UA.

    Returns:
      Browser version.
    """
    if not self.__browser_version:
      self._ParseBrowserInfo()
    return self.__browser_version

  def _ParseOSInfo(self):
    """Parses OS family and version information from UA."""
    # Let's look for anything within braces.
    ua_parts = OS_INFO_REGEX.findall(self.user_agent_lowercase)
    if not ua_parts:
      return
    # Let's get rid of opening and closing braces and split.
    ua_os_part = ua_parts[0][1:-1].split(';')[0].strip()
    # Check for linux family of OS.
    if ua_os_part.find(X11) != -1:
      # Let's check for chromeos.
      if ua_parts[0].find(CHROME_OS) != -1:
        self.__os_family = CHROME_OS
        self.__os_version = CROS_VERSION_REGEX.findall(ua_parts[0])[0]
      else:
        self.__os_family = LINUX
        self.__os_version = UNKNOWN
    elif ua_os_part.find(WIN) != -1:
      self.__os_family = WIN
      win_version = WIN_VERSION_REGEX.findall(ua_parts[0])
      if win_version:
        self.__os_version = WIN_NT_VERSIONS[win_version[0]]
      else:
        self.__os_version = UNKNOWN
    elif ua_os_part.find(MAC) != -1:
      self.__os_family = MAC
      mac_version = MAC_VERSION_REGEX.findall(ua_parts[0])
      if mac_version:
        self.__os_version = mac_version[0]

  def GetOSFamily(self):
    """Parses OS family from UA.

    Returns:
      Operating System (OS) family.
    """
    if not self.__os_family:
      self._ParseOSInfo()
    return self.__os_family

  def GetOSVersion(self):
    """Parses OS version from UA.

    Returns:
      Operating system (OS) version.
    """
    if not self.__os_version:
      self._ParseOSInfo()
    return self.__os_version

  def _ParseLayoutEngineInfo(self):
    """Parses layout engine family and version information from UA."""
    if not self.__browser_family:
      self._ParseBrowserInfo()
    if self.__browser_family == CHROME:
      self.__layout_engine_family = WEBKIT
      webkit_engine_info = WEBKIT_ENGINE_REGEX.findall(
          self.user_agent_lowercase)
      if webkit_engine_info:
        self.__layout_engine_version = webkit_engine_info[0]
    elif self.__browser_family == FIREFOX:
      self.__layout_engine_family = GECKO
      gecko_version = GECKO_ENGINE_REGEX.findall(
          self.user_agent_lowercase)
      if gecko_version:
        self.__layout_engine_version = gecko_version[0]

  def GetLayoutEngineFamily(self):
    """Parses layout engine family from UA.

    Returns:
      Layout Engine family.
    """
    if not self.__layout_engine_family:
      self._ParseLayoutEngineInfo()
    return self.__layout_engine_family

  def GetLayoutEngineVersion(self):
    """Parses layout engine version from UA.

    Returns:
      Layout Engine version.
    """
    if not self.__layout_engine_version:
      self._ParseLayoutEngineInfo()
    return self.__layout_engine_version
