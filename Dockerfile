FROM python:3.9.10-slim-buster
MAINTAINER Philipp D. Rohde <philipp.rohde@tib.eu>

# install dependencies
COPY requirements.txt /TravSHACL/requirements.txt
RUN python -m pip install --upgrade --no-cache-dir pip==22.0.* && \
    python -m pip install --no-cache-dir -r /TravSHACL/requirements.txt

# copy the source code into the container
COPY . /TravSHACL
WORKDIR /TravSHACL

# Trav-SHACL is no servie; so make the container stay active
CMD ["tail", "-f", "/dev/null"]
