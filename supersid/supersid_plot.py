#!/usr/bin/python
'''
    supersid_plot
    version: 1.3.1 enhanced for Python 2.7 and 3.3
    Original Copyright: Stanford Solar Center - 2008
    Copyright: Eric Gibert - 2012


    Support one to many files as input, even in Drag & Drop
    Draw multi-stations graphs
    Offer the possibility to generate PDF and email it (perfect for batch mode)
    Offer the possibility to fetch NOAA XRA data and add them on the plot

'''
from __future__ import print_function   # use the new Python 3 'print' function
import sys
import datetime, time
import itertools
import os.path
import glob
# matplolib tools
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter as ff
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.dates
# Internet and Email modules
import smtplib
try:  # python 2.7 vs. Python 3.3
    import urllib2
    from email.MIMEText import MIMEText
except ImportError:
    import urllib.request, urllib.error
    from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders, utils
import argparse
# SuperSID modules
from sidfile import SidFile
from config import Config

def sendMail(config, To_mail, msgBody, PDFfile):
    """Send the mail using the smtplib module
       The plot (as PDF) attached"""
    senderEmail = config.get("from_mail","")
    mailserver = config.get("email_server","")
    mailserveruser = config.get("email_login","")          # <-- set to None if no login required
    mailserverpasswd = config.get("email_password","")     # <-- set to None if no login required

    # create the mail message
    msg = MIMEMultipart(_subtype='html')
    msg['Subject'] = 'Auto-generated eMail from SuperSID'
    msg.attach( MIMEText(msgBody) )

    # Following headers are useful to show the email correctly
    msg['From'] = senderEmail
    msg['Reply-to'] = senderEmail
    msg['To'] = To_mail
    msg['Date'] = utils.formatdate(localtime = 1)

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
    if mailserveruser: s.login(mailserveruser, mailserverpasswd)
    # Send the email - real from, real to, extra headers and content ...
    s.sendmail(senderEmail, To_mail, msg.as_string())
    s.close()
    print ("Email to %s sent." % To_mail)

class SUPERSID_PLOT():
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

    def plot_filelist(self, filelist, showPlot = True, eMail=None, pdf=None, web=False, config=None):
        """Read the files in the filelist parameters.
           Each data are combine in one plot.
           That plot can be displayed or not (showPlot), sent by email (eMail provided), saved as pdf (pdf provided).
           Connection for the given days to NOAA website is possible (web) in order to draw vetical lines for XRA data."""
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
        # use glob for one or more files
        filenames.extend([a for a in itertools.chain.from_iterable([glob.glob(f) for f in filelist])])
        #print (filenames)

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
        daysList = set()  # date of NOAA's pages already retrieved, prevent multiple fetch
        figTitle = []     # list of file names (w/o path and extension) as figure's title
        # one color per station
        colorList = "brgcmy"
        colorStation = {}
        colorIdx = 0

        time.clock()
        for filename in sorted(filenames):
            figTitle.append(os.path.basename(filename)[:-4]) # extension .csv assumed
            sFile = SidFile(filename)
            for station in sFile.stations:
                # Does this station already have a color? if not, reserve one
                if station not in colorStation:
                    colorStation[station] = colorList[colorIdx % len(colorList)] + '-'  # format like 'b-'
                    colorIdx += 1
                # Add points to the plot
                plt.plot_date(sFile.timestamp, sFile.get_station_data(station), colorStation[station])
                # Extra housekeeping
                maxData = max(max(sFile.get_station_data(station)), maxData)  # maxData will be used later to put the XRA labels up
                #msg = str(len(sFile.get_station_data(station))) + " points plotted after reading " + os.path.basename(filename)
                msg = "[{}] {} points plotted after reading {}".format(station, len(sFile.get_station_data(station)), os.path.basename(filename))
                print (msg)
                emailText.append(msg)

                if web and sFile.startTime not in daysList:
                    # get the XRA data from NOAA website to draw corresponding lines on the plot
                    # fetch that day's flares on NOAA as not previously accessed
                    day = sFile.sid_params["utc_starttime"][:10].replace("-","")
                    #NOAA_URL = 'http://www.swpc.noaa.gov/ftpdir/warehouse/%s/%s_events/%sevents.txt' % (day[:4], day[:4], day)
                    #ftp://ftp.swpc.noaa.gov/pub/indices/events/20141030events.txt
                    NOAA_URL = 'ftp://ftp.swpc.noaa.gov/pub/indices/events/%sevents.txt' % (day)
                    response = None
                    if sys.version[0]<'3':  # python 2.7 vs. Python 3.3
                        try:
                            response = urllib2.urlopen(NOAA_URL)
                        except urllib2.HTTPError as err:                            
                            print (err,"\n",NOAA_URL)
                    else:
                        try:
                            response = urllib.request.urlopen(NOAA_URL)
                        except urllib.error.HTTPError as err:                            
                            print (err,"\n",NOAA_URL)
                    lastXRAlen = len(XRAlist) # save temporarly current number of XRA events in memory
                    if response:
                        for webline in response.read().splitlines():
                            if sys.version[0]>='3': webline = str(webline, 'utf-8') # Python 3: cast bytes to str
                            fields = webline.split()
                            if len(fields) >= 9 and not fields[0].startswith("#"):
                                if fields[1] == '+': fields.remove('+')
                                if fields[6] in ('XRA', ):  # maybe other event types could be of interrest
                                    #     eventName,    BeginTime,    MaxTime,      EndTime,      Particulars
                                    msg = fields[0]+" "+fields[1]+" "+fields[2]+" "+fields[3]+" "+fields[8]
                                    emailText.append(msg)
                                    print (msg)
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

                    msg = str(len(XRAlist) - lastXRAlen) + " XRA events recorded by NOAA on " + day
                    emailText.append(msg)
                    print (msg)
                # keep track of the days
                daysList.add(sFile.startTime)

        print ("All files read in", time.clock(), "sec.")

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
            label.set_rotation(30)  # 'vertical')
            #label.set_horizontalalignment='left'

        for label in current_axes.xaxis.get_minorticklabels():
            label.set_fontsize(12 if len(daysList) == 1 else 8)

        fig.suptitle(", ".join(figTitle))

        xLegend = 0.03
        for station, color in colorStation.items():
            fig.text(xLegend, 0.93, station, color=color[0], fontsize=12, bbox={'fc':"w", 'pad':10, 'ec':color[0]})
            xLegend += 0.05

        # actions requested by user
        if pdf or eMail:
            pp = PdfPages(pdf or 'Image.pdf')  # in case option eMail is given but not pdf
            plt.savefig(pp, format='pdf')
            pp.close()
        if showPlot: plt.show()
        if eMail: sendMail(config, eMail, "\n".join(emailText), pdf or 'Image.pdf')


