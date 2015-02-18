#!/bin/sh
cd /usr/share/northants/
nohup nice /usr/share/northants/twitterd.py start --outdir /usr/share/northants/twout/ --cmd stream_filter --max-time 259200 --settings /usr/share/northants/.twitter_api_keys.json &
