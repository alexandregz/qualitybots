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
 * @fileoverview This file contains the content script to extract nodes info and
 * layout info from the page.
 *
 */


goog.provide('appcompat.webdiff.Content');

goog.require('appcompat.webdiff.Prerender');
goog.require('appcompat.webdiff.ScreenshotContent');
goog.require('appcompat.webdiff.constants');
goog.require('common.dom.querySelector');
goog.require('goog.Timer');
goog.require('goog.Uri');
goog.require('goog.events');



/**
 * Content script class.
 * @param {Object} opt_window Optional, a mock window object.
 * @constructor
 */
appcompat.webdiff.Content = function(opt_window) {
  /**
   * A mock window object (for testing) or the global window object.
   * @type {Object}
   */
  this.window = opt_window || goog.global.window;
};


/**
 * Enum for the actions that the content script can take.
 * @enum {string}
 **/
appcompat.webdiff.Content.Actions = {
  ABORT: 'abort',
  BYE: 'bye',
  CLOSE_TAB: 'close_tab',
  DATA_SENT: 'data_sent',
  DUPLICATE: 'duplicate',
  EXTRACT_DATA: 'extract_data',
  INIT: 'init',
  OK_TO_INIT: 'ok_to_init',
  READY_TO_RUN: 'ready_to_run',
  REG_VISIBILITY_CHANGE_EVENT: 'reg_vis_event',
  REG_VISIBILITY_CHANGE_EVENT_DONE: 'reg_vis_event_done',
  SEND_RESULTS: 'send_results',
  SET_PRERENDER_STATUS: 'set_prerender_status',
  WAIT: 'wait',
  WAIT_FOR_PRERENDER: 'wait_for_prerender'
};


/**
 * String prefix to be used to append the assigned ID into the node's className
 * attribute.
 * @type {string}
 * @private
 * @const
 */
appcompat.webdiff.Content.ID_PREFIX_ = 'appcompat-id-';


/**
* String prefix to be used to append the assigned ID into the node's className
* attribute.
* @type {string}
* @const
*/
appcompat.webdiff.Content.BOTS_STATE_ATTR = 'botsState';


/**
* Connection port for communication with background page.
* @type {Object}
* @private
*/
appcompat.webdiff.Content.connectionPort_ = null;


/**
 * The "do once" timer for waiting on window creation complete.
 * @type {?number}
 * @private
 */
appcompat.webdiff.Content.prototype.waitTimer_ = null;


/**
* The "do once" timer for waiting before prerender action.
* @type {?number}
* @private
*/
appcompat.webdiff.Content.prototype.prerenderWaitTimer_ = null;


/**
 * Table containing descriptive information of all HTML nodes in the page. Each
 * node's index in this list is its assigned ID and is stored into its className
 * attribute.
 * @type {Array.<Object.<string, (number|string)>>}
 * @private
 */
appcompat.webdiff.Content.prototype.nodesTable_ = null;


/**
 * List of integers identifying the id assigned to the className of dynamic
 * content.
 * @type {Array.<number>}
 * @private
 */
appcompat.webdiff.Content.prototype.dynamicContentTable_ = null;


/**
 * List of regular expressions to use to test for dynamic content and ads.
 * @type {Array.<RegExp>}
 */
appcompat.webdiff.Content.patterns = [
    /https?:\/\/ads?-?g?\.doubleclick\.net/g, /https?:\/\/ads?\.cnn\.com/g];


/**
 * Table containing the page's layout information. The (i, j)th element in the
 * table corresponds to the assigned ID of the node at position (i, j) on the
 * page.
 * @type {Array.<Array.<string>>}
 * @private
 */
appcompat.webdiff.Content.prototype.layoutTable_ = null;


/**
 * The class that handles the screenshot taking from the content script side.
 * @type {appcompat.webdiff.ScreenshotContent}
 * @private
 */
appcompat.webdiff.ScreenshotContent.screenshotContent_ = null;


