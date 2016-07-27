import u3
import math
d = u3.U3()
d.getCalibrationData()

#44006 - Ambient
Aamb=1.032e-03
Bamb=2.387e-04
Camb=1.58e-07
#44004 - Surface
Asurf=1.468e-03
Bsurf=2.383e-04
Csurf=1.007e-07

print ""
print "Surface Thermistor"
print ""

##### SURFACE THERMISTOR #####
ain0bits, = d.getFeedback(u3.AIN(0)) # Read raw bits from AIN0
ain1bits, = d.getFeedback(u3.AIN(1)) # Read raw bits from AIN1
print "Thermistor Voltage Bits"
print ain1bits
print "Source Voltage Bits"
print ain0bits
#Convert raw bits to voltage
ainValue0 = d.binaryToCalibratedAnalogVoltage(ain0bits, isLowVoltage = False, channelNumber = 0)
ainValue1 = d.binaryToCalibratedAnalogVoltage(ain1bits, isLowVoltage = False, channelNumber = 0)
print "Thermistor Voltage"
print ainValue1
print "Source Voltage"
print ainValue0
#Convert voltages to resistance
thermistor_resistance = 14930*ainValue1/(ainValue0-ainValue1)
print "Thermistor Resistance"
print thermistor_resistance
#Convert resistance to temperature
lnR = math.log(thermistor_resistance)
thermistor_temperature = 1/(Asurf+Bsurf*lnR+Csurf*lnR*lnR*lnR)-273.15
print "Thermistor Temperature"
print thermistor_temperature

print ""
print ""
print "Ambient Thermistor"
print ""

##### AMBIENT THERMISTOR #####
ain2bits, = d.getFeedback(u3.AIN(2)) # Read raw bits from AIN2
ain3bits, = d.getFeedback(u3.AIN(3)) # Read raw bits from AIN3
print "Thermistor Voltage Bits"
print ain3bits
print "Source Voltage Bits"
print ain2bits
#Convert raw bits to voltage
ainValue2 = d.binaryToCalibratedAnalogVoltage(ain2bits, isLowVoltage = False, channelNumber = 0)
ainValue3 = d.binaryToCalibratedAnalogVoltage(ain3bits, isLowVoltage = False, channelNumber = 0)
print "Thermistor Voltage"
print ainValue3
print "Source Voltage"
print ainValue2
#Convert voltages to resistance
thermistor_resistance = 14930*ainValue3/(ainValue2-ainValue3)
print "Thermistor Resistance"
print thermistor_resistance
#Convert resistance to temperature
lnR = math.log(thermistor_resistance)
thermistor_temperature = 1/(Aamb+Bamb*lnR+Camb*lnR*lnR*lnR)-273.15
print "Thermistor Temperature"
print thermistor_temperature
