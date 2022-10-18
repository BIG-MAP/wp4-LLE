#Imports
import time
import os
import logging
import pandas as pd
import asyncio

import numpy as np
from scipy import ndimage
import scipy.signal as sig
import scipy.stats as stat
import math

#Import drivers
from Drivers.BeltSensorCmd import BeltSensorDriverCmd as BeltDriver
from Drivers.DrainingAndRotaryCmd import DrainingAndRotaryCmdDriver as DrainDriver
from Drivers.CameraDriver import CameraDriver as CamDriver

logging.basicConfig(level=logging.DEBUG)

#Global data
interfacePosition = 0.0
dataPath = "Data"
imageFolderName = "Images"
countFilePath = "count.txt"
funnelScanned  = True
lowerPhaseDrained = False
pumpDirection = False
conversionFactor = 66/100


#Driver Initialization
#Rotary valve
valveCurrentPort = DrainDriver.move_home()
valveStatus = True
camStatus = CamDriver.initCamera()



#Function definition

#Support functions
def nextDelta(lastDelta):
    nextDelta = lastDelta
    return nextDelta

def getNextBrightness(lastBrightness, lastDelta):
    nextBrightness = lastBrightness + nextDelta(lastDelta)
    return nextBrightness

def calculateVolumeFulstrum(initialVolume,tubingVolume,r,deltaDistance,funnelAngle):
    """
        Returns the volume in ml given a distance from the reference initial volume point
        and its associated radius in the funnel
    """
    R = (deltaDistance*math.sin(funnelAngle)) + r
    h = deltaDistance*math.cos(funnelAngle) 
    radiusTerm = (R*R) + (R*r) + (r*r)
    v = (math.pi*h*radiusTerm)/3
    return v*1000000+initialVolume+tubingVolume

def createDataFrameFromFile(path):
 
    column_names = ["A","B","C","D","E","F","G","H","I","J","K","L","R","S","T","U","V","W"]
    
    df = pd.read_csv(path)
    df.columns = column_names
    df.index += 1

    return df

def getVolumeLowerPhase(interfacePosition: float) -> float:
    sensorBorderM = (interfacePosition - 15)*0.001

    volumeMl = calculateVolumeFulstrum(300,0,0.0455,sensorBorderM,0.296706)#80-5ml error Original 300 ml initial volume 10 ml tubing volume

    return volumeMl

def convertMlToSeconds(mlToDrain: float)-> float:
    global conversionFactor
    return mlToDrain*conversionFactor, conversionFactor



#Main functions

#Move to port
def moveValveToPort(target_port_id: int)-> int:
    """Function keeps the rotary valve moving until it reaches the goal."""
    global valveCurrentPort
    global valveStatus

    if valveStatus:
        if target_port_id < 1 or target_port_id > 4:  # NOTE: assuming ports have numbers 1, 2, 3 and 4
            logging.error(f'Invalid port has been called: {target_port_id}')
            return -1
      
        logging.info("valveCurrentPort: "+ str(valveCurrentPort))
        logging.info("target_port_id: " + str(target_port_id))
        while int(valveCurrentPort) != target_port_id:
            valveCurrentPort = DrainDriver.move_next()
    else:
        logging.error("Valve hasn't been started")
        return -1

    return valveCurrentPort

    

