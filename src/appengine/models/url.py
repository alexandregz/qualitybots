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


"""URL model to store the URL submitted by Users.

URL model stores URL itself and important pieces parsed out of the url to
make it easy for searching later on.
"""




import logging
import urlparse

from google.appengine.api import taskqueue
from google.appengine.ext import db

from models import bots_user


ADD_DEFAULT_URL_CONFIG_URL = '/signup/add_default_url_config'
ADD_SUBMITTED_URL = '/signup/add_submitted_url'
ADD_INTERESTED_URL = '/signup/add_interested_url'


class UrlNotFoundError(Exception):
  pass


class QuotaError(Exception):
  pass


class Url(db.Model):
  """Stores URL signed by users and other important information.

  Attributes:
    url: Complete Url.
    creation_date: Date of creation.
    domain: Domain name of the url submitted.
    interested_users: List of interested users (BotsUser key). This list
      includes bots_users who have submitted this URL.
  """
  url = db.StringProperty()
  creation_date = db.DateTimeProperty(auto_now_add=True)
  domain = db.StringProperty(default='')
  interested_users = db.ListProperty(db.Key)


def SearchUrl(url, fetch_limit=20):
  """Search possible matching URL entity using input Url and domain.

  Args:
    url: Url to search for.
    fetch_limit: Limit to apply while fetching.

  Returns:
    List of possible matching url entities.
  """
  # If url does not start with http, let's prepend it.
  if not url.startswith('http'):
    url = 'http://' + url
  parsed = urlparse.urlsplit(url, scheme='http')
  domain = parsed.netloc
  parsed_url = parsed.geturl()
  matching_urls = db.GqlQuery(
      'SELECT * FROM Url WHERE url= :1', parsed_url).fetch(fetch_limit)
  if matching_urls:
    return matching_urls
  else:
    matching_urls = db.GqlQuery(
        'SELECT * FROM Url WHERE domain= :1', domain).fetch(fetch_limit)
    return matching_urls


def InsertUrl(url, bots_user_key):
  """Create/Insert URL entity using input Url, domain and bots_user.

  This method creates a URL as well as default UrlConfig corresponding to that
  user and url. This happens in transaction to guarantee the atomicity of
  operation.

  Args:
    url: Url to add.
    bots_user_key: bots_user entity key (db.Key).

  Raises:
    TypeError: If required parameter is missing.
    QuotaError: When user has reached max allowed quota limit.

  Returns:
    Newly created url entity.
  """
  if not url:
    raise TypeError(
        'Missing parameter - url is a required parameter.')
  if not bots_user_key:
    raise TypeError(
        'Missing parameter - bots_user_key is a required parameter.')
  if not bots_user.HasMoreUrlQuota(bots_user_key):
    raise QuotaError('User has reached the max allowed quota.')

  # If url does not start with http, let's prepend it.
  if not url.startswith('http'):
    url = 'http://' + url
  parsed = urlparse.urlsplit(url)
  domain = parsed.netloc

  # Let's create a method so we can run that in transaction. This method will
  # insert url, add it to submitted_urls and also create default urlconfig.
  def _Txn():
    url_entity = Url(url=url, domain=domain, interested_users=[bots_user_key])
    url_key = url_entity.put()
    # Let's use transactional tasks to get atomicity and still avoid running
    # into same entity group requirement of appengine transaction.
    task_params = {'existing_url_key': str(url_key),
                   'bots_user_key': str(bots_user_key)}
    default_url_config_task = taskqueue.Task(url=ADD_DEFAULT_URL_CONFIG_URL,
                                             params=task_params, method='POST')
    default_url_config_task.add(queue_name='signup', transactional=True)
    add_submitted_url_task = taskqueue.Task(url=ADD_SUBMITTED_URL,
                                            params=task_params, method='POST')
    add_submitted_url_task.add(queue_name='signup', transactional=True)
    return url_entity
  return db.run_in_transaction(_Txn)


def _IsDuplicateInterestedUser(url_entity, bots_user_key):
  """Checks if bots_user_key exist in interested_users.

  Args:
    url_entity: BotsUrl Entity to check for.
    bots_user_key: bots_user entity key (db.Key).

  Returns:
    True if bots_user_key exist in interested_users, else False.
  """
  return str(bots_user_key) in [str(x) for x in url_entity.interested_users]


def _AddInterestedUserAndUrl(existing_url_key, bots_user_key):
  """Adds a url to BotsUser's interested_url and user to interested_user field.

  This method must be run in trasaction to maintain the atomicity.

  Args:
    existing_url_key: Key of the url entity to update (db.Key).
    bots_user_key: bots_user entity key (db.Key).

  Raises:
    UrlNotFoundError: If no url exist with existing_url_key.

  Returns:
    Updated url entity.
  """
  existing_url = Url.get(existing_url_key)
  if not existing_url:
    raise UrlNotFoundError(
        'URL entity does not exist - %s' % (str(existing_url_key)))
  if _IsDuplicateInterestedUser(existing_url, bots_user_key):
    logging.warning('Attempt to add duplicate user into interested users.' +
                    'url_key: %s, bots_user_key: %s'
                    % (str(existing_url_key), str(bots_user_key)))
    return
  else:
    existing_url.interested_users.append(bots_user_key)
    existing_url.put()
    # Let's use transactional tasks to get atomicity and still avoid running
    # into same entity group requirement of appengine transaction.
    task_params = {'existing_url_key': str(existing_url_key),
                   'bots_user_key': str(bots_user_key)}

    add_interested_url_task = taskqueue.Task(url=ADD_INTERESTED_URL,
                                             params=task_params, method='POST')
    add_interested_url_task.add(queue_name='signup', transactional=True)
    return existing_url


def AddInterestedUserAndUrl(existing_url_key, bots_user_key):
  """Updates user models's interested_url and url model's interested_user field.

  This method updates url and bots_user model in trasaction to maintain the
  atomicity.

  Args:
    existing_url_key: Key of the url entity to update (db.Key).
    bots_user_key: bots_user entity key (db.Key).

  Raises:
    TypeError: If required parameter is missing.

  Returns:
    Updated url entity.
  """
  if not existing_url_key:
    raise TypeError(
        'Missing parameter - existing_url_key is a required parameter.')
  if not bots_user_key:
    raise TypeError(
        'Missing parameter - bots_user_key is a required parameter.')
  return db.run_in_transaction(_AddInterestedUserAndUrl, existing_url_key,
                               bots_user_key)
