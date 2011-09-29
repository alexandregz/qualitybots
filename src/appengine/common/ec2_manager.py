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
from third_party import boto

from google.appengine.api import memcache
from google.appengine.ext import db

from common import enum
from models import aws_account_details


AWS_ACCOUNT_MEMCACHE_KEY = 'aws_account'
AMIS_MEMCACHE_KEY = 'bots_amis'
DEFAULT_AMI_COUNT = 1
MICRO_INSTANCE = 't1.micro'
SMALL_INSTANCE = 'm1.small'
LARGE_INSTANCE = 'm1.large'
HIGH_CPU_MEDIUM = 'c1.medium'
HIGH_CPU_EXTRA_LARGE = 'c1.xlarge'
BOTS_KEY_PAIR_NAME = 'bots'
WIN_SECURITY_GROUPS = ['win-group1']

# A map of enum.OS values to EC2 platform strings.
OS_MAP = {
    enum.OS.WINDOWS: 'windows',
    enum.OS.LINUX: 'linux',
    enum.OS.MAC: 'INVALID PLATFORM',
    enum.OS.CHROMEOS: 'INVALID PLATFORM'}


class EC2ConnectionError(Exception):
  pass


class EC2ConfigurationError(Exception):
  pass


def _GetAttr(obj, attr, default_value):
  """Gets a specified attribute of an object (if exist).

  Args:
    obj: Object.
    attr: Attribute name (string).
    default_value: Default value to return if object does not have attribute
      specified.

  Returns:
    Specified attribute value if exists, else default value.
  """
  if hasattr(obj, attr):
    return obj.__getattribute__(attr)
  else:
    return default_value


class BotoEC2DataObject(object):
  """Abstract super class for various BotoEC2 data objects."""

  def __init__(self):
    """Do not call - __init__ method of uninstantiable interface class."""
    raise NotImplementedError('uninstantiable abstract superclass')

  @staticmethod
  def Encode(obj):
    """Custom encoder for BotoEC2DataObject.

    To understand JSON Serialization and encoding stuff,
    refer: http://diveintopython3.org/serializing.html.

    Args:
      obj: Object to encode.

    Returns:
      Encoded object.

    Raises:
      TypeError: If object is of not supported type.
    """
    if not isinstance(obj, BotoEC2DataObject):
      raise TypeError('%r is not JSON serializable' %(obj))
    return obj.__dict__


class BotsAMI(BotoEC2DataObject):
  """Class about Bots AMI (Amazon Machine Image).

  Attributes:
    id: AMI Id (string).
    name: AMI Name (string).
    platform: AMI Platform (string).
    description: AMI Description (string).
    architecture: AMI architecture (e.g. u'i386') (string).
    region: AMI region name (string).
  """

  def __init__(self, image):
    """Inits BotsAMI class.

    Args:
      image: EC2 Image.
    """
    # Disable '__init__ of base class not called' lint error.
    # pylint: disable-msg=W0231
    self.id = image.id
    self.name = image.name
    self.platform = image.platform
    self.description = image.description
    self.architecture = image.architecture
    self.region = image.region.name


