#Imports
import time
import os
import logging
import pandas as pd
import asyncio
import scipy.stats as stat
import math

import numpy as np
from scipy import ndimage
import scipy.signal as sig

from enum import Enum

#Import drivers
from software.Drivers.BeltSensorCmd import BeltSensorDriverCmd as BeltDriver
from software.Drivers.DrainingAndRotaryCmd import DrainingAndRotaryCmdDriver as DrainDriver
from software.Drivers.CameraDriver import CameraDriver as CamDriver
from software.Drivers.TubingSensor import TubingSensorDriverCmd as TubingSensorDriver

#Import interface finding algorithms
#from API.FastAPI.BeltDrainLLE.InterfaceAlg import *

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
conversionFactor = 1/1.60425 #1/1.5 #66/100
liquidType = LiquidType.ethyl
lowestDetectionPoint = 400


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

def calculateVolumeFulstrum(initialVolume:float,tubingVolume:float,r:float,deltaDistance:float,funnelAngle:float)->float:
    """
        Returns the volume in ml given a distance from the reference initial volume point
        and its associated radius in the funnel
    """
    R = (deltaDistance*math.sin(funnelAngle)) + r
    h = deltaDistance*math.cos(funnelAngle) 
    radiusTerm = (R*R) + (R*r) + (r*r)
    v = (math.pi*h*radiusTerm)/3
    return v*1000000+initialVolume+tubingVolume

def calculateVolumeRegression(interfacePosition:float):
    # squareConstant = 0.0435  # FISC March 2023
    # linearConstant = 4.4515
    # bias = 253.74
    squareConstant = 0.0519  # FISC August 2023
    linearConstant = 3.798
    bias = 258.42
    squareTerm = (interfacePosition*interfacePosition)*squareConstant
    linearTerm = interfacePosition*linearConstant

    return squareTerm+linearTerm+bias

def createDataFrameFromFile(path):
 
    column_names = ["A","B","C","D","E","F","G","H","I","J","K","L","R","S","T","U","V","W"]
    
    df = pd.read_csv(path)
    df.columns = column_names
    df.index += 1

    return df

def getVolumeLowerPhase(interfacePosition: float) -> float:
    #sensorBorderM = (interfacePosition - 15)*0.001
    #volumeMl = calculateVolumeFulstrum(300,0,0.0455,sensorBorderM,0.296706)#80-5ml error Original 300 ml initial volume 10 ml tubing volume
    volumeMl = calculateVolumeRegression(interfacePosition) 

    return volumeMl

def convertMlToSeconds(mlToDrain: float,speed: int)-> float:
    global conversionFactor
    if speed == 255:
        with open('./conversion255.txt', "r") as conversionFile:
            conversion = float(conversionFile.read())
            return mlToDrain*conversion, conversion
    elif speed == 50:
        with open('./conversion50.txt', "r") as conversionFile:
            conversion = float(conversionFile.read())
            return mlToDrain*conversion, conversion
    elif speed == 100:
        with open('./conversion100.txt', "r") as conversionFile:
            conversion = float(conversionFile.read())
            return mlToDrain*conversion, conversion
    elif speed == 130:
        with open('./conversion130.txt', "r") as conversionFile:
            conversion = float(conversionFile.read())
            return mlToDrain*conversion, conversion


    return mlToDrain*conversionFactor, conversionFactor


