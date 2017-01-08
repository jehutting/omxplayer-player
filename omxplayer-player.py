#!/usr/bin/env python

#
#      Copyright (C) 2016-2017 Jozef Hutting <jehutting@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import sys
import os
import subprocess
import logging
import threading
import time
import RPi.GPIO as GPIO
import glob

from keyb import KBHit

__author__ = 'Jozef Hutting'
__copyright__ = 'Copyright (C) 2016-2017 Jozef Hutting <jehutting@gmail.com>'
__license__ = 'GPLv2'
__version__ = '0.10'

USAGE = (
"usage:\n"
"    python omxplayer-player DIRECTORY [FILE_EXTENSION]\n"
"where\n"
"    DIRECTORY is the directory (/folder) containing the files to play.\n"
"    FILE_EXTENSION is optional and defaulted to 'mp3.'\n"
"\nFor more info, see https://github.com/jehutting/omxplayer-player\n"
"Version "+__version__  
)

# the REAL OMXPlayer
OMXPLAYER = 'omxplayer'
# REAL OMXPLAYER options
OMXPLAYER_ARGS = [
     #'--display=4',  # Raspberry Pi touchscreen
     #'--alsa', # ALSA device (USB Audio dongle)
     '--no-osd' # Do not display status information on screen
    ]


class EventHook(object):

    '''http://stackoverflow.com/questions/1092531/event-system-in-python'''

    def __init__(self):
        self.__handlers = []

    def __iadd__(self, handler):
        self.__handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.__handlers.remove(handler)
        return self

    def fire(self, *args, **keywargs):
        for handler in self.__handlers:
            handler(*args, **keywargs)

    def clearObjectHandlers(self, inObject):
        for theHandler in self.__handlers:
            if theHandler.im_self == inObject:
                self -= theHandler


class OMXPlayer:

    '''
    Note: this python wrapper to control OMXPlayer is a very simple implementation.
    If you want a more (on the edge) control over OMXPlayer, I suggest to use 
    Will Price OMXPlayer wrapper (https://github.com/willprice/python-omxplayer-wrapper).
    '''

    process = None
    running = False
    completed = False
    playback_status = "Stopped"

    def __init__(self):
        self.logger = logging.getLogger('__OMXPlayer__')
        self.onCompleted = EventHook()

    def log(self, args):
        self.logger.debug('{0}'.format(args))

    def log_error(self, args):
        self.logger.error('{0}'.format(args))

    def play(self, filename):

        def run_in_thread():

            command = [OMXPLAYER]
            command.extend(OMXPLAYER_ARGS)  # default arguments
            command.append(filename)
            self.log('Full command={0}'.format(command))
            with open(os.devnull, 'w') as devnull:
                self.process = subprocess.Popen(command,
                                                stdin=subprocess.PIPE,
                                                stdout=devnull,
                                                stderr=devnull,
                                                bufsize=0)

            # wait for REAL OMXPlayer process is running
            while self.process.poll() is not None:
                time.sleep(0.01) # seconds
                self.log('#')
            self.log('process PID={0}'.format(self.process.pid))
            self.running = True

            self.process.wait()

            self.log('REAL OMXPlayer exit status/return code : {0}'
                     .format(self.process.returncode))
            self.completed = True
            self.playback_status = "Stopped"
            # onCompleted only when NOT quited
            if self.running:
                self.onCompleted.fire()
            return

        if not os.path.isfile(filename):
             self.log_error('Error: File "{0}" not found!'.format(filename))
             raise IOError(filename)

        self.thread = threading.Thread(target=run_in_thread, args=())
        self.thread.start()
        self.log('Waiting for running REAL OMXPlayer...') 
        while(not self.running):
            continue;
        self.log('REAL OMXPlayer is up and running!')
        self.playback_status = "Playing"

    def quit(self):
        p = self.process
        if (p is not None):
            if not (self.playback_status == "Stopped"):
                try:
                    self.log('Quitting REAL OMXPlayer...')
                    self.__key(b'q')  # send quit command           
                    self.running = False
                    # wait for process termination 
                    self.thread.join() 
                except:
                    self.log_error('Error upon quitting REAL OMXPlayer: {0}'
                                   .format(sys.exc_info()[0]))

    def pause(self):
        if self.running:
            self.log('Pause REAL OMXPlayer')
            self.__key(b' ') # SPACE character to pause
            self.playback_status = "Paused"

    def resume(self):
        if self.running:
            self.log('Resume REAL OMXPlayer')
            self.__key(b' ') # SPACE character to unpause
            self.playback_status = "Playing"

    def __key(self, value):
        if self.running:
            try:
                self.process.stdin.write(value)
                self.log("Key b'{0}' sent successfully".format(value))
            except:
                self.log_error('Error on sending key to REAL OMXPlayer: {0}'
                               .format(sys.exc_info()[0]))


