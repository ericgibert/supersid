#!/usr/bin/env python
"""
 Name:        sidfile.py
 Purpose:     Usage 1: Provide a Class to handle SID and SuperSID formatted files
              Usage 2: Please refer to the USAGE string for utilities information


 Author:      Eric Gibert

 Created:     13-10-2012
 Copyright:   (c) eric 2012
 Licence:     Open to All

    20150801:
    - truncate ['utc_starttime'] to 19 chars

"""
from __future__ import print_function   # use the new Python 3 'print' function
from datetime import datetime, timedelta
import numpy
from matplotlib.mlab import movavg

from config import FILTERED, RAW

USAGE = """
Provide some utilities to manipulate SID/SuperSID files:
    - When one file is given as argument:
       - file is SID Format: DISPLAY some information - good for debugging
       - file is SuperSID format: SPLIT to one file per station in SID format
    - When two files are given as arguments:
       - both files are SID Format: MERGE in one SID Format
       - one file is SuperSID and one is SID: MERGE the SID file with the matching station from SuperSId file
       - both are SuperSID: MERGE in one SuperSID with "station to station" matching
"""

class SidFile():
    """Class to read SID or SuperSID files.
    Provides header information and data content access.
    """
    _TIMESTAMP_STANDARD = "%Y-%m-%d %H:%M:%S"
    _TIMESTAMP_EXTENDED = "%Y-%m-%d %H:%M:%S.%f"
    _timestamp_format = _TIMESTAMP_STANDARD  # conservative default

    def __init__(self, filename = "", sid_params = {}, force_read_timestamp = False):
        """Two ways to create a SIDfile:
        1) A file already exists and you want to read it: use 'filename'
        2) A new empty file needs to be created: use 'sid_params'
            to indicate the parameters of the file's header.
            The dictionary retrieved from a config file can be used.
            Usually this means you need to write that file after data collection.

        Note: only one or the other parameter should be given. If both are given
        then 'filename' is taken and 'sid_params' is ignored.
        """
        self.version = "1.4 20150801"
        self.filename = filename
        self.sid_params = sid_params    # dictionary of all header pairs
        self.is_extended = False
        self.timestamp_format = SidFile._TIMESTAMP_STANDARD

        if filename:
            # Read all lines in a buffer used by 'read_data' and 'read_header'
            try:
                with open(self.filename, "rt") as fin:
                    self.lines = fin.readlines()
            except IOError as why:
                print ("Error reading", filename)
                print(str(why))
                exit(1)

            self.read_header()
            self.read_timestamp_format()
            self.control_header()
            self.read_data(force_read_timestamp)

        elif self.sid_params:
            # create zeroes numpy arrays to receive data
            self.control_header()
            self.clear_buffer()
    ##
    ##  Read a SID File and control header's consistency
    ##
    def clear_buffer(self, next_day=False):
        """creates zeroes numpy arrays to receive data and generates the timestamp vector"""
        if next_day:
            self.data.fill(0.0)
            self.set_all_date_attributes()
        else:
            nb_data_per_day = int ( (24 * 3600) / self.LogInterval)
            self.data = numpy.zeros((len(self.stations), nb_data_per_day))
        # create an array containing the timestamps for each data reading, default initialization
        self.generate_timestamp()

    def control_header(self):
        '''Perform sanity check and assign standard attributes in a format independent way.
           SuperSID files have an entry "Stations" while SID files have "StationID"'''
        if "stations" in self.sid_params:
            self.isSuperSID = True
            self.stations = self.sid_params["stations"].split(",")
            self.frequencies = self.sid_params["frequencies"].split(",")
        elif "stationid" in self.sid_params:
            self.isSuperSID = False
            self.stations = [ self.sid_params["stationid"] ]
            self.frequencies = [ self.sid_params["frequency"] ]
        else:
            print("ERROR: No station ID found in this file or configuration. Please check!")
            exit(5)

        # get the datetime for UTC_StartTime
        self.set_all_date_attributes(keep_file_date = True)

        # do we have a LogInterval ?
        if "log_interval" in self.sid_params:
            self.LogInterval = int(self.sid_params["log_interval"])
        elif "loginterval" in self.sid_params:
            self.LogInterval = int(self.sid_params["loginterval"])
        else:
            print ("Warning: Log_Interval is missing! Please check. I assume 5 sec...")
            self.LogInterval, self.sid_params["log_interval"] = 5, 5

    def set_all_date_attributes(self, keep_file_date = False):
        if not keep_file_date or "utc_starttime" not in self.sid_params:
            utcnow = datetime.utcnow()
            self.sid_params["utc_starttime"] = "%d-%02d-%02d 00:00:00" % (utcnow.year, utcnow.month, utcnow.day)
            if SidFile._timestamp_format == SidFile._TIMESTAMP_EXTENDED:
                self.sid_params["utc_starttime"] += ".00000"
        self.UTC_StartTime = self.sid_params["utc_starttime"]
        self.startTime = SidFile._StringToDatetime(self.sid_params["utc_starttime"])

    def read_header(self):
        """Reads the first lines of a SID file to extract the 'sid_params'.
        No more file access: all in memory using 'self.lines'
        """
        self.sid_params.clear()
        self.headerNbLines = 0  # number of header lines
        for line in self.lines:
            if line[0] != "#": break   # end of header
            self.headerNbLines += 1
            tokens = line.split("=")
            if len(tokens) == 2:
                # remove the '#' and force the key to lower case to avoid ambiguity from user's supersid.cfg
                key = tokens[0][1:].strip().lower()
                self.sid_params[key] = tokens[1].strip()

    def read_timestamp_format(self):
        """Check the timestamp found on the first line to deduce the timestamp format"""
        first_data_line = self.lines[self.headerNbLines].split(",")
        if ':' in first_data_line[0]: # yes, a time stamp is found in the first data column
            try:
                datetime.strptime(first_data_line[0], SidFile._TIMESTAMP_EXTENDED)
                self.is_extended = True
                SidFile._timestamp_format = SidFile._TIMESTAMP_EXTENDED
                self.timestamp_format = SidFile._TIMESTAMP_EXTENDED
            except ValueError:
                datetime.strptime(first_data_line[0], SidFile._TIMESTAMP_STANDARD)
                self.is_extended = False
                SidFile._timestamp_format = SidFile._TIMESTAMP_STANDARD
                self.timestamp_format = SidFile._TIMESTAMP_STANDARD

    def read_data(self, force_read_timestamp = False):
        """Using the self.lines buffer, converts the data lines in numpy arrays.
            - One array self.data for the data (one column/vector per station)
            - One array self.timestamp for the timestamps (i.e. timestamp vector)
        Reading method differs accordingly to the self.isSuperSID flag
        New: Extended format supports a timestamp for SuperSID format as well as .%f for second decimals
        """
        # necessary to convert timestamp string (extended or not) to datetime AND decode byte array to string to float for python 3
        converters_dict = {0: SidFile._StringToDatetime }
        for i in range(len(self.stations)):
            converters_dict[i+1] = SidFile._StringToFloat

        if self.isSuperSID and not self.is_extended:
            # classic SuperSID file format: one data column per station, no time stamp (has to be generated)
            print ("Warning: read SuperSid non extended file and generate time stamps.")
            self.data = numpy.loadtxt(self.lines, comments='#', delimiter=",").transpose()
            self.generate_timestamp()
        elif self.isSuperSID and self.is_extended:
            # extended SuperSID file format: one extended time stamp then one data column per station
            print ("Warning: read SuperSid extended file, time stamps are read & converted from file.")
            inData = numpy.loadtxt(self.lines, dtype=datetime, comments='#', delimiter=",", converters=converters_dict)
            self.timestamp = inData[:,0] # column 0
            self.data = numpy.array(inData[:,1:], dtype=float).transpose()
        else:
            # classic SID file format:
            # two columns file: [timestamp, data]. Try to avoid reading timestamps: date str to num conversion takes time
            # self.data must still be a 2 dimensions numpy.array even so only one vector is contained
            if len(self.lines) - self.headerNbLines != (60 * 60 * 24) / self.LogInterval  \
            or force_read_timestamp or self.is_extended:
                print ("Warning: read SID file, timestamps are read & converted from file.")
                inData = numpy.loadtxt(self.lines, dtype=datetime, comments='#', delimiter=",", converters=converters_dict)
                self.timestamp = inData[:,0] # column 0
                self.data = numpy.array(inData[:,1], dtype=float, ndmin=2) # column 1
            else:
                print ("Optimization: read SID file, generate timestamp instead of reading & converting them from file.")
                self.data = numpy.array(numpy.loadtxt(self.lines, comments='#', delimiter=",", usecols=(1,)), ndmin=2) # only read data column
                self.generate_timestamp()
        #print("self.data.shape =", self.data.shape)

    @classmethod
    def _StringToDatetime(cls, strTimestamp):
        if type(strTimestamp) is not str: # i.e. byte array in Python 3
            strTimestamp = strTimestamp.decode('utf-8')
        try:
            dts = datetime.strptime(strTimestamp, SidFile._timestamp_format)
        except ValueError: # try the other format...
            if SidFile._timestamp_format == SidFile._TIMESTAMP_STANDARD:
                dts = datetime.strptime(strTimestamp, SidFile._TIMESTAMP_EXTENDED)
            else:
                dts = datetime.strptime(strTimestamp, SidFile._TIMESTAMP_STANDARD)
        return dts

    @classmethod
    def _StringToFloat(cls, strNumber):
        if type(strNumber) is not str: # i.e. byte array in Python 3
            strNumber = strNumber.decode('utf-8')
        return float(strNumber)

    def generate_timestamp(self):
        """Create the timestamp vector by adding LogInterval seconds to UTC_StartTime"""
        self.timestamp = numpy.empty(len(self.data[0]), dtype=datetime)
        # add 'interval' seconds to UTC_StartTime for each entries
        interval =  timedelta(seconds=self.LogInterval)
        currentTimestamp = self.startTime
        for i in range(len(self.timestamp)):
            self.timestamp[i] =  currentTimestamp
            currentTimestamp += interval
    ##
    ##  Facilitator functions
    ##
    def get_sid_filename(self, station):
        """Return a file name as <Site Name>_<Station>_<UTC Start Date>.csv like RASPI_NWC_2013-08-31.csv"""
        site = self.sid_params['site_name'] if 'site_name' in self.sid_params else self.sid_params['site']
        return "%s_%s_%s.csv" % (site, station, self.sid_params["utc_starttime"][:10])

    def get_supersid_filename(self):
        """Return a file name as <Site Name>__<UTC Start Date>.csv like RASPI_2013-08-31.csv"""
        site = self.sid_params['site_name'] if 'site_name' in self.sid_params else self.sid_params['site']
        return "%s_%s.csv" % (site, self.sid_params["utc_starttime"][:10])

    def get_station_data(self, stationId):
        """Return the numpy array of the given station's data"""
        try:
            idx = self.get_station_index(stationId)
            return self.data[idx]
        except ValueError:
            return []

    def get_station_index(self, station):
        """Returns the index of the station accordingly to the parameter station type"""
        if type(station) is int:
            assert( 0 <= station < len(self.stations) )
            return  station
        elif type(station) is str: # should be a station name/call_sign
            return self.stations.index(station)  # throw a ValueError if 'station' is not in the list
        elif type(station) is dict:
            return self.stations.index(station['call_sign'])  # throw a ValueError if 'station' is not in the list
        else:
            return self.stations.index(station.call_sign)  # throw a ValueError if 'station' is not in the list

    def copy_data(self, second_sidfile):
        """Copy the second_sidfile's data on the current data vector for every common stations.
           If a copy is done then the timestamps are also copied."""
        has_copied = False
        for iStation, station in enumerate(self.stations):
            try:
                second_idx = second_sidfile.get_station_index(station)
                self.data[iStation] = second_sidfile.data[second_idx][:] # deep copy
                has_copied = True
            except ValueError:
                # missing station in the second file
                pass
        if has_copied:
            self.timestamp = second_sidfile.timestamp[:] # deep copy

    ##
    ##  Write a SID File
    ##
    def create_header(self, isSuperSid, log_type):
        """ Create a string matching the SID/SuperSID file header.
        Ensure the same header on both formats.
        - isSuperSid: request a SuperSid header if True else a SID header
        - log_type: must be 'raw' or 'filtered' as in RAW/FILTERED
        """
        hdr = "# Site = %s\n" % (self.sid_params['site_name'] if 'site_name' in self.sid_params else self.sid_params['site'])
        if 'contact' in self.sid_params:
            hdr += "# Contact = %s\n" % self.sid_params['contact']
        if "supersid_version" in self.sid_params:
            hdr += "# Supersid_Version = %s\n" % self.sid_params['supersid_version']
        hdr += "# Longitude = %s\n" % self.sid_params['longitude']
        hdr += "# Latitude = %s\n" % self.sid_params['latitude']
        hdr += "#\n"
        hdr += "# UTC_Offset = %s\n" % self.sid_params['utc_offset']
        hdr += "# TimeZone = %s\n" % (self.sid_params['time_zone'] if 'time_zone' in self.sid_params else self.sid_params['timezone'])
        hdr += "#\n"
        hdr += "# UTC_StartTime = %s\n" % self.sid_params['utc_starttime'][:19]
        hdr += "# LogInterval = %s\n" % (self.sid_params['log_interval'] if 'log_interval' in self.sid_params else self.sid_params['loginterval'])
        hdr += "# LogType = %s\n" % log_type
        hdr += "# MonitorID = %s\n" % (self.sid_params['monitor_id'] if 'monitor_id' in self.sid_params else self.sid_params['monitorid'])
        if isSuperSid:
            hdr += "# Stations = %s\n" % self.sid_params['stations']
            hdr += "# Frequencies = %s\n" % self.sid_params['frequencies']
        else:
            hdr += "# StationID = %s\n" % self.sid_params['stationid']
            hdr += "# Frequency = %s\n" % self.sid_params['frequency']
        return hdr

    def write_data_sid(self, station, filename, log_type, apply_bema = True, extended = False, bema_wing = 6):
        """Write in the file 'filename' the dataset of the given station using the SID format
        i.e. "TimeStamp, Data" lines
        Header respects the SID format definition i.e. conversion if self is SuperSid
        """
        iStation = self.get_station_index(station)
        # need extra information to create the header's SID file parameters if the exiting file is SuperSID
        if self.isSuperSID:
            self.sid_params['stationid'] = self.stations[iStation]
            self.sid_params['frequency'] = self.frequencies[iStation]

        # intermediate buffer to have 'raw' or 'filtered' data ( as in RAW/FILTERED)
        if log_type == RAW or apply_bema == False:
            tmp_data = self.data[iStation]
        else: # filtered
            tmp_data = SidFile.filter_buffer(self.data[iStation], self.LogInterval, bema_wing = bema_wing)
        # write file in SID format
        with open(filename, "wt") as fout:
            # generate header
            hdr = self.create_header(isSuperSid = False, log_type = log_type)
            print(hdr, file=fout, end="")
            # generate the "timestamp, data" serie i.e. data lines
            timestamp_format = SidFile._TIMESTAMP_EXTENDED if extended else SidFile._TIMESTAMP_STANDARD ###"%Y-%m-%d %H:%M:%S.%f" if extended else "%Y-%m-%d %H:%M:%S"
            for t_stamp, x in zip(self.timestamp, tmp_data):
                print("%s, %.15f" % (t_stamp.strftime(timestamp_format), x), file=fout)

    def write_data_supersid(self, filename, log_type, apply_bema = True, extended = False, bema_wing = 6):
        """Write the SuperSID file. Attention: self.sid_params must contain all expected entries."""
        # force to SuperSid format
        hdr = self.create_header(isSuperSid = True, log_type = log_type)
        # create file and write header
        with open(filename, "wt") as fout:
            print(hdr, file=fout, end="")
            # intermediate buffer to have 'raw' or 'filtered' data (as in  as in RAW/FILTERED)
            if log_type == RAW or apply_bema == False:
                tmp_data = self.data
            else: # filtered
                tmp_data = []
                for stationData in self.data:
                    tmp_data.append(SidFile.filter_buffer(stationData, self.LogInterval, bema_wing = bema_wing))
                tmp_data = numpy.array(tmp_data)
            #print(tmp_data.shape)  # should be like (2, 17280)
            if extended:
                for t_stamp, row in zip(self.timestamp, numpy.transpose(tmp_data)):
                    floats_as_strings = ["%.15f" % x for x in row]
                    print( t_stamp.strftime(SidFile._TIMESTAMP_EXTENDED+","), ", ".join(floats_as_strings), file=fout)
            else:
                for row in numpy.transpose(tmp_data):
                    floats_as_strings = ["%.15f" % x for x in row]
                    print(", ".join(floats_as_strings), file=fout)

        # append data to file using numpy function (symmetric to loadtxt)
        # note for future: version 1.7 offers "header=hdr" as new function parameter
        # but for now (1.6) we write header first then savetxt() append data lines
        #numpy.savetxt(filename, tmp_data, delimiter=",", newline="\n", header=hdr)

    @classmethod
    def filter_buffer(cls, raw_buffer, data_interval, bema_wing = 6, gmt_offset = 0):
            '''
            Return bema filtered version of the buffer, with optional time_zone_offset.
            bema filter uses the minimal found value to represent the data points within a range (bema_window)
            bema_wing = 6 => window = 13 (bema_wing + evaluating point + bema_wing)
            '''
            length = len(raw_buffer)
            # Extend 2 wings to the raw data buffer before taking min and average
            dstack = numpy.hstack((raw_buffer[length-bema_wing:length],
                                   raw_buffer[0:length],
                                   raw_buffer[0:bema_wing]))
            # Fill the 2 wings with the values at the edge
            dstack[0:bema_wing] = raw_buffer[0]  #  dstack[bema_wing]
            dstack[length+bema_wing:length+bema_wing*2] = raw_buffer[-1]  # dstack[length+bema_wing-1]
            # Use the lowest point found in window to represent its value
            dmin = numpy.zeros(len(dstack))
            for i in range(bema_wing, length+bema_wing):
                dmin[i] = min(dstack[i-bema_wing:i+bema_wing])
            # The points beyond the left edge, set to the starting point value
            dmin[0:bema_wing] = dmin[bema_wing]
            # The points beyond the right edge, set to the ending point value
            dmin[length+bema_wing:length+bema_wing*2] = dmin[length+bema_wing-1]
            # Moving Average. This actually truncates array to original size
            daverage = movavg(dmin, (bema_wing*2+1))

            if gmt_offset == 0:
                return daverage
            else:
                gmt_mark = gmt_offset * (60/data_interval) * 60
                doffset = numpy.hstack((daverage[gmt_mark:length],daverage[0:gmt_mark]))
                return doffset

