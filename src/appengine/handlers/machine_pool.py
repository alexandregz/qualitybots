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


"""Handler for assisting with the machine install process."""



# Disable 'Import not at top of file' lint error.
# pylint: disable-msg=C6204, C6205, W0611


import logging

from django.utils import simplejson

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import deferred
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from common import ec2_manager
from common import enum
from handlers import base
from handlers import launch_tasks
from models import client_machine


INIT_START = '/init/start'
INSTALL_FAILED = '/init/install_failed'
INSTALL_SUCEEDED = '/init/install_succeeded'


class InitializationStart(base.BaseHandler):
  """Handler to acknowledge a machine starting initialization."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Updates the status of a machine starting initialization."""
    instance_id = self.GetRequiredParameter('instance_id')
    instance = db.GqlQuery('SELECT * FROM ClientMachine WHERE client_id = :1',
                           instance_id).get()

    if not instance:
      logging.error('The given instance id "%s" does not match any machines.',
                    instance_id)
      self.error(500)
      return

    if instance.status != enum.MACHINE_STATUS.PROVISIONED:
      logging.error('The machine with instance id "%s" was in an unexpected '
                    'state for initialization: "%s"', instance_id,
                    enum.MACHINE_STATUS.LookupKey(instance.status))
    instance.status = enum.MACHINE_STATUS.INITIALIZING

    instance.put()

    self.response.out.write('Initialization acknowledged.')


class InstallFailed(base.BaseHandler):
  """Handler to deal with a machine that fails to properly setup and install."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Updates the status of a machine that failed with initialization."""
    instance_id = self.GetRequiredParameter('instance_id')
    log = self.GetOptionalParameter('log', None)

    old_instance = db.GqlQuery(
        'SELECT * FROM ClientMachine WHERE client_id = :1',
        instance_id).get()

    if not old_instance:
      logging.error('The given instance id "%s" does not match any machines.',
                    instance_id)
      self.error(500)
      return

    if old_instance.status != enum.MACHINE_STATUS.INITIALIZING:
      logging.error('The machine with instance id "%s" was in an unexpected '
                    'state for initialization: "%s"', instance_id,
                    enum.MACHINE_STATUS.LookupKey(old_instance.status))
    old_instance.status = enum.MACHINE_STATUS.FAILED

    if log:
      old_instance.initialization_log = log
    old_instance.put()

    if old_instance.retry_count >= client_machine.MAX_RETRIES:
      logging.error('Reached the maximum number of retries for starting this '
                    'machine: %s.', str(old_instance.key()))
      logging.info('Terminating the failed instance.')
      deferred.defer(launch_tasks.TerminateFailedMachine, instance_id,
                     _countdown=launch_tasks.DEFAULT_COUNTDOWN,
                     _queue=launch_tasks.DEFAULT_QUEUE)
      self.error(500)
      return

    logging.info('Rebooting the failed instance.')
    deferred.defer(launch_tasks.RebootMachine, instance_id,
                   _countdown=launch_tasks.DEFAULT_COUNTDOWN,
                   _queue=launch_tasks.DEFAULT_QUEUE)

    self.response.out.write('Initialization failure acknowledged.')


class InstallSucceeded(base.BaseHandler):
  """Handler to deal with a machine that installs successfully."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Updates the status of a machine that succeeded with initialization."""
    instance_id = self.GetRequiredParameter('instance_id')
    log = self.GetOptionalParameter('log', None)

    instance = db.GqlQuery('SELECT * FROM ClientMachine WHERE client_id = :1',
                           instance_id).get()

    if not instance:
      logging.error('The given instance id "%s" does not match any machines.',
                    instance_id)
      self.error(500)
      return

    if instance.status != enum.MACHINE_STATUS.INITIALIZING:
      logging.error('The machine with instance id "%s" was in an unexpected '
                    'state for initialization: "%s"', instance_id,
                    enum.MACHINE_STATUS.LookupKey(instance.status))
    instance.status = enum.MACHINE_STATUS.RUNNING

    if log:
      instance.initialization_log = log
    instance.put()

    self.response.out.write('Initialization success acknowledged.')


application = webapp.WSGIApplication(
    [(INIT_START, InitializationStart),
     (INSTALL_FAILED, InstallFailed),
     (INSTALL_SUCEEDED, InstallSucceeded)],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
