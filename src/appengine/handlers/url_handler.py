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


"""Handles requests for user requested urls and associated pages."""




from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from handlers import base
from models import bots_user


URL_DASHBOARD_URL = '/url/dashboard'
URL_DETAIL_URL = '/url/detail'


class UrlDashboard(base.BaseHandler):
  """Handler for Url Dashboard."""

  # Disable the "Invalid method name" warnings.
  # pylint: disable-msg=C6409
  def get(self):
    """Displays the Add Url landing page."""
    user = users.get_current_user()

    if user:
      # If the user hasn't used Bots before (doesn't have a Bots user account)
      # then show the welcome addurl landing page.  Otherwise show the
      # dashboard.
      if bots_user.GetBotsUser(user):
        self.RenderTemplate('url_dashboard.html', {'email': user.email()})
      else:
        self.RenderTemplate('addurl_landing.html', {})
    else:
      self.redirect(users.create_login_url(self.request.uri))


class UrlDetail(base.BaseHandler):
  """Handler for the detailed results page of a particular URL."""

  # Disable the "Invalid method name" warnings.
  # pylint: disable-msg=C6409
  def get(self):
    """Displays the Add Url landing page."""
    user = users.get_current_user()

    if user:
      self.RenderTemplate('url_detail.html', {'email': user.email()})
    else:
      self.redirect(users.create_login_url(self.request.uri))


application = webapp.WSGIApplication(
    [(URL_DASHBOARD_URL, UrlDashboard),
     (URL_DETAIL_URL, UrlDetail)],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
