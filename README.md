# oaiapp
Django oai app to run with registry

# Release steps
```
# First time only
cd code
git clone https://github.com/ucldc/oaiapp.git
cd avram
ln -s ../oaiapp/oai oai

# Checkout any code you need

source env.local
source ../../python/bin/activate
python ./manage.py migrate oai
python ./manage.py collectstatic
monit restart http

# Add new collections

# collection and repository are the ids in Calisphere
# example: https://calisphere.org/collections/65/
# collection_id = 65, repository_id = 18
cd code/avram
source env.local
source ../../python/bin/activate
python ./manage.py add_collection <collection_id> <repository_id>

# List of institution endpoints: https://registry.cdlib.org/oai/
# each collection is a set under given institution
# At the moment we only have collections from UCI but no changes need to be made to
# add new institutions just add the collections as above and appropriate institution
# endpoint will be added.
```

License
-------

Copyright © 2014, Regents of the University of California
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

- Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
- Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.
- Neither the name of the University of California nor the names of its
  contributors may be used to endorse or promote products derived from this
  software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
