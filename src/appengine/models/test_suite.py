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


"""TestSuite model.

TestSuite model stores the date and time of a test suite, datastore keys of
test browsers and reference browser and its status.
"""


import datetime
import re


from google.appengine.ext import db

from common import enum
from models import browser


class TestSuite(db.Model):
  """TestSuite Model which stores various information about Test Run.

  Attributes:
    date: DateTime of test suite.
    ref_browser: Reference browser entity (Reference Property).
    test_browsers: List of reference browser keys.
    description: Text description of test suite.
  """
  date = db.DateTimeProperty()
  ref_browser = db.ReferenceProperty(browser.Browser)
  test_browsers = db.ListProperty(db.Key)
  description = db.TextProperty(default='')

  def GetNumSites(self):
    """Gets an estimate on number of URLs tested.

    Returns:
      Estimated number of sites tested.
    """
    test_browsers_count = len(self.test_browsers)
    ref_browsers_count = 1
    test_data = self.page_data_set
    return test_data.count() / (test_browsers_count + ref_browsers_count)

  def GetTestBrowsers(self):
    """Gets list of test browser entities.

    Returns:
     List of test browser entities.
    """
    return browser.Browser.get(self.test_browsers)

  def GetTestBrowsersStringWithFlag(self):
    """Gets the TestBrowsers String with flag.

    Returns:
      Testbrowsers string with flag.
    """
    return u', '.join([b.GetBrowserStringWithFlag()
                       for b in self.GetTestBrowsers()])

  def AddTestBrowser(self, test_browser):
    """Add a given test browser's key name into test browser key list.

    This method avoids adding duplicates.

    Args:
      test_browser: Test Browser Entity.
    """
    key_to_add = test_browser.key()
    # Let's make sure we don't add duplicate values.
    if key_to_add not in self.test_browsers:
      self.test_browsers.append(key_to_add)
      self.put()


def _SplitDatetimeString(datetime_string):
  """Splits a datetime string into list of its components.

  Args:
    datetime_string: DateTime String Value.

  Returns:
    Componentized values of datetime string.
  """
  p = r'([0-9]+)-([0-9]+)-([0-9]+) ([0-9]+):([0-9]+):([0-9]+).([0-9]+)'
  return re.search(p, datetime_string).groups()


def GetDatetimeFromDatetimeString(datetime_string):
  """Creates datetime object from string datetime value.

  Args:
    datetime_string: DateTime String Value.

  Returns:
    DateTime Object.
  """
  d = [int(v) for v in _SplitDatetimeString(datetime_string)]
  return datetime.datetime(d[0], d[1], d[2], d[3], d[4], d[5], d[6])


def GetSuiteKeyNameFromDatetimeString(datetime_string):
  """Generates test suite key name from datetime string value.

  Args:
    datetime_string: DateTime String Value.

  Returns:
    Test Suite Key Name.
  """
  d = _SplitDatetimeString(datetime_string)
  return 'suite_' + ('_'.join(d))


def GetOrInsertSuite(suite_date, ref_browser_user_agent, ref_browser_channel):
  """Gets or inserts TestSuite.

  Args:
    suite_date: Test Suite Date.
    ref_browser_user_agent: Reference Browser User Agent.
    ref_browser_channel: String representing reference browser channel.

  Returns:
    Inserted/Retrieved Test Suite Key Name.
  """
  key_name = GetSuiteKeyNameFromDatetimeString(suite_date)
  # Let's see if suite exist already.
  test_suite = TestSuite.get_by_key_name(key_name)
  if not test_suite:
    flag = None
    date = GetDatetimeFromDatetimeString(suite_date)
    # Let's check if ref_browser has flag or not. Flag are pipe separated
    # from browser user agent. So let's check for pipe ('|') and parse it.
    if ref_browser_user_agent.count('|'):
      flag = ref_browser_user_agent.split('|')[1]
      ref_browser = browser.GetOrInsertBrowser(ref_browser_user_agent,
                                               ref_browser_channel, flag=flag)
    else:
      ref_browser = browser.GetOrInsertBrowser(ref_browser_user_agent,
                                               ref_browser_channel)
    test_suite = TestSuite.get_or_insert(key_name=key_name, date=date,
                                         ref_browser=ref_browser,
                                         test_browsers=[])
  return test_suite


def GetLatestSuite():
  """Returns latest TestSuite entity."""
  q = TestSuite.all().order('-date')
  return q.get()


def UpdateRefBrowser(suite, new_ref_browser, delete_old_ref=False):
  """Updates reference browser in TestSuite.

  Args:
    suite: Test Suite Entity.
    new_ref_browser: Reference Browser Entity.
    delete_old_ref: Delete Old Reference flag (default: False).

  Returns:
    Updated Test Suite Entity.
  """
  old_ref_browser = suite.ref_browser.key()
  suite.ref_browser = new_ref_browser
  suite.put()
  if delete_old_ref:
    # Let's delete old reference now.
    db.delete(old_ref_browser)
  return suite
