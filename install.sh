#!/bin/bash

cp silent_xps.py /usr/bin/silent_xps
cp config.json /etc/silent_xps.json
cp silent_xps.service /etc/systemd/system/
systemctl enable silent_xps
systemctl restart silent_xps
