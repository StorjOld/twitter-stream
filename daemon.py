#!/usr/bin/env python
# requires python 3
"""
.. module:: daemon
   :platform: Unix, Windows
   :synopsis: Manages the uploader and grabber processes, performs configuration on first run
.. moduleauthor:: Adam Sheesley <odd.meta@gmail.com>
"""
import sys
compat = True
try:
    if sys.version_info.major < 3:
        compat = False
except NameError:
    compat = False
finally:
    if compat == False:
        print("This script was built on python 3.4.")
        print("A few modifications can probably make it work on python 2.x.")
        print("However it will not work as is.\nHave a nice day.")
        sys.exit(0)

import json
import time
import signal
import multiprocessing
import argparse
import os

# 3rd party imports
import requests

# custom module imports
from twitter_oauth import TwitterOauth
from grabber import Grabber
from uploader import Uploader
import config

def create_grabber(configs, twitter_oauth):
    """
    Setup the twitter grabber object and fire off the twitter grabber process.

    Keyword arguments:
    configs -- list of configuration options
    twitter_oauth -- TwitterOauth object with all proper keys configured

    Returns:
    grabber_process -- reference to the running grabber process
    grabber_heartbeat -- dedicated pipe to check if the grabber process is alive 
    grabber_log_pipe -- pipe for the grabber process to pass out log events
    """
    oauth = twitter_oauth.get_oauth()
    grabber_heartbeat, b = multiprocessing.Pipe()
    grabber_log_pipe, glp = multiprocessing.Pipe()
    grabber = Grabber(configs, oauth, glp)
    grabber_process = multiprocessing.Process( target=grabber_runner, args=(grabber,b,) )
    grabber_process.daemon = True
    grabber_process.start()
    return grabber_process, grabber_heartbeat, grabber_log_pipe


def grabber_runner(grabber, heartbeat):
    """
    Actual function that is pushed into another process to run the twitter grabber.

    Keyword arguments:
    grabber -- an object of the Grabber class
    heartbeat -- pipe for the grabber process to continually announce alive state over
    """
    # Add a message nicer than an error when our user exits with ctrl+c
    def signal_handler(signal, frame):
        print('Exiting grabber process...')
        sys.exit(0)
    # Assign our custom interrupt handler to the grabber process
    signal.signal(signal.SIGINT, signal_handler)
    # Fire off the grabber into a perpetual loop
    grabber.consume_tweets(heartbeat)


def create_uploader(configs):
    """
    Setup the web node uploader process and return it.

    Keyword arguments:
    configs -- list of configuration options

    Returns:
    uploader_process -- reference to the running uploader process
    uploader_log_pipe -- pipe for the uploader process to pass out log events
    """
    uploader_log_pipe, ulp = multiprocessing.Pipe()
    uploader = Uploader(configs, ulp)
    uploader_process = multiprocessing.Process(target=uploader_runner, args=(uploader,))
    uploader_process.daemon = True
    uploader_process.start()
    return uploader_process, uploader_log_pipe


def uploader_runner(uploader):
    """
    Actual function that is pushed into another process to run the web node uploader.

    Keyword arguments:
    uploader -- an object of the Uploader class
    """
    # Add a message nicer than an error when our user exits with ctrl+c
    def signal_handler(signal, frame):
        print('Exiting uploader process...')
        sys.exit(0)
        # Assign our custom interrupt handler to the uploader process
    signal.signal(signal.SIGINT, signal_handler)
    # Fire off the uploader into a perpetual loop
    uploader.upload_files()


def get_args():
    """
    Use argparse to define and pull in our command line arguments.

    Returns:
    args -- object with properties that match the long names of arguments
    """
    parser = argparse.ArgumentParser(description='Twitter Stream:\nUpload the twitter sample stream into a web node')
    parser.add_argument("-v", "--verbosity", help="increase output verbosity", action="store_true")
    parser.add_argument("-q", "--quiet", help="supress all messages", action="store_true")
    args = parser.parse_args()
    return args


