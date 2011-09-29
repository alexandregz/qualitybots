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
 * @fileoverview File for managing the urls a user has requested Bots to test,
 * and displaying them on the page.
 *
 */


goog.provide('bots.dashboard.UrlManager');

goog.require('bots.dashboard.BrowserSelection');
goog.require('bots.dashboard.Constants');
goog.require('bots.dashboard.UrlPopup');
goog.require('goog.Uri');
goog.require('goog.dom');
goog.require('goog.net.XhrIo');
goog.require('goog.string');
goog.require('goog.style');



/**
 * Constructor for the Url Manager class, this class keeps track of the URL's
 * the user has submitted, and provides methods to manage them.
 * @constructor
 * @export
 */
bots.dashboard.UrlManager = function() {

  /**
   * A list of tuples for all the urls currently added:
   *   {'url': the url, 'element': the corresponding element on the page}
   * @type {Array}
   * @private
   */
  this.urls_ = [];

  /**
   * A list of tuples for the submitted urls currently added:
   *   {'url': the url, 'element': the corresponding element on the page}
   * @type {Array}
   * @private
   */
  this.submittedUrls_ = [];

  /**
   * A list of tuples for the interested/shared urls currently added:
   *   {'url': the url, 'element': the corresponding element on the page}
   * @type {Array}
   * @private
   */
  this.interestedUrls_ = [];

  /**
   * The popup client for displaying error messages and options.
   * @type {bots.dashboard.UrlPopup}
   * @private
   */
  this.popupClient_ = new bots.dashboard.UrlPopup();
};


/**
 * The ID of the Add Url link.
 * @type {string}
 */
bots.dashboard.UrlManager.ADD_URL_LINK_ID = 'addUrlLink';


/**
 * The height of a url being displayed.
 * @type {number}
 */
bots.dashboard.UrlManager.URL_HEIGHT = 34;


/**
 * The base height of the results border.
 * @type {number}
 */
bots.dashboard.UrlManager.RESULTS_BORDER_BASE_HEIGHT = 12;


/**
 * The ID of the results border that scales with urls.
 * @type {string}
 */
bots.dashboard.UrlManager.RESULTS_BORDER_ID = 'resultsBorder';


/**
 * The ID of the baseline that scales with urls.
 * @type {string}
 */
bots.dashboard.UrlManager.BASELINE_TEST_ID = 'baselineText';


/**
 * The default margin of the baseline text.
 * @type {number}
 */
bots.dashboard.UrlManager.BASELINE_TEXT_TOP_MARGIN = -75;


/**
 * The ID of the no data text.
 * @type {string}
 */
bots.dashboard.UrlManager.NODATA_ID = 'noDataText';


/**
 * The default margin of the no data text.
 * @type {number}
 */
bots.dashboard.UrlManager.NODATA_TEXT_TOP_MARGIN = -171;


/**
 * The ID of the url container.
 * @type {string}
 */
bots.dashboard.UrlManager.URL_CONTAINER_ID = 'urlList';


/**
 * Returns the icon of a score based on the numeric value.
 * @param {number} score A 0-100 score of how well a url matches.
 * @return {string} The relative path of the corresponding icon.
 * @export
 */
bots.dashboard.UrlManager.getScoreIcon = function(score) {
  if (score < 50) {
    return '/s/rating-poor.png';
  } else if (score < 90) {
    return '/s/rating-fair.png';
  } else if (score < 99) {
    return '/s/rating-good.png';
  } else if (score < 100) {
    return '/s/rating-great.png';
  } else if (score == 100) {
    return '/s/rating-excellent.png';
  }
};


/**
 * Return the urls the user currently has added.
 * @return {Array} An array of {url, element} objects.
 * @export
 */
bots.dashboard.UrlManager.prototype.getUrls = function() {
  return this.urls_;
};


/**
 * Updates the URL containers to be sized to fit the number of urls added.
 * @private
 */
