#!/bin/env python2
'''
    supersid_plot
    version: 1.2 enhanced
    Original Copyright: Stanford Solar Center - 2008
    Copyright: Eric Gibert - 2012


    Support one to many files as input, even in Drag & Drop
    Draw multi-stations graphs
    Offer the possibility to generate PDF and email it (perfect for batch mode)
    Offer the possibility to fetch NOAA XRA data and add them on the plot

'''

#-------------------------------------------------------------------------------
import sys

import numpy
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter as ff
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.dates
import datetime, time
import itertools

import urllib2
import os.path
import glob
import smtplib
from email.mime.multipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from optparse import OptionParser
#-------------------------------------------------------------------------------
# Script personalization
DEFAULT_STATION="NWC,JJI"  #  <-- please change for your own monitor
SUPERSID_ID="DAISYSG"  #  <-- please change for your own monitor

#-------------------------------------------------------------------------------
# function to send automatically an email with the plot (as PDF) attached

def sendMail(To_mail, msgBody, PDFfile):
    """Send the mail using the smtplib module
       The plot (as PDF) attached"""
    #constant to setup as "localisation" --> TO DO: move to the config file ume [email] section
    senderEmail = "ericgibert@asia-dragonfly.net"       # <-- please change for your own monitor
    mailserver = "mail.server.net"                      # <-- please change for your own monitor
    mailserveruser = "myaccount"    					# <-- please set to None if no login required
    mailserverpasswd = "zepassword"                     # <-- please set to None if no login required

    # create the mail message
    msg = MIMEMultipart(_subtype='html')
    msg['Subject'] = 'Auto-generated eMail from SuperSID'
    msg.attach( MIMEText(msgBody) )

    # Following headers are useful to show the email correctly
    msg['From'] = senderEmail
    msg['Reply-to'] = senderEmail
    msg['To'] = To_mail

    # attach the PDF file
    ctype, encoding = ('application/pdf', None)
    maintype, subtype = ctype.split('/', 1)
    with open(PDFfile, 'rb') as pdf:
        att = MIMEBase(maintype, subtype)
        att.set_payload(pdf.read())
        encoders.encode_base64(att)
        att.add_header('Content-Disposition', 'attachment', filename=PDFfile)
        msg.attach(att)

    # Establish an SMTP object by connecting to your mail server
    s = smtplib.SMTP()
    s.connect(mailserver)
    if mailserveruser is not None:
        s.login(mailserveruser, mailserverpasswd)
    # Send the email - real from, real to, extra headers and content ...
    s.sendmail(senderEmail, To_mail, msg.as_string())
    s.close()

    print "message to %s sent." % To_mail

