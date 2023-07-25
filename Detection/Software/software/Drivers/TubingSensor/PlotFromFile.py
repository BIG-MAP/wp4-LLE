import matplotlib.pyplot as plt
import matplotlib.animation as animation
import seaborn as sns
import time
import os
import pandas as pd
import scipy.signal as sig
from scipy import ndimage
import numpy as np

index = 0
dataPath = os.path.dirname(__file__)

def detectInterface(window,threshold):
    detected = False
    index = 0
    
    for i in range(window.shape[1]):
        PeaksChannel, _ = sig.find_peaks(window[:,i],height=threshold)
        #display(window[:,i])
        negPeaksChannel, _ = sig.find_peaks(-window[:,i],height=threshold)
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


def findFirstDifference(df,detected,threshold,normalizingBounds):
    channels = ["R","S","T","U","V","W"]
    for i in range(6):
        df[channels[i]] = df[channels[i]]/normalizingBounds[i]
    readingCurrent = df.to_numpy()

    interfaceIndex = -1
    
    if(len(readingCurrent)>10):
        #readingArray = ndimage.uniform_filter1d(readingCurrent, size=3)
        readingArray = readingCurrent
        readingGr = np.gradient(readingArray,edge_order=1,axis=0)
        if (not detected):
            window = readingGr[-10:-1,:]
            detected,index = detectInterface(window,threshold)
            #print(detected,index)
            if detected:
                interfaceIndex = len(readingGr)-index

    return detected,interfaceIndex


#Get latest count number from file and update file
with open(dataPath+'/count.txt', "r") as counterFile:
    index = int(counterFile.read())
    index = index - 1

folderPath = dataPath + str(index)
fileName = folderPath + '/data.csv' #name of the CSV file generated

threshold = 0.025
normalizingBounds = [2000,450,150,80,125,60]#[3562.50048828125,1112.6715087890625,354.029541015625,194.21142578125,208.8236389160156,97.33015441894533]
detected = False
interface = -1

f, ax = plt.subplots(figsize=(15, 7))

def animate(i):
    global detected, interface
    try:
        df = pd.read_csv(fileName)
        if not detected:
            detected , interface = findFirstDifference(df,detected,threshold,normalizingBounds)
        print("Interface detected ",detected)
        print("Interface ", interface)
        ax.clear()
        sns.lineplot(data = df[["R","S","T","U","V","W"]],palette = 'bright',ax = ax)
        if detected:
            plt.axvline(x=interface,linestyle='--')
            plt.axvspan(interface-1, interface+1 ,0,1, alpha=0.2, color='green')
        #sns.lineplot(data = df[["T","U","V","W"]],palette='bright',ax = ax)
    except pd.errors.EmptyDataError as e:
        print("EmptyDataError")

    

ani = animation.FuncAnimation(f, animate, interval=500)
plt.show()

