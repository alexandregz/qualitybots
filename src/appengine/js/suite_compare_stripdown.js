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
 * @fileoverview Functions used in the suite compare stripdown page.
 */

goog.provide('appcompat.webdiff.SuiteCompareStripDown');

/**
 * Find the given parameter's value in the current page's URL.
 * @param {string} paramName The name of the parameter to find.
 * @return {string} The value of the given parameter in the current page's URL.
 * @export
 */
appcompat.webdiff.SuiteCompareStripDown.findParamFromUrl = function(paramName) {
  paramName = paramName.replace(/[\[]/, '\\\[').replace(/[\]]/, '\\\]');
  var regexS = '[\\?&]' + paramName + '=([^&#]*)';
  var regex = new RegExp(regexS);
  var results = regex.exec(window.location.href);
  if (results == null) {
    return '';
  } else {
    return results[1];
  }
};

/**
 * Set up the navigation menu.
 * @export
 */
appcompat.webdiff.SuiteCompareStripDown.setNavMenuSelect = function() {
  var suite = appcompat.webdiff.SuiteCompareStripDown.findParamFromUrl(
      'suite');
  if (suite && suite.toLowerCase() == 'latest') {
    if (document.location.pathname.indexOf('compare') >= 0) {
      var display_pass =
          appcompat.webdiff.SuiteCompareStripDown.findParamFromUrl(
          'display_pass');
      if (display_pass && display_pass.toLowerCase() == 'true') {
        var link = document.getElementById('latest_suite_pass');
        link.setAttribute('class', 'option selected');
      } else {
        var link = document.getElementById('latest_suite_fail');
        link.setAttribute('class', 'option selected');
      }
    }
  }
};

