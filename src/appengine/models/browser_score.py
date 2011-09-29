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


"""BrowserScore Model.

BrowserScore model stores the agrregated layout score and test run information.
"""




import datetime

from google.appengine.ext import db

#Unused import warning.
#pylint: disable-msg=W0611
from models import browser
from models import test_suite


class BrowserScore(db.Model):
  """Stores average layout score of a browser per test suite.

  It also stores the number of URLs that generated this score so that average
  score across multiple suites can be calculated.
  """
  test_suite = db.ReferenceProperty(test_suite.TestSuite)
  browser = db.ReferenceProperty(browser.Browser)
  layout_score = db.FloatProperty(default=0.0)
  num_urls = db.IntegerProperty(default=0)
  date = db.DateTimeProperty(default=datetime.datetime.min)


def GetBrowserScoreKeyName(suite, browser_instance):
  """Key name generator for browser score model.

  Args:
    suite: TestSuite Entity.
    browser_instance: Browser Entity.

  Returns:
    BrowserScore key name as string.
  """
  return '%s_%s' % (suite.key().name(), browser_instance.key().name())


def GetOrInsertBrowserScore(suite, browser_instance):
  """Gets or Inserts BrowserScore Entity.

  Args:
    suite: TestSuite Entity.
    browser_instance: Browser Entity.

  Returns:
    Newly created/existing BrowserScore Entity.
  """
  return BrowserScore.get_or_insert(
      key_name=GetBrowserScoreKeyName(suite, browser_instance),
      test_suite=suite, browser=browser_instance)