#-------------------------------------------------------------------------------
class SIDfile():
    """Class to read SID or SuperSID files. Provide header information and data content access."""
    ONE_SECOND = (matplotlib.dates.datestr2num("2012-01-01 01:00:00") - matplotlib.dates.datestr2num("2012-01-01 00:00:00"))/3600.0
    def __init__(self, filename):
        """Default intialization. Header reading."""
        self.filename = filename
        #header
        self.sid_params = {}    # dictionary of all header pairs
        self.stations = []      # list of the stations: StationID | Stations
        self.startTime = ""     # datetime from UTC_StartTime
        self.isSuperSID = False # default SID format: one station with timestamp
        self.headerNbLines = 0  # number of header lines
        #data lines
        self.data = []      # will contain the reading for each station
        self.timestamp = [] # will contain the timestamp of each line

        # Read the header lines - populate the self.sid_params dictionary
        try:
            with open(self.filename,"rt") as fin:
                self.lines = fin.readlines()  # this buffer will be used by 'read_data' method
                for line in self.lines:
                    if line[0] != "#": break   # end of header
                    self.headerNbLines += 1
                    tokens = line.split("=")
                    if len(tokens) == 2:
                        key = tokens[0][1:].lower().strip()  # force to lower case
                        self.sid_params[key]=tokens[1].strip()
        except IOError as why:
            print str(why)
            print filename

        # SuperSID files have an entry "Stations" while SID files have "StationID"
        if self.sid_params.has_key("stations"):
            self.isSuperSID = True
            self.stations = self.sid_params["stations"].split(",")
        elif self.sid_params.has_key("stationid"):
            self.isSuperSID = False
            self.stations = [ self.sid_params["stationid"] ]
        else:
            print "ERROR: No station ID found in this file. Please check!"

        # get the datetime for UTC_StartTime
        if self.sid_params.has_key("utc_starttime"):
            self.startTime = matplotlib.dates.datestr2num(self.sid_params["utc_starttime"])
        else:
            print "ERROR: No UTC_StartTime found in this file. Please check!"

        # do we have a LogInterval ?
        if not self.sid_params.has_key("loginterval"):
            print "ERROR: LogInterval is missing! Please check. I assume 5 sec..."
            self.LogInterval = 5
        else:
            self.LogInterval = int(self.sid_params["loginterval"])

    def generate_timestamp(self):
        """Create the timestamp vector by adding LogInterval seconds to UTC_StartTime"""
        self.timestamp = numpy.empty(self.data.shape[0])
        # add 'interval' seconds to UTC_StartTime for each entries
        interval =  SIDfile.ONE_SECOND * self.LogInterval
        i = len(self.timestamp)
        while i > 0:
            i -= 1
            self.timestamp[i] =  i * interval + self.startTime

    def read_data(self):
        """Using the self.lines buffer, converts the data lines in numpy arrays.
            - One array self.data for the data (one column by station)
            - One array self.timestamp for the timestamp
        Reading method differs accordingly to the self.isSuperSID flag
        """
        # print self.filename
        if self.isSuperSID:  # file format: one data column per station, no time stamp (has to be generated)
            self.data = numpy.loadtxt(self.lines, comments='#', delimiter=",")
            self.generate_timestamp()
        else: # two columns file: [timestamp, data]. Try to avoid reading timestamps: date str to num conversion takes time
            if len(self.lines) - self.headerNbLines == (60 * 60 * 24) / self.LogInterval:
                print "Optimization: generate timestamp instead of reading & converting them from file."
                self.data = numpy.loadtxt(self.lines, comments='#', delimiter=",", usecols=(1,)) # only read data column
                self.generate_timestamp()
            else:
                print "Warning: some data are missing so timestamps are read & converted from file."
                inData = numpy.loadtxt(self.lines, comments='#', delimiter=",", converters={0: matplotlib.dates.datestr2num})
                self.timestamp = inData[:,0]
                self.data = inData[:,1]

    def get_station_data(self, stationId):
        """Return the numpy array of the given station's data"""
        idx = self.stations.index(stationId)
        if self.isSuperSID:
            return self.data[:,idx]
        else:
            return self.data

#-------------------------------------------------------------------------------