#Scan funnel
def scanFunnel(initialLEDs: int,delta: int,travelDistance: int, stopEvent: asyncio.Event = asyncio.Event()):
    global funnelScanned
    try:
        #Home sensor
        BeltDriver.homeBelt()

        #Folder and file names
        with open(os.path.dirname(__file__)+'/count.txt', "r") as counterFile:
                start = int(counterFile.read())

        with open(os.path.dirname(__file__)+'/count.txt', "w") as counterFile:
                counterFile.write(str(start+1))

        folderPath = dataPath + str(start)
        os.mkdir(folderPath)

        fileName = folderPath + '/data.csv' #name of the CSV file generated
        fileNameRaw = folderPath + '/dataRAW.csv' #name of the CSV file generated

        imageFolderPath = folderPath + '/'+ imageFolderName
        os.mkdir(imageFolderPath)
        imgCounter = 0

        #Initial LED settings
        #initialLEDs = 4
        currentLEDs = initialLEDs
        nextLEDBrightness = 0
        #delta = 16 #16

        BeltDriver.setNumberOfLEDs(initialLEDs)
        BeltDriver.turnLEDsOn()
        currentLEDs = currentLEDs + 1
        readings = None
        readingsRaw = None

        for i in range(travelDistance):#169 mm Along the belt, 160 in vertical height
            if(stopEvent.is_set()):
                logging.error("Stopping scan")
                break
            #Capture image and save it
            if(camStatus):
                CamDriver.captureImage(imageFolderPath,'funnel'+str(imgCounter)+'.jpg')
                imgCounter = imgCounter + 1
            else:
                logging.error("Camera not initialized")

            #BeltSensorDriverCmd.upSteps(16) #84 steps 1mm in height
            BeltDriver.upMm() # Up 1 mm along the belt

            nextLEDBrightness = getNextBrightness(nextLEDBrightness,delta)

            if nextLEDBrightness >= 255:
                nextLEDBrightness = 255
                BeltDriver.setLEDBrightness(currentLEDs, nextLEDBrightness)
                currentLEDs = currentLEDs + 1
                nextLEDBrightness = 0
            else:
                BeltDriver.setLEDBrightness(currentLEDs, nextLEDBrightness)

            result = BeltDriver.takeMeasurement()

            if readings == None:
                readings  = [[]]
                readings[0] = result[0]
                readingsRaw  = [[]]
                readingsRaw[0] = result[1]
            else:
                readings.append(result[0])
                readingsRaw.append(result[1])
            

            
        BeltDriver.setNumberOfLEDs(currentLEDs)
        BeltDriver.turnLEDsOff()

        column_names = ["A","B","C","D","E","F","G","H","I","J","K","L","R","S","T","U","V","W"]
        df = pd.DataFrame(readings, columns = column_names)
        dfRaw = pd.DataFrame(readingsRaw, columns = column_names)

        df.to_csv(fileName,index=False)
        dfRaw.to_csv(fileNameRaw,index=False)
        funnelScanned = True

    except serial.SerialException as e:
        #There is no new data from serial port readings
        return None, None, "scanFunnel: No data read from serial port"
    except TypeError as e:
        #Disconnect of USB->UART occured
        return None, None, "scanFunnel: Serial port disconnected"

    return df, dfRaw, start, ""


