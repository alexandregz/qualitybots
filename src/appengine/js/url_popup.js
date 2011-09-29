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
 * @fileoverview Scripts for displaying a popup under a URL input box.
 *
 */

goog.provide('bots.dashboard.UrlPopup');

goog.require('goog.dom');
goog.require('goog.events');



/**
 * Url Popup manager for displays errors to the user.
 * @constructor
 * @export
 */
bots.dashboard.UrlPopup = function() {
};


/**
 * The x offset of the popup from it's parent element.
 * @type {number}
 * @private
 */
bots.dashboard.UrlPopup.OFFSET_X_ = 170;


/**
 * The y offset of the popup from it's parent element.
 * @type {number}
 * @private
 */
bots.dashboard.UrlPopup.OFFSET_Y_ = 42;


/**
 * The id of the Url popup container.
 * @type {string}
 * @export
 */
bots.dashboard.UrlPopup.URL_POPUP_CONTAINER_ID = 'url-popup-container';


/**
 * The minimum height of the UrlPopup container
 * @type {number}
 * @private
 */
bots.dashboard.UrlPopup.CONTAINER_BASE_HEIGHT_ = 59;


/**
 * The base top position of the url in the url selection dialog.
 * @type {number}
 * @private
 */
bots.dashboard.UrlPopup.URL_BASE_TOP_ = 31;


/**
 * The height of a url in the url selection dialog.
 * @type {number}
 * @private
 */
bots.dashboard.UrlPopup.URL_HEIGHT_ = 21;


/**
 * The id of the Url popup container.
 * @enum {string}
 */
bots.dashboard.UrlPopup.POPUP_TYPE = {
  INFO: 'info',
  URL_SELECTION: 'urlSelection'
};


/**
 * Finds the position of an element by using the accumulated offset position
 * of the element and it's ancestors.
 * @param {!Element} element The HTML element to find the position of.
 * @return {!{x: number, y: number}} The x, y coordinates of the element.
 * @private
 */
bots.dashboard.UrlPopup.findPosition_ = function(element) {
  var elementLeft = element.offsetLeft;
  var elementTop = element.offsetTop;

  if (element.offsetParent) {
    while (element = element.offsetParent) {
      elementLeft += element.offsetLeft;
      elementTop += element.offsetTop;
    }
  }
  return {x: elementLeft, y: elementTop};
};


/**
 * Wrapper method that open an info popup.
 * @param {string} id The id the element to appear under.
 * @param {string} msg The title for the urls.
 * @export
 */
bots.dashboard.UrlPopup.prototype.openInfoPopup = function(id, msg) {
  this.open_(bots.dashboard.UrlPopup.POPUP_TYPE.INFO, id, {'msg': msg});
};


/**
 * Wrapper method that open a url selection popup.
 * @param {string} id The id the element to appear under.
 * @param {string} title The title for the urls.
 * @param {string} url The original url of the query.
 * @param {Array} urlKeyMap An a array of {url, key} objects.
 * @param {Function} urlSelectHandler Method to call when a user selects a url.
 * @param {Function} urlForceHandler Method to force the original url request.
 * @export
 */
bots.dashboard.UrlPopup.prototype.openUrlSelection = function(
    id, title, url, urlKeyMap, urlSelectHandler, urlForceHandler) {
  this.open_(bots.dashboard.UrlPopup.POPUP_TYPE.URL_SELECTION, id,
             {'title': title, 'url': url, 'urlKeyMap': urlKeyMap,
              'urlSelectHandler': urlSelectHandler,
              'urlForceHandler': urlForceHandler});
};


/**
 * Opens an information popup underneath a specified element, this is designed
 * to be run internally to this class with a popup type and corresponding
 * parameters.
 * @param {bots.dashboard.UrlPopup.POPUP_TYPE} type The type of popup to open.
 * @param {string} id The id the element to appear under.
 * @param {Object} params A dictionary of parameters to pass to the popup.
 * @private
 */
