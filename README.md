SuperSID
========

Cross-platform Sudden Ionospheric Disturbances (SID) monitor

Objectives
----------
Monitoring the Sudden Ionospheric Disturbances (SID) is an easy yet exciting Home Based Radio Astronomy Project. This project is an implementation of [Stanford SOLAR Center’s SuperSID][Standford] .

The default SuperSID project uses a PC on Windows OS to record the pre-amplified signal received by the antenna with a “SuperSID Monitor”. 

This *SuperSID* project is a similar but simpler implementation on Linux whithout the “SuperSID Monitor”. This *SuperSID* includes a text mode which allows to turn your Raspberry Pi in a SID monitor (tested on Raspbian Wheezy & Fedora mix distro).


|Original Project  |RasPi-SID Project
|------------------|-----------------------
|Desktop/Laptop PC |Raspberry Pi (512Mb)
|Windows OS        |Linux OS
|Any Soundcard     |USB External Soundcard
|SuperSID Monitor pre-amp.  |Direct connection to External Soundcard

Other improvements
------------------

Both Python 2 and 3 are supported. Note that currently only the *text* viewer can be used with Python 3 as wxPython is [not *yet* ported to Python 3][Phoenix].

supersid.py:
 - More options in the configuration file (.cfg)
 - Continue recording after interruption
 - auto adjustment of the interval period for better accuracy
 - New extended file format with time stamp to the 1.000th of second
 - sidfile.py can be used as a utility to manipualte SID files

supersid_plot.py:
 - Accepts multiple files to display up to 10 days in continue
 - Can connect to NOAA to draw the day's events
 - Can send the graph as PDF by email

[Standford]: http://solar-center.stanford.edu/SID/sidmonitor/
[Phoenix]: http://wxpython.org/Phoenix/docs/html/index.html
