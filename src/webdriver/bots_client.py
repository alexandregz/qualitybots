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


"""Drives the analysis of a URL through webdriver."""



import atexit
import base64
import json
import logging
import optparse
import sys
import time
import urllib
import urllib2

import appengine_communicator
import client_logging
import webdriver_wrapper


BROWSER_OPTIONS = ['chrome', 'firefox']

COMMUNICATION_RETRIES = 3
EXECUTION_RETRIES = 3

# The amount of time to wait for the page to load in seconds.
WEBSITE_LOAD_TIME = 5

SUCCESS = 'success'
FAILURE = 'failure'
UPLOAD_ERROR = 'upload_error'
TIMEOUT_ERROR = 'timeout_error'

_INSTANCE_ID_URL = 'http://169.254.169.254/latest/meta-data/instance-id'
_USER_DATA_URL = 'http://169.254.169.254/latest/user-data'

LOGGER_NAME = 'bots_client'

# Initialize the logger for this module
logger = client_logging.GetLogger(LOGGER_NAME)


def _LoadFileToString(filename):
  """Load the given file to a string.

  Args:
    filename: A string representing the name of the file to load.

  Returns:
    A string representing the file contents.
  """
  with open(filename) as f:
    return f.read()


def _GetDataFromUrl(url, params=None):
  """Get and return data from the given URL.

  Args:
    url: A string indicating the URL to request data from.
    params: An optional dictionary of URL params to send with the request.

  Returns:
    A string representing the data returned from the request to the URL.
  """
  response = None

  if params:
    params = urllib.urlencode(params)
  else:
    params = ''

  try:
    # Let the server know that this instance is starting up.
    response = urllib2.urlopen(url+'?'+params)
    response = response.read()
  except urllib2.URLError:
    logger.error('Failed to connect to "%s".', url)

  return response


def _FetchData(data_url):
  """Fetch data from the given url.

  Args:
    data_url: A string representing the url to fetch data from.

  Returns:
    A string representing the fetched data. None is returned if the fetch fails.
  """
  data = None
  for attempt in range(COMMUNICATION_RETRIES):
    data = _GetDataFromUrl(data_url)

    if not data:
      logger.error('Failed to get the data from the EC2 server.')
      appengine_communicator.AppEngineCommunicator.ExponentialBackoff(attempt)
    else:
      break

  return data


def _FetchInstanceId():
  """Fetch the instance id from the internal Amazon server.

  Returns:
    A string representing the instance id or None if fetching the instance id
    fails.
  """
  return _FetchData(_INSTANCE_ID_URL)


def _FetchUserDataTokenAndChannel():
  """Fetch the instance id from the internal Amazon server.

  Returns:
    A tuple of strings representing the token and channel. If there are any
    failures or the data is not available, either of the values can be None.
  """
  user_data = None
  try:
    user_data = json.loads(_FetchData(_USER_DATA_URL))
  except (TypeError, ValueError):
    logger.exception('Could not load the user data as a JSON dictionary.')

  token = None
  if user_data and 'token' in user_data:
    token = user_data['token']

  channel = None
  if user_data and 'channel' in user_data:
    channel = user_data['channel']

  return (token, channel)


def _SpawnWebdriver(driver, browser):
  """Spawn the webdriver browser for the given browser string.

  Args:
    driver: A webdriver_wrapper.WebdriverWrapper object to use to spawn the
      browser.
    browser: A string representing the browser to spawn.
  """
  if browser == 'chrome':
    driver.SpawnChromeDriver()
  elif browser == 'firefox':
    driver.SpawnFirefoxDriver()


def _FetchTestCase(communicator):
  """Fetch a test case from the distributor.

  Args:
    communicator: An appengine_communicator.AppEngineCommunicator object to
      use for requesting a test case.

  Returns:
    A appengine_communicator.TestCase object that represents the new test case.
    If no test case is available, None is returned.
  """
  test_case = None
  for attempt in range(COMMUNICATION_RETRIES):
    try:
      test_case = communicator.FetchTest()
      break
    except appengine_communicator.CommunicationError:
      logger.exception('Failed to load the test on attempt "%d".', attempt+1)
      appengine_communicator.AppEngineCommunicator.ExponentialBackoff(attempt)

  return test_case


