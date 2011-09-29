#!/usr/bin/python2.6
#
# Copyright 2010 Google Inc. All Rights Reserved.
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


"""A helper library which provides support for (windows) chrome installation.

The library provides methods to check if Chrome is installed and the ability to
install/uninstall it. Currently, there is no cleanup of previously downloaded
installers and their associated folders.
"""



import cStringIO
import csv
import os
import subprocess
import sys
import time
import urllib
import urllib2
import _winreg
import mylogger

logger = mylogger.InitLogging('Chrome_SiteCompat', True, True)

# Url that contains the list of the latest Chrome builds.
OMAHA_URL = 'https://omahaproxy.appspot.com/dl_urls'

# Installer flags and executable
CHROME_SILIENT_INSTALL_FLAGS = ' --do-not-launch-chrome --system-level'
CHROME_SILIENT_UNINSTALL_FLAGS = (' --uninstall --force-uninstall '
                                  '--delete-profile --system-level')
INSTALLER_FILENAME = 'installer.exe'

# Registry keys
CHROME_EXE_KEY = (r'Software\Microsoft\Windows\CurrentVersion\App Paths'
                  r'\chrome.exe')
VERSION_KEY_PATH = r'Software\Google'
VERSION_KEY = 'bots_installed_version'


class ChromeAutomationHelperException(Exception):
  pass


