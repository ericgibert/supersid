#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      eric
#
# Created:     10-08-2012
# Copyright:   (c) eric 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python2
import sys
from os import path
import glob
import datetime
from sidfile import SidFile
from config import FILTERED, RAW

# Script personalization
DEFAULT_STATION="NWC:10000,JJI:100000"
SUPERSID_ID="DAISYSG"

if __name__ == '__main__':
    
    if sys.argv[1].lower() == "yesterday":
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        input_file = r"C:\Users\eric\Documents\supersid-master\Data\%s_%04d-%02d-%02d.csv" % (SUPERSID_ID,yesterday.year,yesterday.month,yesterday.day)
        year, month, day = yesterday.year, yesterday.month, yesterday.day
    else:
        input_file = sys.argv[1]
        yyyy_mm_dd = path.basename(path.splitext(input_file)[0])[-10:]
        year = int(yyyy_mm_dd[0:4])
        month = int(yyyy_mm_dd[5:7])
        day = int(yyyy_mm_dd[8:])
        print(yyyy_mm_dd, year, month, day)
        
    sid = SidFile(input_file, force_read_timestamp = True)
                            
    for station, f in [p.split(":") for p in DEFAULT_STATION.split(",")]:
        factor = int(f) if len(sys.argv) < 3 else int(sys.argv[2])
        if factor != 1:
            iStation = sid.get_station_index(station)
            sid.data[iStation] *= factor
        fname = r"C:\Users\eric\Documents\supersid\Private\ToSend\Sending\%s_%s_%04d-%02d-%02d.csv" % \
                                            (SUPERSID_ID, station, year, month, day)
        # if the original file is filtered then we can save it "as is" els we ned to apply_bema i.e. filter it
        sid.write_data_sid(station, fname, FILTERED, apply_bema = sid.sid_params['logtype'] == RAW)

