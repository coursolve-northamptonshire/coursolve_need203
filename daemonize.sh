#!/bin/sh
cd /usr/share/northants/
nohup nice /usr/share/northants/twitterd.py start --outdir /usr/share/northants/twout/ --cmd stream_filter --settings /usr/share/northants/.twitter_api_keys.json
