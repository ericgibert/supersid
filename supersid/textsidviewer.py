""" textsidviewer.py

Minimal output for SuperSID in text mode i.e. within terminal window.
Useful for Server mode
"""
from __future__ import print_function   # use the new Python 3 'print' function
import sys
from threading import Timer
from _getch import _Getch

class textSidViewer:
    def __init__(self, controller):
        self.version = "1.3.1 20130803"
        print ("SuperSID initialization")
        self.controller = controller
        self.getch = _Getch()
        self.MAXLINE = 70
        self.print_menu()
        self.timer = Timer(0.5, self.check_keyboard)
        self.timer.start()
        
        
    def status_display(self, msg, level = 0):
        print (("\r" + msg + " "*self.MAXLINE)[:self.MAXLINE],  end='')
        sys.stdout.flush()
        
    def clear(self):
        pass
    
    def close(self):
        self.timer.cancel()
    
    def print_menu(self):
        print ("\n" + "-" * self.MAXLINE)
        print ("Site:", self.controller.config['site_name'], " " * 20, end='')
        print ("Monitor:", self.controller.config['monitor_id'])
        print ("-" * self.MAXLINE)
        print (" F) save Filtered buffers")
        print (" R) save Raw buffers")
        print (" E) save Extended raw buffers")
        print ("-" * self.MAXLINE)
        print (" C) list the Config file(s) parameters")
        print (" V) Version")
        print (" ?) display this menu")
        print (" X) eXit (without saving)")
        print ("-" * self.MAXLINE)
        
    def check_keyboard(self):
        s = self.getch().lower()
        if s == 'x':
            self.controller.close()
        elif s in ('f', 'r', 'e'):
            print ("\n\n")
            for fname in self.controller.save_current_buffers(log_type = 'filtered' if s=='f' else 'raw', 
                                                              log_format = 'both_extended' if s == 'e' else 'both'):
                print (fname, "saved")
            self.print_menu()
        elif s == '?':
            self.print_menu()
        elif s == 'c':
            print ("\nConfig file(s):", self.controller.config.filenames)
            for key in sorted(self.controller.config.keys()):
                print ("\t%s = %s" % (key, str(self.controller.config[key])))
            print ("Stations:", self.controller.config.stations)
        elif s == 'v':
            print ("\n")
            try:
                print ("Controller:", self.controller.version)
                print ("Sampler:", self.controller.sampler.version)
                print ("Timer:", self.controller.timer.version)
                print ("Config:", self.controller.config.version)
                print ("Logger:",self.controller.logger.version)
                print ("Sidfile:",self.controller.logger.sid_file.version)
                print ("Text viewer:", self.version)
            except AttributeError:
                print ("Version not found")
        else:
            sys.stdout.write('\a')  # terminal bell
        # call myself again in half a second to check if a new key has been pressed
        if s != 'x':
            self.timer = Timer(0.5, self.check_keyboard)
            self.timer.start()
        
        