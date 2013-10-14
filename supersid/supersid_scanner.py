#!/usr/bin/python
""" supersid_scanner.py
    version 1.3
    Segregation MVC

    Based on supersid.py
    Scan a large number of frequencies for a given number of minutes
    Help to determine what stations are the strongest
    Can help to orientate the antenna

"""
from __future__ import print_function   # use the new Python 3 'print' function
import os.path
# matplotlib ONLY used in Controller for its PSD function, not for any graphic
from matplotlib.mlab import psd as mlab_psd
from time import sleep
import argparse

# SuperSID Package classes
from sidtimer import SidTimer
from sampler import Sampler
from config import Config
from logger import Logger
from textsidviewer import textSidViewer

class SuperSID_scanner():
    '''
    This is the main class which creates all other objects.
    In CMV pattern, this is the Controller.
    '''
    running = False  # class attribute to indicate if the SID application is running

    def __init__(self, config_file='', scan_params=(15,16000,24000)):
        self.version = "1.3.1 20130910"
        self.timer = None
        self.sampler = None
        self.viewer = None

        # Read Config file here
        print("Reading supersid.cfg ...", end='')
        # this script accepts a .cfg file as optional argument else we default
        # so that the "historical location" or the local path are explored
        self.config = Config(config_file or "supersid.cfg")
        # once the .cfg read, some sanity checks are necessary
        self.config.supersid_check()
        if not self.config.config_ok:
            print("ERROR:", self.config.config_err)
            exit(1)
        else:
            print(self.config.filenames) # good for debugging: what .cfg file(s) were actually read

        (self.scan_duration, self.scan_from, self.scan_to) = scan_params
        print ("Scanning for %d minutes on [%d:%d]..." % scan_params)
        # create an artificial list of stations
        self.config.stations = []
        for freq in range(self.scan_from, self.scan_to+100, 100):
            new_station = {}
            new_station['call_sign'] = "ST_%d" % freq
            new_station['frequency'] = str(freq)
            self.config.stations.append(new_station)

        # Create Logger - Logger will read an existing file if specified as -r|--read script argument
        self.logger = Logger(self,'')
        if 'utc_starttime' not in self.config:
            self.config['utc_starttime'] = self.logger.sid_file.sid_params["utc_starttime"]

        # Create the viewer based on the .cfg specification (or set default):
        # Note: the list of Viewers can be extended provided they implement the same interface
        self.config['viewer'] = 'text'   # Lighter text version a.k.a. "console mode"
        self.viewer = textSidViewer(self)
        self.psd = mlab_psd             # calculation only

        # calculate Stations' buffer_size
        self.buffer_size = int(24*60*60 / self.config['log_interval'])

        # Create Sampler to collect audio buffer (sound card or other server)
        self.sampler = Sampler(self, audio_sampling_rate = self.config['audio_sampling_rate'], NFFT = 1024)
        if not self.sampler.sampler_ok:
            self.close()
            exit(3)
        else:
            self.sampler.set_monitored_frequencies(self.config.stations)

        # Link the logger.sid_file.data buffers to the config.stations
        for ibuffer, station  in enumerate(self.config.stations):
            station['raw_buffer'] =  self.logger.sid_file.data[ibuffer]

        # Create Timer
        self.viewer.status_display("Waiting for Timer ... ")
        self.timer = SidTimer(self.config['log_interval'], self.on_timer, delay=2)
        self.scan_end_time = self.timer.start_time + 60 * self.scan_duration


    def clear_all_data_buffers(self):
        """Clear the current memory buffers and pass to the next day"""
        self.logger.sid_file.clear_buffer(next_day = True)

    def on_timer(self):
        """Callback function triggered by SidTimer every 'log_interval' seconds"""
        # current_index is the position in the buffer calculated from current UTC time
        current_index = self.timer.data_index
        utc_now = self.timer.utc_now
        # clear the View to prepare for new data display
        self.viewer.clear()

        # Get new data and pass them to the View
        message = "%s  [%d]  Capturing data..." % (self.timer.get_utc_now(), current_index)
        self.viewer.status_display(message, level=1)

        try:
            data = self.sampler.capture_1sec()  # return a list of 1 second signal strength
            Pxx, freqs = self.psd(data, self.sampler.NFFT, self.sampler.audio_sampling_rate)
        except IndexError as idxerr:
            print("Index Error:", idxerr)
            print("Data len:", len(data))

        signal_strengths = []
        for binSample in self.sampler.monitored_bins:
            signal_strengths.append(Pxx[binSample])

        # ensure that one thread at the time accesses the sid_file's' buffers
        with self.timer.lock:
            # Save signal strengths into memory buffers ; prepare message for status bar
            message = self.timer.get_utc_now() + "  [%d]  " % current_index
            message += "%d" % (self.scan_end_time - self.timer.time_now)
            for station, strength in zip(self.config.stations, signal_strengths):
                station['raw_buffer'][current_index] = strength
            self.logger.sid_file.timestamp[current_index] = utc_now

            # did we complete the expected scanning duration?
            if self.timer.time_now >= self.scan_end_time:
                fileName = "scanner_buffers.raw.ext.%s.csv" % (self.logger.sid_file.sid_params['utc_starttime'][:10])
                fsaved = self.save_current_buffers(filename=fileName, log_type='raw', log_format='supersid_extended')
                print (fsaved,"saved.")
                self.close()
                exit(0)

        # end of this thread/need to handle to View to display captured data & message
        self.viewer.status_display(message, level=2)

    def save_current_buffers(self, filename='', log_type='raw', log_format = 'both'):
        """ Save buffer data from logger.sid_file

            log_type = raw or filtered
            log_format = sid_format|sid_extended|supersid_format|supersid_extended|both|both_extended"""
        filenames = []
        if log_format.startswith('both') or log_format.startswith('sid'):
            fnames = self.logger.log_sid_format(self.config.stations, '', log_type=log_type, extended=log_format.endswith('extended')) # filename is '' to ensure one file per station
            filenames += fnames
        if log_format.startswith('both') or log_format.startswith('supersid'):
            fnames = self.logger.log_supersid_format(self.config.stations, filename, log_type=log_type, extended=log_format.endswith('extended'))
            filenames += fnames
        return filenames

    def on_close(self):
        self.close()

    def run(self, wx_app = None):
        """Start the application as infinite loop accordingly to need"""
        self.__class__.running = True
        if self.config['viewer'] == 'wx':
            wx_app.MainLoop()
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
def exist_file(x):
    """
    'Type' for argparse - checks that file exists but does not open.
    """
    if not os.path.isfile(x):
        raise argparse.ArgumentError('{} does not exist'.format(x))
    return x

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--duration", dest="scan_duration", required=False, type=int, default=15,
                        help="Scan a large range of frequencies for a period of the given number of minutes")
    parser.add_argument("-f", "--from", dest="scan_from", required=False, type=int, default=16000,
                        help="Scan from the given frequency")
    parser.add_argument("-t", "--to", dest="scan_to", required=False, type=int, default=24000,
                        help="Scan to the given frequency")
    parser.add_argument("-r", "--record", dest="record_sec", required=False,
                        help="record specified seconds of sound - testing pyaudio")
    parser.add_argument('config_file', nargs='?', default='')
    args, unk = parser.parse_known_args()

    if args.record_sec:
        from sampler import pyaudio_soundcard
        import wave

        # record_sec as x seconds or s,f for sec,frequence
        if ',' in args.record_sec:
            sec, freq = args.record_sec.split(',')
            RATE = int(freq)
            SEC = int(sec)
        else:
            RATE = 44100
            SEC = int(args.record_sec)

        card = pyaudio_soundcard(RATE)
        frames = card.capture(SEC)
        card.close()

        wf = wave.open("record_test.wav", 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(card.pa_lib.get_sample_size(card.FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()


    else:
        scanner = SuperSID_scanner(config_file=args.config_file, scan_params=(args.scan_duration, args.scan_from, args.scan_to))
        scanner.run()
        scanner.close()
