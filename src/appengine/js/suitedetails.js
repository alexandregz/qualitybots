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
 * @fileoverview Handle test suite details.
 */

goog.provide('appcompat.SuiteDetails');

goog.require('goog.dom');
goog.require('goog.json');



/**
 * Handle the manipulation of test suite details.
 * @constructor
 * @export
 */
appcompat.SuiteDetails = function() {
};

/**
 * The server URL to connect to.
 * @type{string}
 * @const
 */
appcompat.SuiteDetails.SERVER_URL = 'http://YOUR_APPENGINE_SERVER_HERE/';

/**
 * Set the status message for the the suite details.
 * @param {string} msg The status message.
 * @param {string?} opt_className Class name to set on the message div.
 * @private
 */
appcompat.SuiteDetails.prototype.setStatusMessage_ =
    function(msg, opt_className) {
  var className = opt_className || 'suiteDetailsStatus';
  var msgDiv = goog.dom.getElement('suite_details_status');
  if (msgDiv != null) {
    msgDiv.setAttribute('class', className);
    goog.dom.setTextContent(msgDiv, msg);
  }
};


/**
 * Set the status message for the the suite details.
 * @param {Element} elem An element to use as the root of the xpath search.
 * @param {string} xpath The xpath to use to get elements.
 * @return {Array.<Element>} An array of elements that are found from the
 *     given xpath.
 */
appcompat.SuiteDetails.prototype.getElementsByXPath = function(elem, xpath) {
  var elements = [];
  var doc = elem.ownerDocument == null ? elem : elem.ownerDocument;
  var foundElements = doc.evaluate(xpath, elem, null,
      XPathResult.ORDERED_NODE_ITERATOR_TYPE, null);
  var iElement = foundElements.iterateNext();
  while (iElement) {
    elements.push(iElement);
    iElement = foundElements.iterateNext();
  }
  return elements;
};


/**
 * Change the checked status of elements found from the given name.
 * @param {string} name Name of the elements to change.
 * @param {boolean} selected Whether the element should be checked or not.
 * @export
 */
appcompat.SuiteDetails.prototype.selectAll = function(name, selected) {
  var inputs = document.getElementsByName(name);
  for (var i = 0, node; node = inputs[i]; i++) {
    node.checked = selected;
  }
};

/**
 * Find a parameter from within the current URL.
 * @param {string} paramName The name of the parameter to find.
 * @param {string?} opt_url An optional URL to check for the parameter. If an
 *     url is not specified, the current location's URL is used.
 * @return {string} If the parameter name is found, the parameter value is
 *     returned. Otherwise, an empty string is returned.
 */
appcompat.SuiteDetails.prototype.findParamFromUrl = function(
    paramName, opt_url) {
  paramName = paramName.replace(/[\[]/, '\\\[').replace(/[\]]/, '\\\]');
  var regexS = '[\\?&]' + paramName + '=([^&#]*)';
  var regex = new RegExp(regexS);
  if (!opt_url) {
    opt_url = window.location.href;
  }
  var results = regex.exec(opt_url);
  if (results == null)
    return '';
  else
    return results[1];
};


/**
 * Remove the save button element from the given element.
 * @param {Element} element The element to remove the save button from.
 * @export
 */
appcompat.SuiteDetails.prototype.removeSaveButton = function(element) {
  element.parentElement.removeChild(element);
};


/**
 * Save the text data within the given element.
 * @param {Element} element The element to remove the save button from.
 * @export
 */
appcompat.SuiteDetails.prototype.saveData = function(element) {
  element.setAttribute('disabled', 'disabled');
  element.setAttribute('value', 'Saving...');
  var elemTextArea = element.parentElement.getElementsByTagName('textarea')[0];
  var textAreaValue = elemTextArea.value;

  try {
    var dataKey = this.getElementsByXPath(
        element.parentElement.parentElement,
        ".//input[@name='result']")[0].value;
  } catch (TypeError) {
    var dataKey = element.parentElement.getElementsByTagName('input')[0].value;
  }
  var dataName = elemTextArea.getAttribute('name');
  var info = {};
  info[dataName] = textAreaValue;
  var params = 'key=' + escape(dataKey) + '&info=' + goog.json.serialize(info);
  var http = new XMLHttpRequest();
  http.open('POST', appcompat.SuiteDetails.SERVER_URL + 'delta/edit', false);
  http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
  http.send(params);
  this.removeSaveButton(element);
  this.removeAlert(elemTextArea);
};


/**
 * Add a new element with the given name and attributes to the specified
 * parent element.
 * @param {Element} parentElement Parent element to add the new element to.
 * @param {string} newElemName Name of the new element.
 * @param {Object} newElemAttr An object containinge the keys and values to
 *     use for setting the new element's attributes.
 */
appcompat.SuiteDetails.prototype.addElement =
    function(parentElement, newElemName, newElemAttr) {
  var newElement = document.createElement(newElemName);
  for (var k in newElemAttr) {
    newElement.setAttribute(k, newElemAttr[k]);
  }
  parentElement.appendChild(newElement);
};


/**
 * Add a save button to the given element.
 * @param {Element} element Element to add the save button to.
 * @export
 */
appcompat.SuiteDetails.prototype.addSaveButton = function(element) {
  var elementClass = element.getAttribute('class') + '_save';
  var saveButton = this.getElementsByXPath(
      element.parentElement.parentElement,
      ".//input[@class='" + elementClass + "']")[0];

  // Don't add button if it's already present.
  if (saveButton) {
    return;
  }

  var attr = {'type': 'button',
              'class': elementClass,
              'onclick': 'sd.saveData(this)',
              'value': 'Save'};
  this.addElement(element.parentElement, 'input', attr);
  // Let's add onblur event on element to remove this save button.
  element.setAttribute('onblur', 'sd.removeSaveButton(this)');
};


/**
 * Add an alert to the given element.
 * @param {Element} element Element to add the alert to.
 */
appcompat.SuiteDetails.prototype.addAlert = function(element) {
  var style = ('background-color:#CCFFCC;' +
               'background-image:url(\'/s/alert_fav.png\');' +
               'background-repeat:no-repeat;background-position:right top;');
  // If Existing style present then let's append.
  if (element.hasAttribute('style')) {
    style = element.getAttribute('style') + ';' + style;
  }
  element.setAttribute('style', style);
  element.setAttribute('title', 'Unsaved Changes');
};


/**
 * Remove an alert from the given element.
 * @param {Element} element Element to remove the alert from.
 */
appcompat.SuiteDetails.prototype.removeAlert = function(element) {
  element.removeAttribute('style');
  element.removeAttribute('title');
};


/**
 * Disable the "onblur" handler for the given element.
 * @param {Element} element Element to disable the onblur handler for.
 * @export
 */
appcompat.SuiteDetails.prototype.disableOnBlur = function(element) {
  element.removeAttribute('onblur');
  this.addAlert(element);
};


/**
 * Save the ignore status for the given element.
 * @param {Element} element Element to save the ignore status for.
 * @export
 */
appcompat.SuiteDetails.prototype.saveIgnore = function(element) {
  this.setStatusMessage_('Saving...');
  var dataKey = this.getElementsByXPath(
      element.parentElement.parentElement, ".//input[@name='result']")[0].value;
  var ignore = element.checked;
  var params = 'key=' + escape(dataKey) + '&ignore=' + ignore;
  var http = new XMLHttpRequest();
  http.open('POST', appcompat.SuiteDetails.SERVER_URL + 'delta/edit', false);
  http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
  http.send(params);
  this.setStatusMessage_('', 'none');
};
