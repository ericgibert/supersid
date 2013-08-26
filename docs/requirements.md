
SuperSID is written in for Python 2.7.

Moving to Python 3.3 is part of the "to do list" but wxPython is still  not available. Nevertheless, the possibility to run the application in text mode should be considered as a first step

Python dependencies
-------------------

SuperSID needs the following modules and their dependencies:

 - matplotlib: ``# apt-get install python-matplotlib`` (this will install *numpy* too)
 - wxPython: ``# apt-get install python-wxgtk2.8``


Sound Card Configuration
------------------------

This is really the tricky part as sound capture on Linux is rather complex. The original SuperSID program uses *PyAudio*, which works fine on Windows. But for Linux, with ALSA, it is rather frustrating: mode selection (with high sampling rate) is not always successfull, *jackd* is requiered but its configuration is not easy. And this means an extra daemon running, not good for Rasperry Pi.

After various unsuccessful attempts to run SuperSID with *PyAudio*, I decided to switch to another library which will directly capture sound at ALSA level: [alsaaudio](http://pyalsaaudio.sourceforge.net/)

 - alsaaudio: ``# yum/apt-get install python-alsaaudio``

Note: it is not necessary to install *PyAudio* on Linux.

-----

Before starting:
- Need to edit the matplotlibrc file to force using wxPython backend:

In Python shell, run:

    >>> import matplotlib
    >>> matplotlib.matplotlib_fname()
    '/usr/local/lib/python2.7/dist-packages/matplotlib/mpl-data/matplotlibrc'

As root, copy this file for backup then edit it:

    backend      : Agg
change to

    backend      : WXAgg


This is the same as doing in the program:

    import matplotlib
    matplotlib.rcParams['backend']="WXAgg"
    
------
For reference only
------------------

If you want to give a try to *PyAudio*:

- Python Library used by SuperSID which allow PortAudio access.
- Found at http://people.csail.mit.edu/hubert/pyaudio/
 --> Download pyaudio-0.2.7.tar.gz

Install PortAudio  ``# apt-get install libportaudio0``

Or get its source from http://www.portaudio.com/download.html
 --> Download pa_stable_v19_20111121.tgz

To do:

``# apt-get install python-dev``

then follow instructions under General UNIX Guide at 
http://people.csail.mit.edu/hubert/pyaudio/compilation.html
