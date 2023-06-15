import PyCmdMessenger
import time
import os
import logging


if os.name == 'nt':
    comPort = "COM8"
else:
    comPort = '/dev/ttyUSB0'

_current_port_id = 1

arduino = PyCmdMessenger.ArduinoBoard(comPort,baud_rate=115200,timeout=10)


# List of command names (and formats for their associated arguments). These must
# be in the same order as in the sketch.
commands = [["kWatchdog","s"],
            ["kAcknowledge","s"],
            ["kError","s"],
            ["kOpenValve","i"],
            ["kCloseValve","i"],
            ["kStartPump",""],
            ["kStopPump",""],
            ["kSetPumpSpeed","f"]]


# Initialize the messenger
comm = PyCmdMessenger.CmdMessenger(arduino,commands)
#Wait for arduino to come up
msg = comm.receive()
print(msg)


def open_Valve(valveNumber: int) -> int:

    if(valveNumber >=0 or valveNumber <=7):
        comm.send("kOpenValve",valveNumber)
        msg = comm.receive()
        logging.info("Opened valve number  " + str(valveNumber))

    else:
        logging.info("Valve number not recognized")
        return 1
    
    return 0


def close_Valve(valveNumber: int) -> int:

    if(valveNumber >=0 or valveNumber <=7):
        comm.send("kCloseValve",valveNumber)
        msg = comm.receive()
        logging.info("Closed valve number  " + str(valveNumber))

    else:
        logging.info("Valve number not recognized")
        return 1
    
    return 0

def set_Pump_Speed(speed: int) -> int:

    if(speed >=0 or speed <=100):
        comm.send("kSetPumpSpeed",speed)
        msg = comm.receive()
        logging.info("Set pump speed to " + str(speed))

    else:
        logging.info("Pump speed out of bounds")
        return 1
    
    return 0


def start_Pump() -> int:
    """Function drains a specific amount of ml with the pump."""
    comm.send("kStartPump")

    msg = comm.receive()
    logging.info(msg[1])

    return 0


def stop_Pump() -> int:
    """Function drains a specific amount of ml with the pump."""
    comm.send("kStopPump")

    msg = comm.receive()
    logging.info(msg[1])

    return 0