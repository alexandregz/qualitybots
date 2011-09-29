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
 * @fileoverview Functions used by the suite compare page.
 */

goog.provide('appcompat.webdiff.SuiteCompare');

/**
 * Change the checked status of the given elements.
 * @param {string} name The name of the elements to get.
 * @param {boolean} selected Whether the elements should be checked or not.
 * @export
 */
appcompat.webdiff.SuiteCompare.selectAll = function(name, selected) {
  var inputs = document.getElementsByName(name);
  for (var i = 0, node; node = inputs[i]; i++) {
    node.checked = selected;
  }
};

/**
 * Parse a query string to extract the parameter key-value pairs.
 * @param {string} query The query to parse for parameters.
 * @return {Object} The parameter key-value pairs.
 * @export
 */
appcompat.webdiff.SuiteCompare.parseQuery = function(query) {
  var Params = new Object();
  if (!query) {
    // return empty object
    return Params;
  }
  var Pairs = query.split(/[;&]/);
  for (var i = 0; i < Pairs.length; i++) {
    var KeyVal = Pairs[i].split('=');
    if (! KeyVal || KeyVal.length != 2) {
      continue;
    }
    var key = unescape(KeyVal[0]);
    var val = unescape(KeyVal[1]);
    val = val.replace(/\+/g, ' ');
    Params[key] = val;
  }
  return Params;
};

/**
 * Insert the given key and value into the specified query parameters string.
 * @param {string} queryParam The query parameters string.
 * @param {string} key The key to add to the parameters.
 * @param {string} value The value associated with the given key.
 * @return {string} The query parameters string with the key and value inserted.
 */
appcompat.webdiff.SuiteCompare.insertParam = function(queryParam, key, value) {
  key = escape(key);
  value = escape(value);
  var kvp = queryParam.toString().split('&');
  var i = kvp.length;
  var x;
  while (i--) {
    x = kvp[i].split('=');
    if (x[0] == key) {
      x[1] = value;
      kvp[i] = x.join('=');
      break;
    }
  }
  if (i < 0) {
    kvp[kvp.length] = [key, value].join('=');
  }
  return kvp.join('&');
};

/**
 * Remove the given key from the specified query parameters string.
 * @param {string} queryParam The query parameters string.
 * @param {string} key The key to add to the parameters.
 * @return {string} The query parameters string with the given key removed.
 */
appcompat.webdiff.SuiteCompare.removeParam = function(queryParam, key) {
  key = escape(key);
  var kvp = queryParam.toString().split('&');
  var i = kvp.length;
  var x;
  while (i--) {
    x = kvp[i].split('=');
    if (x[0] == key) {
      kvp.splice(i, 1);
      break;
    }
  }
  return kvp.join('&');
};

/**
 * Refresh the values on the page.
 * @export
 */
appcompat.webdiff.SuiteCompare.refreshPage = function() {
  var scoreThreshold = document.getElementById('score_threshold').value;
  var queryParam = document.location.search.substr(1);
  queryParam = appcompat.webdiff.SuiteCompare.insertParam(
      queryParam, 'score_threshold', scoreThreshold);
  var devThreshold = document.getElementById('dev_threshold').value;
  queryParam = appcompat.webdiff.SuiteCompare.insertParam(
      queryParam, 'dev_threshold', devThreshold);

  var displayFail = document.getElementById('display_fail').value;
  var displayPass = document.getElementById('display_pass').value;
  var showAll = document.getElementById('show_all').value;

  if (displayFail) {
    queryParam = appcompat.webdiff.SuiteCompare.insertParam(
        queryParam, 'display_fail', 'true');
    queryParam = appcompat.webdiff.SuiteCompare.removeParam(
        queryParam, 'display_pass');
  }

  if (displayPass) {
    queryParam = appcompat.webdiff.SuiteCompare.insertParam(
        queryParam, 'display_pass', 'true');
    queryParam = appcompat.webdiff.SuiteCompare.removeParam(
        queryParam, 'display_fail');
  }

  if (showAll) {
    queryParam = appcompat.webdiff.SuiteCompare.insertParam(
        queryParam, 'limit', '1000');
  } else {
    queryParam = appcompat.webdiff.SuiteCompare.removeParam(
        queryParam, 'limit');
  }

  queryParam = appcompat.webdiff.SuiteCompare.removeParam(
      queryParam, 'offset');
  window.location.search = queryParam;
};

/**
 * Find the given parameter's value in the current page's URL.
 * @param {string} paramName The name of the parameter to find.
 * @return {string} The value of the given parameter in the current page's URL.
 * @export
 */
appcompat.webdiff.SuiteCompare.findParamFromUrl = function(paramName) {
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
 * Refresh the form parameters for the page.
 * @export
 */
appcompat.webdiff.SuiteCompare.setRefereshFormParams = function() {
  var score_threshold = appcompat.webdiff.SuiteCompare.findParamFromUrl(
      'score_threshold');

  if (score_threshold) {
    document.getElementById('score_threshold').value = score_threshold;
  } else {
    document.getElementById('score_threshold').value = '99.00';
  }

  var dev_threshold = appcompat.webdiff.SuiteCompare.findParamFromUrl(
      'dev_threshold');
  if (dev_threshold) {
    document.getElementById('dev_threshold').value = dev_threshold;
  } else {
    document.getElementById('dev_threshold').value = 0;
  }

  if (appcompat.webdiff.SuiteCompare.findParamFromUrl(
        'display_pass').toLowerCase() == 'true') {
    document.getElementById('display_pass').checked = true;
    document.getElementById('display_fail').checked = false;
  } else if (appcompat.webdiff.SuiteCompare.findParamFromUrl(
        'display_fail').toLowerCase() == 'true') {
    document.getElementById('display_fail').checked = true;
    document.getElementById('display_pass').checked = false;
  } else {
    document.getElementById('display_pass').checked = true;
    document.getElementById('display_fail').checked = true;
  }

  if (appcompat.webdiff.SuiteCompare.findParamFromUrl('limit') == '1000') {
    document.getElementById('show_all').checked = true;
  } else {
    document.getElementById('show_all').checked = false;
  }
};
