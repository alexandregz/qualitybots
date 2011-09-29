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


"""Handlers for Test Suite."""




import cgi
import math
import urllib
import urlparse

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from handlers import base
# Disable 'unused import' lint warning.
# pylint: disable-msg=W0611
from models import browser
from models import browser_score
from models import page_delta
from models import test_suite

SUITE_LIST_URL = '/suite/list'
SUITE_DETAILS_URL = '/suite/details'
SUITE_COMPARE_URL = '/suite/compare'
SUITE_STATS_URL = '/suite/stats'
PASS_URL = '/pass'
FAIL_URL = '/fail'


def SetRecordData(delta, dev_threshold, score_threshold):
  """Calculates and set record data for compare suite view.

  Args:
    delta: List of similar page delta Entities(PageDelta entities which has same
        combination of ref and test browsers as well as matching URL).
    dev_threshold: Standard Deviation Threshold which will be used for deciding
        pass/fail.
    score_threshold: Layout Score Threshold which will be used for deciding
        pass/fail.

  Returns:
    List of record data object {'delta', 'standard deviation', 'flag for fail'}.
  """
  if delta:
    deviation = StandardDeviation(delta)
    fail = False
    for e in delta:
      if not e.score or e.score < score_threshold:
        fail = True
    if deviation > dev_threshold:
      fail = True
    record_data = {'delta': delta, 'std': deviation, 'fail': fail}
    return record_data
  else:
    # This will never execute as there will always be atleast one page delta
    # entity. None page delta entity are not allowed by Models.
    return None


def StandardDeviation(delta):
  """Calculates standard deviation for a given page deltas.

  Args:
    delta: Page Delta Entities(Must contain 1 or more values in delta).

  Returns:
    Standard Deviation Value.
  """
  if len(delta) == 1:
    return 0
  mean = 0
  for e in delta:
    if not e.score or e.score < 0:
      return None
    mean += e.score
  mean /= float(len(delta))
  deviation = 0
  for e in delta:
    deviation += (e.score-mean)**2
  deviation = math.sqrt(deviation/float(len(delta)-1))
  return deviation


class SuiteList(base.BaseHandler):
  """Handler for Test Suite List."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Get Handler for test suite list."""
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return

    suites = test_suite.TestSuite.all().order('-date')

    template_values = {
        'is_admin': users.is_current_user_admin(),
        'num_suites': suites.count(),
        'suites': suites}
    self.RenderTemplate('suite_list.html', template_values)


