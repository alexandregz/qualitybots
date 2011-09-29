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
 * @fileoverview Page specific scripts for displaying data for the comparison
 * of a specific page.
 *
 */

goog.provide('bots.dashboard.DetailPage');

goog.require('bots.dashboard.Constants');
goog.require('goog.Timer');
goog.require('goog.Uri');
goog.require('goog.dom');
goog.require('goog.events');
goog.require('goog.fx.Dragger');
goog.require('goog.graphics');
goog.require('goog.json');
goog.require('goog.net.XhrIo');
goog.require('goog.style');



/**
 * The detail page client for interacting with the detail page.
 * @constructor
 */
bots.dashboard.DetailPage = function() {
  /**
   * Dragger for the test screenshot.
   * @type {goog.fx.Dragger}
   */
  this.testDragger = null;

  /**
   * Dragger for the ref screenshot.
   * @type {goog.fx.Dragger}
   */
  this.refDragger = null;

  /**
   * Storage for the server response providing details.
   * @type {Object}
   */
  this.response = null;

  /**
   * List of element delta's used in overlay.
   * @type {Array}
   * @private
   */
  this.deltaTable_ = [];

  /**
   * List of server responses for differences of elements on the page.
   * @type {Array}
   * @private
   */
  this.deltaResponseList_ = [];

  /**
   * List of server responses for differences of dynamic content on the page.
   * @type {Array}
   * @private
   */
  this.dynamicResponseList_ = [];
};


/**
 * The ID of the frame that acts as a viewport for the test browser screenshot.
 * @type {string}
 */
bots.dashboard.DetailPage.prototype.TEST_FRAME_ID = 'testFrame';


/**
 * The ID of the test browser screenshot.
 * @type {string}
 */
bots.dashboard.DetailPage.prototype.TEST_SCREENSHOT_ID = 'testScreenshot';


/**
 * The ID of the container for the test browser screenshot.
 * @type {string}
 */
bots.dashboard.DetailPage.prototype.TEST_SCREENSHOT_CONTAINER_ID =
    'testData';


/**
 * The ID of the thumbnail of the test browser screenshot.
 * @type {string}
 */
bots.dashboard.DetailPage.prototype.TEST_THUMBNAIL_ID = 'testThumbnail';


/**
 * The ID of the frame that acts as a viewport for the ref browser screenshot.
 * @type {string}
 */
bots.dashboard.DetailPage.prototype.REF_FRAME_ID = 'refFrame';


/**
 * The ID of the ref browser screenshot.
 * @type {string}
 */
bots.dashboard.DetailPage.prototype.REF_SCREENSHOT_ID = 'refScreenshot';


/**
 * The ID of the container of the ref browser screenshot.
 * @type {string}
 */
bots.dashboard.DetailPage.prototype.REF_SCREENSHOT_CONTAINER_ID =
    'refData';


/**
 * The ID of the label that shows the percent score of the comparison.
 * @type {string}
 */
bots.dashboard.DetailPage.prototype.SCORE_PERCENT_ID = 'scorePercent';


/**
 * The ID of the label that shows the test browser version.
 * @type {string}
 */
bots.dashboard.DetailPage.prototype.TEST_BROWSER_LABEL_ID = 'testBrowserLabel';


/**
 * The ID of the label that shows the ref browser version.
 * @type {string}
 */
bots.dashboard.DetailPage.prototype.REF_BROWSER_LABEL_ID = 'refBrowserLabel';


/**
 * The ID of the container for the test browser version label.
 * @type {string}
 */
bots.dashboard.DetailPage.prototype.TEST_BROWSER_LABEL_CONTAINER_ID =
    'testBrowserLabelContainer';


/**
 * The ID of the container for the ref browser version label.
 * @type {string}
 */
bots.dashboard.DetailPage.prototype.REF_BROWSER_LABEL_CONTAINER_ID =
    'refBrowserLabelContainer';