bots.dashboard.UrlManager.prototype.updateUrlContainers_ = function() {
  // Scales the UI if there are more urls.
  if (this.urls_.length > 5) {
    var resultsBorder = goog.dom.getElement(
        bots.dashboard.UrlManager.RESULTS_BORDER_ID);
    goog.style.setStyle(
        resultsBorder, 'height', (this.urls_.length *
        bots.dashboard.UrlManager.URL_HEIGHT +
        bots.dashboard.UrlManager.RESULTS_BORDER_BASE_HEIGHT) + 'px');

    var baselineText = goog.dom.getElement(
        bots.dashboard.UrlManager.BASELINE_TEST_ID);
    goog.style.setStyle(
        baselineText, 'top', (this.urls_.length *
        (bots.dashboard.UrlManager.URL_HEIGHT / 2) +
        bots.dashboard.UrlManager.BASELINE_TEXT_TOP_MARGIN) + 'px');

    var noDataText = goog.dom.getElement(bots.dashboard.UrlManager.NODATA_ID);
    goog.style.setStyle(
        noDataText, 'top', (this.urls_.length *
        (bots.dashboard.UrlManager.URL_HEIGHT / 2) +
        bots.dashboard.UrlManager.NODATA_TEXT_TOP_MARGIN) + 'px');
  }

  if (this.submittedUrls_.length >= bots.dashboard.Constants.MAX_URLS) {
    var urlInputBox = goog.dom.getElement(
        bots.dashboard.Constants.URL_INPUT_ID);
    goog.style.setStyle(urlInputBox, 'display', 'none');

    var addUrlLink = goog.dom.getElement(
        bots.dashboard.UrlManager.ADD_URL_LINK_ID);
    goog.events.removeAll(addUrlLink);
    goog.style.setStyle(addUrlLink, 'innerHTML',
        'No additional URL\'s may be added.');
  }
};


/**
 * Adds and submits a URL to the server and dashboard.
 * @param {string} url The url to add to the dashboard.
 * @param {boolean} force Whether to force add the url.
 * @param {?Function} opt_successCallback Optional callback when the url is
 *   successfully added.
 * @export
 */
bots.dashboard.UrlManager.prototype.addUrl = function(
    url, force, opt_successCallback) {
  if (this.submittedUrls_.length >= bots.dashboard.Constants.MAX_URLS) {
    this.popupClient_.openInfoPopup(bots.dashboard.Constants.URL_INPUT_ID,
        'Currently users may only add up to' +
        bots.dashboard.Constants.MAX_URLS + ' URLs.');
  }

  try {
    var validatedUrl = this.validateUrl_(url);
    this.sendUrlToServer_(validatedUrl, force,
                          goog.bind(this.handleSendResponse_, this,
                                    validatedUrl, opt_successCallback));
  } catch (err) {
    this.popupClient_.openInfoPopup(bots.dashboard.Constants.URL_INPUT_ID,
        'An error occurred while processing your url. ' +
        'Please make sure it\'s correct and try again.');
  }
};


/**
 * Sends a URL to the server.
 * @param {string} url The url to add to the dashboard.
 * @param {boolean} force Whether to force add the url.
 * @param {Function} callback The function to call after completing
 *   the request.
 * @private
 */
bots.dashboard.UrlManager.prototype.sendUrlToServer_ = function(
    url, force, callback) {
  var dataUrl = bots.dashboard.Constants.ADDURL_URL + '?' +
                bots.dashboard.Constants.ADDURL_URL_SITE_PARAM + '=' + url;
  if (force) {
    dataUrl = dataUrl + '&' + bots.dashboard.Constants.FORCED_ADD_PARAM +
              '=true';
  }
  goog.net.XhrIo.send(dataUrl, callback, 'POST');
};


/**
 * Adds a "interested" URL to the list that someone else is running.
 * @param {string} key The key of the url on the server.
 * @param {string} url The url being added.
 * @export
 */
