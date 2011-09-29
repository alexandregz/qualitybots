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
 * @fileoverview Class for running a countdown mechanism till the next
 * Bots run.
 *
 */

goog.provide('bots.dashboard.Countdown');

goog.require('goog.Timer');
goog.require('goog.date');
goog.require('goog.dom');



/**
 * Constructor for Countdown class that keeps track of the amount of time
 * until the next Bots run.
 * @param {string} countdownElementId The element to update with the countdown.
 * @constructor
 * @export
 */
bots.dashboard.Countdown = function(countdownElementId) {
  this.endTime = 0;
  this.countdownElement = goog.dom.getElement(countdownElementId);

  // TODO(user): To be replaced by a XHRIO call.
  mockCountdownServer(goog.bind(this.startCountdown, this));
};


/**
 * The number of milliseconds in a second
 * @type {number}
 */
bots.dashboard.Countdown.MILLISECONDS_IN_SECOND = 1000;


/**
 * The number of milliseconds in a minute
 * @type {number}
 */
bots.dashboard.Countdown.MILLISECONDS_IN_MINUTE =
    bots.dashboard.Countdown.MILLISECONDS_IN_SECOND * 60;


/**
 * The number of milliseconds in an hour
 * @type {number}
 */
bots.dashboard.Countdown.MILLISECONDS_IN_HOUR =
    bots.dashboard.Countdown.MILLISECONDS_IN_MINUTE * 60;


/**
 * The number of milliseconds in a day
 * @type {number}
 */
bots.dashboard.Countdown.MILLISECONDS_IN_DAY =
    bots.dashboard.Countdown.MILLISECONDS_IN_HOUR * 24;


/**
 * Converts a milliseconds count into a two character string based on a
 * specified division.
 * @param {number} milliseconds The number of milliseconds in the time period.
 * @param {number} period The number of milliseconds in the divisible period.
 * @param {boolean} round Whether to round the number or floor it (default).
 * @param {boolean} sixtyBase Whether the time is in sixty based blocks.
 * @return {string} A "xx" formatted string of the time period.
 * @export
 */
bots.dashboard.Countdown.timeToXX = function(
    milliseconds, period, round, sixtyBase) {
  var time = 0;
  var timeString = '';

  if (round) {
    time = Math.round(milliseconds / period);
  } else {
    time = Math.floor(milliseconds / period);
  }

  // Return 00 if the time is sixty based, and exactly 60.
  if (sixtyBase && time == 60) {
    return '00';
  }

  // Add a leading zero if neccessary, if the number is greater than 100
  // return '99'
  if (time < 10) {
    timeString += '0';
  } else if (sixtyBase && time > 60) {
    return '59';
  } else if (time > 99) {
    return '99';
  }

  timeString += time;

  return timeString;
};


/**
 * Converts a milliseconds count into a string that uses "dd:hh:mm:ss"
 * format.
 * @param {number} milliseconds The number of milliseconds in the time period.
 * @return {string} A "dd:hh:mm:ss" formatted string of the time period.
 * @export
 */
bots.dashboard.Countdown.timeToStringDDHHMMSS = function(milliseconds) {
  var resultString = '';
  var remainingTime = milliseconds;

  resultString += bots.dashboard.Countdown.timeToXX(
      remainingTime, bots.dashboard.Countdown.MILLISECONDS_IN_DAY, false,
      false) + ':';
  remainingTime %= bots.dashboard.Countdown.MILLISECONDS_IN_DAY;
  resultString += bots.dashboard.Countdown.timeToXX(
      remainingTime, bots.dashboard.Countdown.MILLISECONDS_IN_HOUR, false,
      false) + ':';
  remainingTime %= bots.dashboard.Countdown.MILLISECONDS_IN_HOUR;

  // If there's >59.5 seconds left, add a minute to the clock.
  if (Math.round((remainingTime %
          bots.dashboard.Countdown.MILLISECONDS_IN_MINUTE) / 1000) == 60) {
    remainingTime += bots.dashboard.Countdown.MILLISECONDS_IN_MINUTE;
  }

  resultString += bots.dashboard.Countdown.timeToXX(
      remainingTime, bots.dashboard.Countdown.MILLISECONDS_IN_MINUTE, false,
      true) + ':';
  remainingTime %= bots.dashboard.Countdown.MILLISECONDS_IN_MINUTE;
  resultString += bots.dashboard.Countdown.timeToXX(
      remainingTime, bots.dashboard.Countdown.MILLISECONDS_IN_SECOND, true,
      true);
  remainingTime %= bots.dashboard.Countdown.MILLISECONDS_IN_SECOND;

  return resultString;
};


/**
 * Kicks off the countdown using a response from a server.
 * @param {Object} response The mock server response with the time.
 */
bots.dashboard.Countdown.prototype.startCountdown = function(response) {
  this.endTime = response['time'];
  this.updateCountdown();
};


/**
 * Updates the time until the next Bots run, calls itself recursively.
 */
bots.dashboard.Countdown.prototype.updateCountdown = function() {
  var currentTime = new goog.date.DateTime();
  var untilEndTime = bots.dashboard.Countdown.timeToStringDDHHMMSS(
      this.endTime - currentTime.getTime());

  // If the time has expired return a time of 0
  if (untilEndTime < 0) {
    untilEndTime = 0;
  }
  this.countdownElement.innerHTML = untilEndTime;
  goog.Timer.callOnce(goog.bind(this.updateCountdown, this),
                      bots.dashboard.Countdown.MILLISECONDS_IN_SECOND);
};


/**
 * A mock responder for the countdown service, will be replaced when
 * the handlers are implemented.
 * @param {Function} callback The callback to call with the response.
 */
function mockCountdownServer(callback) {
  var nextRun = new goog.date.DateTime();

  // Set the time to 7 days in the future.
  callback({time: (nextRun.getTime() + 86400 * 1000 * 7)});
}

