import u3
import math
d = u3.U3()
d.getCalibrationData()

#### INFRARED 1 ####
#send & receive I2C ambient data
infrared_data = d.i2c(0x0, [0x6], NoStopWhenRestarting = True, NumI2CBytesToReceive = 3)
I2CBytes = infrared_data['I2CBytes']
##Convert I2C Data into temp
temperature = (I2CBytes[0] + 16*16*I2CBytes[1])*0.02 - 273.15
print "Infrared Ambient"
print ""
print "I2CBytes:"
print I2CBytes
print "Temperature"
print temperature
print ""
print ""

#send & receive I2C object data
infrared_data = d.i2c(0x0, [0x7], NoStopWhenRestarting = True, NumI2CBytesToReceive = 3)
I2CBytes = infrared_data['I2CBytes']
##Convert I2C Data into temp
temperature = (I2CBytes[0] + 16*16*I2CBytes[1])*0.02 - 273.15
print "Infrared Object"
print ""
print "I2CBytes:"
print I2CBytes
print "Temperature"
print temperature
print ""

