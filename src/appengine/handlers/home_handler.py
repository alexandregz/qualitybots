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


"""Displays the home page for QualityBots.

Handler for homepage of QualityBots, which users can use to navigate
and see various test run results.
"""



import logging
import urlparse

from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from handlers import base
#Unused import warning.
#pylint: disable-msg=W0611
from models import page_data
from models import page_delta
from models import test_suite


CLEANUP_URL = '/clean'
DASHBOARD_URL = '/dashboard'
DELETE_URL = '/delete'
HOME_URL = '/'
PRERENDER_URL = '/prerender'
MEMCACHE_KEY_CLEANUP_DATA_COUNT = 'cleanup_data_count'


class Home(base.BaseHandler):
  """Handler for home page."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    self.redirect('/url/dashboard')


class Delete(base.BaseHandler):
  """Handler for deleting data.

  Uses key to find and delete data and it's related data.
  """

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Deletes data using given Key."""
    data_key = self.request.get('key')
    data = db.get(db.Key(data_key))
    # Let's delete all associated/related data.
    if hasattr(data, 'DeleteData'):
      data.DeleteData()
    # Now, let's delete the data itself.
    db.delete(data)
    last_url = self.request.get('lastUrl')
    if last_url:
      self.redirect(last_url)
    else:
      self.redirect(DASHBOARD_URL)


class Prerender(base.BaseHandler):
  """Handler for Prerender Page."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Displays Prerender Page for given URL."""
    url = self.request.get('url')
    parsed_url = urlparse.urlsplit(url, scheme='http').geturl()
    template_values = {'url': parsed_url}
    self.RenderTemplate('prerender.html', template_values)
    return


class CleanUnusedData(base.BaseHandler):
  """Handler for periodic cleaning of data.

  Cleans the PageData and associated data if the PageData doesn't have an
  associated test suite using task queue mechanism.
  """

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Iterate and clean useless page data and it's related data."""
    data_to_delete = []
    count = 0
    # Let's check if there is cursor provided, then let's use it to iterate.
    last_cursor = self.GetOptionalParameter(parameter_name='cursor')
    # Limit is used to restrict the amount of data being scanned each time.
    limit = self.GetOptionalParameter(parameter_name='limit', default_value=10)
    q = page_data.PageData.all()
    if last_cursor:
      q = q.with_cursor(last_cursor)
    pd = q.fetch(int(limit))
    # Let's iterate through page data model and find values which has no
    # corresponding test suite.
    for data in pd:
      try:
        db.get(data.test_suite.key())
      except db.Error:
        data.DeleteData()
        data_to_delete.append(data)
        count += 1
        memcache.incr(key=MEMCACHE_KEY_CLEANUP_DATA_COUNT, initial_value=1)
    db.delete(data_to_delete)
    cursor = q.cursor()
    # Let's prepate next task info and add that task to queue.
    task_params = {'cursor': cursor, 'limit': limit}
    if pd:
      logging.info('%d data removed.', count)
      taskqueue.add(url=CLEANUP_URL, params=task_params, method='GET')
      logging.info('Cleanup Data Task Added.')
      self.response.out.write('%d data removed. Cleanup task is added.' % count)
    else:
      # Looks like there is no more PageData values to scan. So we are done !
      final_count = memcache.get(key=MEMCACHE_KEY_CLEANUP_DATA_COUNT)
      if not final_count:
        logging.info('No Data removed.')
      else:
        logging.info('Total %s data removed.', final_count)
      memcache.delete(key=MEMCACHE_KEY_CLEANUP_DATA_COUNT)
      logging.info('Clean up data task done!')
      self.response.out.write('Cleanup task is Done!')


application = webapp.WSGIApplication(
    [(HOME_URL, Home),
     (DELETE_URL, Delete),
     (CLEANUP_URL, CleanUnusedData),
     (PRERENDER_URL, Prerender)],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
