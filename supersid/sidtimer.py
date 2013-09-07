#!/usr/bin/python
"""Class SidTimer
    Define a timer with auto-correction to ensure that data acquisition is done
    on the 'interval' and as accurately as possible.
    The auto-correction compensates for the micro-seconds lost from one tick to the next.
    Implemenation examples are provided at the source's end, which can be used to test the module/class.
"""
from __future__ import print_function   # use the new Python 3 'print' function
import time
from datetime import datetime 
import threading

class SidTimer():
    def __init__(self, interval, callback):
        """Synchronize the timer and start the trigger mechanism.
            Public properties:
            - start_time: reference startig time.time() in local time *on the interval* (synchro)
            - expected_time: theoritical time the trigger should happen as 'start_time + X * interval'
            - time_now: real time.time() when the trigger happened
        """
        self.version = "1.3.1 20130907"
        self.callback = callback
        self.interval = interval
        self.lock = threading.Lock()
        # wait for synchro on the next 'interval' sec
        now = time.gmtime() 
        while now.tm_sec % self.interval != 0:
            time.sleep(0.05)
            now = time.gmtime()
        # request a Timer     
        self.start_time = int(time.time() / self.interval) * self.interval
        self.expected_time = self.start_time + self.interval
        self._timer = threading.Timer(self.expected_time - time.time(), self._ontimer)
        self._timer.start()

    def _ontimer(self):
        """Retrigger a timer for the next INTERVAL with adjustment if necessary i.e. running late/fast then perform callback"""
        self.time_now = time.time()
        self.utc_now = datetime.utcnow()
        self._timer = threading.Timer(self.interval + self.expected_time - self.time_now, self._ontimer)
        self._timer.start()
        self.data_index = int((self.utc_now.hour * 3600 + self.utc_now.minute * 60 + self.utc_now.second) / self.interval)
        self.expected_time += self.interval
        # callback to perform tasks
        self.callback()
        
    def stop(self):
        """Cancel the timer currently running in background"""
        self._timer.cancel()
    
    def get_utc_now(self):
        return self.utc_now.strftime("%Y-%m-%d %H:%M:%S.%f")

if __name__ == '__main__':
    TIME_INTERVAL = 5.0 #seconds
    TEST_LENGTH = 3600.0 #seconds

    class test_SidTimer_superclass(SidTimer):
        """Example of SidTimer implementation by extending SidTimer class and inheriting its properties"""
        def __init__(self, interval):
            print ("Waiting for synchro...", end='')
            SidTimer.__init__(self, interval, self.onTimerEvent)
            print ("done.")
            self.max_plus_error, self.max_minus_error = 0, 0


        def onTimerEvent(self):
            """Call back function to do tasks when Timer is tiggered.
                In this test class, only display some tracking on the timer's accuracy
            """
            time_error =  self.expected_time - self.time_now - self.interval
            if time_error > 0 and time_error > self.max_plus_error:
                self.max_plus_error = time_error
            elif time_error < 0 and time_error < self.max_minus_error:
                self.max_minus_error = time_error
            
            print ("Idx", self.data_index, "now:", self.time_now, "expec_time:", self.expected_time - self.interval)
            print (" err:", time_error, "interv: %f" % (self.expected_time - self.time_now))

        def cancel_timer(self):
            self.stop()

    class test_SidTimer_simple():
        """Example of SidTimer implementation using a local variable 'sidtimer' to handle the new SidTimer instance"""
        def __init__(self, interval):
            print ("Waiting for synchro...",end='')
            self.sidtimer = SidTimer(interval, self.onTimerEvent)
            print ("done.")
            self.max_plus_error, self.max_minus_error = 0, 0

        def onTimerEvent(self):
            """Call back function to do tasks when Timer is tiggered.
                In this test class, only display some tracking on the timer's accuracy
            """
            time_error =  self.sidtimer.expected_time - self.sidtimer.time_now - self.sidtimer.interval
            if time_error > 0 and time_error > self.max_plus_error:
                self.max_plus_error = time_error
            elif time_error < 0 and time_error < self.max_minus_error:
                self.max_minus_error = time_error

            print ("Idx", self.sidtimer.data_index, "now:", self.sidtimer.time_now, "expec_time:", self.sidtimer.expected_time - self.sidtimer.interval)
            print (" err:", time_error, "interv: %f" % (self.sidtimer.expected_time - self.sidtimer.time_now))

        def cancel_timer(self):
            self.sidtimer.stop()

    # choose either 'test_SidTimer_simple' or 'test_SidTimer_superclass'. Results will be the same.
    tst = test_SidTimer_simple(TIME_INTERVAL)
    try:
        time.sleep(TEST_LENGTH)  # do nothing while testing the timer's accuracy
    except (KeyboardInterrupt, SystemExit):
        pass

    # let's cleanup and show max errors
    tst.cancel_timer()
    print ("max positive error: ", tst.max_plus_error)
    print ("max negative error: ", tst.max_minus_error)
