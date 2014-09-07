"""
tkSidViewer class implements a graphical user interface for SID based on tkinter
"""
from __future__ import print_function
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

# handle both Python 2 and 3
import sys
if sys.version_info[0] < 3:
    import Tkinter as tk
else:
    import tkinter as tk

import supersid_plot as SSP
from config import FILTERED, RAW

class tkSidViewer(tk.Frame):
    '''
    Create the Tkinter GUI
    '''
    def __init__(self, controller):
        """SuperSID Viewer using Tkinter GUI for standalone and client.
        Creation of the Frame with menu and graph display using matplotlib
        """
        self.version = "1.3.1 20130817"
        self.controller = controller  # previously referred as 'parent'
        tk.Frame.__init__(self, controller, background="white")
        self.controller.title("supersid @ " + self.controller.config['site_name'])

        # All Menus creation

        # Frame
        self.pack(fill=tk.BOTH, expand=1)

        # FigureCanvas
        psd_figure = Figure(facecolor='beige')
        self.canvas = FigureCanvas(psd_figure, self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.toolbar = NavigationToolbar2TkAgg( self.canvas, self )
        self.toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.axes = psd_figure.add_subplot(111)
        self.axes.hold(True)

        # StatusBar


        # Default View

    def updateDisplay(self, msg):
        """
        Receives data from thread and updates the display (graph and statusbar)
        """
        try:
            self.canvas.draw()
            self.status_display(msg.data)
        except:
            pass

    def clear(self):
        try:
            self.axes.cla()
        except:
            pass

    def status_display(self, message, level=0, field=0):
        pass

def MainLoop():
    root = tk()
    root.geometry("300x280+300+300")
    app = tkSidViewer(root)
    root.mainloop()