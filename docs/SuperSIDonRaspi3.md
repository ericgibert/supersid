SuperSID on Raspberry Pi 3
==========================

1) Preparation
--------------

Latest image downloaded as .ZIP: 2019-09-26-raspbian-buster.zip
Download and use the easy tool to write this image *etcher*. Highly recommended.
Boot on the new micro-SD card, follow normal process for any fresh system install.\
Execute the classic:
- firmware upgrade
- apt-get update and upgrade

2) Extra software
-----------------

Time synchro over the Internet:
''''
    sudo apt-get install ntpdate ntp
''''
Follow tutorial at  https://victorhurdugaci.com/raspberry-pi-sync-date-and-time

Virtualenv management for Python:
````
    sudo apt-get install virtualenv
````

3) Installing SuperSID
----------------------

### 3.1) Global installation

This Raspi 3 is dedicated to SuperSid or you do not plan to mix various libraries: install at system level all the libraries.
You can do so exactly like you would do in linux:
````
sudo apt-get install python3-pip
pip3 install -r requirements.txt
````

If you prefer to install everythin manually:

````
    sudo apt-get install python3-matplotlib
    sudo apt-get install libasound2-dev

    sudo pip3 install pyalsaaudio

````


























### 3.1) optional virtualenv

This step is optional. Creating your own environment allows to install libraries in all freedom,
without 'sudo' and ensure you have a coherent and working set of libraries (soundcard).
If your Raspi is dedicated to SuperSID then you can skip this step and install all globally.

From /home/pi:
````
    virtualenv -p /usr/bin/python3.5 supersid.1.5
    source supersid.1.5/bin/activate
    cd supersid.1.5
````

This also ensures that we run in Python3.5.


### 3.2) Standard Libraries


pip install matplotlib







