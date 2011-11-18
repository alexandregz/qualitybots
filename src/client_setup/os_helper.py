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


"""Defines information and a helper base class for all OS helper classes.

The OSHelper class contains abstract functions and is intended to be used as a
base class and not instantiated.  Assume derived classes have implemented all
functionality and a try/except is not required when using these functions.
"""



import subprocess

import mylogger

# Operating system specific constants
#   Values derived from platform.uname()[0]
LINUX = 'Linux'
WINDOWS = 'Windows'

# Browser specific constants.  These are replicated for use in client scripts
# from browser_helper.py.
CHROME = 'chrome'
CHROME_BETA = 'beta'
CHROME_CANARY = 'canary'
CHROME_DEV = 'dev'
CHROME_STABLE = 'stable'

FIREFOX = 'firefox'
FIREFOX_AURORA = 'aurora'
FIREFOX_STABLE = 'stable'

_logger = mylogger.InitLogging('OSHelper', True, True)


class AccessError(Exception):
  pass


class ExecuteFailed(Exception):
  pass


class OSHelper(object):
  """Defines the base class for all operating system helper classes."""

  def __init__(self):
    pass

  def Install(self, browser, channel, installer_url, for_system=True):
    """Installs the specified browser channel.

    Args:
      browser: The browser name. (string)
      channel: The browser channel name. (string)
      installer_url: The url for use in downloading the installer. (string)
      for_system: Whether or not to install system-wide or for the user.  Be
          aware that some browsers may only allow system-wide installation.
          (boolean)

    Returns:
      Whether or not installation was successful. (boolean)

    Raises:
      NotImplemenetedError: Derived class has not overridden this function.
    """
    raise NotImplementedError

  def IsInstalled(self, browser, channel):
    """Determines if the given browser is installed for the current OS.

    Args:
      browser: The browser name. (string)
      channel: The browser channel name. (string)

    Returns:
      Whether or not the browser channel is installed already. (boolean)

    Raises:
      NotImplemenetedError: Derived class has not overridden this function.
      os_helper.AccessError: An exception is raised when return False would not
          make sense for the question the function is asking.
    """
    raise NotImplementedError

  @staticmethod
  def IsSupported(browser, channel):
    """Determines if the given browser is supported for the current OS.

    Args:
      browser: The browser name. (string)
      channel: The browser channel name. (string)

    Returns:
      Whether or not the browser and channel are supported. (boolean)

    Raises:
      NotImplemenetedError: Derived class has not overridden this function.
    """
    raise NotImplementedError

  def Uninstall(self, browser, channel):
    """Uninstalls the specified browser; for both system and current user.

    If a key exists in the registry under Uninstall for the given browser then
    it needs to be uninstalled.  The Uninstall registry keys include an
    UninstallString value with the exact string used to uninstall the browser.
    This string with some additional parameters will be run and then checked to
    ensure it succeeded.

    Args:
      browser: The browser name. (string)
      channel: The browser channel name. (string)

    Returns:
      Whether or not the browser was successfully uninstalled. (boolean)

    Raises:
      NotImplemenetedError: Derived class has not overridden this function.
    """
    raise NotImplementedError

  def _ExecuteCommand(self, command):
    """Executes a command on the command line.

    A number of errors are possible, but they do not necessary preclude the
    successful execution of the command.

    Args:
      command: The command to execute. (string)

    Raises:
      ExecuteFailed: Raised if something went wrong while executing the given
          command.
    """
    try:
      p = subprocess.Popen(command, shell=True)
      p.wait()
    except OSError, e:
      _logger.exception('An operating system error occurred: %s.', e)
      raise ExecuteFailed
    except subprocess.CalledProcessError, e:
      _logger.exception('Executed command returned a non-zero value: %s.', e)
      raise ExecuteFailed
    except ValueError, e:
      _logger.exception('Invalid arguments given to the command: %s.', e)
      raise ExecuteFailed
