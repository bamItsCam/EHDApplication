import Tkinter as tk
import Tkconstants, tkFileDialog
import ttk
from home_page import HomePage
from storage import Storage
from time import strftime
import time
from test import *
import logging
import os
from os.path import isfile,join,isdir
from os import makedirs


class DebugPage(ttk.Frame):
	def __init__(self,parent,storage,controller,home_page=None):
		ttk.Frame.__init__(self,parent)
		self.parent = parent
		self.config(padding=30)
		self.storage = storage
		self.homepage = home_page
		# Geometry initialization
		tk.Grid.rowconfigure(self, 0, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 1, uniform=2,weight=5)
		tk.Grid.rowconfigure(self, 2, uniform=1,weight=1)
		tk.Grid.rowconfigure(self, 3, uniform=1,weight=1)
		tk.Grid.columnconfigure(self,0,uniform=1,weight=1)
		tk.Grid.columnconfigure(self,1,uniform=1,weight=1)

		# Geometry initialization - Labels
		tk.Label(self,text="Debug Information",font=("Helvetica", 20)).grid(row=0,column=0,columnspan=2)

		# Geometry initialization - Buttons
		self.refresh_button = tk.Button(self,text="Refresh",width=20,command=lambda: self.refresh())
		self.refresh_button.grid(row=3,column=0)
		self.refresh_button.config(state=tk.NORMAL)
		self.open_log_button = tk.Button(self,text="Open Log File",width=20,command=lambda: self.open_log())
		self.open_log_button.config(state=tk.NORMAL)
		self.open_log_button.grid(row=3,column=1)


		# Geometry initialization - Scrollable Textboxes
		self.canv = tk.Canvas(self)
		self.canv.grid(row=1,column=0,columnspan=2,sticky=tk.E+tk.W)

		self.scroll_debug_x = tk.Scrollbar(self.canv,orient=tk.HORIZONTAL)
		self.scroll_debug_x.pack(side=tk.BOTTOM,fill=tk.X)

		self.scroll_debug = tk.Scrollbar(self.canv)
		self.scroll_debug.pack(side=tk.RIGHT,fill=tk.Y)

		self.debug_disp = tk.Text(self.canv)
		self.debug_disp.pack(fill=tk.X)
		self.debug_disp.config(state=tk.DISABLED,yscrollcommand=self.scroll_debug.set,xscrollcommand=self.scroll_debug_x.set)
		self.scroll_debug_x.config(command=self.debug_disp.xview)
		self.scroll_debug.config(command=self.debug_disp.yview)


	def refresh_debug(self):
		filename = self.storage.current_log_filename
		debug_string = ''
		queue_holder = []
		queue_size = self.storage.debug_queue.qsize()
		for i in range(0,queue_size):
			queue_holder.append(self.storage.debug_queue.get())
			debug_string = debug_string + str(queue_holder[i]) + '\n'
		for i in range(0,queue_size):
			self.storage.debug_queue.put(queue_holder[i])
		self.debug_disp.config(state=tk.NORMAL)
		self.debug_disp.delete("1.0", tk.END)
		self.debug_disp.insert(tk.END,debug_string)
		self.debug_disp.config(state=tk.DISABLED)

	def open_log(self):
		if not isdir('C:\\EHD\\'):
			makedirs('C:\\EHD\\')
		if not isdir('C:\\EHD\\Log\\'):
			makedirs('C:\\EHD\\Log\\')
		options = {}
		options['defaultextension'] = '.log'
		options['filetypes'] = [('all files', '.*'), ('log files', '.log')]
		options['initialdir'] = 'C:\\EHD\\Log\\'
		options['initialfile'] = 'App_Log.log'
		options['parent'] = self
		file = tkFileDialog.askopenfile(mode='r', **options)
		if file:
			filename = file.name
			os.startfile(filename)
	def refresh(self):
		self.homepage.check_sensors()
		self.refresh_debug()

def disable_button(button):
	button.config(state=tk.DISABLED)

def enable_button(button):
	button.config(state=tk.NORMAL)