def hello():
    logging.info("hello")

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
    global funnelScanned, interfacePosition,liquidType
    logging.info("Finding the interface")

    interfaceFound = False
    error = ""

    if(funnelScanned):
        #logging.info("Funnel is scanned")
        #logging.info(liquidType)
        if liquidType is LiquidType.ethyl:
            logging.info("Finding ethyl acetate interface")
    
            interfaceFound = False
            error = ""  
            
            df = dataLight
            df[["A","B","C","D","E","F","G","H","I","J","K","L","R","S","T","U","V","W"]] = df[["A","B","C","D","E","F","G","H","I","J","K","L","R","S","T","U","V","W"]].apply(pd.to_numeric)
            print(df)

            #Normalize all channels
            df[["A","B","C","D","E","F","G","H","I","J","K","L","R","S","T","U","V","W"]] = df[["A","B","C","D","E","F","G","H","I","J","K","L","R","S","T","U","V","W"]].apply(lambda x: x/x.max(), axis=0)
            
            smoothWindowSize = 5
            smoothProminence = 1/15
            inverseSmoothProminence =1/15
            gradientProminence = 1
            gradient2Prominence=1/3

            interfaces = []
            interfaceFound = False
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
                inversePeaks,_ = sig.find_peaks(-smooth, prominence = maxValue*inverseSmoothProminence)
                
                #Find the maximum value of the first difference of the smoothed data
                maxGradient = np.max(gradient)
                #Find the peaks of the first difference of the smoothed data
                peaksGrad, _ = sig.find_peaks(gradient,prominence=gradientProminence*maxGradient,height =maxGradient*1/2)#1/4

                #Find the maximum value of the second difference of the smoothed data
                maxGradient2 = np.max(gradient2)

                #Find the peaks of the second difference of the smoothed data
                peaksGrad2, _ = sig.find_peaks(gradient2,prominence=gradient2Prominence*maxGradient2)#1/4
                #print('Peaks Gradient',peaksGrad)
                
                if len(peaks)>0:
                    #Find all the peaks of the first derivative that are before the most prominent peak
                    indices = np.where((peaksGrad < peaks[-1]))
                    peaksGradCut = peaksGrad[indices]
                
                    #Find all the peaks of the second derivative before the most prominent peak and the last gradient peak
                    if len(peaksGradCut)>0:
                        indices = np.where((peaksGrad2 < peaksGradCut[-1]))
                        peaksGrad2Cut = peaksGrad2[indices]
                    else:
                        indices = np.where((peaksGrad2 < peaks[-1]))
                        peaksGrad2Cut = peaksGrad2[indices]
                
                    if len(peaksGrad2Cut) > 0:
                        interface = peaksGrad2Cut[-1]
                        if channel in ["A","B","C","D","E","F"]:
                            interface -= 10
                        interfaces.append(interface)
                        interfaceFound = True
                    elif len(inversePeaks)> 0:
                    #if len(inversePeaks)> 0:
                        if inversePeaks[0]<peaks[-1]:
                            interface = inversePeaks[0]
                            if channel in ["A","B","C","D","E","F"]:
                                interface -= 10
                            interfaces.append(interface)
                            interfaceFound = True
                else:
                    #error += ", No peaks found in channel " + channel
                    #print(error)
                    print( "No peaks found in channel " + channel)

                    # print('Channel',channel)
                    # print('Peaks',peaks)
                    # print('Peaks gradient cut', peaksGrad)
                    # #print('Peaks gradient cut properties', properties)
                    # print('Peaks gradient 2 cut',peaksGrad2Cut)
                    # #print('Peaks properties',properties)
                    # print('InversePeaks',inversePeaks)

            if interfaceFound:      
                print(interfaces)             
                finalInterface = np.median(interfaces)
                #finalInterface = stat.mode(interfaces)[0][0]
                print('InterfacesList', interfaces)
                print("Final Interface:", finalInterface)
                interfacePosition = finalInterface

            else:
                error += ", Interface not found, no peaks found"
                interfacePosition = 0.0


        if liquidType is LiquidType.dichloro:
            logging.info("Finding dicholoromethane interface")
    
            interfaceFound = False
            error = ""  
            
            df = dataLight
            df[["A","B","C","D","E","F","G","H","I","J","K","L","R","S","T","U","V","W"]] = df[["A","B","C","D","E","F","G","H","I","J","K","L","R","S","T","U","V","W"]].apply(pd.to_numeric)
            print(df)

            #Normalize all channels
            df[["A","B","C","D","E","F","G","H","I","J","K","L","R","S","T","U","V","W"]] = df[["A","B","C","D","E","F","G","H","I","J","K","L","R","S","T","U","V","W"]].apply(lambda x: x/x.max(), axis=0)
            
            smoothWindowSize= 3
            smoothProminence = 1/2
            #inverseSmoothProminence =1/15
            gradient2Prominence=1/3
            offset= 2
    

            interfaces = []
            interfaceFound = False
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
                
                #Find the max value of the gradient2 data to find the peaks
                maxValue2 = np.max(gradient2)
                
                peaksGrad2 , _ =  sig.find_peaks(gradient2, prominence = gradient2Prominence*maxValue2)
                
                
                if len(peaksGrad2)>0:
                    interface = peaksGrad2[0]+offset    
                    if channel in ["A","B","C","D","E","F"]:
                        interface -= 10
                    interfaces.append(interface)
                    interfaceFound = True 
                elif len(peaks)>0:
                    interface = peaks[-1]+offset    
                    if channel in ["A","B","C","D","E","F"]:
                        interface -= 10
                    interfaces.append(interface)
                    interfaceFound = True 
                else:
                    #error += ", No peaks found in channel " + channel
                    #print(error)
                    print("No peaks found in channel " + channel)

            if interfaceFound: 
                finalInterface = np.median(interfaces)
                #finalInterface = stat.mode(interfaces)[0][0]
                print('InterfacesList', interfaces)
                print("Final Interface:", finalInterface)
                interfacePosition = finalInterface
            else:
                error += ",No interfaces found"
                print(error)
                interfacePosition = 0.0


    return interfaceFound, interfacePosition, error



