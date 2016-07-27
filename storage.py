import csv
import urllib
import zipfile
import os
import threading
import logging
import Tkinter as tk
import tkFileDialog
from tkMessageBox import askretrycancel
from os.path import isfile,join,isdir
from os import makedirs
import shutil
from shutil import move
from time import strftime
from Queue import Queue
#The Storage class will be child of the Top class. It creates csv files to store test run data and provides read functionality for accessing previous
#test run data

class StorageException(Exception):
    # desc:     The very simple custom Exception class for Storage
    # purpose:  Allows Storage to raise events that need to be known by Storage owners
	def __init__(self, message):
		self.message = str(message)
	def __str__(self):
		return self.message

class Storage():
	def __init__(self):
		# input:    nothing!
		# output:  	nothing, just initializes members 
		# desc:  	a constructor for the Storage class. It sets up the first two member variables, timeformat and filepath, which will be used to generate
		#			test timestamps. If the filepath where Storage stores the test run csv data files ("C:\EHD\Tests\") is not already created, __init__ creates it on
		#			the user's computer as a new directory.  
		# notes:
		self.timeformat = '%Y%m%d_%H%M%S'
		self.configFile = 'EHD_config.txt'
		self.debugFile = 'EHD_debug.txt'
		self.helpUrl = 'https://bitbucket.org/grovecityehd/ehd-application/wiki/Home'
		self.csvFileViewUrl = 'http://www.nirsoft.net/utils/csvfileview-x64.zip'
		self.csvFileViewFolder = 'C:\\EHD\\CSVFileView\\'
		self.csvFileViewExe = self.csvFileViewFolder + 'CSVFileView.exe'
		self.csvFileViewZip = self.csvFileViewFolder + 'csvfileview-x64.zip'
		self.currentTestFolder = 'C:\\EHD\\Current\\'
		self.testsFolder = 'C:\\EHD\\Tests\\'
		self.configFolder = 'C:\\EHD\\'
		self.logFolder = 'C:\\EHD\\Log\\'
		self.debug_queue = Queue(100)

		# If the directories don't exist, make them!
		if not isdir(self.configFolder):
			makedirs(self.configFolder)
		if not isdir(self.csvFileViewFolder):
			makedirs(self.csvFileViewFolder)
		if not isdir(self.testsFolder):
			makedirs(self.testsFolder)
		if not isdir(self.logFolder):
			makedirs(self.logFolder)

		# if the files don't exist, remake the default ones!
		if not isfile(self.configFolder + self.configFile):
			self.default_config()

		# threading this task is important to not hold the app from loading other resources while waiting on this to download
		if not isfile(self.csvFileViewExe):
			t = threading.Thread(target=self.download_extract_csvViewer, args=())
			t.start()

		self.current_logger_name = 'App_Debug'
		self.logger = logging.getLogger(self.current_logger_name)
		self.current_log_filename = self.logFolder + 'App_Log.log'
		self.hdlr = logging.FileHandler(self.current_log_filename)
		formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
		self.hdlr.setFormatter(formatter)
		self.logger.addHandler(self.hdlr)
		self.logger.setLevel(logging.DEBUG)
		with open(self.current_log_filename, 'w'):
			pass

	def log_event(self,error_type,error):
		if not isdir(self.configFolder):
			makedirs(self.configFolder)
		if not isdir(self.logFolder):
			makedirs(self.logFolder)
		self.logger = logging.getLogger(self.current_logger_name)
		if(self.debug_queue.full()):
			self.debug_queue.get()
			self.debug_queue.put(error)
		else:
			self.debug_queue.put(error)
		if(error_type == 'debug'):
			self.logger.debug(error)


	def test_init(self,parameters,testInfo):
		# input:    test parameters, testInfo
		# output:   nothing
		# desc:     a member function of the Storage class. It initializes a new test by generating a timestamp of the start time and creating a new 
		#			csv file. test_init takes in an array of the user-selected data values to be read in the test (ex. Humidity, Top Temp, Bot Temp, Mass, etc).
		#			These are written to the csv file as the first line and define what each column in the rows of data represents.
		# notes:    

		self.currentTimestamp = strftime(self.timeformat)
		self.currentTestTimestamp = self.currentTimestamp + '.csv'
		self.currentTestFilename = self.testsFolder + self.currentTestTimestamp
		#self.write_entry(testInfo)
		self.write_entry(parameters)

		self.currentLogger = self.logFolder + self.currentTimestamp
		self.current_log_filename = self.currentLogger + '.log'
		self.current_logger_name = self.currentTimestamp
		self.logger = logging.getLogger(self.current_logger_name)
		hdlr = logging.FileHandler(self.current_log_filename)
		formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
		hdlr.setFormatter(formatter)
		self.logger.addHandler(hdlr)
		self.logger.setLevel(logging.DEBUG)
		self.logger.debug('--- TEST HAS BEGUN ---')
		log_file = open(self.current_log_filename,'a')
		log_file.write('--- TEST HAS BEGUN ---\n')
		log_file.close()

	def write_entry(self,entry):
		# input:    data entry (meant for a csv file)
		# output:   nothing! just writes to a file
		# desc:     a member function of the Storage class. It takes in a row of data in an array format and appends that row to the currently test's
		#			csv file as a new row.
		# notes:    		
		try:
			if not isdir(self.configFolder):
				makedirs(self.configFolder)
			if not isdir(self.testsFolder):
				makedirs(self.testsFolder)
			writefile = open(self.currentTestFilename,"ab")
		except IOError as e:
			# the user has the file open
			if ("[Errno 13]" in str(e)): 
				self.log_event('debug',"Test file is in use by another process: %s" %str(e))
			# the user has deleted the current test file
			if ("[Errno 2]" in str(e)): 
				self.log_event('debug',"The test file or directory was deleted: %s" %str(e))
			raise StorageException(e)
		else:
			writer = csv.writer(writefile)
			writer.writerow(entry)
			writefile.close()

	def read_test(self,test):
		# input:   	test name 
		# output:   returns an array of arrays of test data
		# desc:     a member function of the Storage class. It takes in a timestamp of a previous test in the timeformat specified in __init__ and 
		#			stores all the lines of data in a two-dimensional array (with each index containing an array that represents a row of data from the set), which
		#			it returns.
		# notes:    This currently isn't used, but may be helpful if future devs want to add a "view all tests" window
		#TODO: does an exception need to be written for this?

		timestamp = test + '.csv'
		readfile = open(self.testsFolder + timestamp,"rb")
		reader = csv.reader(readfile)
		read_test_array = []
		for row in reader:
			read_test_array.append(row)
		return read_test_array

	def read_all(self):
		# input:    nothing!
		# output:   returns all tests (files) that exist in a directory
		# desc:     a member function of the Storage class. It inspects the folder containing all of the csv test files and returns them as a list of 
		#			timestamps in a readable format (parsed by the parse_timestamps function). Additionally, read_all stores all of the raw filenames in the member 
		#			variable self.filenames in case it is needed for future reference. 
		# notes:    I don't think this is actually used anywhere in the release as of 4/22/16

		onlyfiles = [f for f in listdir(self.testsFolder) if isfile(join(self.testsFolder, f))]
		filenames = onlyfiles
		dates = self.parse_timestamps(onlyfiles)
		all_info = []
		i = 0
		for date in dates:
			date_file = []
			date_file.append(date)
			date_file.append(filenames[i])
			all_info.append(date_file)
			i = i+1
		return all_info


	def open_tests(self):
		# input:	nothing  
		# output:   nothing!
		# desc:     opens a tkinter window for viewing all files (of .csv type) in a directory
		# notes:  
		if not isdir(self.configFolder):
			makedirs(self.configFolder)
		if not isdir(self.testsFolder):
			makedirs(self.testsFolder)
		options = {}
		options['defaultextension'] = '.csv'
		options['filetypes'] = [('all files', '.*'), ('CSV files', '.csv')]
		options['initialdir'] = 'C:\\EHD\\Tests\\'
		options['initialfile'] = 'date_time.csv'
		file = tkFileDialog.askopenfile(mode='r', **options)
		if file:
			os.startfile(file.name)

	def parse_timestamps(self,names,):
		# input:    a list of raw file names
		# output:   returns the formatted time stamp
		# desc:     a member function of the Storage class. It is called by the read_all function and takes in a list of raw filenames which it 
		#			parses and converts to a more readable format (YYYY-MM-DD HH:MM:SS). 
		# notes:    Also not sure this is used as of 4/22/16

		name_arr = []
		for name in names:
			year = month = day = hour = minute = second = ''
			for i in range(0,4):
				year = year+name[i]
			for i in range(4,6):
				month = month+name[i]
			for i in range(6,8):
				day = day+name[i]
			for i in range(9,11):
				hour = hour+name[i]
			for i in range(11,13):
				minute = minute+name[i]
			for i in range(13,15):
				second = second+name[i]
			name_arr.append("%s-%s-%s %s:%s:%s" % (year,month,day,hour,minute,second))
		return name_arr

	def open_config(self):
		# input:   	nothing 
		# output:   nothing!
		# desc:     opens the config file, called from the menu bar found in View
		# notes:  
		 
		# if the config file is deleted and an attempt is made to open it, create a default one
		if not isdir(self.configFolder):
			makedirs(self.configFolder)
		if not isfile(self.configFolder + self.configFile):
			#self.logger.debug('%s could not be found, creating a new default one' %self.configFile)
			self.log_event('debug','%s could not be found, creating a new default one' %self.configFile)
			self.default_config()
		os.startfile(self.configFolder + self.configFile)

	def default_config(self):
		# input: 	nothing
		# output: 	returns nothing, but creates a default config file
		# desc:     creates a default configuration file, is called when the config file can't be found
		# notes:
		
		self.set_config('SAFETY_CUTOFF_COMPARATOR', '12') # The AIN pin for measuring if the HV field was disabled by the comparator
		self.set_config('TOP_THERMISTOR_CHANNEL', '14') # The AIN pin for measuring the Top Thermistor voltage
		self.set_config('BOT_THERMISTOR_CHANNEL', '13') # The AIN pin for measuring the Bot Thermistor voltage
		self.set_config('AMBIENT_THERMISTOR_CHANNEL', '15') # The AIN pin for measuring the Ambient Thermistor voltage
		self.set_config('INFRARED_SCL_CHANNEL', '7') # The DIN pin for measuring the clock signal of the Infrared sensor
		self.set_config('INFRARED_SDA_CHANNEL', '6') # The DIN pin for measuring the data signal of the Infrared sensor
		self.set_config('HUMIDITY_SCL_CHANNEL', '5') # The DIN pin for measuring the clock signal of the Humidity sensor
		self.set_config('HUMIDITY_SDA_CHANNEL', '4') # The DIN pin for measuring the data signal of the Humidity sensor
		self.set_config('MEASURED_VS_CHANNEL', '0') # THE AIN pin for measuring Vs (used in most voltage division calcs)
		self.set_config('HIGH_VOLTAGE_SET_CHANNEL', '0') # The DAC pin for setting the voltage of the HFG supply
		self.set_config('CURRENT_CUTOFF_SET_CHANNEL', '1') # The DAC pin used for setting the reference voltage of the current cutoff
		self.set_config('MEASURED_PLATE_VOLTAGE', '1') # The AIN pin for measuring the voltage of the heating plate
		self.set_config('MEASURED_FIELD_VOLTAGE_CHANNEL', '2') # The AIN pin for measuring the Vout from the HFG representative of the HV field
		self.set_config('MEASURED_FIELD_CURRENT_CHANNEL', '3') #The AIN pin for measuring the Iout from the HFG representative of the current flow
		self.set_config('plateResistor1', '12000') # R1 for calculating plate voltage (parallel voltage divider)
		self.set_config('plateResistor2', '100000') # R2 for calculating plate voltage (parallel voltage divider)
		self.set_config('surfaceResistorTop', '11990') # R for measuring resistance of top thermistor using voltage division
		self.set_config('surfaceResistorBot', '11998') # R for measuring resistance of bot thermistor using voltage division
		self.set_config('ambientResistor', '99955') # R for measuring resistance of ambient thermistor using voltage division
		self.set_config('currentCutoff', '200') # current cutoff threshold, in uA
		self.set_config('ambientA', '1.032e-03') # magic constants for our Omega thermistor when converting resistance to temperature
		self.set_config('ambientB', '2.387e-04') # ditto
		self.set_config('ambientC', '1.580e-07') # ditto
		self.set_config('surfaceA', '1.468e-03') # ditto
		self.set_config('surfaceB', '2.383e-04') # ditto
		self.set_config('surfaceC', '1.007e-07') # ditto
		self.set_config('kelvinOffset', '273.15') # kelvin offset for converting from kelvin to C
		self.set_config('DefaultTestName','0') # default test name on first run of software
		self.set_config('Surface Temperature','1') # indicates if the user has chosen to take Surface Temp data (1 is yes, 0 is no)
		self.set_config('Ambient Temperature','1') # indicates if the user has chosen to take Ambient Temp data (1 is yes, 0 is no)
		self.set_config('Top Temperature','1') # indicates if the user has chosen to take top Temp data (1 is yes, 0 is no)
		self.set_config('Bottom Temperature','1') # indicates if the user has chosen to take bot Temp data (1 is yes, 0 is no)
		self.set_config('Voltage','1') # indicates if the user has chosen to take supply voltage data (1 is yes, 0 is no)
		self.set_config('Current','1') # indicates if the user has chosen to take supply current data (1 is yes, 0 is no)
		self.set_config('Mass','1') # indicates if the user has chosen to take mass data (1 is yes, 0 is no)
		self.set_config('Humidity','1') # indicates if the user has chosen to take humidity data (1 is yes, 0 is no)
		self.set_config('Heat Transfer','1') # indicates if the user has chosen to calculate heat flux data (1 is yes, 0 is no)
		self.set_config('Plate Voltage','1') # indicates if the user has chosen to take plate voltage data (1 is yes, 0 is no)		
		self.set_config('Test Name','') # actual name of the test
		self.set_config('Test Duration','24:00') # duration of the currently running or most recent test
		self.set_config('polyConduct', '.033') # heat flux constant: conductivity of the polystyrene
		self.set_config('plateArea', '0.0225') # heat flux constant: area of the plate (in m^2)
		self.set_config('plateResistance', '18') # heat flux constant: resistance of the heating plate
		self.set_config('plateEmiss', '1') # heat flux constant: emissivity of the surface
		self.set_config('stephBoltzConst', '5.68e-08') # heat flux constant: some constant, idk what it is
		self.set_config('maxTemperature', '70') # max temperature before sensors believe they are receiving incorrect data
		self.set_config('minTemperature', '0') # min temperature before sensors believe they are receiving incorrect data
		self.set_config('Sample Rate','10') # user defined sample rate of the current or most recent test
		self.set_config('Sample Unit','second(s)') # unit of sample rate

	def get_config(self, key):
		# input: 	a key (unique variable name) of type string
		# output: 	returns a value of type string 
		# desc:     when given a key, returns the value of the key from the config file
		# notes:    If this is called but no config file exists, a default is created
		#self.logger = logging.getLogger(self.current_logger_name)
		# if config isn't found, make a new one
		if not isdir(self.configFolder):
			makedirs(self.configFolder)
		if not isfile(self.configFolder + self.configFile):
			#self.logger.debug('%s could not be found, creating a new default one' %self.configFile)
			self.log_event('debug','%s could not be found, creating a new default one' %self.configFile)
			self.default_config()

		# create the searchable dictionary
		f = open(self.configFolder + self.configFile, 'r')
		dictionary = {}
		for line in f:
			if len(line.rstrip()) != 0:
				x = line.split(": ")
				a = x[0]
				b = x[1]
				dictionary[a] = b
		f.close()
		# return desired value
		return dictionary[key]
	
	def set_config(self, key, value):
		# input: 	a key and the desired value for that key, both of type string
		# output: 	returns nothing, modifies the config file  
		# desc:     reads in the current config file as a dict, asigns the requested value to the given key,
		#			wipes the file, and reinserts the updated dict
		# notes:    

		# make a new file if it doesn't exist
		if not isdir(self.configFolder):
			makedirs(self.configFolder)
		if not isfile(self.configFolder + self.configFile):
			f = open(self.configFolder + self.configFile, 'w')
			f.close()
		retry = True
		while(retry == True):
			try:
				f = open(self.configFolder + self.configFile, 'r+')
				# create the searchable dictionary
				dictionary = {}
				for line in f:
					if len(line.strip("\n")) != 0:
						x = line.split(": ")
						a = x[0]
						b = x[1]
						dictionary[a] = b
				# set the desired dictionary key/value pair
				dictionary[key] = value + "\n"
				# wipe the file
				f.seek(0)
				f.truncate()

				# re-store the dictionary
				for key in sorted(dictionary.keys(), reverse=False):
					f.write(key + ": " + dictionary[key])
				f.close()
				retry = False
				return
			except Exception as e:
				retry = askretrycancel("Critical Error", "%s\nPlease close the config file and press 'ok'. In the future use a \ntext editor that doesn't lock the file (i.e. don't use Word)" %str(e))
				if (retry == False):
					quit()

	def open_help(self):
		# input:    nothing!
		# output:   nothing!
		# desc:     opens a file browser to the help wiki
		# notes:    also, the fact that I'm commenting this function feels stupid
		os.startfile(self.helpUrl)

	def open_current_test(self):
		# input:    nothing!
		# output:   nothing!
		# desc:     Opens a viewer of the test currently running, requires a new thread 
		#			because this is essentially spawning a new process, which would lock up tkinter
		# notes:  	
		t = threading.Thread(target=self.open_current_test_embedded, args=())
		t.start()

	def open_current_test_embedded(self):
		# input:    nothing!
		# output:   nothing!
		# desc:     the guts of opening the current test viewer, if the viewer doesn't exist, it creates
		#			the appropriate directories and attempts to download/extract it using download_extract_csvViewer()
		# notes:  
		if not isdir(self.configFolder):
			makedirs(self.configFolder)
		if not isdir(self.csvFileViewFolder):
			makedirs(self.csvFileViewFolder)
		if not isfile(self.csvFileViewExe):
			self.download_extract_csvViewer()
		try:
			os.system("%s /load %s" %(self.csvFileViewExe, self.currentTestFilename))
		except Exception as e:
			self.log_event('debug',"Couldn't run %s, did it download/unzip correctly?\n%s" %(self.csvFileViewExe, e))

	def download_extract_csvViewer(self):
		# input:    nothing!
		# output:   nothing!
		# desc:     called when the csvFileViewer doesn't exist; this fetches it from the internet and unzips it.
		# notes:  
		try:
			urllib.urlretrieve(url=self.csvFileViewUrl,filename=self.csvFileViewZip)
		except Exception as e:
			self.log_event('debug',"Couldn't retrieve %s, do you have internet?\n%s" %(self.csvFileViewZip, e))
		else:
			try:
				z = zipfile.ZipFile(self.csvFileViewZip, 'r')
				z.extractall(self.csvFileViewFolder)
				z.close()
				os.remove(self.csvFileViewZip)
			except Exception as e:
				self.log_event('debug',"Couldn't extract %s, was the zip deleted after downloading?\n%s" %(self.csvFileViewExe, e))