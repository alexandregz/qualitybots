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


"""Tests for appengine_communicator.

These tests are mostly checking for proper data handling.
"""



import json
import StringIO
import time
import unittest
import urllib
import urllib2

import mox

import appengine_communicator


class AppengineCommunicatorTest(unittest.TestCase):

  def setUp(self):
    self.mox = mox.Mox()
    self._communicator = appengine_communicator.AppEngineCommunicator(
        'chromedriver', 'chrome', 'instance')

  def tearDown(self):
    self.mox.UnsetStubs()

  def testExponentialBackoff_FirstAttempt(self):
    start = time.time()
    appengine_communicator.AppEngineCommunicator.ExponentialBackoff(0)
    finish = time.time()
    self.assertTrue(start+1 < finish)
    self.assertTrue(start+3 > finish)

  def testExponentialBackoff_SecondAttempt(self):
    start = time.time()
    appengine_communicator.AppEngineCommunicator.ExponentialBackoff(1)
    finish = time.time()
    self.assertTrue(start+3 < finish)
    self.assertTrue(start+10 > finish)

  def testFetchTest_HasTest(self):
    self.mox.StubOutWithMock(urllib2, 'urlopen')
    test_response = StringIO.StringIO(
        '{"data_str": "ContentMap[\\"URL\\"]=\\"http:\\/\\/finance.google.com'
        '\\"", "start_time": "2011-08-10 23:45:51.548554", "config": '
        '"{\\"Tokens\\":\\"chromedriver\\",\\"height\\":\\"512\\",\\'
        '"Project\\":\\"AppCompat\\",\\"width\\":\\"1024\\",\\"useCachedPage'
        '\\":\\"false\\",\\"refBrowser\\":\\"Chrome\\/14.0.835.15\\",'
        '\\"refBrowserChannel\\":\\"stable\\"}", '
        '"id": 4490381, "key": 259702}')

    data = urllib.urlencode({'tokens': 'chromedriver',
                             'useragent': 'chrome',
                             'instance_id': 'instance'})
    urllib2.urlopen(appengine_communicator._FETCH_TEST_URL,
                    data).AndReturn(test_response)

    self.mox.ReplayAll()
    test_case = self._communicator.FetchTest()
    self.assertEqual(test_case, self._communicator._current_test_case)
    self.assertEqual('http://finance.google.com', test_case.url)
    self.assertEqual('2011-08-10 23:45:51.548554', test_case.start_time)
    self.assertEqual(json.loads(
        '{"Tokens":"chromedriver","height":"512","Project":"AppCompat",'
        '"width":"1024","useCachedPage":"false","refBrowser":'
        '"Chrome/14.0.835.15","refBrowserChannel":"stable"}'),
                     test_case.config)
    self.assertEqual(259702, test_case.test_key)
    self.assertEqual(None, test_case.auth_cookie)
    self.mox.VerifyAll()

  def testFetchTest_HasTestAndCookie(self):
    self.mox.StubOutWithMock(urllib2, 'urlopen')
    test_response = StringIO.StringIO(
        '{"data_str": "ContentMap[\\"URL\\"]=\\"http:\\/\\/finance.google.com'
        '\\"", "start_time": "2011-08-10 23:45:51.548554", "config": '
        '"{\\"Tokens\\":\\"chromedriver\\",\\"height\\":\\"512\\",\\'
        '"Project\\":\\"AppCompat\\",\\"width\\":\\"1024\\",\\"useCachedPage'
        '\\":\\"false\\",\\"refBrowser\\":\\"Chrome\\/14.0.835.15\\",'
        '\\"refBrowserChannel\\":\\"stable\\",'
        '\\"auth_domain\\":\\"finance.google.com\\",\\"auth_cookies\\":'
        '[{\\"domain\\":\\".google.com\\",\\"secure\\": false,\\"value\\":'
        '\\"www\\", \\"expiry\\": 131689857.0,\\"path\\":\\"/\\",'
        '\\"http_only\\":false,\\"name\\":\\"SelectedEdition\\"}]}", '
        '"id": 4490381, "key": 259702}')

    data = urllib.urlencode({'tokens': 'chromedriver',
                             'useragent': 'chrome',
                             'instance_id': 'instance'})
    urllib2.urlopen(appengine_communicator._FETCH_TEST_URL,
                    data).AndReturn(test_response)

    self.mox.ReplayAll()
    test_case = self._communicator.FetchTest()
    self.assertEqual(test_case, self._communicator._current_test_case)
    self.assertEqual('http://finance.google.com', test_case.url)
    self.assertEqual('2011-08-10 23:45:51.548554', test_case.start_time)
    self.assertEqual(json.loads(
        '{"Tokens":"chromedriver","height":"512","Project":"AppCompat",'
        '"width":"1024","useCachedPage":"false","refBrowser":'
        '"Chrome/14.0.835.15","refBrowserChannel":"stable",'
        '"auth_domain":"finance.google.com",'
        '"auth_cookies":[{"domain":".google.com","secure":false,"value":"www",'
        '"expiry":131689857.0,"path":"/","http_only":false,"name":'
        '"SelectedEdition"}]}'), test_case.config)
    self.assertEqual(259702, test_case.test_key)
    self.assertNotEqual('finance.google.com', test_case.auth_cookie)
    self.assertEqual('finance.google.com', test_case.auth_cookie.domain)
    self.assertEqual([{'domain': '.google.com', 'secure': False, 'value': 'www',
                       'expiry': 131689857.0, 'path': '/', 'http_only': False,
                       'name': 'SelectedEdition'}],
                     test_case.auth_cookie.cookies)
    self.mox.VerifyAll()

  def testFetchTest_NoTest(self):
    self.mox.StubOutWithMock(urllib2, 'urlopen')
    test_response = StringIO.StringIO('null')

    data = urllib.urlencode({'tokens': 'chromedriver',
                             'useragent': 'chrome',
                             'instance_id': 'instance'})
    urllib2.urlopen(appengine_communicator._FETCH_TEST_URL,
                    data).AndReturn(test_response)

    self.mox.ReplayAll()
    test_case = self._communicator.FetchTest()
    self.assertEqual(None, self._communicator._current_test_case)
    self.assertEqual(None, test_case)
    self.mox.VerifyAll()

  def testFinishTest_HasTest(self):
    self._communicator._current_test_case = appengine_communicator.TestCase(
        'www.google.com', '123', [], 1234)
    self.mox.StubOutWithMock(urllib2, 'urlopen')

    data = urllib.urlencode({'key': 1234, 'result': 'success',
                             'instance_id': 'instance'})
    urllib2.urlopen(appengine_communicator._FINISH_TEST_URL,
                    data).AndReturn(None)

    self.mox.ReplayAll()
    self._communicator.FinishTest('success')
    self.assertEqual(None, self._communicator._current_test_case)
    self.mox.VerifyAll()

  def testFinishTest_NoTest(self):
    self.assertEqual(None, self._communicator.FinishTest('success'))


def main():
  unittest.main()


if __name__ == '__main__':
  main()
