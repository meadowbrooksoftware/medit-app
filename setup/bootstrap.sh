#!/bin/bash

# required software

sudo apt-get update
sudo apt-get install -y git
sudo apt-get install -y python
sudo apt-get install -y python-pip

# dirs

sudo mkfs -t ext4 /dev/xvdb
sudo mkdir -p /opt/
cd opt

# application

sudo git clone https://github.com/meadowbrooksoftware/meditsvc
sudo mkdir /opt/meditsvc/data/
sudo mount /dev/xvdb/ /opt/meditsvc/data/
sudo chown -R ubuntu /opt/meditsvc/
mkdir /opt/meditsvc/data/logs/
cd /opt/meditsvc/

# python modules

pip install -r requirements.pip

# start service

echo "try:python meditsvc.py 2&>1 &"




