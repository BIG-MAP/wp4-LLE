import numpy as np
import serial
import time
import os


if os.name == 'nt':
    comPort = "COM5"
    cameraDev = 0
else:
    comPort = '/dev/ttyUSB0'
    cameraDev = '/dev/video0'


def resetArduinoSerial():
    time.sleep(0.5) #Wait for port to close
    arduino = serial.Serial(port=comPort, baudrate=115200, timeout=10)
    print("Resetting arduino serial port, freezing for 5 seconds")
    time.sleep(5) #Hard wait as everything is stopped
    arduino.close()




class BeltSensor:
    stepsPerPass = 10
    line = 0
    arduino = None
    file = None
    fileRaw = None
    lightHeight = 5

    def init(self, stepsPerPass):
        self.stepsPerPass = stepsPerPass

        #Connect to arduino
        self.arduino = serial.Serial(port=comPort, baudrate=115200, timeout=2)
        time.sleep(10)

        #Other process parameters
        with open('count.txt', "r") as counterFile:
            start = int(counterFile.read())+1
        print("Start number ", start)

        fileName='BeltSpectro-data'+str(start)+'.csv' #name of the CSV file generated
        fileNameRaw='BeltSpectro-data'+str(start)+'RAW.csv' #name of the CSV file generated

        self.file = open(fileName, "a")
        self.fileRaw = open(fileNameRaw, "a")
        print("Created files")
        self.line  = 0

        with open('count.txt', "w") as counterFile:
            counterFile.write(str(start))

        data = "A,B,C,D,E,F,G,H,I,J,K,L,R,S,T,U,V,W,Stage,Interval"
        self.file.write(data + "\n") #write data with a newline
        self.fileRaw.write(data + "\n") #write data with a newline


    def sensorPass(self,milimeters):
        
        self.arduino.write(bytes('a'+str(self.lightHeight), 'utf-8'))

        self.waitForResponse()

        self.arduino.write(bytes('n', 'utf-8'))

        self.waitForResponse()

        self.arduino.write(bytes('h', 'utf-8'))

        self.waitForResponse()


        for i in range(self.stepsPerPass):
            if milimeters:
                self.arduino.write(bytes('s', 'utf-8'))
            else:
                self.arduino.write(bytes('u', 'utf-8'))

            getData= self.arduino.readline()
            data = getData.decode('utf-8').rstrip()

            stop = False
            while data!='0':
                getData= self.arduino.readline()
                data = getData.decode('utf-8').rstrip()
                if data == "Already at the top":
                    print("At the top")
                    stop = True
                time.sleep(0.1)

            if stop:
                break


            self.arduino.write(bytes('m', 'utf-8'))

            getData= self.arduino.readline()
            data = getData.decode('utf-8').rstrip()
            
            getData= self.arduino.readline()
            dataRaw = getData.decode('utf-8').rstrip()
            
            self.line = self.line + 1
            print(str(self.line))
            data = data
            dataRaw = dataRaw
                
            print(data)
            print(dataRaw)
            
            #add the data to the files
            self.file.write(data + "\n") #write data with a newline
            self.fileRaw.write(dataRaw + "\n") #write data with a newline

        print("Logged "+str(self.line)+" lines")

        self.arduino.write(bytes('o', 'utf-8'))

        self.waitForResponse()

        self.file.close()
        self.fileRaw.close()
        self.arduino.close()

        return "Pass completed"

    def waitForResponse(self):

        getData= self.arduino.readline()
        data = getData.decode('utf-8').rstrip()

        while data!='0':
            getData= self.arduino.readline()
            data = getData.decode('utf-8').rstrip()
            time.sleep(0.1)




def main():
    measure = BeltSensor()

    measure.init(20)

    measure.sensorPass(True)




if __name__ == '__main__':
    main()





