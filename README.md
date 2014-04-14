twitter-stream
==============

Store Twitter streaming API data for testing.

# Quick start
1. Follow the instructions in INSTALL.md
1. run ./twitter-stream
2. Follow the prompts to input twitter app keys and to authorize the app with a twitter account. 
   The app account and the user the app is authorized against can be the same account.

The daemon.py script is now configured for automatic function and should work uninterrupted as long as the application remains authorized by the twitter account and the application's API key and secret are not regenerated.

# Description
The daemon.py script acts as a controller that promts the user to setup oauth if it is not configured and kicks off grabber.py and uploader.py in their own processes. All twitter data is saved into the directory defined in config.ini. By default this is set to /var/www. Ensure that the user running the script has permission to read and write to this directory. The size of each file uploaded is defined by grabber_cut_size in config.ini in kilobytes. To specify 32 KB files set "grabber_cut_size = 32". To specify 1 MB, set "grabber_cut_size = 1024".

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