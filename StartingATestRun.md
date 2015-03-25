# Introduction #

In order to get results into the QualityBots system, you must run a Test Run over the submitted URLs. To kick off a test run manually, you must be an administrator for the QualityBots App Engine instance. A test run consists of running the different Chrome browser channels against the submitted URLs on an EC2 client and then computing the results from this data on the QualityBots App Engine instance.

# Starting a Test Run #
There are two ways of running a test run: kicking it off manually or kicking the job off through a regularly scheduled cron job. Once started, the test run will schedule each URL submitted to the system to run against each Chrome browser channel. The EC2 machines are brought up and monitored automatically.

For kicking the run off manually, you need to send a POST request to your App Engine instance at /distributor/start\_run. You must be logged in as an administrator to have access to this URL.

The easiest way to do things is by scheduling a cron job against the /distributor/start\_run URL. Instructions on setting up a scheduled task are available at http://code.google.com/appengine/docs/python/config/cron.html.

# Monitoring a Test Run #

Currently, the best way to monitor the test run is to look at the RunLog and ClientMachine data model status through the Datastore Viewer. These models will be updated as the test progresses.

In general, each URL takes an average of four minutes to process per version. By multiplying the number of URLs in your run by four, you can get a good estimate of the amount of time that your run will take.

# Stopping a Test Run #
If you decide that you no longer need further results from the test run or that you don't want the run to continue, you can expire the test run by sending a POST request to /distributor/expire\_test\_run and providing a "token" parameter equal to the token for your test run (the token can be determined by looking at the RunLog or ClientMachine models).

Expiring the test run will remove the remaining URLs from the processing queue and will shut down your EC2 instances for that test run.