class Button():

    def __init__(self, name, bcm_port_number, call_back):
        self.logger = logging.getLogger('__Button__')
        self.name = name
        self.bcm_port_number = bcm_port_number
        self.onChanged = EventHook()
        self.onChanged += call_back
        GPIO.setup(self.bcm_port_number, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(self.bcm_port_number, GPIO.BOTH, callback=self.__edge_callback
                              )#, bouncetime=1)
        self.state = self.__get_state(self.bcm_port_number)
        self.log('initial state={0}'.format(self.state))

    def __get_state(self, gpio):
        return GPIO.input(gpio)

    def log(self, args):
        self.logger.debug('{0}: {1}'.format(self.name, args))

    def __edge_callback(self, channel):
        state = self.__get_state(self.bcm_port_number)
        self.log('Edge detected {0}=>{1}'.format(self.state, state))
        # Hmmm...sometimes I get 0=0 and 1=>1 edges!?
        # I ONLY want the real edges!
        if state != self.state:
            if state == 1: # edge 0=>1
                self.log('pressed!')
                self.onChanged.fire(1)
            else: # edge 1=>0
                self.log('released!')
                self.onChanged.fire(0)
            self.state = state


class Led():

    state = None

    def __init__(self, name, bcm_port_number):
        self.logger = logging.getLogger('__Led__')
        self.name = name
        self.bcm_port_number = bcm_port_number
        GPIO.setup(self.bcm_port_number, GPIO.OUT)
        self.off()

    def log(self, args):
        self.logger.debug('{0}: {1}'.format(self.name, args))

    def on(self):
         self.log('on')
         self.__stop_blinking()
         self.__on()
         self.state = "on"

    def __on(self):
         GPIO.output(self.bcm_port_number, 1)

    def off(self):
         self.log('off')
         self.__stop_blinking()
         self.__off()
         self.state = "off"

    def __off(self):
         GPIO.output(self.bcm_port_number, 0)

    def blink(self):
         self.log('blink')
         self.blink_time = 0.2 # seconds
         self.e = threading.Event()
         self.t = threading.Thread(name=self.name, target=self.__blinking, args=(self.e, self.blink_time))
         self.t.start()
         self.state = "blinking"

    def __stop_blinking(self):
        if self.state == "blinking":
            self.log('stop blinking')
            self.e.set()
            self.t.join()

    def __blinking(self, e, t):
        """http://raspberrypi.stackexchange.com/questions/28984/how-to-blink-leds-on-off-continually-while-continuing-execution-of-a-script"""
        self.log('blinking started')
        toggle = 1
        while not e.isSet():
            if toggle:
                self.__on()
                toggle = 0
            else:
                self.__off()
                toggle = 1
            event_is_set = e.wait(t)
            #if event_is_set:
            #    self.log('stop led from blinking')


class Player():

    omxplayer = None

    def __init__(self):
        self.logger = logging.getLogger('__Main__')

    def log(self, args):
        self.logger.debug('{0}'.format(args))

    def log_error(self, args):
        self.logger.error('{0}'.format(args))

    def __incr_index(self):
        self.index += 1
        if self.index >= len(self.files):
            self.index = 0

    def __decr_index(self):
        self.index -= 1
        if self.index < 0:
            self.index = len(self.files)-1

    def __onOmxplayerCompleted(self):
        self.log('onCompleted')
        self.__incr_index()
        self.play()

    def __onPlayButtonChanged(self, pressed):
        self.log('onPlayButtonChanged {0}'.format(pressed))
        if pressed:
            if self.omxplayer.playback_status == "Playing":
                self.omxplayer.pause()
                self.ledPlay.blink()
            else:
                self.omxplayer.resume()
                self.ledPlay.on()
     
    def __onPreviousButtonChanged(self, pressed):
        self.log('onPreviousButtonChanged {0}'.format(pressed))
        if pressed:
            self.omxplayer.quit()
            self.__decr_index()
            self.play()

    def __onNextButtonChanged(self, pressed):
        self.log('onNextButtonChanged {0}'.format(pressed))
        if pressed:
            self.omxplayer.quit()
            self.__incr_index()
            self.play()

    def play(self):
        filename = files[self.index]
        self.omxplayer.play(filename)
        index = self.index
        self.ledPlay.on()

    def run(self, files):
        self.files = files
        self.index = 0

        self.omxplayer = OMXPlayer()

        # -----H A R D W A R E   d e f i n i t i o n ---------------------------
        btnPlay = Button("Play", 25, self.__onPlayButtonChanged) # GPIO header pin 22
        btnPrevious = Button("Previous", 23, self.__onPreviousButtonChanged) # GPIO header pin 16
        btnNext = Button("Next", 24, self.__onNextButtonChanged) # GPIO header pin 18
        self.ledPlay = Led("Play", 22) # GPIO header pin 15
        # ----------------------------------------------------------------------

        return_code = 0 # OK

        try:    

            self.omxplayer.onCompleted += self.__onOmxplayerCompleted
            self.play()

            # KEYBOARD control
            kb = KBHit()
            while True:
                if kb.kbhit():
                    c = kb.getch()
                    #print(c)
                    if c == chr(27): # ESC key to quit
                        self.log('ESC key pressed')
                        break
                    elif c == 'q': # <== and this one too to quit
                        self.log('Quit key pressed')
                        break
                    elif c == ' ': # <== SPACE key for Play/Pause
                        self.log('SPACE key pressed')
                        self.__onPlayButtonChanged(1)
                    elif c == 'p': # <== PREVIOUS key
                        self.log('PREVIOUS key pressed')
                        self.__onPreviousButtonChanged(1)
                    elif c == 'n': # <== NEXT key
                        self.log('NEXT key pressed')
                        self.__onNextButtonChanged(1)               
                time.sleep(1)

        except KeyboardInterrupt:
            """http://stackoverflow.com/questions/19807134/python-sub-process-ctrlc"""
            self.log('KeyboardInterrupt')

        self.omxplayer.quit()
        print('EXIT')
        return return_code


if __name__ == '__main__':

    if len(sys.argv) == 1:
        print(sys.argv[0]+': missing directory operand.')
        print(USAGE)
        sys.exit(-1)

    logging.basicConfig(level=logging.DEBUG)

    dirname = sys.argv[1]
    print('dirname="{0}"'.format(dirname))

    pattern = '*.mp3'
    if len(sys.argv) > 2:
       pattern = '*.' + sys.argv[2]
    print('pattern="{0}"'.format(pattern))

    # directory must exist
    if not os.path.isdir(dirname):
        print('Error: Folder "{0}" not found!'.format(dirname))
        sys.exit(-2)

    files = glob.glob(os.path.join(dirname, pattern))
    files = sorted(files) # sort in alphabetical order
    print(files)

    # need some files to play with
    if len(files) == 0:
        print(sys.argv[0]+": no files found on '"+dirname+"' matching pattern '"+pattern+"'.")
        sys.exit(-3)

    # let's roll... 
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        player = Player();
        return_code = player.run(files);
    finally:
        GPIO.cleanup()
 
    sys.exit(return_code);
