#!/bin/bash
mvn clean 
mvn package 
mv target/valid-1.0-SNAPSHOT.jar build/
mvn clean