bots.dashboard.UrlManager.prototype.addInterestedUrl = function(key, url) {
  this.sendInterestedUrlToServer_(key,
                                  goog.bind(this.handleSendResponse_, this,
                                            url, null));
};


/**
 * Submits an "interested" URL to subscribe the user to it.
 * @param {string} key The key of the url on the server.
 * @param {Function} callback The function to call after completing
 *   the request.
 * @private
 */
bots.dashboard.UrlManager.prototype.sendInterestedUrlToServer_ = function(
    key, callback) {
  var dataUrl = bots.dashboard.Constants.ADDURL_URL + '?' +
      bots.dashboard.Constants.ADDURL_URL_EXISTING_PARAM + '=' + key;
  goog.net.XhrIo.send(dataUrl, callback, 'POST');
};


/**
 * Handles the response from submitting a request.
 * @param {string} url The original url requested.
 * @param {?Function} successCallback Callback if the add was successful.
 * @param {Object} response The response from the server.
 * @private
 */
bots.dashboard.UrlManager.prototype.handleSendResponse_ = function(
    url, successCallback, response) {
  var json_response = response.target.getResponseJson();
  if (json_response.status == 'success') {

    // If the request was a success but there are matching urls then display
    // them to the user, otherwise update the page with the new url.
    if (json_response['matching_urls'] != undefined) {
      this.popupClient_.openUrlSelection(
          'urlInput', 'This URL may be one we already crawl:',
          url, json_response['matching_urls'],
          goog.bind(this.addInterestedUrl, this),
          goog.bind(this.addUrl, this));
    } else {

      // Clear the input box after successfully submitting.
      var urlInput = goog.dom.getElement(
          bots.dashboard.Constants.URL_INPUT_ID);
      if (urlInput) {
        urlInput.value = 'http://...';
      }

      if (successCallback) {
        successCallback();
      } else {
        if (json_response['new_url_key'] != undefined) {
          this.addUrlToDashboard_(url, json_response['new_url_key'], true);
        } else if (json_response['updated_url_key'] != undefined) {
          this.addUrlToDashboard_(url, json_response['updated_url_key'], false);
        }
      }
    }
  } else if (json_response.status == 'warning') {
    // If the user already added it, let them know.
    if (json_response.message.toLowerCase() ==
        'url already part of submitted_urls.') {
      this.popupClient_.openInfoPopup('urlInput',
          'This URL has already been added for this account.');
    }
  } else {
    // For other errors show them directly to the user.
    this.popupClient_.openInfoPopup(
        bots.dashboard.Constants.URL_INPUT_ID, response['message']);
  }
};


/**
 * Performs light validation on url to screen out bad requests.
 * @param {string} url The url to validate.
 * @return {string} The validated url.
 * @private
 */
bots.dashboard.UrlManager.prototype.validateUrl_ = function(url) {
  var validatedUrl = url;

  // Add a http:// if it's missing
  if (!goog.string.startsWith(validatedUrl, 'http')) {
    validatedUrl = 'http://' + validatedUrl;
  }

  // Validate the url by parsing it and ensuring that it has a domain.
  if (goog.Uri.parse(validatedUrl).hasDomain() == false ||
      validatedUrl == 'http://...') {
    throw Error('Invalid URL, please recheck and try again.');
  }

  return validatedUrl;
};


/**
 * Adds a URL to the Dashboard
 * @param {string} url The url to add to the dashboard.
 * @param {string} key The key of the url being added.
 * @param {boolean} submitted Whether the url is submitted vs. interested.
 * @private
 */
