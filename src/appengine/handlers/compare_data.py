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


"""Compares page data sent from the client.

This file contains handlers that are used to run data comparisons.
"""



import math

from django.utils import simplejson

from google.appengine.api import taskqueue
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from models import data_list
from models import page_data
from models import page_delta
from models import screenshot


COMPUTE_DELTA_URL = '/compute_delta'
COMPUTE_DELTA_BY_PART_URL = '/compute_delta_by_part'
COMPUTE_SCORE_URL = '/compute_score'


class ComputeDeltaHandler(webapp.RequestHandler):
  """Handler for computing a page delta."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Compares a page delta based on the given delta key."""
    delta_key = self.request.get('delta')
    if delta_key:
      delta = db.get(db.Key(delta_key))
    else:
      delta = self.FindPairToCompare()

    if delta:
      self.AddCompareTasksToQueue(delta)
    else:
      self.response.out.write('No data to compare.')

  def FindPairToCompare(self):
    """Finds a pair of data to compare if exits.

    If it finds a pair of data, it will mark entry from the test browser as
    already compared (in a transaction) and then create and save a new delta
    entry and return it.

    Returns:
      The delta entry if there's a pair to compare. None otherwise.
    """

    uncompared_test_data = page_data.PageData.all().filter(
        'is_reference =', False).filter('compared =', False)

    for test_data in uncompared_test_data:
      if not test_data.IsReady():
        continue

      try:
        suite = test_data.test_suite
      except db.Error:
        continue

      ref_data = page_data.PageData.all().filter(
          'test_suite =', suite).filter(
              'site =', test_data.site).filter(
                  'is_reference =', True).get()

      if ref_data:
        test_data_key = str(test_data.key())

        # Function to run in a transaction. Returns True if the data is good
        # to be compared; returns False if it has already been marked as
        # compared by some other requests.
        def MarkDataAsCompared():
          # Re-fetch and double check if the data hasn't been compared to avoid
          # concurrency problems.
          data = db.get(db.Key(test_data_key))
          if not data.compared:
            test_data.compared = True
            test_data.put()
            return True
          else:
            return False

        if db.run_in_transaction(MarkDataAsCompared):
          delta = page_delta.PageDelta()
          delta.test_data = test_data
          delta.ref_data = ref_data
          delta.test_browser = test_data.browser
          delta.test_browser_channel = test_data.browser.channel
          delta.ref_browser = ref_data.browser
          delta.ref_browser_channel = ref_data.browser.channel
          if test_data.metadata:
            delta.test_data_metadata = test_data.metadata
          if ref_data.metadata:
            delta.ref_data_metadata = ref_data.metadata
          delta.test_suite = test_data.test_suite
          delta.compare_key = page_delta.GetOrInsertUniqueKey(
              delta.GetTestBrowser().key().name(),
              delta.GetRefBrowser().key().name(), delta.GetSiteUrl())
          delta.delta = data_list.CreateEmptyDataList()
          delta.dynamic_content = data_list.CreateEmptyDataList()

          # This is hack to work around screenshot blobstore missing issue.
          self.SetScreenshotKeyUsingPageDataRef(test_data)
          self.SetScreenshotKeyUsingPageDataRef(ref_data)

          delta.put()
          return delta

    return None

  def AddCompareTasksToQueue(self, delta):
    """Adds a task to the task queue to compute the given delta.

    Each task computes one part of the layout.

    Args:
      delta: A PageDelta object to add to the task queue.
    """
    delta_key = str(delta.key())

    task_url = '/compute_delta_by_part'

    for i in range(data_list.NUM_ENTRIES):
      task_params = {'deltaKey': delta_key,
                     'part': i}
      taskqueue.add(url=task_url, params=task_params, method='GET')

    self.response.out.write('Tasks added. key=%s' % delta_key)

  def SetScreenshotKeyUsingPageDataRef(self, pd):
    """Adds a screenshot blobstore key to page data model(if missing).

    This is a hack for screenshot key missing issue for page_data model.

    Args:
      pd: A PageData object to check if screenshot is missing.
    """
    if not pd.screenshot:
      pd_screenshot = screenshot.Screenshot.all(keys_only=True).filter(
          'pagedata_ref =', str(pd.key())).get()
      if pd_screenshot:
        pd.screenshot = pd_screenshot
        pd.put()


