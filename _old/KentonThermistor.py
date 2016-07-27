import u3
import math
d = u3.U3()
d.getCalibrationData()

##### THERMISTOR #####
ain0bits, = d.getFeedback(u3.AIN(0, 31, True)) # Read raw bits from AIN0
ain1bits, = d.getFeedback(u3.AIN(1, 31, True)) # Read raw bits from AIN1
print "Thermistor Voltage Bits"
print ain0bits
print "Source Voltage Bits"
print ain1bits
#Convert raw bits to voltage
ainValue0 = d.binaryToCalibratedAnalogVoltage(ain0bits, isLowVoltage = False, channelNumber = 0)
ainValue1 = d.binaryToCalibratedAnalogVoltage(ain1bits, isLowVoltage = False, channelNumber = 0)
print "Thermistor Voltage"
print ainValue0
print "Source Voltage"
print ainValue1
#Convert voltages to resistance
thermistor_resistance = 14930*ainValue0/(ainValue1-ainValue0)
print "Thermistor Resistance"
print thermistor_resistance
#Convert resistance to temperature
#44006
A=1.032e-03
B=2.387e-04
C=1.58e-07
#44004
#A=1.468e-03
#B=2.383e-04
#C=1.007e-07
lnR = math.log(thermistor_resistance)
thermistor_temperature = 1/(A+B*lnR+C*lnR*lnR*lnR)-273.15
print "Thermistor Temperature"
print thermistor_temperature

#### INFRARED 1 ####
#send & receive I2C ambient data
infrared_data = d.i2c(0x0, [0x6], NoStopWhenRestarting = True, NumI2CBytesToReceive = 3)
I2CBytes = infrared_data['I2CBytes']
##Convert I2C Data into temp
temperature = (I2CBytes[0] + 16*16*I2CBytes[1])*0.02 - 273.15
print "Infrared Ambient1"
print temperature

#send & receive I2C object data
infrared_data = d.i2c(0x0, [0x7], NoStopWhenRestarting = True, NumI2CBytesToReceive = 3)
I2CBytes = infrared_data['I2CBytes']
##Convert I2C Data into temp
temperature = (I2CBytes[0] + 16*16*I2CBytes[1])*0.02 - 273.15
print "Infrared Object1"
print temperature

#### INFRARED 2 ####
#send & receive I2C ambient data
infrared_data = d.i2c(0x0, [0x6], NoStopWhenRestarting = True, SDAPinNum = 4, SCLPinNum = 5, NumI2CBytesToReceive = 3)
I2CBytes = infrared_data['I2CBytes']
##Convert I2C Data into temp
temperature = (I2CBytes[0] + 16*16*I2CBytes[1])*0.02 - 273.15
print "Infrared Ambient2"
print temperature

#send & receive I2C object data
infrared_data = d.i2c(0x0, [0x7], NoStopWhenRestarting = True, SDAPinNum = 4, SCLPinNum = 5, NumI2CBytesToReceive = 3)
I2CBytes = infrared_data['I2CBytes']
##Convert I2C Data into temp
temperature = (I2CBytes[0] + 16*16*I2CBytes[1])*0.02 - 273.15
print "Infrared Object2"
print temperature
