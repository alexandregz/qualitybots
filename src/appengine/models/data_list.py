#!/usr/bin/python2.4
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


"""DataList model and DataListEntry model.

DataList model is an empty model which is there to link together DataListEntry
as a collection. DataList is stored as a reference-property in DataListEntry,
which can be accessed using 'collection_name'. This model is designed solely
for breaking data into small chunks (64 pieces) for efficient sending/retrieval
over the network.
"""



from django.utils import simplejson

from google.appengine.ext import db


NUM_ENTRIES = 64


#TODO(user): Simplify Models by getting rid of DataList all together.
class DataList(db.Model):
  """Represents a collection of DataListEntry entities."""

  def _GetEntryKeyName(self, index, dynamic_content_flag=False):
    """Contructs a string key name that uniquely identify a DataListEntry.

    Args:
      index: Index of DataListEntry.
      dynamic_content_flag: Flag to represent dynamic content related
          DataListEntry.

    Returns:
      DataListEntry key name.
    """
    if dynamic_content_flag:
      return '%s_entry_dynamiccontent_%d' % (self.key().id_or_name(), index)
    else:
      return '%s_entry_%d' % (self.key().id_or_name(), index)

  def AddEntry(self, index, data, dynamic_content_flag=False):
    """Create a new DataListEntry.

    Args:
      index: Index of DataListEntry.
      data: Data to store.
      dynamic_content_flag: Flag to represent dynamic content related
          DataListEntry.

    Returns:
      Created DataListEntry entity.
    """
    entry_key_name = self._GetEntryKeyName(index, dynamic_content_flag)
    entry = DataListEntry.get_or_insert(key_name=entry_key_name,
                                        list=self, order=index)
    entry.content = simplejson.dumps(data)
    entry.length = len(data)
    entry.put()
    return entry

  def GetEntryData(self, index):
    """Retrieves DataListEntry stored at the given index.

    Args:
      index: Index of DataListEntry.

    Returns:
      Content of the DataListEntry.
    """
    entry = self.data_entries.filter('order =', index).get()
    if entry and entry.content:
      return simplejson.loads(entry.content)
    else:
      return []

  def ClearEntries(self):
    """Deletes all DataListEntries."""
    entries = self.data_entries.fetch(100)
    if entries:
      db.delete(entries)

  def EntriesReady(self):
    """Checks if all the DataListEntries are received or not."""
    return self.data_entries.count() == NUM_ENTRIES


class DataListEntry(db.Model):
  """Stores one piece of data and its index."""
  list = db.ReferenceProperty(DataList, collection_name='data_entries')
  order = db.IntegerProperty()
  content = db.TextProperty(default='')
  length = db.IntegerProperty(default=0)


def CreateEmptyDataList():
  """Creates an empty DataList and put into the datastore.

  Returns:
    Newly created DataList Entity.
  """
  data_list = DataList()
  data_list.put()
  return data_list


def CreateDataListIndex(data_list):
  """Create a list to show which data list indices have data list entries.

  Args:
    data_list: A DataList object to create the index for.

  Returns:
    A JSON string representing the data list index.
  """
  entries = data_list.data_entries

  index = []
  for entry in entries:
    if entry.content != '[]':
      index.append(int(entry.order))

  index.sort()
  return simplejson.dumps(index)
