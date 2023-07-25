import pandas as pd
import os
import signal
import scipy.signal as sig
from scipy import ndimage
import time
import numpy as np



import TubingSensorDriverCmd as SensorDriver

index = 0
dataPath = os.path.dirname(__file__)
readings = None
readingsRaw = None
finish = False

def signal_handler(signal, frame):
  global finish
  finish = True 

signal.signal(signal.SIGINT, signal_handler)

def detectInterface(window):
    detected = False
    index = 0
    
    for i in range(window.shape[1]):
        PeaksChannel, _ = sig.find_peaks(window[:,i],prominence=0.03)
        #display(window[:,i])
        negPeaksChannel, _ = sig.find_peaks(-window[:,i],prominence=0.03)
        if negPeaksChannel.size > 0:
            print("Neg Peaks",negPeaksChannel)
            index = 8 - negPeaksChannel[-1] + 2
            #index = negPeaksChannel[-1]
            print(index,i)
            detected = True
            break
            
        if PeaksChannel.size > 0:
            print("Pos Peaks",PeaksChannel)
            index = 8 - PeaksChannel[-1] + 2
            #index = PeaksChannel[-1]
            print(index,i)
            detected = True
            break
    
    return detected, index


def findFirstDifference(df,detected,normalizingBounds):
    channels = ["R","S","T","U","V","W"]
    for i in range(6):
        df[channels[i]] = df[channels[i]]/normalizingBounds[i]
    readingCurrent = df.to_numpy()

    interfaceIndex = -1
    
    if(len(readingCurrent)>10):
        readingArray = ndimage.uniform_filter1d(readingCurrent, size=3)
        readingGr = np.gradient(readingArray,edge_order=1,axis=0)
        if (not detected):
            window = readingGr[-10:-1,:]
            detected,index = detectInterface(window)
            #print(detected,index)
            if detected:
                interfaceIndex = len(readingGr)-index

    return detected,interfaceIndex
            


#Get latest count number from file and update file
with open(dataPath+'/count.txt', "r") as counterFile:
    index = int(counterFile.read())

with open(dataPath+'/count.txt', "w") as counterFile:
    counterFile.write(str(index+1))


folderPath = dataPath + str(index)
os.mkdir(folderPath)

fileName = folderPath + '/data.csv' #name of the CSV file generated
fileNameRaw = folderPath + '/dataRAW.csv' #name of the CSV file generated

#data = [0,0,0,0,0,0]
detected = False
normalizingBounds = [3562.50048828125,1112.6715087890625,354.029541015625,194.21142578125,208.8236389160156,97.33015441894533]

while(True):
    result = SensorDriver.takeMeasurement()
    #reading = []
    
    # for i in range(len(data)):
    #     reading.append(data[i])
    #     data[i] = data[i] + 1

    if readings == None:
        readings  = [[]]
        readings[0] = result[0]
        readingsRaw  = [[]]
        readingsRaw[0] = result[1]
    else:
        readings.append(result[0])
        readingsRaw.append(result[1])

    print("Taking measurement")

    column_names = ["R","S","T","U","V","W"]
    df = pd.DataFrame(readings, columns = column_names)
    dfRaw = pd.DataFrame(readingsRaw, columns = column_names)

    df.to_csv(fileName,index=False)
    dfRaw.to_csv(fileNameRaw,index=False)

    #Normalize
    #df[["R","S","T","U","V","W"]] = df[["R","S","T","U","V","W"]].apply(lambda x: x/x.max(), axis=0)

    #detected , interface = findFirstDifference(df,detected,normalizingBounds)
    #print("Interface detected ",detected)
    #print("Interface ", interface)

    time.sleep(0.1)

    if(finish):
        print("Finish")
        break











