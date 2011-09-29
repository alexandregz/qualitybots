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


"""Computes average scores for browsers."""



import datetime

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from handlers import base
from models import browser_score


COMPUTE_AVERAGE_SCORE_URL = '/stats/average'
COMPUTE_MULTI_SUITE_AVERAGE_URL = '/stats/multi'


class ComputeAverageScore(webapp.RequestHandler):
  """Handler for computing average suite scores.

  Computes average scores for each browser involved in a suite.
  """

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Calculates the average suite score per test browser."""
    suite_key = self.request.get('suite')
    suite = db.get(db.Key(suite_key))
    test_browsers = suite.GetTestBrowsers()

    # Fetch all the results (page-delta).
    pd_results = []
    query = suite.results
    pd = query.fetch(1000)
    last_cursor = query.cursor()
    while pd:
      pd_results.extend(pd)
      query = query.with_cursor(last_cursor)
      pd = query.fetch(1000)
      last_cursor = query.cursor()

    scores = {}
    counts = {}
    for test_browser in test_browsers:
      scores[test_browser.key().name()] = 0
      counts[test_browser.key().name()] = 0

    for result in pd_results:
      # Check for invalid results
      if result.score < 0:
        continue

      browser_key = result.GetTestBrowser().key().name()

      # Only count results that are non-ignored.
      if not result.ignore:
        scores[browser_key] += result.score
        counts[browser_key] += 1

    for test_browser in test_browsers:
      test_browser_key = test_browser.key().name()
      scores[test_browser_key] /= float(counts[test_browser_key])
      average_score = browser_score.GetOrInsertBrowserScore(suite, test_browser)
      average_score.layout_score = scores[test_browser_key]
      average_score.num_urls = counts[test_browser_key]
      average_score.date = datetime.datetime.utcnow()
      average_score.put()

    self.redirect('/suite/stats?suite=%s' % suite_key)


class GetAverageScoreOfMultiSuites(base.BaseHandler):
  """Handler for computing average score among multiple suites.

  Computes the average scores for each browser in the specified suites.
  """

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Calculates the average score per test browser across mutliple suites."""
    suite_keys = self.request.get_all('suite')

    browser_scores = {}
    browser_num_urls = {}

    for suite_key in suite_keys:
      suite = db.get(db.Key(suite_key))

      for test_browser in suite.GetTestBrowsers():
        score = browser_score.GetOrInsertBrowserScore(suite, test_browser)
        browser_name = unicode(test_browser)
        if not browser_name in browser_scores:
          browser_scores[browser_name] = 0
          browser_num_urls[browser_name] = 0
        total_urls = browser_num_urls[browser_name] + score.num_urls
        browser_scores[browser_name] = (
            browser_scores[browser_name] * browser_num_urls[browser_name] +
            score.layout_score * score.num_urls) / float(total_urls)
        browser_num_urls[browser_name] = total_urls

    score_output = []
    num_urls_output = []
    keys = browser_scores.keys()
    keys.sort()
    for browser_name in keys:
      score_output.append('["%s", %f]' % (browser_name,
                                          browser_scores[browser_name]))
      num_urls_output.append('%s (%d urls)' % (browser_name,
                                               browser_num_urls[browser_name]))

    template_values = {'browser_scores': ',\n'.join(score_output),
                       'test_browsers': num_urls_output}

    self.RenderTemplate('suite_stats.html', template_values)


application = webapp.WSGIApplication(
    [(COMPUTE_AVERAGE_SCORE_URL, ComputeAverageScore),
     (COMPUTE_MULTI_SUITE_AVERAGE_URL, GetAverageScoreOfMultiSuites)],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
