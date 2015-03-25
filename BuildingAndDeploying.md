# Building #

After you have checked out the QualityBots code, building is a simple process. To build everything for deployment, run the build.py script from the root directory. You will need to specify both your App Engine instance name and the App Engine server address that you will be running QualityBots from.

```
./build.py --server_address="yourinstance.appspot.com" --appengine_name="yourinstance"
```

If you have the svn command line client installed, the Closure library (http://code.google.com/closure/library/docs/gettingstarted.html) will be checked out for you. If you don't have the svn command line client installed, please check out
the Closure library to the closure-library directory in the root directory with your equivalent svn command:

```
svn checkout http://closure-library.googlecode.com/svn/trunk/ closure-library
```

Finally, you need to download the boto library (http://code.google.com/p/boto/) and copy the boto source directory to the src/appengine/third\_party directory. You must add the line
```
from __future__ import with_statement
```
to the top of the connection.py file so that the "with" statements used by boto will be compatible with Python 2.5 run by App Engine.

# Build Details #

The following are details about what happens in the build script. Skip to the next section if you are uninterested in these details. For exact build details, look at the build.py file.

### Building the client Python zip bundles ###
The client python code is built into a bundle by combining the files into a zip file and copying the main file to main.py within the zip.

This allows the zip to be directly executed by Python (version 2.6 is used).

These bundles are copied to the src/appengine/static directory so that they can be downloaded and used by the client.

### Building the server and client JavaScript ###

The server and client JavaScript relies on the Closure library and closure compiler. The Closure compiler is executed against all the main scripts to produce compiled versions that are used by the tool.

The client script (built from src/client) is copied to the src/appengine/static directory to be downloaded by the client.

# Deploying #

Using the appcfg.py App Engine script, you can deploy the tool to App Engine by running:
```
appcfg.py -V your_version src/appengine
```

# Configuring #

To use the QualityBots tool you must associate your Amazon AWS account information so that the tool can deploy EC2 instances.

Go to /config/config on your instance and enter your AWS account credentials to save them in the App Engine data store.