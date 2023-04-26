#Imports
import time
import os
import logging
import pandas as pd
import asyncio
import scipy.stats as stat
import math

from enum import Enum

#Import drivers
from Drivers.BeltSensorCmd import BeltSensorDriverCmd as BeltDriver
from Drivers.DrainingAndRotaryCmd import DrainingAndRotaryCmdDriver as DrainDriver
from Drivers.CameraDriver import CameraDriver as CamDriver

#Import interface finding algorithms
import InterfaceAlg

logging.basicConfig(level=logging.DEBUG)

class LiquidType(Enum):
    ethyl = "ethyl"
    dichloro = "dichloro"
    water = "water"

#Global data
interfacePosition = 0.0
dataPath = "Data"
imageFolderName = "Images"
countFilePath = "count.txt"
funnelScanned  = True
lowerPhaseDrained = False
pumpDirection = False
conversionFactor = 1/1.5 #66/100
liquidType = LiquidType.ethyl


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

def setLiquidType(lType):
    global liquidType
    if lType in LiquidType.__members__:
        for name in LiquidType.__members__:
            if lType == name:
                liquidType = LiquidType[name]
    else:
        print("Not a valid liquid type") 


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

    global funnelScanned, interfacePosition
    if(funnelScanned):

        if liquidType is LiquidType.ethyl:
            interfaceFound, interfacePosition, error = InterfaceAlg.findInterfaceEthyl(dataLight,smoothProminence,smoothWindowSize)
        elif liquidType is LiquidType.dichloro:
            interfaceFound, interfacePosition, error = InterfaceAlg.findInterfaceDichloro(dataLight,smoothProminence,smoothWindowSize)
        else:
            interfaceFound = False
            interfacePosition = 0.0
            error = "No procedure defined for finding the interface"

    return interfaceFound, interfacePosition, error



#Drain phases
async def drain(portLower: int, portUpper: int) -> str:
    await drainLowerPhase(portLower)
    await drainUpperPhase(portUpper)

    return "All phases drained"

def startPump(speed:int,dir:bool):
    if pumpDirection != dir:
        DrainDriver.changePumpDirection()
        pumpDirection = dir

    DrainDriver.drainSpeed(speed)

    return 1

def stopPump():
    DrainDriver.stopDraining()

#Calculate the ml resting given a list of limits for different stages 
def calculateDrainStages(drainLimits: list, mlToDrain: float)-> list:
    drainStages = []

    rest = mlToDrain

    for i in range(len(drainLimits)):
        if rest >= drainLimits[i]:
            drainStages.append(rest - drainLimits[i])
            rest = drainLimits[i]
        else:
            drainStages.append(0)

    return drainStages


#Drain lower phase
async def drainLowerPhase(port: int,interfacePosition:float) -> str:
    global lowerPhaseDrained, pumpDirection


    #Convert the interface position in a number of ml to drain
    mlToDrain = getVolumeLowerPhase(interfacePosition)

    #Divide the volume in 5 parts and reduce the speed by 20% for each part

    drainLimits = [450,200,100,50,0]

    drainStages = calculateDrainStages(drainLimits,mlToDrain)

    stageSpeed = [255,204,153,102,51]

    # drainSpeeds = []
    # drainSpeeds[0] = 255 # 1
    # drainSpeeds[1] = 153 #0.6
    # drainSpeeds[2] = 102 #0.4
    # drainSpeeds[3] = 51 #0.2

    try:
        moveValveToPort(port)
        if not pumpDirection:
            DrainDriver.changePumpDirection()
            pumpDirection = not pumpDirection
        
        for i in range(len(drainStages)):
            
            secondsToDrain, conversionFactor = convertMlToSeconds(drainStages[i])

            secondsToDrain = secondsToDrain*(255/stageSpeed[i])
     
            logging.info("interfacePosition = " + str(interfacePosition))
            logging.info("mlToDrain = " + str(drainStages[i]))
            logging.info("secondsToDrain = " + str(secondsToDrain))

            DrainDriver.drainSpeed(stageSpeed[i])
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


async def pumpMlFromPort(ml: float, port :int , tubingVolume:float):
    global pumpDirection

    secondsToPump, conversionFactor = convertMlToSeconds(ml+tubingVolume)
    logging.info("mlToPump = " + str(ml))
    logging.info("secondsToPump = " + str(secondsToPump))

    moveValveToPort(port)

    if pumpDirection:
        DrainDriver.changePumpDirection()
        pumpDirection = not pumpDirection
    
    DrainDriver.drainSpeed(255)
    await asyncio.sleep(secondsToPump)#66 around 100ml
    DrainDriver.stopDraining()

    return port, ml, conversionFactor, secondsToPump, ""


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