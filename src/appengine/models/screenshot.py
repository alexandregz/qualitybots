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


"""Screenshot model.

Screenshot model stores the data URL of the screenshot taken by the extension.
It also provides a method to decode the base64 data URL to the actual binary
content of the JPG image.
"""




import base64

from google.appengine.ext import blobstore
from google.appengine.ext import db


class Screenshot(db.Model):
  """Stores the data URL of the screenshot image."""
  # TODO(user): Remove the deprecated src_data field and use the blob data.
  src_data = db.BlobProperty()
  image_data = blobstore.BlobReferenceProperty()
  # Data duplication as a work around for screenshot blobstore missing issue.
  pagedata_ref = db.StringProperty(default=None)


def GetDecodedContent(src):
  """Decodes the data URL into binary content of a JPG image.

  Args:
    src: source data.

  Returns:
    Base64 Decoded source data.
  """
  prefix = 'data:image/jpg;base64,'
  content = src[len(prefix):]
  return base64.b64decode(content)


def AddScreenshot(src):
  """Stores screenshot data into screenshot model.

  Args:
    src: source data.

  Returns:
    Newly created screenshot object.
  """
  if src:
    content = GetDecodedContent(src)
    screenshot_image = Screenshot(src_data=content)
    screenshot_image.put()
    return screenshot_image


def AddBlobstoreScreenshot(blob_info, pagedata):
  """Stores screenshot data into screenshot model.

  Args:
    blob_info: A blobstore.BlobInfo object that refers to the blobstore image
      data.
   pagedata: Pagedata Entity

  Returns:
    A newly created screenshot object associated with the provided blob
    reference. If blob_info is None, None is returned.
  """
  if blob_info:
    screenshot_image = Screenshot(image_data=blob_info,
                                  pagedata_ref=str(pagedata.key()))
    screenshot_image.put()
    return screenshot_image