class CompareSuites(base.BaseHandler):
  """Handler for comparing test suites.

  CompareSuites handler is used to compare test suites. It automatically looks
  for the test suites which had exact same browser combination (i.e. same
  pair of ref and test browsers) and compares their results side by side.
  """

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Get handler for comparing test suites."""
    # Let's preprocess all request parameters.
    params = self.ProcessRequestParams()
    suite_key = params['suite_key']
    if not suite_key:
      self.response.out.write('No suite key specified.')
      return
    if suite_key.lower() == 'latest':
      suite = test_suite.TestSuite.all().order('-date')[0]
    else:
      suite = db.get(db.Key(suite_key))
    if not suite:
      self.response.out.write('No Matching suites found.')
      return

    processed_results = self.FetchAndProcessPageDelta(params, suite)
    delta_count = suite.results.count()
    data_count = suite.page_data_set.count()

    # Let's create URLs/links for template.
    start = params['offset']
    end = min(params['offset'] + params['limit'] - 1, delta_count)
    next_ = params['offset'] + params['limit']
    if next_ >= delta_count:
      next_ = ''
    else:
      next_ = str(next_)

    prev = params['offset'] - params['limit']
    if prev < 0:
      prev = ''
    else:
      prev = str(prev)
    prev_url = self.InsertQueryParams(params['url'], {'offset': prev})
    next_url = self.InsertQueryParams(params['url'], {'offset': next_})
    latest_url = self.InsertQueryParams(params['url'], {'order': '-date'})
    scores_hl_url = self.InsertQueryParams(params['url'], {'order': '-score'})
    scores_lh_url = self.InsertQueryParams(params['url'], {'order': 'score'})
    template_values = {
        'data_count': data_count,
        'delta_count': delta_count,
        'deltas': processed_results['deltas'],
        'end': end,
        'latest_url': latest_url,
        'limit': params['limit'],
        'next': next_,
        'next_url': next_url,
        'prev': prev,
        'prev_url': prev_url,
        'record_count': processed_results['record_count'],
        'scores_hl_url': scores_hl_url,
        'scores_lh_url': scores_lh_url,
        'start': start,
        'suite': suite,
        'url': params['url']}
    if params['display_stripdown'] and params['display_stripdown'] == 'true':
      self.RenderTemplate('suite_compare_stripdown.html', template_values)
      return
    else:
      self.RenderTemplate('suite_compare.html', template_values)
      return

  def InsertQueryParams(self, url, kvp):
    """Adds a query parameter to given URL.

    Args:
      url: Original URL.
      kvp: Key-value pair that you want to add as query parameter.

    Returns:
      Newly created URL.
    """
    url_parts = list(urlparse.urlparse(url))
    # Let's get query string which is at Index 4.
    query_string = dict(cgi.parse_qsl(url_parts[4]))
    query_string.update(kvp)
    url_parts[4] = urllib.urlencode(query_string)
    return urlparse.urlunparse(url_parts)

  def ProcessRequestParams(self):
    """Processes query parameters from request.

    This method does pre-processing of request parameters and prepares
    params object(key-value pair) which has ncessary request atrributes.

    Returns:
      Request parameter in param object.
    """
    suite_key = self.request.get('suite')
    url = self.request.url
    offset = int(self.GetOptionalParameter(parameter_name='offset',
                                           default_value=0))
    # Limits are used for pagination. Indicates number of records/entity
    # on a single page.
    limit = int(self.GetOptionalParameter(parameter_name='limit',
                                          default_value=50))
    order = self.GetOptionalParameter(parameter_name='order',
                                      default_value='-score')
    # Deviation threshold is used to determine if test case is passed or failed.
    deviation_threshold = float(
        self.GetOptionalParameter(parameter_name='dev_threshold',
                                  default_value=0))
    # Score threshold is used to determine if test case is passed or failed.
    # If layout score is higher than it's pass else fail.
    score_threshold = float(
        self.GetOptionalParameter(parameter_name='score_threshold',
                                  default_value=99))
    display_pass = self.GetOptionalParameter(parameter_name='display_pass')
    if display_pass:
      display_pass = display_pass.lower()
    display_fail = self.GetOptionalParameter(parameter_name='display_fail')
    if display_fail:
      display_fail = display_fail.lower()
    # Stripdown flag is used to produce simple list of URLs for a given
    # selection(pass/fail)
    display_stripdown = self.GetOptionalParameter(
        parameter_name='display_stripdown')
    if display_stripdown:
      display_stripdown = display_stripdown.lower()
    params = {
        'deviation_threshold': deviation_threshold,
        'display_fail': display_fail,
        'display_pass': display_pass,
        'display_stripdown': display_stripdown,
        'limit': limit,
        'offset': offset,
        'order': order,
        'score_threshold': score_threshold,
        'suite_key': suite_key,
        'url': url}
    return params

  def FetchAndProcessPageDelta(self, params, suite):
    """Fetches and processes Suite Delta.

    Args:
      params: Request Query Parameter object.
      suite: Test Suite Entity.

    Returns:
      Processed result object which contains page delta values and it's count.
    """
    # If any of the display parameter is set to true then let's fetch more
    # records upfront so we can filter.
    if ((params['display_fail'] and params['display_fail'] == 'true') or
        (params['display_pass'] and params['display_pass'] == 'true')):
      suite_deltas = suite.results.order(params['order']).fetch(
          limit=params['limit']*4, offset=params['offset'])
    else:
      suite_deltas = suite.results.order(params['order']).fetch(
          limit=params['limit'], offset=params['offset'])
    deltas = []
    record_count = 0
    for suite_delta in suite_deltas:
      # Number of records reach the limit requested, let's stop processing.
      if record_count == params['limit']:
        break
      # Let's check if compare_key is present or not.
      if not suite_delta.compare_key:
        # If not present, then let's generate and insert the key. This key is
        # used for quick lookup of page_delta values which have matching ref
        # test browser combination for a given URL.
        suite_delta.compare_key = page_delta.GetOrInsertUniqueKey(
            suite_delta.GetTestBrowser().key().name(),
            suite_delta.GetRefBrowser().key().name(),
            suite_delta.GetSiteUrl()).key()
        suite_delta.put()
      delta = suite_delta.compare_key.unique_compare_keys.order(
          params['order']).fetch(100)
      record_data = SetRecordData(
          delta, params['deviation_threshold'], params['score_threshold'])
      # let's count records into record_count only if results of it matches with
      # display option supplied with request.
      if params['display_fail'] and params['display_fail'] == 'true':
        if record_data['fail']:
          deltas.append(record_data)
          record_count += 1
        else:
          continue
      if params['display_pass'] and params['display_pass'] == 'true':
        if not record_data['fail']:
          deltas.append(record_data)
          record_count += 1
        else:
          continue
      # If nothing is set as display option then let's count every record.
      if (not params['display_fail']) and (not params['display_pass']):
        deltas.append(record_data)
        record_count += 1

    processed_results = {'deltas': deltas, 'record_count': record_count}
    return processed_results


class Failed(base.BaseHandler):
  """Handler for stripdown view of failed test cases/URLs."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Get handler for stripdown view of failed URLs."""
    self.redirect('/suite/compare?suite=latest&display_fail=true&'
                  'limit=1000&display_stripdown=true')


