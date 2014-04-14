# Dependencies

These steps were built to work with debian 7 (wheezy) 64 bit.

First install python 3
    apt-get install python3.2

First we want to install virtualenv 
    apt-get install python-virtualenv

run setup our clean virtual environment with python3.2
    virtualenv --python=/usr/bin/python3.2 ".env"

activate our virtual environment
    source .env/bin/activate

install our dependencies
    pip install -r requirements.txt

deactivate the virtual environment
    deactivate

You should now be setup to run. You may have to chmod u+x the twitter-stream script.

To run:
    ./twitter-stream [-v [-q]]