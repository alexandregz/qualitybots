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


"""Test distributor that handles creating tests and distributing them."""





import datetime
import logging
import math
import re
import urllib
import uuid

from django.utils import simplejson

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import deferred
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from common import chrome_channel_util
from common import ec2_manager
from common import enum
from common import firefox_channel_util
from handlers import base
from handlers import launch_tasks
from models import client_machine
from models import run_log
from models import url


START_RUN_URL = '/distributor/start_run'
ACCEPT_WORK_ITEM_URL = '/distributor/accept_work_item'
FINISH_WORK_ITEM_URL = '/distributor/finish_work_item'
CHECK_MACHINES_URL = '/distributor/check_machines'
UPLOAD_CLIENT_LOG_URL = '/distributor/upload_client_log'
EXPIRE_TEST_RUN_URL = '/distributor/expire_test_run'

DEFAULT_MIN_MACHINE_COUNT = 2
WORK_ITEM_SUCCESS = 'success'
WORK_ITEM_FAILURE = 'failed'
WORK_ITEM_UPLOAD_ERROR = 'upload_error'
WORK_ITEM_TIMEOUT_ERROR = 'timeout_error'

MAX_HOURS = 5 * 24
MINUTES_PER_URL = 3.0
MAX_UNRESPONSIVE_MINUTES = 20

MILLISECONDS_PER_SECOND = 1000
MICROSECONDS_PER_MILLISECOND = 1000
MILLISECONDS_PER_DAY = 24 * 60 * 60 * MILLISECONDS_PER_SECOND

BROWSERS = [enum.BROWSER.CHROME, enum.BROWSER.FIREFOX]
# Browser versions are ordered from oldest to newest.
BROWSER_VERSIONS_MAP = {
    enum.BROWSER.CHROME: [
        enum.BROWSERCHANNEL.LookupKey(enum.BROWSERCHANNEL.STABLE).lower(),
        enum.BROWSERCHANNEL.LookupKey(enum.BROWSERCHANNEL.BETA).lower(),
        enum.BROWSERCHANNEL.LookupKey(enum.BROWSERCHANNEL.DEV).lower()],
    enum.BROWSER.FIREFOX: [
        enum.BROWSERCHANNEL.LookupKey(enum.BROWSERCHANNEL.STABLE).lower(),
        enum.BROWSERCHANNEL.LookupKey(enum.BROWSERCHANNEL.AURORA).lower()]}
OPERATING_SYSTEMS = [enum.OS.WINDOWS]

CLIENT_INFO_JSON = ('{"height": "512", "Project": "AppCompat", '
                    '"width": "1024", "useCachedPage": "false"}')


