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


"""Site model and method for get or insert from URL string.

Site model stores root URL for a site. i.e. scheme://netloc. Remember, it
doesn't store path or any other parameters from a URL.
e.g. http://www.google.com:80/%7investors/q4r.html -- For this URL we will only
store http://www.google.com:80.
"""



import urlparse

from google.appengine.api import users
from google.appengine.ext import db

from models import bots_user
from models import url_config


MAX_FETCH_COUNT = 1000


class SiteError(Exception):
  pass


class Site(db.Model):
  """Stores site root URL."""
  url = db.StringProperty()
  domain = db.StringProperty()
  # This UrlConfig key reference is used to glue the results and input url.
  config = db.ReferenceProperty(url_config.UrlConfig, default=None,
                                collection_name='associated_sites')


def GetOrInsertSiteFromUrl(url_string, url_config_key):
  """Parses an input URL to get only the root and gets or inserts an entity.

  It tries to glue site and url_config together while accessing or creating
  site entity.

  Args:
    url_string: Site URL.
    url_config_key: UrlConfig Key Reference (db.Key).

  Raises:
    TypeError: If required parameter is missing.
    SiteError: If no matching url_config found for given url_config_key.

  Returns:
    Newly created/existing Site Entity.
  """
  if not url_string:
    raise TypeError(
        'Missing parameter - url_string is a required parameter.')
  if not url_config_key:
    raise TypeError(
        'Missing parameter - url_config_key is a required parameter.')
  my_url_config = db.get(url_config_key)
  if not my_url_config:
    raise SiteError('Invalid url_config_key:%s , no matching UrlConfig found.'
                    % (str(url_config_key)))

  url = url_string
  # If url does not start with http, let's prepend it.
  if not url.startswith('http'):
    url = 'http://' + url
  parsed = urlparse.urlsplit(url.strip())
  domain = parsed.netloc

  # Let's find the exact site which has same config.
  site = my_url_config.associated_sites.get()
  if not site:
    # If exact matching site not found then let's find sites with matching urls.
    matching_sites = Site.all().filter('url =', url).fetch(MAX_FETCH_COUNT)
    for matching_site in matching_sites:
      # If site doesn't have config associated and supplied config is without
      # auth then we can safely assoicate config with this site.
      if not matching_site.config and not my_url_config.auth_enabled:
        matching_site.config = my_url_config.key()
        matching_site.domain = domain
        matching_site.put()
        return matching_site
    # If no matching site found or auth is enabled for config then let's
    # create new site entity.
    site = Site(url=url, domain=domain, config=my_url_config.key())
    site.put()
  return site
