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


"""RunLog model.

RunLog model that describes a the result log of a test run. The RunLog entry
specifies the result for a specific test case instance of a test run.
"""




from common import enum
from google.appengine.ext import db
from models import url_config


class RunLog(db.Model):
  """RunLog model which acts as a queue for test cases.

  Attributes:
    url: A string that represents the URL for this particular log entry.
    config: Reference to associated UrlConfig (ReferenceProperty).
    token: A string reprenting the token that identifies the test run instance
      that this RunLog belongs to.
    client_id: A string indicating which client is currently processing this
      URL.
    client_info: A string representing a JavaScript dictionary of client
      configuration information used by the extension.
    creation_time: The date and time at which this model was created.
    updated_time: The last date and time that the model was updated.
    status: An integer value representing the status of this log instance.
    user: The user who created this run log instance.
    browser: An integer indicating the browser that is required for this log
      instance. The integer is from the enum.BROWSER enum.
    browser_version: A string indicating the browser version or channel that
      this machine is running.
    os: An integer indicating the operating system that this machine is
      running. The integer is from the enum.OS enum.
    priority: The priority for this testcase. Higher numbers indicate a higher
      priority.
    retry_count: The number of remaining times to retry this URL
    start_time: The time when this URL began being processed.
    end_time: The time when this URL finished being processed.
    duration: An integer count of milliseconds representing the processing
      duration for this URL.
  """
  url = db.StringProperty()
  config = db.ReferenceProperty(url_config.UrlConfig,
                                collection_name='run_log_entries')
  token = db.StringProperty()
  client_id = db.StringProperty()
  client_info = db.StringProperty()
  creation_time = db.DateTimeProperty()
  updated_time = db.DateTimeProperty(auto_now=True)
  status = db.IntegerProperty(choices=enum.CASE_STATUS.ListEnumValues())
  user = db.UserProperty(auto_current_user_add=True)
  browser = db.IntegerProperty(choices=enum.BROWSER.ListEnumValues())
  browser_version = db.StringProperty()
  os = db.IntegerProperty(choices=enum.OS.ListEnumValues())
  priority = db.IntegerProperty(default=0)
  retry_count = db.IntegerProperty(default=0)
  start_time = db.DateTimeProperty()
  end_time = db.DateTimeProperty()
  duration = db.IntegerProperty()
