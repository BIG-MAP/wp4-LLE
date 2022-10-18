#include <Arduino.h>
#include <CmdMessenger.h>  // CmdMessenger

CmdMessenger cmdMessenger(Serial,',',';','/');


//Refill pump
#define PWMA 3
#define DIRA 12
#define BRAKEA 9

//Drain pump
#define PWMB 11
#define DIRB 13
#define BRAKEB 8


#define VALVE0 2
#define VALVE1 3
#define VALVE2 4
#define VALVE3 5
#define VALVE4 49
#define VALVE5 47
#define VALVE6 45
#define VALVE7 43

int valves[][8] = {{VALVE0, VALVE1, VALVE2, VALVE3, VALVE4, VALVE5, VALVE6, VALVE7},
                  {0,0,0,0,0,0,0,0}};

boolean DEBUG = false;

float pumpSpeed = 50;

// This is the list of recognized commands. These can be commands that can either be sent or received. 
// In order to receive, attach a callback function to these events
enum
{
  // Commands
  kWatchdog            , // Command to request application ID
  kAcknowledge         , // Command to acknowledge a received command
  kError               , // Command to message that an error has occurred
  kOpenValve        , // Command to open a valve             
  kCloseValve        , // Command to close a valve               
  kStartPump       , // Command to start pump  
  kStopPump  , // Command to stop pump   
  kSetPumpSpeed  , // Command to set pump speed
};


// Commands we send from the PC and want to receive on the Arduino.
// We must define a callback function in our Arduino program for each entry in the list below.
void attachCommandCallbacks()
{
  // Attach callback methods
  cmdMessenger.attach(OnUnknownCommand);
  cmdMessenger.attach(kWatchdog, OnWatchdogRequest);
  cmdMessenger.attach(kOpenValve, OnOpenValve);
  cmdMessenger.attach(kCloseValve, OnCloseValve);
  cmdMessenger.attach(kStartPump, OnStartPump);
  cmdMessenger.attach(kStopPump, OnStopPump);
  cmdMessenger.attach(kSetPumpSpeed, OnSetPumpSpeed);
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

void OnOpenValve()
{
  //int recv = cmdMessenger.readBinArg<int>();
  int recv = (int)cmdMessenger.readFloatArg();
  if (cmdMessenger.isArgOk()) {
    
    openSolValve(recv);

    cmdMessenger.sendCmd(kAcknowledge,"Opened valve " + recv);
    
  } else {
    // Error in received goal temperature! Send error back to PC
    cmdMessenger.sendCmd(kError,"Error in received in open valve");
  }
   
}


void OnCloseValve()
{
  //int recv = cmdMessenger.readBinArg<int>();
  int recv = (int)cmdMessenger.readFloatArg();
  if (cmdMessenger.isArgOk()) {
    
    closeSolValve(recv);

    cmdMessenger.sendCmd(kAcknowledge,"Closed valve " + recv);
    
  } else {
    // Error in received goal temperature! Send error back to PC
    cmdMessenger.sendCmd(kError,"Error in received in close valve");
  }
   
}


void OnStartPump()
{
    int pwmSpeed = map(pumpSpeed,0,100,0,255);
    analogWrite(PWMA, pwmSpeed);
    cmdMessenger.sendCmd(kAcknowledge,"Moving Pumps"); 
}


void OnStopPump()
{
    analogWrite(PWMA, 0);
    cmdMessenger.sendCmd(kAcknowledge,"TBI"); 
}

void OnSetPumpSpeed()
{
 float recv = cmdMessenger.readBinArg<float>();

   if (cmdMessenger.isArgOk()) {
       if(recv>100){
        pumpSpeed = 100;
      }else{
        if(recv<0){
          pumpSpeed = 0;
        }else{
          pumpSpeed = recv;
        }
      }

    // Send acknowledgment back to PC
    cmdMessenger.sendCmd(kAcknowledge,pumpSpeed); 
  } else {
    // Error in received goal temperature! Send error back to PC
    cmdMessenger.sendCmd(kError,"Error in received set pump speed");
  }
}


// ------------------ M A I N  ----------------------


void setup() {
  Serial.begin(115200);

  // Do not print newLine at end of command, 
  // in order to reduce data being sent
  cmdMessenger.printLfCr(false);

  pinMode(PWMA, OUTPUT);
  pinMode(DIRA, OUTPUT);
  pinMode(BRAKEA, OUTPUT);
  pinMode(PWMB, OUTPUT);
  pinMode(DIRB, OUTPUT);
  pinMode(BRAKEB, OUTPUT);

  digitalWrite(BRAKEA, LOW);
  digitalWrite(BRAKEB, LOW);
  digitalWrite(DIRA, LOW);
  digitalWrite(DIRB, LOW);

  pinMode(VALVE0, OUTPUT);
  pinMode(VALVE1, OUTPUT);
  pinMode(VALVE2, OUTPUT);
  pinMode(VALVE3, OUTPUT);
  pinMode(VALVE4, OUTPUT);
  pinMode(VALVE5, OUTPUT);
  pinMode(VALVE6, OUTPUT);
  pinMode(VALVE7, OUTPUT);
  

  // Attach my application's user-defined callback methods
  attachCommandCallbacks();
  
  cmdMessenger.sendCmd(kAcknowledge,"Arduino has started!");

}

void loop() {
  // Process incoming serial data, and perform callbacks
  cmdMessenger.feedinSerialData();

}

void openSolValve(int valve){
  if(valve >= 0 && valve <= 7){
    if(valves[1][valve] != 1){
        digitalWrite(valves[0][valve],HIGH);
        valves[1][valve] = 1;
    }
  }else{
    cmdMessenger.sendCmd(kError,"Not a valid valve identifier");
  }
}

void closeSolValve(int valve){
  if(valve >= 0 && valve <= 7){
    if(valves[1][valve] != 0){
        digitalWrite(valves[0][valve],LOW);
        valves[1][valve] = 0;
    }
  }else{
    cmdMessenger.sendCmd(kError,"Not a valid valve identifier");
  }
}