class ComputeDeltaByPart(webapp.RequestHandler):
  """Handler for computing a page delta based on part of the page."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Compares a page delta by part based on the given delta key and part."""
    delta_key = self.request.get('deltaKey')
    part = int(self.request.get('part'))
    delta = db.get(db.Key(delta_key))

    if delta.test_data.layout_table:
      dl = []
      ignoredContent = []

      nt1 = delta.test_data.GetNodesTable()
      nt2 = delta.ref_data.GetNodesTable()

      # Let's initialize dynamicContentTable.
      dynamic_content_table_test = None
      dynamic_content_table_ref = None

      if delta.test_data.dynamic_content_table:
        dynamic_content_table_test = simplejson.loads(
            delta.test_data.dynamic_content_table)
      if delta.ref_data.dynamic_content_table:
        dynamic_content_table_ref = simplejson.loads(
            delta.ref_data.dynamic_content_table)

      rows1 = delta.test_data.layout_table.GetEntryData(part)
      rows2 = delta.ref_data.layout_table.GetEntryData(part)

      part_length = int(math.ceil(delta.test_data.height /
                                  float(data_list.NUM_ENTRIES)))

      for i in range(min(len(rows1), len(rows2))):
        for j in range(min(len(rows1[i]), len(rows2[i]))):
          try:
            nid1 = int(rows1[i][j])
            nid2 = int(rows2[i][j])
          except ValueError:
            nid1 = int(rows1[i][j].split()[0])
            nid2 = int(rows2[i][j].split()[0])

          if nid1 < 0 or nid2 < 0:
            continue

          # If element is marked as dynamic content then add it to
          # ignoredContent and continue.
          if ((dynamic_content_table_test and
               (nid1 in dynamic_content_table_test)) or
              (dynamic_content_table_ref and
               (nid2 in dynamic_content_table_ref))):

            x = j
            y = i + part * part_length
            ignoredContent.append((x, y, nid1, nid2))
            continue

          try:
            node1 = nt1[nid1]
            node2 = nt2[nid2]
          except IndexError:
            continue

          if not AreNodesSame(node1, node2):
            x = j
            y = i + part * part_length
            dl.append((x, y, nid1, nid2))

      delta.delta.AddEntry(part, dl)
      delta.dynamic_content.AddEntry(part, ignoredContent, True)

    if delta.delta.EntriesReady():
      task_params = {'deltaKey': delta_key}
      taskqueue.add(url='/compute_score', params=task_params, method='GET')
    else:
      self.response.out.write('Tasks %d finished.' % part)


class ComputeScore(webapp.RequestHandler):
  """Computes the score of a given delta after all parts are finished.

  Also deletes the layout table of the original test data entry to save space.
  Handler also calculates various element count and create indices necessary.
  """

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    key = self.request.get('deltaKey')
    result = db.get(db.Key(key))
    if result.score < 0:
      result.ComputeScore()
      result.test_data.DeleteLayoutTable()
    result.CreateIndices()
    result.CalculateElemCount()

    self.response.out.write('Done.')


def AreNodesSame(node_data_1, node_data_2):
  """Compares if two nodes are the same.

  Currently using a very basic algorithm: assume the nodes are the same if
  either their XPaths are the same or their dimension/positions are the same.

  Args:
    node_data_1: A dictionary of values about a DOM node.
    node_data_2: A dictionary of values about a DOM node.

  Returns:
    A boolean indicating whether the two nodes should be considered equivalent.
  """

  return (node_data_1['p'].lower() == node_data_2['p'].lower() or
          (node_data_1['w'] == node_data_2['w'] and
           node_data_1['h'] == node_data_2['h'] and
           node_data_1['x'] == node_data_2['x'] and
           node_data_1['y'] == node_data_2['y']))


application = webapp.WSGIApplication(
    [(COMPUTE_DELTA_URL, ComputeDeltaHandler),
     (COMPUTE_DELTA_BY_PART_URL, ComputeDeltaByPart),
     (COMPUTE_SCORE_URL, ComputeScore)],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
