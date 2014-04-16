"""
.. module:: uploader
   :platform: Unix, Windows
   :synopsis: Uploads twitter data to web nodes
.. moduleauthor:: Adam Sheesley <odd.meta@gmail.com>
"""
# requires python 3
import os
import time
import sys
import json

# 3rd party imports
import requests

class Uploader(object):
    """
    Handles all uploading of twitter data files into the web node
    and disposes of the twitter data files after they have been uploaded

    Configuration options used:
    grabber_storage_directory -- directory to hold files of twitter data
    grabber_temp_file -- name of the file the grabber uses as a working storage
    upload_retries -- number of times to attempt to upload a file to the web node before giving up
    upload_url -- URL of the web node to upload to
    verbosity -- print out a plethora of status messages
    quite -- print no status messages, overrides verbosity setting
    """

    def __init__(self, configs, log_pipe=None):
        """
        Arguments:
        configs -- list of configuration options
        log_pipe -- pipe for passing log messages back to the daemon
        """

        self.log_pipe = log_pipe
        self.configs = configs
        if self.configs['verbosity'] and not(self.configs['quiet']):
            print("Starting up uploader...")

    def upload_files(self):
        """
        Initiates the loop to upload completed twitter data files if they exist.
        If there no files exist, wait for a bit and look for files again.
        """

        while True:
            # Look for files in the twitter storage directory and shove them into a list
            tmp_files = []
            for f in os.listdir(self.configs["grabber_storage_directory"]):
                if os.path.isfile(os.path.join(self.configs["grabber_storage_directory"],f)):
                    tmp_files.append(f)
            # Make sure we only are uploading files that are finished and were created by a Grabber
            # using our config information
            files = []
            for filename in tmp_files:
                if self.configs["tweet_file_prefix"] in filename:
                    files.append(filename)


            # If we don't actually have any files to upload wait a bit and flip back to the beginning
            if len(files) == 0:
                if self.configs['verbosity'] and not(self.configs['quiet']):
                    print("no files to upload, waiting for 10 seconds.")
                time.sleep(10)
                continue

            # Pick the oldest file we can find for upload
            files.sort()
            filename = os.path.join(self.configs["grabber_storage_directory"],files[0])
            to_upload = open( filename, "rb")

            # Setup our variables for the upcoming loop
            max_retries = self.configs["upload_retries"]
            on_try = 0
            result = None
            if self.configs['verbosity'] and not(self.configs['quiet']):
                    print("Upload attempting to push file %s" % filename)

            # Attempt to upload the file until we hit max_retries
            while on_try < max_retries:
                if self.configs['verbosity'] and not(self.configs['quiet']):
                    print("Upload try %s" % on_try)
                try:
                    result = self.do_upload(self.configs["upload_url"], to_upload)
                    break
                except requests.exceptions.RequestException as e:
                    if not (self.log_pipe == None):
                        self.log_pipe.send(['error','Upload failed, %s %s' % (type(e), str(e)) ])
                    on_try += 1

            if not (result == None):
                # If we got our file up, send a message to the upload log, otherwise write to the error log
                if result.status_code == 201:
                    if not (self.log_pipe == None):
                        self.log_pipe.send(['log', '%s %s' % ( result.status_code, json.dumps(result.text) )])
                                    # If an upload is successful this is the filehash
                    if self.configs['verbosity'] and not(self.configs['quiet']):
                        print(result.text)
                    
                    # If we manage to successfully upload the file then close the handle and delete the file
                    if self.configs['verbosity'] and not(self.configs['quiet']):
                        print("Upload succeeded, deleting %s" % filename)
                    to_upload.close()
                    os.remove(filename)
                else:
                    if not (self.log_pipe == None):
                        self.log_pipe.send(['error', '%s %s' % ( result.status_code, json.dumps(result.text) )])
            else:
                # If we hit max_retries bail on the upload process
                if not (self.log_pipe == None):
                    self.log_pipe.send(['error','Upload failed %s times, killing uploader' % max_retries])
                sys.exit(1)


    def do_upload(self, url, filehandle):
        """
        Do a multi-part post upload to a provided URL and return the resulting response

        Arguments:
        url -- place we're posting to
        filehandle -- the file to upload

        Returns:
        result object with text and status_code attributes
        """
        files = {'file': filehandle}
        class FakeResult(object):
            pass
        try:
            result = requests.post(url, files=files, timeout=2)
        except MemoryError:
            result = FakeResult()
            result.text = "Out of memory error, file size too large"
            result.status_code = 0

        return result

if __name__ == "__main__":
    import config
    configs, configs_api, configs_oauth = config.get_config()
    configs["verbosity"] = True
    configs["quiet"] = False
    uploader = Uploader(configs)
    uploader.upload_files()