#-------------------------------------------------------------------------------
'''
For running supersid_plot.py directly from command line
'''

def do_main(filelist, showPlot = True, eMail=None, pdf=None, web=False, config=None):
    ssp = SUPERSID_PLOT()
    ssp.plot_filelist(filelist, showPlot, eMail, pdf, web, config);

if __name__ == '__main__':
    filenames = ""
    parser = argparse.ArgumentParser(description="""Usage:   supersid_plot.py  filename.csv\n
     Usage:   supersid_plot.py  "filename1.csv,filename2.csv,filename3.csv"\n
     Usage:   supersid_plot.py  "filename*.csv"\n
     Note: " are optional on Windows, mandatory on *nix\n
     Other options:  supersid_plot.py -h\n""")
    parser.add_argument("-c", "--config", dest="cfg_filename", required=False, default='',
              help="SuperSID Configuration file")
    parser.add_argument("-f", "--file", dest="filename",
              help="Read SID and SuperSID csv file(s). Wildcards accepted.", metavar="FILE|FILE*.csv")
    parser.add_argument("-p", "--pdf", dest="pdffilename",
              help="Write the plot in a PDF file.", metavar="filename.PDF")
    parser.add_argument("-e", "--email", dest="email", nargs="?",
              help="sends PDF file to the given email", metavar="address@server.ex")
    parser.add_argument("-n", "--noplot",
              action="store_false", dest="showPlot", default=True,
              help="do not display the plot. Usefull in batch mode.")
    parser.add_argument("-w", "--web",
              action="store_true", dest="webData", default=False,
              help="Add information on flares (XRA) from NOAA website.")
    parser.add_argument("-y", "--yesterday",
              action="store_true", dest="askYesterday", default=False,
              help="Yesterday's date is used for the file name.")
    parser.add_argument("-t", "--today",
              action="store_true", dest="askToday", default=False,
              help="Today's date is used for the file name.")
    parser.add_argument("-i", "--site_id", dest="site_id",
              help="Site ID to use in the file name", metavar="SITE_ID")
    parser.add_argument("-s", "--station", dest="station_id",
              help="Station ID to use in the file name or * for all", metavar="STAID")
    parser.add_argument("-v", "--verbose",
              action="store_true", dest="verbose", default=False,
              help="Print more messages.")
    (args, unk) = parser.parse_known_args()
    #print ("Options:",args)
    #print ("Files:", unk)
    if args.cfg_filename:
        config = Config(args.cfg_filename)
        if args.verbose: 
            print(args.cfg_filename, "read as config file.")
            for k, v in config.items():
                print(k, "=", v)
            for s in config.stations:
                print("Station:", s)
    else:
        config={}
    #print (config)
    if args.filename is None: # no --file option specified
        if len(unk) > 0:  # last non options arguments are assumed to be a list of file names
            filenames = ",".join(unk)
        else:
            # try building the file name from given options or found in the provided .cfg file
            Now = datetime.datetime.now() # by default today
            if args.askYesterday: Now -= datetime.timedelta(days=1)
            # stations can be given as a comma delimited string
            # SuperSID id is unique
            lstFileNames = []
            data_path = config.get("data_path", None) or "../Data"
            if args.station_id is None:  # file name like supersid file format
                lstFileNames.append("%s/%s_%04d-%02d-%02d.csv" % 
                                    (data_path,
                                     args.site_id or config["site_name"],
                                     Now.year,Now.month,Now.day))
            else:
                if args.station_id == '*': # all possible stations from .cfg file - must be '*' on the command line!
                    strStations = ",".join([s["call_sign"] for s in config.stations])
                else: # only the given stations - can be a comma delimited list
                    strStations = args.station_id
                # build the list of sid format file names
                for station in strStations.split(","):
                    lstFileNames.append("%s/%s_%s_%04d-%02d-%02d.csv" % 
                                        (data_path,
                                         args.site_id or config["site_name"],
                                         station, Now.year,Now.month,Now.day))
            filenames = ",".join(lstFileNames)
    else:
        filenames = args.filename
    
    if args.verbose:
        print("List of files:", filenames)
        
    do_main(filenames, showPlot = args.showPlot, eMail=args.email or config.get("to_mail", None), pdf=args.pdffilename, web = args.webData, config=config)


