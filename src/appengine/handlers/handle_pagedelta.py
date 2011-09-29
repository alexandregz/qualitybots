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


"""Display page delta related handlers."""




from django.utils import simplejson

from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp.util import run_wsgi_app

from handlers import base
from models import data_list

# Disable 'unused import' lint warning.
# pylint: disable-msg=W0611
from models import page_delta
from models import screenshot


EDIT_PAGE_DELTA_URL = '/delta/edit'
GET_DELTA_LIST_URL = '/delta/list'
GET_DYNAMIC_CONTENT_LIST_URL = '/delta/dynamiccontent'
SHOW_DELTA_URL = '/delta/show'
GET_SCREENSHOT_BLOB_URL = '/screenshotblob'
GET_SCREENSHOT_IMAGE_URL = '/screenshot'


class GetScreenshotImage(webapp.RequestHandler):
  """Handler for loading the screenshot image.

  URL Params:
    key: A string representing the key for the Screenshot model containing the
      image to load.

  Returns:
    The screenshot image to display.
  """

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Load the screenshot image associated with the given key."""
    key = self.request.get('key')
    try:
      screenshot_image = db.get(db.Key(key))
    except db.BadKeyError:
      screenshot_image = None

    if screenshot_image:
      if screenshot_image.src_data:
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.headers['Cache-Control'] = 'max-age=3600, public'
        self.response.headers['Content-Encoding'] = 'gzip'
        self.response.out.write(screenshot_image.src_data)
        return
      elif screenshot_image.image_data:
        self.redirect((GET_SCREENSHOT_BLOB_URL + '?key=%s') %
                      screenshot_image.image_data.key())
        return

    self.redirect('/s/noimage.png')


class GetScreenshotBlob(blobstore_handlers.BlobstoreDownloadHandler):
  """Handler for loading the screenshot image from blobstore."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Load the screenshot image associated with the given key.

    URL Params:
      key: A string indicating the key for the blobstore image to load.

    Returns:
      The screenshot image associated with the given key.
    """
    blob_key = self.request.get('key')
    blob_info = blobstore.BlobInfo.get(blob_key)

    if blob_info:
      self.send_blob(blob_info)
    else:
      self.redirect('/s/noimage.png')


class EditPageDelta(base.BaseHandler):
  """Handler for editing the page delta information."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Duplicate the post functionality for a GET request."""
    self.post()

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Update the page delta based on the provided parameters."""
    key = self.request.get('key')
    try:
      delta = db.get(db.Key(key))
    except db.BadKeyError:
      self.response.out.write('No Matching PageDelta found.')
      return

    info_param = self.request.get('info')
    ignore = self.request.get('ignore')
    if ignore:
      if ignore.lower() == 'true':
        delta.UpdateIgnoreFlag(True)
      else:
        delta.UpdateIgnoreFlag(False)
    if info_param:
      info = simplejson.loads(info_param)
      if 'comments' in info:
        delta.UpdateComments(info['comments'])
      if 'bugs' in info:
        delta.UpdateBugs(info['bugs'])
      self.response.out.write('Info updated successfully.')


class GetDeltaList(base.BaseHandler):
  """Handler for getting a list of page deltas."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Get a list of page deltas that match the given parameters."""
    key = self.request.get('key')

    try:
      pdelta = db.get(db.Key(key))
    except db.BadKeyError:
      return

    i = self.request.get('i')
    if not i:
      i = 0
    i = int(i)

    delta_list_raw = pdelta.delta.GetEntryData(i)

    test_nodes_table = pdelta.test_data.GetNodesTable()
    ref_nodes_table = pdelta.ref_data.GetNodesTable()

    delta_list = []
    for d in delta_list_raw:
      delta_list.append((d[0], d[1],
                         test_nodes_table[d[2]], ref_nodes_table[d[3]]))

    if self.request.get('deltaonly'):
      self.response.headers['Cache-Control'] = 'max-age=3600, public'
      self.response.headers['Content-Encoding'] = 'gzip'
      self.response.out.write(simplejson.dumps(delta_list))
    else:
      template_values = {
          'delta': pdelta,
          'delta_list': delta_list,
          'entry_indices': range(data_list.NUM_ENTRIES),
          'current_index': i}
      self.RenderTemplate('delta_list.html', template_values)


