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


"""Controls the instance by communicating with the server."""


import base64
import json
import sys
import urllib
import urllib2
import zlib

import chrome_manager
import mylogger

logger = mylogger.InitLogging('Bots', True, True)

SERVER = 'http://YOUR_APPENGINE_SERVER_HERE'

# Communication paths
START = '/init/start'
INSTALL_FAILED = '/init/install_failed'
INSTALL_SUCCEEDED = '/init/install_succeeded'
INSTANCE_ID_URL = 'http://169.254.169.254/latest/meta-data/instance-id'
USER_DATA_URL = 'http://169.254.169.254/latest/user-data'


def Start(server):
  """Function run when instance is up and bots scripts run.

  The following process outlines the flow of the function:
      1. Begin by requesting the EC2 specific information from the internal
         Amazon server. Then, send a request to the bots server indicating
         that this instance is starting initialization. The browser OS and
         channel information is available from the EC2 user data.
      2. Install specified browser
      3. Send request to the bots server saying the browser was installed; or
         failed if the install failed.

  Args:
    server: A string representing the server url that does not terminate in a
      slash.
  """
  logger.info('Getting the instance id from the internal EC2 server.')
  instance_id = _GetDataFromUrl(INSTANCE_ID_URL)

  if not instance_id:
    logger.fatal('Failed to connect to the EC2 server to get the instance id.')
    return

  logger.info('Getting the user data from the internal EC2 server.')
  user_data = _GetDataFromUrl(USER_DATA_URL)

  if not user_data:
    logger.fatal('Failed to connect to the EC2 server to get the user data.')
    return
  else:
    try:
      user_data = json.loads(user_data)
    except TypeError:
      logger.fatal('Could not load the user data.')
      return

  logger.info('Notifying the server that this instance is starting setup.')
  _GetDataFromUrl(server + START, {'instance_id': instance_id})

  if 'os' not in user_data or not user_data['os']:
    logger.fatal('User data is invalid; missing os information.')
    return
  if 'channel' not in user_data or not user_data['channel']:
    logger.fatal('User data is invalid; missing channel information.')
    return

  download_info = ''
  if 'download_info' in user_data and user_data['download_info']:
    logger.info('The download information was provided.')
    # Make sure we have a string rather than unicode.
    download_info = str(user_data['download_info'])

  # TODO(user): Consider adding a mapping from os.uname() to Omaha OS to avoid
  #   using an OS param from user data.
  operating_system = user_data['os']
  channel = user_data['channel']

  result_url = INSTALL_SUCCEEDED
  try:
    helper = chrome_manager.ChromeAutomationHelper()
    helper.InstallChrome(operating_system, channel, download_info=download_info)
  except chrome_manager.ChromeAutomationHelperException:
    result_url = INSTALL_FAILED
  # Let's compress and base64 encode data before upload.
  log_data = base64.b64encode(zlib.compress(_GetLog()))
  _Post(server + result_url, instance_id, log_data)


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


def _Post(url, instance_id, data):
  """Sends a request to the server.

  Args:
    url: A string representing the url for the request.
    instance_id: A string representing the EC2 instance id.
    data: A string to send to the url as part of a POST.
  """
  try:
    data_to_send = {'log': data, 'instance_id': instance_id}
    urllib2.urlopen(url, urllib.urlencode(data_to_send))
  except urllib2.URLError:
    logger.info('Failed to connect to server during configuration.')
    return


def _GetLog():
  """Load the log file and return it as a string for upload to the server.

  If the log does not exist then nothing will be sent back.

  Returns:
    Returns a string form of the log.  If the log does not exist then an empty
    string is returned.
  """
  try:
    with open('log.txt', 'r') as f:
      return f.read()
  except IOError:
    return ''


if __name__ == '__main__':
  arg = SERVER
  if len(sys.argv) > 1:
    arg = sys.argv[1]
  Start(arg)
