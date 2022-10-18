import serial
import time
import os

if os.name == 'nt':
    comPort = "COM7"
else:
    comPort = '/dev/ttyUSB0'


mixer = serial.Serial(port=comPort, baudrate=9600, timeout=10, parity=serial.PARITY_EVEN, xonxoff=False)
time.sleep(1)


def set_Speed(speed: int) -> int:

    mixer.write(bytes('OUT_SP_4 '+str(speed)+' \r \n', 'utf-8'))
    print('Setting speed to '+str(speed))

    return 0


def get_Name() -> int:

    mixer.write(bytes('IN_NAME \r \n', 'utf-8'))

    getData= mixer.readline()
    data = getData.decode('utf-8').rstrip()
    print(data) 

    return 0


def get_Speed() -> int:

    mixer.write(bytes('IN_PV_4 \r \n', 'utf-8'))

    getData= mixer.readline()
    data = getData.decode('utf-8').rstrip()
    print(data)

    return 0

def get_Speed_Set_Point() -> int:

    mixer.write(bytes('IN_SP_4 \r \n', 'utf-8'))

    getData= mixer.readline()
    data = getData.decode('utf-8').rstrip()
    print(data)

    return 0


def get_Viscosity_Trend() -> int:

    mixer.write(bytes('IN_PV_5 \r \n', 'utf-8'))

    getData= mixer.readline()
    data = getData.decode('utf-8').rstrip()
    print(data)

    return 0


def start() -> int:

    mixer.write(bytes('START_4 \r \n', 'utf-8'))
    print('Starting Mixer')

    return 0


def stop() -> int:

    mixer.write(bytes('STOP_4 \r \n', 'utf-8'))
    print('Stopping Mixer')

    return 0


def reset() -> int:

    mixer.write(bytes('RESET \r \n', 'utf-8'))
    print('Resetting Mixer...')
    time.sleep(30)

    return 0



# get_Name()
# time.sleep(2)
# set_Speed(100)
# time.sleep(2)
# start()
# time.sleep(2)
# set_Speed(100)
# time.sleep(20)
# set_Speed(400)
# get_Speed()
# time.sleep(20)
# get_Speed()
# time.sleep(5)
# stop()



