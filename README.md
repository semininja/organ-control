# organ-control
a python script for interpreting MIDI files for output from a Raspberry Pi to the solenoid controllers for an air-horn organ  
the master branch uses relative time in the scroll, and therefore times output using time since last update

The 8 output boards are each comprised of one SN74HC595N and one ULN2803APG, and each board can output to 8 solenoids. The input boards use 8 SN74HC165 with 2 inputs per channel for a total of 64 pairs of inputs. The current iteration is scripted with a built-in range of 64 chromatic notes starting at MIDI pitch 24. The PCB design can be found [here](https://oshpark.com/shared_projects/iThMdQEp). This project requires [py-spidev](https://github.com/doceme/py-spidev) and [python-midi](https://github.com/vishnubob/python-midi/tree/feature/python3).

The project blog can be found [here](https://diwhyorgan.hedler.info).
