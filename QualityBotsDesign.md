# Objective #
An automated scalable testing of web properties (websites)  and/or browsers to uncover potential site compat/layout issues and reduce the regression test suite. An automated testing solution that very much behaves and functions like Search - it crawls, it indexes and it scores. Primary goal of QualityBots is to reduce the regression test suite and provide free web testing at scale with minimal human intervention. It also can serve as early watchdog and alert system to catch potential issues at early stage of development.

# Background #

When it comes to testing of web properties, there are many approaches - manual, automated and hybrid - taken within google. Majority of web property rely on some sort of hybrid approach where they have QA team manually testing each site on various platforms and browsers at every release along with some mix of unit testing and automated testing. Manual testing has benefit of human eye balls looking at it, but at the same it’s extremely expensive and often times can’t scale. In a typical web testing, 80% of the test are just regression test and are repeated every single release cycle. Automated testing helps reduce this regression work.

WebDriver/Selenium are widely used for automated web testing and they are great tools to automate manual testing work, but all of these approaches have an incremental benefit. i.e. Each automated test is site/functionality specific and has to be maintained to stay in sync with change in site design/functionality. Hence, automated testing is equally expensive and mainly discouraged for many properties where things change too frequently.

# Overview #

QualityBots (aka Bots) aims to reduce the regression test suite by automated testing of web properties across browsers versions, browser types and platforms. Bots doesn’t rely on traditional image comparison which many have tried and failed. Instead it will rely on entire DOM index (pixel by pixel) and use that to compare between different runs. Bots will crawl the website on a given platform and browser, while crawling it will record the HTML elements rendered at each pixel of the page. Later this data will be used to compare and calculate layout score. Bots are designed in a way to not have any false positives, although it can have false negatives which can be reduced with smarter and better scoring algorithm and dynamic content detection techniques.

In order to ensure we scale with the web, Google App Engine (Python) is used for the server which is responsible for data collection, storage, score calculation and result display. The client was originally designed as a browser extension, but later switched to webdriver model mainly to benefit from webdriver’s cross browser support. In order to make it scalable and have windows support, we went with Skytap for test execution in the cloud for early experimentation, but later switched to Amazon EC2 for cost effectiveness and better API support.

# Detailed Design #

QualityBots has two major components - Google App Engine based server and webdriver-based Client. Let’s look at a detailed design of both the components and their subcomponents.

## QualityBots Server: ##

The QualityBots server is a Python based Google App Engine instance. The  primary reason for selecting Google App Engine is mainly because it is Google technology which is designed to scale reasonably well with the data and web plus its simplicity and fast learning curve. Let’s look at detailed design of its subcomponents.

### Signup Flow: ###

Sign up flow consists of mechanism to identify, detect and manage bots users, URL management and management of other configuration associated with each url. User detection and sign up is done using standard GAIA mechanism. Hence, it is required for every user of bots to have Google account. Once user is authenticated, user will be able to submit urls for crawl.

In order to prevent spam and abuse of the system, system has limitation on how many number of URLs a given user can submit to crawl at a given point of time. In initial iteration this limitation will be set to around 20 URLs per user. De-duping and URL validation is done at the time of insertion. In order to ensure multiple users don’t submit same URL for crawl, user will be notified if URL that he/she is trying to add it is already part of crawl list. Hence, user has a choice to add those URLs as interested (aka Shared). Interested URLs are associated with a given bots user, but not being used to calculate the quota. This mechanism allows user to mark many urls as interested but still not exhaust quota. Depth, auth and other important information about URL is stored in URL\_CONFIG Model where urls will be stored in URL Model and users will be stored in BOTS\_USER model. Depth is used to crawl landing page and links from that page. By default we only crawl landing page only. Currently, user can’t edit any of these URL\_CONFIG information, but with subsequent release we are hoping to release more customization and config information which will allow us to crawl more than the landing page as well as pages behind auth.

### Test Run / Execution: ###

