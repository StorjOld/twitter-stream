"""
.. module:: twitter_oauth
   :platform: Unix, Windows
   :synopsis: Sets up and creates oauth objects for twitter APIs
.. moduleauthor:: Adam Sheesley <odd.meta@gmail.com>
"""
#requires python 3
from urllib import parse
import json
import time
import configparser

#3rd party imports
import requests
from requests_oauthlib import OAuth1

#config imports
import config

class TwitterOauth(object):
    """
    Handles setup and configuration of twitter oauth.

    Configuration options used:
    REQUEST_TOKEN_URL -- twitter token request URL
    AUTHORIZE_URL -- twitter authorization URL
    ACCESS_TOKEN_URL -- twitter token access URL

    CONSUMER_KEY -- twitter API key
    CONSUMER_SECRET -- twitter API secret

    OAUTH_TOKEN -- twitter user oauth token
    OAUTH_TOKEN_SECRET -- twitter user oauth secret
    """

    def __init__(self, config, config_api, config_oauth):
        """
        Arguments:
        config -- list of most config options
        config_api -- contains twitter API options
        config_oauth -- contains twitter user oauth options
        """
        self.REQUEST_TOKEN_URL = config["REQUEST_TOKEN_URL"]
        self.AUTHORIZE_URL = config["AUTHORIZE_URL"]
        self.ACCESS_TOKEN_URL = config["ACCESS_TOKEN_URL"]

        self.CONSUMER_KEY = config_api['CONSUMER_KEY']
        self.CONSUMER_SECRET = config_api['CONSUMER_SECRET']

        self.OAUTH_TOKEN = config_oauth['OAUTH_TOKEN']
        self.OAUTH_TOKEN_SECRET = config_oauth['OAUTH_TOKEN_SECRET']

    def setup_oauth(self):
        """Authorize your app via identifier."""
        # Request token
        oauth = OAuth1(self.CONSUMER_KEY, client_secret=self.CONSUMER_SECRET)
        r = requests.post(url=self.REQUEST_TOKEN_URL, auth=oauth)
        credentials = parse.parse_qs(r.content)

        resource_owner_key = credentials[b'oauth_token'][0].decode()
        resource_owner_secret = credentials[b'oauth_token_secret'][0].decode()

        # Authorize
        authorize_url = self.AUTHORIZE_URL + resource_owner_key
        print('Please go here and authorize: ' + authorize_url)

        verifier = input('Please input the verifier pin: ')
        oauth = OAuth1(self.CONSUMER_KEY,
                       client_secret=self.CONSUMER_SECRET,
                       resource_owner_key=resource_owner_key,
                       resource_owner_secret=resource_owner_secret,
                       verifier=verifier)
        # Finally, Obtain the Access Token
        r = requests.post(url=self.ACCESS_TOKEN_URL, auth=oauth)
        credentials = parse.parse_qs(r.content)
        token = credentials[b'oauth_token'][0].decode()
        secret = credentials[b'oauth_token_secret'][0].decode()
        return token, secret

    def get_oauth(self):
        """
        Use the requests_oauthlib to get a valid oauth object for twitter

        Returns:
        oauth -- contians twitter oauth object

        """
        oauth = OAuth1(self.CONSUMER_KEY,
                    client_secret=self.CONSUMER_SECRET,
                    resource_owner_key=self.OAUTH_TOKEN,
                    resource_owner_secret=self.OAUTH_TOKEN_SECRET)
        return oauth

    def set_oauth_config(self, token, secret):
        """
        Set the twitter user oauth token and secret for the object

        Arguments:
        token -- twitter user oauth token
        secret -- twitter user oauth secret
        """

        self.OAUTH_TOKEN = token
        self.OAUTH_TOKEN_SECRET = secret

    def save_oauth_config(self, token, secret):
        """
        Save the oauth token and secret to the config file

        Arguments:
        token -- twitter user oauth token
        secret -- twitter user oauth secret
        """

        self.OAUTH_TOKEN = token
        self.OAUTH_TOKEN_SECRET = secret
        oauth_config_file = open(config.config_twitter_oauth_filename,"w")
        file_string = "[DEFAULT]\nOAUTH_TOKEN = \"" + self.OAUTH_TOKEN + "\"\n" + "OAUTH_TOKEN_SECRET = \"" + self.OAUTH_TOKEN_SECRET + "\""
        oauth_config_file.write(file_string)
        oauth_config_file.close()

    def check_oauth_config(self):
        """
        Check if the oauth token and secret are set
        """
        is_configured = True
        try:
            if self.OAUTH_TOKEN is None or self.OAUTH_TOKEN_SECRET is None:
                is_configured = False
        except AttributeError:
            is_configured = False
        return is_configured

    def check_client_config(self):
        """
        Check if the twitter api key and secret are set
        """
        is_configured = True
        try:
            if self.CONSUMER_KEY is None or self.CONSUMER_SECRET is None:
                is_configured = False
        except AttributeError:
            is_configured = False
        return is_configured