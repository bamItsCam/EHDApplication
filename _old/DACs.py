import u3
d = u3.U3()
d.getCalibrationData()

DAC0_VALUE = d.voltageToDACBits(2, dacNumber = 0, is16Bits = False)
d.getFeedback(u3.DAC0_8(DAC0_VALUE))        # Set DAC0
