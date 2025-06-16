###
# Copyright (2023) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

# Use python 3.10-slim-buster as base image.

FROM python:3.10-slim-buster
#this is the user app workdir
WORKDIR /app


RUN apt-get update && apt-get install -y \
    build-essential git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


RUN python3 -m pip install git+https://github.com/HewlettPackard/cmf
#show the cmf initialization
CMD ["cmf", "init", "show"]