#Drain phases
async def drain(portLower: int, portUpper: int) -> str:
    await drainLowerPhase(portLower)
    await drainUpperPhase(portUpper)

    return "All phases drained"

def startPump(speed:int,dir:bool):
    global pumpDirection
    if pumpDirection != dir:
        DrainDriver.changePumpDirection()
        pumpDirection = dir
    print("Direction checked")
    DrainDriver.drainSpeed(speed)
    print("Pump started")
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
def detectInterfaceTubingWindow(window, threshold):
    detected = False
    index = 0

    for i in range(window.shape[1]):
        PeaksChannel, _ = sig.find_peaks(window[:, i], height=threshold)
        # display(window[:,i])
        negPeaksChannel, _ = sig.find_peaks(-window[:, i], height=threshold)
        if negPeaksChannel.size > 0:
            print("Neg Peaks", negPeaksChannel)
            index = 8 - negPeaksChannel[-1] + 2
            # index = negPeaksChannel[-1]
            print(index, i)
            detected = True
            break

        if PeaksChannel.size > 0:
            print("Pos Peaks", PeaksChannel)
            index = 8 - PeaksChannel[-1] + 2
            # index = PeaksChannel[-1]
            print(index, i)
            detected = True
            break

    return detected, index


def findInterfaceTubing(df, detected, threshold, normalizingBounds):
    channels = ["R", "S", "T", "U", "V", "W"]
    for i in range(6):
        df[channels[i]] = df[channels[i]] / normalizingBounds[i]
    readingCurrent = df.to_numpy()

    interfaceIndex = -1

    if (len(readingCurrent) > 10):
        # readingArray = ndimage.uniform_filter1d(readingCurrent, size=3)
        readingArray = readingCurrent
        readingGr = np.gradient(readingArray, edge_order=1, axis=0)
        if (not detected):
            window = readingGr[-10:-1, :]
            detected, index = detectInterfaceTubingWindow(window, threshold)
            # print(detected,index)
            if detected:
                interfaceIndex = len(readingGr) - index

    return detected, interfaceIndex