/**
 * Label showing information about an element in the test browser.
 * @type {string}
 */
bots.dashboard.DetailPage.prototype.TEST_ELEMENT_DATA_ID = 'testElementData';


/**
 * Label showing information about an element in the ref browser.
 * @type {string}
 */
bots.dashboard.DetailPage.prototype.REF_ELEMENT_DATA_ID = 'refElementData';


/**
 * The ID of the link to start the element overlay process.
 * @type {string}
 */
bots.dashboard.DetailPage.prototype.OVERLAY_LINK_ID = 'overlayLink';


/**
 * The ID of the label that shows the url under test.
 * @type {string}
 */
bots.dashboard.DetailPage.prototype.URL_LABEL_ID = 'urlLabel';


/**
 * The ID of the label that shows the total number of elements.
 * @type {string}
 */
bots.dashboard.DetailPage.prototype.TOTAL_ELEMENTS_ID = 'totalElements';


/**
 * The ID of the label that shows the number of matched elements.
 * @type {string}
 */
bots.dashboard.DetailPage.prototype.MATCHED_ELEMENTS_ID = 'matchedElements';


/**
 * The ID of the label that shows the number of differing elements.
 * @type {string}
 */
bots.dashboard.DetailPage.prototype.DIFFERING_ELEMENTS_ID = 'differingElements';


/**
 * The width of the side panel with detailed information.
 * @type {number}
 */
bots.dashboard.DetailPage.prototype.DETAIL_PANEL_WIDTH = 300;


/**
 * The width of the side panel with detailed information.
 * @type {number}
 */
bots.dashboard.DetailPage.prototype.SCREENSHOT_TOP = 98;


/**
 * The offset of the ref screenshot from the test screenshot
 * @type {number}
 */
bots.dashboard.DetailPage.prototype.REF_SCREENSHOT_OFFSET = 12;


/**
 * The offset of the screenshots from the top of the screenshot frame.
 * @type {number}
 */
bots.dashboard.DetailPage.prototype.SCREENSHOT_TOP_OFFSET = 16;


/**
 * The margin
 * The width of the side panel with detailed information.
 * @type {number}
 */
bots.dashboard.DetailPage.prototype.SCREENSHOT_WIDTH_MARGIN = 28;


/**
 * Handles data from the server for the detail page request.
 * @param {Object} response Response from the server.
 * @export
 */
bots.dashboard.DetailPage.prototype.handleDetailData = function(response) {
  var json_response = response.target.getResponseJson();
  if (json_response['status'] == 'success') {
    var resultDetails = json_response['result_details'];
    var comparisonContainer = goog.dom.getElement('comparisonContainer');

    this.displayScreenshot_(this.TEST_SCREENSHOT_ID,
                            resultDetails['test_screenshot_key']);
    this.displayScreenshot_(this.TEST_THUMBNAIL_ID,
                            resultDetails['test_screenshot_key']);
    this.displayScreenshot_(this.REF_SCREENSHOT_ID,
                            resultDetails['ref_screenshot_key']);

    var scorePercent = goog.dom.getElement(this.SCORE_PERCENT_ID);
    goog.dom.setProperties(scorePercent, {
        'innerHTML': Math.floor(resultDetails['score']) + '%'});

    var testLabel = goog.dom.getElement(this.TEST_BROWSER_LABEL_ID);
    goog.dom.setProperties(testLabel, {'innerHTML': 'Chrome ' +
        resultDetails['test_browser_version']});

    var refLabel = goog.dom.getElement(this.REF_BROWSER_LABEL_ID);
    goog.dom.setProperties(refLabel, {'innerHTML': 'Chrome ' +
        resultDetails['ref_browser_version']});

    var urlLabel = goog.dom.getElement(this.URL_LABEL_ID);
    goog.dom.setProperties(urlLabel, {'innerHTML': resultDetails['url']});

    var totalElements = goog.dom.getElement(this.TOTAL_ELEMENTS_ID);
    goog.dom.setProperties(totalElements, {
        'innerHTML': resultDetails['test_total_elem_count'] +
        ' elements total'});

    // Matched elements is calculated by # total - # differing.
    var matchedElements = goog.dom.getElement(this.MATCHED_ELEMENTS_ID);
    goog.dom.setProperties(matchedElements, {
        'innerHTML': (resultDetails['test_total_elem_count'] -
            resultDetails['test_unmatched_elem_count']) +
            ' matched'});

    var differingElements = goog.dom.getElement(this.DIFFERING_ELEMENTS_ID);
    goog.dom.setProperties(differingElements, {
        'innerHTML': resultDetails['test_unmatched_elem_count'] +
            ' need investigation'});

    this.initScreenshotContainers_();
    goog.style.setStyle(comparisonContainer, 'display', 'block');

    var overlayLink = goog.dom.getElement(this.OVERLAY_LINK_ID);
    goog.events.listen(overlayLink, goog.events.EventType.CLICK,
        goog.bind(this.startOverlay, this));

    this.response = resultDetails;
  }
};


