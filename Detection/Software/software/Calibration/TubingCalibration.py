import time
import pandas as pd
import asyncio

from software.API.FastAPI.BeltDrainLLE import LLEBeltDrainProcedures as LLEProc

def tubing_calibration(port:int,volume:float):
    rows_list = []

    #LLEProc.setLiquidType("ethyl")
    LLEProc.setLiquidType("dichloro")

    stopEvent = asyncio.Event()
    dataLight, dataLightRaw, idN, error = LLEProc.scanFunnel(initialLEDs=4, delta=16, travelDistance=169,
                                                             stopEvent=stopEvent)

    # Find interface
    interfaceFound, interfacePosition, error = LLEProc.findInterface(dataLight, 0, 0, 0)
    print("Interface found: " + str(interfaceFound))
    print("Interface position: " + str(interfacePosition))

    # Calculate volume
    volume = LLEProc.calculateVolumeRegression(interfacePosition)
    print("Volume: " + str(volume))

    input("Check interface position and volume results and press enter")

    asyncio.run(LLEProc.drainToLowestDetectionPoint(port,interfacePosition))

    input("Drained to lowest detectable position (400ml) press enter to continue")

    dataLight, dataLightRaw, idN, error = LLEProc.scanFunnel(initialLEDs=4, delta=16, travelDistance=169,
                                                             stopEvent=stopEvent)
    # Find interface
    interfaceFound, interfacePosition, error = LLEProc.findInterface(dataLight, 0, 0, 0)
    print("Interface found: " + str(interfaceFound))
    print("Interface position: " + str(interfacePosition))

    # Calculate volume
    volume = LLEProc.calculateVolumeRegression(interfacePosition)
    print("Volume: " + str(volume))

    input("Check interface position and volume results and press enter")

    asyncio.run(LLEProc.drainLowerPhase(port,interfacePosition+12,True,False))

    print("Check tubing sensor output")

def main():
    tubing_calibration(port = 2,volume=1000)


if __name__ == "__main__":
    main()