class GetDynamicContentList(base.BaseHandler):
  """Handler for getting a list of dynamic content for a page delta."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Get the dynamic content for a given page delta."""
    key = self.request.get('key')

    try:
      pdelta = db.get(db.Key(key))
    except db.BadKeyError:
      return

    i = self.request.get('i')
    if not i:
      i = 0
    i = int(i)
    dynamic_content_list = []
    if pdelta.dynamic_content:
      dynamic_content_list_raw = pdelta.dynamic_content.GetEntryData(i)

      test_nodes_table = pdelta.test_data.GetNodesTable()
      ref_nodes_table = pdelta.ref_data.GetNodesTable()

      for d in dynamic_content_list_raw:
        dynamic_content_list.append((d[0], d[1], test_nodes_table[d[2]],
                                     ref_nodes_table[d[3]]))

    self.response.headers['Cache-Control'] = 'max-age=3600, public'
    self.response.headers['Content-Encoding'] = 'gzip'
    self.response.out.write(simplejson.dumps(dynamic_content_list))


class ShowDelta(base.BaseHandler):
  """Handler to show a page delta."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Render a page delta based on the given parameters."""
    key = self.request.get('key')

    try:
      delta = db.get(db.Key(key))
    except db.BadKeyError:
      self.response.out.write('No Matching PageDelta found.')
      return

    test_date = delta.test_data.date
    ref_date = delta.ref_data.date
    time_diff = _CalculateTimeDiff(test_date, ref_date)
    # If the time difference is more than 5 minutes, then there is a
    # possible synchronization issue.
    timediff = abs(test_date-ref_date)
    if (timediff.seconds/60) > 5:
      possible_sync_issue_flag = True
    else:
      possible_sync_issue_flag = False

    delta.CreateIndices()

    template_values = {
        'delta': delta,
        'time_diff': time_diff,
        'possible_sync_issue_flag': possible_sync_issue_flag,
        'test_data': delta.test_data,
        'ref_data': delta.ref_data,
        'site_url': delta.GetSiteUrl(),
        'test_browser': delta.GetTestBrowser().GetBrowserStringWithFlag(),
        'test_prerender_tag': delta.GetTestPrerenderTag(),
        'ref_browser': delta.GetRefBrowser().GetBrowserStringWithFlag(),
        'ref_prerender_tag': delta.GetRefPrerenderTag(),
        'prerendered_string': page_delta.PRERENDERED_STRING,
        'delta_index': delta.delta_index,
        'dynamic_content_index': delta.dynamic_content_index}

    self.response.headers['Cache-Control'] = 'max-age=3600, public'
    self.response.headers['Content-Encoding'] = 'gzip'
    self.RenderTemplate('delta_visual.html', template_values)


def _CalculateTimeDiff(date1, date2):
  """Calculate a time difference string based on two provided datetimes.

  Args:
    date1: A datetime.datetime object.
    date2: A datetime.datetime object.

  Returns:
    A string indicating the time difference between the two datetimes.
  """
  timediff = abs(date1-date2)
  diff_seconds = timediff.seconds
  days, remainder = divmod(diff_seconds, 24*3600)
  hours, remainder = divmod(remainder, 3600)
  minutes, seconds = divmod(remainder, 60)
  if days > 0:
    return '%02d Days, %02dh:%02dm:%02ds' % (days, hours, minutes, seconds)
  else:
    return '%02dh:%02dm:%02ds' % (hours, minutes, seconds)


application = webapp.WSGIApplication(
    [(EDIT_PAGE_DELTA_URL, EditPageDelta),
     (GET_DELTA_LIST_URL, GetDeltaList),
     (GET_DYNAMIC_CONTENT_LIST_URL, GetDynamicContentList),
     (SHOW_DELTA_URL, ShowDelta),
     (GET_SCREENSHOT_IMAGE_URL, GetScreenshotImage),
     (GET_SCREENSHOT_BLOB_URL, GetScreenshotBlob)],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
