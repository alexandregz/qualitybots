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


"""Downloads and executes the client files from the app engine server."""



import json
import math
import random
import subprocess
import sys
import time
import urllib
import urllib2

import mylogger


logger = mylogger.InitLogging('Bots', True, True)

SERVER = 'http://YOUR_APPENGINE_SERVER_HERE'
CLIENT_FILE_LIST = '/client_file_list'
COMMUNICATION_RETRIES = 3

# Max wait time in seconds between retries
_MAX_WAIT_TIME = 3


class FileDownloadError(Exception):
  pass


class FileExecutionError(Exception):
  pass


def _ExponentialBackoff(attempt, max_wait_time=_MAX_WAIT_TIME):
  """Wait a time that increases exponentially with the attempt number.

  Args:
    attempt: The most recent attempt number (starting at 0).
    max_wait_time: An optional int that specifies the max base time to wait
      in seconds.
  """
  sleep_time = math.pow(2, attempt) * random.uniform(0.5, 1.0) * max_wait_time
  time.sleep(sleep_time)


def _GetDataFromUrl(url, params=None, retries=COMMUNICATION_RETRIES):
  """Get and return data from the given URL.

  Args:
    url: A string indicating the URL to request data from.
    params: An optional dictionary of URL params to send with the request.
    retries: The number of retries if the communication fails.

  Returns:
    A string representing the data returned from the request to the URL.
  """
  response = None

  if params:
    params = urllib.urlencode(params)
  else:
    params = ''

  for attempt in range(retries):
    try:
      response = urllib2.urlopen(url+'?'+params)
      response = response.read()
      break
    except urllib2.URLError:
      logger.error('Failed to connect to "%s".', url)
      _ExponentialBackoff(attempt)

  return response


def _SaveFileFromServer(server, filename):
  """Save the file from the server to a local file.

  Args:
    server: A string indicating the server to pull the file from.
    filename: A string indicating the name of the file to download.

  Raises:
    FileDownloadError: Raised if the file fails to download.
  """
  data = _GetDataFromUrl(server + '/s/' + filename)

  if not data:
    raise FileDownloadError('Could not download "%s"' % filename)

  with open(filename, 'wb') as f:
    f.write(data)


def _ExecutePythonFile(filename):
  """Execute the python file specified by the given filename.

  Args:
    filename: A string indicating the name of the file to execute.

  Returns:
    An integer indicating the return value from executing the file.

  Raises:
    FileExecutionError: Raised if an error occurs during program execution.
  """
  return_code = 1
  try:
    return_code = subprocess.call(['python', filename])
  except (OSError, ValueError):
    logger.exception('The file "%s" did not execute properly.', filename)
    raise FileExecutionError('Failed execution with "%s", filename')

  return return_code


def main(args):
  """The main function that downloads the files and kicks them off.

  Args:
    args: A list of strings representing the program arguments.
  """
  server = SERVER
  if len(args) > 1:
    server = sys.argv[1]

  logger.info('Getting the file list from "%s".', server)
  file_data = _GetDataFromUrl(server + CLIENT_FILE_LIST)

  if not file_data:
    logger.fatal('Could not get the file list from "%s".', server)
    return

  file_data = json.loads(file_data)

  # Download the necessary files.
  logger.info('Downloading the necessary files.')
  for filename in file_data['file_list']:
    logger.info('Downloading "%s".', filename)
    _SaveFileFromServer(server, filename)

  # Execute the specified files.
  logger.info('Executing the specified files.')
  for filename in file_data['execution_list']:
    logger.info('Executing "%s".', filename)
    _ExecutePythonFile(filename)

  logger.info('Finished executing the files.')


if __name__ == '__main__':
  main(sys.argv)
