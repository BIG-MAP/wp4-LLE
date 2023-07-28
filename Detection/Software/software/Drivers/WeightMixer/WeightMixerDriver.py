import serial
import time
import os

if os.name == 'nt':
    comPort = "COM9"#COM depends on computer, only for debugging 
else:
    comPort = '/dev/ttyUSB0'


weightMixer = serial.Serial(port=comPort, baudrate=9600, timeout=10, parity=serial.PARITY_EVEN, xonxoff=False)
time.sleep(1)

def get_Name() -> int:

    weightMixer.write(bytes('IN_NAME \r \n', 'utf-8'))

    getData= weightMixer.readline()
    data = getData.decode('utf-8').rstrip()
    print(data) 

    return 0


def set_Speed(speed: int) -> int:

    weightMixer.write(bytes('OUT_SP_4 '+str(speed)+' \r \n', 'utf-8'))
    print('Setting speed to '+str(speed))

    return 0

def get_Speed() -> int:

    weightMixer.write(bytes('IN_PV_4 \r \n', 'utf-8'))

    getData= weightMixer.readline()
    data = getData.decode('utf-8').rstrip()
    print(data)
    speed = data[0:data.find(" ")]

    return speed

def get_Speed_Set_Point() -> int:

    weightMixer.write(bytes('IN_SP_4 \r \n', 'utf-8'))

    getData= weightMixer.readline()
    data = getData.decode('utf-8').rstrip()
    print(data)
    speed = data[0:data.find(" ")]

    return speed

def get_Viscosity_Trend() -> int:

    weightMixer.write(bytes('IN_PV_5 \r \n', 'utf-8'))

    getData= weightMixer.readline()
    data = getData.decode('utf-8').rstrip()
    print(data)
    viscosity = data[0:data.find(" ")]

    return viscosity

def start_Mixer() -> int:

    weightMixer.write(bytes('START_4 \r \n', 'utf-8'))
    print('Starting Mixer')

    return 0

def stop_Mixer() -> int:

    weightMixer.write(bytes('STOP_4 \r \n', 'utf-8'))
    print('Stopping Mixer')

    return 0

def reset() -> int:

    weightMixer.write(bytes('RESET \r \n', 'utf-8'))
    print('Resetting Mixer...')
    time.sleep(30)

    return 0


def start_Weight() -> int:

    weightMixer.write(bytes('START_90 \r \n', 'utf-8'))
    print('Starting Weight')

    return 0

def stop_Weight() -> int:

    weightMixer.write(bytes('STOP_90 \r \n', 'utf-8'))
    print('Stopping Weight')

    return 0

def get_Weight_Value() -> int:

    weightMixer.write(bytes('IN_PV_90 \r \n', 'utf-8'))

    getData= weightMixer.readline()
    data = getData.decode('utf-8').rstrip()
    print(data)
    weight = data[0:data.find(" ")]

    return weight

def get_Weight_Status() -> int:
    tare = False
    scale_on = False
    scale_stable = False
    scale_overload = False
    scale_power_on = False

    weightMixer.write(bytes('STATUS_90 \r \n', 'utf-8'))

    getData= weightMixer.readline()
    data = getData.decode('utf-8').rstrip()
    print(data)
    value = data[0:data.find(" ")]
    value = int(value)
    print(bin(value))
    
    if value & 0b1:
        print("Scale stable")
        scale_stable = True
    else:
        print("Scale not stable")

    if value & 0b1000:
        print("Tare completed")
        tare = True
    else:
        print("Tare not completed")

    if value & 0b10000:
        print("Scale on")
        scale_on = True
    else:
        print("Scale not on")

    if value & 0b1000000000:
        print("Scale overload")
        scale_overload = True

    if value & 0b10000000000:
        print("Scale power on")
        scale_power_on = True

    return tare,scale_on,scale_stable,scale_power_on,scale_overload

# get_Name()
# time.sleep(2)
# set_Speed(100)
# time.sleep(2)
# start_Mixer()
# time.sleep(2)
# set_Speed(100)
# time.sleep(10)
# set_Speed(400)
# get_Speed()
# time.sleep(10)
# get_Speed()
# time.sleep(5)
# stop_Mixer()
# time.sleep(5)

# start_Weigh()
# #stop_Weigh()
# time.sleep(20)
# tare,scale_on,scale_stable,scale_power_on,scale_overload=get_Weigh_Status()
# while not ((tare or scale_stable) and scale_on):
#     time.sleep(1)
#     print("Not ready to weigh")
#     tare,scale_on,scale_stable,scale_power_on,scale_overload=get_Weigh_Status()
# get_Weigh_Value()
# time.sleep(10)
# tare,scale_on,scale_stable,scale_power_on,scale_overload=get_Weigh_Status()
# while not ((tare or scale_stable) and scale_on):
#     time.sleep(1)
#     print("Not ready to weigh")
#     tare,scale_on,scale_stable,scale_power_on,scale_overload=get_Weigh_Status()
# get_Weigh_Value()
# stop_Weigh()