bots.dashboard.UrlManager.prototype.addUrlToDashboard_ = function(
    url, key, submitted) {
  var urlsContainer = goog.dom.getElement(
      bots.dashboard.UrlManager.URL_CONTAINER_ID);
  var newUrlContainer = goog.dom.createElement(goog.dom.TagName.DIV);
  goog.dom.setProperties(newUrlContainer, {'class': 'scoresResultContainer'});

  var i = 0;
  while (i < bots.dashboard.Constants.BROWSERS_UNDER_TEST.length) {
    var newBrowserScore = goog.dom.createElement(goog.dom.TagName.SPAN);
    goog.dom.setProperties(newBrowserScore,
        {'id': 'browser' + url +
             bots.dashboard.Constants.BROWSERS_UNDER_TEST[i].id,
         'class': 'browser' + (i + 1) + 'Score'});
    goog.dom.appendChild(newUrlContainer, newBrowserScore);
    i++;
  }

  var newBrowserScoreURL = goog.dom.createElement(goog.dom.TagName.SPAN);
  if (submitted) {
    goog.dom.setProperties(newBrowserScoreURL,
        {'class': 'scoresURL', 'innerHTML': url});
  } else {
    var sharedLabel = goog.dom.createDom(goog.dom.TagName.SPAN, {
        'class': 'sharedLabel',
        'title': 'Shared URL\'s don\'t count against the total ' +
                 'number of urls you can submit.',
        'innerHTML': 'shared'});
    goog.dom.setProperties(newBrowserScoreURL,
        {'class': 'scoresURL', 'innerHTML': url});
    goog.dom.appendChild(newBrowserScoreURL, sharedLabel);
  }
  goog.dom.appendChild(newUrlContainer, newBrowserScoreURL);
  goog.dom.appendChild(urlsContainer, newUrlContainer);

  // Update the internal store of urls and the page UI.
  this.urls_.push({'url': url, 'key': key, 'element': newUrlContainer});
  if (submitted) {
    this.submittedUrls_.push(
        {'url': url, 'key': key, 'element': newUrlContainer});
  } else {
    this.interestedUrls_.push(
        {'url': url, 'key': key, 'element': newUrlContainer});
  }
  this.updateUrlContainers_();
};


/**
 * Handles a list of all urls from the server.
 * @param {?Function} callback Callback to run after getting the results.
 * @param {Object} response The response from the server.
 * @export
 */
bots.dashboard.UrlManager.prototype.urlHandler = function(
    callback, response) {
  var existingUrls = response.target.getResponseJson();
  for (var i = 0; i < existingUrls.length; i++) {
    this.addUrlToDashboard_(
        existingUrls[i]['url'], existingUrls[i]['key'], true);
  }
  if (callback) {
    callback();
  }
};


/**
 * Handles a list of submitted urls from the server.
 * @param {?Function} callback Callback to run after getting the results.
 * @param {Object} response The response from the server.
 * @export
 */
bots.dashboard.UrlManager.prototype.submittedUrlHandler = function(
    callback, response) {
  var existingUrls = response.target.getResponseJson();
  for (var i = 0; i < existingUrls.length; i++) {
    this.addUrlToDashboard_(
        existingUrls[i]['url'], existingUrls[i]['key'], true);
  }
  if (callback) {
    callback();
  }
};


/**
 * Handles a list of interested urls from the server.
 * @param {?Function} callback Callback to run after getting the results.
 * @param {Object} response The response from the server.
 * @export
 */
bots.dashboard.UrlManager.prototype.interestedUrlHandler = function(
    callback, response) {
  var existingUrls = response.target.getResponseJson();
  for (var i = 0; i < existingUrls.length; i++) {
    this.addUrlToDashboard_(
        existingUrls[i]['url'], existingUrls[i]['key'], false);
  }
  if (callback) {
    callback();
  }
};


/**
 * Prepares the UI to display scores, removing the "No Data" display.
 * @private
 */
bots.dashboard.UrlManager.prototype.initScoresUI_ = function() {
    var comparisonBorder = goog.dom.getElement('comparisonBorder');
    goog.dom.setProperties(comparisonBorder,
                           {'class': 'comparisonBorderResults'});

    var noDataText = goog.dom.getElement('noDataText');
    goog.style.setStyle(noDataText, 'display', 'none');

    var layoutLegend = goog.dom.getElement('layoutLegendContainer');
    goog.style.setStyle(layoutLegend, 'display', 'block');

    this.clearUrlScores_();
};


