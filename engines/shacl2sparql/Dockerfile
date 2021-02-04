FROM ubuntu:18.04

COPY . /apps/shacl-sparql

RUN apt update &&\
    apt install openjdk-8-jdk maven nano -y &&\
    apt autoremove openjdk-11-jre* -y &&\
    apt clean &&\
    cd /apps/shacl-sparql &&\
    ./build.sh

WORKDIR /apps/shacl-sparql

CMD ["tail", "-f", "/dev/null"]
