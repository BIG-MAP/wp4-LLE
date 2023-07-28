import time
import pandas as pd
import asyncio


from software.Drivers.WeightMixer import WeightMixerDriver as WeightDriver
from software.API.FastAPI.BeltDrainLLE import LLEBeltDrainProcedures as LLEProc


def pump_calibration(port: int, speed: int, initial_volume: int, repetitions: int,pumping_time: int, results_file:str):

    #r = requests.get('http://127.0.0.1:8000/pumpFromPort/'+str(port)+'/'+str(initial_volume))
    asyncio.run(LLEProc.pumpMlFromPort(initial_volume,port,0))
    time.sleep(2)

    # Start Weigh (tares the weight)
    WeightDriver.start_Weight()
    time.sleep(5)

    tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
    while not ((tare or scale_stable) and scale_on):
       time.sleep(1)
       print("Not ready to weigh")
       tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
    print("Ready to weigh!")


    rows_list = []
    weightMeasure = 0

    for i in range(repetitions):
        #Drain for a specific amount of time
        asyncio.run(LLEProc.drainTimeToPort(pumping_time,port,speed))

        #Measure weight
        tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
        while not ((tare or scale_stable) and scale_on):
            time.sleep(1)
            print("Not ready to weigh")
            tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
        print("Taking weight measurement and saving it")
        weightMeasure = WeightDriver.get_Weight_Value()

        rowDict = {'PumpSpeed': speed, 'Pumped time': pumping_time, 'Weight': weightMeasure}
        rows_list.append(rowDict)

    column_names = ['ExpectedVolume', 'Pumped time', 'Weight']
    results = pd.DataFrame(rows_list, columns=column_names)
    results = results.apply(pd.to_numeric)
    results.to_csv(results_file, index=False)

    tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
    while not ((tare or scale_stable) and scale_on):
        time.sleep(1)
        print("Not ready to weigh")
        tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
    weightMeasure = WeightDriver.get_Weight_Value()
    print("Draining last part")
    print("Before final volume", weightMeasure)

    #asyncio.run(LLEProc.drainMlToPortSpeed(20, 1, 255))


    average_volume_pumped = results['Weight'][0]
    for i in range(1,len(results.index)):
        diff = results['Weight'][i]-results['Weight'][i-1]
        average_volume_pumped +=  diff

    average_volume_pumped = average_volume_pumped/len(results.index)

    conversion_factor = pumping_time/average_volume_pumped

    print("Conversion factor: " + str(conversion_factor))

    with open('./conversion'+str(speed)+'.txt', "w") as counterFile:
        counterFile.write(str(conversion_factor))

def pump_calibration_check(port: int,volume: int, volume_step:int, speed: int, repetitions: int,check_file :str):
    print(asyncio.run(LLEProc.pumpMlFromPort(volume, port, 0)))

    # Start Weigh (tares the weight)
    WeightDriver.start_Weight()
    time.sleep(5)

    tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
    while not ((tare or scale_stable) and scale_on):
       time.sleep(1)
       print("Not ready to weigh")
       tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
    print("Ready to weigh!")

    rows_list = []
    weightMeasure = 0

    for i in range(repetitions):
        # Drain a specific volume
        asyncio.run(LLEProc.drainMlToPortSpeed(volume_step, port, speed))

        # Measure weight
        tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
        while not ((tare or scale_stable) and scale_on):
            time.sleep(1)
            print("Not ready to weigh")
            tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
        print("Taking weight measurement and saving it")
        weightMeasure = WeightDriver.get_Weight_Value()

        rowDict = {'PumpSpeed': speed, 'Pumped volume': volume, 'Weight': weightMeasure,'Volume_step':volume_step}
        rows_list.append(rowDict)

    column_names = ['PumpSpeed', 'Pumped volume', 'Weight','Volume_step']
    results = pd.DataFrame(rows_list, columns=column_names)
    results = results.apply(pd.to_numeric)
    results.to_csv(check_file, index=False)

    average_volume_pumped = results['Weight'][0]
    for i in range(1, len(results.index)):
        diff = results['Weight'][i] - results['Weight'][i - 1]
        average_volume_pumped += diff

    average_volume_pumped = average_volume_pumped / len(results.index)

    print("Average volume pumped: "+str(average_volume_pumped))


def main():
    pump_calibration(port = 1,speed=130,initial_volume=1,repetitions=5,pumping_time=100,results_file='pumpingCalibration130.csv')
    #pump_calibration(port=1, speed=255, initial_volume=1100, repetitions=4, pumping_time=240,results_file='pumpingCalibration.csv')
    pump_calibration_check(port=1,volume=0,speed=130,volume_step=100,repetitions=2,check_file="pumpingCalibrationCheck130.csv")


if __name__ == "__main__":
    main()



