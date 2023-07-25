import PyCmdMessenger
import time
import os
import logging
import sys
import glob
import serial

deviceID = "0,0000000-0000-0000-0000-00000000002;" 

if os.name == 'nt':
    comPort = "COM3"
else:
    comPort = '/dev/ttyUSB0'

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


_current_port_id = 1

arduino = PyCmdMessenger.ArduinoBoard(comPort,baud_rate=115200,timeout=10)

# List of command names (and formats for their associated arguments). These must
# be in the same order as in the sketch.
commands = [["kWatchdog","s"],
            ["kAcknowledge","s"],
            ["kError","s"],
            ["kGetSensorReading",""],
            ["kGetSensorReadingResult","ffffff"],
            ["kGetSensorReadingResultRaw","IIIIII"],
            ["kToggleBulb",""],
            ["kSensorType",""],
            ["kGetSensorTypeResult","I"],
            ["kSetLEDBrightness","ii"],
            ["kLEDsOff",""]]


# Initialize the messenger
comm = PyCmdMessenger.CmdMessenger(arduino,commands)
#Wait for arduino to come up
msg = comm.receive()
print(msg)



def turnLEDsOff() -> int:
    """Function for turning all LEDs off."""

    comm.send("kLEDsOff")

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

def getSensorType() -> int:
    """Function for getting the type of sensor connected to the arduino."""

    comm.send("kSensorType")

    msg = comm.receive()
    result = msg[1]

    if result == 0:
        logging.info("Sensor not initialized")

    return result

def toggleBulb() -> int:
    """Function for toggling the bulb of the sensor on and off when taking measurements."""

    comm.send("kToggleBulb")

    msg = comm.receive()
    logging.info(msg[1])

    return 0





##Debug
#logging.basicConfig(level=logging.DEBUG)