def _Authenticate(driver, test_case):
  """Authenticate the browser if necessary for the test case.

  Args:
    driver: A webdriver_wrapper.WebdriverWrapper object for the browser under
      test.
    test_case: An appengine_communicator.TestCase object describing the test to
      process.
  """
  if test_case.auth_cookie is not None:
    logger.info('Authenticating for "%s".', test_case.url)
    driver.NavigateToSite(test_case.auth_cookie.domain)
    driver.DeleteAllCookies()
    driver.AddCookies(test_case.auth_cookie.cookies)
    driver.RefreshPage()


def _ProcessTestCase(driver, test_case, test_script):
  """Process a test case.

  Args:
    driver: A webdriver_wrapper.WebdriverWrapper object for the browser under
      test.
    test_case: An appengine_communicator.TestCase object describing the test to
      process.
    test_script: A string representing the javascript to run against the URL.

  Returns:
    A tuple of status string, script execution results, and a string
    representing the base64-encoded screenshot.
  """
  status = SUCCESS
  results = None
  base64_png = None
  for attempt in range(EXECUTION_RETRIES):
    try:
      driver.ResizeBrowser(int(test_case.config['width']),
                           int(test_case.config['height']))

      logger.info('Navigating to the "%s" and waiting for it to load.',
                  test_case.url)
      driver.NavigateToSite(test_case.url)
      time.sleep(WEBSITE_LOAD_TIME)

      # Insert the script into the browser and run it.
      logger.info('Executing the processing script.')
      driver.ExecuteScript(test_script)
      results = driver.ExecuteScript(
          'return appcompat.webdiff.webdriver.executeScript();')

      # Perform basic validation on the results.
      if (not results or
          'layout_table' not in results or
          'nodes_table' not in results or
          'dynamic_content_table' not in results):
        raise webdriver_wrapper.ExecutionError(
            'Webdriver did not get proper results.')

      # Take a screenshot
      logger.info('Taking a screenshot of the page.')
      base64_png = driver.GetScreenshot()
      if not base64_png:
        base64_png = ''

      status = SUCCESS
      break
    except webdriver_wrapper.ExecutionError:
      status = FAILURE
      logger.exception('Failed to process URL "%s" on attempt "%d".',
                       test_case.url, attempt+1)
    except webdriver_wrapper.TimeoutError:
      status = TIMEOUT_ERROR
      logger.exception(
          'Failed to process URL "%s" on attempt "%d" due to timeout.',
          test_case.url, attempt+1)

  return (status, results, base64_png)


def _UploadTestResults(communicator, test_case, results, base64_png, channel):
  """Process a test case.

  Args:
    communicator: An appengine_communicator.AppEngineCommunicator object to
      use for requesting a test case.
    test_case: An appengine_communicator.TestCase object describing the test to
      process.
    results: A list of dictionaries describing the test results.
    base64_png: A string respresenting a base64 png screenshot.
    channel: A string representing the channel for the browser under test.

  Returns:
    A string indicating whether the test was a SUCCESS, FAILURE, or experienced
    an UPLOAD_ERROR.
  """
  test_result = FAILURE
  if results:
    for attempt in range(COMMUNICATION_RETRIES):
      try:
        communicator.UploadResults(
            results['nodes_table'], results['layout_table'],
            results['dynamic_content_table'],
            base64.b64decode(base64_png), channel=channel)
        test_result = SUCCESS
        break
      except appengine_communicator.CommunicationError:
        logger.exception('Failed to upload test results on attempt "%d".',
                         attempt+1)
        test_result = UPLOAD_ERROR
        appengine_communicator.AppEngineCommunicator.ExponentialBackoff(attempt)
      except KeyError:
        logger.exception('Failed to upload test results on attempt "%d".',
                         attempt+1)
        test_result = FAILURE
        appengine_communicator.AppEngineCommunicator.ExponentialBackoff(attempt)
  else:
    logger.error(
        'Did not get the results from executing the test script for "%s".',
        test_case.url)

  return test_result


def _FinishTestCase(communicator, test_result):
  """Report that a test case is finished.

  Args:
    communicator: An appengine_communicator.AppEngineCommunicator object to
      use for requesting a test case.
    test_result: A string indicating the test result.
  """
  for attempt in range(COMMUNICATION_RETRIES):
    try:
      communicator.FinishTest(test_result)
      break
    except appengine_communicator.CommunicationError:
      logger.exception('Failed to finish the test on attempt "%d".',
                       attempt+1)
      appengine_communicator.AppEngineCommunicator.ExponentialBackoff(attempt)


