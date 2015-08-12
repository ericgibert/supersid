#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:        ftp_to_Standford.py
# Purpose:     send SID data files to Standford FTP server
#
# Author:      Eric Gibert
#
# Created:     10-08-2012 as send_to_standford.py
# Updated:     31-07-2015
# Copyright:   (c) eric 2012
# Licence:     <your licence>
#
# Script's Arguments:
# -c|--config supersid.cfg : the configuration file for its [FTP] and [PARAMETERS] sections
# -y|--yesterday : to send yesterday's superSID file  [data_path/<monitor_id>_YYYY_MM_DD.csv]
# [filename1 filename2 ...]: optional list of files to send
#
# New section in the configuration file:
# [FTP]
# automatic_upload = yes
# ftp_server = sid-ftp.stanford.edu
# ftp_directory = /incoming/SuperSID/NEW/
# local_tmp = /home/eric/supersid/Private/tmp
# call_signs = NWC:10000,JJI:100000
#-------------------------------------------------------------------------------
from __future__ import print_function   # use the new Python 3 'print' function
import argparse
from os import path
import ftplib
from datetime import datetime, timedelta
from sidfile import SidFile
from config import Config, FILTERED, RAW

def exist_file(x):
    """
    'Type' for argparse - checks that file exists but does not open it
    """
    if not path.isfile(x):
        raise argparse.ArgumentError("{0} does not exist".format(x))
    return x


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", dest="cfg_filename", required=True, type=exist_file,
                            help="Supersid configuration file")
    parser.add_argument("-y", "--yesterday", action="store_true", dest="askYesterday", default=False,
                            help="Yesterday's date is used for the file name.")
    args, file_list = parser.parse_known_args()
    # read the configuration file
    cfg = Config(args.cfg_filename)
    # what stations are to be selected from the input file(s) ?
    stations = cfg['call_signs'].split(",") if cfg['call_signs'] else [s['call_sign'] for s in cfg.stations] # i.e. else all stations
    # file list
    if args.askYesterday:
        yesterday = datetime.utcnow() - timedelta(days=1)
        file_list.append("{}{}{}_{}-{:02d}-{:02d}.csv".format(cfg['data_path'], path.sep, cfg['site_name'],
                                                       yesterday.year,yesterday.month,yesterday.day))
    # generate all the SID files ready to send in the local_tmp file
    files_to_send = []
    for input_file in file_list:
        if path.isfile(input_file):
            sid = SidFile(input_file, force_read_timestamp = True)
            if sid.sid_params['contact'] == "" and cfg['contact'] != "":
                sid.sid_params['contact'] = cfg['contact']
            # print(sid.sid_params)
            for station in stations:
                print("Sending data from", station)
                # if necessary, apply a multiplicator factor to the signal of one station [NWC:100000]
                if ':' in station:
                    station_name, factor = station.split(':')
                    factor = int(factor)
                else:
                    station_name, factor = station, 1

                if station_name not in sid.stations: # strange: the desired station in not found in the file
                    print("Warning:", station_name, "is not in the data file", input_file)
                    continue

                if factor > 1:
                    iStation = sid.get_station_index(station_name)
                    sid.data[iStation] *= factor
                # generate the SID file of that station
                # UTC_StartTime = 2014-05-31 00:00:00
                file_startdate = sid.sid_params['utc_starttime']
                file_name = "{}{}{}_{}_{}.csv".format(cfg['local_tmp'] or cfg["data_path"], path.sep,
                                                     cfg['site_name'], station_name, file_startdate[:10])
                # if the original file is filtered then we can save it "as is" else we need to apply_bema i.e. filter it
                sid.write_data_sid(station_name, file_name, FILTERED, extended = False, apply_bema = sid.sid_params['logtype'] == RAW)
                files_to_send.append(file_name)

        else:
            print("Error:", input_file, "does not exist.")

    # now sending the files by FTP
    if files_to_send and cfg['automatic_upload']=='yes':
        print("Opening FTP session with", cfg['ftp_server'])
        data = []

        ftp = ftplib.FTP(cfg['ftp_server'])
        ftp.login("anonymous", cfg['contact'])
        ftp.cwd(cfg['ftp_directory'])
        # ftp.dir(data.append)
        for f in files_to_send:
            print("Sending", f)
            try:
                ftp.storlines("STOR " + path.basename(f), open(f, "rt"))
            except ftplib.error_perm as err:
                print("Error sending", path.basename(f), ":", err)
        ftp.quit()
        print("FTP session closed.")

        for line in data:
            print ("-", line)


