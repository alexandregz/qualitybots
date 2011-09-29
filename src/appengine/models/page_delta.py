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


"""Page Delta and UniqueKey Model.

After comparing two page-data entities, information is stored in page delta
entity, which is used for comparison view between page data.
"""




from common import enum
from django.utils import simplejson
from google.appengine.ext import db

#Unused import warning.
#pylint: disable-msg=W0611

from models import browser
from models import data_list
from models import page_data
from models import site
from models import test_suite


PRERENDER_METADATA_KEY = 'prerender'
PRERENDERED_STRING = 'Pre-rendered'
NOT_PRERENDERED_STRING = 'Not Pre-rendered'


class UniqueKey(db.Model):
  """Stores the unique key for given combination.

  It calculates unique key using test browser, ref browser and site url. This
  model is solely created for faster look up and comparing data across multiple
  runs if runs have same combination of values (i.e. test browser, ref browser
  and site url). It exploits 'collection_name' lookup mechanism of AppEngine
  Models for faster performance.
  """


def GetOrInsertUniqueKey(test_browser, ref_browser, site_url):
  """Gets or inserts unique key value.

  Args:
    test_browser: Test Browser Key Name.
    ref_browser: Reference Browser Key Name.
    site_url: Site URL.

  Returns:
    Unique key.
  """
  return UniqueKey.get_or_insert(
      key_name='uniquekey_%s_%s_%s' % (test_browser, ref_browser, site_url))


