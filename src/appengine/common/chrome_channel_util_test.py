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


"""Tests for chrome_channel_util.

These tests test the common.chrome_channel_util module.
"""



import unittest
import mox

import chrome_channel_util


class ChromeChannelUtilTest(unittest.TestCase):

  OMAHAPROXY_HEADER = (
      'os,channel,current_version,previous_version,current_reldate,'
      'previous_reldate,base_trunk_revision,branch_revision,'
      'base_webkit_revision\n')
  OMAHAPROXY_SHORT_HEADER = (
      'os,channel,current_version\n')
  OMAHAPROXY_CSV_DATA = (
      'cf,dev,12.0.742.30,12.0.742.21,05/07/11,05/06/11,82248,84361,84325\n'
      'cf,beta,12.0.742.30,11.0.696.65,05/09/11,05/06/11,82248,84361,84325\n'
      'cf,stable,11.0.696.65,11.0.696.57,05/06/11,04/27/11,77261,84435,80534\n'
      'linux,dev,12.0.742.30,12.0.742.21,05/06/11,05/06/11,82248,84361,84325\n'
      'linux,beta,12.0.742.30,11.0.696.65,05/09/11,05/06/11,82248,84361,84325\n'
      'linux,stable,11.0.696.1,11.0.696.0,05/06/11,04/27/11,77261,84435,80534\n'
      'mac,canary,13.0.761.0,13.0.760.0,05/10/11,05/09/11,84747,NA,86061\n'
      'mac,dev,12.0.742.30,12.0.742.21,05/07/11,05/06/11,82248,84361,84325\n'
      'mac,beta,12.0.742.30,11.0.696.65,05/09/11,05/06/11,82248,84361,84325\n'
      'mac,stable,11.0.696.65,11.0.696.57,05/06/11,04/27/11,77261,84435,80534\n'
      'win,canary,13.0.761.0,13.0.760.0,05/10/11,05/09/11,84747,NA,86061\n'
      'win,dev,12.0.742.30,12.0.742.21,05/07/11,05/06/11,82248,84361,84325\n'
      'win,beta,12.0.742.30,11.0.696.65,05/09/11,05/06/11,82248,84361,84325\n'
      'win,stable,11.0.696.65,11.0.696.60,05/06/11,04/28/11,77261,84435,80534\n'
      'cros,dev,12.0.742.46,12.0.742.22,05/10/11,05/05/11,82248,84577,84325\n'
      'cros,beta,11.0.696.57,11.0.696.54,05/02/11,04/20/11,77261,82915,80534\n')

  def setUp(self):
    """Setup method for unit test."""
    self.mox_obj = mox.Mox()

  def tearDown(self):
    """Teardown method for unit test."""
    self.mox_obj.UnsetStubs()

  def testParseChannelData_RegularData(self):
    results = chrome_channel_util._ParseChannelData(self.OMAHAPROXY_HEADER +
                                                    self.OMAHAPROXY_CSV_DATA)

    expected_results = [
        {'base_webkit_revision': '84325', 'previous_version': '12.0.742.21',
         'previous_reldate': '05/06/11', 'base_trunk_revision': '82248',
         'current_reldate': '05/07/11', 'current_version': '12.0.742.30',
         'os': 'cf', 'channel': 'dev', 'branch_revision': '84361'},
        {'base_webkit_revision': '84325', 'previous_version': '11.0.696.65',
         'previous_reldate': '05/06/11', 'base_trunk_revision': '82248',
         'current_reldate': '05/09/11', 'current_version': '12.0.742.30',
         'os': 'cf', 'channel': 'beta', 'branch_revision': '84361'},
        {'base_webkit_revision': '80534', 'previous_version': '11.0.696.57',
         'previous_reldate': '04/27/11', 'base_trunk_revision': '77261',
         'current_reldate': '05/06/11', 'current_version': '11.0.696.65',
         'os': 'cf', 'channel': 'stable', 'branch_revision': '84435'},
        {'base_webkit_revision': '84325', 'previous_version': '12.0.742.21',
         'previous_reldate': '05/06/11', 'base_trunk_revision': '82248',
         'current_reldate': '05/06/11', 'current_version': '12.0.742.30',
         'os': 'linux', 'channel': 'dev', 'branch_revision': '84361'},
        {'base_webkit_revision': '84325', 'previous_version': '11.0.696.65',
         'previous_reldate': '05/06/11', 'base_trunk_revision': '82248',
         'current_reldate': '05/09/11', 'current_version': '12.0.742.30',
         'os': 'linux', 'channel': 'beta', 'branch_revision': '84361'},
        {'base_webkit_revision': '80534', 'previous_version': '11.0.696.0',
         'previous_reldate': '04/27/11', 'base_trunk_revision': '77261',
         'current_reldate': '05/06/11', 'current_version': '11.0.696.1',
         'os': 'linux', 'channel': 'stable', 'branch_revision': '84435'},
        {'base_webkit_revision': '86061', 'previous_version': '13.0.760.0',
         'previous_reldate': '05/09/11', 'base_trunk_revision': '84747',
         'current_reldate': '05/10/11', 'current_version': '13.0.761.0',
         'os': 'mac', 'channel': 'canary', 'branch_revision': 'NA'},
        {'base_webkit_revision': '84325', 'previous_version': '12.0.742.21',
         'previous_reldate': '05/06/11', 'base_trunk_revision': '82248',
         'current_reldate': '05/07/11', 'current_version': '12.0.742.30',
         'os': 'mac', 'channel': 'dev', 'branch_revision': '84361'},
        {'base_webkit_revision': '84325', 'previous_version': '11.0.696.65',
         'previous_reldate': '05/06/11', 'base_trunk_revision': '82248',
         'current_reldate': '05/09/11', 'current_version': '12.0.742.30',
         'os': 'mac', 'channel': 'beta', 'branch_revision': '84361'},
        {'base_webkit_revision': '80534', 'previous_version': '11.0.696.57',
         'previous_reldate': '04/27/11', 'base_trunk_revision': '77261',
         'current_reldate': '05/06/11', 'current_version': '11.0.696.65',
         'os': 'mac', 'channel': 'stable', 'branch_revision': '84435'},
        {'base_webkit_revision': '86061', 'previous_version': '13.0.760.0',
         'previous_reldate': '05/09/11', 'base_trunk_revision': '84747',
         'current_reldate': '05/10/11', 'current_version': '13.0.761.0',
         'os': 'win', 'channel': 'canary', 'branch_revision': 'NA'},
        {'base_webkit_revision': '84325', 'previous_version': '12.0.742.21',
         'previous_reldate': '05/06/11', 'base_trunk_revision': '82248',
         'current_reldate': '05/07/11', 'current_version': '12.0.742.30',
         'os': 'win', 'channel': 'dev', 'branch_revision': '84361'},
        {'base_webkit_revision': '84325', 'previous_version': '11.0.696.65',
         'previous_reldate': '05/06/11', 'base_trunk_revision': '82248',
         'current_reldate': '05/09/11', 'current_version': '12.0.742.30',
         'os': 'win', 'channel': 'beta', 'branch_revision': '84361'},
        {'base_webkit_revision': '80534', 'previous_version': '11.0.696.60',
         'previous_reldate': '04/28/11', 'base_trunk_revision': '77261',
         'current_reldate': '05/06/11', 'current_version': '11.0.696.65',
         'os': 'win', 'channel': 'stable', 'branch_revision': '84435'},
        {'base_webkit_revision': '84325', 'previous_version': '12.0.742.22',
         'previous_reldate': '05/05/11', 'base_trunk_revision': '82248',
         'current_reldate': '05/10/11', 'current_version': '12.0.742.46',
         'os': 'cros', 'channel': 'dev', 'branch_revision': '84577'},
        {'base_webkit_revision': '80534', 'previous_version': '11.0.696.54',
         'previous_reldate': '04/20/11', 'base_trunk_revision': '77261',
         'current_reldate': '05/02/11', 'current_version': '11.0.696.57',
         'os': 'cros', 'channel': 'beta', 'branch_revision': '82915'}]

    self.assertEqual(len(expected_results), len(results))

    for i in range(len(expected_results)):
      for key in expected_results[i]:
        self.assertEqual(expected_results[i][key], results[i][key])

  def testParseChannelData_ShortHeader(self):
    results = chrome_channel_util._ParseChannelData(
        self.OMAHAPROXY_SHORT_HEADER + self.OMAHAPROXY_CSV_DATA)

    expected_results = [
        {'current_version': '12.0.742.30', 'os': 'cf', 'channel': 'dev'},
        {'current_version': '12.0.742.30', 'os': 'cf', 'channel': 'beta'},
        {'current_version': '11.0.696.65', 'os': 'cf', 'channel': 'stable'},
        {'current_version': '12.0.742.30', 'os': 'linux', 'channel': 'dev'},
        {'current_version': '12.0.742.30', 'os': 'linux', 'channel': 'beta'},
        {'current_version': '11.0.696.1', 'os': 'linux', 'channel': 'stable'},
        {'current_version': '13.0.761.0', 'os': 'mac', 'channel': 'canary'},
        {'current_version': '12.0.742.30', 'os': 'mac', 'channel': 'dev'},
        {'current_version': '12.0.742.30', 'os': 'mac', 'channel': 'beta'},
        {'current_version': '11.0.696.65', 'os': 'mac', 'channel': 'stable'},
        {'current_version': '13.0.761.0', 'os': 'win', 'channel': 'canary'},
        {'current_version': '12.0.742.30', 'os': 'win', 'channel': 'dev'},
        {'current_version': '12.0.742.30', 'os': 'win', 'channel': 'beta'},
        {'current_version': '11.0.696.65', 'os': 'win', 'channel': 'stable'},
        {'current_version': '12.0.742.46', 'os': 'cros', 'channel': 'dev'},
        {'current_version': '11.0.696.57', 'os': 'cros', 'channel': 'beta'}]

    self.assertEqual(len(expected_results), len(results))

    for i in range(len(expected_results)):
      for key in expected_results[i]:
        self.assertEqual(expected_results[i][key], results[i][key])

  def testIdentifyChannel(self):
    self.mox_obj.StubOutWithMock(chrome_channel_util, 'memcache')
    self.mox_obj.StubOutWithMock(chrome_channel_util, '_GetChannelData')
    chrome_channel_util.memcache.get(mox.IgnoreArg()).AndReturn(None)
    chrome_channel_util._GetChannelData().AndReturn(self.OMAHAPROXY_HEADER +
                                                    self.OMAHAPROXY_CSV_DATA)
    chrome_channel_util.memcache.set(mox.IgnoreArg(), mox.IgnoreArg(),
                                     time=mox.IgnoreArg()).AndReturn(None)
    self.mox_obj.ReplayAll()
    channel = chrome_channel_util.IdentifyChannel('windows', '13.0.761.0')
    self.assertEqual('canary', channel)
    self.mox_obj.VerifyAll()

  def testGetAllChannelVersions(self):
    self.mox_obj.StubOutWithMock(chrome_channel_util, 'memcache')
    self.mox_obj.StubOutWithMock(chrome_channel_util, '_GetChannelData')
    chrome_channel_util.memcache.get(mox.IgnoreArg()).AndReturn(None)
    chrome_channel_util._GetChannelData().AndReturn(self.OMAHAPROXY_HEADER +
                                                    self.OMAHAPROXY_CSV_DATA)
    chrome_channel_util.memcache.set(mox.IgnoreArg(), mox.IgnoreArg(),
                                     time=mox.IgnoreArg()).AndReturn(None)
    self.mox_obj.ReplayAll()
    channel_info = chrome_channel_util.GetAllChannelVersions('windows')
    self.assertEqual('13.0.761.0', channel_info['canary'])
    self.assertEqual('12.0.742.30', channel_info['dev'])
    self.assertEqual('12.0.742.30', channel_info['beta'])
    self.assertEqual('11.0.696.65', channel_info['stable'])
    self.mox_obj.VerifyAll()


if __name__ == '__main__':
  unittest.main()
