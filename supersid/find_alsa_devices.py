#!/usr/bin/env python3

"""
Module for printing the names of all the audio recording devices.

There may be several audio capture devices on your system.
You will need to pick one of these strings to give as the value of
the "Device" parameter in the [Capture] section of the supersid.cfg file.
"""
import pprint
import alsaaudio

device_list = alsaaudio.pcms(alsaaudio.PCM_CAPTURE)

pprint.pprint(device_list)
