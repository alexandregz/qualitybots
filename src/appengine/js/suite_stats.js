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
 * @fileoverview Draw graphs for the suite stats page.
 */


goog.provide('bots.appcompat.SuiteStats');


// Load the Visualization API and the column chart package.
google.load('visualization', '1', {'packages': ['corechart']});

// Set a callback to run when the Google Visualization API is loaded.
google.setOnLoadCallback(drawChart);



/**
 * Callback that creates and populates a data table, instantiates the pie
 * chart, passes in the data and draws it.Draw a chart for the suite stats
 * page.
 */
function drawChart() {
  // Create our data table.
  var data = new google.visualization.DataTable();
  data.addColumn('string', 'Browser');
  data.addColumn('number', 'Layout');
  data.addRows([browser_scores]);

  // Instantiate and draw our chart, passing in some options.
  var chart = new google.visualization.ColumnChart(
      document.getElementById('chart_div'));
  chart.draw(data, {title: 'Average Scores',
          width: 600, height: 400,
          hAxis: {title: 'Browsers'},
          vAxis: {maxValue: 100.0, minValue: 50.0}});
}
