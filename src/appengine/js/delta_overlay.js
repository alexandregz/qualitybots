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

goog.provide('appcompat.webdiff.DeltaOverlay');
goog.provide('appcompat.webdiff.Xpath');

goog.require('appcompat.webdiff.BasicCommManager');
goog.require('goog.dom');
goog.require('goog.events');
goog.require('goog.graphics');
goog.require('goog.json');


/**
 * An XPath object used for storing XPath information.
 * @constructor
 */
appcompat.webdiff.Xpath = function() {
  /** @type {*} */
  this.p;

  /** @type {*} */
  this.h;

  /** @type {*} */
  this.w;
};


/**
 * UI for visualizing the delta between two pages.
 * @param {goog.graphics.SolidFill} fillColor The color to use when drawing the
 *     delta overlay.
 * @param {Array.<number>} index An array containing a list of the indices that
 *     have data for this overlay.
 * @param {string} layoutUrl The URL to query for layout information.
 * @constructor
 */
appcompat.webdiff.DeltaOverlay = function(fillColor, index, layoutUrl) {
  /**
   * Counter of how many responses have been received.
   * @type {number}
   * @private
   */
  this.responseCount_ = 0;

  /**
   * An instance of goog.graphics.AbstractGraphics that draws the delta pixels.
   * @type {goog.graphics.AbstractGraphics}
   * @private
   */
  this.graphicsContext_ = null;

  /**
   * The DIV node containing a screenshot of the test data and delta overlay.
   * @type {Node}
   * @private
   */
  this.testDataDiv_ = goog.dom.getElement('testData');

  /**
   * The DIV node containing a screenshot of the ref data and delta overlay.
   * @type {Node}
   * @private
   */
  this.refDataDiv_ = goog.dom.getElement('refData');

  /**
   * The DIV node for drawing the overlay on the test data screenshot.
   * @type {Node}
   * @private
   */
  this.testCanvas_ = null;

  /**
   * The DIV node for drawing the overlay on the reference data screenshot.
   * @type {Node}
   * @private
   */
  this.refCanvas_ = null;

  /**
   * Table containing the indices to query for delta information.
   * @type {Array.<number>}
   * @private
   */
  this.deltaIndex_ = index;

  /**
   * Table containing node information of the DOM element at each pixel from the
   * data received from two browsers.
   * @type {Array.<Array.<Object>>}
   * @private
   */
  this.deltaTable_ = [];

  /**
   * The URL to use to query for delta information.
   * @type {string}
   * @private
   */
  this.deltaLayoutUrl_ = layoutUrl;

  /**
   * The fill color to use when drawing points.
   * @type {goog.graphics.SolidFill}
   * @private
   */
  this.fillColor_ = fillColor;

  /**
   * The data responses from the server for delta rendering.
   * @type {Array.<string>}
   * @private
   */
  this.responseList_ = [];

  /**
   * A callback function that will be called when data retrieval is complete.
   * @type {Function}
   * @private
   */
  this.retrievalCallback_ = null;

  /**
   * A function to call after each delta piece is loaded.
   * @type {Function}
   * @private
   */
  this.progressFunction_ = null;

  /**
   * The DIV node that shows information about the DOM element at that pixel
   * from the test browser.
   * @type {Node}
   * @private
   */
  this.testElementInfo_ = goog.dom.getElement('testElementInfo');

  /**
   * The DIV node that shows information about the DOM element at that pixel
   * from the reference browser.
   * @type {Node}
   * @private
   */
  this.refElementInfo_ = goog.dom.getElement('refElementInfo');

  /**
   * The DIV node that shows the current coordinates.
   * @type {Node}
   * @private
   */
  this.pixelCoords_ = goog.dom.getElement('pixelCoords');
};


/**
 * Sends out requests to retrieve the delta from the server.
 * @param {string} resultKey The encoded key of the delta entity to retrieve.
 * @param {Function} progressFunction A function to call after each delta
 *     piece is processed.
 */
