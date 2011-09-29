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


"""AppEngine Datastore/GQL related Utilities module.

This common util provides helper functionality to extend/support
various GQL related queries.
"""




def FetchEntities(query_obj, limit):
  """Fetches number of Entities up to limit using query object.

  Args:
    query_obj: AppEngine Datastore Query Object.
    limit: Fetch limit on number of records you want to fetch.

  Returns:
    Fetched Entities.
  """
  entities = []
  # If Limit is more than 1000 than let's fetch more records using cursor.
  if limit > 1000:
    results = query_obj.fetch(1000)
    entities.extend(results)
    cursor = query_obj.cursor()
    while results and limit > len(entities):
      query_obj.with_cursor(cursor)
      results = query_obj.fetch(1000)
      entities.extend(results)
      cursor = query_obj.cursor()
  else:
    entities = query_obj.fetch(limit)
  return entities
