#!/usr/bin/python2.4
#
# Copyright 2010 Google Inc. All Rights Reserved.
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


"""Filters that are used in the HTML templates."""




from google.appengine.ext import webapp


register = webapp.template.create_template_register()


@register.filter
def UnicodeString(value):
  """Convert a value into a unicode string."""
  return unicode(value)


@register.filter
def StringToFloat4(value):
  """Convert a float value into a string with four decimal places."""
  return '%.4f' % value


@register.filter
def StringToFloat2(value):
  """Convert a float value into a string with two decimal places."""
  if value:
    return '%.2f' % value


@register.filter
def CsvToTableRow(value):
  """Convert a string of comma-separated values into a table row string."""
  return ListToTableRow(value.split(','))


@register.filter
def ListToString(list_items):
  """Convert a list of items into a unicode string of a comma-separated."""
  str_list = [unicode(v) for v in list_items]
  return u', '.join(str_list)


@register.filter
def ListToTableRow(list_items):
  """Convert a list of items into an HTML table row string."""
  list_items = [u'<td>%s</td>' % unicode(item) for item in list_items]
  return u'<tr>%s</tr>' % u''.join(list_items)
