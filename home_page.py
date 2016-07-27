import Tkinter as tk
from PIL import Image, ImageTk
import ttk
from tkMessageBox import showinfo,showerror,askokcancel,askretrycancel
from storage import Storage
from test_params_window import TestParamsWindow
from heatflux_params_window import HeatfluxParamsWindow
from hardwareIO import HardwareIO
import time
from test import *
import os

# Author:   Abigail Liff
# Date:     4/13/16t
# Desc:     This is the HomePage class, which is inherited from ttk.Frame. It is the tab that comes into focus when the application
#			is first started and contains displays to view the current test information, sensor connectivity, and test notes.
# Notes: 

class HomePage(ttk.Frame):
	# name: __init__
    # input:    parent (type: ttk.Notebook), hardwareIO (type: HardwareIO), storage (type: Storage), debug_page (type: DebugPage),
    #			data_page (type: DataPage)
    # output    nothing
    # desc:     The constructor for the HomePage class
    # purpose:  Runs the parent constructor, sets up the geometry of the Home tab, and initializes the sensor status panel by running
    # 			check_sensors. 
	def __init__(self,parent,hardwareIO,storage,debug_page,data_page=None):
		# Parent Constructor
		ttk.Frame.__init__(self,parent)

		# Member object initialization
		self.parent = parent
		self.data_page = data_page
		self.debug_page = debug_page
		self.store = storage
		self.hardwareIO = hardwareIO

		# Geometry initialization

		self.config(padding=30)
		tk.Grid.columnconfigure(self, 0, uniform=1,weight=1)
		tk.Grid.columnconfigure(self, 1,uniform=1,weight=1)
		tk.Grid.columnconfigure(self, 2, uniform=1,weight=1)
		tk.Grid.columnconfigure(self, 3, uniform=1,weight=1)
		tk.Grid.columnconfigure(self, 4, uniform=1,weight=1,minsize=200)
		tk.Grid.columnconfigure(self,5,uniform=1,weight=1)
		tk.Grid.columnconfigure(self,6,uniform=1,weight=1)
		tk.Grid.columnconfigure(self,7,uniform=1,weight=1)
		tk.Grid.columnconfigure(self,8,uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 0, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 1, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 2, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 3, uniform=1,weight=5)
		tk.Grid.rowconfigure(self, 4, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 5, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 6, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 7, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 8, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 9, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 10, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 11, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 12, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 13, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 14, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 15, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 16, uniform=1,weight=1)

		# Parameters list, which are used for config file IO, writing to various screens, etc.
		self.parameter_list = ["Top Temperature","Bottom Temperature","Surface Temperature","Ambient Temperature","Humidity","Mass","Voltage","Current","Plate Voltage"]
		self.parameter_list_2 = ["Surface Temperature","Ambient Temperature","Voltage","Current","Humidity","Mass","Plate Voltage"]
		self.parameter_list_3 = ["Time: ","Top Temperature: ","Bottom Temperature: ","Surface Temperature: ","Ambient Temperature: ","Humidity: ","Mass: ","Voltage: ","Current: ","Plate Voltage: ","Heat Transfer: "]

		# Geometry initialization - Labels and Separators
		tk.Label(self,text="Test Setup",font=("Helvetica", 20)).grid(row=0,column=0,columnspan=9)
		s = ttk.Separator(self, orient=tk.HORIZONTAL)
		s.grid(row=1,column=0,columnspan=9,sticky=tk.E+tk.W)
		tk.Label(self,text="Current Test Parameters",font=("Helvetica",12)).grid(row=2,column=0,columnspan=4)
		tk.Label(self,text="Sensor Status",font=("Helvetica",12)).grid(row=4,column=0,columnspan=4)
		tk.Label(self,text="Sensor",font=("Helvetica",10)).grid(row=5,column=1)
		tk.Label(self,text="On/Off",font=("Helvetica",10)).grid(row=5,column=2)
		tk.Label(self,text="Notes",font=("Helvetica",12)).grid(row=2,column=5,columnspan=4)

		# Geometry initialization - Buttons
		self.zero_balance_button = tk.Button(self,text="Zero Balance",width=20,command=lambda: self.zero_balance())
		self.zero_balance_button.grid(row=14,column=5,columnspan=4)
		self.zero_balance_button.config(state=tk.NORMAL)
		self.edit_params_button = tk.Button(self,text="Edit Test Parameters",width=20,command=lambda: self.setup_test())
		self.edit_params_button.grid(row=15,column=5,columnspan=4)
		self.edit_params_button.config(state=tk.NORMAL)
		self.start_button = tk.Button(self,text="Start Test",width=20,command=lambda: self.data_page.start_test())
		self.start_button.grid(row=16,column=5,columnspan=4)
		self.start_button.config(state=tk.DISABLED)
		self.refresh_button = tk.Button(self,text="Refresh",width=20,command=lambda: self.refresh())
		self.refresh_button.grid(row=16,column=0,columnspan=4)
		self.refresh_button.config(state=tk.NORMAL)

		# Geometry initializiation - Text Boxes and Scrollbars (packed into Canvases)
		self.test_params_canv = tk.Canvas(self)
		self.test_params_canv.grid(row=3,column=0,columnspan=4)

		self.scroll_params = tk.Scrollbar(self.test_params_canv)
		self.scroll_params.pack(side=tk.RIGHT,fill=tk.Y)

		self.params_disp = tk.Text(self.test_params_canv)
		self.params_disp.pack()
		self.params_disp.config(state=tk.DISABLED,yscrollcommand=self.scroll_params.set)
		self.scroll_params.config(command=self.params_disp.yview)

		self.notes_canv = tk.Canvas(self)
		self.notes_canv.grid(row=3,column=5,columnspan=4)

		self.scroll_notes = tk.Scrollbar(self.notes_canv)
		self.scroll_notes.pack(side=tk.RIGHT,fill=tk.Y)

		self.notes_disp = tk.Text(self.notes_canv)
		self.notes_disp.pack()
		self.notes_disp.config(state=tk.NORMAL,yscrollcommand=self.scroll_notes.set)
		self.scroll_notes.config(command=self.notes_disp.yview)

		#green_circle_fn = os.path.join(os.path.dirname(__file__), 'Icons\\Circle_Green.png')
		#red_circle_fn = os.path.join(os.path.dirname(__file__), 'Icons\\Circle_Red.png')
		green_circle_fn = "Circle_Green.png"
		red_circle_fn = "Circle_Red.png"
		self.green_circle = ImageTk.PhotoImage(file=(r'%s'%green_circle_fn))
		self.red_circle = ImageTk.PhotoImage(file=(r'%s'%red_circle_fn))
		self.canv_list = []
		self.red_circles = []
		self.green_circles = []
		self.current_circles = []
		y = 0;
		for x in self.parameter_list:
			tk.Label(self,text=x,font=("Helvetica",8)).grid(row=6+y,column=1,columnspan=2,sticky=tk.W)
			canv = tk.Canvas(self)
			canv.grid(row=6+y,column=2)
			red_circle_label = tk.Label(canv,image=self.red_circle)
			green_circle_label = tk.Label(canv,image=self.green_circle)
			self.red_circles.append(red_circle_label)
			self.green_circles.append(green_circle_label)
			self.canv_list.append(canv)
			y = y + 1
		# Runs check sensors to initially refresh the Sensor Status Panel and Debug window
		self.refresh()

	# name: zero_balance
    # input:    nothing
    # output    nothing
    # desc:     Method called upon clicking the "Zero Balance" button to zero the balance
    # purpose:  First, this method checks to see if the balance is connected by running HardwareIO's check_sensors method. If the
    # 			balance is connected, it prompts the user to remove everything from the test area so that the balance can be zeroed.
    # 			When the user clicks "Ok" on the popup, hardwareIO's zero_balance method is called, which sends a command to the
    #			 balance to zero it. 
	def zero_balance(self):
		retry = True
		while(retry == True):
			self.refresh()
			# Checking if the balance is connected
			temp_array = self.hardwareIO.check_sensors(self.store)

			# If it's NOT connected, notify the user
			if(temp_array[5] == 0):
				self.zero_window = askretrycancel("Balance Not Connected", "Please make sure the balance is plugged in and powered on,\nthen select 'retry'.")
				retry = self.zero_window

			# If it IS connected, proceed with the zeroing prompt
			else:
				self.zero_window = askokcancel("Zero Balance", "Please remove the sample before selecting 'OK'.\nIf you don't want to zero the balance, press 'cancel'.")
				if (self.zero_window == True):
					self.hardwareIO.balance.zero_balance()
				retry = False;
				

	# name: 	setup_test
    # input:    nothing
    # output    nothing
    # desc:     Method called upon clicking the "Edit Test Parameters" button to open the Test Parameters window
    # purpose:  First, this method runs check_sensors to determine which sensors are connected. Next, it creates a new TestParamsWindow
    #
	def setup_test(self):
		try:
			self.params_window.deiconify()
		except:
			self.check_sensors()
			self.params_window = TestParamsWindow(self,self.store,self,self.start_button,self.sensors_valid,self.data_page.start_button)
			self.params_window.focus()
			self.params_window.mainloop()

	def setup_heatflux(self):
		try:
			self.heatflux_window.deiconify()
		except:
			self.heatflux_window = HeatfluxParamsWindow(self,self.store)
			self.heatflux_window.focus()
			self.heatflux_window.mainloop()

	# refresh is a member method of the HomePage class. It runs the check_sensor method which checks the status of any data input devices needed
	# for data aquisition then updates the HomePage's Sensor Status Panel accordingly. It then runs the DebugPage's refresh_debug() method, which 
	# refreshes the information in the Debug window
	def refresh(self):
		self.check_sensors()
		self.debug_page.refresh_debug()

	# check_sensors is a member method of the HomePage class. It runs the HardwareIO object's sensor_valid method, which returns an array indicating
	# which data input devices are currently connected to the computer. This is used to set HomePage's debug window to alert the user if there are 
	# data input devices that are not available and to gray out checkbuttons in the Test Parameter window to prevent the user from selecting data
	# input devices to measure that are not currently avaliable. check_sensor is run when the HomePage object is created in View and each time that a 
	# new TestParam object is created. It will also (future) run each time that the "Refresh" button on the HomePage is clicked.
	def check_sensors(self):
		# Once the sensor_valid method has been created for HardwareIO, it will be used here to get the sensor_valid array, which includes a 1 or 0 for
		# each data input device, indicating whether or not it is connected to the computer. 
		self.sensors_valid = self.hardwareIO.check_sensors(self.store)

		# This section determines which sensors are invalid and uses this information to update the HomePage's Sensor Status Panel. The config file 
		# keys for each of the data input devices are also set to 0 if a sensor is unavailable
		invalid_sensors = []
		# Surface Temperature
		if self.sensors_valid[2] == 0:
			#self.store.set_config(self.parameter_list[2],'0')
			invalid_sensors.append(self.parameter_list[2])
		# Ambient Temperature
		if self.sensors_valid[3] == 0:
			#self.store.set_config(self.parameter_list[3],'0')
			invalid_sensors.append(self.parameter_list[3])
		# Humidity
		if self.sensors_valid[4] == 0:
			#self.store.set_config(self.parameter_list[4],'0')
			invalid_sensors.append(self.parameter_list[4])
		# Mass
		if self.sensors_valid[5] == 0:
			#self.store.set_config(self.parameter_list[5],'0')
			invalid_sensors.append(self.parameter_list[5])
		# Voltage
		if self.sensors_valid[6] == 0:
			#self.store.set_config(self.parameter_list[6],'0')
			invalid_sensors.append(self.parameter_list[6])
		# Current
		if self.sensors_valid[7] == 0:
			#self.store.set_config(self.parameter_list[7],'0')
			invalid_sensors.append(self.parameter_list[7])
		# Plate Voltage
		if self.sensors_valid[8] == 0:
			#self.store.set_config(self.parameter_list[8],'0')
			invalid_sensors.append(self.parameter_list[8])
		# Top Temperature
		if self.sensors_valid[0] == 0:
			#self.store.set_config(self.parameter_list[0],'0')
			invalid_sensors.append(self.parameter_list[0])
		# Bottom Temperature
		if self.sensors_valid[1] == 0:
			#self.store.set_config(self.parameter_list[1],'0')
			invalid_sensors.append(self.parameter_list[1])
		# Geometry initialization - Sensor Status Panel
		y=0;
		for i in range(0,9):
			self.red_circles[i].pack_forget()
			self.green_circles[i].pack_forget()
		for x in self.parameter_list:
			if x in invalid_sensors:
				self.red_circles[y].pack()
			else:
				self.green_circles[y].pack()
			y = y+1
		del invalid_sensors

def disable_button(button):
	button.config(state=tk.DISABLED)

def enable_button(button):
	button.config(state=tk.NORMAL)