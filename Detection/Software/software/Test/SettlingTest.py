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

def settling_test(settlingTime:int,scanInterval:int):
    print("Settling")
    r = requests.post('http://127.0.0.1:8000/startSettling',
                      json={'settlingSettings': {'scanInterval': scanInterval, 'settlingTime': settlingTime}})
    check_finished()

def main():
    settling_test(settlingTime=54000,scanInterval=3600)


if __name__ == "__main__":
    main()