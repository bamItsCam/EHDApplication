import sys
from time import strftime
import u3
import math
import time
import threading
from balance import Balance
from balance import BalanceException
from storage import Storage
from LabJackPython import LabJackException
# Author:   Cameron Holloway
# Date:     12 Feb 2016
# Desc:     This is the HardwareIO class, which is in charge of interacting with all the hardware for this project.
#           The key function is gather_data() which polls all sensors/scales for information
# Notes:    Conventional order for CSV file columns:
#               Timestamp
#               top surface temp (thermistor)
#               bot surface temp (thermistor)
#               surface temp (infrared)
#               ambient temp (thermistor)
#               humidity (i2c)
#               mass (balance)
#               voltage (HFG)
#               current (HFG)
#               plate voltage (HP)
#               heat transfer
#           Conventional order for sensors:
#               top surface temp (thermistor)
#               bot surface temp (thermistor)
#               surface temp (infrared)
#               ambient temp (thermistor)
#               humidity (i2c)
#               mass (balance)
#               voltage (HFG)
#               current (HFG)
#               plate voltage (HP)

class HardwareIOException(Exception):
    # input:    nothing
    # output    nothing
    # desc:     The very simple custom Exception class for HardwareIO
    # purpose:  Allows HardwareIO to raise events that need to be known by HardwareIO owners
    def __init__(self, message):
        self.message = str(message)
    def __str__(self):
        return self.message