async def drainToLowestDetectionPoint(port: int, interfacePosition: float)->(int,float,float,float,str):
    global pumpDirection,lowestDetectionPoint

    mlToDrain = getVolumeLowerPhase(interfacePosition)

    moveValveToPort(port)
    if not pumpDirection:
        DrainDriver.changePumpDirection()
        pumpDirection = not pumpDirection

    mlToDrain = mlToDrain - lowestDetectionPoint

    if mlToDrain <= 0:
        logging.info("Already at or beyond lowest detection point")
        return port, mlToDrain, 0, 0, False, "Already at or beyond lowest detection point"

    secondsToDrain, conversionFactor = convertMlToSeconds(mlToDrain,100)

    logging.info("interfacePosition = " + str(interfacePosition))
    logging.info("mlToDrain = " + str(mlToDrain))
    logging.info("secondsToDrain = " + str(secondsToDrain))
    logging.info("pumpSpeed = " + str(100))

    DrainDriver.drainSpeed(100)
    await asyncio.sleep(secondsToDrain)  # 66 around 100ml
    DrainDriver.stopDraining()

    return port, mlToDrain, conversionFactor, secondsToDrain, True, ""




async def drainLowerPhase(port : int, interfacePosition : float, tubingSensor : bool = False, bottomSensor : bool = False) -> str:
    global lowerPhaseDrained,pumpDirection

    mlToDrain = getVolumeLowerPhase(interfacePosition)

    moveValveToPort(port)
    if not pumpDirection:
        DrainDriver.changePumpDirection()
        pumpDirection = not pumpDirection

    secondsToDrain, conversionFactor = convertMlToSeconds(mlToDrain,100)

    logging.info("interfacePosition = " + str(interfacePosition))
    logging.info("mlToDrain = " + str(mlToDrain))
    logging.info("secondsToDrain = " + str(secondsToDrain))
    logging.info("pumpSpeed = " + str(100))

    start = 0
    folderPath = None
    fileName = None
    fileNameRaw = None

    readings = None
    readingsRaw = None
    detected = False

    normalizingBounds = [3562.50048828125, 1112.6715087890625, 354.029541015625, 194.21142578125,
                         208.8236389160156, 97.33015441894533]
    threshold = 0.025


    if tubingSensor:
        print("Using tubing sensor")
        # Folder and file names
        with open(os.path.dirname(__file__) + '/countTubing.txt', "r") as counterFile:
            start = int(counterFile.read())

        with open(os.path.dirname(__file__) + '/countTubing.txt', "w") as counterFile:
            counterFile.write(str(start + 1))

        folderPath = dataPath + 'Tubing' + str(start)
        os.mkdir(folderPath)

        fileName = folderPath + '/data.csv'  # name of the CSV file generated
        fileNameRaw = folderPath + '/dataRAW.csv'  # name of the CSV file generated

        readings = None
        readingsRaw = None
        detected = False

        print("Creating tubing files")

    loop = asyncio.get_running_loop()
    startTime = loop.time()
    print("Start time " + str(startTime))
    currentTime = loop.time()

    #Start pump at the slowest speed and wait for secondsToDrain
    DrainDriver.drainSpeed(100)
    while((currentTime - startTime ) <= secondsToDrain):

        if bottomSensor and ((currentTime - startTime) >= secondsToDrain*0.75):
            pass

        if tubingSensor and ((currentTime - startTime) >= secondsToDrain*0.5):

            result = TubingSensorDriver.takeMeasurement()

            if readings is None:
                readings = [[]]
                readings[0] = result[0]
                readingsRaw = [[]]
                readingsRaw[0] = result[1]
            else:
                readings.append(result[0])
                readingsRaw.append(result[1])

            print("Taking tubing measurement")

            column_names = ["R", "S", "T", "U", "V", "W"]
            df = pd.DataFrame(readings, columns=column_names)
            dfRaw = pd.DataFrame(readingsRaw, columns=column_names)

            df.to_csv(fileName, index=False)
            dfRaw.to_csv(fileNameRaw, index=False)

            if not detected:
                detected, interface = findInterfaceTubing(df, detected, threshold, normalizingBounds)
            print("Interface detected ", detected)
            print("Interface ", interface)

            if detected:
                break

        currentTime = loop.time()
        await asyncio.sleep(0.1)  # 66 around 100ml
    DrainDriver.stopDraining()
    # DrainDriver.setMlPerDrainStep(mlToDrain)
    # DrainDriver.drainStep()

    lowerPhaseDrained = True

    return port, mlToDrain, conversionFactor, secondsToDrain, ""