##-------------------------------------------------------------------------------
##  This module can be used alone as a utility to manipulate SID Files
##  To see its options, execute at prompt level :   sidfile.py -h
##
if __name__ == '__main__':
    from os import path
    import argparse

    def exist_file(x):
        """
        'Type' for argparse - checks that file exists but does not open it
        """
        if not path.isfile(x):
            raise argparse.ArgumentError("{0} does not exist".format(x))
        return x

    fmerge = lambda x: "%s.merge%s" % path.splitext(x)  # /original/path/name.merge.ext
    # check that one or two arguments are given
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--split", dest="filename_split", required=False, type=exist_file,
                            help="Split 1 supersid_format in N sid_format / 1 supersid_extended in N sid_extended i.e. one per station")
    parser.add_argument("-m", "--merge", dest="filename_merge", required=False, type=exist_file, nargs="*",
                            help="Merge 2 sid_format in one supersid_format / 2 supersid_extended in one supersid_extended")
    parser.add_argument("-i", "--info", dest="filename_info", required=False, type=exist_file,
                            help="Display information about one file")
    parser.add_argument("-f", "--filter", dest="filename_filter", required=False, type=exist_file,
                            help="Filter a raw file")
    parser.add_argument("-b", "--bema_wing", dest="bema_wing", required=False, type=int, default=6,
                            help="Width of the window used in filtering a.k.a. 'bema_wing' (default=6)")
    args, unk = parser.parse_known_args()
    if args.filename_info:
        sid = SidFile(args.filename_info, force_read_timestamp = True)
        print("-" * 5, "Header information", "-" * 5)
        if sid.is_extended:
            print("Time stamps are extended.")
        if sid.isSuperSID:
            print("SuperSID file format")
            print("Monitored Stations List:", sid.stations)
        else:
            print("SID File Format")
            print("Station:", sid.stations)
        print("Start Time:", sid.startTime)
        print("Number of TimeStamps:", len(sid.timestamp))
        # try to print 5 non zero records if found:
        print("-" * 5, "Dataset shape:", sid.data.shape, "-" * 5)
        for i in range(len(sid.timestamp)):
            if sid.data[0][i] != 0.0: break
        if i == len(sid.timestamp): i = 0
        for t_stamp, row in zip(sid.timestamp[i:i+5], numpy.transpose(sid.data)[i:i+5]):
            floats_as_strings = ["%.15f" % x for x in row]
            print( t_stamp.strftime(sid.timestamp_format+","), ", ".join(floats_as_strings))
        # print the whole dictionary
        print("-" * 5, "sid_params", "-" * 5)
        for key, value in sid.sid_params.items():
            print(" " * 5, key, "=", value)
    # Some 'real' manipulations:
    elif args.filename_split:
        # Explode this SuperSID file in one file per station in SID format
        sid = SidFile(args.filename_split, force_read_timestamp = True)
        print("Proceed to split this SuperSID file in %d SID files:" % sid.data.shape[0])
        for station in sid.stations:
            fname = "%s/%s_%s_%s.split.csv" % (path.dirname(sid.filename),
                                         sid.sid_params['site'],
                                         station,
                                         sid.sid_params['utc_starttime'][:10])
            sid.write_data_sid(station, fname, sid.sid_params['logtype'], apply_bema = False)
            print(fname, "created.")
    elif args.filename_merge:
        # Merge 2 SuperSID files station by station
        sid1, sid2 = SidFile(args.filename_merge[0]), SidFile(args.filename_merge[1])
        if sid1.isSuperSID and sid2.isSuperSID:
            for istation in range(len(sid1.stations)):
                sid1.data[:, istation] += sid2.get_station_data(sid1.stations[istation])
            sid1.write_data_supersid(fmerge(sid1.filename), apply_bema = False)
            print(fmerge(sid1.filename), "created.")
        # one SID file and one SuperSID file: merge the SuperSID's matching station to SID file
        elif sid1.isSuperSID != sid2.isSuperSID:
            if sid1.isSuperSID:
                supersid = sid1
                sid = sid2
            else:
                sid = sid1
                supersid = sid2
            station = sid.stations[0]
            if station not in supersid.stations:
                print("Error: station %s in not found in the superSId file. Cannot merge." % station)
            else:
                sid.data += supersid.get_station_data(station)
                sid.write_data_sid(station, fmerge(sid.filename), sid.sid_params['logtype'], apply_bema = False)
                print(fmerge(sid.filename), "created.")
        # 2 SID files to merge in one SID file - sid1's header is kept
        else:
            sid1.data += sid2.data
            sid1.write_data_sid(sid1.stations[0], fmerge(sid1.filename), sid1.sid_params['logtype'], apply_bema = False)
            print(fmerge(sid1.filename), "created.")
    elif args.filename_filter:
        # Convert a RAW file into a Filtered one. Can filter an already filtered file too...
        # optional parameter --bema_wing can be specified
        sid = SidFile(args.filename_filter, force_read_timestamp = True)
        fname = "%s.filtered%s" % path.splitext(args.filename_filter)
        if sid.sid_params['logtype'] != RAW:
            print("Warning: %s is not a raw file. This might filter an already filtered file." % args.filename_filter)
        bema_wing = args.bema_wing if args.bema_wing else 6
        if sid.isSuperSID:
            sid.write_data_supersid(fname, log_type=FILTERED, apply_bema = True, extended = sid.is_extended, bema_wing=bema_wing)
        else:
            sid.write_data_sid(sid.stations[0], fname, log_type=FILTERED, apply_bema = True, extended = sid.is_extended, bema_wing=bema_wing)
    else:
        parser.print_help()
