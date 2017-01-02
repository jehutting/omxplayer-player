# omxplayer-player

A player controlling omxplayer by gpio (/buttons) or keyboard keys.

## Introduction

This python program has been written as an example to have the [Raspberry pi as mp3 player without LCD](https://www.raspberrypi.org/forums/viewtopic.php?f=63&t=168392).

The program runs on a Raspberry Pi with OS Raspbian Jessie.

It is written in python. Tested with Python version 2 (2.7.9) as well as version 3 (3.4.2).

## Usage

To run the program<br>
&nbsp;&nbsp;&nbsp;&nbsp;python omxplayer-player DIRECTORY [FILE_EXTENSION]<br>
where<br>
&nbsp;&nbsp;&nbsp;&nbsp;FILE_EXTENSION is optional and defaulted 'mp3'.<br> 

To run it under Python3, just replace python with python3.

As OMXPlayer is able to play video, the playing is not only limitted to .mp3 files. 

Currently hardwired 3 buttons (Play, Previous and Next) and 1 LED (Play/Paused).

![Photo of the breadboard setup](https://github.com/jehutting/omxplayer-player/raw/master/image-1.jpg)


The player starts playing the first file on the list.

Pressing the play button pauses the playing. Again pressing the Play button, the playing is resumed.

When the player is playing the LED is on. During the paused state the LED is blinking.

The next button stops the current one being played and the player continuous to play the next one on the list.

The previous button stops the current one being played, and the player continouous with the previous one on the list.

Playing of the files is continuously: when reaching the end of the list, it continuous with the first one.
Therefore the sequence is : first => ... last => first ... etc.
Pressing the previous button when the first file is the current one being played, 
the player continuous the playing of the last file., 

The main target is the controlling of omxplayer by the GPIO. However, it can also be controlled by the keyboard.

The functions:<br>
- SPACE key, the play/pause function<br>
- the 'p' key for the previous function<br>
- the 'n' key for the next function<br>

The program is terminated by the 'ESC' (Escape) or 'q' key.

### Usage Examples

To play all mp3 files in the folder '/home/pi/music':<br>
&nbsp;&nbsp;&nbsp;&nbsp;python omxplayer-player /home/pi/music<br>
(which is equal to<br>
&nbsp;&nbsp;&nbsp;&nbsp;python omxplayer-player /home/pi/music mp3<br>
as .mp3 file_extension is default)

To play all mkv video files in the folder '/home/pi/movies':<br>
&nbsp;&nbsp;&nbsp;&nbsp;python omxplayer-player /home/pi/movies mkv<br>

## Details

### The audio(/video) player OMXPlayer

The playing of the audio/video file is done with OMXPlayer.
OMXPlayer is the standard player on the Raspberry Pi. It is part of the distribution, and therefore it needs not to be installed


### GPIO

The GPIO support is done with python module 'RPi.GPIO'.

Install RPi.GPIO with:<br>
&nbsp;&nbsp;&nbsp;&nbsp;sudo apt-get install python-rpi.gpio
For usage with python3:<br>
&nbsp;&nbsp;&nbsp;&nbsp;sudo apt-get install python3-rpi.gpio

With the following commands you can use the Raspbian Jessie GPIOs without the need to be root (superuser):<br>
&nbsp;&nbsp;&nbsp;&nbsp;sudo groupadd gpio<br>
&nbsp;&nbsp;&nbsp;&nbsp;sudo usermod -aG gpio USERNAME<br>
&nbsp;&nbsp;&nbsp;&nbsp;sudo reboot<br>


### Hardware

Currently there are 3 buttons and 1 led hardwired.

btnPlay => GPIO25 (GPIO header pin 22)<br>
btnPrevious => GPIO23 (GPIO header pin 16)<br>
btnNext => GPIO24 (GPIO header pin 18)<br>
ledPlay => GPIO22 (GPIO header pin 15)<br>


+3.3V (GPIO header pin 3)<br>
GND (GPIO header pin 6)

+3.3V --->---| button |-----> GPIOx

GPIOxx --->-----| Kathode  LED  Anode |----[ resistor 330R ]----> GND



## History
* V0.10 Initial version
