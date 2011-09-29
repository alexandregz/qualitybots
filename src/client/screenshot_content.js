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
 * @fileoverview Provides functionality for full webpage screenshots from the
 * content script side.
 *
 */


goog.provide('appcompat.webdiff.ScreenshotContent');

goog.require('appcompat.webdiff.constants');
goog.require('goog.dom');
goog.require('goog.iter.StopIteration');
goog.require('goog.style');


/**
 * ScreenshotContent class.
 * @constructor
 */
appcompat.webdiff.ScreenshotContent = function() {
  /**
   * An array of the elements that had the style changed for the screenshot.
   * @type {Array.<Element>}
   * @private
   */
  this.fixedElements_ = null;
};
goog.addSingletonGetter(appcompat.webdiff.ScreenshotContent);


/**
 * The size in pixels of a scrollbar in Chrome.
 * @const
 * @type {number}
 */
appcompat.webdiff.ScreenshotContent.SCROLL_BAR_SIZE = 15;


/**
 * Enable absolute positioning on all fixed-position elements.
 * @private
 */
appcompat.webdiff.ScreenshotContent.prototype.enableAbsolutePosition_ =
    function() {
  this.fixedElements_ = [];
  var nodes = goog.dom.getDocument().querySelectorAll('*');

  for (var i = 0; i < nodes.length; i++) {
    var nodePosition = goog.style.getComputedStyle(nodes[i], 'position');

    if (nodePosition == 'fixed') {
      this.fixedElements_.push(nodes[i]);
      goog.style.setStyle(nodes[i], 'position', 'absolute');
    }
  }
};


/**
 * Disable absolute positioning on elements that were changed from fixed
 * positioning.
 * @private
 */
appcompat.webdiff.ScreenshotContent.prototype.disableAbsolutePosition_ =
    function() {
  for (var i = 0, l = this.fixedElements_.length; i < l; ++i) {
    goog.style.setStyle(this.fixedElements_[i], 'position', 'fixed');
  }
};


/**
 * Process messages from background page.
 * @param {Object} message A message object that contains information from the
 *     background page.
 * @param {Object} port An initialized port that can be used to communicate
 *     with the background page.
 */
appcompat.webdiff.ScreenshotContent.prototype.processMessage =
    function(message, port) {
  if (message.action == appcompat.webdiff.constants.ScreenshotActions.SCROLL) {
    var responseData = this.scroll_(message.data.scrollXCount,
                                    message.data.scrollYCount);
    port.postMessage({action: responseData.msg, data: responseData});
  }
};


/**
 * Calculate the next position of the scrollbar
 * @param {number} scrollXCount The count of horizontal scroll iterations.
 * @param {number} scrollYCount The count of vertical scroll iterations.
 * @return {Object} An object containing the new scroll count and the document
 *   width and height.
 * @private
 */
appcompat.webdiff.ScreenshotContent.prototype.scroll_ = function(scrollXCount,
                                                                scrollYCount) {
  // TODO(user): Consider moving all the logic here to the background script.
  var visibleWidth = goog.dom.getWindow().innerWidth;
  if ((goog.dom.getWindow().innerHeight -
       appcompat.webdiff.ScreenshotContent.SCROLL_BAR_SIZE) <
      goog.dom.getDocument().body.scrollHeight) {
    visibleWidth -= appcompat.webdiff.ScreenshotContent.SCROLL_BAR_SIZE;
  }

  var visibleHeight = goog.dom.getWindow().innerHeight;
  if ((goog.dom.getWindow().innerWidth -
       appcompat.webdiff.ScreenshotContent.SCROLL_BAR_SIZE) <
      goog.dom.getDocument().body.scrollWidth) {
    visibleHeight -= appcompat.webdiff.ScreenshotContent.SCROLL_BAR_SIZE;
  }

  // Fix the element positioning on the initial run.
  if (scrollXCount == 0 && scrollYCount == 0) {
    this.enableAbsolutePosition_();
  }

  if (scrollYCount * visibleHeight >= goog.dom.getDocument().height) {
    scrollXCount++;
    scrollYCount = 0;
  }

  if (scrollXCount * visibleWidth < goog.dom.getDocument().width) {
    window.scrollTo(
        scrollXCount * visibleWidth,
        scrollYCount * visibleHeight);

    return {msg: appcompat.webdiff.constants.ScreenshotActions.ITERATION_DONE,
            scrollXCount: scrollXCount,
            scrollYCount: scrollYCount,
            visibleHeight: visibleHeight,
            visibleWidth: visibleWidth,
            docHeight: goog.dom.getDocument().height,
            docWidth: goog.dom.getDocument().width};
  } else {
    // Scrolling is finished, scroll to the top and undo element style changes.
    window.scrollTo(0, 0);
    this.disableAbsolutePosition_();
    return {msg: appcompat.webdiff.constants.ScreenshotActions.COMPLETE};
  }
};