/**
 * Handles the server response returning the scores for a url.
 * @param {string} url The url being queried.
 * @param {Object} response The response from the server.
 * @private
 */
bots.dashboard.UrlManager.prototype.scoreHandler_ = function(url, response) {
  var json_response = response.target.getResponseJson();

  if (json_response['status'] == 'success' &&
      json_response['message'] != 'No results data found.') {
    for (var i = 0; i < json_response['result_deltas'].length; i++) {
      this.addUrlScore(url,
          json_response['result_deltas'][i]['test_browser_channel'],
          json_response['result_deltas'][i]['score'],
          json_response['result_deltas'][i]['page_delta_key']);
    }
  }
};


/**
 * Adds the score of a specified url to the dashboard.
 * @param {string} url The url of the browser.
 * @param {string} browser The name of the browser channel.
 * @param {number} score The diff score.
 * @param {string} resultKey The key to the page/browsers results.
 * @export
 */
bots.dashboard.UrlManager.prototype.addUrlScore = function(
    url, browser, score, resultKey) {
  var scoreCell = goog.dom.getElement('browser' + url + browser);
  if (scoreCell) {
    var scoreImg = goog.dom.createDom(goog.dom.TagName.IMG, {
        'src': bots.dashboard.UrlManager.getScoreIcon(score),
        'style': 'cursor: pointer'});
    goog.dom.removeChildren(scoreCell);
    goog.dom.appendChild(scoreCell, scoreImg);
    goog.events.listen(scoreImg, goog.events.EventType.CLICK,
                       goog.bind(this.openDetailPage_, this, resultKey));
  }
};


/**
 * Clears the scores on the dashboard and fills them with blank results.
 * @private
 */
bots.dashboard.UrlManager.prototype.clearUrlScores_ = function() {
  // Iterate through the urls and browser channels and add scores when
  // they're available.
  for (var i = 0; i < this.urls_.length; i++) {
    var urlObj = this.urls_[i]['element'];
    for (var k = 0; k < bots.dashboard.Constants.BROWSERS_UNDER_TEST.length;
         k++) {
      var scoreCell = goog.dom.getElement('browser' + this.urls_[i]['url'] +
          bots.dashboard.Constants.BROWSERS_UNDER_TEST[k].id);

      var noScoreImg = goog.dom.createElement(goog.dom.TagName.IMG);
      goog.dom.setProperties(noScoreImg, {'src': '/s/rating-nodata.png'});
      goog.dom.removeChildren(scoreCell);
      goog.dom.appendChild(scoreCell, noScoreImg);

    // TODO(user): Remove the style definitions here and just use
    // absolute positioning so this isn't neccessary.
      goog.style.setStyle(scoreCell, 'padding-left', '15px');
    }

    // TODO(user): Remove the style definitions here and just use
    // absolute positioning so this isn't neccessary.
    var urlColumn = goog.dom.getElementByClass('scoresURL', urlObj);
    goog.style.setStyle(urlColumn, 'padding-left', '30px');
  }
};


/**
 * Opens the detail page with url and browser selected as parameters.
 * @param {string} resultKey The key to the page/browsers results.
 * @private
 */
bots.dashboard.UrlManager.prototype.openDetailPage_ = function(resultKey) {
  window.location = bots.dashboard.Constants.DETAIL_URL + '?' +
                    bots.dashboard.Constants.DETAIL_URL_DELTAKEY_PARAM + '=' +
                    resultKey;
};


/**
 * Fetches scores from the server and displays them on the dashboard.
 * @export
 */
bots.dashboard.UrlManager.prototype.getAndDisplayScores = function() {
  this.initScoresUI_();
  for (var i = 0; i < this.urls_.length; i++) {
    var key = this.urls_[i]['key'];
    goog.net.XhrIo.send('/results?url_key=' + key,
        goog.bind(this.scoreHandler_, this, this.urls_[i]['url']), 'GET');
  }
};

