import time
import requests


def check_finished():
    finished = False
    time.sleep(1)

    r = requests.get('http://127.0.0.1:8000/status')
    result = r.json()
    while result['status'] != 'finished':
        print("Status: " + result['status'])
        r = requests.get('http://127.0.0.1:8000/status')
        result = r.json()
        time.sleep(2)

    print("Status: " + str(r.json()['status']))


def extraction_process(liquid_type: str, input_port: int, waste_port: int, initial_volume: float):

    # Pump mixture from input port
    print("Pumping from port " + str(input_port) + " to funnel")
    r = requests.get('http://127.0.0.1:8000/pumpFromPort/' + str(input_port) + '/' + str(initial_volume))
    check_finished()

    # Start the settling process
    print("Settling")
    r = requests.post('http://127.0.0.1:8000/startSettling', json={'settlingSettings': {'scanInterval': 20, 'settlingTime': 30}})
    check_finished()

    print("Getting data")
    r = requests.get('http://127.0.0.1:8000/imageData')

    print("Finding Interface")
    r = requests.post('http://127.0.0.1:8000/startScanFind/ethyl')
    check_finished()

    print("Get resulting interface")
    r = requests.get('http://127.0.0.1:8000/results')
    result = r.json()
    print("Interface Found: " + str(result['results']['interfaceResult']['interfaceFound']))
    print("Interface position: " + str(result['results']['interfaceResult']['interfacePosition']))
    print("Last scan time : " + str(result['results']['interfaceResult']['lastScanTime']))

    print("Setting interface")

    print("Draining lower layer")

    print("Draining upper layer")








def main():
    extraction_process(liquid_type="ethyl",input_port=1,waste_port=3,initial_volume=10)


if __name__ == "__main__":
    main()