""" Log Station data into 2 different formats: sid_format (single column with time), supersid (multiple columns without time),

"""
from __future__ import print_function   # use the new Python 3 'print' function
from time import gmtime, strftime

from sidfile import SidFile

class Logger():

    def __init__(self, controller, read_file):
        self.version = "1.3.1 20130819"
        self.controller = controller
        self.config = controller.config
        # Do we have a 'Continue' entry in the config file?
        if read_file:
            self.file = SidFile(filename = read_file)
            if self.file.sid_params['logtype'] != 'raw':
                print("The file type is not raw but", self.file.sid_params['logtype'])
                answer = raw_input("Do you still want to keep its content and continue recording? [y/N]")
                if answer.lower()!='y':
                    print("Abort.")
                    exit(-10)
            elif self.file.sid_params['utc_starttime'] != strftime("%Y-%m-%d 00:00:00", gmtime()):
                print("Not today's file. The file UTC_StartTime =", self.file.sid_params['utc_starttime'])
                answer = raw_input("Do you still want to keep its content and continue recording? [y/N]")
                if answer.lower()!='y':
                    print("Abort.")
                    exit(-11)
            elif sorted(self.file.stations) != sorted([s['call_sign'] for s in self.config.stations]):
                print("Station Lists are different:", self.file.stations, "!=", [s['call_sign'] for s in self.config.stations])
                answer = raw_input("Do you still want to keep its content and continue recording? [y/N]")
                if answer.lower()!='y':
                    print("Abort.")
                    exit(-11)
            print("Continue recoding with data from file", read_file, "included.")
        else:
            # no file to continue: fresh buffer in memory
            if len(self.config.stations) == 1:
                # only one station to monitor, let's default to SID file format
                self.controller.isSuperSID = False
                self.config["stationid"] = self.config.stations[0]['call_sign']
                self.config["frequency"] = self.config.stations[0]['frequency']
                self.config['log_format'] = "sid_format"
            elif len(self.config.stations) > 1:
                # more than one station to monitor, let's default to SuperSId file format
                self.controller.isSuperSID = True
                self.config["stations"] = ",".join([s['call_sign'] for s in self.config.stations])
                self.config["frequencies"] = ",".join([s['frequency'] for s in self.config.stations])
                self.config['log_format'] = "supersid_format"
            else:
                print("Error: no station to log???")
                exit(5)
            self.file = SidFile(sid_params = self.config)
    
    def log_sid_format(self, stations, date_begin_epoch, filename='', log_type='filtered', extended = False):
        """ One file per station. By default, buffered data is filtered."""
        filenames = []
        self.config['utc_starttime'] = strftime("%Y-%m-%d %H:%M:%S", gmtime(date_begin_epoch))
        for station in stations:       
            my_filename = filename if filename != '' else self.config['site_name'] + "_" + station['call_sign'] + strftime("_%Y-%m-%d",gmtime(date_begin_epoch))
            my_filename = self.config.data_path  + my_filename + ".csv"
            filenames.append(my_filename)
            self.file.write_data_sid(station, my_filename, log_type, extended=extended)  
        return filenames
    
    def log_supersid_format(self, stations, date_begin_epoch, filename='', log_type='filtered', extended = False):
        """Cascade all buffers in one file."""
        filenames = []
        self.config['utc_starttime'] = strftime("%Y-%m-%d %H:%M:%S", gmtime(date_begin_epoch))
        if filename == '':
            filename = self.config['site_name'] + strftime("_%Y-%m-%d", gmtime(date_begin_epoch)) + ".csv"
        filename = self.config.data_path + filename
        filenames.append(filename)
        self.file.write_data_supersid(filename, log_type, extended=extended)
        return filenames
      
      