class PageDelta(db.Model):
  """Page Delta Model.

  This model stores results from comparison of two page data models. Most of
  the properties here are reference property. It exploits 'collection_name' for
  faster lookup.

  Attributes:
    test_suite: Test Suite (Reference Property).
    site: WebSite (Reference Property).
    ref_data: PageData entity which is used as reference for comparison
        (Reference Property).
    ref_data_total_elem_count: Total element count from ref page data.
    ref_data_unmatched_elem_count: Unmatched element count from ref page data.
    test_data: PageData entity which is used in comparison
        (Reference Property).
    test_data_total_elem_count: Total element count from test page data.
    test_data_unmatched_elem_count: Unmatched element count from test page data.
    ref_browser: Reference Browser (Reference Property).
    ref_browser_channel:  An integer value from an enumeration that indicates
      the channel for the ref browser.
    test_browser: Test Browser (Reference Property).
    test_browser_channel:  An integer value from an enumeration that indicates
      the channel for the test browser.
    delta: DataList which has information about differences between two web
        pages (Reference Property).
    delta_index: A JSON string indicating which delta data list indices have
        information.
    dynamic_content: DataList which has information about dynamic content
        (e.g. Ads) (Reference Property).
    dynamic_content_index: A JSON string indicating which dynamic content data
        list indices have information.
    score: Computed layout score. Score indicates layout similarity at DOM pixel
        level. Negative score indicates comparison is not done yet.
    date: DateTime when comparison was done.
    compare_key: Unique reference key, solely created for faster lookup of
        compared results across runs.
    comments: Comments from user/admin about test run/result.
    bugs: List of bugs associated with/found by test run.
    ignore: Boolean flag indicating whether to ignore test run or not (Results
        marked ignore are not used in overall browser score and stats).
  """
  test_suite = db.ReferenceProperty(test_suite.TestSuite,
                                    collection_name='results')
  site = db.ReferenceProperty(site.Site)
  ref_data = db.ReferenceProperty(page_data.PageData,
                                  collection_name='ref_results')
  ref_data_total_elem_count = db.IntegerProperty()
  ref_data_unmatched_elem_count = db.IntegerProperty()

  test_data = db.ReferenceProperty(page_data.PageData,
                                   collection_name='test_results')
  test_data_total_elem_count = db.IntegerProperty()
  test_data_unmatched_elem_count = db.IntegerProperty()
  ref_browser = db.ReferenceProperty(browser.Browser,
                                     collection_name='ref_results')
  ref_browser_channel = db.IntegerProperty(
      choices=enum.BROWSERCHANNEL.ListEnumValues(), default=None)
  test_browser = db.ReferenceProperty(browser.Browser,
                                      collection_name='test_results')
  test_browser_channel = db.IntegerProperty(
      choices=enum.BROWSERCHANNEL.ListEnumValues(), default=None)
  delta = db.ReferenceProperty(data_list.DataList)
  delta_index = db.StringProperty()
  dynamic_content = db.ReferenceProperty(data_list.DataList,
                                         collection_name='dynamic_content')
  dynamic_content_index = db.StringProperty()
  score = db.FloatProperty(default=-1.0)
  date = db.DateTimeProperty(auto_now_add=True)
  compare_key = db.ReferenceProperty(UniqueKey,
                                     collection_name='unique_compare_keys')
  comments = db.StringProperty()
  bugs = db.ListProperty(int)
  ignore = db.BooleanProperty(default=False)
  # Copy of meta data from ref_data e.g. prerender. For faster lookup.
  ref_data_metadata = db.TextProperty(default=None)
  # Copy of meta data from test_data e.g. prerender. For faster lookup.
  test_data_metadata = db.TextProperty(default=None)

  def CreateIndices(self):
    """Create the indices for a given page delta object."""
    model_changed = False

    if not self.delta_index:
      self.delta_index = data_list.CreateDataListIndex(self.delta)
      model_changed = True

    if not self.dynamic_content_index:
      self.dynamic_content_index = data_list.CreateDataListIndex(
          self.dynamic_content)
      model_changed = True

    if model_changed:
      self.put()

  def GetSiteUrl(self):
    """Retrieves site URL associated with page-delta.

    If site information is not available for page-delta, then it retrieves
    this information first using reference page-data and stores it back.

    Returns:
      Site URL associated with page-delta.
    """
    if not self.site:
      self.site = self.ref_data.site
      self.put()
    return self.site.url

  def CalculateElemCount(self):
    """Calculates and updates various element count for test and ref data.

    If total element count and unmatched element count is not present, this will
    calculate it for test and ref data and update the entity.
    """
    if not self.ref_data_total_elem_count:
      ref_nodes_table = self.ref_data.GetNodesTable()
      self.ref_data_total_elem_count = len(ref_nodes_table)
      test_nodes_table = self.test_data.GetNodesTable()
      self.test_data_total_elem_count = len(test_nodes_table)
      if not self.delta_index:
        self.CreateIndices()
      unmatched_layout_table_part = []
      delta_index = simplejson.loads(self.delta_index)
      for i in delta_index:
        unmatched_layout_table_part.extend(self.delta.GetEntryData(i))
      test_unmatched_elem_set = set()
      ref_unmatched_elem_set = set()
      for pix in unmatched_layout_table_part:
        test_unmatched_elem_set.add(pix[2])
        ref_unmatched_elem_set.add(pix[3])
      self.test_data_unmatched_elem_count = len(test_unmatched_elem_set)
      self.ref_data_unmatched_elem_count = len(ref_unmatched_elem_set)
      self.put()

  def GetRefBrowser(self):
    """Retrieves reference browser entity associated with page-delta.

    If reference browser is not available for page-delta, then it retrieves
    this information first using reference page-data and stores it back.

    Returns:
      Reference Browser entity associated with page-delta.
    """
    if not self.ref_browser:
      self.ref_browser = self.ref_data.browser
      self.put()
    return self.ref_browser

  def GetTestBrowser(self):
    """Retrieves test browser entity associated with page-delta.

    If test browser is not available for page-delta, then it retrieves
    this information first using test page-data and stores it back.

    Returns:
      Test Browser entity associated with page-delta.
    """
    if not self.test_browser:
      self.test_browser = self.test_data.browser
      self.put()
    return self.test_browser

  def GetTestPrerenderTag(self):
    """Returns a prerender tag associated with test browser.

    This is done using test_data_metadata.

    Returns:
      Prerender tag associated with test browser.
    """
    return  self.GetPrerenderTag(self.test_data_metadata)

  def GetRefPrerenderTag(self):
    """Returns a prerender tag associated with ref browser.

    This is done using ref_data_metadata.

    Returns:
      Prerender tag associated with ref browser.
    """
    return  self.GetPrerenderTag(self.ref_data_metadata)

  def GetPrerenderTag(self, metadata):
    """Returns a prerender tag from browser metadata.

    Args:
      metadata: String indicating metadata information.

    Returns:
      Prerender tag associated with appropriate browser.
    """
    prerender_tag = ''
    if metadata:
      metadata_dict = simplejson.loads(metadata)
      if PRERENDER_METADATA_KEY in metadata_dict:
        if metadata_dict[PRERENDER_METADATA_KEY]:
          prerender_tag = PRERENDERED_STRING
        else:
          prerender_tag = NOT_PRERENDERED_STRING
    return prerender_tag

  def GetNumPixels(self):
    """Calculates number of pixels associated with page-delta.

    Returns:
      Number of pixels.
    """
    return self.ref_data.width * self.ref_data.height

  def Completed(self):
    """Check to see if comparison is completed.

    Assumption here is that initial score is always negative(-1).

    Returns:
      True if comparison is completed else false.
    """
    return self.score >= 0

  def _ComputePercentDifferent(self, count):
    """Calculates difference in percentage between page-data entities.

    Args:
      count: Number of pixels that are different.

    Returns:
      Page difference in percentage of pixels.
    """
    return count / float(self.GetNumPixels()) * 100.0

  def ComputeScore(self):
    """Computes and stores layout score."""
    if self.delta.EntriesReady():
      count = 0
      # Let's count the length of differences (pixel difference).
      for entry in self.delta.data_entries:
        count += entry.length

      # Deducting differences from 100 gives us percent of similarity between
      # pages, which is used as layout score.
      self.score = 100.0 - self._ComputePercentDifferent(count)
      self.put()

  def UpdateComments(self, comments):
    """Updates comments property of page-delta.

    Args:
      comments: User Comments.
    """
    self.comments = comments
    self.put()

  def UpdateIgnoreFlag(self, ignore):
    """Updates Ignore Flag of page-delta.

    Args:
      ignore: Ignore Flag (boolean).
    """
    self.ignore = ignore
    self.put()

  def UpdateBugs(self, bugs):
    """Updates bugs porperty of page-delta.

    Args:
      bugs: List of Bug numbers.
    """
    if not bugs:
      return
    else:
      self.bugs = bugs
      self.put()

  def DeleteData(self):
    """Deletes associated pixel difference info (i.e. delta property.)."""
    if self.delta:
      self.delta.ClearEntries()
      db.delete(self.delta)
