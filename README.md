twitter-stream
==============

Store Twitter streaming API data for testing.

These scripts connect to https://stream.twitter.com/1.1/statuses/sample.json, store twitter data in files that are approximately 1MB large, and then uploads all finished files to a storj web node.

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
* `grabber_cut_size` Size of files to be uploaded to webnode in kilobytes
* `grabber_storage_directory` Directory to store temporary twitter files in
* `stream_url` URI that the grabber uses to stream tweets from
* `grabber_retries` Times the Grabber will attempt to reconnect to the stream_url on initial connection
* `config_twitter_oauth_filename` Name of the file that twitter oauth token and secret will be stored in
* `grabber_temp_file` File the Grabber uses to store tweets before the cut size has been reached
* `config_twitter_api_filename` Name of the file that twitter API key and secret will be stored in
* `request_token_url` Part of twitter's oauth infrastructure, do not change unless twitter has changed this
* `authorize_url` Part of twitter's oauth infrastructure, do not change unless twitter has changed this
* `access_token_url` Part of twitter's oauth infrastructure, do not change unless twitter has changed this

### Uploader Configuration
* `upload_url` Storj webnode URI to attempt an upload to
* `upload_retries` Number of times to attempt to retry an upload to the webnode before restarting process

### General Script Configuration
* `log_directory` Directory that log files are stored in
* `tweet_file_prefix` An arbitrary prefix for all files that an Uploader will scoop up
* `warn` Show the warning message about key, secret, and token storage on the filesystem


# Operational Details
The `daemon.py` script acts as a controller that prompts the user to setup oauth if it is not configured and kicks off `grabber.py` and `uploader.py` in their own processes. Twitter data is then streamed into files by the grabber process. The uploader process constantly scans for files that are complete, uploading any completed files that it finds. 

In the event of a connection dropout, from either twitter, the webnode, or both, each process will attempt to reconnect a set number of times and then terminate if it is unsuccessful. The daemon constantly checks for a dead uploader process and a dead grabber process; restarting the processes as necessary. The `grabber.py` and `uploader.py` scripts will continue to run until the process running `daemon.py` is killed.

Both `grabber.py` and `uploader.py` can be run independently if the proper configuration information is present in `config.ini`, `config_twitter_api.ini`, and `config_twitter_oauth.ini`. This can be useful for uploading files that were not created with `grabber.py` or streaming twitter data into files for purposes other than uploading to a webnode.


# Issues
Currently Upload objects read in the entire file at once from disk and then attempt to upload it. This can result in a MemoryError for large files. Testing has indicated files around 900MB can cause this problem, based on research this is entirely dependent on how much memory the system has. To fix this issue files would need to be uploaded as they are read from disk. This StackOverflow posting provides a [sample implementation](http://stackoverflow.com/a/16221027).

# Dependencies
* [requests 2.2.1](https://pypi.python.org/pypi/requests) is used to stream down tweets from twitter and upload files to webnodes
* [requests_oauthlib 0.4.0](https://github.com/requests/requests-oauthlib/tree/v0.4.0) is used for twitter's oauth
* [oauthlib 0.6.1](https://pypi.python.org/pypi/oauthlib) is used by `requests_oauthlib`