class BotsInstance(BotoEC2DataObject):
  """Class about Bots Instance (AWS EC2 Instance).

  Attributes:
    inst_id: Instance Id (string).
    inst_platform: Instance platform (e.g. windows) (string).
    inst_state: Instance State (string).
    inst_previous_state: Instance previous state (string).
    inst_architecture: Instance Architecture (e.g. u'i386') (string).
    inst_message: Instance Message (string).
    inst_public_dns_name: Instance public DNS name (string).
    inst_private_ip_address: Instance private ip address (string).
    inst_region: Instance region name (e.g. 'us-east-1'.) (string).
    inst_key_name: Instance Keypair Name (e.g. bots) (string).
    inst_image_id: Instance Image ID (string).
    inst_reason: Instance Reason (string).
    inst_launch_time: Instance Launch Time (e.g. u'2011-08-16T19:01:48.000Z')
      (string).
  """

  def __init__(self, inst):
    """Inits BotsInstance class.

    Args:
      inst: Boto EC2 Instance.
    """
    # Disable '__init__ of base class not called' lint error.
    # pylint: disable-msg=W0231
    logging.info(inst)
    self.inst_id = inst.id
    self.inst_platform = _GetAttr(inst, 'platform', None)
    self.inst_state = _GetAttr(inst, 'state', None)
    self.inst_previous_state = _GetAttr(inst, 'previous_state', None)
    self.inst_architecture = _GetAttr(inst, 'architecture', None)
    self.inst_public_dns_name = _GetAttr(inst, 'public_dns_name', None)
    self.inst_private_ip_address = _GetAttr(inst, 'private_ip_address', None)
    self.inst_region = _GetAttr(inst, 'region.name', None)
    self.inst_key_name = _GetAttr(inst, 'key_name', None)
    self.inst_image_id = _GetAttr(inst, 'image_id', None)
    self.inst_launch_time = _GetAttr(inst, 'launch_time', None)


