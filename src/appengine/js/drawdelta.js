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
 * @fileoverview This file contains the script to draw all the delta pixels on
 * a page's screenshot and show the delta information on mouseover.
 *
 */

goog.provide('appcompat.webdiff.LayoutDeltaUI');

goog.require('appcompat.webdiff.DeltaOverlay');
goog.require('goog.dom');
goog.require('goog.events');
goog.require('goog.fx.Dragger');
goog.require('goog.graphics');
goog.require('goog.json');
goog.require('goog.style');
goog.require('goog.ui.Component');
goog.require('goog.ui.ProgressBar');
goog.require('goog.ui.SplitPane');
goog.require('goog.ui.SplitPane.Orientation');



/**
 * UI for visualizing the delta between two pages.
 * @param {string} resultKey The encoded key of the delta entity to retrieve.
 * @param {number} layoutScore The layout score for the current page delta.
 * @constructor
 * @export
 */
appcompat.webdiff.LayoutDeltaUI = function(resultKey, layoutScore) {
  /**
   * The encoded key of the delta entity to retrieve.
   * @type {string}
   */
  this.resultKey = resultKey;

  /**
   * The layout score for the current page delta.
   * @type {number}
   */
  this.layoutScore = layoutScore;

  /**
   * The DIV node containing the progress bar.
   * @type {Element}
   */
  this.progressPane = null;

  /**
   * The progress bar for loading the delta.
   * @type {goog.ui.ProgressBar}
   */
  this.progressBar = null;

  /**
   * The DIV node to render the split pane that contains the two screen shots.
   * @type {Object}
   */
  this.splitpaneDiv = null;

  /**
   * The split pane object.
   * @type {goog.ui.SplitPane}
   */
  this.splitpane = null;

  /**
   * The split pane object.
   * @type {goog.math.Size}
   * @private
   */
  this.splitpaneSize_ = null;

  /**
   * Width of the canvas.
   * @type {number}
   */
  this.canvasWidth = 0;

  /**
   * Height of the canvas.
   * @type {number}
   */
  this.canvasHeight = 0;

  /**
   * The DIV node containing a screenshot of the test data and delta overlay.
   * @type {Node}
   */
  this.testDataDiv = null;

  /**
   * Dragger object for the test data contents.
   * @type {goog.fx.Dragger}
   */
  this.testDataDragger = null;

  /**
   * The DIV node containing a screenshot of the ref data and delta overlay.
   * @type {Node}
   */
  this.refDataDiv = null;

  /**
   * Dragger object for the ref data contents.
   * @type {goog.fx.Dragger}
   */
  this.refDataDragger = null;

  /**
   * The minimum left offset relative to the split pane container for the
   * draggable data contents.
   * @type {number}
   * @private
   */
  this.minDragLeft_ = 0;

  /**
   * The minimum top offset relative to the split pane container for the
   * draggable data contents.
   * @type {number}
   * @private
   */
  this.minDragTop_ = 0;

  /**
   * The overlay object for the difference delta view.
   * @type {appcompat.webdiff.DeltaOverlay}
   * @private
   */
  this.differenceOverlay_ = null;

  /**
   * The overlay object for the dynamic content delta view.
   * @type {appcompat.webdiff.DeltaOverlay}
   * @private
   */
  this.dynamicContentOverlay_ = null;
};


/**
 * The URL path to retrieve the delta.
 * @type {string}
 */
appcompat.webdiff.LayoutDeltaUI.LAYOUT_DELTA_PATH =
    '/delta/list';


/**
 * The URL path to retrieve the dynamic content delta.
 * @type {string}
 */
appcompat.webdiff.LayoutDeltaUI.LAYOUT_DYNAMIC_CONTENT_PATH =
    '/delta/dynamiccontent';


/**
 * The fill color to use when drawing points.
 * @type {goog.graphics.SolidFill}
 */
appcompat.webdiff.LayoutDeltaUI.RED_FILL =
    new goog.graphics.SolidFill('red', 0.25);


/**
 * The fill color to use when drawing points.
 * @type {goog.graphics.SolidFill}
 */
appcompat.webdiff.LayoutDeltaUI.YELLOW_FILL =
    new goog.graphics.SolidFill('yellow', 0.25);