/**
 * Displays a screenshot from the server using the specified key and element id.
 * @param {string} id The id of the element to update.
 * @param {string} key The key of the screenshot to display.
 * @private
 */
bots.dashboard.DetailPage.prototype.displayScreenshot_ = function(id, key) {
  var screenshotElement = goog.dom.getElement(id);
  goog.dom.setProperties(screenshotElement,
      {'src': bots.dashboard.Constants.SCREENSHOT_URL + '?' +
              bots.dashboard.Constants.SCREENSHOT_URL_KEY_PARAM + '=' +
              key});
};


/**
 * Inits a drag listener for the specified element.
 * @param {Element} element The element to listen for.
 * @return {goog.fx.Dragger} Object that handles dragging for the element.
 */
bots.dashboard.DetailPage.prototype.initDragger = function(element) {
  var dragger = new goog.fx.Dragger(element, element);
  goog.events.listen(dragger, 'drag', goog.bind(this.syncDrag, this));

  return dragger;
};


/**
 * Synchronizes the dragging of both screenshots..
 * @param {goog.events.Event} e The drag event.
 */
bots.dashboard.DetailPage.prototype.syncDrag = function(e) {
  var target = e.target.target;  // The DOM element being dragged.
  var top = parseInt(target.style.top, 10);
  var left = parseInt(target.style.left, 10);

  var maxDragTop = goog.global.document.body.clientHeight;
  // Check limits.
  if (top > 0) {
    top = 0;
  } else if (top > maxDragTop) {
    top = maxDragTop;
  }

  var maxDragLeft = goog.global.document.body.clientWidth -
      this.DETAIL_PANEL_WIDTH;

  if (left > 0) {
    left = 0;
  } else if (left > maxDragLeft) {
    left = maxDragLeft;
  }

  target.style.top = top + 'px';
  target.style.left = left + 'px';

  // Sync the other one.
  if (target.id == this.TEST_SCREENSHOT_CONTAINER_ID) {
    var other = goog.dom.getElement(this.REF_SCREENSHOT_CONTAINER_ID);
  } else {
    var other = goog.dom.getElement(this.TEST_SCREENSHOT_CONTAINER_ID);
  }

  other.style.top = target.style.top;
  other.style.left = target.style.left;
};


/**
 * Synchronizes the dragging of both components.
 * @private
 */
bots.dashboard.DetailPage.prototype.initScreenshotContainers_ = function() {
  this.testDragger = this.initDragger(goog.dom.getElement(
      this.TEST_SCREENSHOT_CONTAINER_ID));
  this.refDragger = this.initDragger(goog.dom.getElement(
      this.REF_SCREENSHOT_CONTAINER_ID));

  this.updateScreenshotContainers_();
  goog.events.listen(window, goog.events.EventType.RESIZE,
                     goog.bind(this.updateScreenshotContainers_, this));
};


