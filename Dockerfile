FROM python:3.12.9-slim-bookworm
MAINTAINER Philipp D. Rohde <philipp.rohde@tib.eu>

# install dependencies
COPY requirements.txt /TravSHACL/requirements.txt
RUN python -m pip install --upgrade --no-cache-dir pip==24.2.* && \
    python -m pip install --no-cache-dir -r /TravSHACL/requirements.txt

# copy the source code into the container
COPY . /TravSHACL
WORKDIR /TravSHACL

# Trav-SHACL is no servie; so make the container stay active
ENV FLASK_APP=TravSHACL/app/__init__.py
ENV PYTHONUNBUFFERED=1
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
CMD ["flask", "run"]
