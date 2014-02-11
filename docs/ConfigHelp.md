# File Naming Convention and Location #
SuperSID uses the parameters set in the provided configuration file passed as argument on the command line. By convention, the file name is "supersid.cfg".
It is possible to have more than one configuration file to launch the SuperSID application with different parameters. For example to specify different list of Stations to monitor or to choose between graphic or text mode interface (like 'supersid.text.cfg' and 'supersid.wx.cfg').

The file can be located in any accessible directory providing that the full qualified path is given. On the other hand and for previous version compatibility, the configuration file argument can be omitted. In this case, the default "supersid.cfg" is searched:
 1) In the '../Config/..' folder
 2) In the local directory
 3) In the home directory '~/' (*nix system only)
 
# File Organization #
The configuration file is a simple text file formatted as a classic '.ini' structure i.e. sections with squared brackets and a list of pairs 'key=value"
 
 The supported sections are:
  * [PARAMETERS]
  * [STATION_x] where x is a number in [1..n]
  * [Capture]
  * [Email]
  
## [PARAMETERS] ##
This section groups most of the parameters identifying your SuperSID monitor. Some optional parameters offer the possibility to change some default values used by the program.

### Monitor Identification ###
  * contact:  email of the SuperSID owner
  * site_name:
  * monitor_id: 
  * longitude:
  * latitude:
  * utc_offset:
  * time_zone:
  
### Log Parameters ###
  * audio_sampling_rate:
  * log_interval:
  * log_type: 'filtered' or 'raw'
  * automatic_upload:
  * data_path: 
  * log_format:
  * hourly_save:
  
  * ftp_server:
  * ftp_directory:
  
  * number_of_stations:
  * scaling_factor:
  
### Extra ###
  * mode: [ignored] **Server**, **Client**, **Standalone** (default) . Reserved for future client/server dev.
  * viewer: **text** for text mode light interface, **wx** for *wxPython* graphical interface (default)
  * bema_wing: beta_wing parameter for sidfile.filter_buffer() calculation. Default is '6'.
  
## [STATION_x] ##
Each station to monitor is enumerated from 1 till n=*number_of_stations*. For each station, one must provide:
  * call_sign:
  * frequency:
  * color:
  
## [Capture] ##
This section can be omitted if you plan to use the 'pyaudio' library. If you want to use the "alsaaudio" library then you can declare:
  * Audio: python library to use **alsaaudio** or **pyaudio** (default), **server** reserved for client/server future dev.
  * Card: [for alsaaudio only] card name for capture. Default is 'External'.
  * PeriodSize: [for alsaaudio only] period size for capture. Default is '128'.
  
## [Email] ##
The 'supersid_plot.py' program can send you an email with the attached plot as a PDF file. In order to use this feature, you must provide the information necessary to contact your email server as well as which email to use.
  * from_mail: sender's emai
  * to_mail: recipient's email
  * email_server: email server to use (SMPT)
  * email_login: [optional] if your server requires a login for identification
  * email_password: [optional] if your server requires a password for identification
  
