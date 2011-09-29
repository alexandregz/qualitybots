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


"""AWS Account Details model.

This model is used to store AWS Account details (Account number, access_id
and secret_access_key).
"""




from google.appengine.ext import db


class AwsAccountDetails(db.Model):
  """Stores the details about AWS Account.

  Attributes:
    aws_account_number: Amazon EC2 account number.
    aws_access_key_id: AWS access Key ID.
    aws_secret_access_key: AWS secret access key.
  """
  aws_account_number = db.StringProperty()
  aws_access_key_id = db.StringProperty()
  aws_secret_access_key = db.StringProperty()
