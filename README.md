twitter-stream
==============

Store Twitter streaming API data for testing.

# quick start
1. Run daemon.py
2. Login to https://twitter.com with a valid twitter account
3. Visit https://apps.twitter.com/app in the same browser session you logged in with
4. Click the "Create New App" button
5. Enter all required information; Name, Description, and Website
    this will result in generating the consumer key and secret with the signed in twitter account
6. You should be taken to the application management screen for the application you just created.
7. Click on the "API Keys" tab 
8. Enter the "API key" and API secret into the prompts.

The final config.py setup should look something like
CONSUMER_KEY = "random_api_key_string_copied_from_twitter"
CONSUMER_SECRET = "random_api_secret_string_copied_from_twitter"

9. You will be prompted to authorize the application to a given twitter account; you can use the same twitter account you created the API key and secret with
10. Copy the URL provided by the script and visit it with a browser session that has been logged into twitter.com
11. Click "Authorize app"
12. Copy and paste the seven digit pin into the script's prompt and press enter

The daemon.py script is now configured for automatic function and should work uninterrupted as long as the application remains authorized by the twitter account and the application's API key and secret are not regenerated.

# theory of operation
daemon.py acts as a controller that helps initially setup oauth and kicks off grabber.py and uploader.py 
in their own processes. All twitter data is saved into the directory defined in config.ini. The size of each file uploaded
is defined by grabber_cut_size in config.ini in kilobytes.

# depends
oauthlib 0.6.1
https://pypi.python.org/pypi/oauthlib

requests 2.2.1
https://pypi.python.org/pypi/requests

requests_oauthlib 4.0
https://github.com/requests/requests-oauthlib/tree/v0.4.0

# attribution
primary twitter_oauth.py piece derived from
http://thomassileo.com/blog/2013/01/25/using-twitter-rest-api-v1-dot-1-with-python/