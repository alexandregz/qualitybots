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


"""Provides nice formatted logging using the standard logging module.

Nice formatted logging wrapper on top of python logging.
"""




import logging
import sys


DEFAULT_LOGGING_LEVEL = logging.INFO
LOG_FILENAME = 'bots_client_log.txt'
COMMUNICATION_RETRIES = 3


def GetLogger(logger_name, enable_console_log=True, enable_file_log=True):
  """Get and initialize a logger.

  Args:
    logger_name: A string name for the logger.
    enable_console_log: An optional boolean flag for enabling console log
      (default:True).
    enable_file_log: An optional boolean flag for enabling file log
      (default: True).

  Returns:
    A logger object to use for all logging.
  """
  logger = logging.getLogger(logger_name)

  # If the logger already exists and has been initialized, return it.
  if logger.handlers:
    return logger

  logger.setLevel(DEFAULT_LOGGING_LEVEL)
  formatter = logging.Formatter(
      fmt='%(levelname)s %(asctime)s %(module)s:%(lineno)d] %(message)s',
      datefmt='%m%d %H:%M:%S')

  if enable_file_log:
    try:
      file_handler = logging.FileHandler(LOG_FILENAME)
      file_handler.setLevel(DEFAULT_LOGGING_LEVEL)
      file_handler.setFormatter(formatter)
      logger.addHandler(file_handler)
    except IOError:
      # Error creating the file, omit this handler.
      pass

  if enable_console_log:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(DEFAULT_LOGGING_LEVEL)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

  return logger