def start():
    """
    Primary daemon process. Manages twitter oauth setup, grabber and uploader process setup, logging 
    to various log files, and restarting the grabber and uploader processes.
    """
    # Add a message nicer than an error when our user exits with ctrl+c
    def signal_handler(signal, frame):
        print('Exiting daemon process...')
        sys.exit(0)
    # Assign our custom interrupt handler for the main (daemon) process
    signal.signal(signal.SIGINT, signal_handler)

    args = get_args()
    configs, configs_api, configs_oauth = config.get_config()
    if "verbosity" not in configs:
        configs["verbosity"] = args.verbosity
    if "quiet" not in configs:
        configs["quiet"] = args.quiet

    if configs['warn']:
        print("This script saves all keys, secrets, and tokens into configuration files in the same directory.")
        print("If you are working in a shared computing environment please set permissions and umask values to prevent unauthorized access.")
        print("This message will not appear again.")
        config.set_warn("0")

    twitter_oauth = TwitterOauth(configs, configs_api, configs_oauth)
    if not twitter_oauth.check_client_config():
        print("Consumer key and secret have not been configured.")
        print("Please edit the values of CONSUMER_KEY and CONSUMER_SECRET in config.py")
        print("Visit https://apps.twitter.com/ to create an application and aquire these values (API key and API secret)")
        sys.exit(1)

    if not twitter_oauth.check_oauth_config():
        print("This script has not been authorized for any twitter accounts.")
        print("Follow the instructions to authorize this script to a twitter user's account.")
        print("This is necessary even if you generated the consumer key and secret with a twitter account you control.")
        token, secret = twitter_oauth.setup_oauth()
        twitter_oauth.set_oauth_config(token, secret)
        config.save_oauth_config(token, secret, configs['config_twitter_oauth_filename'])


    # Fire off the grabber and uploader processes
    grabber_process, grabber_heartbeat, grabber_log_pipe = create_grabber(configs, twitter_oauth)
    uploader_process, uploader_log_pipe = create_uploader(configs)

    if not(configs['quiet']):
        print("Started and grabbing.\nStatus messages will be shown when a file is rolled.\nEdit config.ini to change script behavior.")
        print("Edit or delete config_twitter_oauth.ini to reconfigure authorized twitter account.")
        print("Edit or delete config_twitter_api.ini to reconfigure twitter application key and secret.")
        print("Ctrl+C to exit.")

    # Setup our grabber's heartbeat timeout
    timeout = 5
    last_beat = time.time()

    while True:
        # Check if our grabber has any log messages for us and write them to the appropriate log file
        if grabber_log_pipe.poll():
            log_file = open( os.path.join(configs["log_directory"], "error.log"), "a" )
            log_data = grabber_log_pipe.recv()
            log_line = "%s %s %s" % (time.time(), "grabber", log_data[1])
            log_file.write("%s\n" % log_line)
            log_file.close()

        # Check if our uploader has any log messages for us and write them to the appropriate log file
        if uploader_log_pipe.poll():
            log_file = open( os.path.join(configs["log_directory"], "error.log"), "a" )
            log_data = uploader_log_pipe.recv()
            if log_data[0] == "error":
                log_file = open( os.path.join(configs["log_directory"], "error.log"), "a" )
            else:
                log_file = open( os.path.join(configs["log_directory"], "upload.log"), "a" )
            log_line = "%s %s %s" % (time.time(), "uploader", log_data[1])
            log_file.write("%s\n" % log_line)
            log_file.close()

        # Check if our uploader process is dead the proper way and restart it if it is dead
        if not (uploader_process.is_alive()):
            if not(configs['quiet']):
                    print("Upload process cannot connect... restarting upload process.")
            uploader_process, uploader_log_pipe = create_uploader(configs)

        # Round about way to check if the grabber process has hung up, kill it if it has hung and restart it
        # This round-about process is required due to requests literally hanging up the entire process
        # if a stream stops returning data
        has_beat = grabber_heartbeat.poll()
        if has_beat == True:
            beat = grabber_heartbeat.recv()
            last_beat = time.time()
        if (time.time() - last_beat) > timeout:
            if not(configs['quiet']):
                    print("Grabber process has lost connection... restarting grabber process.")
            last_beat = time.time() + 5
            grabber_process.terminate()
            grabber_process, grabber_heartbeat, grabber_log_pipe = create_grabber(configs, twitter_oauth)

if __name__ == "__main__":
    start()