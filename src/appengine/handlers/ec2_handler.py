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


"""Handler for managing EC2 Machines.

Handler to manage EC2 Images (start, stop, take snapshot, terminate, getstatus
etc).
"""



import logging

from django.utils import simplejson

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from common import ec2_manager
from handlers import base
from models import aws_account_details


EC2_GET_IMAGES_URL = '/ec2/get_images'
EC2_START_AMI_URL = '/ec2/start_ami'
EC2_STOP_INSTANCES_URL = '/ec2/stop_instances'
EC2_STOP_ALL_INSTANCES_URL = '/ec2/stop_all_instances'
EC2_TERMINATE_INSTANCES_URL = '/ec2/terminate_instances'
EC2_TERMINATE_ALL_INSTANCES_URL = '/ec2/terminate_all_instances'
EC2_START_INSTANCES_URL = '/ec2/start_instances'
EC2_GET_INSTANCES_URL = '/ec2/get_instances'


class GetImages(base.BaseHandler):
  """Handler to get AMI Information associated with bots AWS Account."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def get(self):
    """Returns list of images (BotsAMI) associated with bots aws account."""
    ec2 = ec2_manager.EC2Manager()
    bots_amis = ec2.GetImages()
    self.response.out.write(
        simplejson.dumps([ec2_manager.BotoEC2DataObject.Encode(x)
                          for x in bots_amis]))


class StartAMI(base.BaseHandler):
  """Handler to start EC2 AMI Instance."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Starts given amount of instances of AMI (image)."""
    ami_id = self.GetRequiredParameter('ami_id')
    count = self.GetOptionalParameter('count', 1)
    key_name = self.GetOptionalParameter('key_name',
                                         ec2_manager.BOTS_KEY_PAIR_NAME)
    instance_type = self.GetOptionalParameter('instance_type',
                                              ec2_manager.MICRO_INSTANCE)
    user_data = self.GetOptionalParameter('user_data', None)
    if not ami_id:
      logging.error('Missing AMI ID.')
      self.response.out.write('Missing AMI ID.')
    ec2 = ec2_manager.EC2Manager()
    bots_instances = ec2.StartAMI(ami_id, count, key_name, instance_type,
                                  user_data)
    self.response.out.write(
        simplejson.dumps([ec2_manager.BotoEC2DataObject.Encode(x)
                          for x in bots_instances]))


class StopInstances(base.BaseHandler):
  """Handler to stop EC2 Instances."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Stops instances given list of instance ids."""
    instance_ids = simplejson.loads(self.GetRequiredParameter('instance_ids'))
    if not instance_ids:
      logging.error('Missing Instance ID.')
      self.response.out.write('Missing Instance ID.')
    ec2 = ec2_manager.EC2Manager()
    bots_instances = ec2.StopInstances(instance_ids)
    self.response.out.write(
        simplejson.dumps([ec2_manager.BotoEC2DataObject.Encode(x)
                          for x in bots_instances]))


class StopAllInstances(base.BaseHandler):
  """Handler to stop all EC2 Instances."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Stops all running instances."""
    ec2 = ec2_manager.EC2Manager()
    bots_instances = ec2.StopAllInstances()
    self.response.out.write(
        simplejson.dumps([ec2_manager.BotoEC2DataObject.Encode(x)
                          for x in bots_instances]))


class TerminateInstances(base.BaseHandler):
  """Handler to terminate EC2 Instances."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Terminate instances given list of instance ids."""
    instance_ids = simplejson.loads(self.GetRequiredParameter('instance_ids'))
    if not instance_ids:
      logging.error('Missing Instance ID.')
      self.response.out.write('Missing Instance ID.')
    ec2 = ec2_manager.EC2Manager()
    bots_instances = ec2.TerminateInstances(instance_ids)
    self.response.out.write(
        simplejson.dumps([ec2_manager.BotoEC2DataObject.Encode(x)
                          for x in bots_instances]))


class TerminateAllInstances(base.BaseHandler):
  """Handler to terminate all EC2 Instances."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Terminates all instances or all running instances."""
    ec2 = ec2_manager.EC2Manager()
    only_running = self.GetOptionalParameter('only_running', 'true')
    only_running = simplejson.loads(only_running)
    bots_instances = ec2.TerminateAllInstances(only_running)
    self.response.out.write(
        simplejson.dumps([ec2_manager.BotoEC2DataObject.Encode(x)
                          for x in bots_instances]))


class StartInstances(base.BaseHandler):
  """Handler to start EC2 Instances."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Starts instances given list of instance ids."""
    instance_ids = simplejson.loads(self.GetRequiredParameter('instance_ids'))
    if not instance_ids:
      logging.error('Missing Instance ID.')
      self.response.out.write('Missing Instance ID.')
    ec2 = ec2_manager.EC2Manager()
    bots_instances = ec2.StartInstances(instance_ids)
    self.response.out.write(
        simplejson.dumps([ec2_manager.BotoEC2DataObject.Encode(x)
                          for x in bots_instances]))


class GetInstances(base.BaseHandler):
  """Handler to get EC2 Instances."""

  # Disable 'Invalid method name' lint error.
  # pylint: disable-msg=C6409
  def post(self):
    """Gets information about instances given list of instance ids."""
    instance_ids = self.GetOptionalParameter('instance_ids', None)
    if instance_ids:
      instance_ids = simplejson.loads(instance_ids)
    ec2 = ec2_manager.EC2Manager()
    bots_instances = ec2.GetInstances(instance_ids)
    self.response.out.write(
        simplejson.dumps([ec2_manager.BotoEC2DataObject.Encode(x)
                          for x in bots_instances]))

application = webapp.WSGIApplication(
    [(EC2_GET_IMAGES_URL, GetImages),
     (EC2_START_AMI_URL, StartAMI),
     (EC2_STOP_INSTANCES_URL, StopInstances),
     (EC2_STOP_ALL_INSTANCES_URL, StopAllInstances),
     (EC2_TERMINATE_INSTANCES_URL, TerminateInstances),
     (EC2_TERMINATE_ALL_INSTANCES_URL, TerminateAllInstances),
     (EC2_START_INSTANCES_URL, StartInstances),
     (EC2_GET_INSTANCES_URL, GetInstances)],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
