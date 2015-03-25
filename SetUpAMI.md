# Introduction #

The QualityBots tool uses Amazon EC2 for the clients that crawl the webpages. This document explains the process of setting up an Amazon Machine Image (AMI) for QualityBots to use.


# Using the Existing AMI #

We have created a custom AMI that is already setup and is available for public use:
```
AMI ID: ami-19a66b70
Username: administrator
Password: QualityBots
```

Make sure to change the AMI password and associate the AMI with your security group to avoid intrusion. Once done with changing the password, you should update the scheduled task which runs QualityBots to match the  updated credentials.

Take a snapshot of the AMI and save it under your account. Currently, QualityBots uses the first available AMI from your AWS account with the correct OS, so make sure that this is the only AMI you have in your account or that you update the code to use the specific AMI ID.

# Creating Your Own AMI #

If you'd like to create your own AMI, there are a few prerequisites that are required for the QualityBots client to run. Here are the instructions for creating a new AMI from scratch:

### Setup the image within AWS ###
  1. Get a standard Windows Server 2008 AMI from Amazon’s public AMI.
  1. Start the AMI and change the AMI’s Administrator password for safety reasons.

### Install the necessary software ###
  1. Install Python 2.6 from http://www.python.org/download/. Make sure to add python to system path so it’s accessible from anywhere.
  1. Download and install the Selenium 2.7.0 Python bindings from http://pypi.python.org/pypi/selenium. Alternatively, you can install “pip” and then run "pip install -U selenium”.
  1. Create a directory where you can put all the files required for the run (e.g. C:\QualityBots) and add that directory to the Windows PATH. This will be used as the QualityBots working directory.
  1. Download and install the latest chrome driver from http://code.google.com/p/chromium/downloads/list. Make sure to put ChromeDriver in in the previously created QualityBots working directory.
  1. From the QualityBots source, build “download\_files\_bundle.zip” and put the bundle in the QualityBots working directory. When building with the build.py script, the download\_files\_bundle.zip will be placed in the src/appengine/static directory.
  1. Optionally, feel free to install other additional tools to help with basic debugging.

### Image configuration ###
  1. Setup a scheduled task in Windows with appropriate credentials (ensure you set it to run even when user is not logged in). The scheduled task should kick off on machine start up and should run “python download\_files\_bundle.zip”.
  1. Take a snapshot of AMI and save it.

After following these steps, your AMI is setup and ready to go.