# TODO(user): Refactor this into base class and create factory which will
# return platform specific implementation.
class ChromeAutomationHelper(object):
  """Provides methods to support chrome automation."""

  def InstallChrome(self, operating_system, channel, download_info=''):
    """Silent install of Chrome for all users.

    Args:
      operating_system: A string representing the desired operating system for
        the build.  Acceptable values are ['win'].
      channel: A string representing which variant is desired.  Acceptable
        values are ['canary', 'dev', 'beta', 'stable'].
      download_info: An optional string that represents the info necessary to
        download the correct Chrome browser version.

    Raises:
      ChromeAutomationHelperException: Raised if something went wrong
        retrieving information or downloading/installing of Chrome.
    """
    logger.info('Downloading latest Chrome version information.')

    (url, version) = self._GetLatestChromeDownloadUrl(
        operating_system, channel, download_info=download_info)

    if self.IsChromeInstalled():
      if self._GetInstalledVersion() == version:
        logger.info('Chrome already installed.  Exiting.')
        return
      else:
        logger.info('Uninstalling current version of Chrome because a new '
                    'version is available and will be installed.')
        self.UninstallChrome()

    logger.info('Installation of Chrome has begun.')
    local_file = self._DownloadLatestBuild(url, version)

    command = '"' + local_file + '"' + CHROME_SILIENT_INSTALL_FLAGS
    logger.info('Installation command: ' + command)
    self._ExecuteCommand(command)

    if not self.IsChromeInstalled():
      logger.info('Chrome not installed.')
      self._LogAndRaise('Something went wrong, installation can not verify '
                        'installation.')

    # Set the version of the newly installed chrome.  Upon failure uninstall.
    try:
      self._SetInstalledVersion(version)
    except ChromeAutomationHelperException, exception:
      logger.info('Chrome not installed.')
      self.UninstallChrome()
      self._LogAndRaise(str(exception))

    logger.info('Chrome installed successfully.')

  def IsChromeInstalled(self):
    """Check if Chrome is installed.

    Returns:
      True if installed
      False if not installed
    """
    is_chrome_installed = False
    key = None
    try:
      # Check for the regkey value presence.
      key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, CHROME_EXE_KEY)
      chrome_exe_path = _winreg.QueryValueEx(key, None)[0]
      is_chrome_installed = True
      logger.info('IsInstalled: Chrome is installed at %s' % chrome_exe_path)
    except WindowsError:
      logger.info('IsInstalled: Chrome is not installed.')
    finally:
      if key:
        _winreg.CloseKey(key)

    return is_chrome_installed

  def UninstallChrome(self):
    """Silent uninstall of Chrome for all users.

    Raises:
      ChromeAutomationHelperException: Raised if something went wrong
        uninstalling Chrome.
    """
    try:
      version = self._GetInstalledVersion()
    except ChromeAutomationHelperException:
      logger.info('No version found, nothing to uninstall.')
      return

    local_file = self._GetOrCreateFilename(version)
    if not os.path.exists(local_file):
      self._LogAndRaise('Chrome installed but no installer to use for '
                        'uninstall.')

    logger.info('Uninstalling Chrome.')
    command = '"' + local_file + '"' + CHROME_SILIENT_UNINSTALL_FLAGS
    logger.info(command)
    self._ExecuteCommand(command)

    if self.IsChromeInstalled():
      self._LogAndRaise('Failed to uninstall Chrome.')

    logger.info('Chrome has been successfully uninstalled.')

    # TODO(user): Determine if it should go here or before the
    # the uninstall.  What is more important a spare key or a spare installed
    # browser?
    self._RemoveVersionKey()

  def _DownloadLatestBuild(self, url, version):
    """Downloads the latest build from the given url.

    Args:
      url: The url from which to download the installer.
      version: The version of the installer.

    Returns:
      A string specifying where the installer is located.

    Raises:
      ChromeAutomationHelperException: Raised if any of the information could
        not be found.
    """
    local_file = self._GetOrCreateFilename(version)

    try:
      urllib.urlretrieve(url, local_file)
    except urllib.ContentTooShortError, content_exception:
      self._LogAndRaise('Failed to download installer. The given error is: ' +
                        str(content_exception))
    except IOError, url_exception:
      self._LogAndRaise('Failed to retrieve chrome installer information '
                        'from ' + url + '. The given error is: ' +
                        str(url_exception))
    finally:
      urllib.urlcleanup()

    if not os.path.exists(local_file):
      self._LogAndRaise('Failed to download installer. File does not exist.')

    return local_file

  def _ExecuteCommand(self, command):
    """Executes a command on the command line.

    Args:
      command: A string representing the command to execute.

    Raises:
      ChromeAutomationHelperException: Raised if the command fails.
    """
    try:
      p = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE)
      p.stdin.close()
      if p.wait() != 0:
        self._LogAndRaise('Wait failed while executing command: ' + command)
    except OSError, os_error:
      self._LogAndRaise('An operating system error occurred with error:' +
                        os_error)
    except subprocess.CalledProcessError, called_process_error:
      self._LogAndRaise('Executed command returned a non-zero value with '
                        'error: ' + called_process_error)
    except ValueError, value_error:
      self._LogAndRaise('Invalid arguments given to the command with error: ' +
                        value_error)

    # Sleep for few seconds to ensure all Window registries are updated.
    time.sleep(5)

  def _GetOrCreateFilename(self, version):
    """Creates a path to a file using the given version.

    In addition to generating the path, it also will create any missing folders
    needed by the path.

    Args:
      version: The version of chrome.

    Returns:
      A string representing the path to a specific installer file.
    """
    local_path = os.path.join(os.path.dirname(sys.argv[0]), version)
    if not os.path.exists(local_path):
      os.mkdir(local_path)
    local_file = os.path.join(local_path, INSTALLER_FILENAME)
    return str(local_file)

  def _GetInstalledVersion(self):
    """Retrieves the version number of the currently installed Chrome.

    This function assumes that the installation of Chrome has already been
    verified.

    Returns:
      A string representing the version number.

    Raises:
      ChromeAutomationHelperException: Raised if the version could not be
        retrieved.
    """
    key = None
    try:
      # Check for the regkey value presence.
      key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, VERSION_KEY_PATH)
      version = _winreg.QueryValueEx(key, VERSION_KEY)[0]
      return version
    except WindowsError:
      logger.error('Version not found.')
      return None
    finally:
      if key:
        _winreg.CloseKey(key)

  def _GetLatestChromeDownloadUrl(self, operating_system, channel,
                                  download_info=''):
    """Finds the url of the latest Chrome build.

    Using an Omaha server, retrieve a list of the current builds and extract
    the appropriate information.  The format of each line in the downloaded
    file is [os, channel, version, download url].

    Args:
      operating_system: A string representing the desired operating system for
        the build.  Acceptable values are ['win'].
      channel: A string representing which variant is desired.  Acceptable
        values are ['canary', 'dev', 'beta', 'stable'].
      download_info: An optional string that represents the info necessary to
        download the correct Chrome browser version.

    Returns:
      Returns a tuple of strings (url, version).

    Raises:
      ChromeAutomationHelperException: Raised if any of the information could
        not be found.
    """
    retries = 10
    response = None

    # Access to the url can be unstable and can potentially require a large
    # unknown number of retries.
    if download_info:
      response = cStringIO.StringIO(download_info)
    else:
      for retry in range(retries):
        try:
          response = urllib2.urlopen(OMAHA_URL)
          break
        except urllib2.URLError, url_exception:
          logger.info('Retry (' + str(retry) + ') Failed to retrieve chrome ' +
                      'installer information from ' + OMAHA_URL +
                      '. The given error is: ' + str(url_exception))

    if not response:
      self._LogAndRaise('Failed to download list of latest builds.')

    reader = csv.DictReader(response)
    for line in reader:
      if operating_system == line['os'] and channel == line['channel']:
        return (line['dl_url'], line['current_version'])

    self._LogAndRaise('Did not find the specified build in the list of latest '
                      'builds.')

  def _LogAndRaise(self, message):
    """Logs a message and then raises an exception with the same value.

    Args:
      message: A string representing the message to log/raise.

    Raises:
      ChromeAutomationHelperException: Raised with the given message.
    """
    logger.info(message)
    raise ChromeAutomationHelperException(message)

  def _RemoveVersionKey(self):
    """Removes the registry key for the version number.

    Raises:
      ChromeAutomationHelperException: Raised if the version could not be
        retrieved.
    """
    key = None
    try:
      key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, VERSION_KEY_PATH,
                            0, _winreg.KEY_SET_VALUE)
      _winreg.DeleteValue(key, VERSION_KEY)
    except WindowsError:
      self._LogAndRaise('Version information could not be removed.')
    finally:
      if key:
        _winreg.CloseKey(key)

  def _SetInstalledVersion(self, version):
    """Sets the version number of the currently installed Chrome.

    Args:
      version: A string representing the version of Chrome installed.

    Raises:
      ChromeAutomationHelperException: Raised if the version could not be
        retrieved.
    """
    key = None
    try:
      key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, VERSION_KEY_PATH,
                            0, _winreg.KEY_SET_VALUE)
      _winreg.SetValueEx(key, VERSION_KEY, 0, _winreg.REG_SZ,
                         version)
    except WindowsError:
      self._LogAndRaise('Version information could not be set.')
    finally:
      if key:
        _winreg.CloseKey(key)