/**
 * Returns whether the delta layout score is perfect.
 * @return {boolean} Whether the layout score is perfect.
 * @private
 */
appcompat.webdiff.LayoutDeltaUI.prototype.isPerfectLayoutScore_ = function() {
  return this.layoutScore == 100.0;
};


/**
 * Update the progress bar based on the delta retrieval progress.
 * @param {number} responseCount The number of responses we've received so far.
 * @param {number} totalCount The total number of responses that we expect.
 * @return {number} The progess percentage based on the given values.
 * @private
 */
appcompat.webdiff.LayoutDeltaUI.prototype.calculateProgressValue_ =
    function(responseCount, totalCount) {
  if (totalCount == 0) {
    return 100.0;
  } else {
    return (responseCount / totalCount * 100.0);
  }
};


/**
 * Update the progress bar based on the delta retrieval progress.
 * @private
 */
appcompat.webdiff.LayoutDeltaUI.prototype.updateProgressBar_ = function() {
  if (this.differenceOverlay_ != null && this.dynamicContentOverlay_ != null) {
    var responseCount;
    var totalCount;

    if (this.isPerfectLayoutScore_()) {
      responseCount = this.dynamicContentOverlay_.getResponseCount();
      totalCount = this.dynamicContentOverlay_.getTotalPieces();
    } else {
      responseCount = (this.differenceOverlay_.getResponseCount() +
                       this.dynamicContentOverlay_.getResponseCount());
      totalCount = (this.differenceOverlay_.getTotalPieces() +
                    this.dynamicContentOverlay_.getTotalPieces());
    }

    var progressValue = this.calculateProgressValue_(
        responseCount, totalCount);

    if (progressValue == 100.0) {
      goog.style.setStyle(this.progressPane, 'display', 'none');
    } else {
      this.progressBar.setValue(progressValue);
    }
  }
};


/**
 * Updates the split pane's size upon window resize event.
 * @private
 */
appcompat.webdiff.LayoutDeltaUI.prototype.updateSplitPaneSize_ = function() {
  var r = this.splitpane.getFirstComponentSize() / this.splitpaneSize_.width;

  var newWidth = document.body.clientWidth;
  var newHeight = window.innerHeight - 190;
  this.splitpaneSize_ = new goog.math.Size(newWidth, newHeight);
  this.splitpane.setSize(this.splitpaneSize_);

  this.splitpane.setFirstComponentSize(newWidth * r);
};


/**
 * Update drag limits on the split pane's first component width changes.
 * @param {Object} e The change event.
 * @private
 */
appcompat.webdiff.LayoutDeltaUI.prototype.updateLimits_ = function(e) {
  this.minDragLeft_ = e.target.getFirstComponentSize() - 6 - this.canvasWidth;
  this.minDragTop_ = this.splitpaneDiv.clientHeight - 6 - this.canvasHeight;

  if (this.minDragLeft_ > 0) {
    this.minDragLeft_ = 0;
  }

  if (this.minDragTop_ > 0) {
    this.minDragTop_ = 0;
  }
};


/**
 * Synchronizes the dragging of both components.
 * @param {goog.events.Event} e The drag event.
 * @private
 */
appcompat.webdiff.LayoutDeltaUI.prototype.syncDrag_ = function(e) {
  var target = e.target.target;  // The DOM element being dragged.
  var top = parseInt(target.style.top, 10);
  var left = parseInt(target.style.left, 10);

  // Check limits.
  if (top > 0) {
    top = 0;
  } else if (top < this.minDragTop_) {
    top = this.minDragTop_;
  }

  if (left > 0) {
    left = 0;
  } else if (left < this.minDragLeft_) {
    left = this.minDragLeft_;
  }

  target.style.top = top + 'px';
  target.style.left = left + 'px';

  // Sync the other one.
  if (target.id == 'testData') {
    var other = this.refDataDiv;
  } else {
    var other = this.testDataDiv;
  }

  other.style.top = target.style.top;
  other.style.left = target.style.left;
};


/**
 * Creates and initializes the UI.
 * @export
 */