/**
 * Updates the size and placement of the the screenshot containers.
 * @private
 */
bots.dashboard.DetailPage.prototype.updateScreenshotContainers_ = function() {
  var testFrame = goog.dom.getElement(this.TEST_FRAME_ID);
  var testWidth = (goog.global.document.body.clientWidth -
                   this.DETAIL_PANEL_WIDTH - this.SCREENSHOT_WIDTH_MARGIN) / 2;
  var testHeight = goog.global.document.body.clientHeight -
                   this.SCREENSHOT_TOP - this.SCREENSHOT_TOP_OFFSET;
  testFrame.style.width = testWidth;
  testFrame.style.height = testHeight;

  var refFrame = goog.dom.getElement(this.REF_FRAME_ID);
  refFrame.style.width = testWidth;
  refFrame.style.left = testWidth + this.REF_SCREENSHOT_OFFSET;
  refFrame.style.height = testHeight;
};


/**
 * Kicks off the element overlay process.
 * @export
 */
bots.dashboard.DetailPage.prototype.startOverlay = function() {
  var delta_index = goog.json.parse(
      this.response['delta_index']);
  var dynamic_content_index = goog.json.parse(
      this.response['dynamic_content_index']);
  var totalRequests = delta_index.length + dynamic_content_index.length;

  // Update the status and disable the overlay link from being clicked again.
  var overlayLink = goog.dom.getElement(this.OVERLAY_LINK_ID);
  goog.dom.setProperties(overlayLink,
      {'innerHTML': 'Connecting...', 'class': 'overlayLink'});
  goog.events.removeAll(overlayLink);

  // Send out requests for all the element differences.
  for (var i = 0; i < delta_index.length; i++) {
    goog.net.XhrIo.send(
        bots.dashboard.Constants.DELTA_URL + '?' +
        bots.dashboard.Constants.DELTA_KEY_PARAM + '=' +
        urlParams.getQueryData().get('page_delta_key') + '&' +
        bots.dashboard.Constants.DELTA_DELTAONLY_PARAM + '=true&' +
        bots.dashboard.Constants.DELTA_INDEX_PARAM + '=' + delta_index[i],
        goog.bind(this.saveOverlayResponse_, this, totalRequests, false),
        'GET');
   }

  // Send out requests for all the dynamic content differences.
  for (var j = 0; j < dynamic_content_index.length; j++) {
    goog.net.XhrIo.send(
        bots.dashboard.Constants.DELTA_DYNAMICCONTENT_URL + '?' +
        bots.dashboard.Constants.DELTA_KEY_PARAM + '=' +
        urlParams.getQueryData().get('page_delta_key') + '&' +
        bots.dashboard.Constants.DELTA_DELTAONLY_PARAM + '=true&' +
        bots.dashboard.Constants.DELTA_INDEX_PARAM + '=' +
        dynamic_content_index[j],
        goog.bind(this.saveOverlayResponse_, this, totalRequests, true),
        'GET');
   }
};


/**
 * Saves the server response for an overlay request.
 * @param {number} expectedCount The total number of responses expected.
 * @param {boolean} dynamicContentFlag Whether the response is for
 *   dynamic content.
 * @param {Object} response The response from the server.
 * @private
 */
bots.dashboard.DetailPage.prototype.saveOverlayResponse_ = function(
    expectedCount, dynamicContentFlag, response) {
  if (dynamicContentFlag) {
    this.dynamicResponseList_.push(response.target.getResponseJson());
  } else {
    this.deltaResponseList_.push(response.target.getResponseJson());
  }

  var overlayLink = goog.dom.getElement(this.OVERLAY_LINK_ID);
  var currentCount = this.deltaResponseList_.length +
      this.dynamicResponseList_.length;

  if (currentCount == expectedCount) {
    this.renderOverlay_('refData', 'refScreenshot', this.deltaResponseList_,
        this.dynamicResponseList_);
    this.renderOverlay_('testData', 'testScreenshot', this.deltaResponseList_,
        this.dynamicResponseList_);
    overlayLink.innerHTML = 'Overlay Enabled';
  } else {
    overlayLink.innerHTML = 'Loading (' +
        (Math.floor(100 * currentCount / expectedCount)) + '%)';
  }
};


