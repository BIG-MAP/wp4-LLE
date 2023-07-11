/**************************************************************************/
/*Aptinex_MCP4725 Library for Aptinex DA1C010BI Module

  This is a library for the Aptinex DAC Module DA1C010BI I2C Digital to Analog 0-10V Module
  
  ----> https://aptinex.com/product/aptinex-dac-module-da1c010bi-digital-to-analog-0-10v-mcp4725-i2c/
  
  Aptinex(PVT)Ltd
  No 167 1/1, Galle road,
  Dehiwala,
  Sri Lanka.

  
*/
/**************************************************************************/

#if ARDUINO >= 100
 #include "Arduino.h"
#else
 #include "WProgram.h"
#endif

#include <Wire.h>

#define MCP4726_CMD_WRITEDAC            (0x40)  // Writes data to the DAC
#define MCP4726_CMD_WRITEDACEEPROM      (0x60)  // Writes data to the DAC and the EEPROM (persisting the assigned value after reset)

class Aptinex_MCP4725{
 public:
  Aptinex_MCP4725();
  void begin(uint8_t a);  
  void setVoltage( uint16_t output, bool writeEEPROM );

 private:
  uint8_t _i2caddr;
};
