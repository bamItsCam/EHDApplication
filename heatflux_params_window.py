# -*- coding: utf-8 -*-
import re
from storage import Storage
from tkMessageBox import showerror
import Tkinter as tk 
import ttk
from Tkconstants import *
import os,sys

class HeatfluxParamsWindow(tk.Toplevel):
	def __init__(self,parent,storage):
		# input:    window parent, storage objct,
		# output:  	nothing, just initializes members 
		# desc:  	a constructor for the HeatfluxParams window/class. It initializes the window, 
		#			sets up the grid layout, and creates members
		# notes:    
		self.parent = parent
		self.storage = storage
		tk.Toplevel.__init__(self,parent)
		tk.Toplevel.title(self,"Heatflux Parameters")
		tk.Toplevel.config(self,borderwidth=5)
		self.resizable(0,0)

		# text box labels
		tk.Label(self,text="Thermal Conductivity (W/(m•K))",font=10).grid(row=0,column=0,sticky=tk.W)
		tk.Label(self,text="ex. 0.033").grid(row=0,column=2,sticky=tk.W)
		tk.Label(self,text="Plate Emissivity (%)",font=10).grid(row=1,column=0,sticky=tk.W)
		tk.Label(self,text="ex. 0.85").grid(row=1,column=2,sticky=tk.W)
		tk.Label(self,text=(u"Plate Area (m²)"),font=10).grid(row=2,column=0,sticky=tk.W)
		tk.Label(self,text="ex. 0.0225").grid(row=2,column=2,sticky=tk.W)
		tk.Label(self,text="Plate Resistance (Ω)",font=10).grid(row=3,column=0,sticky=tk.W)
		tk.Label(self,text="ex. 18").grid(row=3,column=2,sticky=tk.W)

		# get user input
		self.conductVar = tk.DoubleVar()
		self.emissVar = tk.DoubleVar()
		self.areaVar = tk.DoubleVar()
		self.resistVar = tk.DoubleVar()

		self.conductVar.set(self.storage.get_config("polyConduct"))
		self.emissVar.set(self.storage.get_config("plateEmiss"))
		self.areaVar.set(self.storage.get_config("plateArea"))
		self.resistVar.set(self.storage.get_config("plateResistance"))

		self.conductEntry = tk.Entry(self,width=20,textvariable=self.conductVar)
		self.emissEntry = tk.Entry(self,width=20,textvariable=self.emissVar)
		self.areaEntry = tk.Entry(self,width=20,textvariable=self.areaVar)
		self.resistEntry = tk.Entry(self,width=20,textvariable=self.resistVar)

		self.conductEntry.grid(row=0,column=1)
		self.emissEntry.grid(row=1,column=1)
		self.areaEntry.grid(row=2,column=1)
		self.resistEntry.grid(row=3,column=1)

		self.ok = tk.Button(self,text="Ok",width=10,command=lambda:self.saveHeatfluxParams())
		self.cancel = tk.Button(self,text="Cancel",width=10,command=self.destroy)
		self.ok.grid(row=4,column=1,sticky=tk.E)
		self.cancel.grid(row=4,column=2,sticky=tk.E)

		self.bind("<Return>",self.click)

	def click(self,event):
		# input:    an event (ya know, like clicking)
		# output:  	nothing!
		# desc:  	for use when binding the enter key to the ok button
		# notes: 
		self.ok.invoke()

	def saveHeatfluxParams(self):
		# input:    nothing!
		# output:  	nothing!
		# desc:  	checks and verifies user input for parameters; if they're good, save them to config!
		# notes: 	
		canExit = True

		# Polystyrene Thermal Conductivity Check
		try:
			float(self.conductVar.get())
		except ValueError:
			self.withdraw()
			canExit = False
			showerror("ERROR","Please enter a valid integer or float for Thermal Conductivity\nEx: 7 or 0.033")
			self.conductEntry.config(bg="#FFDBDB")
			self.deiconify()
			self.lift()
		else:
			if(float(self.conductVar.get()) > 1000 or float(self.conductVar.get()) < 0):
				self.withdraw()
				canExit = False
				showerror("ERROR","Please enter a Thermal Conductivity value\nthat falls within a reasonable range\n (0 <= Conductivity <= 1000)")
				self.conductEntry.config(bg="#FFDBDB")
				self.deiconify()
				self.lift()
			else: #acceptable input
				self.conductEntry.config(bg="#FFFFFF")
				self.storage.set_config("polyConduct", str(self.conductVar.get()))

		# Plate Emissivity Check
		try:
			float(self.emissVar.get())
		except ValueError:
			self.withdraw()
			canExit = False
			showerror("ERROR","Please enter a valid integer or float for Plate Emissivity\nEx: 1 or 0.8")
			self.emissEntry.config(bg="#FFDBDB")
			self.deiconify()
			self.lift()
		else:
			if(float(self.emissVar.get()) > 1 or float(self.emissVar.get()) <= 0):
				self.withdraw()
				canExit = False
				showerror("ERROR","Please enter a Plate Emissivity value\nthat falls within a reasonable range\n (0 < Emissivity <= 1)")
				self.emissEntry.config(bg="#FFDBDB")
				self.deiconify()
				self.lift()
			else: #acceptable input
				self.emissEntry.config(bg="#FFFFFF")
				self.storage.set_config("plateEmiss", str(self.emissVar.get()))

		# Plate Area Check
		try:
			float(self.areaVar.get())
		except ValueError:
			self.withdraw()
			canExit = False
			showerror("ERROR","Please enter a valid integer or float for Plate Area\nEx: 1 or 0.0225")
			self.areaEntry.config(bg="#FFDBDB")
			self.deiconify()
			self.lift()
		else:
			if(float(self.areaVar.get()) > 1 or float(self.areaVar.get()) <= 0):
				self.withdraw()
				canExit = False
				showerror("ERROR","Please enter a Plate Area value\nthat falls within a reasonable range\n (0 < Area <= 1)")
				self.areaEntry.config(bg="#FFDBDB")
				self.deiconify()
				self.lift()
			else: #acceptable input
				self.areaEntry.config(bg="#FFFFFF")
				self.storage.set_config("plateArea", str(self.areaVar.get()))

		# Plate Resistance Check
		try:
			float(self.resistVar.get())
		except ValueError:
			self.withdraw()
			canExit = False
			showerror("ERROR","Please enter a valid integer or float for Plate Resistance\nEx: 18 or 20.5")
			self.resistEntry.config(bg="#FFDBDB")
			self.deiconify()
			self.lift()
		else:
			if(float(self.resistVar.get()) > 50 or float(self.resistVar.get()) <= 0):
				self.withdraw()
				canExit = False
				showerror("ERROR","Please enter a Plate Resistance value\nthat falls within a reasonable range\n (0 < Resistance <= 50)")
				self.resistEntry.config(bg="#FFDBDB")
				self.deiconify()
				self.lift()
			else: #acceptable input
				self.resistEntry.config(bg="#FFFFFF")
				self.storage.set_config("plateResistance", str(self.resistVar.get()))

		if(canExit):
			self.destroy()
