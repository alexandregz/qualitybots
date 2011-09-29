#!/usr/bin/python2.4
#
# Copyright 2010 Google Inc. All Rights Reserved.
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


"""Handler for QualityBots Dashboard."""




import logging

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from handlers import base
from models import browser_score
from models import page_delta
from models import test_suite


DASHBOARD_URL = '/dashboard'


class ShowDashboard(base.BaseHandler):
  """Creates and computes necessary data for Chrome AppCompat Dashboard."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Create and render the dashboard page."""
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return

    q = browser_score.BrowserScore.all().order('-date')
    all_browser_score = []
    records = q.fetch(1000)
    last_cursor = q.cursor()
    while records:
      all_browser_score.extend(records)
      records = q.with_cursor(last_cursor)
      records = q.fetch(1000)
      last_cursor = q.cursor()

    trend_chart_data = []

    latest_test_suite = all_browser_score[0].test_suite
    latest_test_browser_name = '%s Canary' % (
        unicode(all_browser_score[0].browser))

    # Let's calculate score variation(diff) from run to run.
    score_diff = {}
    for current in range(len(all_browser_score)):
      # compare the last one to itself
      if current+1 == len(all_browser_score):
        prev = current
      else:
        prev = current+1

      score_diff[all_browser_score[current].key().name()] = abs(
          all_browser_score[current].layout_score -
          all_browser_score[prev].layout_score)

      # Calculate trend chart data.
      test_browser_name = '%s Canary' % (
          unicode(all_browser_score[current].browser))
      ref_browser_name = '%s Dev' % (
          unicode(all_browser_score[current].test_suite.ref_browser))
      build = '%s Vs %s' % (test_browser_name, ref_browser_name)
      run_date = str(all_browser_score[current].test_suite.date)
      trend_chart_data.append({
          'type': 'Layout Score',
          'score': all_browser_score[current].layout_score,
          'date': run_date,
          'build': build})

    latest_score_diff = score_diff[all_browser_score[0].key().name()]

    if latest_score_diff <= 0.1:
      light = 'green'
    elif  latest_score_diff > 0.1 and latest_score_diff <= 4.0:
      light = 'yellow'
    else:
      light = 'red'

    score_distribution = CalculateScoreDistribution(
        str(latest_test_suite.key()))
    logging.info(score_distribution)
    logging.info(trend_chart_data)

    template_values = {
        'latest_test_browser_name': latest_test_browser_name,
        'light': light,
        'latest_test_suite': latest_test_suite,
        'score_diff': score_diff,
        'all_browser_score': all_browser_score,
        'score_disribution': score_distribution,
        'trend_chart_data': trend_chart_data}

    self.RenderTemplate('dashboard.html', template_values)


def CalculateScoreDistribution(suite_key, include_ignore=False):
  """Calculate the score distribution for a specified test suite.

  Args:
    suite_key: An integer key that references the suite to use in calculations.
    include_ignore: A boolean that indicates whether we should include results
      with the ignore field set to True.

  Returns:
    A list of dictionaries with name and count fields that describe the score
    distribution.
  """
  suite_results = GetSuiteResults(suite_key, include_ignore)
  memcache_key = suite_key + '_score_distribution'
  score_distribution = memcache.get(memcache_key)
  if score_distribution is not None:
    logging.info('Got from memcache -' + memcache_key)
    return score_distribution
  score_distribution = []
  score_above_95 = {'name': 'Above 95', 'count': 0}
  score_90_95 = {'name': '90-95', 'count': 0}
  score_80_90 = {'name': '80-90', 'count': 0}
  score_60_80 = {'name': '60-80', 'count': 0}
  score_30_60 = {'name': '30-60', 'count': 0}
  score_below_30 = {'name': 'Below 30', 'count': 0}

  logging.info(len(suite_results))
  logging.info(suite_results)

  for unused_key, score in suite_results.items():
    logging.info('score-' + str(score))
    if score > 95:
      score_above_95['count'] += 1
    elif score > 90 and score <= 95:
      score_90_95['count'] += 1
    elif score > 80 and score <= 90:
      score_80_90['count'] += 1
    elif score > 60 and score <= 80:
      score_60_80['count'] += 1
    elif score > 30 and score <= 60:
      score_30_60['count'] += 1
    elif score < 30 and score <= 0:
      score_below_30['count'] += 1

  score_distribution.append(score_above_95)
  score_distribution.append(score_90_95)
  score_distribution.append(score_80_90)
  score_distribution.append(score_60_80)
  score_distribution.append(score_30_60)
  score_distribution.append(score_below_30)
  memcache.set(memcache_key, score_distribution, 300)
  return score_distribution


def GetSuiteResults(suite_key, include_ignore=False):
  """Load the suite results for the given suite key.

  Args:
    suite_key: An integer key that references the suite to use in calculations.
    include_ignore: A boolean that indicates whether we should include results
      with the ignore field set to True.

  Returns:
    A list of the PageDelta objects which describe the results of running the
    given test suite.
  """
  memcache_key = suite_key + '_suite_results'
  suite_results = memcache.get(memcache_key)
  if suite_results is not None:
    logging.info('Got from memcache -' + memcache_key)
    return suite_results

  suite = db.get(db.Key(suite_key))
  # Let's fetch all the results (page-delta).
  pd_results = []

  try:
    if include_ignore:
      q = suite.results
    else:
      q = suite.results
      q = suite.results.filter('ignore =', False)
  except AttributeError:
    logging.exception('Could not get the "results" attribute.')
    return pd_results

  pd = q.fetch(1000)
  last_cursor = q.cursor()
  while pd:
    pd_results.extend(pd)
    q = q.with_cursor(last_cursor)
    pd = q.fetch(1000)
    last_cursor = q.cursor()
  suite_results = {}
  for result in pd_results:
    suite_results[result.key()] = result.score
  memcache.set(memcache_key, suite_results, 300)
  return suite_results


application = webapp.WSGIApplication(
    [(DASHBOARD_URL, ShowDashboard)],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
