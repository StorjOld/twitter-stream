# INSTALL

These steps were built to work with debian 7 (wheezy) 64 bit.

First install python 3 

    apt-get install python3.2

First we want to install virtualenv 

    apt-get install python-virtualenv

If you have elevated to root, exit now

Run setup our clean virtual environment with python3.2

    virtualenv --python=/usr/bin/python3.2 ".env"

activate our virtual environment

    source .env/bin/activate

install our dependencies

    pip install -r requirements.txt

deactivate the virtual environment

    deactivate

Allow "twitter-stream" to be executed

    chmod u+x twitter-stream

To run:

    ./twitter-stream [-v [-q]]