class StartTestRun(base.BaseHandler):
  """Handler for starting a test run."""

  @staticmethod
  def CalculateNeededMachines(num_urls, max_hours=MAX_HOURS):
    """Calculate the number of machines that will be needed to process the Urls.

    This function takes into account the number of urls that need to be
    processed and  calculates the number of machines needed to finish in a
    reasonable time. Min machine count is DEFAULT_MIN_MACHINE_COUNT.

    Args:
      num_urls: An integer representing the number of urls to be processed.
      max_hours: An optional parameter specifying the maximum number of hours
        the urls should be processed in.

    Returns:
      An integer representing the total number of machines needed for each
      configuration. So, a return value of one would indicate that one machine
      of each configuration was needed.
    """
    # Calculate the total machine-minutes that are needed for the urls.
    # machine*minutes = urls * ((minutes/url)/machine)
    machine_minutes = num_urls * MINUTES_PER_URL

    # Calculate the total number of minutes that we have for the run.
    # minutes = hours * (minutes/hour)
    max_minutes = max_hours * 60

    # Calculate the number of machines needed given the total machine-minutes
    # required and the maximum minute limit.
    # machines = machine*minutes / minutes
    total_machines = float(machine_minutes) / max_minutes

    # Round the number of machines up because any fractional machine requirement
    # requires a full extra machine.
    return max(int(math.ceil(total_machines)), DEFAULT_MIN_MACHINE_COUNT)

  @staticmethod
  def _CreateClientInfoString(client_info, ref_browser, ref_browser_channel):
    """Create a client info string for the extension to use.

    Args:
      client_info: A string representation of a JavaScript dictionary.
      ref_browser: A string representing the reference browser version.
      ref_browser_channel: A string representing the channel of the reference
        browser.

    Returns:
      A string of the client info with the reference browser added in.
    """
    # TODO(user): Remove the "Chrome" default once more browsers are supported.
    return (client_info[:1] +
            ('"refBrowser": "Chrome/%s", ' % ref_browser) +
            ('"refBrowserChannel": "%s", ' % ref_browser_channel) +
            client_info[1:])

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Start a test run based on the current stored Urls."""
    # Get the current user
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return

    # Figure out the total number of URLs for this run.
    logging.info('Getting the total URL count.')
    query = url.Url.all()
    # TODO(user): Add a global counter for the Url model to avoid count().
    num_urls = query.count()
    logging.info('This run will have %d urls.', num_urls)

    # Create a unique token per test run based on a random uuid.
    token = str(uuid.uuid4())
    creation_time = datetime.datetime.now()

    # TODO(user): Convert this code to loop through all browsers and
    # operating systems and build a list of configurtions based on supported
    # values rather than a complete combinatoric approach.
    operating_systems = OPERATING_SYSTEMS
    browsers = BROWSERS

    chrome_util = chrome_channel_util.ChromeChannelUtil()
    firefox_util = firefox_channel_util.ChromeChannelUtil()

    # Create a list of configurations based on os, browser, and channel that
    # includes version and installer url.
    configurations = []
    for system in operating_system:
      for browser in browsers:
        for channel in BROWSER_VERSIONS_MAP[browser]
          configuration = {'os': system, 'browser': browser,
                           'channel': channel}
          system_name = enum.OS.LookupKey(system).lower()

          if browser == enum.BROWSER.CHROME:
            configuration['version'] = chrome_util.GetVersionForChannel(
                system_name, channel)
            configuration['installer_url'] = chrome_util.GetUrlForChannel(
                system_name, channel)

          elif browser == enum.BROWSER.FIREFOX:
            configuration['version'] = firefox_util.GetVersionForChannel(
                system_name, channel)
            configuration['installer_url'] = firefox_util.GetUrlForChannel(
                system, channel)
          else
            logging.error('Unknown system (%s), browser (%s), channel (%s) '
                          'configuration ... skipping.', system, browser,
                          channel)
            continue

          configurations.append(configuration)

    ref_os = enum.OS.LookupKey(operating_system[0]).lower()
    ref_browser = browsers[0]
    ref_channel = BROWSER_VERSION_MAP[ref_browser][0]
    ref_configuration = None
    for configuration in configurations:
      if (configuration['os'] == ref_os and
          configuration['browser'] == ref_browser and
          configuration['channel'] = ref_channel):
        ref_configuration = configuration
        break

    if ref_configuration is None:
      logging.error('Unable to locate reference browser')
      self.response.out.write('Test run failed.')
      return

    # Add the reference browser to the config params
    client_info = StartTestRun._CreateClientInfoString(
        CLIENT_INFO_JSON, ref_configuration['version'],
        ref_configuration['channel'])

    num_instances = StartTestRun.CalculateNeededMachines(num_urls)

    # Push tasks onto the queue to create the RunLog entries.
    limit = 200
    offset = 0
    while offset < num_urls:
      deferred.defer(launch_tasks.CreateRunLogEntries, offset, limit,
                     token, client_info, creation_time, configurations, user,
                     _countdown=launch_tasks.DEFAULT_COUNTDOWN,
                     _queue=launch_tasks.DEFAULT_QUEUE)
      offset += limit

    # Push tasks onto the queue to create the necessary machines.
    for configuration in configurations:
      deferred.defer(launch_tasks.CreateMachines, num_instances,
                     token, configuration['os'], configuration['browser'],
                     configuration['channel', configuration['installer_url'],
                     _countdown=launch_tasks.DEFAULT_COUNTDOWN,
                     _queue=launch_tasks.DEFAULT_QUEUE)

    self.response.out.write('Test run started.')


class AcceptNextWorkItem(base.BaseHandler):
  """Handler for accepting a work item from the run log queue."""

  @staticmethod
  def _ParseBrowserVersion(useragent):
    """Parse the browser version string from the given useragent string.

    Args:
      useragent: A string representing the browser's user agent.

    Returns:
      A string that represents the browser version for the given useragent
      string. If the useragent doesn't represent a valid browser, None is
      returned.
    """
    version = re.search('Chrome/[^ ]*', useragent)

    if version:
      return version.group()[7:]
    else:
      return None

  @staticmethod
  def _GetTestDataJson(log):
    """Return the JSON representation of a run log to be used by the extension.

    Args:
      log: A run_log.RunLog object to represent as JSON.

    Returns:
      A JSON string representing the given RunLog.
    """
    return simplejson.dumps({
        'data_str': 'ContentMap["URL"]="%s"' % log.url,
        'start_time': log.creation_time.isoformat().replace('T', ' '),
        'config': (log.client_info[:1] +
                   ('"Tokens": "%s", ' % log.token) +
                   log.client_info[1:]),
        'id': 0,
        'key': str(log.key())})

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Retrieve the next queued work item from the run log queue.

    The next work item is determined based on the browser version and token.

    URL Params:
      tokens: A string that uniquely identifies an instance of a test run.
      instance_id: A string that uniquely identifies the machine making the
        request.
      useragent: A string representing the browser useragent string.
    """
    # Get the parameters from the request
    token = self.GetRequiredParameter('tokens')
    instance_id = self.GetRequiredParameter('instance_id')
    useragent = urllib.unquote(self.GetRequiredParameter('useragent'))

    # Log the parameters
    logging.info('\n'.join(['token: %s', 'instance_id: %s', 'useragent: %s']),
                 token, instance_id, useragent)

    browser_version = AcceptNextWorkItem._ParseBrowserVersion(useragent)
    if not browser_version:
      logging.error('Could not parse the given useragent.')
      self.response.out.write('null')
      return

    log = db.GqlQuery(
        'SELECT * FROM RunLog WHERE token = :1 AND browser_version = :2 AND '
        'status = :3 ORDER BY creation_time ASC, priority DESC LIMIT 1',
        token, browser_version, enum.CASE_STATUS.QUEUED).get()

    # Write out a null response if no log exists for the given criteria
    if not log:
      self.response.out.write('null')
      logging.info('No more test cases remain, shutting down the machine "%s".',
                   instance_id)
      deferred.defer(launch_tasks.TerminateFinishedMachine, instance_id,
                     _countdown=launch_tasks.DEFAULT_COUNTDOWN,
                     _queue=launch_tasks.DEFAULT_QUEUE)
      return

    self.response.out.write(AcceptNextWorkItem._GetTestDataJson(log))

    # Update the work item status
    log.status = enum.CASE_STATUS.IN_PROGRESS
    log.client_id = instance_id
    log.start_time = datetime.datetime.now()
    log.put()

    # Update the machine status
    client_machine.SetMachineStatus(instance_id, enum.MACHINE_STATUS.RUNNING)


