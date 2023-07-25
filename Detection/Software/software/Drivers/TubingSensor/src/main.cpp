#include <Arduino.h>
#include "opticalAS726X.h"
#include <Adafruit_DotStar.h>
#include <SPI.h>
#include <CmdMessenger.h> // CmdMessenger

CmdMessenger cmdMessenger(Serial, ',', ';', '/');

#define NUMPIXELS 1 // Number of LEDs in strip

// Here's how to control the LEDs from any two pins:
#define DATAPIN 3
#define CLOCKPIN 2
Adafruit_DotStar strip(NUMPIXELS, DATAPIN, CLOCKPIN, DOTSTAR_BRG);

uint32_t color = 0xFF0000; // 'On' color (starts white)

bool bulb = false;



void OnUnknownCommand();
void OnWatchdogRequest();
void OnArduinoReady();
void OnGetSensorReading();
void OnLEDsOff();
void OnSetLEDBrightness();
void OnGetSensorType();
void OnToggleBulb();
void measure();
void setLEDBrightness(int led, int brightness);
void turnLEDsOff();



// This is the list of recognized commands. These can be commands that can either be sent or received.
// In order to receive, attach a callback function to these events
enum
{
  // Commands
  kWatchdog,                  // Command to request application ID
  kAcknowledge,               // Command to acknowledge a received command
  kError,                     // Command to message that an error has occurred
  kGetSensorReading,          // Command to trigger a sensor reading an get the result
  kGetSensorReadingResult,    // Command to respond to the get sensor reading command
  kGetSensorReadingResultRaw, //  Command to respond to the get sensor reading command with raw readings
  kToggleBulb,                // Command to toggle the use of the bulb
  kGetSensorType,                // Command to return the type of sensor connected
  kGetSensorTypeResult,                // Command to return the type of sensor connected
  kSetLEDBrightness,          //  Command to turn on the LED with an specific brigthness
  kLEDsOff,                   // Command to turn off all LEDs on the strip
};

// Commands we send from the PC and want to receive on the Arduino.
// We must define a callback function in our Arduino program for each entry in the list below.
void attachCommandCallbacks()
{
  // Attach callback methods
  cmdMessenger.attach(OnUnknownCommand);
  cmdMessenger.attach(kWatchdog, OnWatchdogRequest);
  cmdMessenger.attach(kLEDsOff, OnLEDsOff);
  cmdMessenger.attach(kGetSensorReading, OnGetSensorReading);
  cmdMessenger.attach(kSetLEDBrightness, OnSetLEDBrightness);
  cmdMessenger.attach(kGetSensorType, OnGetSensorType);
  cmdMessenger.attach(kToggleBulb, OnToggleBulb);
}

// ------------------  C A L L B A C K S -----------------------

// Called when a received command has no attached function
void OnUnknownCommand()
{
  cmdMessenger.sendCmd(kError, "Command without attached callback");
}

void OnWatchdogRequest()
{
  // Will respond with same command ID and Unique device identifier.
  cmdMessenger.sendCmd(kWatchdog, "0000000-0000-0000-0000-00000000002");
}

// Callback function that responds that Arduino is ready (has booted up)
void OnArduinoReady()
{
  cmdMessenger.sendCmd(kAcknowledge, "Arduino ready");
}

void OnGetSensorReading()
{
  measure();
}

void OnLEDsOff()
{

  turnLEDsOff();
  // Send acknowledgment back to PC
  cmdMessenger.sendCmd(kAcknowledge, "Turned LEDs off");
}

void OnSetLEDBrightness()
{
  // Set the brightness for a specific LED (starts on 0), brightness between 0 and 255
  // int led = cmdMessenger.readInt16Arg();
  int led = cmdMessenger.readBinArg<int>();
  if (cmdMessenger.isArgOk())
  {
    if (led > 0)
    {
      led = 0;
    }
    else
    {
      if (led < 0)
      {
        led = 0;
      }
    }
  }

  // int brightness = cmdMessenger.readInt16Arg();
  int brightness = cmdMessenger.readBinArg<int>();

  if (cmdMessenger.isArgOk())
  {
    if (brightness > 255)
    {
      brightness = 255;
    }
    else
    {
      if (brightness < 0)
      {
        brightness = 0;
      }
    }
  }

  setLEDBrightness(led, brightness);

  // Send acknowledgment back to PC
  cmdMessenger.sendCmd(kAcknowledge, brightness);
}

