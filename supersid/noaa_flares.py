#!python3
"""
    Retrieve data from NOAA regarding X-ray solar flares (GOES):
    - datetime of start, high, end
    - classification (A, B, C, M, X...)

    This data can be used by the supersid_plot to enrich the graph with the X-ray flares

    if the date is in the current year then FTP for the day's file is done
    else the complete past  year file is downloaded (and kept) then data is read

"""
import urllib.request, urllib.error
from os import path
from datetime import datetime, date

class NOAA_flares(object):
    """
        This object carries a list of all events of a given day
    """
    ngdc_URL = "https://www.ngdc.noaa.gov/stp/space-weather/solar-data/solar-features/solar-flares/x-rays/goes/xrs/"
    def __init__(self, day):
        if isinstance(day, str):
            self.day = day[:8]  # limit to YYYYMMDD
        elif isinstance(day, datetime) or isinstance(day, date):
            self.day = day.strftime('%Y%m%d')
        else:
            raise TypeError("Unknown date format - expecting str 'YYYYMMDD' or datetime/date")

        self.Tstamp = lambda HHMM: datetime.strptime(self.day + HHMM, "%Y%m%d%H%M")  # "201501311702" -> datetime(2015, 1, 31, 17, 2)
        today = date.today()
        self.XRAlist = []

        # Starting in year 2017, NOAA makes the data available via FTP.
        # Earlier year data is available via HTTP.
        # So need to decide how to fetch the data based on the date.
        if int(self.day[:4]) >= 2017:
            # given day is 2017 or later --> fetch data by FTP
            self.ftp_NOAA()
        else:
            # given day is 2016 or earlier --> fetch data by https
            # if the file is NOT in the ../PRIVATE/ directory the we need to fetch it first
            # then read line by line to grab the data from the expected day
            file_path = self.http_ngdc()
            with open(file_path, "rt") as fin:
                for line in fin:
                    fields = line.split()
                    if fields and fields[0][5:11]==self.day[2:]:  # compare YYMMDD only
                        # two line formats:
                        #31777151031  0835 0841 0839 N05E57                         C 17    G15  3.6E-04 12443 151104.6
                        #31777151031  1015 1029 1022                                C 15    G15  1.0E-03
                        if len(fields)==11:
                            self.XRAlist.append((
                                fields[4],
                                self.Tstamp(fields[1]),  # beg time
                                self.Tstamp(fields[2]),  # highest time,
                                self.Tstamp(fields[3]),  # end time,
                                fields[5]+fields[6][0]+'.'+fields[6][1]))
                        elif len(fields)==8:
                            self.XRAlist.append((
                                "None",
                                self.Tstamp(fields[1]),  # beg time
                                self.Tstamp(fields[2]),  # highest time,
                                self.Tstamp(fields[3]),  # end time,
                                fields[4]+fields[5][0]+'.'+fields[5][1]))
                        else:
                            print("Please check this line format:")
                            print(line)

    def http_ngdc(self):
        """
            Get the file for a past year from HTTP ngdc if not already saved
            Return the full path of the data file
        """
        file_name = "goes-xrs-report_{}.txt".format(self.day[:4]) if self.day[:4] != "2015"  \
                                                     else "goes-xrs-report_2015_modifiedreplacedmissingrows.txt"
        file_path = path.join("..", "Private", file_name)  # must exists else create supersid/Private
        if not path.isfile(file_path):
            try:
                url = path.join(self.ngdc_URL, file_name)
                txt = urllib.request.urlopen(url).read().decode()
            except (urllib.error.HTTPError, urllib.error.URLError) as err:
                print("Cannot retrieve the file", file_name)
                print("from URL:", url)
                print(err, "\n")
            else:
                with open(file_path, "wt") as fout:
                    fout.write(txt)
        return file_path


    def ftp_NOAA(self):
        """
          Get the XRA data from NOAA website
          (Used to draw corresponding lines on the plot)
          Returns the list of XRA events as
          [(eventName, BeginTime, MaxTime, EndTime, Particulars), ...]
          from the line:
          1000 +     1748   1752      1755  G15  5   XRA  1-8A      M1.0    2.1E-03   2443
        """
        #           ftp://ftp.swpc.noaa.gov/pub/indices/events/20141030events.txt
        NOAA_URL = 'ftp://ftp.swpc.noaa.gov/pub/indices/events/%sevents.txt' % (self.day)
        response, XRAlist = None, []
        try:
            response = urllib.request.urlopen(NOAA_URL)
        except (urllib.error.HTTPError, urllib.error.URLError) as err:
            print("Cannot retrieve the file", '%sevents.txt' % (self.day))
            print("from URL:", NOAA_URL)
            print(err, "\n")
        else:
            for webline in response.read().splitlines():
                fields = str(webline, 'utf-8').split()  # Python 3: cast bytes to str then split
                if len(fields) >= 9 and not fields[0].startswith("#"):
                    if fields[1] == '+': fields.remove('+')
                    if fields[6] in ('XRA',):  # maybe other event types could be of interrest
                        #      eventName,    BeginTime,    MaxTime,      EndTime,      Particulars
                        # msg = fields[0] + " " + fields[1] + " " + fields[2] + " " + fields[3] + " " + fields[8]
                        try:
                            btime = self.Tstamp(fields[1])  # 'try' necessary as few occurences of --:-- instead of HH:MM exist
                        except:
                            pass
                        try:
                            mtime = self.Tstamp(fields[2])
                        except:
                            mtime = btime
                        try:
                            etime = self.Tstamp(fields[3])
                        except:
                            etime = mtime
                        self.XRAlist.append((fields[0], btime, mtime, etime, fields[8]))  # as a tuple

    def print_XRAlist(self):
        for eventName, BeginTime, MaxTime, EndTime, Particulars in self.XRAlist:
            print(eventName, BeginTime, MaxTime, EndTime, Particulars)


if __name__ == '__main__':
    flare = NOAA_flares("20140104")
    print(flare.day, "\n", flare.print_XRAlist(), "\n")
    flare = NOAA_flares("20170104")
    print(flare.day, "\n", flare.print_XRAlist(), "\n")
    flare = NOAA_flares("20201211")
    print(flare.day, "\n", flare.print_XRAlist(), "\n")
