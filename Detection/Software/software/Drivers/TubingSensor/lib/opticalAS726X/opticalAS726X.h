#ifndef OPTICAL
#define OPTICAL

#include <Arduino.h>
#include "Wire.h"
#include "AS726X.h"

class SensorAS726X{
     public:
        bool present = false;
        uint8_t version = 0;
        uint8_t temperature = 0;
        float readings[6] = {0.0,0.0,0.0,0.0,0.0,0.0};
        int rawReadings[6] {0,0,0,0,0,0};
        AS726X sensor;

    void takeMeasurement(bool bulb);
    void printHeaders();
    void printMeasurement();
    void printMeasurementRaw();
    void initialize();
};

extern SensorAS726X opticalSensor;

#endif