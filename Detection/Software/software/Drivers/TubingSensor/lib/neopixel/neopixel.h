#ifndef NEOPIXEL
#define NEOPIXEL

#include <Arduino.h>
#include <Adafruit_DotStar.h>

class NeopixelStrip{
     public:
        uint32_t color = 0xFF0000;      // 'On' color (starts red)


    void takeMeasurement(bool bulb);
    void printHeaders();
    void printMeasurement();
    void printMeasurementRaw();
    void initialize();
};




#endif