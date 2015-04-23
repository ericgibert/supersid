# SuperSID on Linux #

Implementation of the SuperSID program to record Solar Induced Disturbances on a Linux platform.

Program is tested on both Fedora 16 on Desktop PC and Debian Wheezy on **Raspberry Pi**. 

## Python Requirements ##

	* Python 2.7.2
	* Python 2.7 numpy-1.6.1 or higher
	* Python 2.7 matplotlib-1.1.0 or higher
	* wxPython 2.8.12.1 (unicode) for Python 2.7
	* Python 2.7 PyAudio OR pyAlsaAudio (recommended)

~~Python 2.7 scipy-0.10.0~~ no longer requiered.

+ matplotlib:

````
 # yum/apt-get install matplotlib
 # yum/apt-get install python-matplotlib   or yum/apt-get install python3-matplotlib
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

````
> ls -l /proc/asound/  
sss    
ddd

````

#### PeriodSize
Number of frame ... If too big then error `error message` will be returned.


