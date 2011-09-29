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


"""Handler for providing a list of files for the client to download."""




import logging

from django.utils import simplejson

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from handlers import base


CLIENT_FILE_LIST = '/client_file_list'


class ClientFileList(base.BaseHandler):
  """Handler to provide a list of files for the client to download."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Provides a list of files to download and execute."""
    file_list = ['bots_client_bundle.zip', 'browser_install_bundle.zip',
                 'webdriver_content_script.js']
    execution_list = ['browser_install_bundle.zip', 'bots_client_bundle.zip']
    output_data = {'file_list': file_list, 'execution_list': execution_list}

    self.response.out.write(simplejson.dumps(output_data))


application = webapp.WSGIApplication(
    [(CLIENT_FILE_LIST, ClientFileList)],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