bots.dashboard.UrlPopup.prototype.open_ = function(type, id, params) {
  // Don't create a duplicate popup if one already exists.
  if (this.isOpen_()) {
    return;
  }

  // Retrieve the parent element to append the popup to.
  var parent = goog.dom.getElement(id);
  if (!parent) {
    return;
  }

  // Retrieve the position of the parent element, and computes the position
  // of the popup.
  //TODO(user): Handle cases when this doesn't appear in the viewport.
  var parentPosition = bots.dashboard.UrlPopup.findPosition_(parent);
  var popupLeft = parentPosition['x'] + bots.dashboard.UrlPopup.OFFSET_X_;
  var popupTop = parentPosition['y'] + bots.dashboard.UrlPopup.OFFSET_Y_;

  switch (type) {
    case bots.dashboard.UrlPopup.POPUP_TYPE.INFO:
      var popup = this.createInfoPopup_(popupLeft, popupTop, params['msg'],
                                        parent);
      break;
    case bots.dashboard.UrlPopup.POPUP_TYPE.URL_SELECTION:
      var popup = this.createUrlSelectionPopup_(popupLeft, popupTop,
         params['title'], parent, params['url'], params['urlKeyMap'],
         params['urlSelectHandler'], params['urlForceHandler']);
      break;
    default:
      var popup = null;
  }

  // Finally attach the popup to the document body, not the "parent" element
  // itself as that can result in the popup being clipped and not displaying
  // properly.
  goog.dom.appendChild(goog.global.document.body, popup);
};


/**
 * Determines whether the popup exists.
 * @param {number} left The left attribute of the popup.
 * @param {number} top The top attribute of the popup.
 * @param {string} title The message to display.
 * @param {Element} parent The parent element to attach to.
 * @param {string} url The message to display.
 * @param {Array} urlKeyMap The message to display.
 * @param {Function} urlSelectHandler Method to call when a user selects a url.
 * @param {Function} urlForceHandler Method to force the original url request.
 * @return {Element} The popup that's been created.
 * @private
 */
bots.dashboard.UrlPopup.prototype.createUrlSelectionPopup_ = function(
    left, top, title, parent, url, urlKeyMap,
    urlSelectHandler, urlForceHandler) {

  // Create the popup container.
  var popup = goog.dom.createDom(goog.dom.TagName.DIV, {
    'id': bots.dashboard.UrlPopup.URL_POPUP_CONTAINER_ID,
    'class': 'urlPopupContainer',
    'style': 'top:' + top + 'px;' +
             'left: ' + left + 'px;' +
             'height: ' + (urlKeyMap.length *
                           bots.dashboard.UrlPopup.URL_HEIGHT_ +
                           bots.dashboard.UrlPopup.CONTAINER_BASE_HEIGHT_) +
                           'px'});

  // Create the arrow effect at the top of the top this is done in two phases,
  // with this being the base
  var arrowBase = goog.dom.createDom(goog.dom.TagName.DIV, {
      'class': 'popupContainerArrowBase'});
  goog.dom.appendChild(popup, arrowBase);

  // Create the white area of the arrow to overlay on top of the base.
  var arrow = goog.dom.createDom(goog.dom.TagName.DIV, {
      'class': 'popupContainerArrow'});
  goog.dom.appendChild(popup, arrow);

  // Create the URL title and append it to the popup container.
  var titleObj = goog.dom.createDom(goog.dom.TagName.SPAN, {
      'class': 'popupTitle',
      'innerHTML': title});
  goog.dom.appendChild(popup, titleObj);

  for (var i = 0; i < urlKeyMap.length; i++) {
    // Create the URL title and append it to the popup container.
    var urlObj = goog.dom.createDom(goog.dom.TagName.SPAN, {
        'style': 'top: ' + (i * bots.dashboard.UrlPopup.URL_HEIGHT_ +
                            bots.dashboard.UrlPopup.URL_BASE_TOP_) + 'px;',
        'class': 'urlPopupSelectionLink',
        'innerHTML': '+ ' + urlKeyMap[i]['url']});
    goog.events.listen(urlObj, goog.events.EventType.CLICK,
        goog.bind(urlSelectHandler, this, urlKeyMap[i]['key'],
                  urlKeyMap[i]['url']));
    goog.events.listen(urlObj, goog.events.EventType.CLICK,
        goog.bind(this.destroy_, this));
    goog.dom.appendChild(popup, urlObj);
  }

  // Create the URL title and append it to the popup container.
  var noThanksObj = goog.dom.createDom(goog.dom.TagName.SPAN, {
      'style': 'top: ' + (urlKeyMap.length *
                          bots.dashboard.UrlPopup.URL_HEIGHT_ +
                          bots.dashboard.UrlPopup.URL_BASE_TOP_) +
                          'px;',
      'class': 'urlPopupSelectionLink',
      'innerHTML': '+ No thanks, please just add the URL I requested'});
  goog.events.listen(noThanksObj, goog.events.EventType.CLICK,
      goog.bind(urlForceHandler, this, url, true));
  goog.events.listen(noThanksObj, goog.events.EventType.CLICK,
      goog.bind(this.destroy_, this));
  goog.dom.appendChild(popup, noThanksObj);

  // Remove the popup when the user focuses on the url box to fix it.
  goog.events.listen(parent, goog.events.EventType.CLICK,
                     goog.bind(this.destroy_, this), true);

  return popup;
};


