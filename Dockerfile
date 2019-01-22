FROM debian:testing
MAINTAINER nabil-fareed.alikhan@quadram.ac.uk

RUN apt-get update -qq && apt-get install -y git python3 python3-setuptools python3-biopython python3-pip
RUN pip3 install cython

RUN pip3 install git+git://github.com/happykhan/qi_irida_utils.git

WORKDIR /data
