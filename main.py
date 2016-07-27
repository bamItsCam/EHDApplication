import Tkinter as tk
from test_params_window import TestParamsWindow
from home_page import HomePage
from tkMessageBox import showerror,showinfo,askyesno
import ttk
import threading
from storage import Storage
from data_page import DataPage
from hardwareIO import HardwareIO
from hardwareIO import HardwareIOException
from debug_page import DebugPage
from voltage_page import VoltagePage
import re
import cProfile, pstats, StringIO

# Author:   Abigail Liff
# Date:     4/8/16
# Desc:     This is the main class, which, when launched, starts the application and is the main thread that holds all other processes. It is inherited from the tk.Tk class.
# Notes:    

LARGE_FONT = ("Verdana", 12)
NORM_FONT = ("Verdana", 12)
SMALL_FONT = ("Verdana", 8)

class Main(tk.Tk):
	# name: __init__
    # input:    nothing
    # output    nothing
    # desc:     The constructor for the Main class
    # purpose:  Runs the parent constructor, creates and owns other necessary objects, sets up the menubar and sets up the tab 
    # 			geometry
	def __init__(self,*args,**kwargs):

		# Running Parent Constructor
		tk.Tk.__init__(self,*args,**kwargs)

		# Main Window Geometry Grid Initialization
		tk.Grid.rowconfigure(self, 0, weight=1)
		tk.Grid.columnconfigure(self, 0, weight=1)

		# Allow us to run functions upon app exit
		self.protocol("WM_DELETE_WINDOW", self.on_exit)
		# Application Object Creation
		self.storage = Storage()

		# HardwareIO Object Creation
		self.hardwareIO = HardwareIO(self.storage)

		# Zeroing the voltage supply...
		try:
			t = threading.Thread(target=self.embedded_voltage_set, args=(0,))
			t.start()
		except HardwareIO as e:{}

		# Test Default Name Initialization
		self.test_num = int(self.storage.get_config("DefaultTestName"))
		self.current_default_test = "EHD Test " + str(self.test_num)
		self.storage.set_config("Test Name",self.current_default_test)

		# Tab System Initialization
		self.container = ttk.Notebook(self)
		self.container.pack(side="top",fill="both",expand=True)

		self.container.grid_rowconfigure(0,weight=1)
		self.container.grid_columnconfigure(0,weight=1)
		# Menubar Initialization

		# Main menu
		menubar = tk.Menu(self.container)

		# File menu
		filemenu = tk.Menu(menubar,tearoff=0)

		self.openmenu = tk.Menu(filemenu,tearoff=0)

		menubar.add_cascade(label="File",menu=filemenu)

		filemenu.add_cascade(label="Open          ",menu=self.openmenu)
		filemenu.add_separator()
		filemenu.add_command(label="Exit",command=self.quit)

		self.openmenu.add_command(label="Current Test",command=lambda: self.storage.open_current_test())
		self.openmenu.add_separator()
		self.openmenu.add_command(label="Previous Tests",command=lambda: self.storage.open_tests())
		self.openmenu.add_separator()
		self.openmenu.add_command(label="Log File",command=lambda: self.debug.open_log())
		self.openmenu.add_separator()
		self.openmenu.add_command(label="Configuration File",command=lambda: self.storage.open_config())
		
		# Open current test should be disabled by default since no test is running on startup
		self.openmenu.entryconfig("Current Test", state="disabled")

		# Edit menu
		self.editmenu = tk.Menu(menubar,tearoff=0)

		menubar.add_cascade(label="Edit",menu=self.editmenu)

		self.editmenu.add_command(label="Test Parameters",command=lambda: self.setup_test(self.container,self.home))
		self.editmenu.add_separator()
		self.editmenu.add_command(label="Heatflux Parameters", command=lambda: self.setup_heatflux(self.container,self.home))
		self.editmenu.add_separator()
		self.editmenu.add_command(label="Zero Balance",command=lambda: self.home.zero_balance())
		self.editmenu.add_separator()
		self.editmenu.add_command(label="Restore Default Config", command=lambda: self.restore_config())

		# View menu
		self.viewmenu = tk.Menu(menubar,tearoff=0)

		menubar.add_cascade(label="View",menu=self.viewmenu)

		self.viewmenu.add_command(label="Home",command=lambda: self.container.select(self.home))
		self.viewmenu.add_separator()
		self.viewmenu.add_command(label="Data",command=lambda: self.container.select(self.data))
		self.viewmenu.add_separator()
		self.viewmenu.add_command(label="Debug",command=lambda: self.container.select(self.debug))
		self.viewmenu.add_separator()
		self.viewmenu.add_command(label="Voltage Scheduler",command=lambda: self.container.select(self.voltage)) # greyed out at beginning, enabled after test params is "okayed"

		# Voltage Scheduler is disabled by default, requiring the user to edit the test params first
		self.viewmenu.entryconfig("Voltage Scheduler", state="disabled")


		# About menu
		aboutString = """
		The EHD Testing Application is designed to allow 
		researchers to further investigate the effects 
		of electrohydrodynamic drying.

		Made by the following students 
		of Grove City College:
		Abigail Liff
		Cameron Holloway
		Kenton McFaul
		Lucas Cleary

		v 1.1 - Copyright 2016
		"""
		aboutmenu = tk.Menu(menubar, tearoff=0)

		menubar.add_cascade(label="About",menu=aboutmenu)

		aboutmenu.add_command(label="Help (online wiki)",command=lambda: self.storage.open_help())
		aboutmenu.add_separator()
		aboutmenu.add_command(label="About",command=lambda: showinfo("About EHD Testing Environment", aboutString))

		tk.Tk.config(self,menu=menubar)

		# Tab Initialization
		self.debug = DebugPage(self.container,self.storage,self)
		self.home = HomePage(self.container,self.hardwareIO,self.storage,self.debug)
		self.voltage = VoltagePage(self.container,self.storage,self.hardwareIO,self.home)
		self.data = DataPage(self.container, self.storage,self.hardwareIO,self.home,self,self.voltage)
		self.home.data_page = self.data
		self.debug.homepage = self.home
		# Adding tabs to the notebook
		self.add_tab(self.container,self.home,"Home")
		self.add_tab(self.container,self.data,"Data")
		self.add_tab(self.container,self.debug,"Debug")
		self.add_tab(self.container,self.voltage,"Voltage Scheduler")

		# Voltage Scheduler is disabled by default, requiring the user to edit the test params first
		self.container.tab(3,state='disabled')

		
	def on_exit(self):
		if askyesno("Exit?", "Would you like to quit the EHD Testing Application?"):
			try:
				t = threading.Thread(target=self.embedded_voltage_set, args=(0,))
				t.start()
				#popup = showinfo("Exiting", "Setting the voltage to 0...")
			except HardwareIO as e:{}
			finally:
				self.destroy()
	
	def embedded_voltage_set(self,current_voltage):
		try:
			self.hardwareIO.set_hfg_voltage_feedback(current_voltage)
		except HardwareIOException as e:
			self.storage.log_event('debug',str(e))

	# add_tab is a member function of the View class. It makes a tab visible by adding it. 
	def add_tab(self,cont,frame,txt):
	# name: 	add_tab
    # input:    cont (type: tk.Notebook), frame (type: tk.Frame), txt (type: string)
    # output    nothing
    # desc:     Adding at selectable tab to the application
    # purpose:  This method adds frame to cont (the application's Notebook object, which holds all the frames) and assigns txt as 
    # 			the name of the new tab.
		cont.add(frame,text=txt)

	def setup_test(self,cont,frame):
	# name: 	setup_test
    # input:    cont (tk.Notebook object), frame (tk.Frame object)
    # output    nothing
    # desc:     method called by clicking the menu's "Test Parameters" option
    # purpose:  When the "Test Parameters" menu option is selected, this method will run, which will select the HomePage tab
    #			and open run its setup_test method (whose purpose is to open the Edit Test Parameters window).
		cont.select(frame)
		self.home.setup_test()

	def setup_heatflux(self,cont,frame):
	# name: 	setup_heatflux
    # input:    cont (tk.Notebook object), frame (tk.Frame object)
    # output    nothing
    # desc:     method called by clicking the menu's "Heaflux Parameters" option
    # purpose:  When the "Heaflux Parameters" menu option is selected, this method will run, which will select the HomePage tab
    #			and open run its setup_test method (whose purpose is to open the Heatflux Parameters window)
		cont.select(frame)
		self.home.setup_heatflux()

	def restore_config(self):
	# name: 	restore_config
    # input:    nothing
    # output    nothing
    # desc:     method called by clicking the menu's "Restore Default Config" option
    # purpose:  When the "Restore Default Config" menu option is selected, this method will run, which will attempt to run the storage
    #			object's default_config method (whose purpose is to restore the configuration file to default settings).
		try:
			self.storage.default_config()
		except:
			showerror("Restore Config Failed", "Unable to restore the configuration file to the original default.")
		else:
			showinfo("Restore Config Successful", "Successfully restored the configuration file to the original default.")

# Application Creation
app = Main()
app.geometry("800x680")
app.state("zoomed")
app.title("EHD Testing Application v.1.1")
app.mainloop()