async def drainLowerPhaseLimits(port: int,interfacePosition:float) -> str:
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

    #try:
    moveValveToPort(port)
    if not pumpDirection:
        DrainDriver.changePumpDirection()
        pumpDirection = not pumpDirection
        
    for i in range(len(drainStages)):
            
        secondsToDrain, conversionFactor = convertMlToSeconds(drainStages[i],stageSpeed[i])

        secondsToDrain = secondsToDrain*(255/stageSpeed[i])
     
        logging.info("interfacePosition = " + str(interfacePosition))
        logging.info("mlToDrain = " + str(drainStages[i]))
        logging.info("secondsToDrain = " + str(secondsToDrain))
        logging.info("pumpSpeed = " + str(stageSpeed[i]))

        DrainDriver.drainSpeed(stageSpeed[i])
        await asyncio.sleep(secondsToDrain)#66 around 100ml
        DrainDriver.stopDraining()
            #DrainDriver.setMlPerDrainStep(mlToDrain)
            #DrainDriver.drainStep()

    lowerPhaseDrained = True
    #except serial.SerialException as e:
        #There is no new data from serial port readings
    #    return port, mlToDrain, conversionFactor, secondsToDrain, "drainLowerPhase: No data read from serial port"
    #except TypeError as e:
        #Disconnect of USB->UART occured
    #    return port, mlToDrain, conversionFactor, secondsToDrain, "drainLowerPhase: Serial port disconnected"

    return port, mlToDrain, conversionFactor, secondsToDrain, "" 


#Drain upper phase
async def drainUpperPhase(port: int) -> str:
    global lowerPhaseDrained, pumpDirection
    
    mlToDrain = 1000
    secondsToDrain, conversionFactor = convertMlToSeconds(mlToDrain,255)
    
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

    secondsToPump, conversionFactor = convertMlToSeconds(ml+tubingVolume,255)
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

    secondsToDrain, conversionFactor = convertMlToSeconds(ml,255)
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

#Helper function for calibration
async def drainTimeToPort(t: float,port: int,speed: int):
    global pumpDirection

    secondsToDrain = t
    logging.info("secondsToDrain = " + str(secondsToDrain))

    moveValveToPort(port)
    if not pumpDirection:
        DrainDriver.changePumpDirection()
        pumpDirection = not pumpDirection

    DrainDriver.drainSpeed(speed)
    await asyncio.sleep(secondsToDrain)#66 around 100ml
    DrainDriver.stopDraining()
    #DrainDriver.setMlPerDrainStep(mlToDrain)
    #DrainDriver.drainStep()

    return port, secondsToDrain, ""


def getImageDataFolderPath(idN: int)-> str:

    with open(os.path.dirname(__file__)+'/count.txt', "r") as counterFile:
        start = int(counterFile.read())-1

    if(idN <= start):
        folderPath = dataPath + str(idN)
        imageFolderPath = folderPath + '/'+ imageFolderName
        return imageFolderPath
    else:
        return "Data id does not exist"
    
def getLastImageDataFolderPath()-> str:

    with open(os.path.dirname(__file__)+'/count.txt', "r") as counterFile:
        start = int(counterFile.read())-1

    folderPath = dataPath + str(start)
    imageFolderPath = folderPath + '/'+ imageFolderName
    return imageFolderPath

async def drainMlToPortSpeed(ml: float,port: int, speed:int):
    global pumpDirection

    secondsToDrain, conversionFactor = convertMlToSeconds(ml,speed)
    logging.info("mlToDrain = " + str(ml))
    logging.info("secondsToDrain = " + str(secondsToDrain))

    moveValveToPort(port)
    if not pumpDirection:
        DrainDriver.changePumpDirection()
        pumpDirection = not pumpDirection

    DrainDriver.drainSpeed(speed)
    await asyncio.sleep(secondsToDrain)#66 around 100ml
    DrainDriver.stopDraining()
    #DrainDriver.setMlPerDrainStep(mlToDrain)
    #DrainDriver.drainStep()

    return port, ml, conversionFactor, secondsToDrain, ""




#Return last image data

#Return last sensor data