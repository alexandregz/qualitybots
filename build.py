#!/usr/bin/python2.6
#
# Copyright 2011 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Build the QualityBots source so it's ready to push to App Engine."""



import logging
import optparse
import os
import subprocess
import urllib
import zipfile


CHECKOUT_CLOSURE_COMMAND = ('svn checkout http://closure-library.googlecode.com'
                            '/svn/trunk/ closure-library')
CLOSURE_COMPILER_URL = ('http://closure-compiler.googlecode.com/files/'
                        'compiler-latest.zip')
COMPILE_CLOSURE_COMMAND = ('closure-library/closure/bin/build/closurebuilder.py'
                           ' --root=%(root)s --root=closure-library'
                           ' --input=%(input)s'
                           ' --output_mode=compiled --output_file=%(output)s'
                           ' --compiler_jar=compiler.jar')
SERVER_PLACEHOLDER_TEXT = 'YOUR_APPENGINE_SERVER_HERE'
APPENGINE_NAME_PLACEHOLDER_TEXT = 'YOUR_APPENGINE_NAME_HERE'


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')


class ClosureError(Exception):
  pass


def BuildClosureScript(output_filename, input_filename, root, server_address):
  """Build a compiled closure script based on the given input file.

  Args:
    output_filename: A string representing the name of the output script.
    input_filename: A string representing the name of the input script to
      compile.
    root: A string representing the directory containing the script
      dependencies.
    server_address: A string representing the server address
      (ie qualitybots.appspot.com)

  Raises:
    ClosureError: If closure fails to compile the given input file.
  """
  results = ExecuteCommand(
      COMPILE_CLOSURE_COMMAND % {
          'root': root,
          'input': input_filename,
          'output': output_filename})

  ReplaceStringInFile(output_filename, SERVER_PLACEHOLDER_TEXT, server_address)

  if not os.path.exists(output_filename):
    if len(results) >= 2:
      logging.error(results[1])
    raise ClosureError('Failed while compiling %s.' % input_filename)


def BuildPythonZipBundle(output_filename, filename_list, main_file,
                         server_address):
  """Build a python zip bundle containing the given files.

  Args:
    output_filename: A string representing the name of the output zip file.
    filename_list: A list of strings representing the files to include in the
      zip file.
    main_file: A string representing the file to make the __main__.py file for
      the zip bundle.
    server_address: A string representing the server address
      (ie qualitybots.appspot.com)
  """
  output_zip = zipfile.ZipFile(output_filename, 'w')

  for filename in filename_list:
    ReplaceStringInFile(filename, SERVER_PLACEHOLDER_TEXT, server_address)
    output_zip.write(filename)

  output_zip.write(main_file, arcname='__main__.py')
  output_zip.close()