class Passed(base.BaseHandler):
  """Handler for stripdown view of passed test cases/URLs."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Get handler for stripdown view of passed URLs."""
    self.redirect('/suite/compare?suite=latest&display_pass=true&limit=1000&'
                  'display_stripdown=true')


class SuiteDetails(base.BaseHandler):
  """Handler for test suite detailed page."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Get handler for test suite details page."""
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return

    suite_key = self.request.get('suite')
    if not suite_key:
      self.response.out.write('No suite key specified.')
      return
    if suite_key.lower() == 'latest':
      suite = test_suite.TestSuite.all().order('-date')[0]
    else:
      suite = db.get(db.Key(suite_key))
    if not suite:
      self.response.out.write('No Matching suites found.')
      return

    offset = int(self.GetOptionalParameter(parameter_name='offset',
                                           default_value=0))
    # Limit is used for pagination. Indicates number of entities/records
    # to display on a single page.
    limit = int(self.GetOptionalParameter(parameter_name='limit',
                                          default_value=20))
    order = self.GetOptionalParameter(parameter_name='order',
                                      default_value='-date')
    deltas = suite.results.order(order).fetch(limit=limit, offset=offset)
    delta_count = suite.results.count()
    data_count = suite.page_data_set.count()
    start = offset
    end = min(offset + limit -1, delta_count)
    next_ = offset + limit
    if next_ >= delta_count:
      next_ = ''
    else:
      next_ = '%d' % next_

    prev = offset - limit
    if prev < 0:
      prev = ''
    else:
      prev = '%d' % prev

    ref_browser = suite.ref_browser.GetBrowserStringWithFlag()
    test_browsers = suite.GetTestBrowsersStringWithFlag()
    template_values = {
        'data_count': data_count,
        'deltas': deltas,
        'delta_count': delta_count,
        'end': end,
        'is_admin': users.is_current_user_admin(),
        'limit': limit,
        'next': next_,
        'order': order,
        'prerendered_string': page_delta.PRERENDERED_STRING,
        'prev': prev,
        'ref_browser': ref_browser,
        'start': start,
        'suite': suite,
        'test_browsers': test_browsers,
        'url': '/suite/details?suite=%s' % suite_key}
    self.RenderTemplate('suite_details.html', template_values)
    return


class SuiteStats(base.BaseHandler):
  """Test suite stats page handler."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Get handler for Test suite stats page."""
    suite_key = self.request.get('suite')
    if not suite_key:
      self.response.out.write('No suite key specified.')
      return
    suite = db.get(db.Key(suite_key))
    latest_result = suite.results.order('-date').get()
    if latest_result:
      latest_result_date = latest_result.date
      browser_scores = []
      browser_num_urls = []
      for test_browser in suite.GetTestBrowsers():
        score = browser_score.GetOrInsertBrowserScore(suite, test_browser)
        if score.date > latest_result_date:
          browser_scores.append('["%s", %f]' % (unicode(test_browser),
                                                score.layout_score))
          browser_num_urls.append('%s (%d urls)' % (unicode(test_browser),
                                                    score.num_urls))
        else:
          self.redirect('/stats/average?suite=%s' % suite_key)
          return
      template_values = {
          'suite': suite,
          'browser_scores': ',\n'.join(browser_scores),
          'test_browsers': browser_num_urls}
      self.RenderTemplate('suite_stats.html', template_values)
      return


application = webapp.WSGIApplication(
    [(SUITE_LIST_URL, SuiteList),
     (SUITE_DETAILS_URL, SuiteDetails),
     (SUITE_COMPARE_URL, CompareSuites),
     (SUITE_STATS_URL, SuiteStats),
     (PASS_URL, Passed),
     (FAIL_URL, Failed)],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
