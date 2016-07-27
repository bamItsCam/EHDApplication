import Tkinter as tk
from tkMessageBox import showerror
import Tkconstants, tkFileDialog
import ttk
from home_page import HomePage
from storage import Storage
from hardwareIO import HardwareIO, HardwareIOException
import time
from test import *
import os
import re

class VoltagePage(ttk.Frame):
	def __init__(self,parent,storage,controller,home_page=None):
		ttk.Frame.__init__(self,parent)
		self.parent = parent
		self.config(padding=30)
		self.storage = storage
		self.homepage = home_page
		self.current_start = "00:00"
		self.current_voltage = 0
		self.list_of_entries = []
		# Geometry initialization
		tk.Grid.rowconfigure(self, 0, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 1, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 2, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 3, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 4, uniform=1, weight=1)
		tk.Grid.rowconfigure(self, 5, uniform=2, weight=8)
		tk.Grid.rowconfigure(self, 6, uniform=1, weight=1)
		tk.Grid.columnconfigure(self,0,uniform=1,weight=1)
		tk.Grid.columnconfigure(self,1,uniform=1,weight=1)
		tk.Grid.columnconfigure(self,2,uniform=1,weight=1)
		tk.Grid.columnconfigure(self,3,uniform=1,weight=1)
		tk.Grid.columnconfigure(self,4,uniform=1,weight=1)
		tk.Grid.columnconfigure(self,5,uniform=1,weight=1)
		tk.Grid.columnconfigure(self,6,uniform=1,weight=1)

		# Geometry initialization - Labels
		tk.Label(self,text="Voltage Scheduler",font=("Helvetica", 20)).grid(row=0,column=0,columnspan=7)
		tk.Label(self,text="Mode",font=("Helvetica",12)).grid(row=1,column=0,columnspan=7)
		tk.Label(self,text="Voltage Schedule",font=("Helvetica",12)).grid(row=3,column=0,columnspan=7)
		tk.Label(self,text="Type",font=("Helvetica",10)).grid(row=4,column=0,sticky=tk.W)
		tk.Label(self,text="Start Time",font=("Helvetica",10)).grid(row=4,column=1,sticky=tk.W)
		tk.Label(self,text="Stop Time",font=("Helvetica",10)).grid(row=4,column=2,sticky=tk.W)
		tk.Label(self,text="Peak Time",font=("Helvetica",10)).grid(row=4,column=3,sticky=tk.W)
		tk.Label(self,text="Low Voltage",font=("Helvetica",10)).grid(row=4,column=4,sticky=tk.W)
		tk.Label(self,text="High Voltage",font=("Helvetica",10)).grid(row=4,column=5,sticky=tk.W)
		tk.Label(self,text="Direction",font=("Helvetica",10)).grid(row=4,column=6,sticky=tk.W)

		# Geometry initialization - Buttons
		self.add_new = tk.Button(self,text="Add New Item",width=20,command=lambda:self.add_item())
		self.add_new.grid(row=6,column=1)
		self.add_new.config(state=tk.DISABLED)
		self.delete_button = tk.Button(self,text="Delete Selected",width=20,command=lambda:self.remove_selected())
		self.delete_button.config(state=tk.DISABLED)
		self.delete_button.grid(row=6,column=3)
		self.clear_button = tk.Button(self,text="Clear Schedule",width=20,command=lambda:self.remove_all())
		self.clear_button.grid(row=6,column=5)
		self.clear_button.config(state=tk.DISABLED)


		# Geometry initialization - Scrollable Frame
		self.schedulelist = ScheduleList(self)
		self.schedulelist.grid(row=5,column=0,columnspan=7,sticky=tk.E+tk.W+tk.N+tk.S)

		self.scroll_frame_x = tk.Scrollbar(self.schedulelist,orient=tk.HORIZONTAL)
		self.scroll_frame_x.pack(side=tk.BOTTOM,fill=tk.X)

		self.scroll_frame = tk.Scrollbar(self.schedulelist)
		self.scroll_frame.pack(side=tk.RIGHT,fill=tk.Y)

		self.scroll_frame_x.config(command=self.schedulelist.xview)
		self.scroll_frame.config(command=self.schedulelist.yview)

		self.schedulelist.config(yscrollcommand=self.scroll_frame.set,xscrollcommand=self.scroll_frame_x.set)
		
		# Geometry initialization - Radiobuttons for mode
		self.mode_var = tk.IntVar()
		self.mode_var.set(1)

		self.local = tk.Radiobutton(self,text="Local",variable=self.mode_var,value=1,command=self.get_mode)
		self.remote = tk.Radiobutton(self,text="Remote",variable=self.mode_var,value=2,command=self.get_mode)
		self.local.grid(row=2,column=2)
		self.remote.grid(row=2,column=4)


	def get_mode(self):
		self.mode = self.mode_var.get()
		if self.mode == 1:
			showerror("WARNING","Please make sure that the High Voltage Field Generator is set to Local Mode, then press OK")
			disable_button(self.add_new)
			disable_button(self.delete_button)
			disable_button(self.clear_button)
		if self.mode == 2:
			showerror("WARNING","Please make sure that the High Voltage Field Generator is set to Remote Mode, then press OK")
			enable_button(self.add_new)
			enable_button(self.delete_button)
			enable_button(self.clear_button)

	def add_item(self):
		try:
			self.item_page.deiconify()
		except:
			self.item_page = AddItemPage(self)
			self.item_page.focus()
			self.item_page.mainloop()

		
	def remove_selected(self):
		items = self.schedulelist.curselection()
		pos = 0
		for i in items :
			idx = int(i) - pos
			self.schedulelist.delete( idx,idx )
			pos = pos + 1
			self.list_of_entries.pop(idx)


	def remove_all(self):
		self.schedulelist.select_set(0,tk.END)
		self.remove_selected()

	def final_check(self):
		#This function will be called when the start button is pressed 
		#This is where a final range check will happen (in case the user changed the test duration but didn't change the schedule)
		#if the range check is passed, the calc_schedule() function will be run

		duration_sec = int((self.storage.get_config('Test Duration').split(':'))[0])*60*60+int((self.storage.get_config('Test Duration').split(':'))[1])*60
		last_index = len(self.list_of_entries)-1
		if (last_index >= 0) and (self.mode_var.get()==2):
			if((self.list_of_entries[last_index]).stop_sec > duration_sec):
				showerror("WARNING","The voltage schedule specified has a time range (%s-%s) that exceeds the specified test duration (%s).\nPlease adjust the test duration or the voltage schedule time range." % ((self.list_of_entries[last_index]).t_start,(self.list_of_entries[last_index]).t_stop,self.storage.get_config('Test Duration').rstrip()))
				return False
			else:
				self.calc_schedule()
				return True
		elif (last_index < 0) and (self.mode_var.get()==2):
			showerror("WARNING","You have turned on Remote Voltage Control but have not specified a voltage schedule.\nPlease either change the mode to Local Voltage Control on the Voltage tab or add a schedule")
			return False
		else:
			return True

	def calc_schedule(self):
		#This function will be called after the final range check is passed after the start button is pressed
		#It will go through the schedule list and do the following:
		#(1) Loop through the elements in the schedule list. For each type:
		#	RAMP (up): start_voltage = v_low. stop_voltage = v_high. delta_voltage = (v_high-v_low)/((stop_sec-start_sec)*2)
		#	RAMP (down): start_voltage = v_high. stop_voltage = v_low. delta_voltage = -((v_high-v_low)/((stop_sec-start_sec)*2))
		#	STEP (up): start_voltage = v_low. step_voltage = v_high.
		#	STEP (down): start_voltage = v_high. step_voltage = v_low. 
		#	TRIANGLE: start_voltage = v_low. delta_voltage_up = (v_high-v_low)/((mid_sec-start_sec)*2). delta_voltage_down = -((v_high-v_low)/((stop_sec-mid_sec)*2))
		#	CONST: start_voltage = v_high.
		#(2) For each item, create a 2D array that matches delta voltages with times (increment of 30 seconds).
		#(3) Compile these arrays at the end
		item_dict = {'Time':0,'Voltage':0}
		self.schedule = []
		current_step_index = 0
		current_low_index = 0
		total_steps = 0
		for item in self.list_of_entries:
			voltage_sample_rate = 15
			total_steps = total_steps + (item.stop_sec-item.start_sec)/voltage_sample_rate
			#print total_steps
			current_time = item.start_sec
			if(item.item_type == 'RAMP' and item.up_down == 'up'):
				current_voltage = float(item.v_low)*1000
				delta_voltage = (float(item.v_high)*1000-float(item.v_low)*1000)/((total_steps))
			elif(item.item_type == 'RAMP' and item.up_down == 'down'):
				current_voltage = float(item.v_high)*1000
				delta_voltage = -(float(item.v_high)*1000-float(item.v_low)*1000)/((total_steps))
			elif(item.item_type == 'STEP' and item.up_down == 'up'):
				current_voltage = float(item.v_low)*1000
				step_voltage = float(item.v_high)*1000
			elif(item.item_type == 'STEP' and item.up_down == 'down'):
				current_voltage = float(item.v_high)*1000
				step_voltage = float(item.v_low)*1000
			elif(item.item_type == 'TRIANGLE'):
				current_voltage = float(item.v_low)*1000
				delta_voltage = [(float(item.v_high)*1000-float(item.v_low)*1000)/((item.mid_sec-item.start_sec)/voltage_sample_rate),-(float(item.v_high)*1000-float(item.v_low)*1000)/((item.stop_sec-item.mid_sec)/voltage_sample_rate)]
			elif(item.item_type == 'CONST'):
				current_voltage = float(item.v_high)*1000
			else:
				step_voltage = [float(item.v_high)*1000,float(item.v_low)*1000]
				current_voltage = step_voltage[1]

			for i in range(current_low_index,total_steps+1):
				voltage_change = False
				item_dict = {'Time':0,'Voltage':0}
				if(item.item_type =='RAMP'):
					if(i > current_low_index):
						current_voltage = current_voltage + delta_voltage
					voltage_change = True
				if(item.item_type == 'STEP'):
					if(i == current_low_index):
						voltage_change = True
					if(i == current_low_index + (total_steps-current_low_index)/2):
						current_voltage = step_voltage
						voltage_change = True
					else:
						voltage_change = False
				if(item.item_type == 'TRIANGLE'):
					if(i <= item.mid_sec/voltage_sample_rate):
						if i > current_low_index:
							current_voltage = current_voltage + delta_voltage[0]
					else:
						if i > current_low_index:
							current_voltage = current_voltage + delta_voltage[1]
					voltage_change = True
				if(item.item_type == 'CONST'):
					if i == current_low_index:
						voltage_change = True
					elif i == total_steps:
						current_voltage = 0
						voltage_change = True
					else:
						voltage_change = False
				if(item.item_type == 'SQUARE'):
					if(i == current_low_index):
						current_voltage = step_voltage[1]
						voltage_change = True
					elif(i == current_low_index + (total_steps-current_low_index)/4):
						current_voltage = step_voltage[0]
						voltage_change = True
					elif(i == current_low_index + ((total_steps-current_low_index)-((total_steps-current_low_index)/4))):
						current_voltage = step_voltage[1]
						voltage_change = True
					else:
						voltage_change = False
				if(voltage_change == True):
					item_dict['Time'] = current_time
					item_dict['Voltage'] = current_voltage
					print str(item_dict['Time']) + ' ' + str(item_dict['Voltage'])
					self.schedule.append(item_dict)
				current_time = item.start_sec+voltage_sample_rate*(i-current_low_index)
				current_step_index = current_step_index + 1
			current_low_index = current_low_index + current_step_index
			current_step_index = 0

					

