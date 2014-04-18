twitter-stream
==============

Store Twitter streaming API data for testing.

These scripts connect to https://stream.twitter.com/1.1/statuses/sample.json, store twitter data in files that are approximately 1MB large, and then uploads all finished files to twitter.

Designed to run unattended for an extended period of time after initial oauth setup. Information provided in initial oauth setup is saved to disk and used on all further script runs. Scripts are designed to gracefully handle intermittent connection issues with Twitter, Storj nodes, or both.

To run on a remote server for an extended period of time the command line utility `screen` is recommended.

All logs are written to the "logs" directory by default.

All temporary data files are written to the "store" directory by default.

May be run with the -v option for detailed console logging during operation.

# Quick start
1. Follow the instructions in INSTALL.md
1. run ./twitter-stream
2. Follow the prompts to input twitter app keys and to authorize the app with a twitter account. 
   The app account and the user the app is authorized against can be the same account.

The daemon.py script is now configured for automatic function and should work uninterrupted as long as the application remains authorized by the twitter account and the application's API key and secret are not regenerated.

# Configuration files
## config.ini
### Twitter Grabber Configuration
* `grabber_cut_size` The size of files to be uploaded to twitter in kilobytes
* `grabber_storage_directory` The directory to store temporary twitter files in
* `stream_url` The URL that the grabber uses to stream tweets from
* `grabber_retries` The number of times the Grabber will attempt to reconnect to the stream_url on initial connection
* `config_twitter_oauth_filename` The name of the file that twitter oauth token and secret will be stored in
* `grabber_temp_file` The working file that a Grabber object uses to store tweets before the cut size has been reached
* `config_twitter_api_filename` The name of the file that twitter API key and secret will be stored in
* `request_token_url` Part of twitter's oauth infrastructure, do not change unless twitter has changed this
* `authorize_url` Part of twitter's oauth infrastructure, do not change unless twitter has changed this
* `access_token_url` Part of twitter's oauth infrastructure, do not change unless twitter has changed this

### Uploader Configuration
* `upload_url` The storj webnode URI to attempt an upload to
* `upload_retries` The number of times to attempt to retry an upload to the storj webnode before restarting process

### General Script Configuration
* `log_directory` The directory that log files are stored in
* `tweet_file_prefix` An arbitrary prefix for all files that an Uploader will scoop up
* `warn` Show the warning message about key, secret, and token storage on the filesystem


# Misc Details
The daemon.py script acts as a controller that promts the user to setup oauth if it is not configured and kicks off grabber.py and uploader.py in their own processes. All twitter data is saved into the directory defined in config.ini. By default this is set to /var/www. Ensure that the user running the script has permission to read and write to this directory. The size of each file uploaded is defined by grabber_cut_size in config.ini in kilobytes. To specify 32 KB files set "grabber_cut_size = 32". To specify 1 MB, set "grabber_cut_size = 1024".

Upload objects currently read in the entire file at once from disk and then attempt to upload it. This can result in a MemoryError for large files

# Dependencies
oauthlib 0.6.1
https://pypi.python.org/pypi/oauthlib

requests 2.2.1
https://pypi.python.org/pypi/requests

requests_oauthlib 0.4.0
https://github.com/requests/requests-oauthlib/tree/v0.4.0

# attribution
primary twitter_oauth.py piece derived from
http://thomassileo.com/blog/2013/01/25/using-twitter-rest-api-v1-dot-1-with-python/