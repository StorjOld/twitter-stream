"""
.. module:: grabber
   :platform: Unix, Windows
   :synopsis: Grabs data from the twitter streaming API
.. moduleauthor:: Adam Sheesley <odd.meta@gmail.com>
"""
# requires python 3

import time
import json
import os
import sys
import pprint

# 3rd party imports
import requests

"""
TODO: make chunk size a human friendly storage value, 1MB, 1KB, etc
"""

class Grabber(object):
    """
    The Grabber class is used to contain all code relevant to pulling streaming
    data from twitter and writing it out to a collection of files.

    Configuration options used:
    stream_url -- twitter stream URL to pull from
    grabber_storage_directory -- directory to hold files of twitter data
    grabber_temp_file -- name of the file the grabber uses as a working storage
    grabber_cut_size -- size of twitter data storage files in kilobytes
    grabber_retries -- number of times the grabber retries accessing the twitter stream URL
    verbosity -- print out a plethora of status messages
    quite -- print no status messages, overrides verbosity setting
    """

    def __init__(self, configs, oauth, log_pipe):
        """
        Arguments:
        configs -- list of configuration options
        oauth -- oauth object to use with twitter requests
        log_pipe -- pipe for passing log messages back to the daemon
        """

        self.log_pipe = log_pipe
        self.url = configs["stream_url"]
        self.oauth = oauth
        self.configs = configs
        self.working_file = os.path.join(configs["grabber_storage_directory"], self.configs["grabber_temp_file"])
        if self.configs['verbosity'] and not(self.configs['quiet']):
            print("Starting up twitter grabber...")

    def consume_tweets(self, heartbeat):
        """
        Initiates a streaming post request with the requests library and iterates over data coming in from twitter.

        Arguments:
        heartbeat -- pipe to send alive messages to the daemon
        """
        
        # Attempt to open a connection to twitter's streaming API
        max_retries = self.configs["grabber_retries"]
        stream_success = False
        on_try = 0
        while stream_success == False and on_try < max_retries:
            if self.configs['verbosity'] and not(self.configs['quiet']):
                print("on stream try %s" % on_try)
            try:
                r = requests.post(url=self.url, auth=self.oauth, stream=True, data={}, timeout=2)
                if r.status_code is not 200:
                    self.log_pipe.send(['error', '%s %s' % ( r.status_code, json.dumps(r.text) )])
                stream_success = True
            except requests.exceptions.RequestException:
                on_try += 1

        # If we failed to open a stream after all our max tries kill the grabber process, daemon is in charge of restarting it
        if stream_success == False:
            self.log_pipe.send(['error','Connection failure'])
            if not(self.configs['quiet']):
                print("Connection to %s failed %s times, exiting grabber process."  % (self.url, max_retries) )
            sys.exit(1)

        # Open our working file to write tweets out to
        wrote_file = open(self.working_file, "w")
        # Setup our counter to keep track of how much we've written to our temporary file
        wrote_bytes = 0
        # Setup a write cache to save twitter data in so we're not writing to a file every time we read a line
        write_cache = ""
        # Define our maximum write_cache size in bytes (1024 * 1024) == 1MB
        write_cache_size = 1024 * 1024 * 10

        # Start reading lines from our twitter stream
        for line in r.iter_lines():
            # Send out a heartbeat to our daemon to remind it we're still alive
            heartbeat.send(1)

            # Check if our write_cache is full and flush it out to our temp storage file
            if write_cache_size < len(write_cache):
                wrote_file.write(write_cache)
                wrote_bytes += len(write_cache)
                write_cache = ""

            # Check if our total written out, plus whatever is in our write_cache, is bigger than the file size cutoff
            # Rename our temporary file with the current timestamp and start on a new temporary write file
            if wrote_bytes + len(write_cache) > (self.configs['grabber_cut_size'] * 1024 ):
                wrote_file.write(write_cache)
                if self.configs['verbosity'] and not(self.configs['quiet']):
                    print("creating new file...")
                wrote_file.close()
                write_cache = ""
                os.rename(self.working_file, os.path.join(self.configs["grabber_storage_directory"], str(time.time()) + ".txt"))
                wrote_bytes = 0
                wrote_file = open(self.working_file, "w")

            # filter out keep-alive new lines
            if line:
                # decode our tweet data into a python data structure and ignore it if it isn't actually json data (some error messages)
                tweet = {}
                try:
                    tweet = json.loads(line.decode())
                except Exception:
                    pass
                if "text" in tweet:
                    store_tweet = {"text":tweet['text'], "created":tweet['created_at'], "screen_name":tweet['user']['screen_name'], "id":tweet['id']}
                    json_tweet = json.dumps(store_tweet)
                    write_cache += json_tweet