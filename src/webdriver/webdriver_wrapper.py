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


"""Wrap webdriver to perform actions with the browser."""




from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.common import desired_capabilities

import chrome_resize
import client_logging


# Test timeout in seconds.
DEFAULT_TEST_TIMEOUT = 600

DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 512

LOGGER_NAME = 'webdriver_wrapper'

# Initialize the logger for this module
logger = client_logging.GetLogger(LOGGER_NAME)


class SpawnError(Exception):
  pass


class ExecutionError(Exception):
  pass


class TimeoutError(Exception):
  pass


class ChromeWithProfile(webdriver.Chrome):
  """
  """
  def __init__(self, executable_path="chromedriver", port=0):
    self.service = webdriver.chrome.service.Service('chromedriver', port=0)
    self.service.start()

    caps = desired_capabilities.DesiredCapabilities.CHROME
    caps.update({'chrome.switches': ['--user-data-dir=%s' %
                                     chrome_resize.GetChromeProfilePath()]})

    webdriver.remote.webdriver.WebDriver.__init__(
        self, command_executor=self.service.service_url,
        desired_capabilities=caps)


class WebdriverWrapper(object):
  """A wrapper around webdriver used to control a browser.

  Attributes:
    _driver: The webdriver object used to control the browser.
  """

  def __init__(self):
    self._driver = None

  def __del__(self):
    self.KillDriver()

  def AddCookies(self, cookies):
    """Add the given list of cookies to the browser.

    Args:
      cookies: A list of dictionaries describing the cookies to add. The
        dictionaries should have the following attributes describing
        the cookie: domain, secure, value, expiry, path, http_only, and name.
    """
    if self._driver:
      for cookie in cookies:
        self._driver.add_cookie(cookie)

  def DeleteAllCookies(self):
    """Delete all the cookies for the current domain that the browser is on."""
    if self._driver:
      self._driver.delete_all_cookies()

  def ExecuteScript(self, script, timeout=DEFAULT_TEST_TIMEOUT):
    """Execute a given javascript script in the current browser.

    Args:
      script: A string representing the javascript to execute.
      timeout: An optional integer specifying a timeout in seconds to set
        for the script execution.

    Returns:
      The output from the script is returned. If the driver instance doesn't
      exist, None is returned.

    Raises:
      ExecutionError: The javascript failed to execute properly.
    """
    if not self._driver:
      return None

    try:
      self._driver.set_script_timeout(timeout)
      return self._driver.execute_script(script)
    except exceptions.TimeoutException:
      logger.exception('Timeout executing the script.')
      raise TimeoutError('Timeout executing the script.')
    except exceptions.WebDriverException:
      logger.exception('Error executing the script.')
      raise ExecutionError('Error executing the script.')

  def GetScreenshot(self):
    """Takes a screenshot of the current page and returns it as a base64 string.

    Returns:
      A base64-encoded string representing a PNG image of the current page.
      If there is no current driver, None is returned.
    """
    if not self._driver:
      return None

    return self._driver.get_screenshot_as_base64()

  def GetUserAgent(self):
    """Get the useragent from the current webdriver browser.

    Returns:
      A string that represents the useragent for the current webdriver browser.
    """
    if not self._driver:
      return None

    try:
      useragent = self.ExecuteScript('return window.navigator.userAgent;')

      if useragent:
        useragent.encode('ascii')

      logger.info('Using browser with useragent "%s"', useragent)
      return useragent
    except ExecutionError:
      logger.exception('There was an error trying to get the useragent.')
      return None

  def IsRunning(self):
    """Return a boolean indicating whether a webdriver instance is running."""
    return self._driver is not None

  def KillDriver(self):
    """If a webdriver instance exists, kill the instance."""
    if self._driver:
      self._driver.quit()
      self._driver = None

  def NavigateToSite(self, url):
    """Navigate the browser to the given site.

    Args:
      url: A string representing the URL of the site to navigate to.

    Raises:
      ExecutionError: The webdriver failed to navigate to the specified url.
    """
    if not self._driver:
      return

    try:
      self._driver.get(url)
    except exceptions.WebDriverException:
      logger.exception('Failed to navigate to the specified url: %s', url)
      raise ExecutionError(
          'Failed to navigate to the specified url: %s' % url)

  def RefreshPage(self):
    """Refresh the current browser page."""
    if self._driver:
      self._driver.refresh()

  def ResizeBrowser(self, width, height):
    """Attempt to resize the browser to the given width and height.

    Args:
      width: An int representing the requested width for the browser in pixels.
      height: An int representing the requested height for the browser in
        pixels.
    """
    if not self._driver:
      return None

    try:
      self.ExecuteScript('window.resizeTo(%(width)d, %(height)d);' %
                         {'width': width, 'height': height})
    except ExecutionError:
      logger.exception('There was an error trying to get resize the browser.')

  # TODO(user): Add more browsers after they have been tested (IE, Android).
  # TODO(user): Set the width and height based on each test's specifications.
  def SpawnChromeDriver(self, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
    """Spawns a Chrome webdriver instance.

    Raises:
      SpawnException: There is an error spawning the instance.
    """
    # Resize the browser through the profile
    chrome_resize.SetChromeWindowSize(width, height)

    self._SpawnWebDriver(ChromeWithProfile)

  def SpawnFirefoxDriver(self):
    """Spawns a Firefox webdriver instance.

    Raises:
      SpawnError: There is an error spawning the instance.
    """
    self._SpawnWebDriver(webdriver.Firefox)

  def _SpawnWebDriver(self, driver_function):
    """Spawns a given webdriver instance.

    Args:
      driver_function: A function that can be called to spawn the requested
        webdriver instance.

    Raises:
      SpawnException: There is an error spawning the instance.
    """
    # Make sure we only have one webdriver instance running.
    if self._driver:
      self.KillDriver()

    try:
      self._driver = driver_function()
    except exceptions.WebDriverException:
      logger.exception('Failed to spawn a webdriver instance.')
      raise SpawnError('Failed to spawn a webdriver instance.')