def ExecuteCommand(command):
  """Execute the given command and return the output.

  Args:
    command: A string representing the command to execute.

  Returns:
    A string representing the output of the command.
  """
  process = subprocess.Popen(command.split(' '),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
  return process.communicate()


def ReplaceStringInFile(filename, old_text, new_text):
  """Replace the given old_text with new_text throughout the specified file.

  Args:
    filename: A string representing the name of the file to use for string
      replacement.
    old_text: A string representing the text to find and replace.
    new_text: A string representing the new text to use as a replacement.
  """
  file_contents = ''
  with open(filename, 'r') as f:
    file_contents = f.read()

  with open(filename, 'w') as f:
    f.write(file_contents.replace(old_text, new_text))


def SetupClosure():
  """Setup the closure library and compiler.

  Checkout the closure library using svn if it doesn't exist. Also, download
  the closure compiler.

  Raises:
    ClosureError: If closure fails to compile the given input file.
  """
  # Set up the svn repo for closure if it doesn't exist.
  if not os.path.exists('closure-library'):
    ExecuteCommand(CHECKOUT_CLOSURE_COMMAND)
    if not os.path.exists('closure-library'):
      logging.error(('Could not check out the closure library from svn. '
                     'Please check out the closure library to the '
                     '"closure-library" directory.'))
      raise ClosureError('Could not set up the closure library.')

  # Download the compiler jar if it doesn't exist.
  if not os.path.exists('compiler.jar'):
    (compiler_zip, _) = urllib.urlretrieve(CLOSURE_COMPILER_URL)
    compiler_zipfile = zipfile.ZipFile(compiler_zip)
    compiler_zipfile.extract('compiler.jar')


def main():
  usage = 'usage: %prog [options]'
  parser = optparse.OptionParser(usage)
  parser.add_option('--server_address', dest='server_address',
                    action='store', type='string', default='',
                    help=('The name of your server to use in the '
                          'files (ie qualitybots.appspot.com).'))
  parser.add_option('--appengine_name', dest='appengine_name',
                    action='store', type='string', default='',
                    help=('The name of your App Engine instance to use in the '
                          'app.yaml file.'))
  parser.add_option('--omit_bots_client_bundle',
                    dest='omit_bots_client_bundle',
                    action='store_true', default=False,
                    help='Omit building the bots_client_bundle.zip file.')
  parser.add_option('--omit_browser_install_bundle',
                    dest='omit_browser_install_bundle',
                    action='store_true', default=False,
                    help='Omit building the browser_install_bundle.zip file.')
  parser.add_option('--omit_download_files_bundle',
                    dest='omit_download_files_bundle',
                    action='store_true', default=False,
                    help='Omit building the download_files_bundle.zip file.')
  parser.add_option('--omit_webdriver_js',
                    dest='omit_webdriver_js',
                    action='store_true', default=False,
                    help='Omit building the webdriver js.')
  parser.add_option('--omit_appengine_js',
                    dest='omit_appengine_js',
                    action='store_true', default=False,
                    help='Omit building the appengine js.')
  (options, _) = parser.parse_args()

  if not options.server_address:
    parser.error('The --server_address argument is required.')

  if not options.appengine_name:
    parser.error('The --appengine_name argument is required.')

  # Build the bots_client_bundle.zip from src/webdriver.
  if not options.omit_bots_client_bundle:
    logging.info('Building bots_client_bundle.zip')
    BuildPythonZipBundle('src/appengine/static/bots_client_bundle.zip',
                         ['src/webdriver/appengine_communicator.py',
                          'src/webdriver/blobstore_upload.py',
                          'src/webdriver/bots_client.py',
                          'src/webdriver/chrome_resize.py',
                          'src/webdriver/client_logging.py',
                          'src/webdriver/webdriver_wrapper.py'],
                         'src/webdriver/bots_client.py',
                         options.server_address)

  # Build the browser_install_bundle.zip and download_files_bundle from
  # src/client_setup.
  if not options.omit_browser_install_bundle:
    logging.info('Building browser_install_bundle.zip')
    BuildPythonZipBundle('src/appengine/static/browser_install_bundle.zip',
                         ['src/client_setup/chrome_manager.py',
                          'src/client_setup/instance_manager.py',
                          'src/client_setup/mylogger.py'],
                         'src/client_setup/instance_manager.py',
                         options.server_address)

  if not options.omit_download_files_bundle:
    logging.info('Building download_files_bundle.zip')
    BuildPythonZipBundle('src/appengine/static/download_files_bundle.zip',
                         ['src/client_setup/download_files.py',
                          'src/client_setup/mylogger.py'],
                         'src/client_setup/download_files.py',
                         options.server_address)

  if not options.omit_webdriver_js or not options.omit_appengine_js:
    logging.info('Setup the closure library and compiler')
    SetupClosure()

  # Build the webdriver_content_script.js from src/client.
  if not options.omit_webdriver_js:
    logging.info('Building the webdriver js')
    BuildClosureScript('src/appengine/static/webdriver_content_script.js',
                       'src/client/webdriver_content.js', 'src/client',
                       options.server_address)

  if not options.omit_appengine_js:
    logging.info('Building the appengine js')
    appengine_js_files = [
        'addurl_landing', 'drawdelta', 'prerender', 'suitedetails',
        'suite_compare', 'suite_compare_stripdown', 'suite_stats',
        'url_dashboard', 'url_detail']

    for js_file in appengine_js_files:
      logging.info('Compiling %s', js_file)
      BuildClosureScript('src/appengine/js/%s_script.js' % js_file,
                         'src/appengine/js/%s.js' % js_file,
                         'src/appengine/js',
                         options.server_address)

  # Update the App Engine app.yaml name
  ReplaceStringInFile('src/appengine/app.yaml', APPENGINE_NAME_PLACEHOLDER_TEXT,
                      options.appengine_name)


if __name__ == '__main__':
  main()
