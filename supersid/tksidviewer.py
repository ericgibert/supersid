"""
tkSidViewer class implements a graphical user interface for SID based on tkinter
"""
# created on 20150421
# first official release 20150801
from __future__ import print_function
import matplotlib
# matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

# handle both Python 2 and 3
try:# python 3
    import tkinter as tk
    import tkinter.messagebox as MessageBox
    import tkinter.filedialog as FileDialog
except ImportError:
    # python 2
    import Tkinter as tk
    import tkMessageBox as MessageBox
    import tkFileDialog as FileDialog

class tkSidViewer():
    '''
    Create the Tkinter GUI
    '''
    def __init__(self, controller):
        """SuperSID Viewer using Tkinter GUI for standalone and client.
        Creation of the Frame with menu and graph display using matplotlib
        """
        matplotlib.use('TkAgg')
        self.version = "1.4 20150801 (tk)"
        self.controller = controller  # previously referred as 'parent'
        self.tk_root = tk.Tk()
        self.tk_root.title("supersid @ " + self.controller.config['site_name'])

        # All Menus creation
        menubar = tk.Menu(self.tk_root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Save Raw buffers", command=lambda: self.save_file('r'),underline=5,accelerator="Ctrl+R")
        filemenu.add_command(label="Save Filtered buffers", command=lambda: self.save_file('f'),underline=5,accelerator="Ctrl+F")
        filemenu.add_command(label="Save Extended raw buffers", command=lambda: self.save_file('e'),underline=5,accelerator="Ctrl+E")
        filemenu.add_command(label="Save filtered as ...", command=lambda: self.save_file('s'),underline=5,accelerator="Ctrl+S")
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=lambda : self.close(force_close=False)) # ,underline=1,accelerator="Ctrl+X")
        self.tk_root.bind_all("<Control-r>", self.save_file)
        self.tk_root.bind_all("<Control-f>", self.save_file)
        self.tk_root.bind_all("<Control-e>", self.save_file)
        self.tk_root.bind_all("<Control-s>", self.save_file)
        self.tk_root.protocol("WM_DELETE_WINDOW", lambda : self.close(False))  # user click on the [X] to close the window
        menubar.add_cascade(label="File", menu=filemenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About...", command=self.on_about)
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.tk_root.config(menu=menubar)

        # FigureCanvas
        self.psd_figure = Figure(facecolor='beige')
        self.canvas = FigureCanvas(self.psd_figure, master=self.tk_root)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.toolbar = NavigationToolbar2TkAgg( self.canvas, self.tk_root)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.axes = self.psd_figure.add_subplot(111)
        self.axes.hold(False)

        # StatusBar
        self.statusbar_txt = tk.StringVar()
        self.label=tk.Label(self.tk_root, bd=1, relief=tk.SUNKEN, anchor=tk.W,
                           textvariable=self.statusbar_txt,
                           font=('arial',12,'normal'))
        self.statusbar_txt.set('Initialization...')
        self.label.pack(fill=tk.X)

    def run(self):
        self.need_refresh = False
        self.refresh_psd() # start the re-draw loop
        self.tk_root.mainloop()

    def close(self, force_close=True):
        if not force_close and MessageBox.askyesno("Confirm exit", "Are you sure you want to exit SuperSID?"):
            self.tk_root.quit()

    def status_display(self, message, level=0, field=0):
        """update the main frame by changing the message in status bar"""
        #print(message)
        self.statusbar_txt.set(message)

    def get_psd(self, data, NFFT, FS):
        """By calling 'psd' within axes, it both calculates and plots the spectrum"""
        try:
            Pxx, freqs = self.axes.psd(data, NFFT = NFFT, Fs = FS)
            self.need_refresh = True
        except RuntimeError as err_re:
            print("Warning:", err_re)
            Pxx, freqs = None, None
        return Pxx, freqs

    def refresh_psd(self, z=None):
        """redraw the graphic PSD plot if needed i.e.new data have been given to get_psd"""
        if self.need_refresh:
            try:
                self.canvas.draw()
                self.need_refresh = False
            except IndexError as err_idx:
                print("Warning:", err_idx)
        self.tk_root.after(2000, self.refresh_psd)

    def save_file(self, param=None):
        """Save the files as per user's menu choice"""
        param = param if isinstance(param, str) else param.keysym # which is the letter with the CTRL-
        if param == 'r':
            saved_files = self.controller.save_current_buffers(log_type='raw', log_format = 'both')
        elif param == 'f':
            saved_files = self.controller.save_current_buffers(log_type='filtered', log_format = 'both')
        elif param == 'e':
            saved_files = self.controller.save_current_buffers(log_type='raw', log_format = 'supersid_extended')
        elif param == 's':
            filename = self.AskSaveasFilename()
            if filename:
                saved_files = self.controller.save_current_buffers(filename, log_type='filtered', log_format = 'supersid')
        MessageBox.showinfo("SuperSID files saved", "\n".join(saved_files))

    def on_about(self):
        """About message box display"""
        MessageBox.showinfo("SuperSID", self.controller.about_app())

    def AskSaveasFilename(self, title='Save File', filetypes=None, initialfile=''):
        """return a string containing file name (the calling routine will need to open the file)"""
        if filetypes==None:
            filetypes = [
                ('CSV File','*.csv'),
                ('Any File','*.*')]
        fileName = FileDialog.asksaveasfilename(parent=self.tk_root, filetypes=filetypes, initialfile=initialfile ,title=title)
        return fileName