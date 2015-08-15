SuperSID
========

Cross-platform Sudden Ionospheric Disturbances (SID) monitor

Objectives
----------
Monitoring the Sudden Ionospheric Disturbances (SID) is an easy yet exciting Home Based Radio Astronomy Project. This project is an implementation of [Stanford SOLAR Center’s SuperSID][Standford].

The default SuperSID project software runs on Windows OS to record the pre-amplified signal received by the antenna with a “SuperSID Monitor”. 

This *SuperSID* project is an Open Source implementation that runs on Linux and Windows. The scripts are executable by Python 2.7 and Python 3, at your choice.

This *SuperSID* includes a text mode which allows to turn your Raspberry Pi in a SID monitor (tested on Raspbian Wheezy & Pidora distro). TkInter in the default GUI to ensure Python 2 and 3 compatibility (but wxPython is still supported for Python 2 only).


|Original Project  |Open Source SuperSID Project
|------------------|--------------------------------------
|Desktop/Laptop PC |Desktop/Laptop PC/Raspberry Pi (512Mb)
|Windows OS        |Linux and Windows OS
|Python 2.7        |Python 2.7 or 3.3+
|Any Soundcard     |USB External Soundcard
|SuperSID Monitor pre-amp.  |Direct connection to External Soundcard

Other improvements
------------------

supersid.py:
 - More options in the [configuration file (.cfg)] (docs/ConfigHelp.md)
 - Continue recording after interruption
 - Auto adjustment of the interval period for better accuracy
 - New extended file format with time stamp to the 1.000th of second
 - *sidfile.py* can be used as a utility to manipualte SID files

supersid_plot.py:
 - Accepts multiple files to display up to 10 days in continue (wildcards possible)
 - Can connect to NOAA to draw the day's events
 - Can send the graph as PDF by email

![figure_20150703](https://cloud.githubusercontent.com/assets/5303792/9287076/5c4f3eb4-4337-11e5-9db7-00391b9fcf40.png)

[Standford]: http://solar-center.stanford.edu/SID/sidmonitor/

