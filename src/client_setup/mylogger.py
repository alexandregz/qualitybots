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


"""Provides nicely formatted logging using python's builtin logger."""




import logging
import sys


def InitLogging(logger_name, enable_console_log=True, enable_file_log=True):
  """Initialize logging.

  Args:
    logger_name: A string name for the logger.
    enable_console_log: A boolean flag for enabling console log (default:True).
    enable_file_log: A boolean flag for enabling file log (default: True).

  Returns:
    Logger object.
  """
  logger = logging.getLogger(logger_name)
  logger.setLevel(logging.DEBUG)
  debug_formatter = logging.Formatter(
      '\n<<%(levelname)s>>,%(asctime)s, %(module)s,line#%(lineno)d - '
      '%(message)s')
  formatter = logging.Formatter(
      '\n<<%(levelname)s>>,%(asctime)s - %(message)s')

  if enable_file_log:
    fh = logging.FileHandler('log.txt')
    # Let's set the file level logging to DEBUG
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(debug_formatter)
    logger.addHandler(fh)

  if enable_console_log:
    ch = logging.StreamHandler(sys.stdout)
    # Let's set the console level logging to INFO
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

  return logger