def disable_button(button):
	button.config(state=tk.DISABLED)

def enable_button(button):
	button.config(state=tk.NORMAL)

class ScheduleList(tk.Listbox):
	def __init__(self,parent):
		tk.Listbox.__init__(self,parent,bg='white',selectmode=tk.MULTIPLE)
		self.current_row = 0

class AddItemPage(tk.Toplevel):
	def __init__(self,parent):
		tk.Toplevel.__init__(self,parent)
		tk.Toplevel.title(self,"Add Voltage Item")
		tk.Toplevel.config(self,borderwidth=5)
		self.resizable(0,0)
		self.parent = parent
		self.parent.test_duration = self.parent.storage.get_config("Test Duration")
		self.parent.duration = (self.parent.test_duration).split(':')
		self.parent.hr = int(self.parent.duration[0])
		self.parent.m = int(self.parent.duration[1])
		self.parent.s = self.parent.m*60
		tk.Grid.rowconfigure(self, 0, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 1, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 2, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 3, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 4, uniform=1, weight=1)
		tk.Grid.rowconfigure(self, 5, uniform=1, weight=1)
		tk.Grid.rowconfigure(self, 6, uniform=1, weight=1)
		tk.Grid.rowconfigure(self, 7, uniform=1, weight=1)
		tk.Grid.columnconfigure(self,0,uniform=1,weight=1)
		tk.Grid.columnconfigure(self,1,uniform=1,weight=1)
		tk.Grid.columnconfigure(self,2,uniform=1,weight=1)
		tk.Grid.columnconfigure(self,3,uniform=1,weight=1)
		tk.Grid.columnconfigure(self,4,uniform=1,weight=1)
		tk.Grid.columnconfigure(self,5,uniform=1,weight=1)
		# Geometry Initialization - Labels:
		tk.Label(self,text="Item Type",font=("Helvetica",12)).grid(row=0,column=0,sticky=tk.W)
		tk.Label(self,text="Direction",font=("Helvetica",12)).grid(row=1,column=0,sticky=tk.W)
		tk.Label(self,text="Start Time",font=("Helvetica",12)).grid(row=2,column=0,sticky=tk.W)
		tk.Label(self,text="End Time",font=("Helvetica",12)).grid(row=3,column=0,sticky=tk.W)
		tk.Label(self,text="Peak Time",font=("Helvetica",12)).grid(row=4,column=0,sticky=tk.W)
		tk.Label(self,text="Low Voltage",font=("Helvetica",12)).grid(row=5,column=0,sticky=tk.W)
		tk.Label(self,text="High Voltage",font=("Helvetica",12)).grid(row=6,column=0,sticky=tk.W)

		tk.Label(self,text="HH:MM",font=("Helvetica",10)).grid(row=2,column=2,sticky=tk.W)
		tk.Label(self,text="HH:MM",font=("Helvetica",10)).grid(row=3,column=2,sticky=tk.W)
		tk.Label(self,text="HH:MM",font=("Helvetica",10)).grid(row=4,column=2,sticky=tk.W)
		tk.Label(self,text="kV",font=("Helvetica",10)).grid(row=5,column=2,sticky=tk.W)
		tk.Label(self,text="kV",font=("Helvetica",10)).grid(row=6,column=2,sticky=tk.W)
		# Geometry Initialization - Radiobuttons:
		self.radio_var = tk.IntVar()
		self.radio_var.set(1)
		self.radio_var_2 = tk.IntVar()
		self.radio_var_2.set(1)
		self.ramp_radio = tk.Radiobutton(self,text="RAMP",variable=self.radio_var,value=1,command=lambda:self.update_entries("RAMP"))
		self.triangle_radio = tk.Radiobutton(self,text="TRIANGLE",variable=self.radio_var,value=2,command=lambda:self.update_entries("TRI"))
		self.square_radio = tk.Radiobutton(self,text="SQUARE",variable=self.radio_var,value=3,command=lambda:self.update_entries("SQUARE"))
		self.step_radio = tk.Radiobutton(self,text="STEP",variable=self.radio_var,value=4,command=lambda:self.update_entries("STEP"))
		self.const_radio = tk.Radiobutton(self,text="CONST",variable=self.radio_var,value=5,command=lambda:self.update_entries("CONST"))

		self.up_radio = tk.Radiobutton(self,text="Up",variable=self.radio_var_2,value=1)
		self.down_radio = tk.Radiobutton(self,text="Down",variable=self.radio_var_2,value=2)
		self.ramp_radio.grid(row=0,column=1)
		self.triangle_radio.grid(row=0,column=2)
		self.square_radio.grid(row=0,column=3)
		self.step_radio.grid(row=0,column=4)
		self.const_radio.grid(row=0,column=5)
		self.up_radio.grid(row=1,column=1)
		self.down_radio.grid(row=1,column=2)
		# Geometry Initialization - Entry Boxes
		self.t_start_var = tk.StringVar()
		self.t_stop_var = tk.StringVar()
		self.t_peak_var = tk.StringVar()
		self.v_low_var = tk.StringVar()
		self.v_high_var = tk.StringVar()

		#self.t_start_var.set(parent.current_start)

		self.t_start_entry = tk.Entry(self,width=15,textvariable=self.t_start_var)
		self.t_stop_entry = tk.Entry(self,width=15,textvariable=self.t_stop_var)
		self.t_peak_entry = tk.Entry(self,width=15,textvariable=self.t_peak_var)
		self.v_low_entry = tk.Entry(self,width=15,textvariable=self.v_low_var)
		self.v_high_entry = tk.Entry(self,width=15,textvariable=self.v_high_var)

		self.t_start_entry.grid(row=2,column=1)
		self.t_stop_entry.grid(row=3,column=1)
		self.t_peak_entry.grid(row=4,column=1)
		self.t_peak_entry.config(state=tk.DISABLED)
		self.v_low_entry.grid(row=5,column=1)
		self.v_high_entry.grid(row=6,column=1)

		self.t_peak_entry.config(state=tk.DISABLED)
		# Geometry Initialization - Buttons
		self.add_button = tk.Button(self,text="Add",width=10,command=lambda:self.add())
		self.cancel = tk.Button(self,text="Cancel",width=10,command=self.destroy)
		self.add_button.grid(row=6,column=4)
		self.cancel.grid(row=6,column=5)

		self.bind("<Return>",self.click)

	def click(self,event):
		# input:    an event (ya know, like clicking)
		# output:  	nothing!
		# desc:  	for use when binding the enter key to the add button
		# notes: 
		self.add_button.invoke()

	def check_entry(self,entry=None):
		#time box check:
		time_pattern = '([01]?[0-9]|2[0-3]):[0-5][0-9]'
		p = re.compile(time_pattern)
		valid_dur = False 
		if not valid_dur:
			if (p.match(entry.t_start) or entry.t_start == "24:00") and (entry.t_start != '0:00' and entry.t_start != '0'):
				if (p.match(entry.t_stop) or entry.t_stop == "24:00") and (entry.t_stop != '0:00' and entry.t_stop != '0'):
					if entry.t_mid == 'N/A':
						valid_dur = True 
					elif (p.match(entry.t_mid) or entry.t_mid == "24:00") and (entry.t_mid != '0:00' and entry.t_mid != '0'):
						valid_dur = True
			if not valid_dur:
				self.withdraw()
				showerror("ERROR","The format of the start, mid or stop time is incorrect\nEx. 24:00")
				self.t_start_entry.config(bg="#FFDBDB")
				self.t_stop_entry.config(bg="#FFDBDB")
				if self.t_peak_entry.cget('state') != 'disabled':
					self.t_peak_entry.config(bg="#FFDBDB")
				self.deiconify()
				self.lift()
		if valid_dur:
			try:
				entry.calc_seconds()
				return True
			except:
				self.withdraw()
				showerror("ERROR","The format of the start, mid or stop time is incorrect\nEx. 24:00")
				self.t_start_entry.config(bg="#FFDBDB")
				self.t_stop_entry.config(bg="#FFDBDB")
				if self.t_peak_entry.cget('state') != 'disabled':
					self.t_peak_entry.config(bg="#FFDBDB")
				self.deiconify()
				self.lift()				
		else:
			return False

	def range_check(self,entry=None):
		outside_range = True
		for item in self.parent.list_of_entries:
			if (entry.start_sec>item.start_sec) and (entry.start_sec<item.stop_sec):
				outside_range = False
		for item in self.parent.list_of_entries:
			if (entry.stop_sec>item.start_sec) and (entry.stop_sec<item.stop_sec):
				outside_range = False
		for item in self.parent.list_of_entries:
			if (item.start_sec == entry.start_sec) and (entry.stop_sec == item.stop_sec):
				outside_range = False
		if outside_range:
			duration_sec = int((self.parent.storage.get_config('Test Duration').split(':'))[0])*60*60+int((self.parent.storage.get_config('Test Duration').split(':'))[1])*60
			if (entry.stop_sec > duration_sec) or (entry.start_sec > duration_sec):
				outside_range = False
			if outside_range:
				if (entry.t_mid != "N/A"):
					if not ((entry.mid_sec > entry.start_sec) and (entry.mid_sec < entry.stop_sec)):
						outside_range = False
					if outside_range:
						return outside_range
					else:
						self.withdraw()
						showerror("ERROR","The peak time of this item falls outside the item range (%s-%s).\nPlease adjust the peak time to fall within the range." % (entry.t_start,entry.t_stop))
						self.t_peak_entry.config(bg="#FFDBDB")
						self.deiconify()
						self.lift()
						return outside_range
				else:
					return outside_range	
			else:
				self.withdraw()
				showerror("ERROR","One of the entered times of this entry are beyond the selected test duration (%s). Please adjust the item times accordingly." % (self.parent.storage.get_config('Test Duration').rstrip()))
				self.t_start_entry.config(bg="#FFDBDB")
				self.t_stop_entry.config(bg="#FFDBDB")
				if self.t_peak_entry.cget('state') != 'disabled':
					self.t_peak_entry.config(bg="#FFDBDB")
				self.deiconify()
				self.lift()
				return outside_range	
		else:
			self.withdraw()
			showerror("ERROR","The time range of this item (%s-%s) conflicts with a previously-entered item.\nPlease adjust the times or delete the conflicting item." % (entry.t_start,entry.t_stop))
			self.t_start_entry.config(bg="#FFDBDB")
			self.t_stop_entry.config(bg="#FFDBDB")
			if self.t_peak_entry.cget('state') != 'disabled':
				self.t_peak_entry.config(bg="#FFDBDB")
			self.deiconify()
			self.lift()
			return outside_range
	def voltage_check(self,entry=None):
		in_range = True
		try:
			if self.v_low_entry.cget('state') != 'disabled':
				if not((float(entry.v_low) >= 0) and (float(entry.v_low) <= 30)):
					in_range = False
				if not((float(entry.v_high) >= 0) and (float(entry.v_high) <= 30)):
					in_range = False
				if not(float(entry.v_low) < float(entry.v_high)):
					in_range = False
				if not in_range:
					self.withdraw()
					showerror("ERROR","One of the entered voltages is out of range (0kV-30kV) or the low voltage (%s) is greater than the high voltage (%s).\nPlease adjust the voltages." % (entry.v_low,entry.v_high))
					self.v_low_entry.config(bg="#FFDBDB")
					self.v_high_entry.config(bg="#FFDBDB")
					self.deiconify()
					self.lift()
					return in_range
				else:
					self.v_low_entry.config(bg="white")
					self.v_high_entry.config(bg="white")
					return in_range
			else:
				if not((float(entry.v_high) >= 0) and (float(entry.v_high) <= 30)):
					in_range = False
				if not in_range:
					self.withdraw()
					showerror("ERROR","The entered voltage (%s) is out of range (0kV-30kV).\nPlease adjust the voltage." % (entry.v_high))
					self.v_high_entry.config(bg="#FFDBDB")
					self.deiconify()
					self.lift()
				else:
					return in_range
					self.v_high_entry.config(bg="white")
		except:
			in_range = False
			self.withdraw()
			showerror("ERROR","The entered voltage value(s) are in the incorrect format (0-30).\nPlease adjust the voltage value(s).")
			if self.v_low_entry.cget('state')!='disabled':
				self.v_low_entry.config(bg="#FFDBDB")
			self.v_high_entry.config(bg="#FFDBDB")
			self.deiconify()
			self.lift()
			return in_range


	def add(self):
		item_num = self.radio_var.get()
		if item_num == 1:
			item_type = "RAMP"
		if item_num == 2:
			item_type = "TRIANGLE"
		if item_num == 3:
			item_type = "SQUARE"
		if item_num == 4:
			item_type = "STEP"
		if item_num == 5:
			item_type = "CONST"
		start_t = (self.t_start_var.get()).rstrip()
		stop_t = (self.t_stop_var.get()).rstrip()
		low_v = self.v_low_var.get()
		high_v = self.v_high_var.get()
		t_peak = self.t_peak_var.get()
		up_down_num = self.radio_var_2.get()
		if up_down_num == 1:
			up_down = 'up'
		if up_down_num == 2:
			up_down = 'down'
		if item_type == "TRIANGLE":
			schedule_item = TRI(self.parent,"TRIANGLE",start_t,stop_t,t_peak,low_v,high_v,"N/A")
		if item_type == "RAMP":
			schedule_item = RAMP(self.parent,"RAMP",start_t,stop_t,"N/A",low_v,high_v,up_down)
		if item_type == "SQUARE":
			schedule_item = SQR(self.parent,"SQUARE",start_t,stop_t,"N/A",low_v,high_v,"N/A")
		if item_type == "STEP":
			schedule_item = STEP(self.parent,"STEP",start_t,stop_t,"N/A",low_v,high_v,up_down)
		if item_type == "CONST":
			schedule_item = CONST(self.parent,"CONST",start_t,stop_t,"N/A","N/A",high_v,"N/A")	
		self.parent.current_start = stop_t
		self.ramp_radio.config(state=tk.DISABLED)
		self.step_radio.config(state=tk.DISABLED)
		self.triangle_radio.config(state=tk.DISABLED)
		self.square_radio.config(state=tk.DISABLED)
		self.const_radio.config(state=tk.DISABLED)
		self.up_radio.config(state=tk.DISABLED)
		self.down_radio.config(state=tk.DISABLED)
		self.v_low_entry.config(bg="white")
		self.v_high_entry.config(bg="white")
		self.t_start_entry.config(bg="white")
		self.t_stop_entry.config(bg="white")
		self.t_peak_entry.config(bg="white")
		check_true = self.check_entry(schedule_item)
		if check_true:
			check_true = self.range_check(schedule_item)
			if check_true:
				check_true = self.voltage_check(schedule_item)
				if check_true:
					self.update_list(schedule_item)
					self.destroy()

	def update_entries(self,item_type="RAMP"):
		if item_type == "RAMP":
			self.t_peak_entry.config(state=tk.DISABLED)
			self.t_peak_var.set('')
			self.up_radio.config(state=tk.NORMAL)
			self.down_radio.config(state=tk.NORMAL)
			self.v_low_entry.config(state=tk.NORMAL)
		if item_type == "TRI":
			self.t_peak_entry.config(state=tk.NORMAL)
			self.up_radio.config(state=tk.DISABLED)
			self.down_radio.config(state=tk.DISABLED)
			self.v_low_entry.config(state=tk.NORMAL)
		if item_type == "SQUARE":
			self.t_peak_entry.config(state=tk.DISABLED)
			self.v_low_entry.config(state=tk.NORMAL)
			self.up_radio.config(state=tk.DISABLED)
			self.down_radio.config(state=tk.DISABLED)
			self.t_peak_var.set('')
		if item_type == "STEP":
			self.t_peak_entry.config(state=tk.DISABLED)
			self.v_low_entry.config(state=tk.NORMAL)
			self.up_radio.config(state=tk.NORMAL)
			self.down_radio.config(state=tk.NORMAL)
			self.t_peak_var.set('')
		if item_type == "CONST":
			self.t_peak_entry.config(state=tk.DISABLED)
			self.v_low_entry.config(state=tk.DISABLED)
			self.up_radio.config(state=tk.DISABLED)
			self.down_radio.config(state=tk.DISABLED)
			self.t_peak_var.set('')

	def update_list(self,item=None):
		self.parent.schedulelist.delete(0,tk.END)
		self.parent.list_of_entries.append(item)
		sorted_tuple = sorted(self.parent.list_of_entries,key=lambda entry: entry.t_start)
		x = 0
		for entry in sorted_tuple:
			self.parent.list_of_entries[x] = entry
			x = x + 1
		self.parent.schedulelist.current_row = 0
		for entry in self.parent.list_of_entries:
			#print entry.t_start
			list_entry_text = ''
			list_entry_text = list_entry_text + str(entry.item_type)
			for i in range(0,(55-len(str(entry.item_type)))):
				list_entry_text = list_entry_text + ' '
			list_entry_text = list_entry_text + str(entry.t_start)
			for i in range(0,(55-len(str(entry.t_start)))):
				list_entry_text = list_entry_text + ' '
			list_entry_text = list_entry_text + str(entry.t_stop)
			for i in range(0,(55-len(str(entry.t_stop)))):
				list_entry_text = list_entry_text + ' '
			list_entry_text = list_entry_text + str(entry.t_mid)
			for i in range(0,(55-len(str(entry.t_mid)))):
				list_entry_text = list_entry_text + ' '
			list_entry_text = list_entry_text + str(entry.v_low)
			for i in range(0,(55-len(str(entry.v_low)))):
				list_entry_text = list_entry_text + ' '
			list_entry_text = list_entry_text + str(entry.v_high)
			for i in range(0,(55-len(str(entry.v_high)))):
				list_entry_text = list_entry_text + ' '
			list_entry_text = list_entry_text + str(entry.up_down)
			self.parent.schedulelist.insert(self.parent.schedulelist.current_row,list_entry_text)
			self.parent.schedulelist.current_row = self.parent.schedulelist.current_row + 1

