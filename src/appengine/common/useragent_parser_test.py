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


"""Unit test for UAParser(useragent_parser.py) module."""



import unittest

import useragent_parser


class UAParserTest(unittest.TestCase):

  TESTDATA_CHROME = [
      {'user_agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.0; en-US) '
       'AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.27 Safari/525.13',
       'browser_family': 'chrome', 'browser_version': '0.2.149.27',
       'os_family': 'windows', 'os_version': 'win_2000',
       'le_family': 'applewebkit', 'le_version': '525.13'},
      {'user_agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) '
       'AppleWebKit/530.5 (KHTML, like Gecko) Chrome/2.0.172.2 Safari/530.5',
       'browser_family': 'chrome', 'browser_version': '2.0.172.2',
       'os_family': 'windows', 'os_version': 'win_xp',
       'le_family': 'applewebkit', 'le_version': '530.5'},
      {'user_agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) '
       'AppleWebKit/530.5 (KHTML, like Gecko) Chrome/2.0.172.43 Safari/530.5',
       'browser_family': 'chrome', 'browser_version': '2.0.172.43',
       'os_family': 'windows', 'os_version': 'win_xp',
       'le_family': 'applewebkit', 'le_version': '530.5'},
      {'user_agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) '
       'AppleWebKit/530.6 (KHTML, like Gecko) Chrome/2.0.174.0 Safari/530.6',
       'browser_family': 'chrome', 'browser_version': '2.0.174.0',
       'os_family': 'windows', 'os_version': 'win_vista',
       'le_family': 'applewebkit', 'le_version': '530.6'},
      {'user_agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) '
       'AppleWebKit/534.14 (KHTML, like Gecko) Chrome/10.0.601.0 Safari/534.14',
       'browser_family': 'chrome', 'browser_version': '10.0.601.0',
       'os_family': 'windows', 'os_version': 'win_7',
       'le_family': 'applewebkit', 'le_version': '534.14'},
      {'user_agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.30 '
       '(KHTML, like Gecko) Chrome/12.0.742.53 Safari/534.30',
       'browser_family': 'chrome', 'browser_version': '12.0.742.53',
       'os_family': 'windows', 'os_version': 'win_7',
       'le_family': 'applewebkit', 'le_version': '534.30'},
      {'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.36 '
       '(KHTML, like Gecko) Chrome/13.0.766.0 Safari/534.36',
       'browser_family': 'chrome', 'browser_version': '13.0.766.0',
       'os_family': 'linux', 'os_version': 'unknown',
       'le_family': 'applewebkit', 'le_version': '534.36'},
      {'user_agent': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.35 (KHTML,'
       ' like Gecko) Ubuntu/10.10 Chromium/13.0.764.0 Chrome/13.0.764.0 '
       'Safari/534.35',
       'browser_family': 'chrome', 'browser_version': '13.0.764.0',
       'os_family': 'linux', 'os_version': 'unknown',
       'le_family': 'applewebkit', 'le_version': '534.35'},
      {'user_agent': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_2; en-US)'
       ' AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 '
       'Safari/534.16',
       'browser_family': 'chrome', 'browser_version': '10.0.648.133',
       'os_family': 'macintosh', 'os_version': '10_6_2',
       'le_family': 'applewebkit', 'le_version': '534.16'},
      {'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_6) '
       'AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.698.0 Safari/534.24',
       'browser_family': 'chrome', 'browser_version': '11.0.698.0',
       'os_family': 'macintosh', 'os_version': '10_6_6',
       'le_family': 'applewebkit', 'le_version': '534.24'},
      {'user_agent': 'Mozilla/5.0 (X11; U; CrOS i686 0.9.130; en-US) '
       'AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.344 '
       'Safari/534.10',
       'browser_family': 'chrome', 'browser_version': '8.0.552.344',
       'os_family': 'cros', 'os_version': '0.9.130',
       'le_family': 'applewebkit', 'le_version': '534.10'}
      ]

  TESTDATA_FIREFOX = [
      {'user_agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; ru-RU; rv:1.7.7)'
       ' Gecko/20050414 Firefox/1.0.3',
       'browser_family': 'firefox', 'browser_version': '1.0.3',
       'os_family': 'windows', 'os_version': 'win_xp',
       'le_family': 'gecko', 'le_version': 'rv:1.7.7'},
      {'user_agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.0; en-GB; rv:1.7.6)'
       ' Gecko/20050321 Firefox/1.0.2',
       'browser_family': 'firefox', 'browser_version': '1.0.2',
       'os_family': 'windows', 'os_version': 'win_2000',
       'le_family': 'gecko', 'le_version': 'rv:1.7.6'},
      {'user_agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; de; rv:1.9.1.11)'
       ' Gecko/20100701 Firefox/3.5.11 ( .NET CLR 3.5.30729; .NET4.0C)',
       'browser_family': 'firefox', 'browser_version': '3.5.11',
       'os_family': 'windows', 'os_version': 'win_7',
       'le_family': 'gecko', 'le_version': 'rv:1.9.1.11'},
      {'user_agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.0; ja; rv:1.9.2.4)'
       ' Gecko/20100513 Firefox/3.6.4 ( .NET CLR 3.5.30729)',
       'browser_family': 'firefox', 'browser_version': '3.6.4',
       'os_family': 'windows', 'os_version': 'win_vista',
       'le_family': 'gecko', 'le_version': 'rv:1.9.2.4'},
      {'user_agent': 'Mozilla/5.0 (X11; U; Linux x86_64; fr; rv:1.9.0.19) '
       'Gecko/2010051407 CentOS/3.0.19-1.el5.centos Firefox/3.0.19',
       'browser_family': 'firefox', 'browser_version': '3.0.19',
       'os_family': 'linux', 'os_version': 'unknown',
       'le_family': 'gecko', 'le_version': 'rv:1.9.0.19'},
      {'user_agent': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; de; '
       'rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12 GTB5',
       'browser_family': 'firefox', 'browser_version': '3.6.12',
       'os_family': 'macintosh', 'os_version': '10.6',
       'le_family': 'gecko', 'le_version': 'rv:1.9.2.12'},
      {'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0b8) '
       'Gecko/20100101 Firefox/4.0b8',
       'browser_family': 'firefox', 'browser_version': '4.0b8',
       'os_family': 'macintosh', 'os_version': '10.6',
       'le_family': 'gecko', 'le_version': 'rv:2.0b8'},
      {'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0b11pre'
       ') Gecko/20110126 Firefox/4.0b11pre',
       'browser_family': 'firefox', 'browser_version': '4.0b11pre',
       'os_family': 'macintosh', 'os_version': '10.6',
       'le_family': 'gecko', 'le_version': 'rv:2.0b11pre'}
      ]

  def testUAParser_Chrome(self):
    for testdata in self.TESTDATA_CHROME:
      parser = useragent_parser.UAParser(testdata['user_agent'])
      self.assertEqual(parser.GetBrowserFamily(), testdata['browser_family'])
      self.assertEqual(parser.GetBrowserVersion(), testdata['browser_version'])
      self.assertEqual(parser.GetOSFamily(), testdata['os_family'])
      self.assertEqual(parser.GetOSVersion(), testdata['os_version'])
      self.assertEqual(parser.GetLayoutEngineFamily(), testdata['le_family'])
      self.assertEqual(parser.GetLayoutEngineVersion(), testdata['le_version'])

  def testUAParser_Firefox(self):
    for testdata in self.TESTDATA_FIREFOX:
      parser = useragent_parser.UAParser(testdata['user_agent'])
      self.assertEqual(parser.GetBrowserFamily(), testdata['browser_family'])
      self.assertEqual(parser.GetBrowserVersion(), testdata['browser_version'])
      self.assertEqual(parser.GetOSFamily(), testdata['os_family'])
      self.assertEqual(parser.GetOSVersion(), testdata['os_version'])
      self.assertEqual(parser.GetLayoutEngineFamily(), testdata['le_family'])
      self.assertEqual(parser.GetLayoutEngineVersion(), testdata['le_version'])

if __name__ == '__main__':
  unittest.main()
