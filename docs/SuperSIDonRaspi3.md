SuperSID on Raspberry Pi 3
==========================

Preparation
-----------

Latest image downloaded as .ZIP
Download and use the easy tool to write this image *etcher*. Highly recommended.
Boot on the new micro-SD card, follow normal process for any fresh system install.\
Execute the classic:
- firmware upgrade
- apt-get update and upgrade

Upd 27/01/2021: Raspbian GNU/Linux 9 (stretch)


1) Get the latest supersid software
-----------------------------------

Get the source from GitHub.com

```
cd ~
git clone https://github.com/ericgibert/supersid.git
```

To update (pull) to the latest version, do:
```
	cd ~/supersid
	git pull
```


2) Extra software
-----------------

Time synchro over the Internet:
```
    sudo apt-get install ntpdate ntp
```
Follow tutorial at  https://victorhurdugaci.com/raspberry-pi-sync-date-and-time

Virtualenv management for Python:
````
    sudo apt-get install mkvirtualenv
````
Numpy also requires a special package (for opening `shared object (.so)` files):
```
sudo apt-get install libatlas-base-dev
```


3) Installing SuperSID
----------------------
### 3.1) optional virtual environment

This step is optional. Creating your own environment allows to install libraries in all freedom,
without 'sudo' and ensure you have a coherent and working set of libraries (soundcard).
If your Raspi is dedicated to SuperSID then you can skip this step and install all globally.

From /home/pi:
````
    cd ~/supersid
    mkvirtualenv -p /usr/bin/python3 supersid
    workon supersid
    toggleglobalsitepackages
````

Your prompt should now start with '(supersid)'

This also ensures that we run in Python3.5.3 as per current configuration.


### 3.2) Global or local installation

This Raspi 3 is dedicated to SuperSid or you do not plan to mix various libraries: install at system level all the libraries.
You can do so exactly like you would do in linux, for an local installation inside the virtual environement by first executing 'workon supersid'.


````
    sudo apt-get install python3-matplotlib
    sudo apt-get install libasound2-dev

    pip3 install -r requirements.txt
````

4) Choosing your USB Soundcard
------------------------------

Execute first the command 'alsamixer' to ensure that the card is recorgnzed and in proper order of functioning.
Make sure that sound can be captured from it, and that the input volume is between 80 and 90.

Do the following:

``` 
	cd ~/supersid/supersid
	python3 sampler.py 
``` 

Find the right card line you want to use based on the card name and the frquency you want to sample.

In my case:

alsaaudio sound card capture on sysdefault:CARD=External at 48000 Hz
48000 bytes read from alsaaudio sound card capture on sysdefault:CARD=External (48000,)

This means that in the configuration file, I will have:

[PARAMETERS]
audio_sampling_rate = 48000

[Capture]
Audio=alsaaudio
Card=External
PeriodSize = 128





































