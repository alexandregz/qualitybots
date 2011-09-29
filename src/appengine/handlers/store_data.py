#!/usr/bin/python2.4
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


"""Stores page data sent from App Compat extension.

Handles requests from the extensions and stores page data.
"""



import logging

from django.utils import simplejson

from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp.util import run_wsgi_app

from common import enum
from common import useragent_parser
from handlers import base
from models import browser
from models import client_machine
from models import data_list
from models import page_data
from models import run_log
from models import screenshot
from models import site
from models import test_suite
from models import url_config


PUT_DATA_URL = '/putdata'
UPLOAD_SCREENSHOT_IMAGE_URL = '/uploadscreenshot'
GET_SCREENSHOT_UPLOAD_URL_URL = '/getuploadurl'
GET_SCREENSHOT_STATUS_URL = '/screenshotstatus'


class PutDataError(Exception):
  pass


class PutData(webapp.RequestHandler):
  """Handler for putting result data into the database."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Put the given result data into the database."""
    data = self._GetRequestData()

    # Touch the machine instance if the instance id is provided.
    if 'instance_id' in data:
      client_machine.SetMachineStatus(data['instance_id'],
                                      enum.MACHINE_STATUS.RUNNING)

    if 'key' not in data:
      update_suite_info = False
      suite_data = simplejson.loads(data['suiteInfo'])
      suite = test_suite.GetOrInsertSuite(
          suite_data['date'], suite_data['refBrowser'],
          suite_data['refBrowserChannel'])

      channel = None
      if 'channel' in data:
        channel = data['channel']

      # Following code is to take care of the scenario where test browser comes
      # up first with the data. Hence, at that time we don't have sufficient
      # data to put in ref browser.
      # If reference browser information is incomplete then let's mark
      # it for update.
      if suite.ref_browser.os is None:
        parser = useragent_parser.UAParser(data['userAgent'])
        if (parser.GetBrowserVersion() == suite.ref_browser.version and
            channel==suite_data['refBrowserChannel']):
          # If flag is present anywhere then it has to match.
          if 'flag' in data or suite.ref_browser.flag:
            if suite.ref_browser.flag == data['flag']:
              update_suite_info = True
          else:
            update_suite_info = True

      test_data = page_data.PageData()
      if 'screenshot' in data:
        test_data.screenshot = screenshot.AddScreenshot(data['screenshot'])

      test_data.test_suite = suite

      flag = None
      if 'flag' in data:
        flag = data['flag']
      test_data.browser = browser.GetOrInsertBrowser(
          data['userAgent'], channel=channel, flag=flag)

      if update_suite_info:
        logging.info('Updating Reference Browser in Test Suite. old_ref: %s,'
                     ' new_ref: %s', suite.ref_browser.key(),
                     test_data.browser.key())
        test_suite.UpdateRefBrowser(suite, test_data.browser,
                                    delete_old_ref=True)
      # Let's get run log key from suite_data.
      if 'key' not in suite_data:
        raise PutDataError('The run log "key" is a required parameter.')
      my_run_log = db.get(db.Key(suite_data['key']))
      url_config_key = my_run_log.config.key()
      test_data.site = site.GetOrInsertSiteFromUrl(data['url'], url_config_key)

      test_data.nodes_table = data['nodesTable']
      test_data.dynamic_content_table = data['dynamicContentTable']
      test_data.layout_table = data_list.CreateEmptyDataList()

      test_data.width = int(data['width'])
      test_data.height = int(data['height'])
      if 'metaData' in data:
        test_data.metadata = data['metaData']
      # If browser key matches with test_suite's ref browser then
      # let's mark the page_data as reference.
      if str(test_data.browser.key()) == str(suite.ref_browser.key()):
        test_data.is_reference = True
      else:
        test_data.is_reference = False

      test_data.put()

      if not test_data.is_reference:
        suite.AddTestBrowser(test_data.browser)

      response = {
          'key': str(test_data.key()),
          'nPieces': data_list.NUM_ENTRIES}
      self.response.out.write(simplejson.dumps(response))

    else:
      test_data = db.get(db.Key(data['key']))
      layout_table = simplejson.loads(data['layoutTable'])
      test_data.layout_table.AddEntry(int(data['i']), layout_table)
      self.response.out.write('received')

  def _GetRequestData(self):
    data = {}
    args = self.request.arguments()
    for arg in args:
      data[arg] = self.request.get(arg)
    return data


class UploadScreenshotImage(blobstore_handlers.BlobstoreUploadHandler):
  """Handler for uploading the screenshot image."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Upload the screenshot image from the post request.

    URL Params:
      file: A BlobInfo object describing the jpeg screenshot file that is
        stored in blobstore.
      key: A string key indicating the PageData object that the screenshot
        should be associated with.
    """
    upload_files = self.get_uploads('file')
    blob_info = upload_files[0]
    logging.info('Blob Info- %s', blob_info)
    # Associate the screenshot with a given test
    key = self.request.get('key')
    logging.info('PageData Key- %s', key)

    if key:
      try:
        test_data = db.get(db.Key(key))
        logging.info('PageData Loaded.')
      except db.BadKeyError:
        self.error(500)
        logging.error('Bad Key Error Exception.')
        return

      test_data.screenshot = screenshot.AddBlobstoreScreenshot(blob_info,
                                                               test_data)
      logging.info('Screenshot Created-%s', test_data.screenshot.key())
      test_data.put()

    self.redirect((GET_SCREENSHOT_STATUS_URL + '?key=%s') % key)


class GetScreenshotUploadUrl(base.BaseHandler):
  """Handler for getting a blobstore screenshot upload URL."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Provide a blobstore screenshot upload URL.

    This handler prints out a string indicating the URL to use to upload a
    screenshot image.
    """
    self.response.out.write(blobstore.create_upload_url(
        UPLOAD_SCREENSHOT_IMAGE_URL))


class GetScreenshotStatus(base.BaseHandler):
  """Handler for getting the upload status of a blobstore screenshot."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Provide the upload status of a blobstore screenshot.

    URL Params:
    key: A string key indicating the PageData object that the screenshot
      should be associated with.

    Returns:
      A 'success' string if the PageData object has a correctly formed
      Screenshot object associated with it. If the Screenshot is incorrect,
      a 500 error is returned.
    """
    key = self.request.get('key')

    if key:
      try:
        test_data = db.get(db.Key(key))
      except db.BadKeyError:
        self.error(500)
        return

      if test_data.screenshot and test_data.screenshot.image_data:
        self.response.out.write('success')
    else:
      self.error(500)


application = webapp.WSGIApplication(
    [(PUT_DATA_URL, PutData),
     (UPLOAD_SCREENSHOT_IMAGE_URL, UploadScreenshotImage),
     (GET_SCREENSHOT_UPLOAD_URL_URL, GetScreenshotUploadUrl),
     (GET_SCREENSHOT_STATUS_URL, GetScreenshotStatus)],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