def _ShutdownClient(communicator, instance_id=''):
  """Shutdown the client and upload the current client log.

  Args:
    communicator: An appengine_communicator.AppEngineCommunicator object to
      use for requesting a test case.
    instance_id: An optional string that specifies the machine's instance id
      if a communicator object has not been provided.
  """
  # After logging is shutdown, no more logging should be done.
  logging.shutdown()

  if not communicator:
    if instance_id:
      communicator = appengine_communicator.AppEngineCommunicator(
          None, None, instance_id)
    else:
      return

  with open(client_logging.LOG_FILENAME) as log_file:
    log = log_file.read()
    for attempt in range(COMMUNICATION_RETRIES):
      try:
        communicator.UploadLog(log)
        break
      except appengine_communicator.CommunicationError:
        appengine_communicator.AppEngineCommunicator.ExponentialBackoff(attempt)


def main():
  # Parse the flags
  parser = optparse.OptionParser()

  parser.add_option(
      '--token', action='store', type='string', dest='token', default='',
      help='The token to use when requesting test cases to run.')
  parser.add_option(
      '--test_script', action='store', type='string', dest='test_script',
      default='webdriver_content_script.js',
      help='The filename of the script to run against each URL.')
  parser.add_option(
      '--browser', action='store', type='string', dest='browser',
      default='chrome', help='The browser to use for testing URLs.')

  (FLAGS, args) = parser.parse_args()

  if FLAGS.browser not in BROWSER_OPTIONS:
    parser.error('The --browser option must be one of: %s' %
                 str(BROWSER_OPTIONS))

  instance_id = None
  communicator = None
  try:
    logger.info('Starting client initialization.')

    instance_id = _FetchInstanceId()
    if not instance_id:
      logger.error('Could not get the instance id.')
      return

    # Verify the flags.
    if FLAGS.token:
      token = FLAGS.token
    else:
      token, channel = _FetchUserDataTokenAndChannel()
      if not token:
        logger.error('Could not get a valid token.')
        return
      if not channel:
        channel = ''

    logger.info('Instance id and user data were loaded.')

    # Create a webdriver instance to use.
    logger.info('Creating the web driver instance.')
    driver = webdriver_wrapper.WebdriverWrapper()
    _SpawnWebdriver(driver, FLAGS.browser)

    # Get the useragent from the current browser.
    logger.info('Getting the user agent.')
    useragent = driver.GetUserAgent()
    if not useragent or useragent == 'None':
      logger.fatal('Could not get the useragent from the browser.')
      return

    logger.info('The useragent string was loaded: "%s".', useragent)

    communicator = appengine_communicator.AppEngineCommunicator(
        token, useragent, instance_id)

    # Register our atexit handler now that the communicator has been created.
    atexit.register(_ShutdownClient, communicator)

    # Load the test script.
    logger.info('Loading the test script.')
    test_script = _LoadFileToString(FLAGS.test_script)

    logger.info('Starting the test case fetching loop.')
    while True:
      # Check webdriver status.
      if not driver.IsRunning():
        logger.error('The webdriver browser is not running, restarting.')
        _SpawnWebdriver(driver, FLAGS.browser)
        if not driver.IsRunning():
          logger.fatal('Could not restart the webdriver browser.')
          return

      # Fetch the URL to process.
      logger.info('Fetching a test case.')
      test_case = _FetchTestCase(communicator)

      if not test_case or not test_case.url:
        logger.info('No more URLs were available to process.')
        return

      # Authenticate if necessary.
      logger.info('Authenticating if necessary.')
      _Authenticate(driver, test_case)

      # Process the URL.
      logger.info('Processing the test case: %s', test_case.url)
      status, results, base64_png = _ProcessTestCase(driver, test_case,
                                                     test_script)

      # Upload the results.
      if status == SUCCESS:
        logger.info('Uploading the results.')
        status = _UploadTestResults(communicator, test_case, results,
                                    base64_png, channel)
      else:
        logger.info('Test case status is "%s", not uploading results.', status)

      # Finish the URL.
      logger.info('Finishing the test case for "%s" with status "%s".',
                  test_case.url, status)
      _FinishTestCase(communicator, status)
  finally:
    logger.info('Shutting down the client.')
    _ShutdownClient(communicator, instance_id=instance_id)


if __name__ == '__main__':
  main()