At agreed frequency (currently weekly), bots will take all submitted urls and schedule a run. Currently we support chrome only, so we will have run for every channel of the Chrome. Chrome has 4 channels (Stabel, Beta, Dev and Canary). Bots will schedule a test run to crawl each url on all chrome channels. RunQueue is implemented using run\_log model. Each run of bots require one of the browser to be marked as reference browser. Reference browser is the browser whose data is used as baseline while doing comparison and computing layout score. As stable is the most tested and widely used browser for Chrome, bots uses “stable” as its baseline while comparing across various chrome channels. Unique token is generated and passed everywhere between every communication of client and server to identify a specific run. This mechanism allows us to have multiple simultaneous runs.

Depending on the run\_log queue size, bots calculates required number of machines. Currently bots only support windows, in future versions of bots it’s fairly easy to add support for other platforms where webdriver is supported. Using AWS EC2 credentials stored in one of the model, bots spin up EC2 machines. Client machine are spun up using preconfigured EC2 AMI (Amazon Machine Image). EC2 AMI is created using standard Windows EC2 AMI. This AMI has pre-installed webdriver, python, a basic editor (notepad++) and a download script. Download script downloads all the other required scripts to install, set up and start a test run. Due to this design, it’s very easy to quickly push new setup and webdriver script to client machine. All the script (except download scripts) are hosted on Bots Server (as static files for now). Chrome channel and other important data are passed as user\_data to EC2 instance.

Once client machine (EC2) is ready to run test, it starts requesting url to run from this run\_log. Run log uses retry count and priority mechanism to assign test to each client. High priority test are run first and every retry drops the priority of url. This mechanism prevents choking of a test run in case of a bad url. Exponential back-off is used in every retry mechanism bots has.

Once client is done crawling a URL, it submits all the data to server. Snapshots are stored as blobstore images for faster retrieval. This mechanism also helps in reducing storage needs on server. All the client logs - set up and test run logs- are submitted to server for debugging purpose. For efficiency, logs are base64 encoded and zlib compressed. Once client is finished uploading all the data - screenshots, layout table, nodes table etc, client asks server to mark that URL for as finished. Immediately after, client asks for next test case to crawl and whole process repeats, until all the URLs are crawled. Client user\_agent and supplied channel is used to determine work it gets to crawl.

Once run\_log queue is empty, it starts sending “null” to all the client who requests work items afterwards and then server starts terminating (/stopping) each machine. Bots has monitor cron jobs which keep checking for last updates from each client to to avoid dead clients. Any request from client updates the “last updated” timestamp on server and hence allows them to continue working rather than marked as dead. Dead clients are rebooted or re-spawn depending on the state of a client/machine. Each reboot attempt increases the retry count of client/machine until it gets reaches max retry count and then it gets terminated.

### Data storage: ###

Crawled site data is stored in page\_data model, which is later used to compare data against reference browser. Bots creates a separate test suite for each test run. Reference browser crawled are also stored in page data model. For efficiency and to bypass appengine limitation (max entity size of 1 MB and request time not to exceed 30 secs), server is designed to store data in various models. Information about DOM is divided into 2 parts. Nodes table which consists of metadata about each element on the page and layout table is the mapping of element and pixel-map i.e. at each pixel what element exist.

```
nodes_table[uniqueIDOfElement] = {
  'w': node.offsetWidth,
  'h': node.offsetHeight,
  'x': node.offsetLeft,
  'y': node.offsetTop,
  'p': xPath/selector
}
```

Nodes table is directly stored in page\_data as textproperty whereas layout table is broken into 64 pieces and stored as 64 datalist entry. Nodes table data are 64 bit encoded and compressed before send to server to improve the efficiency in storage and retrieval.

Bots also have built-in mechanism to ignore dynamic content like ads. It’s using same kind of mechanism (easylist) as famous firefox extension “AdBlock Plus”. EasyList is openly available crowdsourced list of regex which helps bots identify what elements are ads on the page. Easylist integration is still work in progress and once done it can help improve the accuracy of data as we can ignore dynamic content like ads.

