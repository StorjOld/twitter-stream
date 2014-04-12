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

    def __init__(self, configs, log_pipe):
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
            # Make sure to exclude the temporary file the grabber uses for writing new data
            files = []
            for f in os.listdir(self.configs["grabber_storage_directory"]):
                if os.path.isfile(os.path.join(self.configs["grabber_storage_directory"],f)):
                    files.append(f)
            try:
                files.remove(self.configs["grabber_temp_file"])
            except ValueError:
                # couldn't find the temp download file to remove from the list,
                # not the end of the world, so keep going
                pass

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

            # Attempt to upload the file until we hit max_retries
            upload_success = False
            max_retries = self.configs["upload_retries"]
            on_try = 0
            while upload_success == False and on_try < max_retries:
                if self.configs['verbosity'] and not(self.configs['quiet']):
                    print("Upload try %s" % on_try)
                try:
                    result = self.do_upload(self.configs["upload_url"], to_upload)
                    if result.status_code == 201:
                        self.log_pipe.send(['log', '%s %s' % ( result.status_code, json.dumps(result.text) )])
                    else:
                        self.log_pipe.send(['error', '%s %s' % ( result.status_code, json.dumps(result.text) )])
                    if self.configs['verbosity'] and not(self.configs['quiet']):
                        print(result.text)
                    upload_success = True
                except requests.exceptions.RequestException:
                    on_try += 1
            # If we hit max_retries bail on the upload process
            if upload_success == False:
                self.log_pipe.send(['error','Connection failure'])
                if not(self.configs['quiet']):
                    print("Upload of a file failed %s times, exiting upload process."  % max_retries)
                sys.exit(1)
            # If we manage to successfully upload the file then close the handle and delete the file
            else:
                to_upload.close()
                os.remove(filename)

    def do_upload(self, url, filehandle):
        """
        Do a multi-part post upload to a provided URL and return the resulting response

        Arguments:
        url -- place we're posting to
        filehandle -- the file to upload
        """
        files = {'file': filehandle}
        result = requests.post(url, files=files, timeout=2)
        return result