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
 * @fileoverview Scripts for a standardized url input box on the Bots pages.
 *
 */


goog.provide('bots.dashboard.UrlInput');

goog.require('goog.dom');
goog.require('goog.events');
goog.require('goog.style');


var URL_TEXTBOX_BLANK_VALUE = 'http://...';
var URL_TEXTBOX_DEFAULT_VALUE = 'http://';



/**
 * Activates the text box the users will use to submit urls.
 * @param {string} textBoxId The ID of the textbox to attach behavior to.
 * @param {?Function} opt_activateCallback Optional callback when the control
 *   is activated.
 * @param {?Function} opt_resetCallback Optional callback when the control is
 *   reset.
 * @constructor
 * @export
 */
bots.dashboard.UrlInput = function(
    textBoxId, opt_activateCallback, opt_resetCallback) {
  this.urlTextBoxId_ = textBoxId;

  var urlTextBox = goog.dom.getElement(textBoxId);

  goog.events.listen(urlTextBox, goog.events.EventType.MOUSEDOWN,
      goog.bind(this.activateUrlTextField_, this));
  goog.events.listen(urlTextBox, goog.events.EventType.FOCUSOUT,
      goog.bind(this.resetBlankUrlTextField_, this));

  this.resetCallback_ = opt_resetCallback || null;
  this.activateCallback_ = opt_activateCallback || null;
};


/**
 * Activates the text box when a user begins to enter a url.
 * @private
 */
bots.dashboard.UrlInput.prototype.activateUrlTextField_ = function() {
  var urlInput = goog.dom.getElement(this.urlTextBoxId_);

  // Only do the init if the box is on its default value
  // and isn't storing user data.
  if (urlInput.value == URL_TEXTBOX_BLANK_VALUE) {
    goog.style.setStyle(urlInput, 'color', '#444');
    urlInput.value = URL_TEXTBOX_DEFAULT_VALUE;

    if (this.activateCallback_) {
      this.activateCallback_();
    }
  }
};


/**
  * Resets the url text field if it's blank or has its default value,
  * otherwise this function doesn't have any effect.
  * @private
  */
bots.dashboard.UrlInput.prototype.resetBlankUrlTextField_ = function() {
  var urlInput = goog.dom.getElement(this.urlTextBoxId_);

  // If the url text box is blank reset the page to it's first time
  // use behavior.
  if (urlInput.value == '' || urlInput.value == URL_TEXTBOX_DEFAULT_VALUE) {
    goog.style.setStyle(urlInput, 'color', '#999');
    urlInput.value = URL_TEXTBOX_BLANK_VALUE;

    if (this.resetCallback_) {
      this.resetCallback_();
    }
  }
};


/**
  * Resets the url input text box to it's default state.
  * @export
  */
bots.dashboard.UrlInput.prototype.resetUrlTextField = function() {
  var urlInput = goog.dom.getElement(this.urlTextBoxId_);
  urlInput.value = '';
  this.resetBlankUrlTextField_();
};

