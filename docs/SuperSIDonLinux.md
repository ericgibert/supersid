# SuperSID on Linux #

Implementation of the SuperSID program to record Solar Induced Disturbances on a Linux platform.

Program is tested on Fedora 16, 20, 22 on Desktop PC and Debian Wheezy on **Raspberry Pi** & Pidorra. 

## Python Requirements ##

Python interpreters are installed as:
- python: Python 2
- python3: Python 3

To install the necessary modules, you need to be *root* or to use *sudo*.

matplotlib is a key library used by SuperSid. You need to install it either directly or as a dependency as explain below.

To use SuperSid in text mode only (for both Python2 and Python3):
````
 # dnf/yum/apt-get install python-matplotlib   or dnf/yum/apt-get install python3-matplotlib
````

To use SuperSid with GUI based on wxPython (for Python 2 only):
````
 # dnf/yum/apt-get install python-matplotlib-wx
````

To use SuperSid with GUI based on tkinter (for Python2 and Python3):
````
 # dnf/yum/apt-get install python-matplotlib-tk   or dnf/yum/apt-get install python3-matplotlib-tk
````

## Sound Card Configuration ##
This is really the tricky part as sound capture on Linux is rather complex. The original SuperSID program uses PyAudio, which works fine on Windows. But for Linux, with ALSA, it is rather frustrating: mode selection (with high sampling rate) is not always successfull, **`jackd`** is requiered but its configuration is not easy.

After various unsuccessful attempts to run SuperSID with PyAudio, I decided to switch to another library which directly captures sound at ALSA level: **alsaaudio**.  

````
Python 2:
 # yum/apt-get install python-alsaaudio

Python 3:
 - yum install 'pkgconfig(alsa)'
 - go to http://sourceforge.net/projects/pyalsaaudio/files/
 - download and unpack the latest pyalsaaudio-___.tar.gz
 - python3 setup.py install
````

## Specific `supersid.cfg` Entry ##
A new optional section for specific capture needs can be declared in `Config/supersid.cfg`. 

````
[Capture]
# Default is Audio=pyaudio
Audio=alsaaudio
Card=External  
PeriodSize=128
````

#### Card
Specify which sound card to use. To know which sound card are recognized on your Linux box uses:  

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

To check that the sampler recognizes your card properly, execute the `sample.py` module on its own:
````
python ~/supersid/supersid/sampler.py
Possible capture modules: ['alsaaudio']
Accessing MID ...
alsaaudio sound card capture on sysdefault:CARD=MID at 48000 Hz
Accessing Pro ...
alsaaudio sound card capture on sysdefault:CARD=Pro at 48000 Hz
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


