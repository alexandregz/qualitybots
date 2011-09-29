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


"""Handles test distribution and results upload to app engine."""



import base64
import json
import math
import random
import time
import urllib
import urllib2
import zlib

import blobstore_upload
import client_logging


# Define the constants
_BLOBSTORE_UPLOAD_RETRIES = 3
_PIECES_UPLOAD_RETRIES = 3
_MAX_WAIT_TIME = 3
_TEST_DISTRIBUTION_SERVER = 'http://YOUR_APPENGINE_SERVER_HERE'
_FETCH_TEST_URL = _TEST_DISTRIBUTION_SERVER + '/distributor/accept_work_item'
_FINISH_TEST_URL = _TEST_DISTRIBUTION_SERVER + '/distributor/finish_work_item'
_RESULTS_SERVER = 'http://YOUR_APPENGINE_SERVER_HERE'
_RESULTS_UPLOAD_URL = _RESULTS_SERVER + '/putdata'
_LOG_UPLOAD_URL = _RESULTS_SERVER + '/distributor/upload_client_log'

LOGGER_NAME = 'appengine_communicator'

# Initialize the logger for this module
logger = client_logging.GetLogger(LOGGER_NAME)


class CommunicationError(Exception):
  pass


class AuthCookie(object):
  """A data object that contains cookie dictionaries used to authenticate.

  Attributes:
    domain: A string representing the domain to authenticate on.
    cookies: A list of dictionaries that define the cookies to add to the
      browser in order to authenticate for a webpage.
  """

  def __init__(self, domain, cookies):
    self.domain = domain
    self.cookies = cookies


class TestCase(object):
  """A data object describing a test case to run for bots.

  Attributes:
    url: A string indicating the URL to run for the test.
    start_time: A string indicating the start time for the test.
    config: A dictionary that specifies various configuration settings for
      the test.
    test_key: An integer representing the key that identifies this test.
    auth_cookie: An AuthCookie object that represents data for authenticating
      for the test case.
  """

  def __init__(self, url, start_time, config, test_key, auth_domain=None,
               auth_cookies=None):
    self.url = url
    self.start_time = start_time
    self.config = config
    self.test_key = test_key

    self.auth_cookie = None
    if auth_domain and auth_cookies:
      self.auth_cookie = AuthCookie(auth_domain, auth_cookies)


