import PyCmdMessenger
import os
import logging
import sys
import glob
import serial
import time
from software.Drivers.Serial_find import find_port

deviceID = "0,0000000-0000-0000-0000-00000000003;"
found, comPort = find_port(deviceID)
pumpState = False

arduino = PyCmdMessenger.ArduinoBoard(comPort, baud_rate=115200, timeout=10)

# List of command names (and formats for their associated arguments). These must
# be in the same order as in the sketch.
commands = [["kWatchdog", "s"],
            ["kAcknowledge", "s"],
            ["kError", "s"],
            ["kSetVoltage", "i"],
            ["kStopPump", "s"],
            ["kCyclePump", ""]]

# Initialize the messenger
comm = PyCmdMessenger.CmdMessenger(arduino, commands)
# Wait for arduino to come up
msg = comm.receive()
print(msg)


def setVoltage(voltage: int) -> int:
    """Function for setting the voltage of the DAC controlling the pump (0-4096)."""

    comm.send("kSetVoltage", voltage)

    msg = comm.receive()
    logging.info(msg[1])

    return 0


def stopPump() -> int:
    global pumpState
    """Function for stopping the pump."""

    comm.send("kStopPump")

    msg = comm.receive()
    logging.info(msg[1])

    pumpState = False

    return 0


def cyclePump() -> int:
    global pumpState
    """Function for starting or stopping the pump."""

    comm.send("kCyclePump")

    msg = comm.receive()
    logging.info(msg[1])

    time.sleep(0.4)

    pumpState = not pumpState

    return 0


def getPumpState() -> bool:
    """Function for returning the pump state"""
    global pumpState

    return pumpState

##Always start with pump stopped
# stopPump()

##Debug
# logging.basicConfig(level=logging.DEBUG)
# ## Set Voltage and start pump
# time.sleep(3)
# setVoltage(2047)
# cyclePump()
# time.sleep(3)
# stopPump()
# time.sleep(2)
# cyclePump()
# print(getPumpState())
# setVoltage(1024)
# time.sleep(2)
# stopPump()
# time.sleep(1)
# enablePump(False)
# ##Stop Pump
# setVoltage(0)
# time.sleep(2)
# ##Ramp voltage up
# for i in range(0,4096,50):
#     setVoltage(i)
#     time.sleep(0.05)

# time.sleep(2)
# #Ramp down
# for i in range(4095,-1,-50):
#     setVoltage(i)
#     time.sleep(0.05)

# time.sleep(2)
# ##Stop Pump
# setVoltage(0)
