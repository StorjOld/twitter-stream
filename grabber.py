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
    quiet -- print no status messages, overrides verbosity setting
    """

    def __init__(self, configs, oauth, log_pipe=None):
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

    def consume_tweets(self, heartbeat=None):
        """
        Initiates a streaming post request with the requests library and iterates over data coming in from twitter.

        Arguments:
        heartbeat -- pipe to send alive messages to the daemon
        """
        
        max_retries = self.configs["grabber_retries"]
        stream_success = False
        on_try = 0
        #DO NOT ACCESS r.text BEFORE THE FOR LOOP (for line in r.iter_items()), THE ENTIRE PROCESS WILL HANG FOREVER.
        r = None
        # Attempt to open a connection to twitter's streaming API
        while on_try < max_retries:
            if self.configs['verbosity'] and not(self.configs['quiet']):
                print("On stream try %s" % on_try)

            try:
                if self.configs['verbosity'] and not(self.configs['quiet']):
                    print("Attempting initial connection to twitter streaming URL %s" % self.url)
                r = requests.get(url=self.url, auth=self.oauth, stream=True)
                break
            except requests.exceptions.RequestException as e:
                if self.configs['verbosity'] and not(self.configs['quiet']):
                    print("Grabber failed initial stream connect! Trying again...")
                if not (self.log_pipe == None):
                    self.log_pipe.send(['error','Connection failure - %s %s' % (type(e), str(e))])
                on_try += 1

        # Logic to figure out if we actually got a good response from the twitter streaming endpoint
        if not (r == None):
            if self.configs['verbosity'] and not(self.configs['quiet']):
                print("Connected! code - %s" % r.status_code )
            # This is the only condition that will result in the process continuing to live
            if r.status_code == 200:
                stream_success = True
            # If we get a rate limit status_code from twitter, let the process relax for
            # 30 seconds but keep sending heartbeats so the daemon doesn't kill our process
            elif r.status_code == 420:
                if self.configs['verbosity'] and not(self.configs['quiet']):
                    print("Got rate limiting messsage, sleeping for 30 seconds then restarting Grabber.")
                if not (self.log_pipe == None):
                        self.log_pipe.send(['error','Connection failure - API rate limiting'])
                for x in range(0,30):
                    time.sleep(0.5)
                    if not (heartbeat == None):
                        heartbeat.send(1)
                    time.sleep(0.5)
            else:
                if self.configs['verbosity'] and not(self.configs['quiet']):
                    print( '%s %s' % ( r.status_code, json.dumps(r.text) ) )
                if not (self.log_pipe == None):
                    self.log_pipe.send(['error', '%s %s' % ( r.status_code, json.dumps(r.text) )])
        else:
            if self.configs['verbosity'] and not(self.configs['quiet']):
                print("Couldn't connect to streaming endpoint.")

        # If we didn't get a 200 status code, kill the process
        if stream_success == False:
            if not (self.log_pipe == None):
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
        write_cache_size = 1024 * 1024 * 1

        # Start reading lines from our twitter stream
        for line in r.iter_lines():
            # Send out a heartbeat to our daemon to remind it we're still alive
            if not (heartbeat == None):
                heartbeat.send(1)

            # Check if our write_cache is full and flush it out to our temp storage file
            if write_cache_size < len(write_cache):
                if self.configs['verbosity'] and not(self.configs['quiet']):
                    print("Grabber write cache full, flushing to disk.")
                wrote_file.write(write_cache)
                wrote_bytes += len(write_cache)
                write_cache = ""

            # Check if our total written out, plus whatever is in our write_cache, is bigger than the file size cutoff
            # Rename our temporary file with the current timestamp and start on a new temporary write file
            if wrote_bytes + len(write_cache) > (self.configs['grabber_cut_size'] * 1024 ):
                wrote_file.write(write_cache)
                if self.configs['verbosity'] and not(self.configs['quiet']):
                    print("Grabber working file full, renaming and creating new working file.")
                wrote_file.close()
                write_cache = ""
                dangle = 0
                while True:
                    try:
                        filename = "%s%s-%s.txt" % (self.configs["tweet_file_prefix"], str(time.time()), dangle)
                        write_filename = os.path.join(self.configs["grabber_storage_directory"], filename)
                        os.rename(self.working_file, write_filename)
                        break
                    except FileExistsError:
                        dangle += 1
                wrote_bytes = 0
                wrote_file = open(self.working_file, "w")

            # filter out keep-alive new lines
            if line:
                # decode our tweet data into a python data structure and ignore it if it isn't actually json data (some error messages)
                string_line = line.decode()
                try:
                    json.loads(string_line)
                except ValueError:
                    if not(self.configs['quiet']):
                        print("Got non-json message: %s" % string_line)
                    continue

                write_cache += string_line

if __name__ == "__main__":
    import config
    from twitter_oauth import TwitterOauth
    configs, configs_api, configs_oauth = config.get_config()
    configs["verbosity"] = True
    configs["quiet"] = False
    twitter_oauth = TwitterOauth(configs, configs_api, configs_oauth)
    oauth = twitter_oauth.get_oauth()
    grabber = Grabber(configs, oauth)
    grabber.consume_tweets()