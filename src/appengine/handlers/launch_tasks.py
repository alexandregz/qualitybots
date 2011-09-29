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


"""Functions to perform launch tasks for use as deferred tasks.

In particular, this module contains functions to create RunLog entries and
launch new machines.
"""




import logging

from common import ec2_manager
from common import enum
from common import gql_util

from google.appengine.ext import db

from models import client_machine
from models import run_log
from models import url

# Disable 'unused import' lint warning.
# pylint: disable-msg=W0611
from models import url_config

import simplejson


# This count is used to fetch amount of url configs associated with a url.
URL_CONFIG_FETCH_COUNT = 1000
DEFAULT_PRIORITY = 0
DEFAULT_RETRY_COUNT = 3
DEFAULT_INSTANCE_SIZE = ec2_manager.HIGH_CPU_MEDIUM

# Default task countdown time for deferred tasks in seconds.
DEFAULT_COUNTDOWN = 30
DEFAULT_QUEUE = 'ec2'

# A boolean to determine whether instances should be terminated or stopped.
TERMINATE_INSTANCES = False

OS_TO_USER_DATA = {enum.OS.WINDOWS: 'win', enum.OS.LINUX: 'linux',
                   enum.OS.MAC: 'mac'}


def CreateRunLogEntries(offset, limit, token, client_info, creation_time,
                        browsers, browser_versions, operating_systems, user):
  """Create RunLog entries for the given parameters and Url selection.

  Args:
    offset: An integer representing the offset into the Url model to start
      fetching from.
    limit: An integer representing the  maximum number of Url models to fetch.
    token: A string representing the token for this run.
    client_info: A string representing client info for this run.
    creation_time: A datetime.datetime object representing the creation time
      for this run.
    browsers: A list of integers that correspond to enum.BROWSER values.
    browser_versions: A list of strings representing browser versions to use.
    operating_systems: A list of integers that correspond to enum.OS values.
    user: A User object representing the user starting the test run.
  """
  logging.info('\n'.join(['offset: %d', 'limit: %d', 'token: %s',
                          'client_info: %s', 'creation_time: %s',
                          'browsers: %s', 'browser_versions: %s',
                          'operating_systems: %s', 'user: %s']),
               offset, limit, token, client_info, creation_time, browsers,
               browser_versions, operating_systems, user)

  # Get the URLs to create RunLog entries.
  query = db.Query(url.Url)
  urls = query.fetch(limit, offset=offset)

  logging.info('Creating the RunLog models.')
  run_logs = []
  for test_url in urls:
    # Let's get url_configs associated with test_url.
    configs = gql_util.FetchEntities(test_url.urlconfigs,
                                     URL_CONFIG_FETCH_COUNT)
    for config in configs:
      for system in operating_systems:
        for browser in browsers:
          for version in browser_versions:
            run_logs.append(run_log.RunLog(
                url=test_url.url, config=config.key(), token=token,
                client_info=client_info, creation_time=creation_time,
                status=enum.CASE_STATUS.QUEUED, user=user, browser=browser,
                browser_version=version, os=system, priority=DEFAULT_PRIORITY,
                retry_count=DEFAULT_RETRY_COUNT))

  logging.info('Num run_logs: %d', len(run_logs))

  db.put(run_logs)
  logging.info('Finished creating the RunLog models.')


