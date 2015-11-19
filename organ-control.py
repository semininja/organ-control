#!/usr/bin/env python3

import sys
import time as t

import midi
import spidev

def import_single(mid):
    """Import file; return resolution, list of all events ordered by time."""
    pattern = midi.read_midifile(mid)
    pattern.make_ticks_abs()
    combined = midi.Track()
    for track in pattern:
        for event in track:
            combined.append(event)

    combined.sort(key=lambda note: note.tick)
    tpb = pattern.resolution

    return(tpb, combined)

def time_convert(pairs, tpb):
    """Convert from decimal form of hex pairs."""
    uspb = 0
    for i, val in enumerate(pairs):
        uspb += val * 256**(2-i)
    uspt = int(uspb/tpb)

    return uspt

def scroll_prep(tpb, combined):
    """Restructure combined midi events into 'piano roll' format.

    The input list of midi events is converted to track the notes active at each
    keyframe. Keyframes are given a time code in microseconds since start and
    are generated at each time that a NoteOnEvent occurs
    """
    notes_on = []
    scroll_dict = {}
    uspb = 50000    #microseconds per beat, default (120 bpm)
    running_tick = 0
    running_time = 0
    for event in combined:
        #set tempo for section
        if isinstance(event, midi.SetTempoEvent):
            uspt = time_convert(event.data, tpb)

        #add/remove notes at given time
        elif isinstance(event, midi.NoteEvent):
            event.tick -= running_tick
            running_tick += event.tick
            running_time += event.tick*uspt

            #convert from MIDI pitch to solenoid number
            note_id = event.data[0] - 24

            if 128 > event.data[1] > 0:
                #allow duplicates to prevent premature note cancellation
                notes_on.append(note_id)

            elif event.data[1] == 0:
                if note_id in notes_on:
                    notes_on.remove(note_id)
                else:
                    print(
                        "Error! Note {0} not found at time {1}".format(
                            note_id,
                            running_time))
            #convert ticks to microseconds, eliminates duplicate notes
            scroll_dict[running_time] = tuple(set(notes_on))

    return(scroll_dict)

def scroll_write(scroll_dict):
    """assemble 'piano roll' in preparation for output to horns"""
    scroll = []
    registers = list(range(8))
    running_time = 0
    for time in sorted(scroll_dict.keys()):
        #reset all registers
        for i in range(8):
            registers[i] = 0b0

        #set active notes
        for note in scroll_dict[time]:
            reg_num = note // 8
            reg_bit = note % 8
            registers[reg_num] += 2**reg_bit

        #convert back to relative time
        time -= running_time
        running_time += time

        scroll.append([time, registers[:]])

    return(scroll)

def play(scroll):
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = int(5E6)
    for time, registers in scroll:
        t.sleep(time*1E-6)
        spi.xfer2(registers)

    spi.close()

if __name__ == "__main__":
    mid = sys.argv[1]
    tpb, combined = import_single(mid)
    play(scroll_write(scroll_prep(tpb, combined)))
