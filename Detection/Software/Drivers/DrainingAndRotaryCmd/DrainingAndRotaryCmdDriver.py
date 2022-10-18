import PyCmdMessenger
import time
import os
import logging

import sys
import glob
import serial


deviceID = "0,0000000-0000-0000-0000-00000000000;" 


def getAvailableSerialPorts():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

serial_Ports = getAvailableSerialPorts()
print(serial_Ports)

found = False
for port in serial_Ports:
    print(port)
    s = serial.Serial(port=port, baudrate=115200, timeout=2)
    s.write(bytes('0;', 'utf-8'))
    getData= s.read_until(';')
    s.write(bytes('0;', 'utf-8'))
    getData= s.read_until(';')
    data = getData.decode('utf-8').rstrip()
    print(data)
    s.close()
    if data == deviceID:
        print("Device Match")
        found = True
        comPort = port
        break

if found == False:
    print("Device Id not found")
    exit()

# if os.name == 'nt':
#     comPort = "COM21"
# else:
#     comPort = '/dev/ttyUSB0'

_current_port_id = 1

arduino = PyCmdMessenger.ArduinoBoard(comPort,baud_rate=115200,timeout=10)


# List of command names (and formats for their associated arguments). These must
# be in the same order as in the sketch.
commands = [["kWatchdog","s"],
            ["kAcknowledge","s"],
            ["kError","s"],
            ["kDrainMl",""],
            ["kSetMlPerDrain","f"],
            ["kSetMl2MilisecondsMultiplier","f"],
            ["kChangePumpDirection",""],
            ["kMoveToNextPort",""],
            ["kMoveToHome",""],
            ["kGetPortNumber",""],
            ["kGetPortNumberResult","i"],
            ["kDrainSpeed","i"],
            ["kStopPump",""],
            ["kMoveToLastPort",""]]
            #["kGetSensorReading",""],
            #["kGetSensorReadingResult","ffffffffffffffffff"],
            #["kGetSensorReadingResultRaw","IIIIIIIIIIIIIIIIII"]]


# Initialize the messenger
comm = PyCmdMessenger.CmdMessenger(arduino,commands)
#Wait for arduino to come up
msg = comm.receive()
print(msg)

def drainSpeed(speed: int) -> int:
    """Function changes the direction of the draining pump."""

    comm.send("kDrainSpeed",speed)

    msg = comm.receive()
    logging.info(msg[1])

    return 0

def stopDraining() -> int:
    """Function changes the direction of the draining pump."""

    comm.send("kStopPump")

    msg = comm.receive()
    logging.info(msg[1])

    return 0

def changePumpDirection() -> int:
    """Function changes the direction of the draining pump."""
    
    comm.send("kChangePumpDirection")

    # Receive.
    msg = comm.receive()
    logging.info(msg[1])

    return 0


def drainStep() -> str:
    """Function drains a specific amount of ml with the pump."""
    comm.send("kDrainMl")

    msg = comm.receive()
    logging.info(msg[1])

    return msg[1]


def setMlPerDrainStep(mlPerDrainStep: float) -> int:
    """Function sets the number of ml per drain step when executing the drainStep function"""
    comm.send("kSetMlPerDrain", mlPerDrainStep)

    msg = comm.receive()
    logging.info("Changed ml per drain step to " + str(msg[1]))

    return 0

def setMl2MilisecondsMultiplier(ml2MilisecondsMultiplier: float) -> int:
    """Function sets the conversion between ml and miliseconds in the pump controller."""
    comm.send("kSetMl2MilisecondsMultiplier", ml2DegreeMultiplier)

    msg = comm.receive()
    logging.info("Changed ml to miliseconds multiplier to " + str(msg[1]))

    return 0

def move_next() -> int:
    global _current_port_id

    comm.send("kMoveToNextPort")
    time.sleep(3)

    msg = comm.receive()

    logging.info("Changed to port  " + str(msg[1]))
 
    _current_port_id = msg[1][0]

    return _current_port_id

def move_last() -> int:
    global _current_port_id

    comm.send("kMoveToLastPort")
    time.sleep(3)

    msg = comm.receive()

    logging.info("Changed to port  " + str(msg[1]))
 
    _current_port_id = msg[1][0]

    return _current_port_id

def move_home() -> int:
    global _current_port_id

    comm.send("kMoveToHome")
    time.sleep(20)

    msg = comm.receive()

    logging.info("Changed to home port  " + str(msg[1]))

    _current_port_id = msg[1][0]
    
    return _current_port_id

def current_port() -> int:
    global _current_port_id

    comm.send("kGetPortNumber")
    
    msg = comm.receive()

    logging.info("Currently on port  " + str(msg[1]))

    _current_port_id = msg[1][0]

    return _current_port_id



##Debug
#logging.basicConfig(level=logging.DEBUG)

#move_home()
# print(current_port())
# time.sleep(2)
# move_next() 
# move_next() 
# setMlPerDrainStep(10)
# time.sleep(2)
# changePumpDirection()
# move_last() 
# time.sleep(2)
# move_home()
# time.sleep(2)
# drainStep()
# time.sleep(2)
#changePumpDirection()
#drainSpeed(255)
#time.sleep(33)#66 around 100ml
#stopDraining()
# move_next() 
# drainSpeed(255)
# time.sleep(300)
# stopDraining()
# move_home()

# input("Press enter to adjust")

# dir = True #True: Up, False: down

# finish = False
# while(not finish):
#     command = input("d move interface down 5 ml, u move interface up 5 ml, c finish: ")
#     if command == "d":
#         if not dir:
#             dir = True
#             changePumpDirection()
#         drainSpeed(255)
#         time.sleep(69.5)#66 around 100ml
#         stopDraining()
#     if command == "u":
#         if dir:
#             dir = False
#             changePumpDirection()
#         drainSpeed(255)
#         time.sleep(65)#66 around 100ml
#         stopDraining()
#     if command == "c":
#         finish = True