class ScheduleItem:
	def __init__(self):{}
	def calc_seconds(self):
		t_start_arr = (self.t_start).split(':')
		start_hr = int(t_start_arr[0])
		start_m = int(t_start_arr[1])
		start_m_total = start_m + start_hr*60
		self.start_sec = start_m_total*60
		print self.start_sec
		t_stop_arr = (self.t_stop).split(':')
		stop_hr = int(t_stop_arr[0])
		stop_m = int(t_stop_arr[1])
		stop_m_total = stop_m + stop_hr*60
		self.stop_sec = stop_m_total*60
		if self.t_mid != "N/A":
			t_mid_arr = (self.t_mid).split(':')
			mid_hr = int(t_mid_arr[0])
			mid_m = int(t_mid_arr[1])
			mid_m_total = mid_m + mid_hr*60
			self.mid_sec = mid_m_total*60



class RAMP(ScheduleItem):
	def __init__(self,voltage_page,item_type="RAMP",t_start=0,t_stop=0,t_mid="N/A",v_low=0,v_high=0,up_down='up'):
		self.voltage_page = voltage_page
		self.item_type = item_type
		self.t_start = t_start
		self.t_stop = t_stop
		self.t_mid = t_mid
		self.v_low = v_low
		self.v_high = v_high
		self.up_down = up_down

