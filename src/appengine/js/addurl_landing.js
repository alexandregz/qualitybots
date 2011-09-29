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
 * @fileoverview Scripts for defining the behavior of the add url landing page.
 * Since the page still needs to hooked up to the backend to be functional the
 * current behavior here is mostly for show.
 *
 */

goog.provide('bots.dashboard.AddUrl');

goog.require('bots.dashboard.Common');
goog.require('bots.dashboard.Constants');
goog.require('bots.dashboard.UrlInput');
goog.require('bots.dashboard.UrlManager');
goog.require('goog.Timer');
goog.require('goog.date');
goog.require('goog.dom');
goog.require('goog.events');
goog.require('goog.net.XhrIo');
goog.require('goog.style');


/**
 * Updates the UI of the page when the starts entering a url.
 * @export
 */
function activateUrlUIUpdate() {
  goog.style.setStyle(goog.dom.getElement(
      bots.dashboard.Constants.URL_SUBMIT_ID), 'display', 'block');
  goog.style.setStyle(goog.dom.getElement('urlAdvert'),
                      'display', 'none');
}


/**
  * Resets the page to its default appearance.
  * @export
  */
function resetPageUI() {
  goog.style.setStyle(goog.dom.getElement(
      bots.dashboard.Constants.URL_SUBMIT_ID), 'display', 'none');
  goog.style.setStyle(goog.dom.getElement('urlAdvert'),
                      'display', 'block');
}


/**
  * Opens the URL dashboard.
  * @export
  */
function openDashboard() {
  window.location = '/url/dashboard';
}


/**
 * Inits the URL input box on the page and submit button.
 */
function initUrlInputs() {
  urlInputBox = new bots.dashboard.UrlInput(
      bots.dashboard.Constants.URL_INPUT_ID, activateUrlUIUpdate, resetPageUI);

  var urlSubmitBox = goog.dom.getElement(
      bots.dashboard.Constants.URL_SUBMIT_ID);
  goog.events.listen(urlSubmitBox, goog.events.EventType.CLICK,
      goog.bind(bots.dashboard.Common.submitInputUrl, this,
                bots.dashboard.Constants.URL_INPUT_ID, urlManager,
                openDashboard));
}

var urlInputBox = null;
var submitBox = goog.dom.getElement('urlSubmitBox');
var urlManager = new bots.dashboard.UrlManager();

goog.Timer.callOnce(initUrlInputs, 0);
goog.Timer.callOnce(
    goog.bind(bots.dashboard.Common.loadUrlManagerUrls, this, urlManager), 0);
