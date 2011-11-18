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


"""Defines functionality for getting data/files from a server.

The current functionality includes:
    GetData - Retrieve data from the given url and parameters.
    GetFile - Download a file from a given url into a specified file.
    GetFileViaFtp - Download a file from a given url into a specified file
        using FTP.
    GetFileViaHttp - Download a file from a given url into a specified file
        using HTTP.
"""

import ftplib
import os
import urllib
import urllib2
import urlparse

import mylogger

_logger = mylogger.InitLogging('UrlHelper', True, True)


class GetFileFailed(Exception):
  pass


def GetData(url, params=None):
  """Get and return data from the given URL.

  Args:
    url: The URL to request data from. (string)
    params: An optional dictionary of URL params to send with the request.
        (dict)

  Returns:
    The data returned from the request to the URL. (string)
  """
  response = None

  if params:
    params = urllib.urlencode(params)
  else:
    params = ''

  try:
    # Let the server know that this instance is starting up.
    response = urllib2.urlopen('%s?%s' % (url, params))
    response = response.read()
  except urllib2.URLError:
    _logger.error('Failed to connect to "%s".', url)

  return response


def GetFile(url, output_filename):
  """Downloads a file from the given url.

  Args:
    url: The url from which to download the file. (string)
    output_filename: The filename and path where the downloaded file will
        be saved. (string)

  Raises:
    GetFileFailed: Raised if there is an error using ftp or creating the file.
  """
  url_parts = urlparse.urlparse(url)
  if url_parts.scheme == 'ftp':
    GetFileViaFtp(url_parts.netloc, url_parts.path, output_filename)
  else:
    GetFileViaHttp(url, output_filename)

  if not os.path.exists(output_filename):
    _logger.fatal('Failed to create file (%s).', output_filename)
    raise GetFileFailed


def GetFileViaFtp(domain, path, output_filename):
  """Download a file from the given url domain/path via ftp.

  Args:
    domain: The url domain. (string)
    path: The url path, which is used to move within the ftp directory
        structure and includes the filename to download. (string)
    output_filename: The filename and path where the downloaded file will
        be saved. (string)

  Raises:
    GetFileFailed: Raised if there is an error using ftp or creating the file.
  """
  try:
    ftp = ftplib.FTP(domain)
    ftp.login()
    ftp.retrbinary('RETR ' + path, open(output_filename, 'wb').write)
    return
  except ftplib.all_errors, e:
    _logger.exception('Failed to download file with path (%s): %s.', path, e)
  except IOError, e:
    _logger.exception('Failed to create file (%s): %s.', output_filename, e)
  finally:
    try:
      ftp.quit()
    except ftplib.all_errors:
      ftp.close()

  raise GetFileFailed


def GetFileViaHttp(url, output_filename):
  """Download a file from the given url via http.

  Args:
    url: The url from which to download the file. (string)
    output_filename: The filename and path where the downloaded file will
        be saved. (string)

  Raises:
    GetFileFailed: Raised if there is an error using ftp or creating the file.
  """
  try:
    urllib.urlretrieve(url, output_filename)
  except (urllib.ContentTooShortError, IOError), e:
    _logger.exception('Failed to download file from url (%s): %s.', url, e)
    raise GetFileFailed
  finally:
    urllib.urlcleanup()
