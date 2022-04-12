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
int sensorPin = A5;


void setup() {

  pinMode(LED_BUILTIN, OUTPUT);

  pinMode(sensorPin, INPUT);
  
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
  
  
  
  //Serial.println("Checking sensor");
  if(sensor.begin() == false)
  {
    Serial.println("Sensor does not appear to be connected. Please check wiring. Freezing...");
    while(1);
  }
  sensor.disableIndicator(); //Turn off the blue status LED

}

void loop() {

 
 while (!Serial.available());
 x = Serial.read();

 if(x=='t'){

  Serial.println("A,B,C,D,E,F,G,H,I,J,K,L,R,S,T,U,V,W");
  for(int i = 0; i<250;i++){
    
     //Start draining pump
     analogWrite(PWMA, 150);
     delay(1000);
     analogWrite(PWMA, 0);
     delay(1500);

     sensor.takeMeasurements();
     
     Serial.print(sensor.getCalibratedA());
     Serial.print(",");
     Serial.print(sensor.getCalibratedB());
     Serial.print(",");
     Serial.print(sensor.getCalibratedC());
     Serial.print(",");
     Serial.print(sensor.getCalibratedD());
     Serial.print(",");
     Serial.print(sensor.getCalibratedE());
     Serial.print(",");
     Serial.print(sensor.getCalibratedF());
     Serial.print(",");

     Serial.print(sensor.getCalibratedG());
     Serial.print(",");
     Serial.print(sensor.getCalibratedH());
     Serial.print(",");
     Serial.print(sensor.getCalibratedI());
     Serial.print(",");
     Serial.print(sensor.getCalibratedJ());
     Serial.print(",");
     Serial.print(sensor.getCalibratedK());
     Serial.print(",");
     Serial.print(sensor.getCalibratedL());
     Serial.print(",");

     Serial.print(sensor.getCalibratedR());
     Serial.print(",");
     Serial.print(sensor.getCalibratedS());
     Serial.print(",");
     Serial.print(sensor.getCalibratedT());
     Serial.print(",");
     Serial.print(sensor.getCalibratedU());
     Serial.print(",");
     Serial.print(sensor.getCalibratedV());
     Serial.print(",");
     Serial.print(sensor.getCalibratedW());
     Serial.println();
  }
  Serial.println("end");
   
 }

 

 if(x == 'c'){
     analogWrite(PWMA, 200);
     analogWrite(PWMB, 200);
     delay(200000);
     analogWrite(PWMA, 0);
     analogWrite(PWMB, 0);
     delay(1000);
 }

 if(x == 'r'){
     analogWrite(PWMB, 200);
     delay(250000);
     analogWrite(PWMB, 0);
     delay(1000);
 }

 if(x == 'e'){
     analogWrite(PWMA, 200);
     delay(250000);
     analogWrite(PWMA, 0);
     delay(1000);
 }

 if(x == 's'){
     analogWrite(PWMA, 150);
     delay(1000);
     analogWrite(PWMA, 0);
     delay(1500);
 }

 if(x == 'm'){
     measure();
 }

 if(x == 'v'){
     lastReading = analogRead(sensorPin);
     Serial.println(lastReading);  
 }


}

void measure(){

     sensor.takeMeasurements();
     lastReading = analogRead(sensorPin);
     
     Serial.print(sensor.getCalibratedA());
     Serial.print(",");
     Serial.print(sensor.getCalibratedB());
     Serial.print(",");
     Serial.print(sensor.getCalibratedC());
     Serial.print(",");
     Serial.print(sensor.getCalibratedD());
     Serial.print(",");
     Serial.print(sensor.getCalibratedE());
     Serial.print(",");
     Serial.print(sensor.getCalibratedF());
     Serial.print(",");

     Serial.print(sensor.getCalibratedG());
     Serial.print(",");
     Serial.print(sensor.getCalibratedH());
     Serial.print(",");
     Serial.print(sensor.getCalibratedI());
     Serial.print(",");
     Serial.print(sensor.getCalibratedJ());
     Serial.print(",");
     Serial.print(sensor.getCalibratedK());
     Serial.print(",");
     Serial.print(sensor.getCalibratedL());
     Serial.print(",");

     Serial.print(sensor.getCalibratedR());
     Serial.print(",");
     Serial.print(sensor.getCalibratedS());
     Serial.print(",");
     Serial.print(sensor.getCalibratedT());
     Serial.print(",");
     Serial.print(sensor.getCalibratedU());
     Serial.print(",");
     Serial.print(sensor.getCalibratedV());
     Serial.print(",");
     Serial.print(sensor.getCalibratedW());
     Serial.print(",");
     Serial.print(lastReading);
     Serial.println();

     Serial.print(sensor.getA());
     Serial.print(",");
     Serial.print(sensor.getB());
     Serial.print(",");
     Serial.print(sensor.getC());
     Serial.print(",");
     Serial.print(sensor.getD());
     Serial.print(",");
     Serial.print(sensor.getE());
     Serial.print(",");
     Serial.print(sensor.getF());
     Serial.print(",");

     Serial.print(sensor.getG());
     Serial.print(",");
     Serial.print(sensor.getH());
     Serial.print(",");
     Serial.print(sensor.getI());
     Serial.print(",");
     Serial.print(sensor.getJ());
     Serial.print(",");
     Serial.print(sensor.getK());
     Serial.print(",");
     Serial.print(sensor.getL());
     Serial.print(",");

     Serial.print(sensor.getR());
     Serial.print(",");
     Serial.print(sensor.getS());
     Serial.print(",");
     Serial.print(sensor.getT());
     Serial.print(",");
     Serial.print(sensor.getU());
     Serial.print(",");
     Serial.print(sensor.getV());
     Serial.print(",");
     Serial.print(sensor.getW());
     Serial.print(",");
     Serial.print(lastReading);
     Serial.println();
}
