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


"""Client Machine model.

This model is describes a client machine that processes URLs for bots.
"""




import logging

from google.appengine.ext import db

from common import enum

MAX_RETRIES = 10


class ClientMachine(db.Model):
  """Describes a client machine that processes URLs for bots.

  Attributes:
    creation_time: The date and time at which this model was created.
    updated_time: The last date and time that the model was updated.
    vm_service: An integer id representing the vm service used to run this
      machine. The integer is from the enum.VM_SERVICE enum.
    client_id: A string that uniquely identifies this machine. For EC2
      machines, this is the instance id.
    os: An integer indicating the operating system that this machine is
      running. The integer is from the enum.OS enum.
    browser: An integer indicating the browser that this machine is running.
      The integer is from the enum.BROWSER enum.
    browser_version: A string indicating the browser version or channel that
      this machine is running.
    status: An integer that represents the status of this machine.
    install_log: A string representing the log from initializing the system.
    run_log: A string representing the log from running the system.
    retry_count: An integer representing the current retry number
    token: a string representing the token used by the instance to request test
      cases.
    installer_url: A string representing the url to use to download the
      browser on the client machine.
  """
  creation_time = db.DateTimeProperty(auto_now_add=True)
  updated_time = db.DateTimeProperty(auto_now=True)
  vm_service = db.IntegerProperty(choices=enum.VM_SERVICE.ListEnumValues())
  client_id = db.StringProperty()
  os = db.IntegerProperty(choices=enum.OS.ListEnumValues())
  browser = db.IntegerProperty(choices=enum.BROWSER.ListEnumValues())
  browser_version = db.StringProperty()
  status = db.IntegerProperty(choices=enum.MACHINE_STATUS.ListEnumValues())
  initialization_log = db.TextProperty()
  run_log = db.TextProperty()
  retry_count = db.IntegerProperty(default=0)
  token = db.StringProperty()
  installer_url = db.TextProperty()


def GetClientMachineFromInstanceId(instance_id):
  """Get the client machine model with the given instance id.

  Args:
    instance_id: A string representing the client id of a client machine.

  Returns:
    A ClientMachine model with a matching client id or None.
  """
  query = db.Query(ClientMachine)
  query.filter('client_id =', instance_id)
  return query.get()


def SetMachineStatus(instance_id, status):
  """Set the machine with the given instance id to the given status.

  Args:
    instance_id: A string representing the client id of a the ClientMachine
      model to touch.
    status: An integer representing an enum.MACHINE_STATUS value.
  """
  client = GetClientMachineFromInstanceId(instance_id)
  if not client:
    logging.error(
        'Could not find the ClientMachine model for instance id "%s".',
        instance_id)
    return
  client.status = status
  client.put()


def IncrementRetryCount(instance_id):
  """Increment the retry count of the machine with the given instance id.

  Args:
    instance_id: A string representing the client id of a the ClientMachine
      model to touch.
  """
  client = GetClientMachineFromInstanceId(instance_id)
  if not client:
    logging.error(
        'Could not find the ClientMachine model for instance id "%s".',
        instance_id)
    return
  client.retry_count += 1
  client.put()
