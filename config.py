"""
.. module:: config
   :platform: Unix, Windows
   :synopsis: Sets up the entire config list for the other modules
.. moduleauthor:: Adam Sheesley <odd.meta@gmail.com>
"""
# requires python 3

import configparser

CONFIG_FILE = "config.ini"

def get_config():
    """
    Pulls in all the configuration options from ini files

    Returns:
    config_store -- a list that contains most options
    config_api_store -- a list that contains the twitter app API key and secret for this script
    config_oauth_store -- a list that contains the twitter user key and secret for oauth
    """
    config_store = {}
    config_api_store = {}
    config_oauth_store = {}

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    config_store["grabber_cut_size"] = int(config['DEFAULT']['grabber_cut_size'])
    config_store["grabber_storage_directory"] = config['DEFAULT']['grabber_storage_directory']
    config_store["config_twitter_oauth_filename"] = config['DEFAULT']['config_twitter_oauth_filename']
    config_store["config_twitter_api_filename"] = config['DEFAULT']['config_twitter_api_filename']
    config_store["REQUEST_TOKEN_URL"] = config['DEFAULT']['REQUEST_TOKEN_URL']
    config_store["AUTHORIZE_URL"] = config['DEFAULT']['AUTHORIZE_URL']
    config_store["ACCESS_TOKEN_URL"] = config['DEFAULT']['ACCESS_TOKEN_URL']
    config_store["warn"] = config.getboolean('DEFAULT','warn')
    config_store["stream_url"] = config['DEFAULT']['stream_url']
    config_store["grabber_temp_file"] = config['DEFAULT']['grabber_temp_file']
    config_store["upload_url"] = config['DEFAULT']['upload_url']
    config_store["upload_retries"] = int(config['DEFAULT']['upload_retries'])
    config_store["grabber_retries"] = int(config['DEFAULT']['grabber_retries'])
    config_store["log_directory"] = config['DEFAULT']['log_directory']
    config_store["tweet_file_prefix"] = config['DEFAULT']['tweet_file_prefix']
    config_api_store = get_api_config(config_store["config_twitter_api_filename"])
    config_oauth_store = get_oauth_config(config_store["config_twitter_oauth_filename"])
    return config_store, config_api_store, config_oauth_store

def get_api_config(filename):
    """
    Attempt to pull in twitter app API key and secret. If the key 
    and secret don't exist prompt for them.

    Arguments:
    filename -- name of the config file to try and parse
    
    Returns:
    config_api_store -- contains the twitter API key and secret
    """

    config_api_store = {}
    config_twiter_api = configparser.ConfigParser()
    config_twiter_api.read(filename)
    # Try and find the API key and secret in the config file
    try:
        config_api_store["CONSUMER_KEY"] = config_twiter_api['DEFAULT']['CONSUMER_KEY']
        config_api_store["CONSUMER_SECRET"] = config_twiter_api['DEFAULT']['CONSUMER_SECRET']
    # If we can't find them, prompt for them and write them in to the configuration file
    except KeyError:
        print("Visit https://apps.twitter.com/ to create an application and aquire these values (API key and API secret)")
        config_api_store["CONSUMER_KEY"] = input("Please enter a valid twitter app API key: ")
        config_api_store["CONSUMER_SECRET"] = input("Please enter a valid twitter app API secret: ")
        api_config_file = configparser.ConfigParser()
        api_config_file['DEFAULT'] = {'CONSUMER_KEY': config_api_store["CONSUMER_KEY"], 'CONSUMER_SECRET': config_api_store["CONSUMER_SECRET"]}
        with open(filename, 'w') as configfile:
            api_config_file.write(configfile)
    return config_api_store

def get_oauth_config(filename):
    """
    Attempt to pull in twitter user key and secret from the 
    config file. If the key and secret don't exist set them to none.

    Arguments:
    filename -- name of the config file to try and parse
    
    Returns:
    config_api_store -- contains the twitter API key and secret
    """
    config_oauth_store = {}
    config_twiter_oauth = configparser.ConfigParser()
    config_twiter_oauth.read(filename)
    try:
        if config_twiter_oauth['DEFAULT']['OAUTH_TOKEN'] == "None":
            config_oauth_store["OAUTH_TOKEN"] = None
        else:
            config_oauth_store["OAUTH_TOKEN"] = config_twiter_oauth['DEFAULT']['OAUTH_TOKEN']
        if config_twiter_oauth['DEFAULT']['OAUTH_TOKEN_SECRET'] == "None":
            config_oauth_store["OAUTH_TOKEN_SECRET"] = None
        else:
            config_oauth_store["OAUTH_TOKEN_SECRET"] = config_twiter_oauth['DEFAULT']['OAUTH_TOKEN_SECRET']
    except KeyError:
        config_oauth_store["OAUTH_TOKEN"] = None
        config_oauth_store["OAUTH_TOKEN_SECRET"] = None
        oauth_config_file = configparser.ConfigParser()
        oauth_config_file['DEFAULT'] = {'OAUTH_TOKEN': 'None', 'OAUTH_TOKEN_SECRET': 'None'}
        with open(filename, 'w') as configfile:
            oauth_config_file.write(configfile)
    return config_oauth_store

def save_api_config(key, secret, filename):
    """
    Save a twitter API key and secret to a given config file.

    Arguments:
    key -- API key to save
    secret -- API secret to save
    filename -- config file name to save stuff to
    """
    api_config_file = configparser.ConfigParser()
    api_config_file['DEFAULT'] = {'CONSUMER_KEY': key, 'CONSUMER_SECRET': secret}
    with open(filename, 'w') as configfile:
        api_config_file.write(configfile)

def save_oauth_config(token, secret, filename):
    """
    Save a twitter user key and secret to a given config file.

    Arguments:
    key -- API key to save
    secret -- API secret to save
    filename -- config file name to save stuff to
    """
    oauth_config_file = configparser.ConfigParser()
    oauth_config_file['DEFAULT'] = {'OAUTH_TOKEN': token, 'OAUTH_TOKEN_SECRET': secret}
    with open(filename, 'w') as configfile:
        oauth_config_file.write(configfile)

def set_warn(warn):
    """
    Turns off the warning message about storage of keys and secrets after
    the first script run.

    Arguments:
    warn -- value to set the warn option to
    """
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    config['DEFAULT']['warn'] = warn
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)