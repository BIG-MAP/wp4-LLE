/**************************************************************************/
/*
	
	I2C Driver for Microchip's MCP4725 I2C DAC

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

#include "Aptinex_MCP4725.h"

/**************************************************************************/
/*! 
    @brief  Instantiates a new MCP4725 class
*/
/**************************************************************************/
Aptinex_MCP4725::Aptinex_MCP4725() {
}

/**************************************************************************/
/*! 
    @brief  Setups the HW
*/
/**************************************************************************/
void Aptinex_MCP4725::begin(uint8_t addr) {
  _i2caddr = addr;
  Wire.begin();

}
 
/**************************************************************************/
/*! 
    @brief  Sets the output voltage to a fraction of source vref.  (Value
            can be 0..4095)

    @param[in]  output
                The 12-bit value representing the relationship between
                the DAC's input voltage and its output voltage.
    @param[in]  writeEEPROM
                If this value is true, 'output' will also be written
                to the MCP4725's internal non-volatile memory, meaning
                that the DAC will retain the current voltage output
                after power-down or reset.
*/
/**************************************************************************/
void Aptinex_MCP4725::setVoltage( uint16_t output, bool writeEEPROM )
{
#ifdef TWBR
  uint8_t twbrback = TWBR;
  TWBR = ((F_CPU / 400000L) - 16) / 2; // Set I2C frequency to 400kHz
#endif
  Wire.beginTransmission(_i2caddr);
  if (writeEEPROM)
  {
    Wire.write(MCP4726_CMD_WRITEDACEEPROM);
  }
  else
  {
    Wire.write(MCP4726_CMD_WRITEDAC);
  }
  Wire.write(output / 16);                   // Upper data bits          (D11.D10.D9.D8.D7.D6.D5.D4)
  Wire.write((output % 16) << 4);            // Lower data bits          (D3.D2.D1.D0.x.x.x.x)
  Wire.endTransmission();
#ifdef TWBR
  TWBR = twbrback;
#endif
}
