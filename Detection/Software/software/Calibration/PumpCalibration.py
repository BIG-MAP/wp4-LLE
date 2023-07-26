import time
import pandas as pd


#from software.Drivers.WeightMixer import WeightMixerDriver as WeightDriver
from software.API.FastAPI.BeltDrainLLE import LLEBeltDrainProcedures as LLEProc


def pump_calibration(port: int, speed: int, initial_volume: int, repetitions: int,pumping_time: int, results_file:str):

    #r = requests.get('http://127.0.0.1:8000/pumpFromPort/'+str(port)+'/'+str(initial_volume))
    LLEProc.pumpMlFromPort(initial_volume,port,0)

    # Start Weigh (tares the weight)
    # WeightDriver.start_Weight()

    # tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
    # while not ((tare or scale_stable) and scale_on):
    #    time.sleep(1)
    #    print("Not ready to weigh")
    #    tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
    print("Ready to weigh!")

    rows_list = []
    weightMeasure = 0

    for i in range(repetitions):
        #Drain for a specific amount of time
        LLEProc.drainTimeToPort(pumping_time,port,speed)

        #Measure weight
        # tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
        # while not ((tare or scale_stable) and scale_on):
        #     time.sleep(1)
        #     print("Not ready to weigh")
        #     tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
        # print("Taking weight measurement and saving it")
        # weightMeasure = WeightDriver.get_Weight_Value()

        rowDict = {'PumpSpeed': speed, 'Pumped time': pumping_time, 'Weight': weightMeasure}
        rows_list.append(rowDict)

    column_names = ['ExpectedVolume', 'Pumped time', 'Weight']
    results = pd.DataFrame(rows_list, columns=column_names)
    results.to_csv(results_file, index=False)

    # tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
    # while not ((tare or scale_stable) and scale_on):
    #     time.sleep(1)
    #     print("Not ready to weigh")
    #     tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()

    print("Draining last part")
    # weightMeasure = WeightDriver.get_Weight_Value()
    print("Before final volume", weightMeasure)

    LLEProc.drainMlToPortSpeed(500, 1, 255)


    average_volume_pumped = results['Weight'][0]
    for i in range(1,len(results.index)):
        diff = results['Weight'][i]-results['Weight'][i-1]
        average_volume_pumped +=  diff

    average_volume_pumped = average_volume_pumped/len(results.index)

    conversion_factor = pumping_time/average_volume_pumped

    with open('./conversion'+str(speed)+'.txt', "w") as counterFile:
        counterFile.write(str(conversion_factor))

def pump_calibration_check(port: int,volume: int, speed: int, repetitions: int,check_file :str):
    LLEProc.pumpMlFromPort(volume, port, 0)

    # Start Weigh (tares the weight)
    # WeightDriver.start_Weight()

    # tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
    # while not ((tare or scale_stable) and scale_on):
    #    time.sleep(1)
    #    print("Not ready to weigh")
    #    tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
    print("Ready to weigh!")

    rows_list = []
    weightMeasure = 0

    for i in range(repetitions):
        # Drain a specific volume
        LLEProc.drainMlToPortSpeed(volume, port, speed)

        # Measure weight
        # tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
        # while not ((tare or scale_stable) and scale_on):
        #     time.sleep(1)
        #     print("Not ready to weigh")
        #     tare, scale_on, scale_stable, scale_power_on, scale_overload = WeightDriver.get_Weight_Status()
        # print("Taking weight measurement and saving it")
        # weightMeasure = WeightDriver.get_Weight_Value()

        rowDict = {'PumpSpeed': speed, 'Pumped volume': volume, 'Weight': weightMeasure}
        rows_list.append(rowDict)

    column_names = ['ExpectedVolume', 'Pumped volume', 'Weight']
    results = pd.DataFrame(rows_list, columns=column_names)
    results.to_csv(check_file, index=False)

    average_volume_pumped = results['Weight'][0]
    for i in range(1, len(results.index)):
        diff = results['Weight'][i] - results['Weight'][i - 1]
        average_volume_pumped += diff

    average_volume_pumped = average_volume_pumped / len(results.index)

    print("Average volume pumped: "+str(average_volume_pumped))


def main():
    pump_calibration(port = 1,speed=255,initial_volume=10,repetitions=3,pumping_time=10,results_file='pumpingCalibration')
    pump_calibration_check(port=1,volume=10,speed=255,repetitions=3,check_file="pumpingCalibrationCheck")


if __name__ == "__main__":
    main()



