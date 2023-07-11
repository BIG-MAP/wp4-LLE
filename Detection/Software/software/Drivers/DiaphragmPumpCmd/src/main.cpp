#include <Arduino.h>
#include <Wire.h>
#include "Aptinex_MCP4725.h"
#include <CmdMessenger.h> // CmdMessenger

// Defines

#define DAC_I2C_ADDRESS 0x60
#define CYCLE_PIN  6

// Objects and fields

CmdMessenger cmdMessenger(Serial, ',', ';', '/');

Aptinex_MCP4725 dac;

uint16_t voltage = 0;

bool pumpStarted = false;

// Functions

void OnUnknownCommand();
void OnWatchdogRequest();
void OnArduinoReady();
void OnSetVoltage();
void OnStopPump();
void OnCyclePump();
void setDAC(int setPoint);
void cyclePump();

// This is the list of recognized commands. These can be commands that can either be sent or received.
// In order to receive, attach a callback function to these events
enum
{
  // Commands
  kWatchdog,                  // Command to request application ID
  kAcknowledge,               // Command to acknowledge a received command
  kError,                     // Command to message that an error has occurred
  kSetVoltage,                // Command to set the voltage of the DAC
  kStopPump,                  // Command to stop the pump
  kCyclePump,                 // Command to cycle the pump
};

// Commands we send from the PC and want to receive on the Arduino.
// We must define a callback function in our Arduino program for each entry in the list below.
void attachCommandCallbacks()
{
  // Attach callback methods
  cmdMessenger.attach(OnUnknownCommand);
  cmdMessenger.attach(kWatchdog, OnWatchdogRequest);
  cmdMessenger.attach(kSetVoltage, OnSetVoltage);
  cmdMessenger.attach(kStopPump, OnStopPump);
  cmdMessenger.attach(kCyclePump, OnCyclePump);


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
  cmdMessenger.sendCmd(kWatchdog, "0000000-0000-0000-0000-00000000003");
}

// Callback function that responds that Arduino is ready (has booted up)
void OnArduinoReady()
{
  cmdMessenger.sendCmd(kAcknowledge, "Arduino ready");
}

void OnSetVoltage()
{
    //Set the number of LEDs to turn on (Starts on 0)
  int recv = cmdMessenger.readBinArg<int>();
  
  if (cmdMessenger.isArgOk()) {
       if(recv>4095){
        voltage = 4095;
      }else{
        if(recv<0){
          voltage = 0;
        }else{
          voltage = recv;
        }
      }
  }

  setDAC(voltage);

  cmdMessenger.sendCmd(kAcknowledge, voltage);
}

void OnStopPump()
{
  setDAC(0);
  if(pumpStarted){
    cyclePump();
    pumpStarted = false;
  }
  // Send acknowledgment back to PC
  cmdMessenger.sendCmd(kAcknowledge, "Pump Stopped");
}


void OnCyclePump(){

    cyclePump();

    pumpStarted = !pumpStarted;

     cmdMessenger.sendCmd(kAcknowledge, "Cycling pump");  
}

/*****************************************************************/
/***********************SETUP*************************************/

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  //while (!Serial);

  // Do not print newLine at end of command,
  // in order to reduce data being sent
  cmdMessenger.printLfCr(false);
  
  pinMode(CYCLE_PIN,OUTPUT);
  
  dac.begin(DAC_I2C_ADDRESS);
  dac.setVoltage(0,false);

  // Attach my application's user-defined callback methods
  attachCommandCallbacks();

  cmdMessenger.sendCmd(kAcknowledge, "Arduino has started!");
}

void loop() {
  // Process incoming serial data, and perform callbacks
  cmdMessenger.feedinSerialData();
}

void setDAC(int setPoint){
   
   dac.setVoltage(setPoint,false);
   delay(100);

}

void cyclePump(){

  digitalWrite(CYCLE_PIN,HIGH);
  delay(100);
  digitalWrite(CYCLE_PIN,LOW);
}