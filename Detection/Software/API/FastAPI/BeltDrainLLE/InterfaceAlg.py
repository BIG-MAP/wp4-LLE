import pandas as pd
import numpy as np
from scipy import ndimage
import scipy.signal as sig
import logging



def findInterfaceEthyl(dataLight, smoothWindowSize: int, smoothProminence: float, gradient2Prominence:float):
    logging.info("Starting find algorithm")
    
    interfaceFound = False  
    error = ""  
    
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
        logging.info("Peaks found", peaks)
                
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
        error = "Interface not found, no peaks found"
        interfacePosition = 0.0

    return interfaceFound, interfacePosition, error


def findInterfaceDichloro(dataLight, smoothWindowSize: int, smoothProminence: float, gradient2Prominence:float):
    
    interfaceFound = False  
    error = ""  
    
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
        error = "Interface not found, no peaks found"
        interfacePosition = 0.0

    return interfaceFound, interfacePosition, error