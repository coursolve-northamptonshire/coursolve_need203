#!/bin/sh
cd /usr/share/northants/coursolve_need203
nohup nice twitterd.py start --outdir twout/ --max-time 120 --cmd stream_filter --settings /usr/share/coursolve/northants/.twitter_api_keys.json