/**
 * Saves the assigned ID into the node's className attribute for later use.
 * @param {Object} node The HTML node to save ID into.
 * @param {number} id The assigned ID of the node.
 * @private
 */
appcompat.webdiff.Content.prototype.saveIdIntoClassName_ = function(node, id) {
  node.className += ' ' + appcompat.webdiff.Content.ID_PREFIX_ + id;
};


/**
* Saves the assigned ID into the node's className attribute for later use.
* @param {boolean} prerenderSuccess The HTML node to save ID into.
* @this appcompat.webdiff.Content
*/
appcompat.webdiff.Content.prerenderAction = function(prerenderSuccess) {
  var prerenderUrl = document.getElementById('prerender').getAttribute('href');
  var port = appcompat.webdiff.Content.connectionPort_;
  console.log('Set Prerender Status -' + prerenderSuccess);
  if (prerenderSuccess) {
    // Let's clear the timer if any.
    if (this.prerenderWaitTimer_) {
      goog.Timer.clear(this.prerenderWaitTimer_);
    }
    appcompat.webdiff.Prerender.showElement('pass');
  } else {
    appcompat.webdiff.Prerender.showElement('fail');
  }
  port.postMessage({
    action: appcompat.webdiff.Content.Actions.SET_PRERENDER_STATUS,
    status: prerenderSuccess});
  console.log('URL Redirect -' + prerenderUrl);
  // Let's go to prerender page now.
  document.location.href = prerenderUrl;
};


/**
 * Extracts the assigned ID from the node's className attribute. Returns '-1' if
 * no assigned ID is stored.
 * @param {Object} node The HTML node to extract ID from.
 * @return {string} The assigned ID, or '-1' if no ID can be found.
 * @private
 */
appcompat.webdiff.Content.prototype.extractIdFromClassName_ = function(node) {
  if (!('className' in node)) {
    console.log('ClassName is not present');
    return '-1';
  }
  var className = node.className;
  var idIndex = className.search(
      appcompat.webdiff.Content.ID_PREFIX_ + '([0-9]+)');
  var id = '-1';
  if (idIndex >= 0) {
    id = className.substr(idIndex +
        appcompat.webdiff.Content.ID_PREFIX_.length);
  }
  return id;
};

/**
 * Checks if the given node is an ad or dynamic content.
 * @param {Object} node The HTML node to check for dynamic content.
 * @private
 */
appcompat.webdiff.Content.prototype.checkForDynamicContent_ = function(node) {
  var dynamicContentFlag = false;
  if (node.hasAttribute('src')) {
    var src = node.getAttribute('src');
  }
  else if (node.hasAttribute('href')) {
    var href = node.getAttribute('href');
  }
  for (var i = 0, len = appcompat.webdiff.Content.patterns.length; i < len;
       ++i) {
    var pattern = appcompat.webdiff.Content.patterns[i];
    if (src && pattern.test(src)) {
      this.dynamicContentTable_.push(
          parseInt(this.extractIdFromClassName_(node), 10));
      dynamicContentFlag = true;
      break;
    }
    else if (href && pattern.test(href)) {
      this.dynamicContentTable_.push(
          parseInt(this.extractIdFromClassName_(node), 10));
      dynamicContentFlag = true;
      break;
    }
  }
  // Let's add all the child elements of dynamic content (ads) as they are
  // also dynamic content. Exception for iframe, as it cannot be accessed
  // due to same domain policy.
  if (dynamicContentFlag && node.tagName.toLowerCase() != 'iframe') {
    for (var k = 0; k < node.childNodes.length; k++) {
      var childNode = node.childNodes[k];
      if (childNode) {
        this.dynamicContentTable_.push(
            parseInt(this.extractIdFromClassName_(childNode), 10));
      }
    }
  }
};


/**
 * Extracts information from all nodes, creates the table containing their
 * information and saves each node's ID into the node. Currently the node's
 * selector, width, height and offset position (relative to its parent) are
 * extracted.
 * @private
 */