/**
 * Renders a list of overlay response in the specified elements.
 * @param {string} dataId The ID of the div container for the applicable
 *   screenshot information.
 * @param {string} screenshotId The ID of the applicable screenshot.
 * @param {Array} deltaResults A list of the element differences.
 * @param {Array} dynamicResults A list of the dynamic content differences.
 * @private
 */
bots.dashboard.DetailPage.prototype.renderOverlay_ = function(
    dataId, screenshotId, deltaResults, dynamicResults) {
  var dataDiv = goog.dom.getElement(dataId);
  var screenshot = goog.dom.getElement(screenshotId);
  var graphicsContext = goog.graphics.createSimpleGraphics(
      screenshot.clientWidth, screenshot.clientHeight);

  var redFillColor = new goog.graphics.SolidFill('red', 0.25);
  var yellowFillColor = new goog.graphics.SolidFill('yellow', 0.25);
  this.renderResults_(graphicsContext, deltaResults, redFillColor);
  this.renderResults_(graphicsContext, dynamicResults, yellowFillColor);

  var canvas = this.createCanvas_(dataDiv, graphicsContext);
  this.addCanvasListeners_(canvas);
};


/**
 * Render a specific set of results in the provided graphicsContext.
 * @param {goog.graphics.AbstractGraphics} graphicsContext The graphics context
 *   to draw in.
 * @param {Array} diffs A list of diffs to render.
 * @param {goog.graphics.SolidFill} fillColor The color to use when drawing.
 * @private
 */
bots.dashboard.DetailPage.prototype.renderResults_ = function(
    graphicsContext, diffs, fillColor) {
  for (var i = 0; i < diffs.length; i++) {
    var diff = diffs[i];
    for (var j = 0; j < diff.length; j++) {
      var x = diff[j][0];
      var y = diff[j][1];

      graphicsContext.drawRect(x, y, 1, 1, null, fillColor);

     if (!this.deltaTable_[y]) {
          this.deltaTable_[y] = [];
     }
     this.deltaTable_[y][x] = {
       'xPath1': diff[i][2],
       'xPath2': diff[i][3]
     };
   }
  }
};


/**
 * Creates a canvas to draw the overlay in a graphicsContext onto.
 * @param {Element} canvasParent The element to add the canvas to.
 * @param {goog.graphics.AbstractGraphics} graphicsContext The graphics context
 *   to draw in.
 * @return {Element} The canvas element.
 * @private
 */
bots.dashboard.DetailPage.prototype.createCanvas_ = function(
    canvasParent, graphicsContext) {
  var canvas = goog.dom.createDom(goog.dom.TagName.DIV,
      {'class': 'overlayCanvas'});
  goog.style.setStyle(canvas, 'width', canvasParent.clientWidth);
  goog.style.setStyle(canvas, 'height', canvasParent.clientHeight);
  goog.dom.appendChild(canvasParent, canvas);
  graphicsContext.render(canvas);
  return canvas;
};


/**
 * Adds mouseover and mouseout listeners to an overlay canvas.
 * @param {Element} canvas The canvas element to put listeners on.
 * @private
 */
bots.dashboard.DetailPage.prototype.addCanvasListeners_ = function(canvas) {
  goog.events.listen(
      canvas, goog.events.EventType.MOUSEMOVE,
      goog.bind(this.showElementInfo_, this));
  goog.events.listen(
      canvas, goog.events.EventType.MOUSEOUT,
      goog.bind(this.hideElementLabels_, this));
};


/**
 * Hides the element labels containing information about an overlay element.
 * @private
 */