/**
 * Determines whether the popup exists.
 * @param {number} left The left attribute of the popup.
 * @param {number} top The top attribute of the popup.
 * @param {string} msg The message to display.
 * @param {Element} parent The parent element to attach to.
 * @return {Element} The popup that's been created.
 * @private
 */
bots.dashboard.UrlPopup.prototype.createInfoPopup_ = function(
    left, top, msg, parent) {
  // Create the popup container.
  var popup = goog.dom.createDom(goog.dom.TagName.DIV, {
      'id': bots.dashboard.UrlPopup.URL_POPUP_CONTAINER_ID,
      'style': 'top:' + top + 'px; left: ' + left + 'px;',
      'class': 'infoPopupContainer'});

  // Create the URL title and append it to the popup container.
  var title = goog.dom.createDom(goog.dom.TagName.SPAN, {
      'class': 'popupTitle',
      'innerHTML': msg});
  goog.dom.appendChild(popup, title);

  // Create the arrow effect at the top of the top this is done in two phases,
  // with this being the base.
  var arrowBase = goog.dom.createDom(goog.dom.TagName.DIV, {
      'class': 'popupContainerArrowBase'});
  goog.dom.appendChild(popup, arrowBase);

  // Create the white area of the arrow to overlay on top of the base.
  var arrow = goog.dom.createDom(goog.dom.TagName.DIV, {
      'class': 'popupContainerArrow'});
  goog.dom.appendChild(popup, arrow);

  // Remove the popup when the user focuses on the url box to fix it.
  goog.events.listen(parent, goog.events.EventType.CLICK,
      goog.bind(this.destroy_, this), true);

  return popup;
};


/**
 * Determines whether the popup exists.
 * @return {boolean} Whether the popup exists or not.
 * @private
 */
bots.dashboard.UrlPopup.prototype.isOpen_ = function() {
  var popup = goog.dom.getElement(
      bots.dashboard.UrlPopup.URL_POPUP_CONTAINER_ID);
  return !!popup;
};


/**
 * Destroys the Url popup.
 * @private
 */
bots.dashboard.UrlPopup.prototype.destroy_ = function() {
  var popup = goog.dom.getElement(
      bots.dashboard.UrlPopup.URL_POPUP_CONTAINER_ID);
  if (popup) {
    popup.parentElement.removeChild(popup);
  }
};