void OnGetSensorType()
{
  cmdMessenger.sendCmdStart(kGetSensorTypeResult);

  cmdMessenger.sendCmdBinArg<uint8_t>(opticalSensor.version);

  cmdMessenger.sendCmdEnd();
}

void OnToggleBulb()
{
  if (bulb)
  {
    bulb = false;
    // Send acknowledgment back to PC
    cmdMessenger.sendCmd(kAcknowledge, "Turned off sensor bulb");
  }
  else
  {
    bulb = true;
    cmdMessenger.sendCmd(kAcknowledge, "Turned on sensor bulb");
  }
}

// ------------------ M A I N  ----------------------

void setup()
{
  // put your setup code here, to run once:
  Serial.begin(115200);
  while (!Serial);

  // Do not print newLine at end of command,
  // in order to reduce data being sent
  cmdMessenger.printLfCr(false);

  Wire.begin();
  opticalSensor.initialize();
  // opticalSensor.printHeaders();

  strip.begin(); // Initialize pins for output
  strip.show();  // Turn all LEDs off ASAP

  // Attach my application's user-defined callback methods
  attachCommandCallbacks();

  cmdMessenger.sendCmd(kAcknowledge, "Arduino has started!");
}

void loop()
{

  // Process incoming serial data, and perform callbacks
  cmdMessenger.feedinSerialData();
}

void measure()
{

  // Turn LED on
  strip.setPixelColor(0, color);
  strip.show();
  delay(100);

  opticalSensor.takeMeasurement(bulb);
  //opticalSensor.printMeasurement();

  // Turn LED off
  strip.setPixelColor(0, 0);
  strip.show();

  cmdMessenger.sendCmdStart(kGetSensorReadingResult);

  cmdMessenger.sendCmdBinArg<float>(opticalSensor.readings[0]);
  cmdMessenger.sendCmdBinArg<float>(opticalSensor.readings[1]);
  cmdMessenger.sendCmdBinArg<float>(opticalSensor.readings[2]);
  cmdMessenger.sendCmdBinArg<float>(opticalSensor.readings[3]);
  cmdMessenger.sendCmdBinArg<float>(opticalSensor.readings[4]);
  cmdMessenger.sendCmdBinArg<float>(opticalSensor.readings[5]);

  cmdMessenger.sendCmdEnd();

  cmdMessenger.sendCmdStart(kGetSensorReadingResultRaw);

  cmdMessenger.sendCmdBinArg<uint16_t>(opticalSensor.rawReadings[0]);
  cmdMessenger.sendCmdBinArg<uint16_t>(opticalSensor.rawReadings[1]);
  cmdMessenger.sendCmdBinArg<uint16_t>(opticalSensor.rawReadings[2]);
  cmdMessenger.sendCmdBinArg<uint16_t>(opticalSensor.rawReadings[3]);
  cmdMessenger.sendCmdBinArg<uint16_t>(opticalSensor.rawReadings[4]);
  cmdMessenger.sendCmdBinArg<uint16_t>(opticalSensor.rawReadings[5]);

  cmdMessenger.sendCmdEnd();
}

void setLEDBrightness(int led, int brightness)
{

  color = (uint32_t)brightness << 16;
  // Serial.print("Color");
  // Serial.println(color, HEX);
  // Serial.print("Brightness ");
  // Serial.println(brightness, DEC);

  strip.setPixelColor(led, color);
  strip.show();
  delay(20);
}

void turnLEDsOff()
{

  strip.setPixelColor(0, 0);
  strip.show();
}
