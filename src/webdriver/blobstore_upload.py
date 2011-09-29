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


"""Performs the upload of data to blobstore.

This is specifically used to upload a screenshot to blobstore.
"""



import httplib
import mimetypes
import socket
import urllib2
import urlparse

import client_logging

BLOBSTORE_UPLOAD_URL = 'http://YOUR_APPENGINE_SERVER_HERE/getuploadurl'
_MULTIPART_BOUNDARY = '----------Boundary_$#$%_783659204_boundarY'

LOGGER_NAME = 'blobstore_upload'

# Initialize the logger for this module
logger = client_logging.GetLogger(LOGGER_NAME)


class BlobstoreUploadError(Exception):
  pass


def _PostMultipartData(url, fields, files):
  """Post the given fields and files as multipart/form-data.

  Args:
    url: A string representing the URL to POST the data to.
    fields: A list of (name, value) tuples describing form field data.
    files: A list of (name, filename, value) tuples describing the files to
      be uploaded.

  Returns:
    Returns the server's response status code as an integer.
  """
  # Split the host and selector parts of the URL
  urlparts = urlparse.urlsplit(url)
  host = urlparts[1]
  selector = urlparts[2]

  # Create the message body
  content_type, body = _EncodeMultipartFormData(fields, files)

  # Send the message
  try:
    connection = httplib.HTTPConnection(host)
    headers = {'User-Agent': 'Python Blobstore Uploader',
               'Content-Type': content_type}
    connection.request('POST', selector, body, headers)
    result = connection.getresponse()
    return result.status
  except (socket.error, httplib.HTTPException):
    logger.exception('Error uploading the image to blobstore.')
    return None


def _EncodeMultipartFormData(fields, files):
  """Encode the given data into a multipart message.

  This function encodes the data to upload a multipart message. See
  http://en.wikipedia.org/wiki/MIME#Multipart_messages for more information
  on MIME multipart messages.

  Args:
    fields: A list of (name, value) tuples describing form field data.
    files: A list of (name, filename, value) tuples describing the files to
      be uploaded.

  Returns:
    A (content_type, body) tuple that can be uploaded as a multipart message.
  """
  crlf = '\r\n'
  body = []

  # Add the fields
  for (key, value) in fields:
    body.append('--' + _MULTIPART_BOUNDARY)
    body.append('Content-Disposition: form-data; name="%s"' % key)
    body.append('')
    body.append(value)

  # Add the files
  for (key, filename, value) in files:
    body.append('--' + _MULTIPART_BOUNDARY)
    body.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (
        key, filename))
    body.append('Content-Type: %s' % _GetContentType(filename))
    body.append('')
    body.append(value)

  body.append('--' + _MULTIPART_BOUNDARY + '--')
  body.append('')

  body = crlf.join(body)
  content_type = 'multipart/form-data; boundary=%s' % _MULTIPART_BOUNDARY

  return content_type, body


def _GetContentType(filename):
  """Get the MIME type for content based on the given filename.

  Args:
    filename: A string representing the filename for the content.

  Returns:
    A string representing the best guess for the MIME type of the file
    is returned.
  """
  file_type = mimetypes.guess_type(filename)[0]

  if file_type:
    return file_type
  else:
    return 'application/octet-stream'


def _GetBlobstoreUploadUrl():
  """Get the URL to use to upload the data to blobstore.

  Returns:
    The URL string is returned if it is fetched successfully. Otherwise, None
    is returned.
  """
  try:
    return urllib2.urlopen(BLOBSTORE_UPLOAD_URL).read()
  except urllib2.URLError:
    logger.exception('Error retrieving the blobstore upload url.')
    return None


# TODO(user): Consider adding a variation of this function with retries.
def UploadImageToBlobstore(key, png):
  """Upload PNG image data and the corresponding test key to blobstore.

  Args:
    key: A string representing the app engine key for the result to associate
      the image data with.
    png: A string representing the binary data for a PNG image to upload.

  Raises:
    BlobstoreUploadError: This exception is raised if either the upload URL
      retrieval or the data upload fail.
  """
  if not png or not key:
    raise BlobstoreUploadError('Incorrect values given for upload.')

  # Get the unique blobstore upload url
  upload_url = _GetBlobstoreUploadUrl()

  if upload_url:
    logger.info('Uploading the image to the following url: %s', upload_url)
  else:
    logger.error('The blobstore upload url could not be retrieved.')
    raise BlobstoreUploadError('Could not retrieve the blobstore upload url.')

  fields = [('key', key)]
  files = [('file', '%s.png' % key, png)]

  # Post the image as a multipart message to blobstore
  result = _PostMultipartData(upload_url, fields, files)

  # Check the result
  if not result or result != 302:
    raise BlobstoreUploadError('Submitting data to blobstore was unsuccessful.')
