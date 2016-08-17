#!/usr/bin/env python3

import sys
import time as t

import midi
import spidev

class Spi:
    '''This class introduces support for 'with' use.
    Spi handles setup, data rate; indicates device open and closed.
    Usage is as follows:
    
    with Spi(device, devtype) as devname:
        #talk to devname
    
    Raspberry Pi supports devices 0 and 1, and supported device types are
    'input', corresponding to SN74HC165, and 'output' (SN74HC595).
    '''
    def __init__(self, device=0, devtype='output'):
        self.spi = spidev.SpiDev()
        self.devnum = device
        self.devtype = devtype
    
    def __enter__(self):
        self.spi.open(0, self.devnum)
        self.spi.max_speed_hz = int(50000)
        print("SPI {} opened.".format(self.dev))
        if self.devtype = 'input':
            self.spi.cshigh = True
        
        return self.spi
    
    def __exit__(self, type, value, traceback):
        self.spi.close()
        print("SPI {} closed.".format(self.dev))
    
def playfile(midifile):
    '''This method interprets a MIDI file and plays it on the organ.
    Default tempo is 120 bpm, valid range is from 24 to 88. Notes out of range
    are warned on the console and transposed into range.
    Obviously, dynamics are not maintained.
    '''
    #convert file to absolute time
    pattern = midi.read_midifile(midifile)
    #absolute tick counts allow global sorting by time
    pattern.make_ticks_abs()
    
    #combine all parts
    single_track = midi.Track()
    single_track.extend([event for track in pattern for event in track])
    
    #aforementioned global sort
    single_track.sort(key=lambda event: event.tick)
    
    #reorganize as notes on at x time in microseconds
    notes_on = []
    scroll_dict = {}
    uspb = 50000    #microseconds per beat, default (120 bpm)
    tpb = pattern.resolution
    running_tick = 0
    running_time = 0
    for event in single_track:
        #set tempo for section
        if isinstance(event, midi.SetTempoEvent):
            uspb = 0
            #convert from decimal equivalent of hex pairs
            for i, val in enumerate(event.data):
                uspb += val * 256**(2-i)
            uspt = int(uspb/tpb)
    
        #add/remove notes at given time
        elif isinstance(event, midi.NoteOnEvent):
            event.tick -= running_tick
            running_tick += event.tick
            running_time += event.tick*uspt
    
            #convert from MIDI pitch to solenoid number
            note_id = event.data[0] - 24
            if 0 <= note_id < 64:
                pass
            else:
                tpos = 0
                while note_id < 0:
                    note_id += 12
                    tpos += 1
                while note_id >= 64:
                    note_id -= 12
                    tpos -= 1
                print("Note transposed by {} octaves".format(tpos))
    
            if 128 > event.data[1] > 0:
                #allow duplicates to prevent premature note cancellation
                notes_on.append(note_id)
    
            elif event.data[1] == 0:
                if note_id in notes_on:
                    notes_on.remove(note_id)
                else:
                    print(
                        "Error! Note {} not found at time {}".format(
                            note_id,
                            running_time))
            #convert ticks to microseconds, eliminates duplicate notes
            scroll_dict[running_time] = tuple(set(notes_on))
    
    #assemble 'piano roll' in preparation for output to horns
    scroll = []
    running_time = 0
    for time in sorted(scroll_dict.keys()):
        #reset all registers
        registers = [0] * 8
    
        #set active notes
        for note in scroll_dict[time]:
            reg_num = note // 8
            reg_bit = note % 8
            registers[reg_num] += 2**reg_bit
    
        #convert back to relative time
        time -= running_time
        running_time += time
    
        scroll.append([time, registers[:]])
    
    #play scroll
    with Spi(0) as spi:
        for time, registers in scroll:
            t.sleep(time*1E-6)
            spi.xfer2(registers)

def live_play_test():
    with Spi(1, 'input') as inspi, Spi(0) as out:
        invals = [0] * 8
        while True:
            inspi.xfer2([0])
            invals = out.xfer2(invals)
            print(invals)

if __name__ == "__main__":
    midifile = sys.argv[1]
    print("Playing...")
    playfile(midifile)
    print("Done!")