class HardwareIO:
    def __init__(self, store):
        # input:    takes a storage object
        # output:   nothing
        # desc:     The "constructor" of the HardwareIO class; 
        #           initializes members from config file; 
        #           also creates a labjack and balance object
        self.store = store
        # Configuration member variables

        # Labjack Channel Globals
        self.SAFETY_CUTOFF_COMPARATOR = int(self.store.get_config('SAFETY_CUTOFF_COMPARATOR'))
        self.MEASURED_VS_CHANNEL = int(self.store.get_config('MEASURED_VS_CHANNEL'))
        self.MEASURED_FIELD_VOLTAGE_CHANNEL = int(self.store.get_config('MEASURED_FIELD_VOLTAGE_CHANNEL'))
        self.MEASURED_FIELD_CURRENT_CHANNEL = int(self.store.get_config('MEASURED_FIELD_CURRENT_CHANNEL'))
        self.MEASURED_PLATE_VOLTAGE = int(self.store.get_config('MEASURED_PLATE_VOLTAGE'))
        self.TOP_THERMISTOR_CHANNEL = int(self.store.get_config('TOP_THERMISTOR_CHANNEL'))
        self.BOT_THERMISTOR_CHANNEL = int(self.store.get_config('BOT_THERMISTOR_CHANNEL'))
        self.AMBIENT_THERMISTOR_CHANNEL = int(self.store.get_config('AMBIENT_THERMISTOR_CHANNEL'))
        self.INFRARED_SDA_CHANNEL = int(self.store.get_config('INFRARED_SDA_CHANNEL'))
        self.INFRARED_SCL_CHANNEL = int(self.store.get_config('INFRARED_SCL_CHANNEL'))
        self.HUMIDITY_SCL_CHANNEL = int(self.store.get_config('HUMIDITY_SCL_CHANNEL'))
        self.HUMIDITY_SDA_CHANNEL = int(self.store.get_config('HUMIDITY_SDA_CHANNEL'))
        self.HIGH_VOLTAGE_SET_CHANNEL = int(self.store.get_config('HIGH_VOLTAGE_SET_CHANNEL'))
        self.CURRENT_CUTOFF_SET_CHANNEL = int(self.store.get_config('CURRENT_CUTOFF_SET_CHANNEL'))

        # Resistor value for thermistors
        self.surfaceResistorTop = int(self.store.get_config('surfaceResistorTop'))
        self.surfaceResistorBot = int(self.store.get_config('surfaceResistorBot'))
        self.ambientResistor = int(self.store.get_config('ambientResistor'))

        # Resistor values for measuring plate voltage
        self.plateResistor1 = int(self.store.get_config('plateResistor1'))
        self.plateResistor2 = int(self.store.get_config('plateResistor2'))

        # Magic constants for the ambient thermistor's equation (model #44006)
        self.ambientA = float(self.store.get_config('ambientA'))
        self.ambientB = float(self.store.get_config('ambientB'))
        self.ambientC = float(self.store.get_config('ambientC'))

        # Magic constants for the surface mount thermistor's equation (model #44004)
        self.surfaceA = float(self.store.get_config('surfaceA'))
        self.surfaceB = float(self.store.get_config('surfaceB'))
        self.surfaceC = float(self.store.get_config('surfaceC'))

        # Other random constants because science
        self.kelvinOffset = float(self.store.get_config('kelvinOffset'))

        try:
            self.labjack = u3.U3()
        except LabJackException as e:
            self.store.log_event('debug',"A LabJack error occurred in __init__(): %s" %str(e))
        except Exception as e:
            self.store.log_event('debug','An unhandled error occurred in __init__(): %s' %str(e))
        else:
            self.set_labjack_config()
            self.labjack.getCalibrationData()
            self.select_current_cutoff(int(self.store.get_config('currentCutoff')))
        try:
            self.balance = Balance()
        except BalanceException as e:
            self.store.log_event('debug',"A Balance error occurred in __init__(): %s" %str(e))

    def gather_data(self, store):
        # input:    storage object so that most recent values from config file are used, not stale data
        # output:   returns an array with a timestamp and temperature/humidity/mass readings, follows CSV order convention
        # desc:     the main workhorse in hardwareIO; 
        #           gets data from the labjack and balance, converts, and returns
        # notes:    1.  Heavily dependent on global variables defined above, implementation may change at a later time
        #           2.  Please note that no labjack object is createcd in this function, it relies on one being created
        #               in init or in check_sensors()
        # TODO: replace self.store with store

        validSensors = self.check_sensors(store)

        timeStamp = strftime('%Y-%m-%d %H:%M:%S')
        dataArray = [timeStamp, 'invalid', 'invalid', 'invalid', 'invalid', 'invalid', 'invalid', 'invalid', 'invalid', 'invalid', 'invalid']

        try:
            vsVoltage = self.get_voltage(self.MEASURED_VS_CHANNEL)

            #--------------------Surface Thermistor Top -----------------------
            if (int(store.get_config('Top Temperature')) and validSensors[0]):
                # get those voltages!
                topThermistorVoltage = self.get_voltage(self.TOP_THERMISTOR_CHANNEL)

                # voltage divide the crap out of the top thermistor
                # resistance = resistor * thermVoltage/(Vs - ThermVoltage)
                topThermistorResistance = self.surfaceResistorTop*topThermistorVoltage/(vsVoltage-topThermistorVoltage)
                
                # apply Omega's magic formula
                lnSurfaceTop = math.log(topThermistorResistance)
                surfaceThermistorTemperatureTop = 1/(self.surfaceA + self.surfaceB*lnSurfaceTop + self.surfaceC*lnSurfaceTop*lnSurfaceTop*lnSurfaceTop) - self.kelvinOffset
                
                # throw this value onto the back of the dataArray train:
                dataArray[1] = surfaceThermistorTemperatureTop
            else:
                dataArray[1] = 'invalid'

            #--------------------Surface Thermistor Bottom -----------------------
            if (int(store.get_config('Bottom Temperature')) and validSensors[1]):
                # get those voltages!
                botThermistorVoltage = self.get_voltage(self.BOT_THERMISTOR_CHANNEL)
                
                # voltage divide the crap out of the ambient thermistor
                botThermistorResistance = self.surfaceResistorBot*botThermistorVoltage/(vsVoltage-botThermistorVoltage)
                
                # apply Omega's magic formula
                lnSurfaceBot = math.log(botThermistorResistance)
                surfaceThermistorTemperatureBot = 1/(self.surfaceA + self.surfaceB*lnSurfaceBot + self.surfaceC*lnSurfaceBot*lnSurfaceBot*lnSurfaceBot) - self.kelvinOffset
                
                # append to dataArray for returning:
                dataArray[2] = surfaceThermistorTemperatureBot
            else:
                dataArray[2] = 'invalid'

            #-----------------Infrared I2C Sensor-----------------------
            if (int(store.get_config('Surface Temperature')) and validSensors[2]):
                # Infrared sensor send and receive I2C object data
                infraredData = self.labjack.i2c(0x0, [0x7], NoStopWhenRestarting = True, SDAPinNum = self.INFRARED_SDA_CHANNEL, SCLPinNum = self.INFRARED_SCL_CHANNEL, NumI2CBytesToReceive = 3)
                I2CInfraredBytes = infraredData['I2CBytes']
                # Convert I2C Data into temp
                infraredTemperature = (I2CInfraredBytes[0] + 16*16*I2CInfraredBytes[1])*0.02 - self.kelvinOffset

                # append to dataArray for returning
                dataArray[3] = infraredTemperature
            else:
                dataArray[3] = 'invalid'

            #-----------------Ambient Thermistor-----------------
            if (int(store.get_config('Ambient Temperature')) and validSensors[3]):
                # get those voltages!
                ambientVoltage = self.get_voltage(self.AMBIENT_THERMISTOR_CHANNEL)
                
                # voltage divide the crap out of the ambient thermistor
                ambientThermistorResistance = self.ambientResistor*ambientVoltage/(vsVoltage-ambientVoltage)
                
                # apply Omega's magic formula
                lnAmbient = math.log(ambientThermistorResistance)
                ambientThermistorTemperature = 1/(self.ambientA + self.ambientB*lnAmbient + self.ambientC*lnAmbient*lnAmbient*lnAmbient) - self.kelvinOffset
                
                # append to dataArray for returning:
                dataArray[4] = ambientThermistorTemperature
            else:
                dataArray[4] = 'invalid'

            #-----------------Ambient Humidity I2C-----------------
            if (int(store.get_config('Humidity')) and validSensors[4]):
                # because gather_data() is called right after check_sensors(), it's possible that some "stale" data may still be found in the 
                # buffer of the humidity chip. If this is so, a value greater than 100 will be read, and if a % is > 100, that's probably not good
                staleData = True
                while(staleData == True):
                    #send & receive I2C humidity and temp data
                    humidity_data = self.labjack.i2c(0x28, [], NoStopWhenRestarting = True, SDAPinNum = self.HUMIDITY_SDA_CHANNEL, SCLPinNum = self.HUMIDITY_SCL_CHANNEL, NumI2CBytesToReceive = 4)
                    I2CBytes = humidity_data['I2CBytes']
                    #Convert I2C data into temp and humidity
                    relative_humidity = 100.0*(I2CBytes[0]*256 + I2CBytes[1])/pow(2,14)
                    if (relative_humidity < 100):
                        staleData = False
                dataArray[5] = relative_humidity
            else:
                dataArray[5] = 'invalid'

            #-----------------Voltage of HFG-----------------
            if (int(store.get_config('Voltage')) and validSensors[6]):
                hfgVoltage = self.get_voltage(self.MEASURED_FIELD_VOLTAGE_CHANNEL) * 6000
                dataArray[7] = hfgVoltage
            else:
                dataArray[7] = 'invalid'
            #-----------------Current of HFG-----------------
            if (int(store.get_config('Current')) and validSensors[7]):
                hfgVoltage = self.get_voltage(self.MEASURED_FIELD_CURRENT_CHANNEL)
                hfgCurrent = hfgVoltage * 80.0 # in uA
                dataArray[8] = hfgCurrent
            else:
                dataArray[8] = 'invalid'
            #-----------------Heating Plate Voltage-----------------
            if (int(store.get_config('Plate Voltage')) and validSensors[8]):
                dividerVoltage = self.get_voltage(self.MEASURED_PLATE_VOLTAGE)
                # Vsource = (R1 + R2)/R1 * Vin
                plateVoltage = (self.plateResistor1 + self.plateResistor2)/self.plateResistor1 * dividerVoltage
                dataArray[9] = plateVoltage
            else:
                dataArray[9] = 'invalid'
            #------------------Heat Transfer (Heat Flux)---------------
            if (int(store.get_config('Heat Transfer'))):
                heatFlux = self.calculate_heat_flux(
                    plateVoltage = dataArray[9], 
                    topTemp = dataArray[1], 
                    botTemp = dataArray[2], 
                    surfaceTemp = dataArray[3], 
                    ambientTemp = dataArray[4])
                dataArray[10] = heatFlux
            else:
                dataArray[10] = 'invalid'

        except AttributeError:{}
            
        except LabJackException as e:
            store.log_event('debug',"A LabJack error occurred in gather_data(): %s" %str(e))

        except Exception as e:
            store.log_event('debug',"An unhandled LabJack error occurred in gather_data(): %s" %str(e))

        try:
            #-----------------------Mass Balance--------------------------
            if (int(store.get_config('Mass')) and validSensors[5]):
                mass = self.balance.get_mass()
                dataArray[6] = mass
            else:
                dataArray[6] = 'invalid'
        except BalanceException as e:
            store.log_event('debug','A Balance error occurred in gather_data(): %s' %str(e))
        except Exception as e:
            store.log_event('debug','An unhandled error occurred in gather_data(): %s' %str(e))
        return dataArray

    def check_sensors(self, store):
        # input:    storage object
        # output:   a boolean array that indicates which sensors are functional, follows the conventional sensor order
        # desc:     checks the state of all sensors before "officially" retrieving data in gather_data()
        # notes:    technically this function encompases the functionality of gather_data(), 
        #           but this is done for ease of use when programming

        # Temperature values for validating sensor readings
        maxTemperature = float(store.get_config('maxTemperature'))
        minTemperature = float(store.get_config('minTemperature'))
        
        sensorStateArray = [0,0,0,0,0,0,0,0,0]


        #------------------------------------Labjack Data-------------------------------------
        try:
            self.labjack = u3.U3()
        except LabJackException as e:
            store.log_event('debug','A LabJack error occurred in check_sensors(): %s' %str(e))
        except Exception as e:
            store.log_event('debug',"An unhandled error occurred in check_sensors(): %s" %str(e))
        else:
            self.set_labjack_config()
            self.labjack.getCalibrationData()
            self.select_current_cutoff(int(self.store.get_config('currentCutoff')))
            try:
                try:
                    vsVoltage = self.get_voltage(self.MEASURED_VS_CHANNEL)

                    if (vsVoltage > 5.1 or vsVoltage < 4.9):
                        store.log_event('debug','Measured Vs is returning a voltage of %fV, which is outside the expected range of 4.9V to 5.1V.' % (vsVoltage))
                except ValueError:
                    store.log_event('debug','An error occurred when reading Vs, are some cables swapped?')
                except Exception as e:
                    store.log_event('debug','An unhandled error occurred when reading Vs: %s' %str(e))
                #----------------------Surface Thermistor Top----------------------
                try:
                    # check top thermistor connection by seeing if voltage reading is reasonable
                    thermVoltage = self.get_voltage(self.TOP_THERMISTOR_CHANNEL)

                    # apply Omega's magic formula
                    lnSurfaceTop = math.log(self.surfaceResistorTop*thermVoltage/(vsVoltage-thermVoltage))
                    thermTemperature = 1/(self.surfaceA + self.surfaceB*lnSurfaceTop + self.surfaceC*lnSurfaceTop*lnSurfaceTop*lnSurfaceTop) - self.kelvinOffset

                    if (thermTemperature <= maxTemperature and thermTemperature >=  minTemperature):
                        sensorStateArray[0] = 1
                    else:
                        sensorStateArray[0] = 0
                        store.log_event('debug','Top Thermistor is returning a temperature of %f, which is outside the expected range of %f to %f.' % (thermTemperature, minTemperature, maxTemperature))
                except ValueError:
                    sensorStateArray[0] = 0
                    store.log_event('debug','An error occurred for Top Thermistor, are some cables swapped?')
                except Exception as e:
                    sensorStateArray[0] = 0
                    store.log_event('debug','An unhandled error occurred for Top Thermistor: %s' %str(e))
                
                #----------------------Surface Thermistor Bottom----------------------
                try:
                    # check bot thermistor connection by seeing if voltage reading is reasonable
                    thermVoltage = self.get_voltage(self.BOT_THERMISTOR_CHANNEL)

                    # apply Omega's magic formula
                    lnSurfaceBot = math.log(self.surfaceResistorBot*thermVoltage/(vsVoltage-thermVoltage))
                    thermTemperature = 1/(self.surfaceA + self.surfaceB*lnSurfaceBot + self.surfaceC*lnSurfaceBot*lnSurfaceBot*lnSurfaceBot) - self.kelvinOffset
                    if (thermTemperature <= maxTemperature and thermTemperature >=  minTemperature):
                        sensorStateArray[1] = 1
                    else:
                        sensorStateArray[1] = 0
                        store.log_event('debug','Bot Thermistor is returning a temperature of %f, which is outside the expected range of %f to %f.' % (thermTemperature, minTemperature, maxTemperature))
                except ValueError:
                    sensorStateArray[1] = 0
                    store.log_event('debug','An error occurred for Bot Thermistor, are some cables swapped?')
                except Exception as e:
                    sensorStateArray[1] = 0
                    store.log_event('debug','An unhandled error occurred for Bot Thermistor: %s' %str(e))

                #----------------------Surface Infrared I2C----------------------
                try:
                    # Infrared sensor send and receive I2C object data
                    infraredData = self.labjack.i2c(0x0, [0x7], NoStopWhenRestarting = True, SDAPinNum = self.INFRARED_SDA_CHANNEL, 
                                                      SCLPinNum = self.INFRARED_SCL_CHANNEL, NumI2CBytesToReceive = 3)
                    I2CInfraredBytes = infraredData['I2CBytes']
                    #print I2CInfraredBytes
                    # Convert I2C Data into temp
                    infraredTemperature = (I2CInfraredBytes[0] + 16*16*I2CInfraredBytes[1])*0.02 - self.kelvinOffset
                    if(I2CInfraredBytes[0] == 255):
                        sensorStateArray[2] = 0
                        store.log_event('debug','Surface Infrared Sensor is unplugged, please plug it back in!.')
                    elif(infraredTemperature <= maxTemperature and infraredTemperature >= minTemperature):
                        sensorStateArray[2] = 1
                    else:
                        sensorStateArray[2] = 0
                        store.log_event('debug','Surface Infrared Sensor is returning a temperature of %f, which is outside the expected range of %f to %f.' % (thermTemperature, minTemperature, maxTemperature))
                except Exception as e:
                    sensorStateArray[2] = 0
                    store.log_event('debug','An unhandled error occurred for Infrared Sensor: %s' %str(e))


                #----------------------Ambient Thermistor----------------------
                try:
                    # check ambient thermistor connection by seeing if voltage reading is reasonable
                    thermVoltage = self.get_voltage(self.AMBIENT_THERMISTOR_CHANNEL)
                    
                    # apply Omega's magic formula
                    lnAmbient = math.log(self.ambientResistor*thermVoltage/(vsVoltage-thermVoltage))
                    thermTemperature = 1/(self.ambientA + self.ambientB*lnAmbient + self.ambientC*lnAmbient*lnAmbient*lnAmbient) - self.kelvinOffset
                    if (thermTemperature <= maxTemperature and thermTemperature >=  minTemperature):
                        sensorStateArray[3] = 1
                    else:
                        sensorStateArray[3] = 0
                        store.log_event('debug','Ambient Thermistor is returning a temperature of %f, which is outside the expected range of %f to %f.' % (thermTemperature, minTemperature, maxTemperature))

                except ValueError:
                    sensorStateArray[3] = 0
                    store.log_event('debug','An error occurred for Ambient Thermistor, are some cables swapped?')
                except Exception as e:
                    sensorStateArray[3] = 0
                    store.log_event('debug','An unhandled error occurred for Ambient Thermistor: %s' %str(e))

                #----------------------Ambient Humidity I2C----------------------
                try:
                    #send & receive I2C humidity and temp data
                    humidity_data = self.labjack.i2c(0x28, [], NoStopWhenRestarting = True, SDAPinNum = self.HUMIDITY_SDA_CHANNEL, SCLPinNum = self.HUMIDITY_SCL_CHANNEL, NumI2CBytesToReceive = 4)
                    I2CBytes = humidity_data['I2CBytes']
                    #Convert I2C data into temp and humidity
                    ambient_temp = -40 + 165.0*(I2CBytes[2]*64 + I2CBytes[3]/16)/pow(2,14)
                    relative_humidity = 100.0*(I2CBytes[0]*256 + I2CBytes[1])/pow(2,14)

                    if(relative_humidity > 100):
                        relative_humidity = relative_humidity - 100
                    if(relative_humidity <= 70 and relative_humidity >= 5):
                        sensorStateArray[4] = 1
                    else:
                        sensorStateArray[4] = 0
                        store.log_event('debug','Ambient Humidity Sensor is returning a value of %f%, which is outside the expected range of 5 to 70%.' % (relative_humidity))
                
                except Exception as e:
                    sensorStateArray[4] = 0
                    store.log_event('debug','An unhandled error occurred for Ambient Humidity Sensor: %s' %str(e))

                #----------------------Voltage of HFG----------------------
                try:
                    # check voltage measuring connection by seeing if voltage reading is reasonable
                    hfgVoltage = self.get_voltage(self.MEASURED_FIELD_VOLTAGE_CHANNEL)

                    if (hfgVoltage <= 5 and hfgVoltage >= 0):
                        sensorStateArray[6] = 1
                    else:
                        sensorStateArray[6] = 0
                        store.log_event('debug','An invalid value of %fV was returned when measuring the field voltage, which is outside the possible range of 0 to 30 kV.' % (hfgVoltage * 6000))
                except Exception as e:
                    sensorStateArray[6] = 0
                    store.log_event('debug','An unhandled error occurred when measuring the field voltage: %s' %str(e))

                #----------------------Current of HFG----------------------
                try:
                    # check current measuring connection by seeing if voltage reading is reasonable
                    hfgVoltage = self.get_voltage(self.MEASURED_FIELD_CURRENT_CHANNEL)
                    hfgCurrent = hfgVoltage * 80.0 # in uA
                    if (hfgCurrent <= 400 and hfgCurrent >= 0):
                        sensorStateArray[7] = 1
                    else:
                        sensorStateArray[7] = 0
                        store.log_event('debug','An invalid value of %fuA was returned when measuring the field current, which is outside the possible range of 0 to 400 uA.' % hfgCurrent)
                except Exception as e:
                    sensorStateArray[7] = 0
                    store.log_event('debug','An unhandled error occurred when measuring the field current: %s' %str(e))

                #----------------------Heating Plate Voltage----------------------
                try:
                    # check heating plate voltage connection by seeing if voltage reading is reasonable
                    dividerVoltage = self.get_voltage(self.MEASURED_PLATE_VOLTAGE)

                    # Vsource = (R1 + R2)/R1 * Vin
                    plateVoltage = (self.plateResistor1 + self.plateResistor2)/self.plateResistor1 * dividerVoltage
                    if (plateVoltage <= 20 and plateVoltage >= 0):
                        sensorStateArray[8] = 1
                    else:
                        sensorStateArray[8] = 0
                        store.log_event('debug','An invalid value of %fV was returned when measuring the plate voltage, which is outside the possible range of 0 to 20 V.' % plateVoltage)
                except Exception as e:
                    sensorStateArray[8] = 0
                    store.log_event('debug','An unhandled error occurred when measuring the plate voltage: %s' %str(e))

            except LabJackException as e:
                store.log_event('debug',"A LabJack error occurred in check_sensors(): %s" %str(e))
            except Exception as e:
                store.log_event('debug','An unhandled error occurred in check_sensors(): %s' %str(e))
        #------------------------------Balance Data---------------------------------  
        try:
            self.balance = Balance()
        except BalanceException as e:
            sensorStateArray[5] = 0
            store.log_event('debug','A Balance error occurred in check_sensors(): %s' %str(e))
        else:
            try:
                #----------------------Mass Balance----------------------
                mass = self.balance.get_mass()
                sensorStateArray[5] = 1
            except AttributeError as e: # The mass isn't connected
                sensorStateArray[5] = 0
                store.log_event('debug','A Balance error occurred in check_sensors(), is it plugged in? %s' %str(e))
            except IndexError as e: # The mass isn't turned on
                sensorStateArray[5] = 0
                store.log_event('debug','A Balance error occurred in check_sensors(), is it powered on or is it being overloaded? %s' %str(e))
            except Exception as e:
                store.log_event('debug','An unhandled Balance error occurred in check_sensors(): %s' %str(e))
        return sensorStateArray

    def get_voltage(self, positiveChannel, negativeChannel = 31, settle = True):
        # input:    positiveChannel, negativeChannel, settle
        # output:   returns a voltage value
        # desc:     polls the labjack for the voltage of a positive channel relative to the negative channel
        # notes:
        if self.labjack:
            return self.labjack.binaryToCalibratedAnalogVoltage(bits = self.labjack.getFeedback(u3.AIN(positiveChannel, negativeChannel, settle))[0], isLowVoltage = positiveChannel/4)
        else:
            self.store.log_event('debug','Attempted to get voltage info when a labjack wasn\'t plugged in, this should never happen')

    def set_labjack_config(self):
        # input:    no arguments passed
        # output:   nothing returned
        # desc:     configures labjack pins; defaults to analog in, sets any I2C channels to digital in
        # notes:    If you (a dev) are adding sensors, YOU NEED TO CONFIGURE THE PINS HERE!
        #           this should be called upon creation of a labjack object
        #           Designed to look at channels selected in the config file and set FIOAnalog and EIOAnalog appropriately
        try:
            # set all channels to analog in, then set the handful of digital ins to zero
            analogSelect = int(math.pow(2, 16) - 1)
            # infrared
            analogSelect = int(analogSelect - math.pow(2, self.INFRARED_SCL_CHANNEL) - math.pow(2, self.INFRARED_SDA_CHANNEL))
            # humidity
            analogSelect = int(analogSelect - math.pow(2, self.HUMIDITY_SCL_CHANNEL) - math.pow(2, self.HUMIDITY_SDA_CHANNEL))
            FIO = 0x00FF & analogSelect
            EIO = analogSelect / 256
            self.labjack.configIO(
                FIOAnalog = FIO, 
                EIOAnalog = EIO)
            return 0

        except AttributeError:
            self.store.log_event('debug','An error occurred in set_labjack_config(), is the labjack plugged in?')
        except LabJackException as e:
            self.store.log_event('debug',"A LabJack error occurred in set_labjack_config(): %s" %str(e))
        except Exception as e:
            self.store.log_event('debug','An unhandled error occurred in set_labjack_config(): %s' %str(e))

    def calculate_heat_flux(self, plateVoltage, topTemp, botTemp, surfaceTemp, ambientTemp):
        # input:    plateVoltage, topTemp, botTemp, surfaceTemp, ambientTemp
        # output:   if successful, returns heat flux
        # desc:     calculates the heat flux, made purely for your readability
        # notes:               
        try:
            plateArea = float(self.store.get_config('plateArea'))
            plateResistance = float(self.store.get_config('plateResistance'))
            polyConduct = float(self.store.get_config('polyConduct'))
            plateEmiss = float(self.store.get_config('plateEmiss'))
            stephBoltzConst = float(self.store.get_config('stephBoltzConst'))
            heatFlux = (math.pow(plateVoltage, 2)/(plateArea * plateResistance) - polyConduct/plateEmiss * (topTemp - botTemp) - stephBoltzConst * (math.pow(surfaceTemp + self.kelvinOffset, 4) - math.pow(ambientTemp + self.kelvinOffset, 4)))/(surfaceTemp - ambientTemp)
        except Exception as e:
            self.store.log_event('debug','An error occurred in calculate_heat_flux(%f, %f, %f, %f, %f): %s' %(plateVoltage, topTemp, botTemp, surfaceTemp, ambientTemp, str(e)))
        else:
            return heatFlux

    def set_hfg_voltage_feedback(self, desiredVoltage = 0, localMode = False, errorVoltage = 0, maxCalls = 20): 
        # input:    receives a user-determined voltage (will convert from 0-5V or 0-30kV)
        # output:   nothing, but sets the field voltage accordingly over chosen DAC (probs DAC0)
        # desc:     given a voltage range of either (0-5V) or (0-30kV), sets the HV field;
        #           also measures the HV supply's "output" voltage, finds error, and does a feedback loop
        # notes:    1. it seems to be accurate enough for now, within roughly .005 volts 
        #           2. DON'T overload the maxCalls parameter when using, it's done this way for recursion
        try:

            # for future devs, you may find that the threading we've done is stupid. you may want to add
            # additional checks for thread count and kill old voltage threads if needed - idk though
            #print threading.activeCount()
            #threading.currentThread()._Thread__delete()
            #print threading.activeCount()
            #print threading.currentThread().getName()

            if(localMode == False and threading.active_count() == 2):
                if(maxCalls > 0):
                    # convert from 0-30kV to 0-5V if necessary
                    if (desiredVoltage < 0 or desiredVoltage > 30000):
                        self.store.log_event('debug','The desired voltage was %s, which falls outside the feasible range of 0V to 30000V' %desiredVoltage)
                        return
                    # assume the user will never want a field voltage of less than 100 (100/30000 * 5 = .016667)
                    if (desiredVoltage < .017):
                        desiredVoltage = .017

                    if (desiredVoltage > 5):
                        desiredVoltage = desiredVoltage / 6000.0
                    bits = self.labjack.voltageToDACBits(volts = desiredVoltage + errorVoltage * 0.85, dacNumber = self.HIGH_VOLTAGE_SET_CHANNEL, is16Bits = True)
                    self.labjack.getFeedback(u3.DAC16(Dac = self.HIGH_VOLTAGE_SET_CHANNEL, Value = bits))
                    if(maxCalls == 20):
                        time.sleep(2)
                    else:
                        time.sleep(.2) ## give the voltage a bit to settle
                    measuredVoltage = self.get_voltage(self.MEASURED_FIELD_VOLTAGE_CHANNEL)      
                    errorVoltage = desiredVoltage - measuredVoltage
                    #print ("[Measured:%f | Error:%f]" %(measuredVoltage, errorVoltage))
                    if (errorVoltage > .005 or errorVoltage < -.005): # should provide accuracy within %0.1 of the desired voltage
                        self.set_hfg_voltage_feedback(desiredVoltage, False, errorVoltage, maxCalls - 1)
                    else:
                        return 0
                elif(maxCalls == 0 and errorVoltage > .1):
                    # voltage wasn't able to settle, either a result of the generator being in manual (local) mode or the safety cutoff being tripped
                    comparatorVoltage = self.get_voltage(self.SAFETY_CUTOFF_COMPARATOR)
                    if(comparatorVoltage < 1):
                        raise HardwareIOException('[ERROR2] Unable to remotely control the voltage, safety cutoff was activated.')
                    else:
                        raise HardwareIOException('[ERROR1] Unable to remotely control the voltage, is the supply on, is it in remote mode, and is the DAC pin correct?')
                        
                else:
                    # voltage wasn't able to settle in 20 calls
                    return 1 
        except AttributeError as e:
            self.store.log_event('debug','A LabJack error occurred in set_hfg_voltage_feedback(%f, %f): %s' %(desiredVoltage, errorVoltage, str(e)))
            return 1
        except KeyError as e:
            self.store.log_event('debug','A Labjack error occurred in set_hfg_voltage_feedback(%f, %f): %s' %(desiredVoltage, errorVoltage, str(e)))
            return 1
        except LabJackException as e:
            self.store.log_event('debug','A LabJack error occurred in set_hfg_voltage_feedback(%f, %f): %s' %(desiredVoltage, errorVoltage, str(e)))


    def set_hfg_voltage_lookup(self, desiredVoltage, localMode = False):
        # input:    receives a user-determined voltage
        # output:   nothing, but sets the field voltage accordingly over chosen DAC (probs DAC0)
        # desc:     As of 4/6/2016, this function is not in use and has been included as a backup to the feedback function
        #           Acts like a lookup table for voltages - definitely not ideal
               
        try:
            #convert voltage given in volts to kV
            desiredVoltage = int(desiredVoltage / 1000)
            voltageTable = [0/6.0, 1/6.0, 2/6.0, 3/6.0, 4/6.0, 5/6.0, 6/6.0, 7/6.0, 8/6.0, 9/6.0, 
                            10/6.0, 11/6.0, 12/6.0, 13/6.0, 14/6.0, 15/6.0, 16/6.0, 17/6.0, 18/6.0, 19/6.0,
                            20/6.0, 21/6.0, 22/6.0, 23/6.0, 24/6.0, 25/6.0, 26/6.0, 27/6.0, 28/6.0, 29/6.0, 30/6.0]

            bits = self.labjack.voltageToDACBits(
                            volts = voltageTable[desiredVoltage], 
                            dacNumber = self.HIGH_VOLTAGE_SET_CHANNEL, 
                            is16Bits = True)
            self.labjack.getFeedback(u3.DAC16(Dac = self.HIGH_VOLTAGE_SET_CHANNEL, Value = bits))
            return 0
        except Exception as e:
            self.store.log_event('debug','An unhandled error occurred in set_hfg_voltage_lookup(%f): %s' %(desiredVoltage, str(e)))
            return 1

    def select_current_cutoff(self, currentuA = 200):
        # input:    receives a current cutoff (in uA)
        # output:   nothing, but sets the voltage (0-5V) that's proportional to the possible current of the HV supply
        # desc:     This sets a voltage that represents the current going through the supply;
        #           this voltage is run through a comparator/sr-latch circuit; 
        #           if this current threshold is hit, the supply is disabled via hardware
        # notes:     
                
        try:
            selectVoltage = (currentuA/400.0) * 5
            bits = self.labjack.voltageToDACBits(
                volts = selectVoltage, 
                dacNumber = self.CURRENT_CUTOFF_SET_CHANNEL, 
                is16Bits = True)
            self.labjack.getFeedback(u3.DAC16(Dac = self.CURRENT_CUTOFF_SET_CHANNEL, Value = bits))
            return 0
        except Exception as e:
            self.store.log_event('debug','An unhandled error occurred in select_current_cutoff(%f): %s' %(currentuA, str(e)))
            return 1
            
def hardwareIO_driver():
    # Desc: a simple test driver that creates a hardware object and runs gather_data()
    h = HardwareIO(Storage())
    #h.balance.zero_balance()
    #h.balance.lock_screen()
    #time.sleep(10)
    #h.balance.unlock_screen()
    while (False): 
        #print h.check_sensors(Storage())
        #print '\n'
        #h.select_current_cutoff(10)
        #h.set_hfg_voltage_feedback(0)
        time.sleep(3)

#hardwareIO_driver()