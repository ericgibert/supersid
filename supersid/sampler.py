#!/usr/bin/python
"""
    Sampler handles audio data capture, calculating PSD, extracting signal strengths at monitored frequencies,
    saving spectrum and spectrogram (image) to png file
    
    This is pure Model, no wx import possible else Thread conflict
    
    The Sampler class will use on 'device' to capture 1 second of sound.
    This 'device' can be a local sound card:
     - controlled by pyaudio on Windows or other system
     - controlled by alsaaudio on Linux
    or this 'device' can be a remote server
     - client mode accessing server thru TCP/IP socket (to be implemented)
     
    All these 'devices' must implement:
     - __init__: open the 'device' for future capture
     - capture_1sec: obtain one second of sound and return as an array of 'audio_sampling_rate' integers
     - close: close the 'device'
"""
# 20150801:
#   - modify the __main__ to help debugging the soundcard
from __future__ import print_function   # use the new Python 3 'print' function
from struct import unpack as st_unpack
from numpy import array

audioModule=[]
try:
    import alsaaudio  # for Linux direct sound capture
    audioModule.append("alsaaudio")
    # pip3 install setuptools
    # dnf install python3-cffi
    # dnf install portaudio
    # pip3 install sounddevice

    
    class alsaaudio_soundcard():
        def __init__(self, card, periodsize, audio_sampling_rate):
            self.FORMAT = alsaaudio.PCM_FORMAT_S16_LE
            self.audio_sampling_rate = audio_sampling_rate
            card = 'sysdefault:CARD=' + card  # to add in the .cfg file under [Linux] section
            self.inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, card)
            self.inp.setchannels(1)
            self.inp.setrate(audio_sampling_rate)
            self.inp.setperiodsize(periodsize)
            self.inp.setformat(self.FORMAT)
            self.name = "alsaaudio sound card capture on " + card

        def capture_1sec(self):
            raw_data = b''
            while len(raw_data) < 2 * self.audio_sampling_rate:
                length,data = self.inp.read()
                if length> 0: raw_data += data
            return array(st_unpack("%ih"%self.audio_sampling_rate, raw_data[:2 * self.audio_sampling_rate]))
        
        def close(self):
            pass  # to check later if there is something to do

        def info(self):
            print(self.name, "at", self.audio_sampling_rate,"Hz")
            one_sec = self.capture_1sec()
            print(len(one_sec),"bytes read from", self.name, type(one_sec))
            print(one_sec[:10])

        
except ImportError:
    pass


try:
    import sounddevice  # for Linux http://python-sounddevice.readthedocs.org
    audioModule.append("sounddevice")

    class sounddevice_soundcard():
        def __init__(self, device, audio_sampling_rate):
            self.audio_sampling_rate = audio_sampling_rate
            sounddevice.default.samplerate = audio_sampling_rate
            sounddevice.default.device = int(device)
            sounddevice.default.channels = 1
            self.name = "sounddevice capture on device " + str(device)

        def capture_1sec(self):
            # duration = 1 sec hence   1 x self.audio_sampling_rate = self.audio_sampling_rate
            one_sec_record = b''
            try:
                one_sec_record = sounddevice.rec(self.audio_sampling_rate)
            except sounddevice.PortAudioError as err:
                print("Error reading device", self.name)
                print(err)
            return one_sec_record

        def close(self):
            pass  # to check later if there is something to do

        def info(self):
            print(self.name, "at", self.audio_sampling_rate,"Hz")
            one_sec = self.capture_1sec()
            print(len(one_sec),"bytes read from", self.name, type(one_sec))
            print(one_sec[:10])


except ImportError:
    pass