class SUPERSID_PLOT():

    def __init__(self):
        pass

    def select_file(self):
        self.filename = "";

    def read_data(self, filename):
        """Transfered in SIDfile class"""
        pass


    #-------------------------------------------------------------------------------
    # not used anymore
    def sim_read_data(self, filename):
        # parse header , parse data
        self.filename = filename
        self.log_interval = 5
        samples_per_hour = int (60 / self.log_interval) * 60
        number_of_samples = samples_per_hour * 24

        # sim data
        self.data = numpy.arange(0, number_of_samples)
        self.t    = numpy.arange(0.0, 24.0 , 1.0/samples_per_hour)

        value = 10
        for i in range(number_of_samples):
            if ((i % samples_per_hour) == 0):
                value += 10
            self.data[i]=value
        return

    #-------------------------------------------------------------------------------
    # not used anymore
    def plot_data(self):


        plt.plot(self.t, self.data)


        # set other decorating plot properties
        current_axes = plt.gca()
        current_axes.set_xlim([0,24])
        current_axes.set_xlabel("UTC Time")
        current_axes.set_ylabel("Signal Strength")
        #current_axes.grid(True)


        # figure
        current_figure = plt.gcf()
        current_figure.canvas.manager.set_window_title('supersid_plot')
        #current_figure.set_figsize_inches(8.0,6.0)

        # Sunrise and sunset shade
        sun_rise = 6.0
        sun_set  = 18.0
        plt.axvspan(0.0, sun_rise, facecolor='blue', alpha=0.2)
        plt.axvspan(sun_set, 24.0, facecolor='blue', alpha=0.2)


        plt.show()

    #-------------------------------------------------------------------------------
    def m2hm(self, x, i):
        """Small function to format the time on horizontal axis - minor ticks"""
        t = matplotlib.dates.num2date(x)
        h = t.hour
        m = t.minute
        return '%(h)02d:%(m)02d' % {'h':h,'m':m} if h % 2 == 1 else ''  # only for odd hours

    def m2yyyymmdd(self, x, i):
        """Small function to format the date on horizontal axis - major ticks"""
        t = matplotlib.dates.num2date(x)
        y = t.year
        m = t.month
        d = t.day
        return '%(y)04d-%(m)02d-%(d)02d --' % {'y':y,'m':m, 'd': d}

    def plot_filelist(self, filelist, showPlot = True, eMail=None, pdf=None, web=False):
        """Read the files in the filelist parameters.
           Each data are combine in one plot.
           That plot can be displayed or not (showPlot), sent by email (eMail provided), saved as pdf (pdf provided).
           Connection for the given days to NOAA website is possible (web) in order to drow vetical lines ofr XRA data."""

        emailText = []
        Tstamp = lambda HHMM: datetime.datetime(year=int(day[:4]), month=int(day[4:6]), day=int(day[6:8]),
                                                hour=int(HHMM[:2]), minute=int(HHMM[2:]))
        ## Sunrise and sunset shade 
        #sun_rise = 6.0
        #sun_set  = 18.0
        #plt.axvspan(0.0, sun_rise, facecolor='blue', alpha=0.2)
        #plt.axvspan(sun_set, 24.0, facecolor='blue', alpha=0.2)

        if type(filelist) is str:
            if filelist.find(',') >= 0:  # file1,file2,...,fileN given as script argument
                filelist = filelist.split(",")
            else:
                filelist = (filelist, )

        filenames = []
        filenames.extend([a for a in itertools.chain.from_iterable([glob.glob(f) for f in filelist])]) #  use glob for one or more files
        #print filenames

        # plot's figure and axis
        fig = plt.figure()
        current_axes = fig.gca()
        current_axes.xaxis.set_minor_locator(matplotlib.dates.HourLocator())
        current_axes.xaxis.set_major_locator(matplotlib.dates.DayLocator())
        current_axes.xaxis.set_major_formatter(ff(self.m2yyyymmdd))
        current_axes.xaxis.set_minor_formatter(ff(self.m2hm))
        current_axes.set_xlabel("UTC Time")
        current_axes.set_ylabel("Signal Strength")

        ## Get data from files
        maxData, data_length = -1, -1; #  impossible values
        XRAlist = []      # flare list from NOAA
        daysList = set()  # NOAA pages already retrieved, prevent multiple fetch
        figTitle = []     # list of file names (w/o path and extension) as figure's title
        # one color per station
        colorList = "brgcmy"
        colorStation = {}
        colorIdx = 0

        #print filenames
        time.clock()
        for filename in sorted(filenames):
            figTitle.append(os.path.basename(filename)[:-4]) # extension .csv assumed
            sFile = SIDfile(filename)
            sFile.read_data()
            for station in sFile.stations:
                # Does this station already have a color? if not, reserve one
                if not colorStation.has_key(station):
                    colorStation[station] = colorList[colorIdx % len(colorList)] + '-'  # format like 'b-'
                    colorIdx += 1
                # Add points to the plot
                plt.plot_date(sFile.timestamp, sFile.get_station_data(station), colorStation[station])
                # Extra housekeeping
                maxData = max(max(sFile.get_station_data(station)), maxData)  # maxData will be used later to put the XRA labels up
                print len(sFile.get_station_data(station)), "points plotted after reading", os.path.basename(filename)
                emailText.append(str(len(sFile.get_station_data(station))) + " points plotted after reading " + filename)

                if web and sFile.startTime not in daysList: # get the XRA data from NOAA website to draw corresponding lines on the plot
                    # fetch that day's flares on NOAA as not previously accessed
                    day = sFile.sid_params["utc_starttime"][:10].replace("-","")
                    NOAA_URL = 'http://www.swpc.noaa.gov/ftpdir/warehouse/%s/%s_events/%sevents.txt' % (day[:4], day[:4], day)
                    try:
                        #response = urllib2.urlopen('http://www.swpc.noaa.gov/ftpdir/indices/events/%sevents.txt' % day)
                        response = urllib2.urlopen(NOAA_URL)
                    except urllib2.HTTPError as err:
                        print err
                        print NOAA_URL
                    lastXRAlen = len(XRAlist) # save current number of XRA events in memory
                    for webline in response.read().splitlines():
                        fields = webline.split()
                        if len(fields) >= 9 and not fields[0].startswith("#"):
                            if fields[1] == '+': fields.remove('+')
                            if fields[6] in ('XRA', ):  # maybe other event types could be of interrest
                                emailText.append(fields[0]+" "+fields[1]+" "+fields[2]+" "+fields[3]+" "+fields[8])
                                print fields[0]+" "+fields[1]+" "+fields[2]+" "+fields[3]+" "+fields[8]
                                try:
                                    btime = Tstamp(fields[1])   # 'try' necessary as few occurences of --:-- instead of HH:MM exist
                                except:
                                    pass
                                try:
                                    mtime = Tstamp(fields[2])
                                except:
                                    mtime = btime
                                try:
                                    etime = Tstamp(fields[3])
                                except:
                                    etime = mtime
                                XRAlist.append( (fields[0], btime, mtime, etime, fields[8]) )  # as a tuple

                    emailText.append(str(len(XRAlist) - lastXRAlen) + " XRA events recorded by NOAA on " + day)
                    print len(XRAlist) - lastXRAlen, "XRA events recorded by NOAA on", day
                # keep track of the days
                daysList.add(sFile.startTime)

        print "All files read in", time.clock(), "sec."

        if web: # add the lines marking the retrieved flares from NOAA
            alternate = 0
            for eventName, BeginTime, MaxTime, EndTime, Particulars in XRAlist:
                plt.vlines( [BeginTime, MaxTime, EndTime], 0, maxData,
                            color=['g','r','y'], linestyles='dotted')
                plt.text(MaxTime, alternate * maxData, Particulars, horizontalalignment='center',
                         bbox=dict(fill=True, alpha=0.5, facecolor='w'))
                alternate = 0 if alternate==1 else 1


        # plot/page size / figure size with on A4 paper
        if len(daysList) == 1:
            fig.set_size_inches(29.7 / 2.54, 21.0 / 2.54, forward=True)
        else:  # allow PDF poster for many days (monthly graph) --> use Adobe PDF Reader --> Print --> Poster mode
            fig.set_size_inches((29.7 / 2.54) * (len(daysList)/2.0), (21.0 / 2.54) / 2.0, forward=True)
        fig.subplots_adjust(bottom=0.08, left = 0.05, right = 0.98, top=0.95)

        # some cosmetics on the figure
        for label in current_axes.xaxis.get_majorticklabels():
            label.set_fontsize(8)
            label.set_rotation('vertical')
            #label.set_horizontalalignment='left'

        for label in current_axes.xaxis.get_minorticklabels():
            label.set_fontsize(12 if len(daysList) == 1 else 8)

        fig.suptitle(", ".join(figTitle))

        xLegend = 0.03
        for station, color in colorStation.iteritems():
            fig.text(xLegend, 0.93, station, color=color[0], fontsize=12, bbox={'fc':"w", 'pad':10, 'ec':color[0]})
            xLegend += 0.05

        # actions requested by user
        if pdf or eMail:
            pp = PdfPages(pdf if pdf is not None else 'Image.pdf')  # in case option eMail is given but not pdf
            plt.savefig(pp, format='pdf')
            pp.close()
        if showPlot: plt.show()
        if eMail: sendMail(eMail, "\n".join(emailText), pdf)


