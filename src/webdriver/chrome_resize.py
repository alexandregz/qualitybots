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


"""Resize the chrome browser window to the appropriate size."""




import getpass
import os
import platform
import re
import subprocess
import time

import client_logging


CHROME_WINDOWS_USER_DATA = ('C:\\Users\\%s\\AppData\\Local\\Google\\Chrome\\'
                            'User Data\\')
CHROME_LINUX_USER_DATA = '~/.config/google-chrome/'


CHROME_WINDOWS_EXECUTABLE = ('C:\\Program Files\\Google\\Chrome\\'
                             'Application\\chrome.exe')
CHROME_LINUX_EXECUTABLE = 'google-chrome'

# This is structured data from the Chrome profile for defining the size.
WINDOW_PLACEMENT = """"window_placement": {
         "bottom": %(height)d,
         "left": 0,
         "maximized": false,
         "right": %(width)d,
         "top": 0,
         "work_area_bottom": 1080,
         "work_area_left": 0,
         "work_area_right": 1920,
         "work_area_top": 0
      }"""
BROWSER_PREFERENCE = '\n"browser": {\n%s\n},'

# This is the outer area surrounding the browser viewport (the browser chrome)
CHROME_HEIGHT = 82
CHROME_WIDTH = 20

LOGGER_NAME = 'chrome_resize'

# Initialize the logger for this module
logger = client_logging.GetLogger(LOGGER_NAME)


def GetChromeProfilePath():
  """Return the path the to the Chrome profile.

  Returns:
    A string representing the path to the Chrome profile for the current OS.
  """
  operating_system = platform.uname()[0]

  if operating_system == 'Windows':
    return CHROME_WINDOWS_USER_DATA % getpass.getuser()
  elif operating_system == 'Linux':
    return CHROME_LINUX_USER_DATA


def GetChromeProfilePreferences():
  """Return the path the to the Chrome profile preferences file.

  Returns:
    A string representing the path to the Chrome profile preferences file
    for the current OS.
  """
  return os.path.join(GetChromeProfilePath(), 'Default', 'Preferences')


def _GetChromeExecutable():
  """Return the path the to the Chrome executable.

  Returns:
    A string representing the path to the Chrome executable for the current OS.
  """
  operating_system = platform.uname()[0]

  if operating_system == 'Windows':
    return CHROME_WINDOWS_EXECUTABLE
  elif operating_system == 'Linux':
    return CHROME_LINUX_EXECUTABLE


def _SpawnAndKillChrome():
  """Spawn and kill Chrome in order to set up the profile."""
  # Spawn and kill chrome to set up the profile
  chrome_process = subprocess.Popen(_GetChromeExecutable())
  time.sleep(10)
  chrome_process.terminate()


def SetChromeWindowSize(width, height):
  """Set the default size for the Chrome window.

  The Chrome window size must be set before Chrome is opened.

  Args:
    width: An integer representing the width for the browser.
    height: An integer representing the height for the browser.
  """
  try:
    with open(GetChromeProfilePreferences(), 'r') as f:
      file_contents = f.read()
  except IOError:
    logger.info('The Preferences file does not exist, spawning Chrome.')
    _SpawnAndKillChrome()

  _SetChromeWindowPreferences(GetChromeProfilePreferences(),
                              width, height)


def _SetChromeWindowPreferences(preference_filename, width, height):
  """Update the Chrome window size by editing the Preferences file directly.

  Args:
    preference_filename: A string representing the Chrome Preference file to
      open and edit.
    width: An integer representing the width for the browser.
    height: An integer representing the height for the browser.
  """
  # Check if the file exists
  file_contents = ' '
  try:
    with open(preference_filename, 'r') as f:
      file_contents = f.read()
  except IOError:
    logger.error('The Preferences file does not exist, not setting the size.')
    return

  with open(preference_filename, 'w') as f:
    # Find the window_placement section and replace it.
    window_placement = WINDOW_PLACEMENT % {'width': width + CHROME_WIDTH,
                                           'height': height + CHROME_HEIGHT}

    if re.search(r'"window_placement": {[^}]*}', file_contents):
      f.write(re.sub(r'"window_placement": {[^}]*}', window_placement,
                     file_contents))
    else:
      f.write(file_contents[0] +
              (BROWSER_PREFERENCE % window_placement) +
              file_contents[1:])