appcompat.webdiff.DeltaOverlay.prototype.retrieveDelta =
    function(resultKey, progressFunction) {
  this.progressFunction_ = progressFunction;

  for (var i = 0; i < this.deltaIndex_.length; i++) {
    var query = {
      'key': resultKey,
      'deltaonly': 'true',
      'i': this.deltaIndex_[i]
    };

    appcompat.webdiff.BasicCommManager.send(
        this.deltaLayoutUrl_, goog.bind(this.saveDeltaData_, this),
        'GET', query);
  }

  // Ensure the progress function is called even if the deltaIndex is empty.
  if (this.progressFunction_ != null) {
    this.progressFunction_();
  }
};


/**
 * Returns the number of responses that have been retrieved for this overlay.
 * @return {number} The number of responses that have been retrieved.
 */
appcompat.webdiff.DeltaOverlay.prototype.getResponseCount = function() {
  return this.responseCount_;
};

/**
 * Returns the total number of pieces for this overlay.
 * @return {number} The total number of pieces.
 */
appcompat.webdiff.DeltaOverlay.prototype.getTotalPieces = function() {
  return this.deltaIndex_.length;
};

/**
 * Returns whether the retrieval process is complete.
 * @return {boolean} Whether the retrieval process is complete.
 */
appcompat.webdiff.DeltaOverlay.prototype.isRetrievalComplete = function() {
  return (this.responseCount_ == this.deltaIndex_.length);
};


/**
 * Saves the delta data from the server response so that it can be rendered.
 * @param {string} response A JSON string containing a list of the delta pixels.
 * @private
 */
appcompat.webdiff.DeltaOverlay.prototype.saveDeltaData_ = function(response) {
  this.responseCount_++;
  this.responseList_.push(response);

  if (this.progressFunction_ != null) {
    this.progressFunction_();
  }

  if (this.isRetrievalComplete() && this.retrievalCallback_ != null) {
    this.retrievalCallback_();
  }
};


/**
 * Draws all the delta points received from the server.
 * @param {number} width The width of the deltaOverlay.
 * @param {number} height The height of the deltaOverlay.
 */
appcompat.webdiff.DeltaOverlay.prototype.renderDeltaOverlay =
    function(width, height) {
  this.graphicsContext_ = goog.graphics.createSimpleGraphics(
      width, height);

  if (this.isRetrievalComplete()) {
    this.drawDeltaPoints_();
    this.renderOverlays_(width, height);
  } else {
    this.retrievalCallback_ = function() {
      this.drawDeltaPoints_();
      this.renderOverlays_(width, height);
    };
  }
};


/**
 * Draws all the overlay points contained in the response JSON string.
 * @private
 */
appcompat.webdiff.DeltaOverlay.prototype.drawDeltaPoints_ = function() {
  var dataString = this.responseList_.pop();
  while (dataString != undefined) {
    var dataList = goog.json.parse(dataString);

    for (var i = 0; i < dataList.length; i++) {
      var x = parseInt(dataList[i][0], 10);
      var y = parseInt(dataList[i][1], 10);

      this.drawPoint_(x, y);

      if (!this.deltaTable_[y]) {
        this.deltaTable_[y] = [];
      }

      this.deltaTable_[y][x] = {
        'xPath1': dataList[i][2],
        'xPath2': dataList[i][3]
      };
    }

    dataString = this.responseList_.pop();
  }
};


/**
 * Draws a point at the given (x, y) coordinate on the canvas.
 * @param {number} x The x-coordinate to draw the point.
 * @param {number} y The y-coordinate to draw the point.
 * @private
 */
appcompat.webdiff.DeltaOverlay.prototype.drawPoint_ =
    function(x, y) {
  this.graphicsContext_.drawRect(x, y, 1, 1, null, this.fillColor_);
};


/**
 * Renders the delta overlay on both sides.
 * @param {number} width The width of the deltaOverlay.
 * @param {number} height The height of the deltaOverlay.
 * @private
 */
appcompat.webdiff.DeltaOverlay.prototype.renderOverlays_ =
    function(width, height) {
  this.renderTestOverlay_(width, height);
  this.renderReferenceOverlay_();

  this.setupCanvasEvents_(this.testCanvas_);
  this.setupCanvasEvents_(this.refCanvas_);
};


/**
 * Creates and renders the test overlay.
 * @param {number} width The width of the deltaOverlay.
 * @param {number} height The height of the deltaOverlay.
 * @private
 */
