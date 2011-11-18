#!/usr/bin/python2.6
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


"""Helper class for dealing with Windows specific functionality and data.

The helper class inherits from os_helper.OSHelper.  The base class is intended
to be used as an interface and not use this class directly.
"""



# Disable 'Import not at top of file' lint error.
# pylint: disable-msg=C6204, C6205, W0611
# Try/Except required as the _winreg module is only available on Windows and
# will raise an exception on other operating systems.
try:
  import _winreg
except ImportError:
  pass
import re
import time

import mylogger
import os_helper
import url_helper

# Installer flags and name
#   Flags used to install the browser.  They force the install to proceed
#   silently so no user interaction is required.
_BROWSER_INSTALL_FLAGS = {
    os_helper.CHROME: '--do-not-launch-chrome',
    os_helper.FIREFOX: '-ms'}
#   Flags used to uninstall the browser.  They force the uninstall to proceed
#   silently so no user interaction is required.
_BROWSER_UNINSTALL_FLAGS = {
    os_helper.CHROME: '--force-uninstall --delete-profile',
    os_helper.FIREFOX: '-ms'}
#   The flag used to install some browsers at the system level rather than for
#   the current user.
_INSTALL_SYSTEM_LEVEL = '--system-level'
#   The installer will be downloaded and saved to file with this filename.
_INSTALLER = 'installer.exe'

# Registry specific information
#   When looking for a specific browser within the registry at
#   _REGISTRY_PATH, some browsers names may include version and other
#   information.  These patterns are used to help deduce the correct browser
#   entry.
_REGISTRY_NAME_REGEX = {
    os_helper.CHROME: {
        os_helper.CHROME_BETA: '^Google Chrome$',
        os_helper.CHROME_CANARY: '^Google Chrome$',
        os_helper.CHROME_DEV: '^Google Chrome$',
        os_helper.CHROME_STABLE: '^Google Chrome$'},
    os_helper.FIREFOX: {
        os_helper.FIREFOX_AURORA: '^Aurora \S+ [(]\S+ \S+[)]$',
        os_helper.FIREFOX_STABLE: '^Mozilla Firefox \S+ [(]\S+ \S+[)]$'}}
#   Path to application keys within the registry.  The keys at this location
#   seem to have the most useful information related to this module.  No other
#   paths seemed useful.
_REGISTRY_PATH = r'Software\Microsoft\Windows\CurrentVersion\Uninstall'
#    These are the root keys within the Windows registry.  The first is for
#    system level installations and the second is for user level installations,
#    i.e. for all users or just locally for the current user.
if _winreg:
  _REGISTRY_ROOTS = [_winreg.HKEY_LOCAL_MACHINE, _winreg.HKEY_CURRENT_USER]
#   A key under the browser's key within the registry.  It contains the string
#   Windows uses to uninstall the application when the user asks for it to be
#   uninstalled.
_REGISTRY_UNINSTALL = 'UninstallString'

# Support related information
#   The browser supported by the Windows operating system.
_SUPPORTED_BROWSERS = [os_helper.CHROME, os_helper.FIREFOX]
#   The browser channels supported by the Windows operating system.
_SUPPORTED_CHANNELS = {
    os_helper.CHROME: [os_helper.CHROME_BETA,
                       os_helper.CHROME_CANARY,
                       os_helper.CHROME_DEV,
                       os_helper.CHROME_STABLE],
    os_helper.FIREFOX: [os_helper.FIREFOX_STABLE,
                        os_helper.FIREFOX_AURORA]}

_logger = mylogger.InitLogging('WindowsHelper', True, True)


class _MissingRegistryEntry(Exception):
  pass


class _UnsupportedBrowserChannel(Exception):
  pass


