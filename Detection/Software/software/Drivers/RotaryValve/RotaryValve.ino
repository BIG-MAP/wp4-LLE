#include <Arduino.h>
#include "DRV8825.h"
//#include "BasicStepperDriver.h"

// Motor steps per revolution. Most steppers are 200 steps or 1.8 degrees/step
#define MOTOR_STEPS 200
#define RPM 60
// Microstepping mode. If you hardwired it to save pins, set to the same value here.
#define MICROSTEPS 16


#define DIR 10
#define STEP 9
#define ENA 8

#define HOME 5
#define PORT 6

DRV8825 stepper(MOTOR_STEPS, DIR, STEP, ENA);
//BasicStepperDriver stepper(MOTOR_STEPS, DIR, STEP, ENA);
char x;
boolean DEBUG = false;

bool homePort = false;
bool port = false;
int portNumber = 1;

void setup() {
  // put your setup code here, to run once:
  
  Serial.begin(115200);
  
  pinMode(HOME, INPUT_PULLUP);
  pinMode(PORT, INPUT_PULLUP);
  
  
  stepper.begin(RPM, MICROSTEPS);

  // if using enable/disable on ENABLE pin (active LOW) instead of SLEEP uncomment next line
  stepper.setEnableActiveState(LOW);
  
if(DEBUG){
  Serial.println("START");
}
  
  
}

void loop() {
  while(!Serial.available());
  
  x = Serial.read();

  if(x == 'n'){
     moveToNexPort(true);
     returnPortNumber();
  }

  if(x == 'h'){
     moveToHomePort();
     returnPortNumber();
  }

  if(x == 'c'){
     returnPortNumber();
  }

  if(x == 'd'){
     if(DEBUG){
       DEBUG = false;
       Serial.println("Debug mode off");
     }else{
       DEBUG = true;
       Serial.println("Debug mode on");
     }
  }

  if(DEBUG){
    if(x == 't'){
       move20(true);
        Serial.println(digitalRead(HOME));
        Serial.println(digitalRead(PORT));
    }
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

void moveToNexPort(bool dir){
  int dirMultiplier = 1;
  if(!dir){
    dirMultiplier = -1;
  }
  
  if(DEBUG){
    Serial.println("Starting Motor");
  }
  
  stepper.enable();

  stepper.rotate(dirMultiplier*45);

  stepper.startRotate(dirMultiplier*50);

  while(digitalRead(PORT) != LOW){
     unsigned wait_time_micros = stepper.nextAction();
  }

  
  stepper.stop();

  if(DEBUG){
    Serial.println("Reached port, moving microsteps");
  }

  stepper.move(dirMultiplier*24);

  stepper.stop();

  stepper.disable();

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

void move20(bool dir){
  int dirMultiplier = 1;
  if(!dir){
    dirMultiplier = -1;
  }

  Serial.println("Starting Motor");
  stepper.enable();

  stepper.rotate(dirMultiplier*45);

  
  stepper.stop();

  stepper.disable();

  
}
