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
 * @fileoverview This file wraps the content script for use with webdriver.
 *
 */


goog.provide('appcompat.webdiff.webdriver');

goog.require('appcompat.webdiff.Content');


/**
 * Executes the content script for webdriver.
 * @return {Object.<String, Array>} A dictionary of results from executing
 *    the script.
 * @export
 */
appcompat.webdiff.webdriver.executeScript = function() {
  var worker = new appcompat.webdiff.Content();
  return worker.createNodeAndLayoutTable();
};
