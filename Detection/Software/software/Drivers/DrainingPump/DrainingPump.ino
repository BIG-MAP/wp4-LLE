#include <Arduino.h>
#include "DRV8825.h"

// Motor steps per revolution. Most steppers are 200 steps or 1.8 degrees/step
#define MOTOR_STEPS 200
#define RPM 120
#define RPMVALVE 60
// Microstepping mode. If you hardwired it to save pins, set to the same value here.
#define MICROSTEPS 16

#define DIR 10
#define STEP 9
#define ENA 8

#define DIRVALVE 4
#define STEPVALVE 3
#define ENAVALVE 2

DRV8825 stepper(MOTOR_STEPS, DIR, STEP, ENA);
DRV8825 stepperValve(MOTOR_STEPS, DIRVALVE, STEPVALVE, ENAVALVE);

char x;
boolean DEBUG = false;
float mlPerDrain = 1;
float ml2DegreesMultiplier = 10;
bool rotationDir = true;


void setup() {
  // put your setup code here, to run once:

  Serial.begin(115200);
  stepper.begin(RPM, MICROSTEPS);
  stepper.setEnableActiveState(LOW);

  stepperValve.begin(RPMVALVE,MICROSTEPS);
  stepperValve.setEnableActiveState(LOW);

  stepperValve.disable();
  
  if(DEBUG){
    Serial.println("START");
  }
}

void loop() {
  while(!Serial.available());
  x = Serial.read();

  if(x == 'r'){
     drainMl(mlPerDrain,rotationDir);
     Serial.println("0");
  }

  if(x == 'd'){
     if(DEBUG){
       DEBUG = false;
       Serial.println("Debug mode off");
     }else{
       DEBUG = true;
       Serial.println("Debug mode on");
     }
     Serial.println("0");
  }

  if(x=='s'){
      float recv = Serial.parseFloat();
      if(recv>140){
        mlPerDrain = 140;
      }else{
        if(recv<0){
          mlPerDrain = 0;
        }else{
          mlPerDrain = recv;
        }
      }
      if(DEBUG){
        String preamble = "Setting drain to ";
        Serial.println(preamble + mlPerDrain);
      }
      
      Serial.println("0");
   }

   if(x=='m'){
      float recv = Serial.parseFloat();
      if(recv>500){
        ml2DegreesMultiplier = 500;
      }else{
        if(recv<0){
          ml2DegreesMultiplier = 0;
        }else{
          ml2DegreesMultiplier = recv;
        }
      }
      if(DEBUG){
        String preamble = "Setting multiplier to ";
        Serial.println(preamble + ml2DegreesMultiplier);
      }
      
      Serial.println("0");
   }


   if(x=='i'){
     //delay(500);
     if(rotationDir){
       rotationDir = false;
       if(DEBUG){
         Serial.println("Rotation set to false");
       }
     }else{
       rotationDir = true;
       if(DEBUG){
         Serial.println("Rotation set to true");
       }   
     } 
     int response = 0;
     Serial.println(response);  
   }

  if(DEBUG){
    if(x == 't'){
       drainMl(20,rotationDir);
       Serial.println("0");
    }
  }

}

void drainMl(float ml,bool dir){
  int dirMultiplier = 1;
  if(!dir){
    dirMultiplier = -1;
  }

  float d = convertMltoDegrees(ml);

  if(DEBUG){
    String preamble = "Starting Motor to move to ";
    Serial.println(preamble + d);
  }

  stepper.enable();

  stepper.rotate(dirMultiplier*d);

  stepper.stop();

  if(DEBUG){
    Serial.println("Holding half a second");
  }
  delay(500);

  stepper.disable();

  if(DEBUG){
    Serial.println("Motor stopped");
  }
}



float convertMltoDegrees(float ml){
    float d = ml*ml2DegreesMultiplier;
    return d;  
}
