# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM alpine:3.5

RUN apk update
RUN apk add --no-cache python3 python3-dev build-base
RUN pip3 install --upgrade pip
RUN rm -r /root/.cache

COPY . /app
WORKDIR /app

RUN pip3 install Flask===0.11.1
RUN pip3 install httplib2==0.10.3
RUN pip3 install python-dateutil==2.6.1
RUN pip3 install requests==2.7.0
RUN pip3 install redis==2.10.6
RUN pip3 install hiredis==0.2.0
RUN pip3 install kubernetes==4.0.0

ENTRYPOINT ["python3"]
CMD ["server.py"]
