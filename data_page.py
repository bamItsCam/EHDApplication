import Tkinter as tk
import ttk
from home_page import HomePage
from storage import Storage
from hardwareIO import HardwareIO
from hardwareIO import HardwareIOException
from voltage_page import VoltagePage
from tkMessageBox import showerror
import time
import threading
from test import *

# TODO: keep column titles visible even when more rows exist than are visible
class DataPage(ttk.Frame):
	def __init__(self,parent,storage,hardwareIO,homepage,controller,voltage):
		ttk.Frame.__init__(self,parent)
		self.parent = parent
		self.config(padding=30)
		self.homepage = homepage
		self.hardwareIO = hardwareIO
		self.store = storage
		self.voltage = voltage
		# Geometry initialization
		tk.Grid.rowconfigure(self, 0, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 1, uniform=2,weight=5)
		tk.Grid.rowconfigure(self, 2, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 3, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 4, uniform=1,weight=1)
		tk.Grid.columnconfigure(self,0,uniform=1,weight=1)
		tk.Grid.columnconfigure(self,1,uniform=1,weight=1)
		tk.Grid.columnconfigure(self,2,uniform=1,weight=1)


		self.parameter_list = ["Top Temperature","Bottom Temperature","Surface Temperature","Ambient Temperature","Humidity","Mass","Voltage","Current","Plate Voltage","Heat Transfer"]
		self.parameter_list_2 = ["Top Temperature (C)","Bottom Temperature (C)","Surface Temperature (C)","Ambient Temperature (C)","Humidity (%)","Mass (g)","Voltage (V)","Current (uA)","Plate Voltage (V)","Heat Transfer"]
		self.parameter_list_3 = ["Time (s): ","Top Temperature (C): ","Bottom Temperature (C): ","Surface Temperature (C): ","Ambient Temperature (C): ","Humidity (%): ","Mass (g): ","Voltage (V): ","Current (A): ","Plate Voltage (V): ","Heat Transfer: "]

		# Geometry initialization - Labels
		tk.Label(self,text="Test Data",font=("Helvetica", 20)).grid(row=0,column=0,columnspan=3)

		# Geometry initialization - Buttons
		self.start_button = tk.Button(self,text="Start Test",width=20,command=lambda: self.start_test())
		self.start_button.grid(row=3,column=0)
		self.start_button.config(state=tk.DISABLED)
		self.cancel_button = tk.Button(self,text="Cancel Test",width=20,command=lambda: self.cancel_test())
		self.cancel_button.grid(row=3,column=1)
		self.cancel_button.config(state=tk.DISABLED)
		self.pause_button = tk.Button(self,text="Pause Test",width=20,command=lambda: self.pause_test())
		self.pause_button.grid(row=3,column=2)
		self.pause_button.config(state=tk.DISABLED)


		# Geometry initialization - Scrollable Textboxes
		self.canv = tk.Canvas(self)
		self.canv.grid(row=1,column=0,columnspan=3,sticky=tk.E+tk.W)

		self.scroll_data_x = tk.Scrollbar(self.canv,orient=tk.HORIZONTAL)
		self.scroll_data_x.pack(side=tk.BOTTOM,fill=tk.X)

		self.scroll_data = tk.Scrollbar(self.canv,orient=tk.VERTICAL)
		self.scroll_data.pack(side=tk.RIGHT,fill=tk.Y)

		self.data_disp = tk.Text(self.canv,wrap=tk.NONE)
		self.data_disp.pack(fill=tk.X)
		self.data_disp.config(state=tk.DISABLED,yscrollcommand=self.scroll_data.set,xscrollcommand=self.scroll_data_x.set)
		self.scroll_data_x.config(command=self.data_disp.xview)
		self.scroll_data.config(command=self.data_disp.yview)

		# Geometry initialization - Progressbar
		self.p1_var = tk.IntVar()
		self.p1 = ttk.Progressbar(self,variable=self.p1_var,length=1000)
		self.p1.grid(row=2,column=0,columnspan=3)

		# Geometry initialization - Data Measurement Counter Label
		self.counter_var = tk.StringVar()
		self.counter_var.set("0/0")
		self.counter_label = tk.Label(self,textvariable=self.counter_var)
		self.counter_label.grid(row=4,column=0,columnspan = 3)

		self.paused = False
	
	# star_test is a member mthod of the HomePage class. It determines which data input devices are to be used in the test, creates a new .csv file
	# with the correct time stamp and metadata row using the Storage object's test_init method, and (future) starts the sequence of data aquisition
	def pause_test(self):
		self.after(0,lambda:disable_button(self.pause_button))
		self.after(0,lambda:enable_button(self.start_button))
		self.after(0,lambda:enable_button(self.homepage.start_button))
		self.paused = True
		self.start_button.config(command=lambda:self.unpause_test())
		self.homepage.start_button.config(command=lambda:self.unpause_test())

	def unpause_test(self):
		self.after(0,lambda:enable_button(self.pause_button))
		self.start_button.config(command=lambda:self.start_test())
		self.homepage.start_button.config(command=lambda:self.start_test())
		self.after(0,lambda:disable_button(self.start_button))
		self.after(0,lambda:disable_button(self.homepage.start_button))
		self.parent.select(self)
		self.paused = False

	def start_test(self):
		self.p1_var.set(0)
		voltage_set = self.voltage.final_check()
		if voltage_set == True:
			self.data_disp.configure(state=tk.NORMAL)
			self.data_disp.delete("1.0", tk.END)
			self.data_disp.configure(state=tk.DISABLED)
			# Whoever's supposed to maintain this...I am so sorry for these lines
			self.parent._nametowidget(self.parent.winfo_parent()).openmenu.entryconfig("Configuration File",state="disabled")
			self.parent._nametowidget(self.parent.winfo_parent()).openmenu.entryconfig("Current Test", state="normal")
			self.parent._nametowidget(self.parent.winfo_parent()).editmenu.entryconfig("Test Parameters",state="disabled")
			self.parent._nametowidget(self.parent.winfo_parent()).editmenu.entryconfig("Zero Balance",state="disabled")
			self.parent._nametowidget(self.parent.winfo_parent()).editmenu.entryconfig("Restore Default Config",state="disabled")
			self.parent._nametowidget(self.parent.winfo_parent()).editmenu.entryconfig("Heatflux Parameters",state="disabled")

			# close any external windows
			try:
				self.homepage.params_window.destroy()
				self.homepage.heatflux_window.destroy()
			except:{}
			self.parent.select(self)
			self.after(0,lambda:disable_button(self.homepage.start_button))
			self.after(0,lambda:disable_button(self.homepage.edit_params_button))
			self.after(0,lambda:disable_button(self.homepage.zero_balance_button))
			self.after(0,lambda:disable_button(self.start_button))
			self.after(0,lambda:enable_button(self.cancel_button))
			self.after(0,lambda:enable_button(self.pause_button))
			self.after(0,lambda:disable_button(self.homepage.refresh_button))
			self.after(0,lambda:disable_button(self.homepage.debug_page.refresh_button))
			self.after(0,lambda:disable_button(self.voltage.add_new))
			self.after(0,lambda:disable_button(self.voltage.delete_button))
			self.after(0,lambda:disable_button(self.voltage.clear_button))
			self.voltage.local.configure(state=tk.DISABLED)
			self.voltage.remote.configure(state=tk.DISABLED)
			# Checking the status (1 or 0) of each of the data input devices, which is stored in the config file
			values = [int(self.store.get_config('Top Temperature')),int(self.store.get_config('Bottom Temperature')),int(self.store.get_config('Surface Temperature')),int(self.store.get_config('Ambient Temperature')),int(self.store.get_config('Humidity')),int(self.store.get_config('Mass')),int(self.store.get_config('Voltage')),int(self.store.get_config('Current')),int(self.store.get_config('Plate Voltage')),int(self.store.get_config('Heat Transfer'))]

			# Creating the items to be written to the first two rows of the new .csv file corresponding to the current test
			write_to_file_params = ["Time (s)"]
			i = 0
			for val in values:
				if val == 1:
					write_to_file_params.append(self.parameter_list_2[i])
				i = i+1
			# Sample Rate
			self.sample_rate = self.store.get_config('Sample Rate').rstrip()
			self.sample_unit = self.store.get_config('Sample Unit').rstrip()
			if self.sample_unit == 'second(s)':
				self.sample_rate = int(self.sample_rate)
			if self.sample_unit == 'minute(s)':
				self.sample_rate = int(self.sample_rate)
			if self.sample_unit == 'hour(s)':
				self.sample_rate = int(self.sample_rate)

			self.write_to_file_info = ["Test Name:", self.store.get_config("Test Name").rstrip(),"Test Duration (HH:MM):",self.store.get_config("Test Duration").rstrip(),"Sample Rate:",str(self.sample_rate) + ' ' + self.sample_unit]

			# Setting the length of the Progressbar
			duration = (self.store.get_config("Test Duration")).split(':')
			hr = int(duration[0])
			m = int(duration[1])
			self.total_m = m + hr*60
			self.total_s = self.total_m*60
			self.test_runs_total = self.total_s/self.sample_rate
			self.counter_var.set("0/%d"%self.test_runs_total)

			self.p1.config(maximum=self.test_runs_total+1)
			# Creating the .csv file and writing the first two lines to it
			if self.voltage.mode_var.get() == 2:
				self.new_voltage_item = Voltage(self,self.voltage.schedule,self.hardwareIO,self.total_s)
				self.new_voltage_item.state("withdrawn")
			else: 
				self.new_voltage_item = None
			self.store.test_init(write_to_file_params,self.write_to_file_info)
			self.test_runs = 0
			self.current_test = test(self,self.test_runs_total,self.sample_rate,self.new_voltage_item)
			self.current_test.state("withdrawn")
			self.current_test.mainloop()
			
	def cancel_test(self):
		self.paused = False
		self.current_test.destroy()
		self.data_disp.config(state=tk.NORMAL)
		self.data_disp.insert(tk.INSERT,"Test Cancelled\n")
		self.data_disp.config(state=tk.DISABLED)
		self.after(0,lambda:enable_button(self.homepage.edit_params_button))
		self.after(0,lambda:enable_button(self.homepage.start_button))
		self.after(0,lambda:enable_button(self.homepage.zero_balance_button))
		self.after(0,lambda:enable_button(self.start_button))
		self.after(0,lambda:disable_button(self.cancel_button))
		self.after(0,lambda:disable_button(self.pause_button))
		self.after(0,lambda:enable_button(self.homepage.refresh_button))
		self.after(0,lambda:enable_button(self.homepage.debug_page.refresh_button))
		self.after(0,lambda:enable_button(self.voltage.add_new))
		self.after(0,lambda:enable_button(self.voltage.delete_button))
		self.after(0,lambda:enable_button(self.voltage.clear_button))
		self.voltage.local.configure(state=tk.NORMAL)
		self.voltage.remote.configure(state=tk.NORMAL)
		self.start_button.config(command=lambda:self.start_test())
		self.homepage.start_button.config(command=lambda:self.start_test())
		if self.new_voltage_item != None:
			if(threading.active_count() == 1):
				end_voltage = 0.0
				t = threading.Thread(target=self.new_voltage_item.embedded_voltage_set, args=(end_voltage,))
				t.start()
			self.new_voltage_item.destroy()
		notes = ["User Notes:"]
		user_notes = self.homepage.notes_disp.get('0.0',tk.END)
		if user_notes != "":
			notes.append(user_notes)
			self.store.write_entry(notes)
			self.store.write_entry(self.write_to_file_info)
		self.store.log_event('debug','--- TEST CANCELLED ---')
		# Whoever's supposed to maintain this...I am so sorry for these lines
		self.parent._nametowidget(self.parent.winfo_parent()).openmenu.entryconfig("Configuration File",state="normal")
		self.parent._nametowidget(self.parent.winfo_parent()).openmenu.entryconfig("Current Test", state="disabled")
		self.parent._nametowidget(self.parent.winfo_parent()).editmenu.entryconfig("Test Parameters",state="normal")
		self.parent._nametowidget(self.parent.winfo_parent()).editmenu.entryconfig("Zero Balance",state="normal")
		self.parent._nametowidget(self.parent.winfo_parent()).editmenu.entryconfig("Restore Default Config",state="normal")
		self.parent._nametowidget(self.parent.winfo_parent()).editmenu.entryconfig("Heatflux Parameters",state="normal")
		self.homepage.debug_page.refresh()
		self.store.__init__()


