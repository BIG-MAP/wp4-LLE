import serial
import serial.tools.list_ports

def find_port(deviceID):
    # Get a list of all connected serial devices
    ports = list(serial.tools.list_ports.comports())

    for port in ports:
        try:
            # Open the port
            print(port)
            s = serial.Serial(port.device, baudrate=115200, timeout=2)
            s.write(bytes('0;', 'utf-8'))
            getData = s.read_until(';')
            s.write(bytes('0;', 'utf-8'))
            getData = s.read_until(';')
            data = getData.decode('utf-8').rstrip()
            print(data)
            # If the response is as expected, print the device info and return
           #print(f"Connected to the device: {port.device}")
            s.close()
            if data == deviceID:
                print("Device Match")

                return True,port.device
        except (OSError, serial.SerialException):
            pass

    print("No suitable device found.")
    return None