try:
    import pyaudio  # for Linux with jackd OR windows
    audioModule.append("pyaudio")
    
    class pyaudio_soundcard():
        def __init__(self, audio_sampling_rate):
            self.FORMAT = pyaudio.paInt16
            self.CHUNK = 1024
            self.pa_lib = pyaudio.PyAudio()
            self.audio_sampling_rate = audio_sampling_rate

            self.pa_stream = self.pa_lib.open(format = self.FORMAT,
                                          channels = 1,
                                          rate = self.audio_sampling_rate,
                                          input = True,
                                          frames_per_buffer = self.CHUNK)
            self.name = "pyaudio sound card capture"

        def capture_1sec(self):
            raw_data = b''.join(self.capture(1))  # self.pa_stream.read(self.audio_sampling_rate)
            unpacked_data = st_unpack("{}h".format(self.audio_sampling_rate), raw_data)
            return array(unpacked_data)

        def capture(self, secs):
            frames = []
            expected_number_of_bytes = 2 * self.audio_sampling_rate * secs #int(self.audio_sampling_rate / self.CHUNK * secs)
            while len(frames) < expected_number_of_bytes:
                try:
                    data = self.pa_stream.read(self.CHUNK)
                    frames.extend(data)
                    #print(len(data), len(frames))
                except IOError as io:
                    #print("IOError reading card:", str(io))
                    pass
            return frames[:expected_number_of_bytes]
        
        def close(self):
            self.pa_stream.stop_stream()
            self.pa_stream.close()
            self.pa_lib.terminate()

        def info(self):
            for i in range(self.pa_lib.get_device_count()):
                print(i, ":", self.pa_lib.get_device_info_by_index(i))
            print("default device :", self.pa_lib.get_default_input_device_info())
            default_capability = self.pa_lib.get_default_host_api_info()
            print("default device Capability", default_capability)
            is_supported = self.pa_lib.is_format_supported(input_format=self.FORMAT, input_channels=1,
                                                       rate=self.audio_sampling_rate, input_device=0)
            print("expected format is supported?", is_supported)
            
except ImportError:
    pass


class Sampler():
    """Sampler will gather sound capture from various devices: sound cards or remote server"""
    def __init__(self, controller, audio_sampling_rate = 96000, NFFT = 1024):
        self.version = "1.4 20160207"
        self.controller = controller
        self.scaling_factor = controller.config['scaling_factor']
        
        self.audio_sampling_rate = audio_sampling_rate
        self.NFFT = NFFT
        self.sampler_ok = True

        try:
            if controller.config['Audio'] == 'pyaudio':
                self.capture_device = pyaudio_soundcard(audio_sampling_rate)
            elif controller.config['Audio'] == 'sounddevice':
                self.capture_device = sounddevice_soundcard(controller.config['Card'], audio_sampling_rate)
            elif controller.config['Audio'] == 'alsaaudio':
                self.capture_device = alsaaudio_soundcard(controller.config['Card'],
                                                          controller.config['PeriodSize'],
                                                          audio_sampling_rate)
            else:
                self.display_error_message("Unknown audio module:" + controller.config['Audio'])
                self.sampler_ok = False
        except:
            self.sampler_ok = False
            self.display_error_message("Could not open capture device. Please check your .cfg file or hardware.")
            print ("Error", controller.config['Audio'])
            print("To debugg: remove the try/except clause to get detail on what exception is triggered.")

        if self.sampler_ok:
            print("-", self.capture_device.name)

    def set_monitored_frequencies(self, stations):
        self.monitored_bins = []
        for station in stations:
            binSample = int(((int(station['frequency']) * self.NFFT) / self.audio_sampling_rate))
            self.monitored_bins.append(binSample)
            #print ("monitored freq =", station[Config.FREQUENCY], " => bin = ", binSample)

    def capture_1sec(self):
        """Capture 1 second of data, returned data as an array
        """
        try:
            self.data = self.capture_device.capture_1sec()
        except:
            self.sampler_ok = False
            print ("Fail to read data from audio using " + self.capture_device.name)
            self.data = []
        else:
            #scale A/D raw_data to voltage here (we might substract 5v to make the data look more like SID)
            if(self.scaling_factor != 1.0):
                self.data *= self.scaling_factor
                
        return self.data

    def close(self):
        self.capture_device.close()

    def display_error_message(self, message):
        msg = "From Sampler object instance:\n" + message + ". Please check.\n"
        self.controller.viewer.status_display(msg)            
        
if __name__ == '__main__':
    print('Possible capture modules:', audioModule)

    if 'alsaaudio' in audioModule:
        for card in alsaaudio.cards():
            try:
                print("Accessing", card, "...")
                for sampling_rate in [48000, 96000]:
                    sc = alsaaudio_soundcard(card, 1024, sampling_rate)
                    sc.info()
            except alsaaudio.ALSAAudioError as err:
                print("! ERROR capturing sound on card", card)
                print(err)

    print("\n", "- "*60)

    if 'sounddevice' in audioModule:
        print(sounddevice.query_devices())
        for device, card in enumerate(sounddevice.query_devices()):
            # try:
            print("Accessing", card['name'], "...")
            for sampling_rate in [48000]:
                sc = sounddevice_soundcard(device, sampling_rate)
                sc.info()
            # except alsaaudio.ALSAAudioError as err:
            #     print("! ERROR capturing sound on card", card)
            #     print(err)

    print("\n", "- "*60)

    if 'pyaudio' in audioModule:
        sc = pyaudio_soundcard(48000)
        sc.info()