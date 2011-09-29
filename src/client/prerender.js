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
* @fileoverview Functions used in the prerender page.
*/

goog.provide('appcompat.webdiff.Prerender');

goog.require('goog.style');


/**
* Find the given parameter's value in the current page's URL.
* @param {string} id DOM Element ID.
* @return {boolean} True if Element visibility changed to visible else false.
* @export
*/
appcompat.webdiff.Prerender.showElement = function(id) {
  var element = goog.dom.getElement(id);
  if (element) {
    goog.style.showElement(element, true);
    return true;
  }
  return false;
};
