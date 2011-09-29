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


"""BotsUser model to store user information.

BotsUser model stores important information about signed up user. Currently
we rely on Google Accounts (GAIA Users) to detect and collect information about
user.
"""




import logging

from google.appengine.ext import db
from google.appengine.api import memcache


URL_QUOTA_PER_USER = 20
MEMCACHE_EXP_TIME_IN_SEC = 60*60


class BotsUserNotFoundError(Exception):
  pass


class BotsUser(db.Model):
  """Model to store user information and preferences.

  interested_urls count is not used for quota limitations.Submitted url count
  is calculated using count of submitted_urls. Currently we allow up to
  URL_QUOTA_PER_USER submitted urls per user.

  Attributes:
    user: GAIA User (db.UserProperty).
    creation_date: Date of creation.
    interested_urls: List of Url(entities) keys that user is interested in.
    submitted_urls: List of Url(entities) keys that user has submitted.
    quota_limit: Amount of submitted urls allowed per user.
  """
  user = db.UserProperty(required=True)
  creation_date = db.DateTimeProperty(auto_now_add=True)
  interested_urls = db.ListProperty(db.Key)
  submitted_urls = db.ListProperty(db.Key)
  quota_limit = db.IntegerProperty(default=URL_QUOTA_PER_USER)


def CreateBotsUser(user, quota_limit=URL_QUOTA_PER_USER):
  """Creates a new BotsUser.

  Initially nothing is added to user other than user and quota.

  Args:
    user: Currently signed in GAIA user (UserProperty).
    quota_limit: Quota Limit (Integer) (Default: 20).

  Raises:
    TypeError: If required parameter is missing.

  Returns:
    Newly created BotsUser Entity.
  """
  if not user:
    raise TypeError('Missing parameter - User is required.')
  bots_user = BotsUser(user=user, quota_limit=quota_limit)
  bots_user.put()
  return bots_user


def GetBotsUser(user):
  """Finds and return BotsUser.

  Args:
    user: Currently signed in GAIA user (UserProperty).

  Raises:
    TypeError: If required parameter is missing.

  Returns:
    Matching existing bots user (first user in case of more than one matching),
    else None.
  """
  if not user:
    raise TypeError('Missing parameter - User is required.')
  # Checking the memcache first.
  bots_user = memcache.get(user.user_id())
  if bots_user:
    return bots_user
  existing_bots_users = BotsUser.all().filter('user = ', user).fetch(20)
  if not existing_bots_users:
    return None
  if len(existing_bots_users) > 1:
    logging.warning('More than one matching existing users found. %s',
                    str(existing_bots_users))
  memcache.set(user.user_id(), existing_bots_users[0], MEMCACHE_EXP_TIME_IN_SEC)
  return existing_bots_users[0]


def GetUrls(bots_user_key, only_submitted_urls=False,
            only_interested_urls=False):
  """Finds and return urls associated with bots user.

  Args:
    bots_user_key: bots_user key (db.Key).
    only_submitted_urls: Flag to return only submitted urls (Boolean)
      (Default: False).
    only_interested_urls: Flag to return only interested urls (Boolean)
      (Default: False).

  Raises:
    TypeError: If required parameter is missing.
    BotsUserNotFoundError: If user with given key not found.

  Returns:
    Return a list of {'url': url, 'key', key} dictionaries associated with a
    given bots_user. If only_submitted_urls is True then returns only
    submitted urls. If only_interested_urls is True then returns only
    interested urls. If no flag is provided or both flags are True, then
    returns all urls associated with given user. In case of no urls,
    returns empty list.
  """
  if not bots_user_key:
    raise TypeError(
        'Missing parameter - bots_user_key is a required parameter.')
  bots_user = BotsUser.get(bots_user_key)
  if not bots_user:
    raise BotsUserNotFoundError('BotsUser does not exist - %s'
                                % str(bots_user_key))
  submitted_urls = []
  # Let's get submitted urls.
  if bots_user.submitted_urls and not only_interested_urls:
    submitted_urls = [{'url': x.url, 'key': str(x.key())} for x in
                      db.get(bots_user.submitted_urls)]
  if only_submitted_urls:
    return submitted_urls
  # Let's get interested urls.
  interested_urls = []
  if bots_user.interested_urls:
    interested_urls = [{'url': y.url, 'key': str(y.key())} for y in
                       db.get(bots_user.interested_urls)]
  if only_interested_urls:
    return interested_urls
  return submitted_urls + interested_urls


def _IsDuplicateInterestedUrl(bots_user_entity, url_key):
  """Checks if url_key exist in interested_urls.

  Args:
    bots_user_entity: bots_user entity (BotsUser).
    url_key: BotsUrl Entity to check for (db.Key).

  Returns:
    True if url_key exist in interested_urls, else False.
  """
  return str(url_key) in [str(x) for x in bots_user_entity.interested_urls]