#-------------------------------------------------------------------------------
'''
For running supersid_plot.py directly from command line
'''

def do_main(filelist, showPlot = True, eMail=None, pdf=None, web=False):
    ssp = SUPERSID_PLOT()
    ssp.plot_filelist(filelist, showPlot, eMail, pdf, web);

if __name__ == '__main__':

    filename = ""
    # Only one argument to the script: either [today|yesterday] or a file name (wildcards are accepted)
    if len(sys.argv) == 2 and sys.argv[1][0] != '-':
        if sys.argv[1].lower() in ('today', 'yesterday'):
            Now = datetime.datetime.now()
            if sys.argv[1].lower() == 'yesterday': Now -= datetime.timedelta(days=1)
            filename = "../Data/%s_%s_%04d-%02d-%02d.csv" % (SUPERSID_ID, DEFAULT_STATION, Now.year,Now.month,Now.day)
        else:
            filename = sys.argv[1]
        do_main(filename)
    # many arguments, some may be options. Non options will be consider as file names.
    elif len(sys.argv) > 1:
        parser = OptionParser()
        parser.add_option("-f", "--file", dest="filename",
                  help="Read SID and SuperSID csv file(s). Wildcards accepted.", metavar="FILE|FILE*.csv")
        parser.add_option("-p", "--pdf", dest="pdffilename",
                  help="Write the plot in a PDF file.", metavar="filename.PDF")
        parser.add_option("-e", "--email", dest="email",
                  help="sends PDF file to the given email", metavar="address@server.ex")
        parser.add_option("-n", "--noplot",
                  action="store_false", dest="showPlot", default=True,
                  help="do not display the plot. Usefull in batch mode.")
        parser.add_option("-w", "--web",
                  action="store_true", dest="webData", default=False,
                  help="Add information on flares (XRA) from NOAA website.")
        parser.add_option("-y", "--yesterday",
                  action="store_true", dest="askYesterday", default=False,
                  help="Yesterday's date is used for the file name.")
        parser.add_option("-t", "--today",
                  action="store_true", dest="askToday", default=False,
                  help="Today's date is used for the file name.")
        parser.add_option("-i", "--site_id", dest="site_id",
                  help="Site ID to use in the file name", metavar="SITE_ID")
        parser.add_option("-s", "--station", dest="station_id",
                  help="Station ID to use in the file name", metavar="STAID")
        (options, args) = parser.parse_args()

        print "Options:",options
        print "Files:", args

        if options.filename is None: # no --file option specified
            if len(args) > 0:  # last non options args assumed to be a list of file names
                filename = ",".join(args)
            else:
                # try building the file name from other options
                Now = datetime.datetime.now() # by default today
                if options.askYesterday: Now -= datetime.timedelta(days=1)
                # stations can be given as a comma delimited string
                # SuperSID id is unique
                lstFileNames = []
                strStations = options.station_id if options.station_id is not None else DEFAULT_STATION
                for station in strStations.split(","):
                    lstFileNames.append("../Data/%s_%s_%04d-%02d-%02d.csv" % (options.site_id if options.site_id is not None else SUPERSID_ID,
                                                                     station, Now.year,Now.month,Now.day))
                filename = ",".join(lstFileNames)   
        else:
            filename = options.filename

        do_main(filename, showPlot = options.showPlot, eMail=options.email, pdf=options.pdffilename, web = options.webData)

    else:
        print """Usage:   supersid_plot.py  filename.csv"""
        print """Usage:   supersid_plot.py  "filename1.csv,filename2.csv,filename3.csv" """
        print """Usage:   supersid_plot.py  "filename*.csv" """
        print """Note: " are optional on Windows, mandatory on *nix"""
        print """Other options:  supersid_plot.py -h"""


