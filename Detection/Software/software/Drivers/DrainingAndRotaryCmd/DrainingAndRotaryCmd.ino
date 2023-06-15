#include <Arduino.h>
#include "DRV8825.h"
//#include "SparkFun_AS7265X.h"
#include <CmdMessenger.h>  // CmdMessenger

CmdMessenger cmdMessenger(Serial,',',';','/');

// Motor steps per revolution. Most steppers are 200 steps or 1.8 degrees/step
#define MOTOR_STEPS 200
#define RPMVALVE 60
// Microstepping mode. If you hardwired it to save pins, set to the same value here.
#define MICROSTEPS 16

#define DIRPUMP 8
#define SPEEDPUMP 10
#define MAXSPEEDPUMP 11
#define ENAPUMP 9 

#define DIRVALVE 4
#define STEPVALVE 3
#define ENAVALVE 2

#define HOME 5
#define PORT 6


DRV8825 stepperValve(MOTOR_STEPS, DIRVALVE, STEPVALVE, ENAVALVE);

//AS7265X sensor;

boolean DEBUG = false;

//Draining Pump parameters
float mlPerDrain = 1;
float ml2MilisecondsMultiplier = 100;
bool rotationDir = true;

//Rotary valve parameters
bool homePort = false;
bool port = false;
int portNumber = 1;

// This is the list of recognized commands. These can be commands that can either be sent or received. 
// In order to receive, attach a callback function to these events
enum
{
  // Commands
  kWatchdog            , // Command to request application ID
  kAcknowledge         , // Command to acknowledge a received command
  kError               , // Command to message that an error has occurred
  kDrainMl        , // Command to drain a pre specified number of ml              
  kSetMlPerDrain        , // Command to set the ml per drain               
  kSetMl2MilisecondsMultiplier       , // Command to set the ml to degrees conversion multiplier  
  kChangePumpDirection  , // Command change the draining pump direction   
  kMoveToNextPort  , // Command to move rotary valve to the next port
  kMoveToHome  , // Command to move the rotary valve to the home port
  kGetPortNumber  , // Command to get the current rotary valve port number
  kGetPortNumberResult  , // Command to respond to the get port number command
  kDrainSpeed , // Command to drain continously at a certain speed
  kStopPump , // Command to stop the drain pump 
  kMoveToLastPort , //Command to move the rotary valve to the last port
  //kGetSensorReading  ,  // Command to trigger a sensor reading an get the result
  //kGetSensorReadingResult , // Command to respond to the get sensor reading command
  //kGetSensorReadingResultRaw  ,  //  Command to respond to the get sensor reading command with raw readings
};


// Commands we send from the PC and want to receive on the Arduino.
// We must define a callback function in our Arduino program for each entry in the list below.
void attachCommandCallbacks()
{
  // Attach callback methods
  cmdMessenger.attach(OnUnknownCommand);
  cmdMessenger.attach(kWatchdog, OnWatchdogRequest);
  cmdMessenger.attach(kDrainMl, OnDrainMl);
  cmdMessenger.attach(kSetMlPerDrain, OnSetMlPerDrain);
  cmdMessenger.attach(kSetMl2MilisecondsMultiplier, OnSetMl2MilisecondsMultiplier);
  cmdMessenger.attach(kChangePumpDirection, OnChangePumpDirection);
  cmdMessenger.attach(kMoveToNextPort, OnMoveToNextPort);
  cmdMessenger.attach(kMoveToHome, OnMoveToHome);
  cmdMessenger.attach(kGetPortNumber, OnGetPortNumber);
  cmdMessenger.attach(kDrainSpeed, OnDrainSpeed);
  cmdMessenger.attach(kStopPump, OnStopPump);
  cmdMessenger.attach(kMoveToLastPort, OnMoveToLastPort);
  //cmdMessenger.attach(kGetSensorReading, OnGetSensorReading);
}

// ------------------  C A L L B A C K S -----------------------

// Called when a received command has no attached function
void OnUnknownCommand()
{
  cmdMessenger.sendCmd(kError,"Command without attached callback");
}

void OnWatchdogRequest()
{
  // Will respond with same command ID and Unique device identifier.
  cmdMessenger.sendCmd(kWatchdog, "0000000-0000-0000-0000-00000000000");
}

