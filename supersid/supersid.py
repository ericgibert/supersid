#!/usr/bin/python
""" supersid.py 
    version 1.3
    Segregation MVC
    
    SuperSID class is the Controller.
    First, it reads the .cfg file specified on the command line (unique accepted parameter) or in ../Config
    Then it creates its necessary elements:
    - Model: Logger, Sampler
    - Viewer: Viewer
    using the parameters read in the .cfg file
    Finally, it launches an infinite loop to wait for events:
    - User input (graphic or text)
    - Timer for sampling
    - <still missing> network management with client-server protocol

"""
import sys
# matplotlib ONLY used in Controller for its PSD function, not for any graphic 
from matplotlib.mlab import psd as mlab_psd
# wx.App() object is necessary in Controller to run the event loop, not for any graphic 
from wx import App
from time import sleep

# SuperSID Package classes
from sidtimer import SidTimer
from sampler import Sampler
from config import Config
from logger import Logger
from wxsidviewer import wxSidViewer
from textsidviewer import textSidViewer

class SuperSID():
    '''
    This is the main class which creates all other objects.
    In CMV pattern, this is the Controller.
    '''
    running = False  # class attribute to indicate if the SID application is running
    
    def __init__(self):
        self.version = "1.3.1 20130817"
        self.timer = None
        self.sampler = None
        self.viewer = None
        
        # Read Config file here
        print "Reading supersid.cfg ...",
        # this script accepts a .cfg file as optional argument else we default
        # so that the "historical location" or the local path are explored
        self.config = Config(sys.argv[1] if len(sys.argv) == 2 else "supersid.cfg")
        # once the .cfg read, some sanity checks are necessary
        self.config.supersid_check()
        if not self.config.config_ok:
            print "ERROR:", self.config.config_err
            exit(1)
        else:
            print self.config.filenames # good for debugging: what .cfg file(s) were actually read
            
        # Create Logger - NEW: Logger will read an existing file if specified in .cfg as [Capture].Continue
        self.logger = Logger(self)
                   
        # Create the viewer based on the .cfg specification (or set default):
        # Note: the list of Viewers can be extended provided they implement the same interface
        if self.config['viewer'] == 'wx':       # GUI Frame to display real-time VLF Spectrum based on wxPython
            self.viewer = wxSidViewer(self)
            self.viewer.Show()
        elif self.config['viewer'] == 'text':   # Lighter text version a.k.a. "console mode"
            self.viewer = textSidViewer(self)
        else:
            print "ERROR: Unknown viewer", sid.config['viewer']
            exit(2)
            
        # Assign desired psd function for calculation after capture
        # currently: using matplotlib's psd
        if self.config['viewer'] == 'wx':
            self.psd = self.viewer.get_psd  # calculate psd and draw result in one call
        else:
            self.psd = mlab_psd             # calculation only

        # calculate Stations' buffer_size
        self.buffer_size = int(24*60*60 / self.config['log_interval'])      

        # Create Sampler to collect audio buffer (sound card or other server)
        self.sampler = Sampler(self, audio_sampling_rate = self.config['audio_sampling_rate'], NFFT = 1024);
        if not self.sampler.sampler_ok:
            self.close()
            exit(3)
        else:
            self.sampler.set_monitored_frequencies(self.config.stations);
        
        # Link the logger.file.data buffers to the config.stations
        for ibuffer, station  in enumerate(self.config.stations):
            station['raw_buffer'] =  self.logger.file.data[ibuffer]

        # Create Timer
        self.viewer.status_display("Waiting for Timer ... ")
        self.timer = SidTimer(self.config['log_interval'], self.on_timer)
        

    def clear_all_data_buffers(self):
        self.logger.file.clear_buffer(next_day = True)

    def on_timer(self):
        # self.current_index is the position in the buffer calculated from current UTC time
        self.current_index = self.timer.data_index
        # clear the View to prepare for new data display
        self.viewer.clear()

        # Get new data and pass them to the View
        message = "%s  [%d]  Capturing data..." % (self.timer.get_utc_now(), self.current_index)
        self.viewer.status_display(message, level=1)
            
        try:
            data = self.sampler.capture_1sec()  # return a list of 1 second signal strength
            Pxx, freqs = self.psd(data, self.sampler.NFFT, self.sampler.audio_sampling_rate)
        except IndexError as idxerr:
            print "Index Error:", idxerr
            print "Data len:", len(data)

        # Save signal strengths into buffers and Display on status bar
        signal_strengths = []
        for binSample in self.sampler.monitored_bins:
            signal_strengths.append(Pxx[binSample])
        message = self.timer.get_utc_now() + "  [%d]  " % self.current_index
        for station, strength in zip(self.config.stations, signal_strengths):
            station['raw_buffer'][self.current_index] = strength
            message +=  station['call_sign'] + "=%f " % strength
        self.logger.file.timestamp[self.current_index] = self.timer.utc_now

        
        # When hitting the buffer limit, clear buffers, reset index, set to next date' epoch
        if self.current_index >= self.buffer_size - 1:
            self.save_current_buffers(log_type=self.config['log_type'], log_format='both')
            # Restart a new day
            self.clear_all_data_buffers() 
            self.current_index = 0
            self.timer.date_begin_epoch += 60*60*24

        elif self.config['hourly_save'] == 'YES': # save raw buffers 'on the hour' in raw/superSID format
            if (self.current_index * self.config['log_interval']) % 3600 == 0:
                fileName = "hourly_current_buffers." + self.timer.get_utc_now()[:10]+".csv"
                self.save_current_buffers(fileName, 'filtered', 'supersid_format')
                fileName = "hourly_current_buffers.raw." + self.timer.get_utc_now()[:10]+".csv"
                self.save_current_buffers(fileName, 'raw', 'supersid_format')       

        # end of this thread/need to handle to View to display captured data & message
        self.viewer.status_display(message, level=2)

    def save_current_buffers(self, filename="current_buffers.csv", log_type='raw', log_format = 'both', extended = False):
        ''' Save raw data as supersid_format '''
        filenames = []
        if log_format in ('both', 'sid_format'):
            fnames = self.logger.log_sid_format(self.config.stations, self.timer.date_begin_epoch, '', log_type=log_type, extended=extended) # filename is '' to ensure one file per station
            filenames += fnames
        if log_format in ('both', 'supersid_format'):
            fnames = self.logger.log_supersid_format(self.config.stations, self.timer.date_begin_epoch, filename, log_type=log_type, extended=extended)
            filenames += fnames
        return filenames
        
    def on_close(self):
        self.close()
            
    def run(self, app = None):
        """Start the application as infinite loop accordingly to need"""
        self.__class__.running = True
        if self.config['viewer'] == 'wx':
            app.MainLoop()
        elif self.config['viewer'] == 'text':
            try:
                while(self.__class__.running):
                    sleep(1)
            except (KeyboardInterrupt, SystemExit):
                pass

            
    def close(self):
        """Call all necessary stop/close functions of children objects"""
        if self.sampler:
            self.sampler.close()
        if self.timer: 
            self.timer.stop()
        if self.viewer:
            self.viewer.close()
        self.__class__.running = False


#-------------------------------------------------------------------------------

if __name__ == '__main__':
    try:
        app = App(redirect=False)  # wx application - mandatory for viewer = 'wx', ignored for other viewer
    except:
        print("wx not initialized. Text mode only.")
        app = None
        
    sid = SuperSID()
    sid.run(app)
    sid.close()
    if app: app.Exit()


