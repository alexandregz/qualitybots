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


"""Tests for blobstore_upload."""



import base64
import unittest

import blobstore_upload


class BlobstoreUploadTest(unittest.TestCase):

  def setUp(self):
    # Set up the expected values.
    self.base64_png = (
        'iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w3'
        '8GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg==')

    self.expected_result_field = []
    self.expected_result_field.append('--' +
                                      blobstore_upload._MULTIPART_BOUNDARY)
    self.expected_result_field.append(
        'Content-Disposition: form-data; name="key"')
    self.expected_result_field.append('')
    self.expected_result_field.append('1234')
    self.expected_result_field = '\r\n'.join(self.expected_result_field)

    self.expected_result_file = []
    self.expected_result_file.append('--' +
                                     blobstore_upload._MULTIPART_BOUNDARY)
    self.expected_result_file.append(
        'Content-Disposition: form-data; name="file"; filename="1234.png"')
    self.expected_result_file.append('Content-Type: image/png')
    self.expected_result_file.append('')
    self.expected_result_file.append(base64.b64decode(self.base64_png))
    self.expected_result_file = '\r\n'.join(self.expected_result_file)

    self.expected_result_body = []
    self.expected_result_body.append(
        '--' + blobstore_upload._MULTIPART_BOUNDARY + '--')
    self.expected_result_body.append('')
    self.expected_result_body = '\r\n'.join(self.expected_result_body)

  def testGetContentType_ValidPng(self):
    self.assertEqual('image/png', blobstore_upload._GetContentType('test.png'))
    self.assertEqual('image/png', blobstore_upload._GetContentType('jpg.png'))

  def testGetContentType_ValidJpg(self):
    self.assertEqual('image/jpeg',
                     blobstore_upload._GetContentType('test.jpg'))
    self.assertEqual('image/jpeg',
                     blobstore_upload._GetContentType('test.jpeg'))
    self.assertEqual('image/jpeg',
                     blobstore_upload._GetContentType('png.jpeg'))

  def testGetContentType_InvalidFilename(self):
    self.assertEqual('application/octet-stream',
                     blobstore_upload._GetContentType('test_jpg'))
    self.assertEqual('application/octet-stream',
                     blobstore_upload._GetContentType('test_png'))
    self.assertEqual('application/msword',
                     blobstore_upload._GetContentType('png.doc'))

  def testEncodeMultipartFormData_ContentType(self):
    fields = [('key', '1234')]
    files = [('file', '1234.png', base64.b64decode(self.base64_png))]
    self.assertEqual(
        ('multipart/form-data; boundary=----------'
         'Boundary_$#$%_783659204_boundarY'),
        blobstore_upload._EncodeMultipartFormData(fields, files)[0])

  def testEncodeMultipartFormData_FieldAndFile(self):
    fields = [('key', '1234')]
    files = [('file', '1234.png', base64.b64decode(self.base64_png))]
    self.assertEqual(
        '\r\n'.join([self.expected_result_field, self.expected_result_file,
                     self.expected_result_body]),
        blobstore_upload._EncodeMultipartFormData(fields, files)[1])

  def testEncodeMultipartFormData_File(self):
    fields = []
    files = [('file', '1234.png', base64.b64decode(self.base64_png))]
    self.assertEqual(
        '\r\n'.join([self.expected_result_file, self.expected_result_body]),
        blobstore_upload._EncodeMultipartFormData(fields, files)[1])

  def testEncodeMultipartFormData_Field(self):
    fields = [('key', '1234')]
    files = []
    self.assertEqual(
        '\r\n'.join([self.expected_result_field, self.expected_result_body]),
        blobstore_upload._EncodeMultipartFormData(fields, files)[1])

  def testEncodeMultipartFormData_NoData(self):
    fields = []
    files = []
    self.assertEqual(
        self.expected_result_body,
        blobstore_upload._EncodeMultipartFormData(fields, files)[1])


def main():
  unittest.main()


if __name__ == '__main__':
  main()
