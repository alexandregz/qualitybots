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
 * @fileoverview Page specific scripts for displaying data on the URL
 * dashboard, and taking new requests.
 *
 */

goog.provide('bots.dashboard.UrlDashboard');

goog.require('bots.dashboard.BrowserSelection');
goog.require('bots.dashboard.Common');
goog.require('bots.dashboard.Constants');
goog.require('bots.dashboard.UrlInput');
goog.require('bots.dashboard.UrlManager');
goog.require('goog.Timer');
goog.require('goog.dom');
goog.require('goog.net.XhrIo');
goog.require('goog.style');


/**
 * Updates the UI of the page when the starts entering a url.
 * @export
 */
function activateUrlUIUpdate() {
  goog.style.setStyle(goog.dom.getElement(
      bots.dashboard.Constants.URL_SUBMIT_ID), 'display', 'block');
}


/**
  * Resets the page to its default appearance.
  * @export
  */
function resetPageUI() {
  goog.style.setStyle(goog.dom.getElement(
      bots.dashboard.Constants.URL_SUBMIT_ID), 'display', 'none');
}


/**
 * Gets the browsers that the current user will test with (currently mocked)
 * and displays them on the page.
 * @export
 */
function initBrowserSelection() {
  // Iterate in reverse order
  var i = 0;
  var container = goog.dom.getElement('browserChannelContainer');
  while (i < bots.dashboard.Constants.BROWSERS_UNDER_TEST.length) {
    var browserChannelHeader = goog.dom.createElement(goog.dom.TagName.SPAN);
    goog.dom.setProperties(browserChannelHeader,
        {'class': 'browserColumnHeader',
         'innerHTML':
             bots.dashboard.Constants.BROWSERS_UNDER_TEST[i].abbreviation,
         'title':
             bots.dashboard.Constants.BROWSERS_UNDER_TEST[i].browserName});
    goog.dom.insertChildAt(container, browserChannelHeader, i);
    i++;
  }
}


/**
 * Inits the URL input box on the page and submit button.
 */
function initUrlInputs() {
  urlInputBox = new bots.dashboard.UrlInput(
      bots.dashboard.Constants.URL_INPUT_ID, activateUrlUIUpdate,
      resetPageUI);

  var urlSubmitBox = goog.dom.getElement(
      bots.dashboard.Constants.URL_SUBMIT_ID);
  goog.events.listen(urlSubmitBox, goog.events.EventType.CLICK,
      goog.bind(bots.dashboard.Common.submitInputUrl, undefined,
                bots.dashboard.Constants.URL_INPUT_ID, urlManager, null));
}


// Create instances of the urlManager and urlInput.
var urlInputBox = null;
var urlManager = new bots.dashboard.UrlManager();

// Queue up the init functions.
goog.Timer.callOnce(initBrowserSelection, 0);
goog.Timer.callOnce(initUrlInputs, 0);
goog.Timer.callOnce(
    goog.bind(bots.dashboard.Common.loadUrlManagerUrls, this, urlManager), 0);
