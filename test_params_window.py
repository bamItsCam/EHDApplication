import re
from storage import Storage
from tkMessageBox import showerror
import Tkinter as tk
import ttk
from Tkconstants import *
# The TestParams class is inherited from the tk.Toplevel class. It is the container for the popup that is displayed when the "New Test" option
# is selected from File->New Test or when the "New Test" button is pressed on the homescreen

class TestParamsWindow(tk.Toplevel):
	#__init__ is the constructor of the new_test_params class. It creates and places all of the objects displayed on the "New Test Parameters" popup
	def __init__(self,parent,storage,homepage,start_button,sensors_valid,data_page_start):
		self.parent = parent
		self.homepage = homepage
		# Calling parent function constructor
		tk.Toplevel.__init__(self,parent)
		tk.Toplevel.title(self,"Test Parameters")
		tk.Toplevel.config(self,borderwidth=5)
		self.resizable(0,0)
		self.sensors_valid = sensors_valid
		self.fileIO = storage
		self.start = start_button
		self.data_start = data_page_start
		self.parameter_list = ["Surface Temperature (C)","Ambient Temperature (C)","Humidity (%)","Mass (g)", "Voltage (V)","Current (A)","Plate Voltage (V)", "Heat Transfer"]
		self.parameter_list_2 = ["Top Temperature","Bottom Temperature","Surface Temperature","Ambient Temperature","Humidity","Mass","Voltage","Current","Plate Voltage","Heat Transfer"]
		
		# General labels
		tk.Label(self,text="Test Values",font=12).grid(row=0,column=0)
		tk.Label(self,text="Test Duration",font=12).grid(row=0,column=2,columnspan=3)
		tk.Label(self,text="Test Name",font=12).grid(row=2,column=2,columnspan=3)
		tk.Label(self,text="Sample Rate",font=12).grid(row=4,column=2,columnspan=3)
		tk.Label(self,text="ex. 24:00").grid(row=1,column=5)
		tk.Label(self,text="ex. Test_1").grid(row=3,column=5)

		# Test parameter labels
		tk.Label(self,text=self.parameter_list[0]).grid(row=1,column=0,sticky=tk.W)
		tk.Label(self,text=self.parameter_list[1]).grid(row=2,column=0,sticky=tk.W)
		tk.Label(self,text=self.parameter_list[2]).grid(row=3,column=0,sticky=tk.W)
		tk.Label(self,text=self.parameter_list[3]).grid(row=4,column=0,sticky=tk.W)
		tk.Label(self,text=self.parameter_list[4]).grid(row=5,column=0,sticky=tk.W)
		tk.Label(self,text=self.parameter_list[5]).grid(row=6,column=0,sticky=tk.W)
		tk.Label(self,text=self.parameter_list[6]).grid(row=7,column=0,sticky=tk.W)
		tk.Label(self,text=self.parameter_list[7]).grid(row=8,column=0,sticky=tk.W)

		# Entry boxes
		self.e1_var = tk.StringVar()
		self.e2_var = tk.StringVar()
		self.e3_var = tk.StringVar()
		self.dd_var = tk.StringVar()

		# Initial test name
		self.test_name = self.fileIO.get_config("Test Name")
		self.e2_var.set(self.test_name)

		# Default test duration
		self.test_duration = self.fileIO.get_config('Test Duration')
		self.e1_var.set(self.test_duration)

		# Sample Rate
		self.sample_rate = self.fileIO.get_config('Sample Rate').rstrip()
		self.sample_unit = self.fileIO.get_config('Sample Unit').rstrip()
		if self.sample_unit == 'second(s)':
			self.sample_rate = self.sample_rate
		if self.sample_unit == 'minute(s)':
			self.sample_rate = int(self.sample_rate)/60
		if self.sample_unit == 'hour(s)':
			self.sample_rate = ((int(self.sample_rate)/60)/60)
		self.e3_var.set(self.sample_rate)

		# Sample Rate Units Dropdown
		dd = ttk.OptionMenu(self, self.dd_var,'     ','second(s)','minute(s)','hour(s)')
		dd.grid(row=5,column=5)

		self.dd_var.set(self.sample_unit)

		self.sensors_valid = self.homepage.hardwareIO.check_sensors(self.homepage.store)

		self.e1 = tk.Entry(self,width=30,textvariable=self.e1_var)
		self.e2 = tk.Entry(self,width=30,textvariable=self.e2_var)
		self.e3 = tk.Entry(self,width=30,textvariable=self.e3_var)
		self.e1.grid(row=1,column=2,columnspan=3)
		self.e2.grid(row=3,column=2,columnspan=3)
		self.e3.grid(row=5,column=2,columnspan=3)

		# Buttons
		self.b1 = tk.Button(self,text="Ok",width=10,command=lambda:self.set_test(self.homepage))
		self.b2 = tk.Button(self,text="Cancel",width=10,command=self.destroy)
		self.b1.grid(row=9,column=4)
		self.b2.grid(row=9,column=5)

		# Checkbuttons for test parameters
		self.c1_var = tk.IntVar()
		self.c2_var = tk.IntVar()
		self.c3_var = tk.IntVar()
		self.c4_var = tk.IntVar()
		self.c5_var = tk.IntVar()
		self.c6_var = tk.IntVar()
		self.c7_var = tk.IntVar()
		self.c8_var = tk.IntVar()
		self.c9_var = tk.IntVar()

		# Initializing all checkbuttons
		# Surface Temperature
		c1 = tk.Checkbutton(self,variable=self.c1_var)
		if self.sensors_valid[2] == 1:
			self.c1_var.set(int(self.fileIO.get_config(self.parameter_list_2[2])))
		else:
			self.c1_var.set(0)
			c1.config(state=tk.DISABLED)
		# Ambient Temperature
		c2 = tk.Checkbutton(self,variable=self.c2_var)
		if self.sensors_valid[3] == 1:
			self.c2_var.set(int(self.fileIO.get_config(self.parameter_list_2[3])))
		else:
			self.c2_var.set(0)
			c2.config(state=tk.DISABLED)
		# Humidity
		c3 = tk.Checkbutton(self,variable=self.c3_var)
		if self.sensors_valid[4] == 1:
			self.c3_var.set(int(self.fileIO.get_config(self.parameter_list_2[4])))
		else:
			self.c3_var.set(0)
			c3.config(state=tk.DISABLED)
		# Mass
		c4 = tk.Checkbutton(self,variable=self.c4_var)
		if self.sensors_valid[5] == 1:
			self.c4_var.set(int(self.fileIO.get_config(self.parameter_list_2[5])))
		else:
			self.c4_var.set(0)
			c4.config(state=tk.DISABLED)
		# Voltage
		c5 = tk.Checkbutton(self,variable=self.c5_var)
		if self.sensors_valid[6] == 1:
			self.c5_var.set(int(self.fileIO.get_config(self.parameter_list_2[6])))
		else:
			self.c5_var.set(0)
			c5.config(state=tk.DISABLED)
		# Current
		c6 = tk.Checkbutton(self,variable=self.c6_var)
		if self.sensors_valid[7] == 1:
			self.c6_var.set(int(self.fileIO.get_config(self.parameter_list_2[7])))
		else:
			self.c6_var.set(0)
			c6.config(state=tk.DISABLED)
		# Plate Voltage
		c7 = tk.Checkbutton(self,variable=self.c7_var)
		if self.sensors_valid[8] == 1:
			self.c7_var.set(int(self.fileIO.get_config(self.parameter_list_2[8])))
		else:
			self.c7_var.set(0)
			c7.config(state=tk.DISABLED)
		# Heat Transfer
		c8 = tk.Checkbutton(self,variable=self.c8_var)
		if self.sensors_valid[0] == 1 and self.sensors_valid[1] == 1 and self.sensors_valid[2] == 1 and self.sensors_valid[3] == 1 and self.sensors_valid[8] == 1:
			self.c8_var.set(int(self.fileIO.get_config(self.parameter_list_2[9])))
		else:
			self.c8_var.set(0)
			c8.config(state=tk.DISABLED)

		c1.grid(row=1,column=1)
		c2.grid(row=2,column=1)
		c3.grid(row=3,column=1)
		c4.grid(row=4,column=1)
		c5.grid(row=5,column=1)
		c6.grid(row=6,column=1)
		c7.grid(row=7,column=1)
		c8.grid(row=8,column=1)

		self.bind("<Return>",self.click)

	def click(self,event):
		self.b1.invoke()
		
	# set_test is a member function of the TestParams (yes, I did indeed fix the naming convention, be proud of me) class. It will read in the user-entered values, check them for correct format, and 
	# prompt the initialization of a test
	def set_test(self,homepage):
		# after test params have been saved, enable voltage scheduler
		# also, I apologize for this atrocity:
		if self.sensors_valid[8] == 1:
			self.parent._nametowidget(self.parent.winfo_parent())._nametowidget(self.parent.parent.winfo_parent()).viewmenu.entryconfig("Voltage Scheduler",state="normal")
			self.parent._nametowidget(self.parent.winfo_parent())._nametowidget(self.parent.parent.winfo_parent()).container.tab(3,state='normal')
		else:
			self.parent._nametowidget(self.parent.winfo_parent())._nametowidget(self.parent.parent.winfo_parent()).viewmenu.entryconfig("Voltage Scheduler",state="disabled")
			self.parent._nametowidget(self.parent.winfo_parent())._nametowidget(self.parent.parent.winfo_parent()).container.tab(3,state='disabled')
		self.current_test_dur = self.e1_var.get().rstrip()
		self.current_test_name = self.e2_var.get()
		self.current_test_samp = self.e3_var.get()
		self.current_test_un = self.dd_var.get()
		time_pattern = '([01]?[0-9]|2[0-3]):[0-5][0-9]'
		samp_pattern = '[0-9]?'
		p = re.compile(time_pattern)
		p2 = re.compile(samp_pattern)
		valid_dur = False 
		valid_samp = False
		if not valid_dur:
			if (p.match(self.current_test_dur) or self.current_test_dur == "24:00") and (self.current_test_dur != '0:00' and self.current_test_dur != '0'):
				valid_dur = True
			else:
				self.withdraw()
				showerror("ERROR","Please enter a valid test duration\nEx. 24:00")
				self.e1.config(bg="#FFDBDB")
				self.deiconify()
				self.lift()
		if valid_dur:
			duration = (self.current_test_dur).split(':')
			hr = int(duration[0])
			m = int(duration[1])
			self.total_m = m + hr*60
			self.total_s = self.total_m*60
			if not valid_samp:
				if (p2.match(self.current_test_samp)):
					try:
						if self.current_test_un == 'second(s)':
							self.current_s = int(self.current_test_samp)
						if self.current_test_un == 'minute(s)':
							self.current_s = int(self.current_test_samp)*60
						if self.current_test_un == 'hour(s)':
							self.current_s = int(self.current_test_samp)*60*60
						valid_samp = True
					except:
						valid_samp = False
						self.withdraw()
						showerror("ERROR","Please enter a valid integer sample rate\nEx: 30 second(s)")
						self.e3.config(bg="#FFDBDB")
						self.deiconify()
						self.lift()	
				else:
					valid_samp = False
					self.withdraw()
					showerror("ERROR","Please enter a valid sample rate\nEx: 30 second(s)")
					self.e3.config(bg="#FFDBDB")
					self.deiconify()
					self.lift()	
				if valid_samp:
					if(self.current_s <= self.total_s):
						valid_samp = True
					else:
						valid_samp = False
						self.withdraw()
						showerror("ERROR","The sample rate exceeds the total test duration")
						self.e3.config(bg="#FFDBDB")
						self.deiconify()
						self.lift()		
			if valid_samp:			
				values = [self.c1_var.get(),self.c2_var.get(),self.c3_var.get(),self.c4_var.get(),self.c5_var.get(),self.c6_var.get(),self.c7_var.get(),self.c8_var.get()]
				self.values_arr = []
				i = 0
				for var in values:
					if i < 7:
						if var == 1:
							self.fileIO.set_config(self.parameter_list_2[i+2],'1')
							self.values_arr.append(self.parameter_list[i])
						else:
							self.fileIO.set_config(self.parameter_list_2[i+2],'0')
					else:
						if var == 1:
							# If the user desires to read heat transfer, surface temperature, ambient temperature, top temperature, and bottom temperature
							# must be read
							self.fileIO.set_config(self.parameter_list_2[0],'1')
							self.fileIO.set_config(self.parameter_list_2[1],'1')
							self.fileIO.set_config(self.parameter_list_2[2],'1')
							self.fileIO.set_config(self.parameter_list_2[9],'1')
							self.fileIO.set_config(self.parameter_list_2[3],'1')
							self.fileIO.set_config(self.parameter_list_2[6],'1')
							self.values_arr.append(self.parameter_list[i])
						else:
							self.fileIO.set_config(self.parameter_list_2[0],'0')
							self.fileIO.set_config(self.parameter_list_2[1],'0')
							self.fileIO.set_config(self.parameter_list_2[9],'0')
					i = i + 1

				self.test_info = [(self.current_test_name).rstrip(),self.current_test_dur.rstrip(),str(self.current_s)]
				self.fileIO.set_config('Test Name',self.test_info[0])
				self.fileIO.set_config('Test Duration',self.test_info[1])
				self.fileIO.set_config('Sample Rate',self.test_info[2])
				self.fileIO.set_config('Sample Unit',self.current_test_un)

				params_info = "--- Test Information ---\nTest Name: %s\nTest Duration: %s\nSample Rate: %s %s\n\n" %(self.test_info[0],self.current_test_dur,self.current_test_samp,self.current_test_un)
				params_vals = "--- Parameters ---\nTime (s)\n"
				for i in self.values_arr:
					params_vals = params_vals + i + '\n'
				params = params_info + params_vals
				self.homepage.params_disp.config(state=tk.NORMAL)
				self.homepage.params_disp.delete('1.0',tk.END)
				self.homepage.params_disp.insert(tk.INSERT,params)
				self.homepage.params_disp.config(state=tk.DISABLED)

				self.start.config(state=tk.NORMAL)
				self.data_start.config(state=tk.NORMAL)
				self.destroy()