Screenshots of each URL is stored as blobstore entry and reference to blobstore key is stored in page\_data model.

### Layout Score Computation: ###

Once crawled is collected for each url, constantly running cron job identifies which data is available for comparison. Availability of data for comparison happens when both the page data (reference and test browser) is ready and available. Once data is available for comparison, comparison is done in 64 pieces as all collected data is too large to handle in single request. With the use of google appengine backend, this limitation can be overcome, hence requires some work for future versions of bots to exploit appengine backends.

Current algorithm used for comparison compares each element metadata with reference browser’s element metadata and if if any mismatch found then it’s added to diff list in page\_delta model. All the data about comparison including layout score is stored in page\_delta model. Page\_delta model is a comparison view between test and reference browser, which is used for displaying results. While comparing each pixel data, data which are marked as dynamic content is spared from comparison, this helps us ignore ads and other dynamic content. Algorithm used currently uses simple comparison, but future algorithm can be used for better comparison. From initial investigation and experimentation in this area, it was clear that it’s hard to come up with a single algorithm which works across all sites. Hence, in the future bots we should have set of algorithms, each one specific for site type and category.

Layout score is calculated using this comparison between test and reference browser. Layout score is 100 for identical sites and 0 for unidentical sites. Current mechanism allows us to have multiple test browsers per run, but only one to be used as a reference browser. Future versions of bots should allow on the fly selection of baseline(/reference) browser. Often times, site with high amount of dynamic content or too frequent changes, comes out with bit lower scores than 100 even though there are no differences. This can be avoided with better synchronization between test browser and reference browser. Of course, smart algorithm to detect pixel shift and ad size variation will help here.

Due to dynamic nature of web, bots often generate noise while calculating scores for flash, dynamic or too frequently updating (e.g. news sites) sites. Hence, rather than relying layout score, it’s recommended to rely on deviation in the score over period of time. e.g. www.cnn.com has a layout score of 84 on first run, 80 on the week following, 20 at some later week. Sites like CNN changes too frequently hence, it’s difficult to have identical page between 2 difference crawls (test and reference). Layout score on its own may not be that useful in CNN’s case, but looking at deviation between 2nd and 3rd run, it’s obvious something hugely changed and pages look quite differently on 2 browsers. This itself is worth enough for human investigations.

With many runs of bots we have seen a trend where more than 80% of sites just look identical (~100 layout score) across runs. This is huge savings that humans don’t have to look at this site and we know for sure that these sites are looking exactly the same.

### UX Component: ###

Bots UX component consists of user sign up and results viewing part. All of the UX is written using Google App Engine and django templates.


## QualityBots Client: ##

In the first generation of quality bots, we relied on browser based extension framework. In the later generations of bots we decided to move to webdriver based framework for client. Webdriver supports multiple browsers and platforms by default with minimal client changes, hence it was an obvious choice for later generations of bots.

Current client design includes python scripts and webdriver. There are 3 pieces of client - download component, set up component and test runner component.  Setup component consists of scripts to download appropriated chrome channel and kicking off test runner component. Testrunner  component consists of webdriver script and appengine communicator script. WebDriver script is responsible of kicking off webdriver (/chromedriver) and injecting a content script in the browser and collecting results. AppEngine Communicator is responsible for fetching new test cases, submitting test results and other client-server communication.

Once EC2 instance has started by bots, first thing it does is to kick off download script (/component) which asks the server to give list of all necessary scripts and then start downloading  each scripts. Once all scripts are downloaded, it kicks off setup script which gets the channel assigned from ec2 user\_data. Once, channel and download url is identified from user\_data, it tries to download and install chrome channel. Setup script is designed to uninstall pre-existing versions of Chrome if the version doesn’t match with the version required. Setup script kicks off webdriver (testrunner component) script.

The testrunner component fetches each url to crawl from server and keeps going until it exhaust the runner queue. Currently bots support windows based OS, so pre-configured EC2 AMI is used to kick off a machine. This AMI has pre-installed download script, python, chromedriver and some basic editors.