appcompat.webdiff.Content.prototype.createNodesTable_ = function() {
  this.nodesTable_ = [];

  var allnodes = document.getElementsByTagName('*');
  for (var i = 0, node; node = allnodes[i]; i++) {
    if (node.style.display == 'none' || node.style.display == 'hidden') {
      this.saveIdIntoClassName_(node, -3);
    } else {
      this.saveIdIntoClassName_(node, i);
    }

    var selector = common.dom.querySelector.getSelector(node);
    var nodeData = {
      'w': node.offsetWidth,
      'h': node.offsetHeight,
      'x': node.offsetLeft,
      'y': node.offsetTop,
      'p': selector
    };

    this.nodesTable_[i] = nodeData;
  }

  this.dynamicContentTable_ = [];
  var node;
  for (var i = 0; node = allnodes[i]; i++) {
    this.checkForDynamicContent_(node);
  }
};


/**
 * Samples each pixel and stores the ID of the element at that pixel into the
 * layoutTable.
 * @private
 */
appcompat.webdiff.Content.prototype.createLayoutTable_ = function() {
  this.layoutTable_ = [];

  for (var y = 0; y < this.window.innerHeight; y++) {
    this.layoutTable_[y] = [];

    for (var x = 0; x < this.window.innerWidth; x++) {
      var element = document.elementFromPoint(x, y);
      if (element) {
        this.layoutTable_[y][x] = this.extractIdFromClassName_(element);
      } else {
        this.layoutTable_[y][x] = '-2';
      }
    }
  }
};


/**
 * Sends the data extracted from the page (nodesTable and layoutTable) to the
 * background script. Closes the window after the background script sends back
 * a response.
 * @param {Object} port A connected port to use to communicate with the
 *     extension background page.
 * @private
 */
appcompat.webdiff.Content.prototype.sendDataToBackground_ = function(port) {
  port.postMessage({
    action: appcompat.webdiff.Content.Actions.SEND_RESULTS,
    nodesTable: this.nodesTable_,
    dynamicContentTable: this.dynamicContentTable_,
    layoutTable: this.layoutTable_
  });
};


/**
* Function to update DOM State.
* @param {string} state State of the Communication with background script.
* @private
*/
appcompat.webdiff.Content.prototype.updateDomState_ = function(state) {
  document.body.setAttribute(
      appcompat.webdiff.Content.BOTS_STATE_ATTR,
      state);
};


/**
* Function to handle REG_VISIBILITY_CHANGE_EVENT Message.
* @param {Object} port A connected port to use to communicate with the
*     extension background page.
* @param {Object} msg A json object which represents the content of the
      message.
* @private
*/
appcompat.webdiff.Content.prototype.handleRegVisibilityChangeEventMsg_ =
    function(port, msg) {
  this.updateDomState_(
      appcompat.webdiff.Content.Actions.REG_VISIBILITY_CHANGE_EVENT);

  // Let's create handler to handle webkitvisibilitychange event.
  var handler = function(e) {
    console.log('Event Type:' + e.type);
    console.log('VisibilityState:' + document.webkitVisibilityState);
    var bots_state = document.body.getAttribute(
    appcompat.webdiff.Content.BOTS_STATE_ATTR);
    // Prevent duplicate events from running the code by checking
    // DOM Level Mutex (bots_state) attribute.
    if (bots_state && bots_state ==
      appcompat.webdiff.Content.Actions.READY_TO_RUN) {
      console.log('Duplicate VisibilityChange Event');
      return;
    } else {
      this.updateDomState_(appcompat.webdiff.Content.Actions.READY_TO_RUN);
      var listenerFunc = function() {
        port.postMessage({
          action: appcompat.webdiff.Content.Actions.READY_TO_RUN,
          event: e.type, status: document.readyState,
          visibility: document.webkitVisibilityState});
      };
      goog.Timer.callOnce(goog.partial(listenerFunc, e, port), 5 * 1000, this);
    }
  }
  // Register created handler for webkitvisibilitychange event and notify
  // backgroundscript.
  goog.events.listenOnce(
      document, 'webkitvisibilitychange', handler, false, this);
  console.log('Registered for webkitvisibilitychange Event');
  this.updateDomState_(
      appcompat.webdiff.Content.Actions.REG_VISIBILITY_CHANGE_EVENT_DONE);
  port.postMessage({
    action:
    appcompat.webdiff.Content.Actions.REG_VISIBILITY_CHANGE_EVENT_DONE});
};


