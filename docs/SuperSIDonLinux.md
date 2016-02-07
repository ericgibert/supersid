# SuperSID on Linux #

Version 1.4 20150801

Implementation of the SuperSID program to record Solar Induced Disturbances.

Program is tested on Fedora 16, 20, 22 on Desktop PC and Debian Wheezy & Pidorra on **Raspberry Pi**.
 
Note: this program runs on Windows. Tested on Windows 7.

## Table of Content
- [Python Requirements](#id-section1)
- [Sound Card Configuration](#id-section2)
- [To install SuperSid](#id-section3)
- [Execution](#id-section4)

<div id='id-section1'/>
## Python Requirements ##

Python interpreters are installed as:
- python: Python 2
- python3: Python 3

To install the necessary modules, you need to be *root* or to prefix the command with  *sudo*.

**matplotlib** is a key library used by SuperSid. You need to install it either directly or as a dependency as explain below.

Recommended option: to use SuperSid with text mode and GUI based on tkinter:
````
- for Python2: dnf/yum/apt-get install python-matplotlib-tk
- for Python3: dnf/yum/apt-get install python3-matplotlib-tk
````

To use SuperSid in text mode only:
````
 - for Python2: dnf/yum/apt-get install python-matplotlib
 - for Python3: dnf/yum/apt-get install python3-matplotlib
````

To use SuperSid with GUI based on wxPython:
````
 - for Python 2 only: dnf/yum/apt-get install python-matplotlib-wx
````

<div id='id-section2'/>
## Sound Card Configuration ##
The original SuperSID program uses PyAudio, which works fine on Windows. But for Linux, with ALSA, it is rather frustrating: mode selection (with high sampling rate) is not always successfull, **`jackd`** is requiered but its configuration is not cumbersome.

After various unsuccessful attempts to run SuperSID with PyAudio, I decided to switch to another library which directly captures sound at ALSA level: **alsaaudio**.  

Python 2:
````
 # yum/apt-get install python-alsaaudio
````
Python 3:
 Try to install the package as your ditribution might offer it
````
 - dnf/yum/apt-get install python3-alsaaudio
````
 Else *a la mano*:
````
 - yum install 'pkgconfig(alsa)'
 - go to https://pypi.python.org/pypi/pyalsaaudio
 - download and unpack the latest pyalsaaudio-___.tar.gz  (my current version: 0.8.2)
 - change to this directory
 - as *root* or with *sudo*:  python3 setup.py install 
````

<div id='id-section3'/>
## To install SuperSid ##

Go to your home directory and execute:
```
 # git clone https://github.com/ericgibert/supersid.git
```
In the future, change to the `~/superid` folder and execute `git pull` to update to the latest version.

A *supersid* folder is created with all the software and its documentation. Change to this directory (*cd supersid*).
Create two sub-directories:
- *mkdir Data*
- *mkdir Private*

Copy the supersid cfg files in the Config folder to the Private folder: you can now edit them to match your configuration, including changing the *data_path* to point to the *Data* sub-folder you just created.


## Specific `supersid.*.cfg` Section ##
A new section for Linux capture needs can be declared in `Config/supersid.*.cfg`. 

````
[Capture]
# Default is Audio=pyaudio
Audio=alsaaudio
Card=External  
PeriodSize=128
````

#### Card
Specify which sound card to use in the `Card` entry. To know which sound card are recognized on your Linux box execute `ls -l /proc/asound/`.  

Example on my Raspberry Pi B:
````
> ls -l /proc/asound/  
total 0
lrwxrwxrwx 1 root root 5 Jul 19 10:42 ALSA -> card0
dr-xr-xr-x 3 root root 0 Jul 19 10:42 card0
dr-xr-xr-x 4 root root 0 Jul 19 10:42 card1
-r--r--r-- 1 root root 0 Jul 19 10:42 cards
-r--r--r-- 1 root root 0 Jul 19 10:42 devices
lrwxrwxrwx 1 root root 5 Jul 19 10:42 External -> card1
-r--r--r-- 1 root root 0 Jul 19 10:42 hwdep
dr-xr-xr-x 2 root root 0 Jul 19 10:42 oss
-r--r--r-- 1 root root 0 Jul 19 10:42 pcm
dr-xr-xr-x 2 root root 0 Jul 19 10:42 seq
-r--r--r-- 1 root root 0 Jul 19 10:42 timers
-r--r--r-- 1 root root 0 Jul 19 10:42 version
````
Here the USB soundcard is identified as `External`. Thus the [Capture] section of the config file will be:
````
[Capture]
Audio=alsaaudio
Card=External
PeriodSize = 128
````

Other example on my PC:
````
ls -l /proc/asound/
total 0
dr-xr-xr-x. 6 root root 0 Jul 19 10:44 card0
dr-xr-xr-x. 3 root root 0 Jul 19 10:44 card1
-r--r--r--. 1 root root 0 Jul 19 10:44 cards
-r--r--r--. 1 root root 0 Jul 19 10:44 devices
-r--r--r--. 1 root root 0 Jul 19 10:44 hwdep
lrwxrwxrwx. 1 root root 5 Jul 19 10:44 MID -> card0
-r--r--r--. 1 root root 0 Jul 19 10:44 modules
dr-xr-xr-x. 2 root root 0 Jul 19 10:44 oss
-r--r--r--. 1 root root 0 Jul 19 10:44 pcm
lrwxrwxrwx. 1 root root 5 Jul 19 10:44 Pro -> card1
dr-xr-xr-x. 2 root root 0 Jul 19 10:44 seq
-r--r--r--. 1 root root 0 Jul 19 10:44 timers
-r--r--r--. 1 root root 0 Jul 19 10:44 version
````

I choose the MID card as the second card is my webcam:
````
[Capture]
Audio=alsaaudio
Card=MID
PeriodSize = 128
````

To check that the sampler recognizes your card properly, execute the `sample.py` module on its own:
````
python ~/supersid/supersid/sampler.py
Possible capture modules: ['alsaaudio']
Accessing MID ...
alsaaudio sound card capture on sysdefault:CARD=MID at 48000 Hz
48000 bytes read from alsaaudio sound card capture on sysdefault:CARD=MID
alsaaudio sound card capture on sysdefault:CARD=MID at 96000 Hz
96000 bytes read from alsaaudio sound card capture on sysdefault:CARD=MID
Accessing Pro ...
alsaaudio sound card capture on sysdefault:CARD=Pro at 48000 Hz
48000 bytes read from alsaaudio sound card capture on sysdefault:CARD=Pro
alsaaudio sound card capture on sysdefault:CARD=Pro at 96000 Hz
! ERROR capturing sound on card Pro
Capture data too large. Try decreasing period size

````

This confirms that both `MID` and `Pro` can be used to capture sound.

On the other hand, on the Raspberry Pi, the card0 is playback only i.e. does not allow capture. Hence the following output:
````
python supersid/supersid/sampler.py
Possible capture modules: ['alsaaudio']
Accessing ALSA ...
! ERROR accessing card ALSA
Accessing External ...
alsaaudio sound card capture on sysdefault:CARD=External at 48000 Hz
````

The first soundcard `ALSA` does not allow capture. You need to use the second card (in my case `External`).

#### PeriodSize
Number of frame ... If too big then error `error message` will be returned.
Start with `PeriodSize = 128` and optionaly try out larger power.

<div id='id-section4'/>
## Execution ##

You can execute *~/supersid/supersid.py ~/supersid/Private/superdid.text.cfg* (or any .cfg of your choice).
