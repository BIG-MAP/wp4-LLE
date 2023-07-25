#include "opticalAS726X.h"

byte GAIN = 2;
byte MEASUREMENT_MODE = 0;

void SensorAS726X::takeMeasurement(bool bulb)
{

  if (bulb)
  {
    sensor.takeMeasurementsWithBulb();
  }
  else
  {
    sensor.takeMeasurements();
  }

  opticalSensor.version = sensor.getVersion();
  if (opticalSensor.version == SENSORTYPE_AS7262)
  {
    // Visible readings

    opticalSensor.readings[0] = sensor.getCalibratedViolet();
    opticalSensor.readings[1] = sensor.getCalibratedBlue();
    opticalSensor.readings[2] = sensor.getCalibratedGreen();
    opticalSensor.readings[3] = sensor.getCalibratedYellow();
    opticalSensor.readings[4] = sensor.getCalibratedOrange();
    opticalSensor.readings[5] = sensor.getCalibratedRed();

    opticalSensor.rawReadings[0] = sensor.getViolet();
    opticalSensor.rawReadings[1] = sensor.getBlue();
    opticalSensor.rawReadings[2] = sensor.getGreen();
    opticalSensor.rawReadings[3] = sensor.getYellow();
    opticalSensor.rawReadings[4] = sensor.getOrange();
    opticalSensor.rawReadings[5] = sensor.getRed();
  }
  else if (opticalSensor.version == SENSORTYPE_AS7263)
  {
    // Near IR readings

    opticalSensor.readings[0] = sensor.getCalibratedR();
    opticalSensor.readings[1] = sensor.getCalibratedS();
    opticalSensor.readings[2] = sensor.getCalibratedT();
    opticalSensor.readings[3] = sensor.getCalibratedU();
    opticalSensor.readings[4] = sensor.getCalibratedV();
    opticalSensor.readings[5] = sensor.getCalibratedW();

    opticalSensor.rawReadings[0] = sensor.getR();
    opticalSensor.rawReadings[1] = sensor.getS();
    opticalSensor.rawReadings[2] = sensor.getT();
    opticalSensor.rawReadings[3] = sensor.getU();
    opticalSensor.rawReadings[4] = sensor.getV();
    opticalSensor.rawReadings[5] = sensor.getW();
  }

  opticalSensor.temperature = sensor.getTemperature();
}

void SensorAS726X::printHeaders()
{

  if (opticalSensor.version == SENSORTYPE_AS7262)
  {
    Serial.println("Violet, Blue, Green, Yellow, Orange, Red");
  }
  else if (opticalSensor.version == SENSORTYPE_AS7263)
  {
    Serial.println("R, S, T, U, V, W");
  }
}

void SensorAS726X::printMeasurement()
{
  Serial.print(opticalSensor.readings[0]);
  Serial.print(", ");
  Serial.print(opticalSensor.readings[1]);
  Serial.print(", ");
  Serial.print(opticalSensor.readings[2]);
  Serial.print(", ");
  Serial.print(opticalSensor.readings[3]);
  Serial.print(", ");
  Serial.print(opticalSensor.readings[4]);
  Serial.print(", ");
  Serial.println(opticalSensor.readings[5]);
}

void SensorAS726X::printMeasurementRaw()
{
  Serial.print(opticalSensor.rawReadings[0]);
  Serial.print(", ");
  Serial.print(opticalSensor.rawReadings[1]);
  Serial.print(", ");
  Serial.print(opticalSensor.rawReadings[2]);
  Serial.print(", ");
  Serial.print(opticalSensor.rawReadings[3]);
  Serial.print(", ");
  Serial.print(opticalSensor.rawReadings[4]);
  Serial.print(", ");
  Serial.println(opticalSensor.rawReadings[5]);
}

void SensorAS726X::initialize()
{
  sensor.begin(Wire, GAIN, MEASUREMENT_MODE);
  // Serial.println("Sensor initialized");
  opticalSensor.version = sensor.getVersion();
  opticalSensor.present = true;
}

SensorAS726X opticalSensor;