/**
* Function to handle WAIT Message.
* @param {Object} port A connected port to use to communicate with the
*     extension background page.
* @param {Object} msg A json object which represents the content of the
      message.
* @private
*/
appcompat.webdiff.Content.prototype.handleWaitMsg_ = function(port, msg) {
  console.log('Waiting');
  this.updateDomState_(appcompat.webdiff.Content.Actions.WAIT);
  // Let's create wait handler and register it to be called after given
  // wait time.
  var waitHandler_ = function() {
    this.updateDomState_(appcompat.webdiff.Content.Actions.READY_TO_RUN);
    var visibilityState = document.webkitVisibilityState ?
        document.webkitVisibilityState : 'visible';
    port.postMessage({
      action: appcompat.webdiff.Content.Actions.READY_TO_RUN,
      status: document.readyState,
      visibility: visibilityState});
  };
  this.waitTimer_ = goog.Timer.callOnce(waitHandler_,
                                        msg['seconds'] * 1000, this);
};


/**
* Function to handle OK_TO_INIT Message.
* @param {Object} port A connected port to use to communicate with the
*     extension background page.
* @param {Object} msg A json object which represents the content of the
      message.
* @private
*/
appcompat.webdiff.Content.prototype.handleOkToInitMsg_ = function(port, msg) {
  // DOM level mutex (bots_state) is only set once we get 'ok_to_init' from
  // background script.
  this.updateDomState_(appcompat.webdiff.Content.Actions.OK_TO_INIT);
  var visibilityState = document.webkitVisibilityState ?
      document.webkitVisibilityState : 'visible';
  port.postMessage({
    action: appcompat.webdiff.Content.Actions.READY_TO_RUN,
    visibility: visibilityState,
    status: document.readyState});
};


/**
* Function to handle EXTRACT_DATA Message.
* @param {Object} port A connected port to use to communicate with the
*     extension background page.
* @param {Object} msg A json object which represents the content of the
message.
* @private
*/
appcompat.webdiff.Content.prototype.handleExtractDataMsg_ =
    function(port, msg) {
  this.updateDomState_(appcompat.webdiff.Content.Actions.EXTRACT_DATA);
  // Let's clear the timer if any.
  if (this.waitTimer_) {
    goog.Timer.clear(this.waitTimer_);
  }
  var worker = new appcompat.webdiff.Content();
  worker.createNodesTable_();
  worker.createLayoutTable_();
  worker.sendDataToBackground_(port);
};


/**
* Function to handle WAIT_FOR_PRERENDER Message.
* @param {Object} port A connected port to use to communicate with the
*     extension background page.
* @param {Object} msg A json object which represents the content of the
message.
* @private
*/
appcompat.webdiff.Content.prototype.handleWaitForPrerenderMsg_ =
    function(port, msg) {
  this.updateDomState_(appcompat.webdiff.Content.Actions.WAIT_FOR_PRERENDER);
  console.log(appcompat.webdiff.Content.Actions.WAIT_FOR_PRERENDER);
  this.prerenderWaitTimer_ = goog.Timer.callOnce(
      goog.bind(appcompat.webdiff.Content.prerenderAction, this, false),
      msg['seconds'] * 1000);
};


