from serial import Serial
import serial.tools.list_ports
import time
import re
# I wrote this for Python 2.7. Python's serial module, which does not come with the standard installation, can be found here:
# PySerial: https://pypi.python.org/pypi/pyserial
# install it by navigating to the folder where the setup file is located in a command window and typing "python setup.py install"
# ----------------------------------------------------------------------------------------------------------------------------------------------
# the Balance class is a child of the serial.Serial python module. It provided specialized functionality for the Practum Balance that we
# will be using

class BalanceException(Exception):
	def __init__(self, message):
		self.message = str(message)
	def __str__(self):
		return self.message

class Balance(Serial):
	# __init__ is the constructor for the Balance class. It locates the Practum device's com port (if it exists) and opens it
	# with the correct serial parameters
	def __init__(self, *args, **kwargs):
		self.connect_to_balance(args, kwargs)

	def connect_to_balance(self,args,kwargs):
		# input:    args, kwargs
		# output:   nothing!
		# desc:     attempts to connect and configure the balance over a serial connection. This handles all errors relating
		#			to the balance and raises its concerns to the wner of the Balance object
		# notes:	the "jet fuel can't melt steel beams" identifier was Cameron's idea

		ports_list = list(serial.tools.list_ports.comports())
		com_port = 'None'
		for i in ports_list:
			if 'USB CDC serial port emulation' in i[1]:
				com_port = i[0]
				break
		if com_port == 'None':
			raise BalanceException('Balance not found')
		else:
			kwargs['port'] = com_port
			kwargs['baudrate'] = 9600
			kwargs['timeout'] = 1
			try:
				Serial.__init__(self, *args, **kwargs)
			except Exception as e:
				ID = "jet fuel can't melt steel beams"
			else:
				self.write([27,120,49,95])
				ID = self.readline()
			if (ID != 'Mod.  PRACTUM2101-1S\r\n' and ID != "jet fuel can't melt steel beams"):
				raise BalanceException('Balance is not powered on')

	def get_mass(self,wait_time=10):
		# input:    takes in a timeout value
		# output:   nothing!
		# desc:     sends a command to the balance and receives a mass reading from the Practum device
		# notes: 	the timeout feature isn't used...
		self.close()
		self.timeout = wait_time
		self.open()
		self.flushInput()
		self.write([27,80])
		raw_data = self.readline()
		self.close()
		data = self.parse_raw_data(raw_data)
		return data

	def zero_balance(self):
		# input:    nothing!
		# output:   nothing!
		# desc:     sends a command to the balance to zero it
		# notes: 
		self.close()
		self.open()
		self.flushInput()
		self.write([27,84])
		self.close()

	def lock_screen(self):
		# input:    nothing!
		# output:   nothing!
		# desc:     sends a command to the balance to lock the touch screen
		# notes: 	this currently is unused, but may be useful if the user reports a tendency of them 
		#			accidentally touching the screen and messing up the balance
		self.close()
		self.open()
		self.flushInput()
		self.write([27,79])
		self.close()

	def unlock_screen(self):
		# input:    nothing!
		# output:   nothing!
		# desc:     sends a command to the balance to unlock the touch screen
		# notes: 	this currently is unused, but may be useful if the user reports a tendency of them 
		#			accidentally touching the screen and messing up the balance
		self.close()
		self.open()
		self.flushInput()
		self.write([27,82])
		self.close()

	# parse_raw_data is a member function of the Balance class. It parses the data string that is read in from the Practum device
	# and returns the data value as a float with precision of .1
	def parse_raw_data(self,raw_data):
		data = re.findall("\d+\.\d+", raw_data)
		data_sign = re.findall("-",raw_data)
		if len(data_sign) > 0:
			data[0] = data_sign[0] + data[0]
		return float(data[0])