#Find interface
def findInterface(dataLight, smoothWindowSize: int, smoothProminence: float, gradient2Prominence:float):
    #TODO: Update with minima detection

    global funnelScanned, interfacePosition
    if(funnelScanned):

        interfaceFound = False

        # #Folder and file names
        # with open(os.path.dirname(__file__)+'/count.txt', "r") as counterFile:
        #     start = int(counterFile.read())-1

        # folderPath = dataPath + str(start)
        # fileName = folderPath + '/data.csv' #name of the CSV file generated
        # fileNameRaw = folderPath + '/dataRAW.csv' #name of the CSV file generated

        # df = createDataFrameFromFile(fileName)
        df = dataLight
        df[["A","B","C","D","E","F","G","H","I","J","K","L","R","S","T","U","V","W"]] = df[["A","B","C","D","E","F","G","H","I","J","K","L","R","S","T","U","V","W"]].apply(pd.to_numeric)
        print(df)

        #Normalize all channels
        df[["A","B","C","D","E","F","G","H","I","J","K","L","R","S","T","U","V","W"]] = df[["A","B","C","D","E","F","G","H","I","J","K","L","R","S","T","U","V","W"]].apply(lambda x: x/x.max(), axis=0)

        interfaces = []
        offset = 2
        for channel in ["A","B","C","D","E","F","G","H","I","J","K","L","R","S","T","U","V","W"]:
            #for channel in ["G","I"]:
            #Convert channels to numpy arrays
            channelData = df[channel].to_numpy()
            #Smooth the curve with a predefined window size
            smooth = ndimage.uniform_filter1d(channelData, size=smoothWindowSize)
            #Find first finite difference of smoothed curve
            gradient = np.gradient(smooth,edge_order=2)
            #Find second finite difference of smoothed curve
            gradient2 = np.gradient(gradient,edge_order=2)
                
            #Find the max value of the smoothed data to find the peaks
            maxValue = np.max(smooth)
            
            peaks, _ = sig.find_peaks(smooth, prominence = smoothProminence*maxValue)#1/6
                
            #Find the inverse peaks to find the valley when the signal drops
            inversePeaks,_ = sig.find_peaks(-smooth, prominence = maxValue*smoothProminence)
            
            
            #Find the maximum value of the second difference of the smoothed data
            maxGradient2 = np.max(gradient2)
            #Find the negative peaks of the first difference of the smoothed data to find the valleys
            peaksGrad2, _ = sig.find_peaks(gradient2,prominence=gradient2Prominence*maxGradient2)#1/4
            #print('Peaks Gradient',peaksGrad)
            
            #Find all the peaks of the second derivative that are between the first and last most prominent peaks
            indices = np.where((peaksGrad2 < peaks[-1]))
            peaksGrad2Cut = peaksGrad2[indices]       

            if len(peaks)>0:
                if len(peaksGrad2Cut) > 0:
                    interface = peaksGrad2Cut[-1]
                else:
                    interface = inversePeaks[0] 

                interface = peaks[-1]+offset
                if channel in ["A","B","C","D","E","F"]:
                        interface -= 10   
                interfaces.append(interface)
                interfaceFound = True         
        
        if interfaceFound:      
            print(interfaces)

            #finalInterface = np.mean(interfaces)
            finalInterface = np.median(interfaces)
            #finalInterface = stat.mode(interfaces)[0][0]
            print("Final Interface:", finalInterface)

            interfacePosition = finalInterface

        else:
            print("Interface not found")
            interfacePosition = 0.0

        return interfaceFound, interfacePosition, ""



#Drain phases
async def drain(portLower: int, portUpper: int) -> str:
    await drainLowerPhase(portLower)
    await drainUpperPhase(portUpper)

    return "All phases drained"

def stopPump():
    DrainDriver.stopDraining()


#Drain lower phase
async def drainLowerPhase(port: int,interfacePosition:float) -> str:
    global lowerPhaseDrained, pumpDirection
    #Convert the interface position in a number of ml to drain
    mlToDrain = getVolumeLowerPhase(interfacePosition)
    
    secondsToDrain, conversionFactor = convertMlToSeconds(mlToDrain)
     
    logging.info("interfacePosition = " + str(interfacePosition))
    logging.info("mlToDrain = " + str(mlToDrain))
    logging.info("secondsToDrain = " + str(secondsToDrain))

    try:
        moveValveToPort(port)
        if not pumpDirection:
            DrainDriver.changePumpDirection()
            pumpDirection = not pumpDirection

        DrainDriver.drainSpeed(255)
        await asyncio.sleep(secondsToDrain)#66 around 100ml
        DrainDriver.stopDraining()
        #DrainDriver.setMlPerDrainStep(mlToDrain)
        #DrainDriver.drainStep()

        lowerPhaseDrained = True
    except serial.SerialException as e:
        #There is no new data from serial port readings
        return port, mlToDrain, conversionFactor, secondsToDrain, "drainLowerPhase: No data read from serial port"
    except TypeError as e:
        #Disconnect of USB->UART occured
        return port, mlToDrain, conversionFactor, secondsToDrain, "drainLowerPhase: Serial port disconnected"

    return port, mlToDrain, conversionFactor, secondsToDrain, "" 


