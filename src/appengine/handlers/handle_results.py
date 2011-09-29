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




import logging
from django.utils import simplejson

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from common import enum
from handlers import base
# Disable 'unused import' lint warning.
# pylint: disable-msg=W0611
from models import bots_user
from models import browser
from models import page_delta
from models import site
from models import test_suite
from models import url
from models import url_config


GET_RESULTS = '/results'
MEMCACHE_EXP_TIME_IN_SEC = 15*60


class GetResults(base.BaseHandler):
  """Handler to get the results (page delta) for a given url_key.

  URL Params:
    url_key: Existing url_key (Required).
    bots_user_key: Existing bots_user_key (optional)

  Returns:
    Matching results data.
  """

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Gets the results (page delta) for a given url_key."""
    # Let's check to see if user is logged in, else return error message.
    user = users.get_current_user()
    if not user:
      result = {'status': 'error', 'message': 'User not signed-in.'}
      self.response.out.write(simplejson.dumps(result))
      return
    # Let's get all the request parameters.
    url_key = self.GetRequiredParameter('url_key')
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
    memcache_key = '%s_%s' % (str(bots_user_key), url_key)
    result = memcache.get(memcache_key)
    if result:
      self.response.out.write(simplejson.dumps(result))
      return
    existing_url = db.get(db.Key(url_key))
    if not existing_url:
      result = {'status': 'error', 'message': 'No Matching URL found.'}
      self.response.out.write(simplejson.dumps(result))
      return
    existing_url_key = existing_url.key()
    # Let's see if this url is submitted by this user or not.
    is_submitted_url = False
    if existing_url_key in existing_bots_user.submitted_urls:
      is_submitted_url = True

    # Let's get the site_key.
    if is_submitted_url:
      existing_url_config = url_config.UrlConfig.all().filter(
          'user =', bots_user_key).filter('url =', existing_url_key).get()
    else:
      # Let's try to find url_config where auth information is not present. This
      # mechanism prevents user from looking at other user's authenticated
      # results.
      existing_url_configs = url_config.UrlConfig.all().filter(
          'url =', existing_url_key).filter('auth_enabled =', False).fetch(10)
      if len(existing_url_configs) > 1:
        logging.warning('Possible data corruption. Duplicate matching UrlConfig'
                        'data found for url: %s and user: %s',
                        str(existing_url_key), str(bots_user_key))
      # Let's use the first one in such case.
      existing_url_config = existing_url_configs[0]
    if not existing_url_config:
      result = {'status': 'error', 'message': 'No matching url config found.'}
      self.response.out.write(simplejson.dumps(result))
      return
    requested_sites = site.Site.all().filter(
        'config =', existing_url_config.key()).fetch(10)
    if len(requested_sites) > 1:
      logging.warning(
          'Possible data corruption. Duplicate site data found for config: %s',
          str(existing_url_config.key()))
     # Let's use the first one in such case.
    requested_site = requested_sites[0]

    latest_test_suite = test_suite.GetLatestSuite()
    deltas = latest_test_suite.results.filter(
        'site =', requested_site.key()).fetch(10)
    if not deltas:
      result = {'status': 'success', 'message': 'No results data found.'}
      self.response.out.write(simplejson.dumps(result))
      return
    result_detas = []
    for delta in deltas:
      ref_browser_family = enum.BROWSER.LookupKey(
          delta.ref_browser.browser_family).lower()
      test_browser_family = enum.BROWSER.LookupKey(
          delta.test_browser.browser_family).lower()
      ref_channel = enum.BROWSERCHANNEL.LookupKey(
          delta.ref_browser_channel).lower()
      test_channel = enum.BROWSERCHANNEL.LookupKey(
          delta.test_browser_channel).lower()
      result_delta = {
          'page_delta_key': str(delta.key()),
          'ref_browser_family': ref_browser_family,
          'ref_browser_version': delta.ref_browser.version,
          'ref_browser_channel': ref_channel,
          'test_browser_family': test_browser_family,
          'test_browser_version': delta.test_browser.version,
          'test_browser_channel': test_channel,
          'score': delta.score}
      result_detas.append(result_delta)
    result = {'status': 'success', 'message': 'Matching results data found.',
              'result_deltas': result_detas,
              'bots_user_key': str(bots_user_key)}
    # Let's add this to memcache.
    memcache.set(memcache_key, result, MEMCACHE_EXP_TIME_IN_SEC)
    self.response.out.write(simplejson.dumps(result))
    return


application = webapp.WSGIApplication(
    [(GET_RESULTS, GetResults)],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
