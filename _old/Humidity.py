import u3
import time
import math
d = u3.U3()
d.getCalibrationData()

#send & receive I2C humidity and temp data
humidity_data = d.i2c(0x28, [], NoStopWhenRestarting = True, SDAPinNum = 4, SCLPinNum = 5, NumI2CBytesToReceive = 4)
print humidity_data
I2CBytes = humidity_data['I2CBytes']
#Convert I2C data into temp and humidity
relative_humidity = 100.0*(I2CBytes[0]*256 + I2CBytes[1])/pow(2,14)
print "Relative Humidity"
print relative_humidity
ambient_temp = -40 + 165.0*(I2CBytes[2]*64 + I2CBytes[3]/16)/pow(2,14)
print "Ambient Temp"
print ambient_temp

#send & receive I2C object data
infrared_data = d.i2c(0x0, [0x7], NoStopWhenRestarting = True, NumI2CBytesToReceive = 3)
print infrared_data
I2CBytes = infrared_data['I2CBytes']
##Convert I2C Data into temp
temperature = (I2CBytes[0] + 16*16*I2CBytes[1])*0.02 - 273.15
print "Infrared Object1"
print temperature
