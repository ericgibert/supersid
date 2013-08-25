""" Log Station data into 2 different formats: sid_format (single column with time), supersid (multiple columns without time),

"""
from time import gmtime, strftime
import itertools

from sidfile import SidFile

class Logger():

    def __init__(self, controller):
        self.version = "1.3.1 20130819"
        self.controller = controller
        self.config = controller.config
        # Do we have a 'Continue' entry in the config file?
        if 'Continue' in self.config and self.config['Continue'] != '':
            previous_file = self.config['Continue']
            self.file = SidFile(filename = previous_file)
            if self.file.sid_params['logtype'] != 'raw':
                print "The file type is not raw but", self.file.sid_params['logtype']
                answer = raw_input("Do you still want to keep its content and continue recording? [y/N]")
                if answer.lower()!='y':
                    print "Abort."
                    exit(-10)
            elif self.file.sid_params['utc_starttime'] != strftime("%Y-%m-%d 00:00:00", gmtime()):
                print "The file UTC_StartTime =", self.file.sid_params['utc_starttime']
                answer = raw_input("Do you still want to keep its content and continue recording? [y/N]")
                if answer.lower()!='y':
                    print "Abort."
                    exit(-11)
            print "Continue recoding with data from file", previous_file, "included."
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
                print "Error: no station to log???"
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
      

      
    #### OLD VERSION ---- Independent from SidFile module  #########################      
    def _log_header_config(self, log_file, log_type, date_begin_epoch):
        """Ensure the same header on both formats."""
        print >> log_file, "# Site = " + self.config['site_name']
        if 'contact' in self.config:
            print >> log_file, "# Contact = " + self.config['contact']
        print >> log_file, "# Longitude = " + self.config['longitude']
        print >> log_file, "# Latitude = " + self.config['latitude']
        print >> log_file, "#"
        #print >> log_file, "# UTC_Offset = " + str(utc_offset)      # calculated
        print >> log_file, "# UTC_Offset = " + self.config['utc_offset']   # from config file
        print >> log_file, "# TimeZone = " + self.config['time_zone']     # lookup
        print >> log_file, "#"
        print >> log_file, "# UTC_StartTime = " + strftime("%Y-%m-%d %H:%M:%S", gmtime(date_begin_epoch))
        print >> log_file, "# LogInterval = " , self.config['log_interval']
        print >> log_file, "# LogType = " , log_type
        print >> log_file, "# MonitorID = " + self.config['monitor_id']
      
    def _log_sid_format(self, stations, date_begin_epoch, filename='', log_type='filtered'):
        """ OLD VERSION: independent from SidFile
            One file per station. By default, buffered data is filtered."""
        filenames = []
        for station in stations:
            if log_type == 'raw':
                data = station['raw_buffer']
            else:  # 'filtered' is default
                data = SidFile.filter_buffer(station['raw_buffer'], self.config['log_interval'])                
            
            my_filename = filename if filename != '' \
            else self.config['site_name'] + "_" + station['call_sign'] + strftime("_%Y-%m-%d",gmtime(date_begin_epoch)) + ".csv"
    
            with open(self.config.data_path + my_filename, "wt") as log_file:
                filenames.append(log_file.name)  
                # Write header
                self.log_header_config(log_file, log_type, date_begin_epoch)
                print >> log_file, "# StationID = " + station['call_sign']
                print >> log_file, "# Frequency = " + station['frequency']
    
                # Write data
                epoc = date_begin_epoch     
                for d in data:   
                    print >> log_file, strftime("%Y-%m-%d %H:%M:%S, ", gmtime(epoc))+ str(d)
                    epoc += self.config['log_interval']
        return filenames
      
    def _log_supersid_format(self, stations, date_begin_epoch, filename='', log_type='filtered'):
        """Cascade all buffers in one file."""
        data = []
        filenames = []
        for station in stations:
            if log_type == 'raw':
                data.append(station['raw_buffer'])
            else: # 'filtered' default
                data.append(SidFile.filter_buffer(station['raw_buffer'], self.config['log_interval'])) 

        if filename == '':
            filename = self.config['site_name'] + strftime("_%Y-%m-%d", gmtime(date_begin_epoch)) + ".csv"

        with open(self.config.data_path + filename, "wt") as log_file:
            filenames.append(log_file.name)
            # Write header
            self.log_header_config(log_file, log_type, date_begin_epoch)
            print >> log_file, "# Stations = " + ",".join([st['call_sign'] for st in stations])
            print >> log_file, "# Frequencies = " + ",".join([st['frequency'] for st in stations])

            # Write data - note: izip instead of zip for better performance
            for dataRow in itertools.izip(*data):  
                print >> log_file, ",".join([str(d) for d in dataRow])
            
        return filenames