// Callback function that responds that Arduino is ready (has booted up)
void OnArduinoReady()
{
  cmdMessenger.sendCmd(kAcknowledge,"Arduino ready");
}

void OnDrainMl()
{
  stopDrain();
  drainMl(mlPerDrain,rotationDir);

  // Send acknowledgment back to PC
  cmdMessenger.sendCmd(kAcknowledge,"Drained"); 
}

void OnSetMlPerDrain()
{
   float recv = cmdMessenger.readBinArg<float>();

   if (cmdMessenger.isArgOk()) {
       if(recv>140){
        mlPerDrain = 140;
      }else{
        if(recv<0){
          mlPerDrain = 0;
        }else{
          mlPerDrain = recv;
        }
      }

    // Send acknowledgment back to PC
    cmdMessenger.sendCmd(kAcknowledge,mlPerDrain); 
  } else {
    // Error in received goal temperature! Send error back to PC
    cmdMessenger.sendCmd(kError,"Error in received new ml per drain");
  }
}

void OnSetMl2MilisecondsMultiplier()
{
   float recv = cmdMessenger.readBinArg<float>();

   if (cmdMessenger.isArgOk()) {
       if(recv>1500){
        ml2MilisecondsMultiplier = 1500;
      }else{
        if(recv<0){
          ml2MilisecondsMultiplier = 0;
        }else{
          ml2MilisecondsMultiplier = recv;
        }
      }
      
    // Send acknowledgment back to PC
    cmdMessenger.sendCmd(kAcknowledge,ml2MilisecondsMultiplier); 
  } else {
    // Error in received goal temperature! Send error back to PC
    cmdMessenger.sendCmd(kError,"Error in received new ml to degrees multiplier");
  }
}

void OnChangePumpDirection()
{
  if(rotationDir){
       rotationDir = false;
     }else{
       rotationDir = true;  
     } 

  // Send acknowledgment back to PC
  cmdMessenger.sendCmd(kAcknowledge,"Changed pump direction"); 
}

void OnMoveToNextPort()
{
  moveToNexPort(true); 

  // Send acknowledgment back to PC
  cmdMessenger.sendCmd(kAcknowledge,portNumber); 
}

void OnMoveToHome()
{
  moveToHomePort();

  // Send acknowledgment back to PC
  cmdMessenger.sendCmd(kAcknowledge,portNumber); 
}

void OnGetPortNumber()
{
  // Send back the port number
  cmdMessenger.sendBinCmd(kGetPortNumberResult,portNumber);
  //cmdMessenger.sendCmdStart(kFloatAdditionResult);
  //cmdMessenger.sendCmdArg(a+b);
  //cmdMessenger.sendCmdArg(a-b);
  //cmdMessenger.sendCmdEnd(); 
}

void OnDrainSpeed(){
  //Drain at a certain speed
  int recv = cmdMessenger.readBinArg<int>();

  int pumpSpeed = 0;
  
  if (cmdMessenger.isArgOk()) {
       if(recv>255){
        pumpSpeed = 255;
      }else{
        if(recv<0){
          pumpSpeed = 0;
        }else{
          pumpSpeed = recv;
        }
      }
  }

   drainSpeed(pumpSpeed,rotationDir);

   cmdMessenger.sendCmd(kAcknowledge,"Draining");
   
}

void OnStopPump(){
  // Stop the draining pump
  stopDrain();

  cmdMessenger.sendCmd(kAcknowledge,"Stopped draining pump");  
}

void OnMoveToLastPort()
{
  moveToNexPort(false); 

  // Send acknowledgment back to PC
  cmdMessenger.sendCmd(kAcknowledge,portNumber); 
}



// ------------------ M A I N  ----------------------



void setup() {

  Serial.begin(115200);

  // Do not print newLine at end of command, 
  // in order to reduce data being sent
  cmdMessenger.printLfCr(false);

  pinMode(DIRPUMP, OUTPUT);
  pinMode(SPEEDPUMP, OUTPUT);
  pinMode(MAXSPEEDPUMP, OUTPUT);
  pinMode(ENAPUMP, OUTPUT);

  digitalWrite(DIRPUMP, HIGH);
  digitalWrite(MAXSPEEDPUMP, LOW);
  digitalWrite(ENAPUMP, HIGH);
  analogWrite(SPEEDPUMP, 0);

  pinMode(HOME, INPUT_PULLUP);
  pinMode(PORT, INPUT_PULLUP);

  stepperValve.begin(RPMVALVE,MICROSTEPS);
  stepperValve.setEnableActiveState(LOW);

  // Attach my application's user-defined callback methods
  attachCommandCallbacks();
  
  cmdMessenger.sendCmd(kAcknowledge,"Arduino has started!");
}