/**
* Handler to process messages received from background script.
* @param {Object} port A connected port to use to communicate with the
*     extension background page.
* @param {Object} msg A json object which represents the content of the
      message.
* @private
*/
appcompat.webdiff.Content.prototype.messageProcessor_ = function(port, msg) {
  console.log(msg);
  switch (msg['action']) {
    case appcompat.webdiff.Content.Actions.OK_TO_INIT:
      this.handleOkToInitMsg_(port, msg);
      break;
    case appcompat.webdiff.Content.Actions.REG_VISIBILITY_CHANGE_EVENT:
      this.handleRegVisibilityChangeEventMsg_(port, msg);
      break;
    case appcompat.webdiff.Content.Actions.WAIT:
      this.handleWaitMsg_(port, msg);
      break;
    case appcompat.webdiff.Content.Actions.EXTRACT_DATA:
      this.handleExtractDataMsg_(port, msg);
      break;
    case appcompat.webdiff.Content.Actions.DATA_SENT:
      console.log('Data is sent.');
      this.updateDomState_(appcompat.webdiff.Content.Actions.CLOSE_TAB);
      port.postMessage({action: appcompat.webdiff.Content.Actions.CLOSE_TAB});
      break;
    case appcompat.webdiff.Content.Actions.WAIT_FOR_PRERENDER:
      this.handleWaitForPrerenderMsg_(port, msg);
      break;
    case appcompat.webdiff.Content.Actions.BYE:
      this.updateDomState_(appcompat.webdiff.Content.Actions.BYE);
      console.log(appcompat.webdiff.Content.Actions.BYE);
      break;
    case appcompat.webdiff.Content.Actions.DUPLICATE:
      console.log('Duplicate Content Script - Going to Shut up Now.');
      port.onMessage.removeListener(arguments.callee);
      console.log('Removed Listener.');
      break;
    case appcompat.webdiff.constants.ScreenshotActions.SCROLL:
      console.log('Trying to handle as a screenshot request.');
      this.screenshotContent_.processMessage(msg, port);
      break;
    default:
      console.log('Unidentified request');
  }
};


/**
 * Initiates communication with the extension background page and adds a
 * message listener to handle future messages.
 */
appcompat.webdiff.Content.prototype.initCommunication = function() {
  // Don't run this extension-specific code if this is run from webdriver.
  if (typeof(chrome) == 'undefined' || chrome.extension == undefined) {
    return;
  }

  // DOM Level Mutex to prevent multiple content scripts from running.
  var bots_state = document.body.getAttribute(
      appcompat.webdiff.Content.BOTS_STATE_ATTR);
  // If bots_state attribute is already present, that means some other
  // content script came before this one.
  if (bots_state) {
    // Duplicate content script injection, so return without doing anything.
    console.log('Duplicate ContentScript Injection Detected-DOM Level Mutex');
    return;
  } else {
    var port = chrome.extension.connect({name: 'chromeappcompat'});
    appcompat.webdiff.Content.connectionPort_ = port;
    this.screenshotContent_ =
        appcompat.webdiff.ScreenshotContent.getInstance();
    var listenerHandler = goog.bind(
        this.messageProcessor_, this, port);
    port.onMessage.addListener(listenerHandler);
    port.postMessage({action: appcompat.webdiff.Content.Actions.INIT});
  }
};


/**
 * Creates the node and layout tables.
 * @return {Object.<String, Array>} A dictionary of results from creating the
 *     tables.
 */
appcompat.webdiff.Content.prototype.createNodeAndLayoutTable = function() {
  this.createNodesTable_();
  this.createLayoutTable_()
  return { layout_table: this.layoutTable_,
        nodes_table: this.nodesTable_,
        dynamic_content_table: this.dynamicContentTable_};
};


/**
* An instance of this class.
* @type {appcompat.webdiff.Content}
* @private
*/
appcompat.webdiff.Content.instance_ = new appcompat.webdiff.Content();

appcompat.webdiff.Content.instance_.initCommunication();
