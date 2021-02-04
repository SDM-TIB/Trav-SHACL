FROM r-base:3.6.3

RUN apt-get update && \
  apt-get install -y --no-install-recommends python3 python3-pip && \
  pip3 install --upgrade pip && \
  pip3 install pandas==1.1.3 matplotlib && \
  echo "install.packages(\"ggplot2\")" | R --no-save < /dev/stdin && \
  echo "install.packages(\"fmsb\")" | R --no-save < /dev/stdin && \
  echo "install.packages(\"flux\")" | R --no-save < /dev/stdin && \
  apt-get clean
  
COPY ./code /code
WORKDIR /code

