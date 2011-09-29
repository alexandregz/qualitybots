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


"""UrlConfig model to store UrlConfig information.

This model stores information about configuration. There is at least one
configuration associated with each submitted URL. Model stores the references of
URL and BotsUser, hence it can be used to determine the quota for a given user.
"""




import logging

from google.appengine.ext import db

from models import bots_user
from models import url


class UrlConfigError(Exception):
  pass


class UrlConfig(db.Model):
  """Model to store URL configuration information.

  This model is used to store various configuration information about url. For
  every url, we have to have at least one config information. Default config is
  created for every url creation.

  Attributes:
    depth: Depth to crawl while testing a URL (default: 1).
    creation_date: Date of creation.
    update_date: Update Date.
    auth_enabled: Boolean indicating auth is enabled or not.
    auth_username: Username to use for authentication.
    auth_password: Password to use for authentication.
    auth_url: Auth URL to use for authentication.
    auth_parameters: Parameters used for authentication.
    auth_cookie: Auth Cookie.
    auth_cookie_update_date: Date when last auth cookie was updated.
    user: User associated (submitter) with the config
      (ReferenceProperty: BotsUser).
    url: URL Associated with the config. (ReferenceProperty: UrlConfig).
  """
  depth = db.IntegerProperty(default=1)
  creation_date = db.DateTimeProperty(auto_now_add=True)
  update_date = db.DateTimeProperty(auto_now=True)
  auth_enabled = db.BooleanProperty(default=False)
  auth_username = db.StringProperty()
  auth_password = db.StringProperty()
  auth_url = db.StringProperty()
  auth_parameters = db.StringProperty()
  auth_cookie = db.TextProperty()
  auth_cookie_update_date = db.DateTimeProperty()
  user = db.ReferenceProperty(bots_user.BotsUser,
                              collection_name='configs_from_user')
  url = db.ReferenceProperty(url.Url, collection_name='urlconfigs')


def CreateDefaultUrlConfig(url_key, bots_user_key):
  """Creates a default UrlConfig entity corresponding to url and botsuser.

  Args:
    url_key: Existing URL entity key (db.Key).
    bots_user_key: bots_user entity key (db.Key).

  Raises:
    TypeError: If required parameter is missing.
  """
  if not url_key:
    raise TypeError(
        'Missing parameter - url_key is a required parameter.')
  if not bots_user_key:
    raise TypeError(
        'Missing parameter - bots_user_key is a required parameter.')
  url_config = UrlConfig(depth=1, auth_enabled=False, user=bots_user_key,
                         url=url_key)
  url_config.put()
