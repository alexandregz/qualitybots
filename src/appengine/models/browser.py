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


"""Browser model and method for get or insert from user agent string.

Browser model stores name and version of a browser.
"""



import logging
import re


from google.appengine.ext import db

from common import chrome_channel_util
from common import enum
from common import useragent_parser


OS_MAPPING = {'windows': enum.OS.WINDOWS, 'linux': enum.OS.LINUX,
              'macintosh': enum.OS.MAC, 'cros': enum.OS.CHROMEOS}
BROWSER_MAPPING = {'chrome': enum.BROWSER.CHROME,
                   'firefox': enum.BROWSER.FIREFOX}
CHANNEL_MAPPING = {'stable': enum.BROWSERCHANNEL.STABLE,
                   'beta': enum.BROWSERCHANNEL.BETA,
                   'dev': enum.BROWSERCHANNEL.DEV,
                   'canary': enum.BROWSERCHANNEL.CANARY}
LAYOUT_ENGINE_MAPPING = {'applewebkit': enum.LAYOUT_ENGINE_FAMILY.WEBKIT,
                         'gecko': enum.LAYOUT_ENGINE_FAMILY.GECKO}


class Browser(db.Model):
  """Stores browser information.

  Attributes:
    browser_family: An integer value from enum representing browser family.
    version: A string indicating the version of the browser.
    os: An integer value from enum representing OS family (default=None).
    os_version: A string indicating the version of the OS (default=None).
    layout_engine_family: An integer value from enum representing layout engine
      family.
    layout_engine_version: A string indicating the version of the layout_engine
      (default=None).
    flag: A string indicating special flag used by client browser
      (e.g. Chrome Instant Pages) (default=None).
    channel: An integer value from an enumeration that indicates the channel
      for the browser (default=None).
    is_active: Boolean flag indicating if browser is being used or not
      (default=True).
    user_agent: Browser user agent string (default=None).
  """
  browser_family = db.IntegerProperty(
      choices=enum.BROWSER.ListEnumValues())
  version = db.StringProperty()
  os = db.IntegerProperty(choices=enum.OS.ListEnumValues(), default=None)
  os_version = db.StringProperty(default=None)
  layout_engine_family = db.IntegerProperty(
      choices=enum.LAYOUT_ENGINE_FAMILY.ListEnumValues())
  layout_engine_version = db.StringProperty(default=None)
  flag = db.StringProperty(default=None)
  channel = db.IntegerProperty(
      choices=enum.BROWSERCHANNEL.ListEnumValues(), default=None)
  user_agent = db.StringProperty(default=None)

  def __unicode__(self):
    """Returns unicode representation of this Browser object."""
    unicode_str = u'%s %s' % (enum.BROWSER.LookupKey(
        self.browser_family).title(), self.version)
    return unicode_str

  def GetBrowserStringWithFlag(self):
    """Return a string representation of the Browser object and flag."""
    if self.flag:
      return '%s (%s)' % (self.__unicode__(), self.flag)
    else:
      return self.__unicode__()


def GetOrInsertBrowser(user_agent, channel=None, flag=None):
  """Gets or inserts the Browser object for the given user agent string.

  Args:
    user_agent: A string representing browser user agent.
    channel: A string indicating channel of the browser (Default: None).
    flag: A case-insensitive string representing flag value from client
      (e.g. Chrome Instant Pages) (Default: None).

  Returns:
    Newly created/existing Browser Entity.
  """
  if flag:
    flag = flag.lower()
  parser = useragent_parser.UAParser(user_agent)
  browser_family = BROWSER_MAPPING[parser.GetBrowserFamily()]
  browser_version = parser.GetBrowserVersion()
  os_family = parser.GetOSFamily()
  if os_family:
    os_family = OS_MAPPING[parser.GetOSFamily()]
  os_version = parser.GetOSVersion()
  layout_engine_family = LAYOUT_ENGINE_MAPPING[parser.GetLayoutEngineFamily()]
  layout_engine_version = parser.GetLayoutEngineVersion()
  logging.info('\n'.join(['user_agent: %s', 'browser_family: %s',
                          'browser_version: %s','os_family: %s',
                          'os_version: %s, layout_engine_family: %s,'
                          'layout_engine_version: %s',
                          'channel: %s',
                          'flag: %s']),
               user_agent, browser_family, browser_version, os_family,
               os_version, layout_engine_family, layout_engine_version,
               channel, flag)
  # For browser chrome, let's try to use channel for finding a matching existing
  # browser.
  if browser_family == enum.BROWSER.CHROME:
    # Channel is not present, then let's try to identify.
    if not channel:
      if os_family:
        channel_util = chrome_channel_util.ChromeChannelUtil()
        channel = channel_util.IdentifyChannel(
            enum.OS.LookupKey(os_family), browser_version)
        logging.info('Identified Channel as %s', channel)
        channel = CHANNEL_MAPPING[channel]
      else:
        logging.info('Channel can not be identified due to missing os_family.')
        channel = None
    else:
      channel = CHANNEL_MAPPING[channel]

    browser = db.GqlQuery(
        'SELECT * FROM Browser WHERE browser_family= :1 AND version = :2 AND '
        'os = :3 AND os_version = :4 AND flag = :5 AND channel = :6',
        browser_family, browser_version, os_family, os_version, flag,
        channel).get()
  else:
    browser = db.GqlQuery(
        'SELECT * FROM Browser WHERE browser_family= :1 AND version = :2 AND '
        'os = :3 AND os_version = :4 AND flag = :5',
        browser_family, browser_version, os_family, os_version, flag).get()
  # If no matching browser found then let's create new.
  if not browser:
    browser = Browser(
        browser_family=browser_family, version=browser_version, os=os_family,
        os_version=os_version, layout_engine_family=layout_engine_family,
        layout_engine_version=layout_engine_version, flag=flag,
        channel=channel, user_agent=user_agent)
    browser.put()

  return browser