class TRI(ScheduleItem):
	def __init__(self,voltage_page,item_type="TRIANGLE",t_start=0,t_stop=0,t_mid=0,v_low=0,v_high=0,up_down="N/A"):
		self.voltage_page = voltage_page
		self.item_type = item_type
		self.t_start = t_start
		self.t_stop = t_stop
		self.t_mid = t_mid
		self.v_low = v_low
		self.v_high = v_high
		self.up_down = up_down

class SQR(ScheduleItem):
	def __init__(self,voltage_page,item_type="SQUARE",t_start=0,t_stop=0,t_mid="N/A",v_low=0,v_high=0,up_down="N/A"):
		self.voltage_page = voltage_page
		self.item_type = item_type
		self.t_start = t_start
		self.t_stop = t_stop
		self.t_mid = t_mid
		self.v_low = v_low
		self.v_high = v_high
		self.up_down = up_down

class STEP(ScheduleItem):
	def __init__(self,voltage_page,item_type="STEP",t_start=0,t_stop=0,t_mid="N/A",v_low=0,v_high=0,up_down='up'):
		self.voltage_page = voltage_page
		self.item_type = item_type
		self.t_start = t_start
		self.t_stop = t_stop
		self.t_mid = t_mid
		self.v_low = v_low
		self.v_high = v_high
		self.up_down = up_down

class CONST(ScheduleItem):
	def __init__(self,voltage_page,item_type="CONST",t_start=0,t_stop=0,t_mid="N/A",v_low="N/A",v_high=0,up_down="N/A"):
		self.voltage_page = voltage_page
		self.item_type = item_type
		self.t_start = t_start
		self.t_stop = t_stop
		self.t_mid = t_mid
		self.v_low = v_low
		self.v_high = v_high
		self.up_down = up_down