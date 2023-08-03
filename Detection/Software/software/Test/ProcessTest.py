import time
import requests

# global variables
ip = "http://127.0.0.1:8000"

def check_finished():
    finished = False
    time.sleep(1)

    r = requests.get(ip + '/status')
    result = r.json()
    while result['status'] != 'finished':
        print("Status: " + result['status'])
        r = requests.get(ip + '/status')
        result = r.json()
        time.sleep(2)

    print("Status: " + str(r.json()['status']))


def extraction_process(iterations:int, liquid_type: str, input_port: int, waste_port_ethyl: int,waste_port_dichloro:int, initial_volume: float,extra_ml_ethyl:int,test_mode:bool=False):
    if test_mode:
        print("Starting extraction process in test mode!!!!!!!!!")


    for i in range(iterations):
        # Pump mixture from input port
        print("Pumping from port " + str(input_port) + " to funnel")
        r = requests.get(ip + '/pumpFromPort/' + str(input_port) + '/' + str(initial_volume))
        print("API response: " + str(r.json()))
        check_finished()

        # Start the settling process
        print("Settling")
        r = requests.post(ip + '/startSettling', json={'settlingSettings': {'scanInterval': 20, 'settlingTime': 30}})
        check_finished()

        print("Getting data")
        r = requests.get(ip + '/imageData')

        print("Finding Interface")
        r = requests.post(ip + '/startScanFind/ethyl')
        check_finished()

        print("Get resulting interface")
        r = requests.get(ip + '/results')
        result = r.json()
        interfaceFound = result['results']['interfaceResult']['interfaceFound']
        interfacePosition = result['results']['interfaceResult']['interfacePosition']
        scanTime = result['results']['interfaceResult']['lastScanTime']
        print("Interface Found: " + str(interfaceFound))
        print("Interface position: " + str(interfacePosition))
        print("Last scan time : " + str(scanTime))

        print("Draining until lowest detectable point")
        r = requests.get(ip + '/DrainLowerToLowestDetectionPoint/'+str(input_port))
        check_finished()

        print("Finding Interface")
        r = requests.post(ip + '/startScanFind/ethyl')
        check_finished()

        print("Get resulting interface")
        r = requests.get(ip + '/results')
        result = r.json()
        interfaceFound = result['results']['interfaceResult']['interfaceFound']
        interfacePosition = result['results']['interfaceResult']['interfacePosition']
        scanTime = result['results']['interfaceResult']['lastScanTime']
        print("Interface Found: " + str(interfaceFound))
        print("Interface position: " + str(interfacePosition))
        print("Last scan time : " + str(scanTime))

        if test_mode:
            print("setting interface position for test mode")
            r = requests.put(ip + '/setInterfacePosition/3')
            print("API response: " + str(r.json()))

        print("Draining lower layer")
        r = requests.get(ip + '/DrainLowerLayer/'+str(input_port))
        check_finished()

        if i < 2:
            # This is only for the first and second interation
            print("Drain some ml more in the first iteration")
            r = requests.get(ip + '/drainToPort/'+ str(input_port) + '/'+str(extra_ml_ethyl))
            check_finished()

        print("Draining upper layer")
        r = requests.get(ip + '/drainToPort/'+ str(waste_port_ethyl) + '/3')
        #r = requests.get(ip + '/DrainUpperLayer/' + str(waste_port_ethyl))
        check_finished()

        print("Finished iteration "+str(i))

    print("Finished extraction process")


def main():
    extraction_process(iterations=3,liquid_type="ethyl",input_port=1,waste_port_ethyl=3,waste_port_dichloro=4,initial_volume=4,extra_ml_ethyl=9,test_mode=True)



if __name__ == "__main__":
    main()