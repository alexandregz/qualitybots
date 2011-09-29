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


"""PageData Model.

PageData model stores various information about Page under Test.
"""




import base64
import zlib

from django.utils import simplejson

from google.appengine.ext import db

#Unused import warning.
#pylint: disable-msg=W0611
from models import browser
from models import data_list
from models import screenshot
from models import site
from models import test_suite


class PageData(db.Model):
  """PageData model class which stores information about page under test."""
  test_suite = db.ReferenceProperty(test_suite.TestSuite,
                                    collection_name='page_data_set')

  browser = db.ReferenceProperty(browser.Browser,
                                 collection_name='page_data_set')
  site = db.ReferenceProperty(site.Site,
                              collection_name='page_data_set')

  # Nodes table stores information about each element in an array. Array index
  # is uniqueID of an element. width, height, x, y, xpath/selector
  # information is stored in dictionary object. The nodes_table may be stored
  # as a base64-encoded, gzipped string.
  # nodes_table[uniqueIDOfElement] = {
  #                                  'w': node.offsetWidth,
  #                                  'h': node.offsetHeight,
  #                                  'x': node.offsetLeft,
  #                                  'y': node.offsetTop,
  #                                  'p': xPath/selector
  #                                  }
  nodes_table = db.TextProperty()

  # Dynamic Content table stores information about various dynamic content
  # (like ads) on the page. Currently it stores this info in array of element
  # ids (aka uniqueIDOfElement).
  dynamic_content_table = db.TextProperty()

  # Layout Table is about on each pixel what element exist. This information is
  # divided into 64 pieces for efficieny and stored as datalistentry. Reference
  # of this collection is stored as DataList.
  layout_table = db.ReferenceProperty(data_list.DataList)

  # Page width.
  width = db.IntegerProperty()

  # Page Height.
  height = db.IntegerProperty()

  # Reference to page screenshot.
  screenshot = db.ReferenceProperty(screenshot.Screenshot)

  date = db.DateTimeProperty(auto_now_add=True)

  # Flag to indicate whether this page data is compared already or not.
  compared = db.BooleanProperty(default=False)

  # Flag indicator for reference page data (aka PageData from reference
  # browser).
  is_reference = db.BooleanProperty(default=False)

  # Meta data about page_data (e.g. prerender flag).
  metadata = db.TextProperty(default=None)

  def IsReady(self):
    """Checks if all the layout-table information is received and ready.

    Returns:
      True: if layout table information is ready for processing.
      False: otherwise.
    """
    return self.layout_table and self.layout_table.EntriesReady()

  def DeleteLayoutTable(self):
    """Deletes layout-table info by deleting datalist and datalist entries."""
    if self.layout_table:
      self.layout_table.ClearEntries()

  def DeleteData(self):
    """Deletes page-delta, screenshot and layout table for a given page data."""
    self.DeleteLayoutTable()
    if self.screenshot:
      db.delete(self.screenshot)
    # Let's fetch all page-delta and delete them.
    if self.is_reference:
      results = self.ref_results.fetch(100)
    else:
      results = self.test_results.fetch(100)
    for result in results:
      result.DeleteData()
    db.delete(results)

  def GetNodesTable(self):
    """Return the nodes table and convert it from encoded format if necessary.

    The nodes_table data may be stored in base64-encoded, gzipped format. This
    function checks if the data is encoded and decodes it if necessary.

    Returns:
      A dictionary representing the nodes table data.
    """
    # Check if nodes table is compressed
    if '{' in self.nodes_table:
      return simplejson.loads(self.nodes_table)
    else:
      return simplejson.loads(
          zlib.decompress(base64.b64decode(self.nodes_table)))