def AddInterestedUrl(bots_user_key, existing_url_key):
  """Adds url to user models's interested_url.

  This method must be run inside trasaction along with _AddInterestedUser
  from url module to maintain the atomicity.

  Args:
    bots_user_key: bots_user entity key (db.Key).
    existing_url_key: Key of the url entity to update (db.Key).

  Raises:
    TypeError: If required parameter is missing.
    BotsUserNotFoundError: If user with given key not found.
  """
  if not existing_url_key:
    raise TypeError(
        'Missing parameter - existing_url_key is a required parameter.')
  if not bots_user_key:
    raise TypeError(
        'Missing parameter - bots_user_key is a required parameter.')
  bots_user = BotsUser.get(bots_user_key)
  if not bots_user:
    raise BotsUserNotFoundError('BotsUser does not exist - %s'
                                % str(bots_user_key))
  if _IsDuplicateInterestedUrl(bots_user, existing_url_key):
    logging.warning('Attempt to add duplicate url into interested urls.' +
                    'url_key: %s, bots_user_key: %s'
                    % (str(existing_url_key), str(bots_user_key)))
    return
  else:
    bots_user.interested_urls.append(existing_url_key)
    bots_user.put()


def _IsDuplicateSubmittedUrl(bots_user_entity, url_key):
  """Checks if url_key exist in submitted_urls.

  Args:
    bots_user_entity: bots_user entity (BotsUser).
    url_key: BotsUrl Entity to check for (db.Key).

  Returns:
    True if url_key exist in submitted_urls, else False.
  """
  return str(url_key) in [str(x) for x in bots_user_entity.submitted_urls]


def AddSubmittedUrl(bots_user_key, existing_url_key):
  """Adds url to user models's submitted_urls.

  This method must be run inside trasaction while inserting url using InsertUrl
  from url module to maintain the atomicity.

  Args:
    bots_user_key: bots_user entity key (db.Key).
    existing_url_key: Key of the url entity to update (db.Key).

  Raises:
    TypeError: If required parameter is missing.
    BotsUserNotFoundError: If user with given key not found.
  """
  if not existing_url_key:
    raise TypeError(
        'Missing parameter - existing_url_key is a required parameter.')
  if not bots_user_key:
    raise TypeError(
        'Missing parameter - bots_user_key is a required parameter.')
  bots_user = BotsUser.get(bots_user_key)
  if not bots_user:
    raise BotsUserNotFoundError('BotsUser does not exist - %s'
                                % str(bots_user_key))
  if _IsDuplicateSubmittedUrl(bots_user, existing_url_key):
    logging.warning('Attempt to add duplicate url into submitted urls. ' +
                    'url_key: %s, bots_user_key: %s'
                    % (str(existing_url_key), str(bots_user_key)))
    return
  else:
    bots_user.submitted_urls.append(existing_url_key)
    bots_user.put()


def HasMoreUrlQuota(bots_user_key):
  """Checks given user's quota.

  Args:
    bots_user_key: bots_user entity key (db.Key).

  Raises:
    TypeError: If required parameter is missing.
    BotsUserNotFoundError: If user with given key not found.

  Returns:
    True if user has more quota available, else False.
  """
  if not bots_user_key:
    raise TypeError(
        'Missing parameter - bots_user_key is a required parameter.')
  bots_user = BotsUser.get(bots_user_key)
  if not bots_user:
    raise BotsUserNotFoundError('BotsUser does not exist - %s'
                                % str(bots_user_key))
  total_count = len(bots_user.submitted_urls)
  return total_count < bots_user.quota_limit


def _UpdateQuotaLimit(bots_user_key, new_quota_limit):
  """Update given user's quota limit to new_quota_limit.

  Args:
    bots_user_key: bots_user entity key (db.Key).
    new_quota_limit: New quota limit (Integer).

  Raises:
    TypeError: If required parameter is missing.
    BotsUserNotFoundError: If user with given key not found.

  Returns:
    Updated BotsUser entity.
  """
  if not bots_user_key:
    raise TypeError(
        'Missing parameter - bots_user_key is a required parameter.')
  if not new_quota_limit:
    raise TypeError(
        'Missing parameter - new_quota_limit is a required parameter.')

  bots_user = BotsUser.get(bots_user_key)
  if not bots_user:
    raise BotsUserNotFoundError('BotsUser does not exist - %s'
                                % str(bots_user_key))
  bots_user.quota_limit = new_quota_limit
  return bots_user.put()


def IsInSubmittedUrl(bots_user_key, site_url):
  """Checks if url exist in submitted_urls.

  Args:
    bots_user_key: bots_user entity key (db.Key).
    site_url: Url to check for.

  Raises:
    TypeError: If required parameter is missing.
    BotsUserNotFoundError: If user with given key not found.

  Returns:
    True if site_url exist in submitted_urls, else False.
  """
  if not bots_user_key:
    raise TypeError(
        'Missing parameter - bots_user_key is a required parameter.')
  if not site_url:
    raise TypeError(
        'Missing parameter - site_url is a required parameter.')
  bots_user = BotsUser.get(bots_user_key)
  if not bots_user:
    raise BotsUserNotFoundError('BotsUser does not exist - %s'
                                % str(bots_user_key))
  if not bots_user.submitted_urls:
    return False
  else:
    submitted_url_entities = db.get(bots_user.submitted_urls)
    return site_url in [x.url for x in submitted_url_entities]