void loop() {
  // Process incoming serial data, and perform callbacks
  cmdMessenger.feedinSerialData();
}

void drainSpeed(int drainSpeed, bool dir){
  digitalWrite(DIRPUMP, dir);
  analogWrite(SPEEDPUMP, drainSpeed);
  if(drainSpeed == 255){
    digitalWrite(MAXSPEEDPUMP, HIGH);
  }else{
      digitalWrite(MAXSPEEDPUMP, LOW);
  }
  delay(10);

  digitalWrite(ENAPUMP, LOW);
}

void stopDrain(){

  digitalWrite(ENAPUMP, HIGH);
  analogWrite(SPEEDPUMP, 0);
  digitalWrite(MAXSPEEDPUMP, LOW);
  
}

void drainMl(float ml,bool dir){
 digitalWrite(DIRPUMP, dir);
  
 float t = convertMltoMiliseconds(ml);

 digitalWrite(MAXSPEEDPUMP, HIGH);
 
 digitalWrite(ENAPUMP, LOW);

 delay(t);

 digitalWrite(ENAPUMP, HIGH);

 digitalWrite(MAXSPEEDPUMP, LOW);

}

float convertMltoMiliseconds(float ml){
    float d = ml*ml2MilisecondsMultiplier;
    return d;  
}

void moveToNexPort(bool dir){
  int dirMultiplier = 1;
  if(!dir){
    dirMultiplier = -1;
  }
  
  if(DEBUG){
    Serial.println("Starting Valve Motor");
  }
  
  stepperValve.enable();

  stepperValve.rotate(dirMultiplier*45);

  stepperValve.startRotate(dirMultiplier*50);

  while(digitalRead(PORT) != LOW){
     unsigned wait_time_micros = stepperValve.nextAction();
  }

  
  stepperValve.stop();

  if(DEBUG){
    Serial.println("Reached port, moving microsteps");
  }

  stepperValve.move(dirMultiplier*24);

  stepperValve.stop();

  stepperValve.disable();

  portNumber = portNumber + dirMultiplier;

  if(portNumber > 4){
    portNumber = 1;
  }

  if(portNumber < 1){
    portNumber = 4;
  }

  if(DEBUG){
    Serial.println("Reached port number");
    Serial.println(portNumber);
  }
  
}

void returnPortNumber(){
  Serial.println(portNumber);
 }

void moveToHomePort(){

    while(digitalRead(HOME) != LOW){
      moveToNexPort(true);
      delay(5000);
    }
  if(DEBUG){
    Serial.println("Reached Home!");
  }
    portNumber = 1;
}

void moveValve45(bool dir){
  int dirMultiplier = 1;
  if(!dir){
    dirMultiplier = -1;
  }

  Serial.println("Starting valve motor");
  stepperValve.enable();

  stepperValve.rotate(dirMultiplier*45);

  
  stepperValve.stop();

  stepperValve.disable();
}

//void measure(){
//
//     sensor.takeMeasurements();
//
//     cmdMessenger.sendCmdStart(kGetSensorReadingResult);
//    
//     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedA());
//     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedB());
//     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedC());
//     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedD());
//     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedE());
//     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedF());
//
//     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedG());
//     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedH());
//     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedI());
//     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedJ());
//     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedK());
//     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedL());
//
//     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedR());
//     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedS());
//     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedT());
//     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedU());
//     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedV());
//     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedW());
//     cmdMessenger.sendCmdEnd();
//
//     cmdMessenger.sendCmdStart(kGetSensorReadingResultRaw);
//
//     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getA());
//     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getB());
//     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getC());
//     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getD());
//     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getE());
//     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getF());
//
//     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getG());
//     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getH());
//     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getI());
//     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getJ());
//     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getK());
//     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getL());
//
//     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getR());
//     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getS());
//     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getT());
//     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getU());
//     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getV());
//     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getW());
//     cmdMessenger.sendCmdEnd();
//}