#Drain upper phase
async def drainUpperPhase(port: int) -> str:
    global lowerPhaseDrained, pumpDirection
    
    mlToDrain = 1000
    secondsToDrain, conversionFactor = convertMlToSeconds(mlToDrain)
    
    if(lowerPhaseDrained):
     
        logging.info("interfacePosition = " + str(interfacePosition))
        logging.info("mlToDrain = " + str(mlToDrain))
        logging.info("secondsToDrain = " + str(secondsToDrain))
        
        try:
            moveValveToPort(port)
            if not pumpDirection:
                DrainDriver.changePumpDirection()
                pumpDirection = not pumpDirection

            DrainDriver.drainSpeed(255)
            await asyncio.sleep(secondsToDrain)#66 around 100ml
            DrainDriver.stopDraining()
            #DrainDriver.setMlPerDrainStep(mlToDrain)
            #DrainDriver.drainStep()
        except serial.SerialException as e:
            #There is no new data from serial port readings
            return port, mlToDrain, conversionFactor, secondsToDrain, "drainUpperPhase: No data read from serial port"
        except TypeError as e:
            #Disconnect of USB->UART occured
            return port, mlToDrain, conversionFactor, secondsToDrain, "drainUpperPhase: Serial port disconnected"

        return port, mlToDrain, conversionFactor, secondsToDrain, "" 
    else:
        return port, mlToDrain, conversionFactor, secondsToDrain, "drainUpperPhase: Lower phase not drained yet"


#Force interface position
def setInterfacePosition(position: float) -> str:
    global interfacePosition
    interfacePosition = position
    return "Interface position set from outside"

def getSensorData(idN: int):
    with open(os.path.dirname(__file__)+'/count.txt', "r") as counterFile:
        start = int(counterFile.read())-1

    if(idN <= start):
        folderPath = dataPath + str(idN)
        fileName = folderPath + '/data.csv' #name of the CSV file generated

        df = createDataFrameFromFile(fileName)
        logging.info("Returning data " + str(idN))
        return df
    else:
        logging.error("Data id does not exist")
        return None


def getSensorDataRaw(idN: int):
    with open(os.path.dirname(__file__)+'/count.txt', "r") as counterFile:
        start = int(counterFile.read())-1

    if(idN <= start):
        folderPath = dataPath + str(idN)
        fileNameRaw = folderPath + '/dataRAW.csv' #name of the CSV file generated

        dfRaw = createDataFrameFromFile(fileNameRaw)
        logging.info("Returning data raw " + str(idN))
        return dfRaw
    else:
        logging.error("Data id does not exist")
        return None




async def drainMlToPort(ml: float,port: int):
    global pumpDirection

    secondsToDrain, conversionFactor = convertMlToSeconds(ml)
    logging.info("mlToDrain = " + str(ml))
    logging.info("secondsToDrain = " + str(secondsToDrain))

    moveValveToPort(port)
    if not pumpDirection:
        DrainDriver.changePumpDirection()
        pumpDirection = not pumpDirection

    DrainDriver.drainSpeed(255)
    await asyncio.sleep(secondsToDrain)#66 around 100ml
    DrainDriver.stopDraining()
    #DrainDriver.setMlPerDrainStep(mlToDrain)
    #DrainDriver.drainStep()

    return port, ml, conversionFactor, secondsToDrain, ""


def getImageDataFolderPath(idN: int)-> str:

    with open(os.path.dirname(__file__)+'/count.txt', "r") as counterFile:
        start = int(counterFile.read())-1

    if(idN <= start):
        folderPath = dataPath + str(idN)
        imageFolderPath = folderPath + '/'+ imageFolderName
        return imageFolderPath
    else:
        return "Data id does not exist"




#Return last image data

#Return last sensor data