class WindowsHelper(os_helper.OSHelper):
  """Provides helper functionality for the Windows operating system."""

  def Install(self, browser, channel, installer_url, for_system=True):
    """Installs the specified browser channel.

    Assumption:
      The browser channel has already been checked to determine if this
      operating system supports it.

    Args:
      browser: The browser name. (string)
      channel: The browser channel name. (string)
      installer_url: The url for use in downloading the installer. (string)
      for_system: Whether or not to install system-wide or for the user.  Be
          aware that some browsers may only allow system-wide installation.
          (boolean)

    Returns:
      Whether or not installation was successful. (boolean)
    """
    try:
      url_helper.GetFile(installer_url, _INSTALLER)
    except url_helper.GetFileFailed:
      return False

    # Construct command.
    command = [_INSTALLER, _BROWSER_INSTALL_FLAGS[browser]]
    if for_system:
      command.append(_INSTALL_SYSTEM_LEVEL)
    command = ' '.join(command)
    _logger.info(command)

    try:
      self._ExecuteCommand(command)
    except os_helper.ExecuteFailed:
      # Execution can fail, but installation may still be successful.
      pass

    # Sleep for few seconds to ensure all Window registries are updated.
    time.sleep(5)

    # Check if installation is successful.
    try:
      return self.IsInstalled(browser, channel)
    except os_helper.AccessError:
      return False

  def IsInstalled(self, browser, channel):
    """Determines if the given browser is installed for the current OS.

    Assumption:
      The browser channel has already been checked to determine if this
      operating system supports it.

    Args:
      browser: The browser name. (string)
      channel: The browser channel name. (string)

    Returns:
      Whether or not the browser channel is installed already. (boolean)

    Raises:
      os_helper.AccessError: An exception is raised when return False would not
          make sense for the question the function is asking.
    """
    try:
      # __GetBrowserKeys cleans up its keys before raising an exception.
      keys = self.__GetBrowserKeys(browser, channel)
    except _MissingRegistryEntry:
      _logger.fatal('Could not open registry keys.')
      raise os_helper.AccessError
    except _UnsupportedBrowserChannel:
      _logger.fatal('Browser and channel have no regex pattern.')
      raise os_helper.AccessError

    self.__CleanupKeys(keys)  # Does not empty array during cleanup.

    if keys:
      return True
    else:
      return False

  @staticmethod
  def IsSupported(browser, channel):
    """Determines if the given browser channel is supported for the current OS.

    Args:
      browser: The browser name. (string)
      channel: The browser channel name. (string)

    Returns:
      Whether or not the browser and channel are supported. (boolean)
    """
    return (browser in _SUPPORTED_BROWSERS and
            channel in _SUPPORTED_CHANNELS[browser])

  def Uninstall(self, browser, channel):
    """Uninstalls the specified browser; for both system and current user.

    If a key exists in the registry under Uninstall for the given browser then
    it needs to be uninstalled.  The Uninstall registry keys include an
    UninstallString value with the exact string used to uninstall the browser.
    This string with some additional parameters will be run and then checked to
    ensure it succeeded.

    Assumption:
      The browser channel has already been checked to determine if this
      operating system supports it.

    Args:
      browser: The browser name. (string)
      channel: The browser channel name. (string)

    Returns:
      Whether or not the browser was successfully uninstalled. (boolean)
    """
    try:
      # __GetBrowserKeys cleans up its keys before raising an exception.
      keys = self.__GetBrowserKeys(browser, channel)
    except _MissingRegistryEntry:
      _logger.fatal('Could not open registry keys.')
      return False
    except _UnsupportedBrowserChannel:
      _logger.fatal('Browser and channel have no regex pattern.')
      return False

    for browser_key in keys:
      uninstall_string = _winreg.QueryValueEx(browser_key,
                                              _REGISTRY_UNINSTALL)[0]
      command = ('"%s" %s' %
                 (uninstall_string, _BROWSER_UNINSTALL_FLAGS[browser]))
      _logger.info(command)

      try:
        self._ExecuteCommand(command)
      except os_helper.ExecuteFailed:
        # Execution can fail, but uninstall may still be successful.
        pass

    self.__CleanupKeys(keys)

    # Sleep for few seconds to ensure all Window registries are updated.
    time.sleep(5)

    # Check if uninstall is successful.
    try:
      return not self.IsInstalled(browser, channel)
    except os_helper.AccessError:
      return False

  def __CleanupKeys(self, keys):
    """Closes all open registry keys.

    Given a list of open registry keys, close them.

    Args:
      keys: Open registry keys. (list)
    """
    for key in keys:
      _winreg.CloseKey(key)

  def __GetBrowserKeys(self, browser, channel):
    """Returns a list of opened registry keys that match a specific pattern.

    Starting with the Uninstall key, look up the sub keys that match the
    browser channel's name using regular expression matching.  There are
    multiple locations to check, and each will be added to the list of open
    keys returned if a match occurs.  The caller is responsible for closing the
    keys.

    Args:
      browser: The browser name. (string)
      channel: The browser channel name. (string)

    Returns:
      A list containing open keys corresponding to a specific pattern.

    Raises:
      _MissingRegistryEntry: Raised when a key does not exist or it could not
          be opened.
      _UnsupportedBrowserChannel: There is no regular expression for the given
          browser channel.
    """
    if (browser not in _REGISTRY_NAME_REGEX or
        channel not in _REGISTRY_NAME_REGEX[browser]):
      raise _UnsupportedBrowserChannel

    regex = _REGISTRY_NAME_REGEX[browser][channel]

    output = []
    for root_key in _REGISTRY_ROOTS:
      try:
        key = _winreg.OpenKey(root_key, _REGISTRY_PATH)
      except WindowsError:
        self.__CleanupKeys(output)
        raise _MissingRegistryEntry

      # Retrieve list of sub keys and loop over them looking for the browser
      # channel.
      (num_sub_keys, unused_1, unused_2) = _winreg.QueryInfoKey(key)
      for i in range(num_sub_keys):
        sub_key = _winreg.EnumKey(key, i)
        if re.search(regex, sub_key) is not None:
          try:
            output.append(_winreg.OpenKey(key, sub_key))
          except WindowsError:
            output.append(key)  # Close the current key as well as all subkeys.
            self.__CleanupKeys(output)
            raise _MissingRegistryEntry

      _winreg.CloseKey(key)

    return output
