# File Naming Convention and Location #
SuperSID uses the parameters set in the provided configuration file passed as argument on the command line. By convention, the file name is "supersid.cfg".
It is possible to have more than one configuration file to launch the SuperSID application with different parameters. For example to specify different list of Stations to monitor or to choose between graphic or text mode interface (like 'supersid.text.cfg' and 'supersid.wx.cfg').

The file can be located in any accessible directory providing that the full qualified path is given. On the other hand and for previous version compatibility, the configuration file argument can be omitted. In this case, the default "supersid.cfg" is searched:
  1. In the '../Config/..' folder
  2. In the local directory
  3. In the home directory '~/' (*nix system only)
 
# File Organization #
The configuration file is a simple text file formatted as a classic '.ini' structure i.e. sections with squared brackets and a list of pairs 'key=value"
 
 The supported sections are:
  * [PARAMETERS](#id-section1)
  * [STATION_x](#id-section2) where x is a number in [1..n]
  * [Capture](#id-section3)
  * [Email](#id-section4)
  * [FTP](#id-section5)
  
<div id='id-section1'/>

## [PARAMETERS] ##
This section groups most of the parameters identifying your SuperSID monitor. Some optional parameters offer the possibility to change some default values used by the program.

### Monitor Identification ###
  * contact: email or phone number of the SuperSID owner. *Mandatory*
  * site_name: unique identification of the SuperSID monitor. *Mandatory*
  * monitor_id: unique id to distinguish the monitors running on one site
  * longitude: in decimal form
  * latitude: in decimal form
  * utc_offset:
  * time_zone:
  
### Log Parameters ###
  * audio_sampling_rate: **48000** or **96000** (you can experiment with other value as long as your card support them)
  * log_interval: number of second between two reading. Default is '**5**' seconds. Reading/sound capture last one second.
  * log_type: **filtered** or **raw**. When **filtered** is indicated, *bema_wing* function is called to smoothen raw data before writting the file else in **raw** mode, captured data are written 'as is'. Note that *sidfile.py* can be used as an utility to apply 'bema_wing' function to an existing file (raw or not) to smoothen its data.
  * data_path: fully qualified path where files will be written. If not mentionned then '../Data/' is used.
  * log_format:
    - **sid_format**: one file per station with first data column as timestamp and second data column as captured value
    - **supersid_format**: one file for all station. No timestamp but one data column per station. Each line is *log_interval* seconds after the previous, first line at 0:00:00UTC.
    - **supersid_extended**: one file for all station. First data column is extended timestamp HH:MM:SS.mmmmm and following data column as one per station.
  * hourly_save: **yes** / **no** (default). If **yes** then a raw file is written every hour to limit data loss.
  
### FTP to Standford server ###
Version 1.4: FTP information are no longer part of the [PARAMETERS] section. Refer to the [FTP] section below.
  
### Extra ###
  * scaling_factor:
  * mode: [ignored] **Server**, **Client**, **Standalone** (default) . Reserved for future client/server dev.
  * viewer: **text** for text mode light interface, **wx** for *wxPython* GUI or **tk** for TkInter GUI (default)
  * bema_wing: beta_wing parameter for sidfile.filter_buffer() calculation. Default is '**6**'.

  * number_of_stations: specify the number of stations to monitor. Each station is described within its own section.

<div id='id-section2'/>

## [STATION_x] ##
Each station to monitor is enumerated from 1 till n=*number_of_stations*. For each station, one must provide:
  * call_sign: Station ID (various VLF station lists exist like [AAVSO's] (http://www.aavso.org/vlf-station-list) and [Wikipedia's] (http://en.wikipedia.org/wiki/Very_low_frequency#List_of_VLF_transmissions))
  * frequency: emission frequency in Hz
  * color: [rgbyw] to draw multiple graph together in *SuperSID_plot.py*.
  
<div id='id-section3'/>

## [Capture] ##
This section can be omitted if you plan to use the 'pyaudio' library. If you want to use the "alsaaudio" library then you can declare:
  * Audio: python library to use **alsaaudio** or **pyaudio** (default), **server** reserved for client/server future dev.
  * Card: [for alsaaudio only] card name for capture. Default is 'External'.
  * PeriodSize: [for alsaaudio only] period size for capture. Default is '128'.
  
<div id='id-section4'/>

## [Email] ##
The 'supersid_plot.py' program can send you an email with the attached plot as a PDF file. In order to use this feature, you must provide the information necessary to contact your email server as well as which email to use.
  * from_mail: sender's emai
  * to_mail: recipient's email
  * email_server: email server to use (SMPT)
  * email_login: [optional] if your server requires a login for identification
  * email_password: [optional] if your server requires a password for identification
  
<div id='id-section5'/>

## [FTP] ##
Group all parameters to send data to an FTP server i.e. Standford data repository.
  * automatic_upload: [yes/no] if set to 'yes' then trigger the FTP data upload
  * ftp_server: URL of the server (sid-ftp.stanford.edu)
  * ftp_directory: target folder on the FTP server where files should be written (on Standford's server: /incoming/SuperSID/NEW/)
  * local_tmp: local temporary directpry used to write the files before their upload
  * call_signs: list of recorded stations to upload. Not all recorded stations might be of interrest: list only the most relevant one(s).