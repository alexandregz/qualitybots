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


"""Provides a class for managing browsers on the current machine.

The purpose of this class is to provide a buffer between the user and the
os_helper.OSHelper by automatically determining the current operating system.
The buffer takes care of determining whether or not the operating system and
browser channel are supported and will only return a valid BrowserManager if
all supported, otherwise an exception will be raised.  With the assumption that
Browsermanager is valid, all the calls are simply forwarded to the os_helper
with some addition logging.  In the end, this removes a lot of overhead that
would be necessary if users were only provided os_helper classes.  This allows
the os_helper classes to assume support has been determined prior to calling
their functions.

Assumptions:
    The server will spin up the appropriate type of instance and the operating
    system will be deduced using platform.uname()[0].

The primary functionality for the BrowserManager class is:
    Install - Given the url for the installer, download and install it.
    IsInstalled - Checks if the browser channel is installed.
    @staticmethod
    IsSupported - Checks if the browser channel is supported by the operating
        system.
    Uninstall - Uninstalls the specified browser channel; does not check if the
        browser is currently installed.
"""



import platform

import mylogger
import os_helper
import windows_helper

_logger = mylogger.InitLogging('BrowserManager', True, True)


class NotSupported(Exception):
  pass


class BrowserManager(object):
  """Class that allows users to manager browser installations.

  Attributes:
    browser: The browser name. (string)
    channel: The browser channel. (string)
    operating_system: The operating system name as defined by
        platform.uname()[0]. (string)
    __os_helper: A class to help with platform specific installation.
        (os_helper.OSHelper)
  """

  def __init__(self, browser, channel):
    """Constructs a new BrowserManager with the given browser and channel.

    Args:
      browser: The browser name. (string)
      channel: The browser channel name. (string)

    Raises:
      NotSupported: Raised if the current operating system is not supported.
    """
    self.browser = browser
    self.channel = channel
    self.operating_system = platform.uname()[0]

    _logger.info(
        'Constructing BrowserManager for browser (%s), channel (%s), and the '
        'current OS (%s).', browser, channel, self.operating_system)

    if self.operating_system == os_helper.WINDOWS:
      self.__os_helper = windows_helper.WindowsHelper()
      if self.__os_helper.IsSupported(browser, channel):
        return
      else:
        _logger.fatal('Browser and channel are not supported.')
    else:
      _logger.fatal('Operating system is not supported.')

    raise NotSupported

  def Install(self, installer_url, for_system=True):
    """Handles the installation of the browser channel.

    Args:
      installer_url: The url for use in downloading the installer. (string)
      for_system: Whether or not to install system-wide or for the user.  Be
          aware that some browsers may only allow system-wide installation.
          (boolean)

    Returns:
      Whether or not installation was successful. (boolean)
    """
    _logger.info(
        'Installing browser (%s) and channel (%s) for the current OS (%s).',
        self.browser, self.channel, self.operating_system)

    success = self.__os_helper.Install(self.browser, self.channel,
                                       installer_url, for_system=for_system)

    if success:
      _logger.info('Install successful.')
    else:
      _logger.fatal('Installation failed (%s).', installer_url)

    return success

  def IsInstalled(self):
    """Determines if the specified browser is installed.

    Returns:
      Whether or not the browser channel is installed. (boolean)

    Raises:
      os_helper.AccessError: Raised if there was an issue accessing the
          browser channel's installation information.
    """
    _logger.info('Checking if browser (%s) and channel (%s) are installed.',
                 self.browser, self.channel)

    result = self.__os_helper.IsInstalled(self.browser, self.channel)

    if result:
      _logger.info('Browser channel installed.')
    else:
      _logger.info('Browser channel not installed.')

    return result

  @staticmethod
  def IsSupported(browser, channel):
    """Checks if the given browser channel is supported.

    Args:
      browser: The browser name. (string)
      channel: The browser channel name. (string)

    Returns:
      Whether or not the browser channel is supported by the current operating
      system. (boolean)
    """
    operating_system = platform.uname()[0]

    _logger.info('Checking if for browser (%s), channel (%s) are supported on '
                 'the current OS (%s).', browser, channel, operating_system)

    if operating_system == os_helper.WINDOWS:
      result = windows_helper.WindowsHelper.IsSupported(browser, channel)
      if not result:
        _logger.fatal('Browser channel is not supported.')
    else:
      _logger.fatal('Operating system is not supported.')
      result = False

    return result

  def Uninstall(self):
    """Handles the uninstall process for the specified browser channel.

    Returns:
      Whether or not the uninstall was successful.  If the browser, channel, or
      os is not supported then False will be returned. (boolean)
    """
    _logger.info('Uninstalling browser (%s) and channel (%s).', self.browser,
                 self.channel)

    result = self.__os_helper.Uninstall(self.browser, self.channel)

    if result:
      _logger.info('Uninstall successful.')
    else:
      _logger.info('Uninstall unsuccessful.')

    return result
