// Copyright 2011 Google Inc. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.


/**
 * @fileoverview File containing common constants for the Bots Url front end.
 *
 */


goog.provide('bots.dashboard.Constants');

goog.require('bots.dashboard.BrowserSelection');


/**
 * The maximum number of urls allowed.
 * @type {number}
 */
bots.dashboard.Constants.MAX_URLS = 20;


/**
 * The url for retrieving the bots urls a user has signed up for.
 * @type {string}
 */
bots.dashboard.Constants.GETURLS_URL = '/signup/get_urls';


/**
 * The parameter for specifying to get only submitted urls.
 * @type {string}
 */
bots.dashboard.Constants.GETURLS_URL_SUBMITTED_PARAM = 'only_submitted_urls';


/**
 * The parameter for specifying to get only interested urls.
 * @type {string}
 */
bots.dashboard.Constants.GETURLS_URL_INTERESTED_PARAM = 'only_interested_urls';


/**
 * The url stub for adding additional urls.
 * @type {string}
 */
bots.dashboard.Constants.ADDURL_URL = '/signup/add_url';


/**
 * The url parameter for specifying the site when adding a url.
 * @type {string}
 */
bots.dashboard.Constants.ADDURL_URL_SITE_PARAM = 'site_url';


/**
 * The url parameter to subscribe to an existing url.
 * @type {string}
 */
bots.dashboard.Constants.ADDURL_URL_EXISTING_PARAM = 'existing_url_key';


/**
 * The url stub for the detail page.
 * @type {string}
 */
bots.dashboard.Constants.DETAIL_URL = '/url/detail';


/**
 * The url stub for retrieving delta diffs.
 * @type {string}
 */
bots.dashboard.Constants.DELTA_URL = '/delta/list';


/**
 * The url stub for retrieving delta diffs.
 * @type {string}
 */
bots.dashboard.Constants.DELTA_DYNAMICCONTENT_URL = '/delta/dynamiccontent';


/**
 * The url stub for retrieving delta diffs.
 * @type {string}
 */
bots.dashboard.Constants.DELTA_KEY_PARAM = 'key';


/**
 * The url stub for retrieving delta diffs.
 * @type {string}
 */
bots.dashboard.Constants.DELTA_DELTAONLY_PARAM = 'deltaonly';


/**
 * The url stub for retrieving delta diffs.
 * @type {string}
 */
bots.dashboard.Constants.DELTA_INDEX_PARAM = 'i';


/**
 * The url stub for requesting screenshots
 * @type {string}
 */
bots.dashboard.Constants.SCREENSHOT_URL = '/screenshot';


/**
 * The key parameter for fetching screenshots.
 * @type {string}
 */
bots.dashboard.Constants.SCREENSHOT_URL_KEY_PARAM = 'key';


/**
 * The url parameter name for the detail page.
 * @type {string}
 */
bots.dashboard.Constants.DETAIL_URL_URL_PARAM = 'url';


/**
 * The url parameter name for the detail page.
 * @type {string}
 */
bots.dashboard.Constants.DETAIL_URL_DELTAKEY_PARAM = 'page_delta_key';


/**
 * The browser parameter name for the detail page.
 * @type {string}
 */
bots.dashboard.Constants.DETAIL_URL_BROWSER_PARAM = 'browser';


/**
 * The forced add parameter.
 * @type {string}
 */
bots.dashboard.Constants.FORCED_ADD_PARAM = 'forced_add';


/**
 * The default ID of the url input box.
 * @type {string}
 */
bots.dashboard.Constants.URL_INPUT_ID = 'urlInput';


/**
 * The default ID of the url submit button.
 * @type {string}
 */
bots.dashboard.Constants.URL_SUBMIT_ID = 'urlSubmit';


/**
 * The browser parameter name for the detail page.
 * @type {Array.<bots.dashboard.BrowserSelection>}
 */
bots.dashboard.Constants.BROWSERS_UNDER_TEST = [
    new bots.dashboard.BrowserSelection('Chrome Beta Channel', 'beta', 'Beta'),
    new bots.dashboard.BrowserSelection('Chrome Dev Channel', 'dev', 'Dev'),
    new bots.dashboard.BrowserSelection(
        'Chrome Canary Channel', 'canary', 'Cnr')
];