class Voltage(tk.Toplevel):
	def __init__(self,datapage,schedule,hardwareIO,time_loop):
		tk.Toplevel.__init__(self)
		self.datapage = datapage
		self.hardwareIO = hardwareIO
		self.wait_time = 15000
		self.schedule = schedule
		self.schedule
		self.max_time = time_loop
		self.current_time = 0
		self.voltage_set()
	def voltage_set(self):
		if(self.datapage.paused != True):
			if self.current_time <= self.max_time:
				print self.current_time
				for dic in self.schedule:
					if dic['Time'] == self.current_time:
						print dic['Time']
						current_voltage = dic['Voltage']
						if(threading.active_count() == 1):
							t = threading.Thread(target=self.embedded_voltage_set, args=(current_voltage,))
							t.start()
				self.current_time = self.current_time + self.wait_time/1000
				self.after(self.wait_time,lambda:self.voltage_set())
			else:
				self.destroy()
		else:
			self.after(0,lambda:self.voltage_set())

	def embedded_voltage_set(self,current_voltage):
		try:
			self.hardwareIO.set_hfg_voltage_feedback(current_voltage)
		except HardwareIOException as e:
			self.datapage.store.log_event('debug',str(e))

class test(tk.Toplevel):
	def __init__(self,datapage,time_loop,wait_time,voltage=None):
		tk.Toplevel.__init__(self)
		params_array = []
		self.data_mask = [1]
		self.voltage = voltage
		if self.voltage != None:
			self.after(0,lambda:self.voltage.mainloop())
		params_array.append(datapage.parameter_list_3[0])
		j = 1
		for i in datapage.parameter_list:
			if(datapage.store.get_config(i).rstrip()=='1'):
				params_array.append(datapage.parameter_list_3[j])
				self.data_mask.append(1)
			else:
				self.data_mask.append(0)
			j=j+1
		disp_string = ""
		for i in params_array:
			disp_string = disp_string + i
			for x in range(0,25-len(i)):
				disp_string = disp_string + ' '
		disp_string = disp_string + '\n'
		datapage.data_disp.config(state=tk.NORMAL)
		datapage.data_disp.insert(tk.END,disp_string)
		datapage.data_disp.config(state=tk.DISABLED)
		self.data_collect(datapage,time_loop,wait_time)
	def data_collect(self,datapage,time_loop,wait_time):
		if(datapage.paused != True):
			datapage.homepage.debug_page.refresh()
			datapage.test_runs = datapage.test_runs + 1;
			datapage.p1_var.set(datapage.test_runs)
			data_array = datapage.hardwareIO.gather_data(datapage.store)
			config_array = []
			i = 0;
			for val in data_array:
				if((str(val) != 'invalid') and (self.data_mask[i]==1)):
					config_array.append(val)
				if((str(val) == 'invalid') and (self.data_mask[i]==1)):
					config_array.append('invalid')
				i = i+1
			disp_string = ""
			for i in config_array:
				disp_string = disp_string + str(i)
				for x in range(0,25-len(str(i))):
					disp_string = disp_string + ' '
			disp_string = disp_string + '\n'
			datapage.store.write_entry(config_array)
			datapage.data_disp.config(state=tk.NORMAL)
			datapage.data_disp.insert(tk.END,"%s" % disp_string)
			datapage.data_disp.see(tk.END)
			datapage.data_disp.yview()
			datapage.data_disp.config(state=tk.DISABLED)
			if(datapage.test_runs <= time_loop):
				datapage.counter_var.set("%d/%d"%(datapage.test_runs,datapage.test_runs_total))
				self.after(wait_time*1000,lambda:self.data_collect(datapage,time_loop,wait_time))
			else:
				if datapage.new_voltage_item != None:
					if(threading.active_count() == 1):
						end_voltage = 0.0
						t = threading.Thread(target=datapage.new_voltage_item.embedded_voltage_set, args=(end_voltage,))
						datapage.after(10,lambda:t.start())
					datapage.new_voltage_item.destroy()
				datapage.data_disp.config(state=tk.NORMAL)
				datapage.data_disp.insert(tk.END,"Test Completed\n")
				datapage.data_disp.see(tk.END)
				datapage.data_disp.yview()
				datapage.data_disp.config(state=tk.DISABLED)
				datapage.after(0,lambda:enable_button(datapage.homepage.edit_params_button))
				datapage.after(0,lambda:enable_button(datapage.homepage.start_button))
				datapage.after(0,lambda:enable_button(datapage.homepage.zero_balance_button))
				datapage.after(0,lambda:enable_button(datapage.start_button))
				datapage.after(0,lambda:disable_button(datapage.cancel_button))
				datapage.after(0,lambda:disable_button(datapage.pause_button))
				datapage.after(0,lambda:enable_button(datapage.homepage.refresh_button))
				datapage.after(0,lambda:enable_button(datapage.homepage.debug_page.refresh_button))
				datapage.after(0,lambda:enable_button(datapage.voltage.add_new))
				datapage.after(0,lambda:enable_button(datapage.voltage.delete_button))
				datapage.after(0,lambda:enable_button(datapage.voltage.clear_button))
				datapage.voltage.local.configure(state=tk.NORMAL)
				datapage.voltage.remote.configure(state=tk.NORMAL)
				notes = ["User Notes:"]
				user_notes = datapage.homepage.notes_disp.get('0.0',tk.END)
				if user_notes != "":
					notes.append(user_notes)
					datapage.store.write_entry(notes)
					datapage.store.write_entry(datapage.write_to_file_info)
				datapage.store.log_event('debug','--- TEST COMPLETED ---')
				# Whoever's supposed to maintain this...I am so sorry for these lines
				datapage._nametowidget(datapage.parent.winfo_parent()).openmenu.entryconfig("Configuration File",state="normal")
				datapage._nametowidget(datapage.parent.winfo_parent()).editmenu.entryconfig("Test Parameters",state="normal")
				datapage._nametowidget(datapage.parent.winfo_parent()).editmenu.entryconfig("Zero Balance",state="normal")
				datapage._nametowidget(datapage.parent.winfo_parent()).editmenu.entryconfig("Heatflux Parameters",state="normal")
				datapage.homepage.debug_page.refresh()
				datapage.store.__init__();
				self.after(0,lambda:self.destroy())
		else:
			self.after(0,lambda:self.data_collect(datapage,time_loop,wait_time))


def disable_button(button):
	button.config(state=tk.DISABLED)

def enable_button(button):
	button.config(state=tk.NORMAL)