appcompat.webdiff.DeltaOverlay.prototype.renderTestOverlay_ =
    function(width, height) {
  this.testCanvas_ = goog.dom.createDom('div', {'className': 'canvas'});
  goog.style.setStyle(this.testCanvas_, 'width', width);
  goog.style.setStyle(this.testCanvas_, 'height', height);
  goog.dom.appendChild(this.testDataDiv_, this.testCanvas_);
  this.graphicsContext_.render(this.testCanvas_);
};


/**
 * Creates and renders the reference overlay.
 * @private
 */
appcompat.webdiff.DeltaOverlay.prototype.renderReferenceOverlay_ = function() {
  this.refCanvas_ = this.testCanvas_.cloneNode(true);
  goog.dom.appendChild(this.refDataDiv_, this.refCanvas_);
};


/**
 * Setup event listening for the given canvas object.
 * @param {Node} canvas The canvas to setup events for.
 * @private
 */
appcompat.webdiff.DeltaOverlay.prototype.setupCanvasEvents_ =
    function(canvas) {
  goog.events.listen(
      canvas, goog.events.EventType.MOUSEMOVE,
      this.showElementInfo_, false, this);
};


/**
 * If the provided pixel coordinates correspond with a delta pixel, return the
 * information about the element on that pixel from the test browser.
 * @param {number} x The x coordinate of the pixel to return element
 *     information for.
 * @param {number} y The y coordinate of the pixel to return element
 *     information for.
 * @return {string} A string describing the DOM information at the given pixel
 *     coordinates.
 * @private
 */
appcompat.webdiff.DeltaOverlay.prototype.getTestElementInfo_ = function(x, y) {
  if (this.deltaTable_[y] && this.deltaTable_[y][x]) {
    return (this.deltaTable_[y][x].xPath1.p + ' ' +
            this.deltaTable_[y][x].xPath1.w + 'x' +
            this.deltaTable_[y][x].xPath1.h);
  } else {
    return '';
  }
};


/**
 * If the provided pixel coordinates correspond with a delta pixel, return the
 * information about the element on that pixel from the reference browser.
 * @param {number} x The x coordinate of the pixel to return element
 *     information for.
 * @param {number} y The y coordinate of the pixel to return element
 *     information for.
 * @return {string} A string describing the DOM information at the given pixel
 *     coordinates.
 * @private
 */
appcompat.webdiff.DeltaOverlay.prototype.getReferenceElementInfo_ =
    function(x, y) {
  if (this.deltaTable_[y] && this.deltaTable_[y][x]) {
    return (this.deltaTable_[y][x].xPath2.p + ' ' +
            this.deltaTable_[y][x].xPath2.w + 'x' +
            this.deltaTable_[y][x].xPath2.h);
  } else {
    return '';
  }
};


/**
 * The mouseover event handler. If the current pixel is a delta pixel, display
 * information about the element on that pixel from both browsers.
 * @param {Object} e The event object.
 * @private
 */
appcompat.webdiff.DeltaOverlay.prototype.showElementInfo_ = function(e) {
  var draggerDiv = e.target.parentNode;

  if (draggerDiv.style.left) {
    var x = e.offsetX - parseInt(draggerDiv.style.left, 10);
  } else {
    var x = e.offsetX;
  }

  if (draggerDiv.style.top) {
    var y = e.offsetY - parseInt(draggerDiv.style.top, 10);
  } else {
    var y = e.offsetY;
  }

  // Only change the info if it isn't curent.
  var coords = x + ', ' + y;

  if (this.pixelCoords_.innerHTML != coords) {
    this.pixelCoords_.innerHTML = coords;

    this.testElementInfo_.innerHTML = this.getTestElementInfo_(x, y);
    this.refElementInfo_.innerHTML = this.getReferenceElementInfo_(x, y);
  } else if (this.testElementInfo_.innerHTML == '') {
    this.testElementInfo_.innerHTML = this.getTestElementInfo_(x, y);
  } else if (this.refElementInfo_.innerHTML == '') {
    this.refElementInfo_.innerHTML = this.getReferenceElementInfo_(x, y);
  }
};