appcompat.webdiff.LayoutDeltaUI.prototype.createUI = function() {
  // Progress bar.
  var progressBarDiv = goog.dom.createDom('div', {'id': 'progressBar'});
  this.progressPane = goog.dom.createDom(
      'div', {'id': 'progressPane'},
      goog.dom.createTextNode('Loading page delta...'), progressBarDiv);

  goog.dom.appendChild(document.body, this.progressPane);

  this.progressBar = new goog.ui.ProgressBar();
  this.progressBar.render(progressBarDiv);
  this.progressBar.setValue(0);

  // Split pane
  this.splitpaneDiv = goog.dom.getElement('dataFrames');
  this.splitpane = new goog.ui.SplitPane(
      new goog.ui.Component(), new goog.ui.Component(),
      goog.ui.SplitPane.Orientation.HORIZONTAL);

  this.splitpaneSize_ = new goog.math.Size(1000, 480);
  this.splitpane.setInitialSize(500);
  this.splitpane.setHandleSize(2);
  this.splitpane.decorate(this.splitpaneDiv);
  this.updateSplitPaneSize_();
  this.updateLimits_({target: this.splitpane});

  // Listen for change events.
  goog.events.listen(this.splitpane, goog.ui.Component.EventType.CHANGE,
                     goog.bind(this.updateLimits_, this));

  // Listen for window resize events.
  goog.events.listen(
      window, 'resize', goog.bind(this.updateSplitPaneSize_, this));

  // Draggers.
  this.testDataDiv = goog.dom.getElement('testData');
  this.testDataDragger = this.initDragger_(this.testDataDiv);

  this.refDataDiv = goog.dom.getElement('refData');
  this.refDataDragger = this.initDragger_(this.refDataDiv);
};


/**
 * Initializes a dragger for the screenshot.
 * @param {Element} element The element that the dragger should be attached to.
 * @return {goog.fx.Dragger} The resulting initialized dragger.
 * @private
 */
appcompat.webdiff.LayoutDeltaUI.prototype.initDragger_ = function(element) {
  var dragger = new goog.fx.Dragger(element, element);
  goog.events.listen(dragger, 'drag', goog.bind(this.syncDrag_, this));

  return dragger;
};


/**
 * Retrieves the delta data.
 * @param {string} deltaIndex A JSON-encoded string representing an array
 *     describing the delta data to query.
 * @param {string} dynamicContentIndex A JSON-encoded string representing an
 *     array describing the dynamic content data to query.
 * @export
 */
appcompat.webdiff.LayoutDeltaUI.prototype.retrieveData =
    function(deltaIndex, dynamicContentIndex) {
  this.differenceOverlay_ = new appcompat.webdiff.DeltaOverlay(
      appcompat.webdiff.LayoutDeltaUI.RED_FILL,
      /** @type {Array.<number>} */ (goog.json.parse(deltaIndex)),
      appcompat.webdiff.LayoutDeltaUI.LAYOUT_DELTA_PATH);
  this.dynamicContentOverlay_ = new appcompat.webdiff.DeltaOverlay(
      appcompat.webdiff.LayoutDeltaUI.YELLOW_FILL,
      /** @type {Array.<number>} */ (goog.json.parse(dynamicContentIndex)),
      appcompat.webdiff.LayoutDeltaUI.LAYOUT_DYNAMIC_CONTENT_PATH);

  // We don't need to fetch data if there is no difference.
  if (!this.isPerfectLayoutScore_()) {
    this.differenceOverlay_.retrieveDelta(
        this.resultKey, goog.bind(this.updateProgressBar_, this));
  }

  this.dynamicContentOverlay_.retrieveDelta(
      this.resultKey, goog.bind(this.updateProgressBar_, this));
};


/**
 * Renders the delta data.
 * @param {number} width The width of the delta.
 * @param {number} height The height of the delta.
 * @export
 */
appcompat.webdiff.LayoutDeltaUI.prototype.renderData =
    function(width, height) {
  this.canvasWidth = width;
  this.canvasHeight = height;

  this.dynamicContentOverlay_.renderDeltaOverlay(
      width, height);
  this.differenceOverlay_.renderDeltaOverlay(
      width, height);

  // Update the size settings after rendering; this allows dragging to work.
  this.updateSplitPaneSize_();
  this.updateLimits_({target: this.splitpane});
};
