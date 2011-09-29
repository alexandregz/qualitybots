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
 * @fileoverview This file contains URLs for different requests to the server,
 * and a helper method for sending data to the server.
 *
 */

goog.provide('appcompat.webdiff.BasicCommManager');

goog.require('goog.Uri');
goog.require('goog.net.XhrIo');


/**
 * Wrapper method for goog.net.XhrIo.send.
 * @param {string} url The URL to send request to.
 * @param {function(string): void} opt_callback Optional, the callback function.
 * @param {string=} opt_method Optional, the method to use. Default is 'GET'.
 * @param {Object=} opt_query Optional, the query object.
 * @export
 */
appcompat.webdiff.BasicCommManager.send = function(url, opt_callback,
    opt_method, opt_query) {
  var method = opt_method || 'GET';
  var query = opt_query || {};

  var queryString = goog.Uri.QueryData.createFromMap(query).toString();

  if (opt_callback) {
    var callbackFunc = function() {
      var response = '';
      if (this.isSuccess()) {
        response = this.getResponseText();
      } else {
        window.console.error(response);
      }
      opt_callback(response);
    };
  } else {
    var callbackFunc = null;
  }

  if (method == 'GET' && queryString) {
    url = url + '?' + queryString;
    queryString = '';
  }
  goog.net.XhrIo.send(url, callbackFunc, method, queryString);
};