bots.dashboard.DetailPage.prototype.hideElementLabels_ = function() {
  this.resetElementLabel_(this.TEST_BROWSER_LABEL_CONTAINER_ID,
                          this.TEST_ELEMENT_DATA_ID);
  this.resetElementLabel_(this.REF_BROWSER_LABEL_CONTAINER_ID,
                          this.REF_ELEMENT_DATA_ID);
};


/**
 * Resets an overlay element label to it's original state.
 * @param {string} labelContainerID The id of the label container.
 * @param {string} elementDataID The id of element data label.
 * @private
 */
bots.dashboard.DetailPage.prototype.resetElementLabel_ = function(
    labelContainerID, elementDataID) {
  var testBrowserLabel = goog.dom.getElement(labelContainerID);
  goog.dom.setProperties(testBrowserLabel, {'class': 'browserLabelContainer'});
  var testElementData = goog.dom.getElement(elementDataID);
  goog.dom.setProperties(testElementData, {'innerHTML': ''});
};


/**
 * Shows information about an element at a specified x, y coordinate.
 * @param {MouseEvent} e The mouse events to derive coordinates from.
 * @private
 */
bots.dashboard.DetailPage.prototype.showElementInfo_ = function(e) {
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

  if (this.deltaTable_[y] && this.deltaTable_[y][x]) {
    this.addElementLabel_(this.TEST_BROWSER_LABEL_CONTAINER_ID,
        this.TEST_ELEMENT_DATA_ID,
        this.parseXPath(this.deltaTable_[y][x]['xPath1']));
    this.addElementLabel_(this.REF_BROWSER_LABEL_CONTAINER_ID,
        this.REF_ELEMENT_DATA_ID,
        this.parseXPath(this.deltaTable_[y][x]['xPath2']));
  }
};


/**
 * Creates a label describing an overlay element.
 * @param {string} labelContainerID The id of label container to work with.
 * @param {string} elementDataID The id of the element label to populate.
 * @param {string} xPathString The formatted XPath string of the element
 *   being labeled.
 * @private
 */
bots.dashboard.DetailPage.prototype.addElementLabel_ = function(
    labelContainerID, elementDataID, xPathString) {
  var testBrowserLabel = goog.dom.getElement(labelContainerID);
  var testElementData = goog.dom.getElement(elementDataID);
  goog.dom.setProperties(testBrowserLabel,
      {'class': 'expandedBrowserLabelContainer'});
  goog.dom.setProperties(testElementData, {
      'innerHTML': 'Test Browser Element XPath: '});

  var xPathElement = goog.dom.createDom(goog.dom.TagName.SPAN,
    {'class': 'greyText', 'innerHTML': xPathString});
  goog.dom.appendChild(testElementData, xPathElement);
};


/**
 * Parses an xPath object and returns a formatted string.
 * @param {Object} xPathObj A dictionary XPath object.
 * @return {string} The formatted xpath string.
 */
bots.dashboard.DetailPage.prototype.parseXPath = function(xPathObj) {
  var xpathString = xPathObj['p'] + ' ' + xPathObj['w'] + 'x' + xPathObj['h'];

  // Replace the ~'s with nth-child, to revert earlier data compression.
  return xpathString.replace(/~/g, 'nth-child');
};


/**
 * Fetches the detail page data and sends it to the detail page client.
 * @param {string} deltaKey The key for the page delta data on the server.
 * @export
 */
function initDetailPageData(deltaKey) {
  goog.net.XhrIo.send('/results/details?page_delta_key=' + deltaKey,
      goog.bind(detailPageClient.handleDetailData, detailPageClient), 'GET');
}

var urlParams = goog.Uri.parse(window.location.toString());
var detailPageClient = new bots.dashboard.DetailPage();

// Queue up getting the detail page data from the server.
goog.Timer.callOnce(goog.bind(
    initDetailPageData, undefined,
    urlParams.getQueryData().get('page_delta_key')), 0);

