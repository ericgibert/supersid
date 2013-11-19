""" Log Station data into 2 different formats: sid_format (single column with time), supersid (multiple columns without time),

"""
from __future__ import print_function   # use the new Python 3 'print' function
from time import gmtime, strftime

from sidfile import SidFile

class Logger():
    def __init__(self, controller, read_file):
        self.version = "1.3.1 20131118"
        self.controller = controller
        self.config = controller.config
        # first create in memory buffers
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
        self.sid_file = SidFile(sid_params = self.config)

        # Do we have a file to read?
        if read_file:
            sid_file2 = SidFile(filename = read_file)
            if sid_file2.sid_params['logtype'] != 'raw':
                print("The file type is not raw but", sid_file2.sid_params['logtype'])
                answer = raw_input("Do you still want to keep its content and continue recording? [y/N]")
                if answer.lower()!='y':
                    print("Abort.")
                    exit(-10)
            elif sid_file2.sid_params['utc_starttime'] != strftime("%Y-%m-%d 00:00:00", gmtime()):
                print("Not today's file. The file UTC_StartTime =", sid_file2.sid_params['utc_starttime'])
                answer = raw_input("Do you still want to keep its content and continue recording? [y/N]")
                if answer.lower()!='y':
                    print("Abort.")
                    exit(-11)
            elif sorted(sid_file2.stations) != sorted([s['call_sign'] for s in self.config.stations]):
                print("Station Lists are different:", sid_file2.stations, "!=", [s['call_sign'] for s in self.config.stations])
                answer = raw_input("Do you still want to keep its content and continue recording? [y/N]")
                if answer.lower()!='y':
                    print("Abort.")
                    exit(-11)
            self.sid_file.copy_data(sid_file2)
            print("Continue recording with data from file", read_file, "included.")

    def log_sid_format(self, stations,  filename='', log_type='filtered', extended = False):
        """ One file per station. By default, buffered data is filtered."""
        filenames = []
        for station in stations:       
            my_filename = self.config.data_path + (filename or self.sid_file.get_sid_filename(station['call_sign']))
            filenames.append(my_filename)
            self.sid_file.write_data_sid(station, my_filename, log_type, extended=extended, bema_wing=self.config["bema_wing"])
        return filenames
    
    def log_supersid_format(self, stations, filename='', log_type='filtered', extended = False):
        """Cascade all buffers in one file."""
        filenames = []
        my_filename = self.config.data_path + (filename or self.sid_file.get_supersid_filename())
        filenames.append(my_filename)
        self.sid_file.write_data_supersid(my_filename, log_type, extended=extended, bema_wing=self.config["bema_wing"])
        return filenames
    
