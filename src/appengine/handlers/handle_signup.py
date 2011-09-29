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


"""Handler for url sign up flow.

Handler to Add, Update, delete URLs and interested URLs.
"""



# Disable 'Import not at top of file' lint error.
# pylint: disable-msg=C6204, C6205, W0611

import logging
from django.utils import simplejson

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from handlers import base
from models import bots_user
from models import url
from models import url_config


ADD_URL = '/signup/add_url'
ADD_DEFAULT_URL_CONFIG_URL = '/signup/add_default_url_config'
ADD_SUBMITTED_URL = '/signup/add_submitted_url'
ADD_INTERESTED_URL = '/signup/add_interested_url'
GET_URLS = '/signup/get_urls'


class AddUrl(base.BaseHandler):
  """Handler to add url through bots sign up flow."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Provides add/search/update url/user for bots sign up flow."""
    # Let's check to see if user us logged in, else return error message.
    user = users.get_current_user()
    if not user:
      result = {'status': 'error', 'message': 'User not signed-in.'}
      self.response.out.write(simplejson.dumps(result))
      return
    # Let's get all the request parameters.
    site_url = self.GetOptionalParameter('site_url', None)
    fetch_limit = self.GetOptionalParameter('fetch_limit', 20)
    existing_url_key = self.GetOptionalParameter('existing_url_key', None)
    bots_user_key = self.GetOptionalParameter('bots_user_key', None)
    forced_add = simplejson.loads(self.GetOptionalParameter('forced_add',
                                                            'false'))
    if not site_url and not existing_url_key:
      result = {'status': 'error',
                'message': 'site_url and existing_url_key both are missing.'}
      self.response.out.write(simplejson.dumps(result))
      return
    # Let's retrieve bots_user details if not supplied with request.
    if not bots_user_key:
      existing_bots_user = bots_user.GetBotsUser(user)
      # User is not found, so let's create a new bots_user.
      if not existing_bots_user:
        new_bots_user = bots_user.CreateBotsUser(user)
        bots_user_key = new_bots_user.key()
      else:
        bots_user_key = existing_bots_user.key()
    else:
      bots_user_key = db.Key(bots_user_key)
    # If user is asking us to do forced add, let's add the URL.
    if site_url and forced_add:
      new_url = url.InsertUrl(site_url, bots_user_key)
      result = {'status': 'success', 'new_url_key': str(new_url.key()),
                'message': 'URL successfully submitted.'}
      self.response.out.write(simplejson.dumps(result))
      return
    # Let's search url if matches found, return the matches, else add the url.
    if site_url and not forced_add:
      # Let's check to see if site_url already exist in submitted_urls or not.
      if bots_user.IsInSubmittedUrl(bots_user_key, site_url):
        result = {'status': 'warning',
                  'message': 'URL already part of submitted_urls.'}
        self.response.out.write(simplejson.dumps(result))
        return
      matching_urls = url.SearchUrl(site_url, fetch_limit)
      if matching_urls:
        matching_urls_data = [{'key': str(m_url.key()), 'url': m_url.url}
                              for m_url in matching_urls]
        result = {'status': 'success', 'matching_urls': matching_urls_data,
                  'message': 'Matching URLs found.'}
        self.response.out.write(simplejson.dumps(result))
        return
      else:
        logging.info('No Matching url found, so adding url - %s', site_url)
        new_url = url.InsertUrl(site_url, bots_user_key)
        result = {'status': 'success', 'new_url_key': str(new_url.key()),
                  'message': 'URL successfully submitted.'}
        self.response.out.write(simplejson.dumps(result))
        return
    # If request has existing_url_key, let's add that URL into user's interest
    # list.
    if existing_url_key:
      updated_url = url.AddInterestedUserAndUrl(existing_url_key, bots_user_key)
      result = {'status': 'success', 'updated_url_key': str(updated_url.key()),
                'message': 'URL marked as interested url.'}
      self.response.out.write(simplejson.dumps(result))
      return


class AddDefaultUrlConfig(base.BaseHandler):
  """Handler to add default url config."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Adds default url config."""
    # Let's get all the request parameters.
    existing_url_key = self.GetRequiredParameter('existing_url_key')
    bots_user_key = self.GetRequiredParameter('bots_user_key')
    url_config.CreateDefaultUrlConfig(db.Key(existing_url_key),
                                      db.Key(bots_user_key))


class AddSubmittedUrl(base.BaseHandler):
  """Handler to add url to submitted_urls of bots_user model."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Adds url to submitted_urls."""
    # Let's get all the request parameters.
    existing_url_key = self.GetRequiredParameter('existing_url_key')
    bots_user_key = self.GetRequiredParameter('bots_user_key')
    bots_user.AddSubmittedUrl(db.Key(bots_user_key), db.Key(existing_url_key))


class AddInterestedUrl(base.BaseHandler):
  """Handler to add url to interested_urls of bots_user model."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Adds url to interested_urls."""
    # Let's get all the request parameters.
    existing_url_key = self.GetRequiredParameter('existing_url_key')
    bots_user_key = self.GetRequiredParameter('bots_user_key')
    bots_user.AddInterestedUrl(db.Key(bots_user_key), db.Key(existing_url_key))


class GetUrls(base.BaseHandler):
  """Handler to get list of urls associated with bots_user."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Returns list of urls associated with bots_user."""
    # Let's check to see if user is logged in, else return error message.
    user = users.get_current_user()
    if not user:
      result = {'status': 'error', 'message': 'User not signed-in.'}
      self.response.out.write(simplejson.dumps(result))
      return
    # Let's get all the request parameters.
    bots_user_key = self.GetOptionalParameter('bots_user_key', None)
    only_submitted_urls = simplejson.loads(
        self.GetOptionalParameter('only_submitted_urls', 'false'))
    only_interested_urls = simplejson.loads(
        self.GetOptionalParameter('only_interested_urls', 'false'))
    # Let's retrieve bots_user details if not supplied with request.
    if not bots_user_key:
      existing_bots_user = bots_user.GetBotsUser(user)
      bots_user_key = existing_bots_user.key()
    else:
      bots_user_key = db.Key(bots_user_key)
    urls = bots_user.GetUrls(bots_user_key, only_submitted_urls,
                             only_interested_urls)
    self.response.out.write(simplejson.dumps(urls))
    return

application = webapp.WSGIApplication(
    [(ADD_URL, AddUrl),
     (ADD_DEFAULT_URL_CONFIG_URL, AddDefaultUrlConfig),
     (ADD_SUBMITTED_URL, AddSubmittedUrl),
     (ADD_INTERESTED_URL, AddInterestedUrl),
     (GET_URLS, GetUrls)],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
