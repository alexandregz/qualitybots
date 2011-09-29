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
 * @fileoverview Common functions for interacting with pages.
 *
 */


goog.provide('bots.dashboard.Common');

goog.require('bots.dashboard.Constants');
goog.require('bots.dashboard.UrlManager');
goog.require('goog.dom');
goog.require('goog.net.XhrIo');



/**
 * Constructor for the common methods class.
 * @constructor
 * @export
 */
bots.dashboard.Common = function() {
};


/**
 * Submits the url from a specified input box to the server.
 * @param {string} id The id of the input box to use.
 * @param {bots.dashboard.UrlManager} urlManager The urlManager being used.
 * @param {?Function} opt_callback Callback to use when the submit is
 *   successful.
 * @export
 */
bots.dashboard.Common.submitInputUrl = function(id, urlManager, opt_callback) {
  var urlInput = goog.dom.getElement(id);
  urlManager.addUrl(urlInput.value, false, opt_callback);
};


/**
 * Loads the urls from the server for the current user and sends them to the
 * handlers in UrlManager instance.
 * @param {bots.dashboard.UrlManager} urlManager The urlManager being used.
 * @export
 */
bots.dashboard.Common.loadUrlManagerUrls = function(urlManager) {
  // Chaining the load url requests through callbacks, this provides users
  // with a better experience where they see the submitted + interested urls
  // added, followed by any scores.
  // #TODO(user): Merge the get url requests into a single request, and
  // do the interested/submitted sorting client side.
  var getScores = goog.bind(urlManager.getAndDisplayScores, urlManager);
  var getInterestedUrls = goog.bind(goog.net.XhrIo.send, undefined,
      bots.dashboard.Constants.GETURLS_URL + '?' +
      bots.dashboard.Constants.GETURLS_URL_INTERESTED_PARAM + '=true',
      goog.bind(urlManager.interestedUrlHandler, urlManager, getScores),
      'GET');

  goog.net.XhrIo.send(
      bots.dashboard.Constants.GETURLS_URL + '?' +
      bots.dashboard.Constants.GETURLS_URL_SUBMITTED_PARAM + '=true',
      goog.bind(urlManager.submittedUrlHandler,
                urlManager, getInterestedUrls), 'GET');
};

