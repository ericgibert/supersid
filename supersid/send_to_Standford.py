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
import glob
import datetime
from sidfile import SidFile

# Script personalization
DEFAULT_STATION="NWC:10000,JJI:100000"
SUPERSID_ID="DAISYSG"

def main(filelist, multiplication_factor):
    for filename in glob.glob(filelist):
        if filename.startswith("NONE"):
            target = filename.replace("NONE","DAISYSG")
        else:
            target = filename.replace(".csv",".2.csv")

        print filename, target

        with open(filename,"rt") as fin, open(target,"wt") as fout:
            for line in fin.readlines():
                if line.startswith("# Site = NONE"):
                    fout.write("# Site = DAISYSG\n")
                elif line.startswith("# MonitorID = NONE"):
                    fout.write("# MonitorID = 1\n")
                elif line.startswith("#"):
                    fout.write(line)
                else:
                    timestampStr, dataStr = line.split(",")
                    data = float(dataStr) * multiplication_factor
                    fout.write("%s, %.14f\n" % (timestampStr, data))


if __name__ == '__main__':
    
    if sys.argv[1].lower() == "yesterday":
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        input_file = "C:\\Users\\eric\\Documents\\supersid-master\\Data\\%s_%04d-%02d-%02d.csv" % (SUPERSID_ID,yesterday.year,yesterday.month,yesterday.day)
        year, month, day = yesterday.year, yesterday.month, yesterday.day
    else:
        input_file = sys.argv[1]
        last_underscore = input_file.rindex("_")
        year = int(input_file[last_underscore+1:last_underscore+5])
        month = int(input_file[last_underscore+6:last_underscore+8])
        day = int(input_file[last_underscore+9:last_underscore+11])
        
    sid = SidFile(input_file, force_read_timestamp = True)
                            
    for station, f in [p.split(":") for p in DEFAULT_STATION.split(",")]:
        factor = int(f) if len(sys.argv) < 3 else int(sys.argv[2])
        if factor <> 1:
            iStation = sid.get_station_index(station)
            sid.data[iStation] *= factor
        fname = "C:\\Users\\eric\\Documents\\supersid\\Private\\ToSend\\Sending\\%s_%s_%04d-%02d-%02d.csv" % \
                                            (SUPERSID_ID, station, year, month, day)
        sid.write_data_sid(station, fname, sid.sid_params['logtype'], apply_bema = False)

