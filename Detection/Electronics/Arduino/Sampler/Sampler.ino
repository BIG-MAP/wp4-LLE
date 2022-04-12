#include "SparkFun_AS7265X.h"
AS7265X sensor;

//Refill pump
#define PWMA 3
#define DIRA 12
#define BRAKEA 9

//Drain pump
#define PWMB 11
#define DIRB 13
#define BRAKEB 8

char x;

int lastReading = 0;
int sensorPin = A0;


void setup() {

  pinMode(LED_BUILTIN, OUTPUT);
  
  pinMode(PWMA, OUTPUT);
  pinMode(DIRA, OUTPUT);
  pinMode(BRAKEA, OUTPUT);
  pinMode(PWMB, OUTPUT);
  pinMode(DIRB, OUTPUT);
  pinMode(BRAKEB, OUTPUT);
  Serial.begin(115200);

  digitalWrite(BRAKEA, LOW);
  digitalWrite(BRAKEB, LOW);
  digitalWrite(DIRA, LOW);
  digitalWrite(DIRB, LOW);
  analogWrite(PWMB, 0);
  analogWrite(PWMA, 0);
  
  

}

void loop() {

 
 while (!Serial.available());
 x = Serial.read();

 
 
 if(x == 's'){
     analogWrite(PWMA, 150);
     delay(1000);
     analogWrite(PWMA, 0);
     delay(1500);
 }

 if(x == 'r'){
     analogWrite(PWMA, 150);
     delay(30000);
     analogWrite(PWMA, 0);
     delay(1500);
 }

 



}
