FROM ubuntu:18.04

WORKDIR /apps/travshacl
COPY . /apps/travshacl

RUN apt update &&\
    apt upgrade -y &&\
    apt install -y --no-install-recommends python3.6 python3-pip python3-setuptools curl grep &&\
    pip3 install --upgrade --no-cache-dir pip setuptools &&\
    apt clean &&\
    pip3 install --no-cache-dir -r requirements.txt

CMD ["tail", "-f", "/dev/null"]