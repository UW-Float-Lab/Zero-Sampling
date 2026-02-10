#!/usr/bin/env python3
"""
This program gathers the frequency of the conductivity cell
through the use of the 'TCR' command in the CTD gateway. The program automatically
generates a file, and uploads it to the float directory.
to use the program, type in the following command:
python zero_sampling.py -c [calibrated 0 frequency from seabird]
"""
import serial
import numpy as np
import time
import os
import sys

from optparse import OptionParser
import datetime
import shutil
def zero_sampling(ser_float,zero_constant):
    #wakes up float and clears any wake up characters
    for i in range(4):
        ser_float.write(b'n\r')
        time.sleep(1)
    ser_float.reset_input_buffer()
    time.sleep(1)

    #gathers float APF ID
    ser_float.write(b'n\r')     
    time.sleep(1)
    output = ser_float.read_all().decode("utf-8").split()
    if 'number:' in output:
        index = output.index('number:')
        float_num = int(output[index+1])
        print('APF ID: {}'.format(float_num))
    else:
        print('could not detect a float')
        sys.exit()
    ser_float.reset_input_buffer()
    time.sleep(1)

    #gathers float CTD serial number
    ser_float.write(b's\r')
    time.sleep(1)
    ser_float.write(b'n\r')
    time.sleep(10)
    output = ser_float.read_all().decode("utf-8").split()
    if 'number:' in output:
        index = output.index('number:')
        ctd_num = int(output[index+1])
        print('CTD#: {}'.format(ctd_num))
    else:
        print('could not get CTD #')
        sys.exit()    

    #Opens a file to write to
    num_trials = 104
    data = np.zeros(num_trials)
    file_path = (str(ctd_num) + "_zero_frequency.log")
    with open(file_path, 'w') as file:
        file.write('Float APFID: ' + str(float_num) + '\n')
        file.write('CTD Serial Number: ' + str(ctd_num) + '\n')
        file.write('\n')
        ser_float.reset_input_buffer()    
        time.sleep(0.5)

        #enter CTD gateway
        ser_float.write(b's')
        time.sleep(0.5)
        ser_float.write(b'g\r')
        time.sleep(5)
        output = ser_float.read_all().decode("utf-8")
        if '<ESC>' not in output:
            print('could not enter CTD gateway')
            sys.exit()
        else:
            print('Successfully entered CTD gateway')
            print()
        ser_float.reset_input_buffer()    
        ser_float.write(b'\r')
        time.sleep(1)
        ser_float.reset_input_buffer() 
        time.sleep(1)

        #TCR command samples frequency in the conductivity cell
        ser_float.write(b'tcr\r')
        try:
            count = 0
            for i in range(num_trials):
                out = ser_float.readline().decode("utf-8").strip()
                try:
                    value = float(out)
                except ValueError:
                    continue
                n = datetime.datetime.now()
                time_val = '%s ' % n.strftime("%Y-%m-%d-%H:%M:%S:")
                count += 1
                data[i] = value
                if i >2:
                    line = time_val + str(value)
                    file.write(line + '\n')
                    print(line)
            print()
            file.write('\n')
            data = data[:count] 
        except KeyboardInterrupt:
            data = data[:count] 
            print()
            file.write('\n')
        ser_float.write(b'\x1B')
        time.sleep(5)
        data = data[3:]

        print('-----------RESULTS-----------')
        print('Given zero calibration: ' + str(zero_constant))
        print()
        print('Average: ' + str(np.average(data)))
        print('Standard Deviation: ' + str(np.std(data)))
        print('Minimum: ' + str(np.min(data)))
        print('Maximum: ' + str(np.max(data)))

        file.write('-----------RESULTS-----------\n')
        file.write('Given zero calibration: ' + str(zero_constant) + '\n')
        file.write('\n')
        file.write('Average: ' + str(np.average(data)) + '\n')
        file.write('Standard Deviation: ' + str(np.std(data)) + '\n')
        file.write('Minimum: ' + str(np.min(data)) + '\n')
        file.write('Maximum: ' + str(np.max(data)) + '\n')

        ser_float.write(b'i')
        time.sleep(1)
        ser_float.write(b'f')
        time.sleep(1)
        ser_float.write(b'y')

    zero_frequency_destination_files = (f"/net/alace/{float_num}/{file_path}")
    directory_name = (f"/net/alace/{float_num}")
    try:
        os.mkdir(directory_name)
    except FileExistsError:
        hi = 'hi'      
    shutil.copyfile(file_path, zero_frequency_destination_files)

if __name__ == "__main__":
    ser_float = serial.Serial(port = '/dev/com1', baudrate = 9600, bytesize = 8, parity = 'N', stopbits=1,timeout=(5),xonxoff = True)
    parser = OptionParser()
    parser.add_option('-c','--cal_constant',type="float",dest="constant",help="Calibration zero-constant value")
    (options, args) = parser.parse_args()
    zero_constant = options.constant
    zero_sampling(ser_float,zero_constant)
