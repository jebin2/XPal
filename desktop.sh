#!/bin/bash
cd /home/jebin/git/XPal || exit
source ~/.bashrc
penv
python main.py
exec $SHELL