class FinishWorkItem(base.BaseHandler):
  """Handler for finishing a work item in the run log queue."""

  @staticmethod
  def _HandleFailureCase(log, failure_state, failure_message):
    """Handle a failure case by logging the failure and updating the RunLog.

    Args:
      log: A RunLog object to update.
      failure_state: An integer representing an enum.CASE_STATUS enum to set the
        log state to on final failure.
      failure_message: A string indicating the failure type message to log.
    """
    if log.retry_count > 0:
      log.retry_count -= 1
      log.status = enum.CASE_STATUS.QUEUED
      logging.info('Work item re-queued due to %s.', failure_message)
    else:
      log.status = failure_state
      logging.info('Work item finished due to failure cause "%s".',
                   failure_message)

  @staticmethod
  def _TimedeltaToMilliseconds(delta):
    """Convert the given timedelta to milliseconds.

    Args:
      delta: A datetime.timedelta object to convert to milliseconds.

    Returns:
      An integer representing the number of milliseconds in the timedelta.
    """
    return (delta.days * MILLISECONDS_PER_DAY +
            delta.seconds * MILLISECONDS_PER_SECOND +
            delta.microseconds / MICROSECONDS_PER_MILLISECOND)

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Change the state of a run log entry from IN_PROGRESS to FINISHED.

    URL Params:
      key: A string that represents the run log entry key in the datastore.
      instance_id: A string that uniquely identifies the machine making the
        request.
      result: A string result for the finished work item.

    Raises:
      base.InvalidParameterValueError: The given key does not correspond with
        an existing run log in the datastore.
    """
    # Get the parameters from the request
    key = self.GetRequiredParameter('key')
    instance_id = self.GetRequiredParameter('instance_id')
    result = self.GetOptionalParameter('result',
                                       default_value=WORK_ITEM_SUCCESS)

    # Log the parameters
    logging.info('\n'.join(['key: %s', 'instance_id: %s', 'result: %s']),
                 key, instance_id, result)

    log = db.get(key)
    if not log:
      raise base.InvalidParameterValueError('key', key)

    logging.info('Current log status: "%d".', log.status)

    if log.status != enum.CASE_STATUS.IN_PROGRESS:
      # The run log has an invalid run status for finishing, just return
      logging.error('The test case "%s" has an invalid status for finishing.',
                    key)
      return

    if result == WORK_ITEM_SUCCESS:
      # Update the work item status
      log.status = enum.CASE_STATUS.FINISHED
      log.end_time = datetime.datetime.now()
      if log.start_time:
        duration = log.end_time - log.start_time
        log.duration = FinishWorkItem._TimedeltaToMilliseconds(duration)
      logging.info('Work item finished successfully.')
    elif result == WORK_ITEM_FAILURE:
      FinishWorkItem._HandleFailureCase(log, enum.CASE_STATUS.UNKNOWN_ERROR,
                                        'failure')
    elif result == WORK_ITEM_UPLOAD_ERROR:
      FinishWorkItem._HandleFailureCase(log, enum.CASE_STATUS.UPLOAD_ERROR,
                                        'upload error')
    elif result == WORK_ITEM_TIMEOUT_ERROR:
      FinishWorkItem._HandleFailureCase(log, enum.CASE_STATUS.TIMEOUT_ERROR,
                                        'timeout error')

    log.put()

    # Update the machine status
    client_machine.SetMachineStatus(instance_id, enum.MACHINE_STATUS.RUNNING)


class CheckMachines(base.BaseHandler):
  """Handler for checking the machine statuses on a regular basis."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Check the status of the machines and eliminate unresponsive machines."""
    # Get the list of client machines (filtered by RUNNING status or earlier)
    query = db.Query(client_machine.ClientMachine)
    query.filter('status <=', enum.MACHINE_STATUS.RUNNING)

    for machine in query:
      # Check if we've received a response from the machine recently.
      if (datetime.datetime.now() - machine.updated_time >
          datetime.timedelta(seconds=60*MAX_UNRESPONSIVE_MINUTES)):
        # Re-Queue work items checked out by this machine.
        logging.info('Requeueing work items assigned to "%s".',
                     machine.client_id)
        deferred.defer(launch_tasks.RequeueWorkItems, machine.client_id,
                       _countdown=launch_tasks.DEFAULT_COUNTDOWN,
                       _queue=launch_tasks.DEFAULT_QUEUE)

        # Reboot the machine if we have more retries available.
        if machine.retry_count < client_machine.MAX_RETRIES:
          deferred.defer(launch_tasks.RebootMachine, machine.client_id,
                         _countdown=launch_tasks.DEFAULT_COUNTDOWN,
                         _queue=launch_tasks.DEFAULT_QUEUE)
        else:
          # Terminate the old machine.
          logging.info('Terminating failed machine "%s".', machine.client_id)
          deferred.defer(launch_tasks.TerminateFailedMachine, machine.client_id,
                         _countdown=launch_tasks.DEFAULT_COUNTDOWN,
                         _queue=launch_tasks.DEFAULT_QUEUE)


