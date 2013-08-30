Running SuperSID on Raspberry Pi
=================================

SuperSID is written in for Python 2.7. It needs extra modules and a working sound card for sound acquisition.

A) Extra modules
================

For *Debian Wheezy*:

 * matplotlib: ````# apt-get install python-matplotlib````
 * wxPython: ````# apt-get install python-wxgtk2.8````

For *Fedora 18 Mix*:
 * wxPython:````sudo yum install wxPython````
 * matplotlib: ````sudo yum install python-matplotlib-wx````


For all distro:
 * alsa tools:	````sudo yum/apt-get install alsa-utils````
then using alsamixer, verify that the USB sound card is detected and that the volume of input is 85%.


No longer needed:
~~scipy~~: ````# apt-get install python-scipy````

B) Sound Card & Sound Acquisition
=================================

1) PyAudio
----------

Original Python Library used by SuperSID which allow PortAudio access.  
Found at http://people.csail.mit.edu/hubert/pyaudio/

To be used for Windows OS, with Windows' installer.

If you want to experiment with it on Linux:

 1) Install PortAudio  ````# apt-get install libportaudio0````

Or get its source from http://www.portaudio.com/download.html
 --> Download pa_stable_v19_20111121.tgz (or more recent)
 
 2) Prerequsite:

````# apt-get install python-dev````
 
 3) Get PyAudio
 --> Download pyaudio-0.2.7.tar.gz

then follow instructions under General UNIX Guide at 
http://people.csail.mit.edu/hubert/pyaudio/compilation.html


------

Note for matplotlib
-------------------

Before starting:
- [optional] Edit the matplotlibrc file to force using wxPython backend by default:

In Python shell, run:
````
    >>> import matplotlib
    >>> matplotlib.matplotlib_fname()
    '/usr/local/lib/python2.7/dist-packages/matplotlib/mpl-data/matplotlibrc'
````

As root, copy this file for backup then edit it:
    backend      : Agg
change to
    backend      : WXAgg


This is the same as doing in the program:

````python
import matplotlib
matplotlib.rcParams['backend']="WXAgg"
````
