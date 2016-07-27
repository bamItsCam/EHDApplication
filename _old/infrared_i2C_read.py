#import and open the device
import u3
d = u3.U3()
for x in range(0,50):
    #send & receive I2C data
    infrared_data = d.i2c(0x0, [0x7], NoStopWhenRestarting = True, NumI2CBytesToReceive = 3)
    I2CBytes = infrared_data['I2CBytes']
    ##Convert I2C Data into temp
    temperature = (I2CBytes[0] + 16*16*I2CBytes[1])*0.02 - 273.15
    print temperature
