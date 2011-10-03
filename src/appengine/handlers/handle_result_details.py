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


"""Handler for Results Page."""




from common import enum
from django.utils import simplejson
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app


from handlers import base
# Disable 'unused import' lint warning.
# pylint: disable-msg=W0611
from models import bots_user
from models import browser
from models import page_delta
from models import site
from models import url_config


GET_RESULTS_DETAILS = '/results/details'
GET_RESULTS_METADATA = '/results/metadata'
MEMCACHE_EXP_TIME_IN_SEC = 15*60


class GetPageDeltaDetails(base.BaseHandler):
  """Handler to get the results (page delta) for a given page_delta_key.

  URL Params:
    page_delta_key: Existing PageDelta Key (Required).
    bots_user_key: Existing bots_user_key (optional)

  Returns:
    Metadata about given page delta key.
  """

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Gets the metadata for a requested PageDelta."""
    # Let's check to see if user is logged in, else return error message.
    user = users.get_current_user()
    if not user:
      result = {'status': 'error', 'message': 'User not signed-in.'}
      self.response.out.write(simplejson.dumps(result))
      return

    # Let's get all the request parameters.
    existing_page_delta_key = self.GetRequiredParameter('page_delta_key')
    bots_user_key = self.GetOptionalParameter('bots_user_key', None)

    # Let's retrieve bots_user details if not supplied with request.
    if not bots_user_key:
      existing_bots_user = bots_user.GetBotsUser(user)
    else:
      existing_bots_user = db.get(db.Key(bots_user_key))
    # If user was not found, return error message.
    if not existing_bots_user:
      result = {'status': 'error', 'message': 'User not found.'}
      self.response.out.write(simplejson.dumps(result))
      return
    bots_user_key = existing_bots_user.key()
    # Let's check memcache to see if value is in the cache or not.
    memcache_key = '%s_%s' % (str(bots_user_key), existing_page_delta_key)
    result = memcache.get(memcache_key)
    if result:
      self.response.out.write(simplejson.dumps(result))
      return
    existing_page_delta = db.get(db.Key(existing_page_delta_key))
    if not existing_page_delta:
      result = {'status': 'error', 'message': 'No Matching Data found.'}
      self.response.out.write(simplejson.dumps(result))
      return
    existing_page_delta_key = existing_page_delta.key()
    # Let's see if this result is authenticated or not.
    is_auth_result = False
    if existing_page_delta.site.config:
      is_auth_result = existing_page_delta.site.config.auth_enabled
    # If result is authenticated, then let's check to make sure that current
    # user is the owner.
    if (is_auth_result and
        str(bots_user_key) != str(existing_page_delta.site.config.user.key())):
      result = {'status': 'error',
                'message': 'Not authorized to view these results.'}
      self.response.out.write(simplejson.dumps(result))
      return
    # Let's calculate various element count for this delta (diff).
    existing_page_delta.CalculateElemCount()
    test_total_elem_count = existing_page_delta.test_data_total_elem_count
    test_unmatched_elem_count = (
        existing_page_delta.test_data_unmatched_elem_count)
    ref_total_elem_count = existing_page_delta.ref_data_total_elem_count
    ref_unmatched_elem_count = (
        existing_page_delta.ref_data_unmatched_elem_count)

    # Let's get metadata about requested page delta.
    ref_screenshot_key = existing_page_delta.ref_data.screenshot.key()
    test_screenshot_key = existing_page_delta.test_data.screenshot.key()
    ref_browser_family = enum.BROWSER.LookupKey(
        existing_page_delta.ref_browser.browser_family).lower()
    test_browser_family = enum.BROWSER.LookupKey(
        existing_page_delta.test_browser.browser_family).lower()
    ref_channel = enum.BROWSERCHANNEL.LookupKey(
        existing_page_delta.ref_browser_channel).lower()
    test_channel = enum.BROWSERCHANNEL.LookupKey(
        existing_page_delta.test_browser_channel).lower()
    existing_page_delta.CreateIndices()
    result_details = {
        'page_delta_key': str(existing_page_delta.key()),
        'url': existing_page_delta.site.url,
        'ref_screenshot_key': str(ref_screenshot_key),
        'test_screenshot_key': str(test_screenshot_key),
        'score': existing_page_delta.score,
        'date': str(existing_page_delta.date),
        'delta_index': existing_page_delta.delta_index,
        'dynamic_content_index': existing_page_delta.dynamic_content_index,
        'ignore': existing_page_delta.ignore,
        'comments': existing_page_delta.comments,
        'ref_browser_family': ref_browser_family,
        'ref_browser_version': existing_page_delta.ref_browser.version,
        'ref_browser_channel': ref_channel,
        'test_browser_family': test_browser_family,
        'test_browser_version': existing_page_delta.test_browser.version,
        'test_browser_channel': test_channel,
        'test_total_elem_count': test_total_elem_count,
        'test_unmatched_elem_count': test_unmatched_elem_count,
        'ref_total_elem_count': ref_total_elem_count,
        'ref_unmatched_elem_count': ref_unmatched_elem_count}
    result = {'status': 'success',
              'message': 'Matching page delta metadata found.',
              'result_details': result_details,
              'bots_user_key': str(bots_user_key)}
    # Let's add this to memcache.
    memcache.set(memcache_key, result, MEMCACHE_EXP_TIME_IN_SEC)
    self.response.out.write(simplejson.dumps(result))
    return


class GetResultsMetadata(base.BaseHandler):
  """Handler to get the result details for a given page_delta_key.

  URL Params:
    page_delta_key: Existing PageDelta Key (Required).
    bots_user_key: Existing bots_user_key (optional)

  Returns:
    Metadata that has info about other similar runs using given page delta key.
  """

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Gets the metadata for a requested PageDelta."""
    # Let's check to see if user is logged in, else return error message.
    user = users.get_current_user()
    if not user:
      result = {'status': 'error', 'message': 'User not signed-in.'}
      self.response.out.write(simplejson.dumps(result))
      return

    # Let's get all the request parameters.
    existing_page_delta_key = self.GetRequiredParameter('page_delta_key')
    bots_user_key = self.GetOptionalParameter('bots_user_key', None)

    # Let's retrieve bots_user details if not supplied with request.
    if not bots_user_key:
      existing_bots_user = bots_user.GetBotsUser(user)
    else:
      existing_bots_user = db.get(db.Key(bots_user_key))
    # If user was not found, return error message.
    if not existing_bots_user:
      result = {'status': 'error', 'message': 'User not found.'}
      self.response.out.write(simplejson.dumps(result))
      return
    bots_user_key = str(existing_bots_user.key())
    existing_page_delta = db.get(db.Key(existing_page_delta_key))
    if not existing_page_delta:
      result = {'status': 'error', 'message': 'No Matching Data found.'}
      self.response.out.write(simplejson.dumps(result))
      return
    existing_url_key = existing_page_delta.site.config.url.key()
    self.redirect('/results?url_key=%s&bots_user_key=%s'
                  % (str(existing_url_key), bots_user_key))
    return


application = webapp.WSGIApplication(
    [(GET_RESULTS_DETAILS, GetPageDeltaDetails),
     (GET_RESULTS_METADATA, GetResultsMetadata)],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
