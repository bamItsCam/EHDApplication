import Tkinter as tk
import Tkconstants, tkFileDialog
import ttk
from home_page import HomePage
from storage import Storage
from test_params import TestParams
from hardwareIO import HardwareIO
from time import strftime
import time
from test import *
import logging
import os

class AllTestsPage(ttk.Frame):
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
		tk.Grid.columnconfigure(self,2,uniform=1,weight=1)

		# Geometry initialization - Labels
		tk.Label(self,text="Previous Tests",font=("Helvetica", 20)).grid(row=0,column=0,columnspan=3)

		# Geometry initialization - Buttons
		self.refresh_button = tk.Button(self,text="Open Selected",width=20)
		self.refresh_button.grid(row=3,column=0)
		self.refresh_button.config(state=tk.NORMAL)
		self.open_log_button = tk.Button(self,text="Delete Selected",width=20)
		self.open_log_button.config(state=tk.NORMAL)
		self.open_log_button.grid(row=3,column=1)
		self.open_log_button = tk.Button(self,text="Refresh List",width=20)
		self.open_log_button.config(state=tk.NORMAL)
		self.open_log_button.grid(row=3,column=2)		


		# Geometry initialization - Scrollable Canvas
		self.frame = tk.Frame(self,bg='white')
		self.frame.grid(row=1,column=0,columnspan=3,sticky=tk.E+tk.W+tk.N+tk.S)


		self.scroll_frame_x = tk.Scrollbar(self.frame,orient=tk.HORIZONTAL)
		self.scroll_frame_x.pack(side=tk.BOTTOM,fill=tk.X)

		self.scroll_frame = tk.Scrollbar(self.frame)
		self.scroll_frame.pack(side=tk.RIGHT,fill=tk.Y)


		header_elements = ["Timestamp","Filename","Test Name","Duration","Sample Rate","Select"]
		header_text = ''
		for i in header_elements:
			header_text = header_text + i
			for j in range(0,57-len(i)):
				header_text = header_text + ' '

		tk.Label(self.frame,text=header_text,bg="white").pack()

		#self.debug_disp = tk.Text(self.canv)
		#self.debug_disp.pack(fill=tk.X)
		#self.debug_disp.config(state=tk.DISABLED,yscrollcommand=self.scroll_debug.set,xscrollcommand=self.scroll_debug_x.set)
		#self.scroll_debug_x.config(command=self.debug_disp.xview)
		#self.scroll_debug.config(command=self.debug_disp.yview)


	def refresh_list(self):{}

	def open_selected(self):{}

	def delete_selected(self):{}

def disable_button(button):
	button.config(state=tk.DISABLED)

def enable_button(button):
	button.config(state=tk.NORMAL)