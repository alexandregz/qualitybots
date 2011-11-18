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

import browser_manager
import mylogger
import url_helper

_SERVER = 'http://YOUR_APPENGINE_SERVER_HERE'

# Communication paths
_START = '/init/start'
_INSTALL_FAILED = '/init/install_failed'
_INSTALL_SUCCEEDED = '/init/install_succeeded'
_INSTANCE_ID_URL = 'http://169.254.169.254/latest/meta-data/instance-id'
_USER_DATA_URL = 'http://169.254.169.254/latest/user-data'

_logger = mylogger.InitLogging('InstanceManager', True, True)


def Start(server):
  """Function runs when an instance is spun up.

  The following process outlines the flow of the function:
      1. Begin by requesting EC2 specific information from the internal
         Amazon server.
      2. Request run specific information such as the browser and channel
         available from the EC2 user data.
      3. Send a request to the bots server indicating that this instance is
         starting initialization.
      4. Install specified browser
      5. Send request to the bots server saying the browser was installed; or
         failed if the install failed.

  Args:
    server: The server url that does not terminate in a slash. (string)
  """
  # Retrieve instance information.
  _logger.info('Getting the instance id from the internal EC2 server.')
  instance_id = url_helper.GetData(_INSTANCE_ID_URL)

  if not instance_id:
    _logger.fatal(
        'Failed to connect to the EC2 server to get the instance id.')
    return

  _logger.info('Getting the user data from the internal EC2 server.')
  user_data = url_helper.GetData(_USER_DATA_URL)

  if not user_data:
    _logger.fatal('Failed to connect to the EC2 server to get the user data.')
    return
  else:
    try:
      user_data = json.loads(user_data)
    except TypeError:
      _logger.fatal('Could not load the user data.')
      return

  # Process browser information extracted from user_data.
  _logger.info('Notifying the server that this instance is starting setup.')
  url_helper.GetData(server + _START, {'instance_id': instance_id})

  if 'browser' not in user_data or not user_data['browser']:
    _logger.fatal('User data is invalid; missing browser information.')
    return
  if 'channel' not in user_data or not user_data['channel']:
    _logger.fatal('User data is invalid; missing channel information.')
    return
  if 'installer_url' not in user_data or not user_data['installer_url']:
    _logger.fatal('User data is invalid; missing installer_url information.')
    return

  browser = user_data['browser']
  channel = user_data['channel']
  installer_url = user_data['installer_url']

  # Manage browser setup by installing the appropriate version if possible.
  result_url = _INSTALL_SUCCEEDED
  try:
    manager = browser_manager.BrowserManager(browser, channel)
    # If machine crashed and was rebooted then check to see if the browser is
    # already installed.  If it is then mark install as successful and return.
    if not manager.IsInstalled():
      if not manager.Install(installer_url):
        result_url = INSTALL_FAILED
  except browser_manager.NotSupported:
    result_url = INSTALL_FAILED

  # Retrieve logs and let server know of the process's success.
  # Let's compress and base64 encode data before upload.
  log_data = base64.b64encode(zlib.compress(_GetLog()))
  _Post(server + result_url, instance_id, log_data)


def _Post(url, instance_id, data):
  """Sends a request to the server.

  Args:
    url: The url for the request. (string)
    instance_id: The EC2 instance id. (string)
    data: Data to send to the url as part of a POST. (string)
  """
  try:
    # TODO(user): Change data_to_send.log to .data and then move to
    # url_helper.
    data_to_send = {'log': data, 'instance_id': instance_id}
    urllib2.urlopen(url, urllib.urlencode(data_to_send))
  except urllib2.URLError:
    _logger.info('Failed to connect to server during configuration.')
    return


def _GetLog():
  """Load the log file and return it as a string for upload to the server.

  Returns:
    Returns the log.  If the log does not exist then an empty string is
    returned. (string)
  """
  try:
    with open('log.txt', 'r') as f:
      return f.read()
  except IOError:
    return ''


if _name_ == '_main_':
  arg = _SERVER
  if len(sys.argv) > 1:
    arg = sys.argv[1]
  Start(arg)
