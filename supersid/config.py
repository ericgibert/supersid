#!/usr/bin/python
"""Config parses a supersid's .cfg file

Parameter access: all keys are forced to lowercase
  - for parameters: config['site_name'], config['longitude'], etc...
  - for stations:   config.stations[i] is a triplet: (call_sign, frequency, color)

Note: len(config.stations) == config['number_of_stations'] - sanity check -
"""
#
# Eric Gibert
#
#   Change Log:
#   20140816:
#   - define CONSTANTS to ensure universal usage
#   20150801:
#   - add the [FTP] section
#
from __future__ import print_function   # use the new Python 3 'print' function
import os.path
try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

# constant for log_type
FILTERED, RAW = 'filtered', 'raw'
# constant for station parameters
CALL_SIGN, FREQUENCY, COLOR = 'call_sign', 'frequency', 'color'
# constant for log_format
SID_FORMAT, SUPERSID_FORMAT = 'sid_format', 'supersid_format'
SUPERSID_EXTENDED, BOTH_EXTENDED = 'supersid_extended', 'both_extended' # with 5 decimals timestamp
# Default value for alsaaudio Device parameter. Should be something the
# alsaaudio library would never accept.
DEVICE_DEFAULT = 'FOOBAR1234xyz'

class Config(dict):
    """Dictionary containing the key/values pair read from a .cfg file"""
    CONFIG_PATH_NAME = "../Config/" # default for historical reasons
    DATA_PATH_NAME   = "../Data/"   # default for historical reasons - can be overwritten by 'data_path'

    def __init__(self, filename="supersid.cfg"):
        """Read the given .cfg file (formatted as a .ini windows file) or tries to find one.
           All its key/values pairs are stored as a dictionary (self)
        :param filename: superSID .cfg file
        :return: nothing
        """
        self.version = "1.4 20150801"
        dict.__init__(self)         # Config objects are dictionaries
        self.config_ok = True       # Parsing success/failure
        self.config_err = ""        # Parsing failure error message
        config_parser = ConfigParser.ConfigParser()

        if filename == "supersid.cfg": # let's look in various places
            self.filenames = config_parser.read([Config.CONFIG_PATH_NAME + filename,   # historic location
                                                 os.path.join('.', filename),            # current location
                                                 os.path.expanduser(os.path.join('~', filename))]) # $home in *nix
        else: # a specific file has been given
            self.filenames = config_parser.read(filename)

        if len(self.filenames) == 0:
            self.config_ok = False
            self.config_err = "Cannot find configuration file: " + filename
            return

        # each section (dico entry) matches a list of parameters
        # each parameter has a key description, a type for cast, a default value or None if mandatory
        sections = { 'PARAMETERS': ( # optional entries
                                    ('contact', str, None),             # email of the SuperSID owner
                                    ('hourly_save', str, "no"),         # new flag: yes/no to save every hours
                                    ('data_path', str, ""),             # new: to override DATA_PATH_NAME by user
                                    ('log_format', str, SID_FORMAT),    # sid_format (default), supersid_format
                                    ('mode', str, 'Standalone'),        # Server, Client, Standalone (default)
                                    ('viewer', str, 'tk'),              # text, wx, tk (default)
                                    ('bema_wing', int, 6),              # beta_wing for sidfile.filter_buffer()
                                    # mandatory entries
                                    ('site_name', str, None),
                                    ('longitude', str, None),
                                    ('latitude', str, None),
                                    ('utc_offset', str, None),
                                    ('time_zone',  str, None),
                                    ('monitor_id', str, None),
                                    ('log_type',  str, None),           # 'filtered' or 'raw'

                                    ('audio_sampling_rate', int, None),
                                    ('log_interval', int, None),
                                    ('number_of_stations', int, None),
                                    ('scaling_factor', float, None)
                                    ),

                      "Capture":   (("Audio", str, 'pyaudio'),          # soundcard: alsaaudio or pyaudio ; server
                                    ("Card", str, 'External'),          # alsaaudio: card name for capture
                                    ("Device", str, DEVICE_DEFAULT),         # USe instead of card for alsaaudio
                                    ("PeriodSize", int, 128)            # alsaaudio: period size for capture
                                    ),

                      "Linux":     (("Audio", str, 'pyaudio'),          # soundcard: alsaaudio or pyaudio ; server
                                    ("Card", str, 'External'),          # alsaaudio: card name for capture
                                    ("PeriodSize", int, 128)            # alsaaudio: period size for capture
                                    ),

                      "Email":     (("from_mail", str, ""),             # sender email
                                    ("to_mail", str, ""),               # recipient email
                                    ("email_server", str, ""),          # your email server (SMPT)
                                    ("email_port", str, ""),            # your email server's port (SMPT)
                                    ("email_login", str, ""),           # if your server requires a login
                                    ("email_password", str, "")         # if your server requires a passwrd
                                    ),
                      "FTP":       (('automatic_upload',  str, "no"),   # yes/no: to upload the file to the remote FTP server
                                    ('ftp_server',  str, ""),           # address of the server like sid-ftp.stanford.edu
                                    ('ftp_directory', str, ""),         # remote target directory to write the files
                                    ('local_tmp', str, ""),             # local tmp folder to generate files before upload
                                    ('call_signs', str, "")             # list of stations to upload (sub-set of [stations])
                                    ),
                    }

        self.sectionfound = set()
        for section, fields in sections.items():
            # go thru all the current section's fields
            for pkey, pcast, pdefault in fields:
                try:
                    self[pkey] = pcast(config_parser.get(section, pkey))
                except ValueError:
                    self.config_ok = False
                    self.config_err = "'%s' is not of the type %s in 'supersid.cfg'. Please check." % (pkey, pcast)
                    return
                except ConfigParser.NoSectionError:
                    #it's ok: some sections are optional
                    pass
                except ConfigParser.NoOptionError:
                    if pdefault is None: # missing mandatory parameter
                        self.config_ok = False
                        self.config_err = "'"+pkey+"' is not found in '%s'. Please check." % filename
                        return
                    else: # optional, assign default
                        self.setdefault(pkey, pdefault)
                else:
                    self.sectionfound.add(section)

        if "Linux" in self.sectionfound:
            print ("\n*** WARNING***\nSection [Linux] is obsolete. Please replace it by [Capture] in your .cfg files.\n")

        # Getting the stations parameters
        self.stations = []  # now defined as a list of dictionaries

        for i in range(self['number_of_stations']):
            section = "STATION_" + str(i+1)
            tmpDict = {}
            try:
                for parameter in (CALL_SIGN, FREQUENCY, COLOR):
                    tmpDict[parameter] = config_parser.get(section, parameter)
                self.stations.append(tmpDict)
            except ConfigParser.NoSectionError:
                self.config_ok = False
                self.config_err = section + "section is expected but missing from the config file."
                return
            except ConfigParser.NoOptionError:
                self.config_ok = False
                self.config_err = section + " does not have the 3 expected parameters in the config file. Please check."
                return
            else:
                self.sectionfound.add(section)

    def supersid_check(self):
        """Perform sanity checks when a .cfg file is read by 'supersid.py'.
        Verifies that all mandatory sections were read.
        Extend the keys with some other values for easier access."""
        if not self.config_ok: return

        for mandatory_section in ('PARAMETERS',):
            if mandatory_section not in self.sectionfound:
                self.config_ok = False
                self.config_err = mandatory_section + "section is mandatory but missing from the .cfg file."
                return

        # sanity check: as many Stations were read as announced by 'number_of_stations' (now section independent)
        if self['number_of_stations'] != len(self.stations):
            self.config_ok = False
            self.config_err = "'number_of_stations' does not match STATIONS found in supersid.cfg. Please check."
            return

        if 'stations' not in self:
            self[CALL_SIGN] = ",".join([s[CALL_SIGN] for s in self.stations])
            self[FREQUENCY] = ",".join([s[FREQUENCY] for s in self.stations])

        # log_type must be lower case and one of 'filtered' or 'raw'
        self['log_type'] = self['log_type'].lower()
        if self['log_type'] not in (FILTERED, RAW):
            self.config_ok = False
            self.config_err = "'log_type' must be either 'filtered' or 'raw' in supersid.cfg. Please check."
            return

        # 'hourly_save' must be UPPER CASE
        self['hourly_save'] = self['hourly_save'].upper()
        if self['hourly_save'] not in ('YES', 'NO'):
            self.config_ok = False
            self.config_err = "'hourly_save' must be either 'YES' or 'NO' in supersid.cfg. Please check."
            return

        # log_interval should be > 2
        if self['log_interval'] <= 2:
            self.config_ok = False
            self.config_err = "'log_interval' <= 2. Too fast! Please increase."
            return

        # check log_format
        self['log_format'] = self['log_format'].lower()
        if self['log_format'] not in (SID_FORMAT,SUPERSID_FORMAT, SUPERSID_EXTENDED, BOTH_EXTENDED):
            self.config_ok = False
            self.config_err = "'log_format' must be either 'sid_format' or 'supersid_format'/'supersid_extended'."
            return

        # Check the 'data_path' validity and create it as a Config instance property
        self.data_path = os.path.normpath(self['data_path'] or Config.DATA_PATH_NAME) + os.sep
        if not os.path.isdir(self.data_path):
            self.config_ok = False
            self.config_err = "'data_path' does not point to a valid directory:\n" + self.data_path
            return

        # default audio to pyaudio if not declared
        if "Audio" not in self:
            self["Audio"] = "pyaudio"

        # Just one choice: 'plot_offset = 0', for now ; not in the expected parameters list
        self['plot_offset'] = 0


if __name__ == '__main__':
    import sys
    # one argument: the .cfg file to read
    cfg = Config(sys.argv[1])
    cfg.supersid_check()
    if cfg.config_ok:
        print (cfg.filenames, "read successfully:")
    else:
        print ("Error:", cfg.config_err)
    for section in sorted(cfg.sectionfound):
        print ("-", section)
    print("-"*20)
    for k, v in sorted(cfg.items()):
        print (k,"=",v)
    print("-"*20)
    for st in cfg.stations:
        print (st)