class AppEngineCommunicator(object):
  """Handles communication with the test distributor and results servers.

  Attributes:
    _token: A string representing the token to use to pull tests from the
      distributor.
    _useragent: A string representing the useragent of the browser under test.
    _instance_id: A string representing a unique identifier for the machine
      instance.
    _current_test_case: A TestCase object representing the current test case.
    _log_uploaded: A boolean indicating whether the log file has been uploaded.
  """

  def __init__(self, token, useragent, instance_id):
    # Set up the attributes
    self._token = token
    self._useragent = useragent
    self._instance_id = instance_id
    self._current_test_case = None
    self._log_uploaded = False

  # TODO(user): Move this function into a shared utility module.
  @staticmethod
  def ExponentialBackoff(attempt, max_wait_time=_MAX_WAIT_TIME):
    """Wait a time that increases exponentially with the attempt number.

    Args:
      attempt: The most recent attempt number (starting at 0).
      max_wait_time: An optional int that specifies the max base time to wait
        in seconds.
    """
    sleep_time = math.pow(2, attempt) * random.uniform(0.5, 1.0) * max_wait_time
    time.sleep(sleep_time)

  def FetchTest(self):
    """Fetch a new test from the test distributor.

    This function will not prevent you from fetching another test if you have a
    current test case that hasn't been finished. The old test case will be over
    written by the new test case.

    Returns:
      A TestCase object describing the test case that was fetched. If there are
      no more tests to run, None is returned.

    Raises:
      CommunicationError: There is an error in fetching the test.
    """
    # Fetch the test case from the test distributor.
    try:
      data = urllib.urlencode({
          'tokens': self._token, 'useragent': urllib.quote(self._useragent),
          'instance_id': self._instance_id})
      url_page = urllib2.urlopen(_FETCH_TEST_URL, data)
    except urllib2.URLError:
      self._LogAndRaiseException('Failed to fetch a test from app engine.')

    # Process the data from the test distributor.
    self._current_test_case = None
    try:
      test_dictionary = json.loads(url_page.read())

      # Check if there is a test available.
      if test_dictionary:
        test_config = json.loads(test_dictionary['config'])
        auth_domain = None
        auth_cookies = None

        if 'auth_domain' in test_config:
          auth_domain = test_config['auth_domain']

        if 'auth_cookies' in test_config:
          auth_cookies = test_config['auth_cookies']

        self._current_test_case = TestCase(
            test_dictionary['data_str'][19:-1], test_dictionary['start_time'],
            test_config, test_dictionary['key'], auth_domain=auth_domain,
            auth_cookies=auth_cookies)
    except ValueError:
      logger.exception('Could not process the data from the test distributor.')

    return self._current_test_case

  def FinishTest(self, result):
    """Acknowledge that the current test case has been finished.

    Args:
     result: A string indicating the result of executing the test case.

    Raises:
      CommunicationError: There is an error communicating with
        the test distributor.
    """
    # Make sure there is a current test case to finish.
    if not self._current_test_case:
      return

    try:
      data = urllib.urlencode({'key': self._current_test_case.test_key,
                               'result': result,
                               'instance_id': self._instance_id})
      urllib2.urlopen(_FINISH_TEST_URL, data)
      self._current_test_case = None
    except urllib2.URLError:
      self._LogAndRaiseException('Failed acknowledging that the test finished.')

  def _LogAndRaiseException(self, message):
    """Log the current exception being handled and raise a new exception.

    Args:
      message: A string indicating the message to log and use with the new
        exception.

    Raises:
      CommunicationError: This exception is always raised using the given
        message.
    """
    logger.exception(message)
    raise CommunicationError(message)

  def UploadResults(self, nodes_table, layout_table, dynamic_content_table,
                    png, channel=''):
    """Upload the test case results to the results server.

    Args:
      nodes_table: A list representing the node results from the test case.
      layout_table: A list representing the layout results from the test case.
      dynamic_content_table: A list representing the dynamic content results
        from the test case.
      png: A string representing the binary data for a png image.
      channel: An optional string representing the channel for the browser.

    Raises:
      CommunicationError: The initial upload communication failed.
    """
    # Make sure there is a current test case to upload results for.
    if not self._current_test_case:
      return

    # Format the results data for uploading.
    suite_info = {
        'date': self._current_test_case.start_time,
        'key': self._current_test_case.test_key,
        'refBrowser': self._current_test_case.config['refBrowser'],
        'refBrowserChannel': self._current_test_case.config['refBrowserChannel']
        }

    data_to_send = {
        'userAgent': self._useragent,
        'url': self._current_test_case.url,
        'nodesTable': base64.b64encode(
            zlib.compress(json.dumps(nodes_table), 9)),
        'dynamicContentTable': json.dumps(dynamic_content_table),
        'width': self._current_test_case.config['width'],
        'height': self._current_test_case.config['height'],
        'channel': channel,
        'suiteInfo': json.dumps(suite_info),
        'instance_id': self._instance_id
        }

    # Upload the initial data.
    try:
      initial_send = urllib2.urlopen(
          _RESULTS_UPLOAD_URL, urllib.urlencode(data_to_send))
    except urllib2.URLError:
      self._LogAndRaiseException('Failed on the initial results upload.')

    response = initial_send.read()
    if not response:
      self._LogAndRaiseException(
          'Initial results upload did not provide continuation data.')

    response = json.loads(response)
    upload_key = response['key'].encode('ascii')
    num_pieces = int(response['nPieces'])
    layout_table_length = len(layout_table)

    logger.info('Uploading the image to blobstore with key "%s".', upload_key)
    for attempt in range(_BLOBSTORE_UPLOAD_RETRIES):
      try:
        blobstore_upload.UploadImageToBlobstore(upload_key, png)
        break
      except blobstore_upload.BlobstoreUploadError:
        logger.exception('Blobstore upload failed, attempt %d.', attempt+1)
        AppEngineCommunicator.ExponentialBackoff(attempt)

    # Send the layout table in the requested number of pieces.
    logger.info('Uploading remaining results in %d pieces.', num_pieces)
    n_rows_per_piece = int(math.ceil(layout_table_length / (num_pieces * 1.0)))
    start = 0
    end = n_rows_per_piece
    for i in range(num_pieces):
      data_pieces_to_send = {
          'key': upload_key,
          'layoutTable': json.dumps(layout_table[start:end]),
          'i': i,
          'instance_id': self._instance_id
          }

      for attempt in range(_PIECES_UPLOAD_RETRIES):
        try:
          urllib2.urlopen(_RESULTS_UPLOAD_URL,
                          urllib.urlencode(data_pieces_to_send))
          break
        except urllib2.URLError:
          logger.exception('Piece "%d" upload failed, attempt %d.',
                            i, attempt+1)
          AppEngineCommunicator.ExponentialBackoff(attempt)

      start = end
      end = min(end+n_rows_per_piece, len(layout_table))

  def UploadLog(self, log):
    """Upload the test case results to the results server.

    Args:
      log: A string representing the client log to upload.
    """
    # Upload the log data if this is our first upload.
    if self._log_uploaded:
      return

    try:
      urllib2.urlopen(_LOG_UPLOAD_URL, urllib.urlencode(
          {'log': base64.b64encode(zlib.compress(json.dumps(log), 9)),
           'instance_id': self._instance_id}))
      self._log_uploaded = True
    except:
      raise CommunicationError('Failed to upload the client log.')
