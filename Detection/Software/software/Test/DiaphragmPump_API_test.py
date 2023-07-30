import pytest
import requests
import time

# assuming your FastAPI application is running on localhost port 8000
BASE_URL = "http://localhost:8000"

@pytest.mark.run(order=1)
def test_root_path():
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    assert response.json() == {"name": "Diaphragm Pump", "Device id": 2}
    time.sleep(10)

@pytest.mark.run(order=2)
def test_start():
    response = requests.get(f"{BASE_URL}/start")
    assert response.status_code == 200
    assert response.json()['status'] == 'running'
    time.sleep(10)


@pytest.mark.run(order=3)
def test_set():
    settings = {"speed": 1000, "run": True}
    response = requests.post(f"{BASE_URL}/set", json=settings)
    assert response.status_code == 200
    assert response.json()['status'] == 'running'
    print("Did the pump start?")
    time.sleep(10)
@pytest.mark.run(order=4)
def test_set_speed():
    speed = 4096
    response = requests.get(f"{BASE_URL}/setSpeed/{speed}")
    assert response.status_code == 200
    assert response.json()['status'] == 'running'
    print("Did the pump start running faster ?")
    time.sleep(10)

@pytest.mark.run(order=5)
def test_stop():
    response = requests.get(f"{BASE_URL}/stop")
    assert response.status_code == 200
    assert response.json()['status'] == 'stopped'
    print("Did the pump stop?")
    time.sleep(10)

# Run the test with pytest
#pytest -v -s Detection\Software\software\Test\DiaphragmPump_API_test.py

