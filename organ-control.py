#!/usr/bin/env python3

import midi
import sys
import spidev

'''import and convert file to absolute time'''
midifile = sys.argv[1]
pattern = midi.read_midifile(midifile)
pattern.make_ticks_abs()

'''combine all parts'''
single_track = midi.Track()
for track in pattern:
    for event in track:
        single_track.append(event)

single_track.sort(key=lambda note: note.tick)

'''reorganize as notes on at x time in microseconds'''
notes_on = []
scroll_dict = {}
uspb = 50000 #microseconds per beat, default (120 bpm)
tpb = pattern.resolution
running_tick = 0
running_time = 0
for event in single_track:
    '''set tempo for section'''
    if isinstance(event, midi.SetTempoEvent):
        uspb = 0
        #data is saved in decimal equivalent of hex pairs
        for i, val in enumerate(event.data):
            uspb += val * 256**(2-i)
        uspt = int(uspb/tpb)

    '''add/remove notes at given time'''
    elif isinstance(event, midi.NoteOnEvent):
        event.tick -= running_tick
        running_tick += event.tick
        running_time += event.tick*uspt

        #converts from MIDI pitch to solenoid number
        note_id = event.data[0] - 24

        if 128 > event.data[1] > 0:
            #allows duplicates to prevent premature note cancellation
            notes_on.append((event.data[0]))
        elif event.data[1] == 0:
            if event.data[0] in notes_on:
                notes_on.remove(event.data[0])
            else:
                print(
                    "Error! Note {0} not found at time {1}".format(
                        event.data[0],
                        running_time))
        #converts ticks to microseconds, eliminates duplicate notes
        scroll_dict[running_time] = tuple(set(notes_on))

'''assemble 'piano roll' in preparation for output to horns'''
scroll=[]
print("scroll follows")
for i, time in enumerate(sorted(scroll_dict.keys())):
    scroll.append((time, sorted(scroll_dict[time])))
    print(scroll[i])

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = int(5E6)
#send notes
spi.close()
