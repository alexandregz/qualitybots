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


"""Handler for setting configuration options for the system."""



from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from handlers import base
from models import aws_account_details


SET_AWS_ACCOUNT_URL = '/config/set_aws_account'
CONFIG_URL = '/config/config'


class SetAwsAccount(base.BaseHandler):
  """Handler to allow an admin to update the AWS credentials."""

  # Disable the "Invalid method name" warnings.
  # pylint: disable-msg=C6409
  def post(self):
    """Allows an admin user to set the AWS credentials used by the system.

    Url Params:
      aws_account_number: Amazon EC2 account number.
      aws_access_key_id: AWS access Key ID.
      aws_secret_access_key: AWS secret access key.
    """
    aws_account_number = self.GetRequiredParameter('aws_account_number')
    aws_access_key_id = self.GetRequiredParameter('aws_access_key_id')
    aws_secret_access_key = self.GetRequiredParameter('aws_secret_access_key')

    account_details = aws_account_details.AwsAccountDetails.get()

    if not account_details:
      account_details = aws_account_details.AwsAccountDetails()

    account_details.aws_account_number = aws_account_number
    account_details.aws_access_key_id = aws_access_key_id
    account_details.aws_secret_access_key = aws_secret_access_key

    account_details.put()


class ConfigPage(base.BaseHandler):
  """Handler for the configuration page."""

  # Disable the "Invalid method name" warnings.
  # pylint: disable-msg=C6409
  def get(self):
    """Displays the Add Url landing page."""
    self.RenderTemplate('config_settings.html', {})


application = webapp.WSGIApplication(
    [(SET_AWS_ACCOUNT_URL, SetAwsAccount),
     (CONFIG_URL, ConfigPage)],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
