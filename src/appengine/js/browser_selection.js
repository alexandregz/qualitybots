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
 * @fileoverview Class for storing the browsers a user has selected to run
 * Bots against.
 *
 */

goog.provide('bots.dashboard.BrowserSelection');



/**
 * Constructor for Browsers the user wishes to use to test with.
 * @param {string} browserName The full name of the browser channel.
 * @param {string} id The identifier of the browser channel.
 * @param {string} abbreviation A shortened name of the browser channel.
 * @constructor
 * @export
 */
bots.dashboard.BrowserSelection = function(browserName, id, abbreviation) {
  /**
   * The full name of the browser channel.
   * @type {string}
   */
  this.browserName = browserName;

  /**
   * The common identifier of the browser channel.
   * @type {string}
   */
  this.id = id;

  /**
   * A shortened name or abbreviation of the browser selection.
   * @type {string}
   */
  this.abbreviation = abbreviation;
};


