#!/usr/bin/python3
"""
    supersid_plot_gui.py
    version: 1.0 for Python 3.5
    Copyright: Eric Gibert
    Created in Sep-2017
"""
import os.path
import argparse
import tkinter as tk
from tkinter import ttk
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter as ff
from sidfile import SidFile


def m2hm(x, i):
    """Small function to format the time on horizontal axis - minor ticks"""
    t = matplotlib.dates.num2date(x)
    h = t.hour
    m = t.minute
    return '%(h)02d:%(m)02d' % {'h': h, 'm': m} if h % 2 == 1 else ''  # only for odd hours


def m2yyyymmdd(x, i):
    """Small function to format the date on horizontal axis - major ticks"""
    t = matplotlib.dates.num2date(x)
    y = t.year
    m = t.month
    d = t.day
    return '%(y)04d-%(m)02d-%(d)02d --' % {'y': y, 'm': m, 'd': d}


class Plot_Gui(ttk.Frame):
    """Supersid Plot GUI in tk"""
    COLOR = {'b': "blue", 'r': "red", 'g': "green", 'c': "cyan", 'm': "magenta", 'y': "yellow"}
    def __init__(self, parent, file_list, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        matplotlib.use('TkAgg')
        self.version = "1.0 20170902 (tk)"
        self.tk_root = parent
        self.hidden_stations = set()  # hide the graph if the station is in this set
        self.colorStation = {}        # the color assigned to a station in the graph
        self.sid_files = []           # ordered list of sid files read for the graph
        self.init_gui(file_list)

    def init_gui(self, file_list):
        """Builds GUI."""
        self.tk_root.title('SuperSID Plot')
        color_list = "".join(self.COLOR) # one color per station
        color_idx = 0
        self.daysList = set() # date of NOAA's pages already retrieved, prevent multiple fetch
        fig_title = []    # list of file names (w/o path and extension) as figure's title

        # prepare the GUI framework
        self.fig = Figure(facecolor='beige')
        self.canvas = FigureCanvas(self.fig, master=self.tk_root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.graph = self.fig.add_subplot(111)

        self.toolbar = NavigationToolbar2TkAgg( self.canvas, self.tk_root)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Add data to the graph
        for filename in sorted(file_list):
            sFile = SidFile(filename)
            self.sid_files.append(sFile)
            self.daysList.add(sFile.startTime)
            fig_title.append(os.path.basename(filename)[:-4])  # extension .csv assumed
            for station in set(sFile.stations) - self.hidden_stations:
                print(sFile.startTime, station)
                # Does this station already have a color? if not, reserve one
                if station not in self.colorStation:
                    self.colorStation[station] = color_list[color_idx % len(color_list)] + '-'  # format like 'b-'
                    color_idx += 1
                # Add points to the plot
                self.graph.plot_date(sFile.timestamp, sFile.get_station_data(station), self.colorStation[station])

        for s, c in self.colorStation.items():
            btn_color = "white" if s in self.hidden_stations else self.COLOR[c[0]]
            station_button = tk.Button(self.tk_root, text=s,
                                       bg=btn_color, activebackground="white")
            station_button.configure(command=lambda s=s, b=station_button: self.on_click_station(s, b))
            station_button.pack(side='left', padx=1, pady=1)

        self.statusbar_txt = tk.StringVar()
        self.label=tk.Label(self.tk_root,
                            bd=1, relief=tk.SUNKEN, #anchor=tk.W,
                           textvariable=self.statusbar_txt,
                           font=('arial', 10, 'normal'), pady=5)
        self.statusbar_txt.set(", ".join(fig_title))
        self.label.pack(fill=tk.X)

        self.show_figure()


    def on_click_station(self, station, button):
        """Invert the color of the button and hide/draw the corresponding graph"""
        print("click on", station)
        alt_color = self.COLOR[self.colorStation[station][0]]
        if station in self.hidden_stations:
            self.hidden_stations.remove(station)
            button.configure(bg=alt_color, activebackground="white")
        else:
            self.hidden_stations.add(station)
            button.configure(bg="white", activebackground=alt_color)
        self.update_graph()

    def show_figure(self):
        # some cosmetics on the figure
        current_axes = self.fig.gca()
        current_axes.xaxis.set_minor_locator(matplotlib.dates.HourLocator())
        current_axes.xaxis.set_major_locator(matplotlib.dates.DayLocator())
        current_axes.xaxis.set_major_formatter(ff(m2yyyymmdd))
        current_axes.xaxis.set_minor_formatter(ff(m2hm))
        current_axes.set_xlabel("UTC Time")
        current_axes.set_ylabel("Signal Strength")

        for label in current_axes.xaxis.get_majorticklabels():
            label.set_fontsize(8)
            label.set_rotation(30)  # 'vertical')
            # label.set_horizontalalignment='left'

        for label in current_axes.xaxis.get_minorticklabels():
            label.set_fontsize(12 if len(self.daysList) == 1 else 8)
        self.canvas.show()

    def update_graph(self):
        # Redraw the selected stations on a clear graph
        self.fig.clear()
        self.graph = self.fig.add_subplot(111)
        for sFile in self.sid_files:
            for station in set(sFile.stations) - self.hidden_stations:
                print(sFile.startTime, station)
                # Add points to the plot
                self.graph.plot_date(sFile.timestamp, sFile.get_station_data(station), self.colorStation[station])
        self.show_figure()

if __name__ == '__main__':
    filenames = ""
    parser = argparse.ArgumentParser()
    (args, unk) = parser.parse_known_args()
    file_list = [os.path.expanduser(f) for f in unk]

    root = tk.Tk()
    Plot_Gui(root, file_list)
    root.mainloop()