def CreateMachines(num_instances, token, os, browser, browser_version,
                   download_info, retries=0):
  """Create and launch EC2 machines for the given parameters.

  Args:
    num_instances: An integer representing the number of instances to spawn
      with the given configuration.
    token: A string representing the token for this run.
    os: An integer that corresponds to an enum.OS value.
    browser: An integer that corresponds to an enum.BROWSER value.
    browser_version: A string representing browser version to use.
      Specifically, this should be the channel for Chrome.
    download_info: A string representing the information necessary for
      calculating the version and browser download url for the given machine.
    retries: An optional paramater specifying the initial retry count for the
      machine.
  """
  logging.info('\n'.join(['num_instances: %d', 'token: %s', 'os: %d',
                          'browser: %d', 'browser_version: %s']),
               num_instances, token, os, browser, browser_version)

  ec2 = ec2_manager.EC2Manager()
  user_data = simplejson.dumps({'channel': browser_version,
                                'os': OS_TO_USER_DATA[os],
                                'token': token,
                                'download_info': download_info})
  logging.info('Spawning EC2 machines.')
  # Note: All exceptions are caught here because the EC2 API could fail after
  # successfully starting a machine. Because this task is rescheduled on
  # failure, we need to make sure we don't keep spawning EC2 machines.
  try:
    bots_instances = ec2.StartAmiWithOs(
        os, count=num_instances, instance_type=DEFAULT_INSTANCE_SIZE,
        user_data=user_data)
  except Exception:
    logging.exception('Something failed when setting up the EC2 instance. '
                      'Stopping setup for this instance.')
    return

  logging.info('Creating the corresponding ClientMachine models.')
  new_instances = []
  for instance in bots_instances:
    new_instances.append(client_machine.ClientMachine(
        vm_service=enum.VM_SERVICE.EC2, os=os, browser=browser,
        browser_version=browser_version, client_id=instance.inst_id,
        status=enum.MACHINE_STATUS.PROVISIONED, retry_count=retries,
        token=token, download_info=download_info))

  db.put(new_instances)
  logging.info('Finished creating the ClientMachine models.')


def RequeueWorkItems(instance_id):
  """Add any work items being processed by the instance id back to the queue.

  Args:
    instance_id: A string that uniquely identifies a machine.
  """
  query = db.Query(run_log.RunLog)
  query.filter('status =', enum.CASE_STATUS.IN_PROGRESS)
  query.filter('client_id =', instance_id)

  logs = []
  for log in query:
    logs.append(log)

    # Ensure that the work item can be retried.
    if log.retry_count > 0:
      log.retry_count -= 1
      log.status = enum.CASE_STATUS.QUEUED
      log.client_id = ''
      log.priority -= 1
    else:
      log.status = enum.CASE_STATUS.UNKNOWN_ERROR

  db.put(logs)


def TerminateMachine(instance_id, status):
  """Terminate the machine associated with the given instance id.

  Args:
    instance_id: A string that uniquely identifies a machine.
    status: An integer representing an enum.MACHINE_STATUS value.
  """
  # Terminate the EC2 instance.
  ec2 = ec2_manager.EC2Manager()

  if TERMINATE_INSTANCES:
    logging.info('Terminating the machine with instance id "%s".', instance_id)
    ec2.TerminateInstances([instance_id])
  else:
    logging.info('Stopping the machine with instance id "%s".', instance_id)
    ec2.StopInstances([instance_id])

  # Update the corresponding client machine model.
  client_machine.SetMachineStatus(instance_id, status)


def TerminateFailedMachine(instance_id):
  """Terminate the machine associated with the given instance id.

  The status of the machine is set FAILED.

  Args:
    instance_id: A string that uniquely identifies a machine.
  """
  TerminateMachine(instance_id, enum.MACHINE_STATUS.FAILED)


def TerminateFinishedMachine(instance_id):
  """Terminate the machine associated with the given instance id.

  The status of the machine is set TERMINATED.

  Args:
    instance_id: A string that uniquely identifies a machine.
  """
  TerminateMachine(instance_id, enum.MACHINE_STATUS.TERMINATED)


def TerminateExpiredMachine(instance_id):
  """Terminate the machine associated with the given instance id.

  The status of the machine is set EXPIRED.

  Args:
    instance_id: A string that uniquely identifies a machine.
  """
  TerminateMachine(instance_id, enum.MACHINE_STATUS.EXPIRED)


def RebootMachine(instance_id):
  """Reboot the machine associated with the given instance id.

  The status of the machine is set to RUNNING.

  Args:
    instance_id: A string that uniquely identifies a machine.
  """
  # Terminate the EC2 instance.
  ec2 = ec2_manager.EC2Manager()

  logging.info('Rebooting machine with instance id "%s".', instance_id)
  ec2.RebootInstances([instance_id])

  # Update the corresponding client machine model.
  client_machine.SetMachineStatus(instance_id, enum.MACHINE_STATUS.RUNNING)
  client_machine.IncrementRetryCount(instance_id)
