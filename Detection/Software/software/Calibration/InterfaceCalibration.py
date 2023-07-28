import time
import pandas as pd
import asyncio


from software.Drivers.WeightMixer import WeightMixerDriver as WeightDriver
from software.API.FastAPI.BeltDrainLLE import LLEBeltDrainProcedures as LLEProc


def interface_volume_calibration(port: int, initial_volume: float,repetitions:int, volume_step:float, results_file: str):
    rows_list = []
    # Load water
    asyncio.run(LLEProc.pumpMlFromPort(initial_volume, port, 0))

    # Scan funnel
    LLEProc.setLiquidType("dichloro")
    stopEvent = asyncio.Event()
    dataLight, dataLightRaw, idN, error = LLEProc.scanFunnel(initialLEDs=4,delta=16,travelDistance=169,stopEvent=stopEvent)

    # Find interface
    interfaceFound, interfacePosition, error = LLEProc.findInterface(dataLight,0,0,0)
    print("Interface found: " + str(interfaceFound))
    print("Interface position: " + str(interfacePosition))

    # Calculate volume
    volume = LLEProc.calculateVolumeRegression(interfacePosition)
    print("Volume: "+str(volume))

    # Start Weigh (tares the weight)
    WeightDriver.start_Weight()
    time.sleep(5)

    tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
    while not ((tare or scale_stable) and scale_on):
        time.sleep(1)
        print("Not ready to weigh")
        tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
    print("Ready to weigh!")

    rowDict = {'interfaceFound': interfaceFound, "interfacePosition": interfacePosition, 'volume': volume, 'Weight': 0}
    rows_list.append(rowDict)

    for i in range(repetitions):
        asyncio.run(LLEProc.drainMlToPortSpeed(volume_step, port, 255))

        # Measure weight
        tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
        while not ((tare or scale_stable) and scale_on):
            time.sleep(1)
            print("Not ready to weigh")
            tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
        print("Taking weight measurement and saving it")
        weightMeasure = WeightDriver.get_Weight_Value()

        # Scan funnel
        dataLight, dataLightRaw, idN, error = LLEProc.scanFunnel(initialLEDs=4, delta=16, travelDistance=169, stopEvent=stopEvent)

        # Find interface
        interfaceFound, interfacePosition, error = LLEProc.findInterface(dataLight, 0, 0, 0)
        print("Interface found: " + str(interfaceFound))
        print("Interface position: " + str(interfacePosition))

        # Calculate volume
        volume = LLEProc.calculateVolumeRegression(interfacePosition)
        print("Volume: " + str(volume))

        rowDict = {'interfaceFound': interfaceFound, "interfacePosition": interfacePosition, 'volume': volume,
                   'Weight': weightMeasure}
        rows_list.append(rowDict)

    column_names = ['interfaceFound', "interfacePosition", 'volume' , 'Weight']
    results = pd.DataFrame(rows_list, columns=column_names)
    results = results.apply(pd.to_numeric)
    results.to_csv(results_file, index=False)

def main():
    interface_volume_calibration(port=1,initial_volume=2500,repetitions=5,volume_step=300,results_file="interface_calibration.csv")


if __name__ == "__main__":
    main()







