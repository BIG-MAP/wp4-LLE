import PyCmdMessenger
import time
import os
import logging

import sys
import glob
import serial
from software.Drivers.Serial_find import find_port

deviceID = "0,0000000-0000-0000-0000-00000000000;"

found, comPort = find_port(deviceID)

arduino = PyCmdMessenger.ArduinoBoard(comPort, baud_rate=115200, timeout=10)

# List of command names (and formats for their associated arguments). These must
# be in the same order as in the sketch.
commands = [["kWatchdog", "s"],
            ["kAcknowledge", "s"],
            ["kError", "s"],
            ["kDrainMl", ""],
            ["kSetMlPerDrain", "f"],
            ["kSetMl2MilisecondsMultiplier", "f"],
            ["kChangePumpDirection", ""],
            ["kMoveToNextPort", ""],
            ["kMoveToHome", ""],
            ["kGetPortNumber", ""],
            ["kGetPortNumberResult", "i"],
            ["kDrainSpeed", "i"],
            ["kStopPump", ""],
            ["kMoveToLastPort", ""]]
# ["kGetSensorReading",""],
# ["kGetSensorReadingResult","ffffffffffffffffff"],
# ["kGetSensorReadingResultRaw","IIIIIIIIIIIIIIIIII"]]


# Initialize the messenger
comm = PyCmdMessenger.CmdMessenger(arduino, commands)
# Wait for arduino to come up
msg = comm.receive()
print(msg)


def drainSpeed(speed: int) -> int:
    """Function changes the direction of the draining pump."""

    comm.send("kDrainSpeed", speed)

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
# logging.basicConfig(level=logging.DEBUG)

# move_home()
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
# changePumpDirection()
# drainSpeed(255)
# time.sleep(33)#66 around 100ml
# stopDraining()
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

