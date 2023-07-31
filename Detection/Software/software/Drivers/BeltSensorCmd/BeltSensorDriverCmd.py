import PyCmdMessenger
import time
import os
import logging
import sys
import glob
import serial
from software.Drivers.Serial_find import find_port

deviceID = "0,0000000-0000-0000-0000-00000000001;"

found, comPort=find_port(deviceID)

if found == False:
    print("Device Id not found")
    exit()


_current_port_id = 1

arduino = PyCmdMessenger.ArduinoBoard(comPort,baud_rate=115200,timeout=10)

# List of command names (and formats for their associated arguments). These must
# be in the same order as in the sketch.
commands = [["kWatchdog","s"],
            ["kAcknowledge","s"],
            ["kError","s"],
            ["kHomeBelt",""],
            ["kTopBelt",""],
            ["kUpCm",""],
            ["kDownCm",""],
            ["kUpMm",""],
            ["kLEDsOff",""],
            ["kLEDsOn",""],
            ["kSetNumberOfLEDs","i"],
            ["kGetSensorReading",""],
            ["kGetSensorReadingResult","ffffffffffffffffff"],
            ["kGetSensorReadingResultRaw","IIIIIIIIIIIIIIIIII"],
            ["kSetLEDBrightness","ii"],
            ["kUpSteps","i"]]



# Initialize the messenger
comm = PyCmdMessenger.CmdMessenger(arduino,commands)
#Wait for arduino to come up
msg = comm.receive()
print(msg)


def homeBelt() -> str:
    """Function for homing the belt at the bottom of the funnel."""

    comm.send("kHomeBelt")

    msg = comm.receive()
    logging.info(msg[1])

    return msg[1]

def topBelt() -> int:
    """Function for moving the belt to the top of the funnel."""

    comm.send("kTopBelt")

    msg = comm.receive()
    logging.info(msg[1])

    return 0

def upCm() -> int:
    """Function for moving the belt up by one cm."""

    comm.send("kUpCm")

    msg = comm.receive()
    logging.info(msg[1])

    return 0

def downCm() -> int:
    """Function for moving the belt down by one cm."""

    comm.send("kDownCm")

    msg = comm.receive()
    logging.info(msg[1])

    return 0

def upMm() -> int:
    """Function for moving the belt up by one mm along the belt."""

    comm.send("kUpMm")

    msg = comm.receive()
    logging.info(msg[1])

    return 0

def upSteps(steps: int) -> int:
    """Function for moving the belt up by one mm in height."""

    comm.send("kUpSteps", steps)

    msg = comm.receive()
    logging.info(msg[1])

    return 0

def turnLEDsOff() -> int:
    """Function for turning all LEDs off."""

    comm.send("kLEDsOff")

    msg = comm.receive()
    logging.info(msg[1])

    return 0

def turnLEDsOn() -> int:
    """Function for turning all LEDs off."""

    comm.send("kLEDsOn")

    msg = comm.receive()
    logging.info(msg[1])

    return 0

def setNumberOfLEDs(nLEDs: int) -> int:
    """Function for setting the number of LEDs to be turned on (Starts at 0)."""

    comm.send("kSetNumberOfLEDs",nLEDs)

    msg = comm.receive()
    logging.info(msg[1])

    return 0

def takeMeasurement():
    """Function for taking a measurement of the optical sensor and returning a list of lists with the values."""
    result = [[],[]]
    comm.send("kGetSensorReading")

    #Retrieve calibrated data
    msg = comm.receive()
    #logging.info(msg[1])
    #Save data on first position of result
    result[0] = msg[1]

    #Retrieve RAW data
    msg = comm.receive()
    #logging.info(msg[1])
    #Save data on second position of result
    result[1] = msg[1]

    return result

def setLEDBrightness(led: int, brightness: int) -> int: 
    """Function for setting the brightness of one led at a time"""
    comm.send("kSetLEDBrightness",led,brightness)

    msg = comm.receive()
    logging.info(msg[1])

    return 0



##Debug
# logging.basicConfig(level=logging.DEBUG)

# homeBelt()
# # setNumberOfLEDs(0)
# # turnLEDsOn()

# for i in range(30):
#     upMm()
#     time.sleep(0.5)

# time.sleep(20)

# for i in range(10):
#     upMm()
#     time.sleep(0.5)

# homeBelt()


#     setNumberOfLEDs(i)
#     turnLEDsOn()

#     result = takeMeasurement()
#     logging.info(result)

# turnLEDsOff()
# homeBelt()