class EC2Manager(object):
  """Class to manage EC2 instances and AMI (images).

  Attributes:
    aws_account: AWS Account Object.
    connection_obj: EC2 Connection Object.
    bots_amis: List of EC2 Images (AMI).
  """

  def __init__(self):
    self.aws_account = None
    self.connection_obj = None
    self.bots_amis = None

  def _InitEC2Connection(self):
    """Initializes EC2 connection and creates EC2 connection object.

    Raises:
      EC2ConnectionError: EC2 connection error.
      EC2ConfigurationError: The AWS credentials could not be loaded.
    """
    if not self.aws_account:
      self.aws_account = memcache.get(AWS_ACCOUNT_MEMCACHE_KEY)
      if not self.aws_account:
        q = aws_account_details.AwsAccountDetails.all()
        self.aws_account = q.get()

        if not self.aws_account:
          raise EC2ConfigurationError(
              'Could not load the AWS credentials from the datastore.')

        memcache.set(AWS_ACCOUNT_MEMCACHE_KEY, self.aws_account)
    self.connection_obj = boto.connect_ec2(
        self.aws_account.aws_access_key_id,
        self.aws_account.aws_secret_access_key)
    if not self.connection_obj:
      raise EC2ConnectionError('Could not get EC2 Connection Object.')

  def ConvertToBotsInstances(self, ec2_instances):
    """This method convert ec2_instances list into bots_instances list.

    Args:
      ec2_instances: EC2 Instance List.

    Raises:
      TypeError: If required parameter is missing.

    Returns:
      List of BotsInstances created from supplied ec2_instances.
    """
    if not ec2_instances or not isinstance(ec2_instances, list):
      raise TypeError(
          'Required parameter instances is either missing or of wrong type')
    logging.info(ec2_instances)
    return [BotsInstance(inst) for inst in ec2_instances]

  def GetImages(self):
    """Returns list of bots ami instances.

    BotsAMI object has information about AMI stored under bots account.

    Returns:
      List of BotsAMI objects.
    """
    if not self.bots_amis:
      self.bots_amis = memcache.get(AMIS_MEMCACHE_KEY)
      # Let's try to retrieve the image (AMI)info from AWS.
      if not self.bots_amis:
        self._InitEC2Connection()
        images = self.connection_obj.get_all_images(
            owners=[self.aws_account.aws_account_number])
        self.bots_amis = []
        for image in images:
          bots_ami = BotsAMI(image)
          self.bots_amis.append(bots_ami)
        memcache.set(AMIS_MEMCACHE_KEY, self.bots_amis, 3600)
    return self.bots_amis

  def StartAMI(self, ami_id, count=DEFAULT_AMI_COUNT,
               key_name=BOTS_KEY_PAIR_NAME, instance_type=MICRO_INSTANCE,
               user_data=''):
    """Handler to start EC2 Instance/s using AMI ID.

    User data passed while starting an AMI becomes part of instances and can be
    accessed from within instance using http://169.254.169.254/latest/user-data.
    If multiple instances are started (count > 1) then each instance will get
    same user_data.

    Args:
      ami_id: AMI ID (string).
      count: Number of instances to start (default: 1) (string).
      key_name: AWS KeyPair Name (default: 'bots') (string).
      instance_type: AWS Instance type (default: 't1.micro') (string).
      user_data: User data to pass to instance (string).

    Returns:
      List of BotsInstance objects.
    """
    count = int(count)
    self._InitEC2Connection()
    logging.info(
        'image_id: %s, count: %s, key_name: %s, security_groups: %s,'
        'instance_type: %s, user_data: %s', ami_id, count, BOTS_KEY_PAIR_NAME,
        WIN_SECURITY_GROUPS, instance_type, user_data)
    reservation = self.connection_obj.run_instances(
        image_id=ami_id, min_count=count, max_count=count,
        key_name=key_name, security_groups=WIN_SECURITY_GROUPS,
        user_data=user_data, addressing_type=None, instance_type=instance_type)
    logging.info(reservation)
    return self.ConvertToBotsInstances(reservation.instances)

  def StartAmiWithOs(
      self, os, count=DEFAULT_AMI_COUNT, key_name=BOTS_KEY_PAIR_NAME,
      instance_type=MICRO_INSTANCE, user_data=''):
    """Handler to start EC2 Instances for a specified operating system.

    User data passed while starting an AMI becomes part of instances and can be
    accessed from within instance using http://169.254.169.254/latest/user-data.
    If multiple instances are started (count > 1) then each instance will get
    same user_data.

    Args:
      os: An enum.OS value indicating what operating system to start (integer).
      count: Number of instances to start (default: 1) (string).
      key_name: AWS KeyPair Name (default: 'bots') (string).
      instance_type: AWS Instance type (default: 't1.micro') (string).
      user_data: User data to pass to instance (string).

    Returns:
      List of BotsInstance objects.

    Raises:
      EC2ConfigurationError: Could not find an AMI matching the given OS.
    """
    count = int(count)
    self._InitEC2Connection()
    logging.info(
        'os: %d, count: %d, key_name: %s, security_groups: %s,'
        'instance_type: %s, user_data: %s', os, count, BOTS_KEY_PAIR_NAME,
        WIN_SECURITY_GROUPS, instance_type, user_data)
    ami_images = self.GetImages()
    # Filter out the images that don't match the os that we want.
    ami_images = [image for image in ami_images if image.platform == OS_MAP[os]]
    if not ami_images:
      raise EC2ConfigurationError(
          'Could not find an AMI matching the given OS.')

    # Use the first image that fits the OS criteria.
    ami_id = ami_images[0].id

    return self.StartAMI(ami_id, count=count, key_name=key_name,
                         instance_type=instance_type, user_data=user_data)

  def GetInstances(self, instance_ids=None):
    """Gets the instances.

    This method can be primarily used for getting information about the instance
    or instances. Information returned is stored in BotsInstance object and list
    of such objects is returned.

    Args:
      instance_ids: EC2 Instance ID (str) or Instance IDs (str list)
        (default:None).

    Returns:
      List of requested bots instances.
    """
    logging.info(instance_ids)
    self._InitEC2Connection()
    if isinstance(instance_ids, str):
      instance_ids = [instance_ids]
    reservation = self.connection_obj.get_all_instances(instance_ids)
    bots_instances = []
    for r in reservation:
      bots_instances.extend(self.ConvertToBotsInstances(r.instances))
    return bots_instances

  def StartInstances(self, instance_ids):
    """Start the instances.

    Use this method for starting the instance or instances.
    Information returned is stored in BotsInstance object and list
    of such objects is returned.

    Args:
      instance_ids: EC2 Instance ID (str) or Instance IDs (str list)
        (default:None).

    Returns:
      List of started bots instances.
    """
    logging.info(instance_ids)
    self._InitEC2Connection()
    if isinstance(instance_ids, str):
      instance_ids = [instance_ids]
    instances = self.connection_obj.start_instances(instance_ids)
    logging.info(instances)
    return self.ConvertToBotsInstances(instances)

  def StopInstances(self, instance_ids):
    """Stops the instances.

    This method can be primarily used for stopping the instance or instances.
    Information returned is stored in BotsInstance object and list
    of such objects is returned.

    Args:
      instance_ids: EC2 Instance ID (str) or Instance IDs (str list)
        (default:None).

    Returns:
      List of stopped bots instances.
    """
    logging.info(instance_ids)
    self._InitEC2Connection()
    if isinstance(instance_ids, str):
      instance_ids = [instance_ids]
    instances = self.connection_obj.stop_instances(instance_ids)
    logging.info(instances)
    return self.ConvertToBotsInstances(instances)

  def StopAllInstances(self):
    """Stops all the running instances.

    This method can be primarily used for stopping all the instances.

    Returns:
      List of stopped bots instances.
    """
    self._InitEC2Connection()
    bots_instances = self.GetInstances()
    running_instance_ids = [inst.inst_id for inst in bots_instances
                            if inst.inst_state.lower() == 'running']
    logging.info('Running instances - %s', str(running_instance_ids))
    instances = self.connection_obj.stop_instances(running_instance_ids)
    logging.info(instances)
    return self.ConvertToBotsInstances(instances)

  def RebootInstances(self, instance_ids):
    """Reboots /Restarts the instances.

    This method can be primarily used for restarting the instance or instances.
    Information returned is stored in BotsInstance object and list
    of such objects is returned.

    Args:
      instance_ids: EC2 Instance ID (str) or Instance IDs (str list)
        (default:None).

    Returns:
      Boolean indicating success.
    """
    logging.info(instance_ids)
    self._InitEC2Connection()
    if isinstance(instance_ids, str):
      instance_ids = [instance_ids]
    success = self.connection_obj.reboot_instances(instance_ids)
    logging.info(success)
    return success

  def RebootAllInstances(self):
    """Reboots all the running instances.

    This method can be primarily used for rebooting all the instances.

    Returns:
      Boolean indicating success.
    """
    self._InitEC2Connection()
    bots_instances = self.GetInstances()
    running_instance_ids = [inst.inst_id for inst in bots_instances
                            if inst.inst_state.lower() == 'running']
    logging.info('Running instances - %s', str(running_instance_ids))
    success = self.connection_obj.reboot_instances(running_instance_ids)
    logging.info(success)
    return success

  def TerminateInstances(self, instance_ids):
    """Terminates the instances.

    This method can be primarily used for terminate the instance or instances.
    Information returned is stored in BotsInstance object and list
    of such objects is returned. Terminated instances lose the state forever
    and once instance is terminated, it can never be recovered or restarted.

    Args:
      instance_ids: EC2 Instance ID (str) or Instance IDs (str list)
        (default:None).

    Returns:
      List of terminated bots instances.
    """
    logging.info(instance_ids)
    self._InitEC2Connection()
    if isinstance(instance_ids, str):
      instance_ids = [instance_ids]
    instances = self.connection_obj.terminate_instances(instance_ids)
    logging.info(instances)
    return self.ConvertToBotsInstances(instances)

  def TerminateAllInstances(self, only_running=True):
    """Terminates all the instances.

    This method can be primarily used for terminating all the instances or
    terminating all running instances only. Once instance is terminated it
    loses it's state forever. It can never be restarted or recovered.

    Args:
      only_running: Boolean flag indicating whether to terminate only running
        instances or all (Default: True).

    Returns:
      List of terminated bots instances.
    """
    self._InitEC2Connection()
    bots_instances = self.GetInstances()
    all_instance_ids = []
    for bots_instance in bots_instances:
      if only_running and bots_instance.inst_state.lower() == 'running':
        all_instance_ids.append(bots_instance.inst_id)
      else:
        all_instance_ids.append(bots_instance.inst_id)
    logging.info('Instances to terminate - %s', str(all_instance_ids))
    instances = self.connection_obj.terminate_instances(all_instance_ids)
    logging.info(instances)
    return self.ConvertToBotsInstances(instances)