class UploadClientLog(base.BaseHandler):
  """Handler to store the uploaded client log.

  URL Params:
    instance_id: A string that uniquely identifies the machine making the
      request.
    log: A string representing the client log.
  """

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Updates the status of a machine that failed with initialization."""
    instance_id = self.GetRequiredParameter('instance_id')
    log = self.GetRequiredParameter('log')

    instance = db.GqlQuery(
        'SELECT * FROM ClientMachine WHERE client_id = :1',
        instance_id).get()

    if not instance:
      logging.error('The given instance id "%s" does not match any machines.',
                    instance_id)
      self.error(500)
      return

    instance.run_log = log
    instance.put()


class ExpireTestRun(base.BaseHandler):
  """Handler for expiring a test run."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Expire all the machines and RunLogs involved in a specified test run.

    URL Params:
      token: A string that uniquely identifies an instance of a test run.
    """
    # Get the parameters from the request
    token = self.GetRequiredParameter('token')

    # Get the list of ClientMachines (filtered by the token).
    query = db.Query(client_machine.ClientMachine)
    query.filter('token =', token)

    for machine in query:
      # Terminate the machine as expired if it hasn't been terminated.
      if machine.status <= enum.MACHINE_STATUS.RUNNING:
        deferred.defer(launch_tasks.TerminateExpiredMachine,
                       machine.client_id,
                       _countdown=launch_tasks.DEFAULT_COUNTDOWN,
                       _queue=launch_tasks.DEFAULT_QUEUE)

    # TODO(user): Process the RunLogs in a task queue to avoid timeouts.
    # Get the list of RunLogs (filtered by the token).
    query = db.Query(run_log.RunLog)
    query.filter('token =', token)

    logs = []
    for log in query:
      # Update the log status if it hasn't finished processing.
      if (log.status == enum.CASE_STATUS.QUEUED or
          log.status == enum.CASE_STATUS.IN_PROGRESS):
        # Mark the RunLog as expired.
        log.status = enum.CASE_STATUS.EXPIRED
        logs.append(log)

    db.put(logs)

    self.response.out.write('Test run "%s" expired.' % token)


application = webapp.WSGIApplication(
    [(START_RUN_URL, StartTestRun),
     (ACCEPT_WORK_ITEM_URL, AcceptNextWorkItem),
     (FINISH_WORK_ITEM_URL, FinishWorkItem),
     (CHECK_MACHINES_URL, CheckMachines),
     (UPLOAD_CLIENT_LOG_URL, UploadClientLog),
     (EXPIRE_TEST_RUN_URL, ExpireTestRun)],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
