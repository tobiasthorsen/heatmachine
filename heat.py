#!/usr/bin/env python3

# Display UTC.
# started with https://docs.python.org/3.4/library/tkinter.html#module-tkinter

import tkinter as tk
import time
import sys
import RPi.GPIO as GPIO
import json
import math
#from tkinter.ttk import Separator, Style
from tkinter import ttk
from tkinter import *
from sys import platform
from max31855 import MAX31855, MAX31855Error
from datetime import datetime
from functools import partial
print (platform)
windowWidth = 100
windowHeight = 100

PIN_OVENCONTROL = 4
PIN_THERMO_PIN = 15
PIN_THERMO_CLOCK = 14
PIN_THERMO_DATA = 18 # cs_pin, clock_pin, data_pin
PIN_SWITCH = 23

def current_iso8601():
	"""Get current date and time in ISO8601"""
	# https://en.wikipedia.org/wiki/ISO_8601
	# https://xkcd.com/1179/
	return time.time()
	# return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

class Oven:
	def __init__(self):
		self.mode = "real"
		GPIO.setup(PIN_OVENCONTROL, GPIO.OUT)
		GPIO.output(PIN_OVENCONTROL,  0)
		GPIO.setup(PIN_SWITCH, GPIO.IN)
		self.thermocouple = MAX31855(PIN_THERMO_PIN,PIN_THERMO_CLOCK,PIN_THERMO_DATA)
		if platform == "darwin":
			self.mode = "simulated"

		self.temperature = 12.0
		self.cputemperature = 12.0
		self.heating = 0
		self.targettemperature = 2000
		self.trackTemperature = 0
		self.open = 0

	def update(self):
		if self.mode == "real":
			# get the temperature from the max31855
			rj = self.thermocouple.get_rj()
			gottemperature = 0
			try:
				tc = self.thermocouple.get()
				self.temperature = tc
				gottemperature = 1
			except MAX31855Error as e:
				self.temperature = -1
				#tc = "Error: "+ e.value
				#running = False

			self.cputemperature = rj

			self.open = GPIO.input(PIN_SWITCH) # input the lid status maybe
		else:
			# simulated oven
			#print("simul")
			if self.heating:
				self.temperature += 0.1
			else:
				self.temperature += (12 - self.temperature ) * 0.01
		

		if (self.trackTemperature):
			print("tracking",self.targettemperature)
			if (not self.heating and self.temperature < self.targettemperature-.2):
			
				self.heat()
			
			elif (self.heating and self.temperature > self.targettemperature + .2):
				self.cool()
		

	def heat(self):
		GPIO.output(PIN_OVENCONTROL,  1)
		self.heating = 1

	def cool(self):
		GPIO.output(PIN_OVENCONTROL,  0)
		self.heating = 0
			


		

class Application(tk.Frame):
	def __init__(self, master=None):
		tk.Frame.__init__(self, master)
		GPIO.setmode(GPIO.BCM)
		self.pack()
		self.oven = Oven()
		self.washeating = 0
		self.wasopen = 0
		self.config = {}
		#GPIO.setmode(GPIO.BOARD)
		self.loadPrograms()

		self.setupTemperatureArray()
		
		self.createWidgets()
		self.onProgramClick("manual")
		self.onUpdate() #// start updating
	
	def loadPrograms(self):
		file = open('./programs.json', 'r')
		self.programs = json.load(file)
		self.programbuttons = {}
		self.config["manualtemperature"] = 40
		try:
			file = open('./config.json', 'r')
			self.config =  json.load(file)
			self.oven.targettemperature = self.config["manualtemperature"] 
		except:
			print("No config file. It will be created")

	def saveConfig(self):
		cfile = open('./config.json', 'w')
		json.dump(self.config, cfile)

	def setupTemperatureArray(self):
		self.temparray = []
		self.lastTemperatureLogTime = 0
		try:
			file = open('./temperatures.json', 'r')
			#print file
			self.temparray = json.load(file)
		except:
  			print("No temperature file. It will be created")
  		


	def logTemperature(self, _tempThermo, _tempInternal):
		t = time.time() - self.lastTemperatureLogTime
		if (t >= 4):
			self.temparray.append( {"time":int(time.time()), "tempThermo":_tempThermo, "tempInternal":_tempInternal} )# Temperature(tempThermo, tempInternal))
			self.lastTemperatureLogTime=time.time()
			self.drawTemperatureGraph()

			if len(self.temparray) % 10 == 0:
				self.saveTempArray()
				print (len(self.temparray))
			
	
	def drawTemperatureGraph(self) :
		#self.temperatureCanvas.create_line(0,0,100,100)
		self.temperatureCanvas.delete("all")
		self.temperatureCanvas.create_rectangle(0, 0, self.canvas_width, self.canvas_height, fill="#003366")
		# draw the grid first.
		nows = time.time()
		now = datetime.now()
		hoursprev = 1
		hoursahead = 1
		tempmax = 100
		tempmin = 0
		
		# look at graph to adjust tempmax and hours ahead and behind
		if (self.program["type"]=="graph"):
			for t in self.program["graph"]:
				if (t["temperature"] > tempmax):
					tempmax = t["temperature"]
				if (t["time"] > hoursahead):
					hoursahead = t["time"]
			if self.programRunning:
				programtime = (nows - self.programstarttime) / 60 / 60
				if (int(programtime+1) > hoursprev):
					hoursprev = int(programtime+1)
		
		
			if (int(hoursahead) <= hoursahead):
				hoursahead = int(hoursahead) + 1
		#hoursprev = hoursahead

		timestart = nows - hoursprev * 60 * 60 - now.second
		timeend = nows + hoursahead * 60 * 60 - now.second


		idx = 0
		while (len(self.temparray)>0 and self.temparray[0]["time"] < timestart):
			self.temparray.pop(0)
			#print ("can delete", idx)
			idx += 1 
		#print("deleted ", idx)


		# find tempmin and max
		for t in self.temparray:
			if (t["time"]<timestart):
				continue
			if (t["tempThermo"] > tempmax):
				tempmax = t["tempThermo"]
		
		tempmax *= 1.1

		self.temperatureCanvas.create_text(self.canvas_width-20, 20, text=str(int(tempmax)), fill="yellow", font=('Helvetica 13 bold'))

		

		t = timestart
		timeoff = 60 - now.minute
		pixelsprminute = float(self.canvas_width) / (float(hoursahead) + float(hoursprev)) / 60
		pixelsprdegree = float(self.canvas_height) / (tempmax - tempmin)
		#print "pixelsprdegree " + str(pixelsprdegree)
		hour = now.hour - hoursprev + 1
		while t<timeend:
			# draw a line at this point + offset (each hour bar)
			x = ((t-timestart)/60 + timeoff) * pixelsprminute
			self.temperatureCanvas.create_line(x,0,x,self.canvas_height)
			timetext = str((hour + 24) % 24) + ":00"
			self.temperatureCanvas.create_text(x, self.canvas_height-20, text=timetext, fill="white", font=('Helvetica 15 bold'))
			t+=(60*60)
			hour += 1

		# draw a bar at the now time.
		x = (nows-timestart) / 60 * pixelsprminute
		self.temperatureCanvas.create_line(x,0,x,self.canvas_height, fill="white")

		
		# draw the projected temperaturecurve
		
		prevx = -1
		prevy = 0
		if (self.program["type"]=="graph"):
			prevy = self.canvas_height - self.program["graph"][0]["temperature"] * pixelsprdegree
			startdisplaytime = nows
			if self.programRunning:
				startdisplaytime = self.programstarttime
			for t in self.program["graph"]:
				timesec = t["time"] * 60 * 60 + startdisplaytime
				x = (timesec - timestart ) / 60 * pixelsprminute
				y = self.canvas_height - t["temperature"] * pixelsprdegree
				self.temperatureCanvas.create_line(prevx,prevy,x,y, fill="gray")
				prevx = x
				prevy = y

				self.temperatureCanvas.create_line(x,y,x,y+15, fill="white")
				self.temperatureCanvas.create_text(x, y + 20, text=str(int(t["temperature"])), fill="white", font=('Helvetica 10'))
				#print("graph time ", timesec)
		
		# draw the graphs..		
		prevx = -1
		prevy = 0
		for t in self.temparray:
			if (t["time"]<timestart):
				continue
			x = (t["time"] - timestart) / 60 * pixelsprminute
			y = self.canvas_height - t["tempThermo"] * pixelsprdegree
			dx = x - prevx
			if (dx>1 ):#and x-prevx>1):
				if (dx < 8):
					self.temperatureCanvas.create_line(prevx,prevy,x,y, fill="yellow")
				prevx = x
				prevy = y

			#print(t["time"])

	
	def saveTempArray(self):
		#print json.dumps(self.temparray)
		tempfile = open('./temperatures.json', 'w')
		json.dump(self.temparray, tempfile)

	def buttonClickOn(self):
		self.oven.heat()
		

	def buttonClickOff(self):
		self.oven.cool()
		#GPIO.output(4,  0)

	def createWidgets(self):
		
		temperatureFrame = tk.Frame(self, bg="black",width=windowWidth*.27, height=190)
		#left.pack(fill="both", expand=True) # pack_propagate(False)
		temperatureFrame.pack_propagate(False)
		temperatureFrame.grid(column=0, row = 0, pady=2 ,padx=2, sticky="n")
		tk.Label(temperatureFrame, text="Kiln", fg="white", bg="black", anchor="center", justify="center").pack()
		
		
		self.temperatureLabel = tk.Label(temperatureFrame, text="69", fg="white", bg="black", anchor="center", justify="center", font=("Arial Bold", 65))
		self.temperatureLabel.pack()
		self.temperatureLabel.configure(text="65") #//['text'] = 68
		
		tk.Label(temperatureFrame, text="Cpu", fg="white", bg="black", anchor="center", justify="center").pack()
		self.cpuTemperatureLabel = tk.Label(temperatureFrame, text="24",  fg="white", bg="black", anchor="center", justify="center", font=("Arial Bold", 25))
		self.cpuTemperatureLabel.pack()

		self.activeProgramFrame = tk.Frame(self, bg="black", width=windowWidth*.67,height=190)
		self.activeProgramFrame.pack_propagate(False)
		
		self.activeProgramFrame.grid(column=1, row = 0, pady=2,padx=2, sticky="n")
		tk.Label(self.activeProgramFrame,  text="Actions", fg="white", bg="black").pack(side=TOP, anchor=NW)

		temperatureGraph = tk.Frame(self, bg="black", width=windowWidth*.95,height=270)
		temperatureGraph.pack_propagate(False)
		temperatureGraph.grid(column=0, columnspan=2, row = 1, pady=0,padx=0, sticky="n")

		self.canvas_width = windowWidth*.95
		self.canvas_height = 270
		self.temperatureCanvas = tk.Canvas(temperatureGraph, width=self.canvas_width, height=self.canvas_height)
		self.temperatureCanvas.pack()

		activeProgramFrame = tk.Frame(self, bg="black", width=windowWidth*(.95-.27),height=100)
		activeProgramFrame.pack_propagate(False)
		activeProgramFrame.grid(column=0, columnspan=2, row = 2, pady=2,padx=2, sticky="n")

		separator = ttk.Separator(activeProgramFrame, orient='vertical')
		separator.pack(side=LEFT, fill="y", padx=10, pady=0)

		for x in self.programs:
			btn = tk.Button(activeProgramFrame, text=x, fg="red", width=12, height = 3, command=partial(self.onProgramClick, x))
			btn.pack(side=LEFT)
			separator = ttk.Separator(activeProgramFrame, orient='vertical')
			separator.pack(side=LEFT, fill="y", padx=10, pady=0)
			self.programs[x]["button"] = btn
			print(x)


		self.QUIT = tk.Button(self, text="QUIT", fg="red", command=root.destroy)
		#self.QUIT.pack(side="bottom")
		self.QUIT.grid(column = 0, row = 3,  pady=5,padx=10, sticky="n")
		# to prevent the frame from adapting to its content :
		"""
		
		
		sep = Separator(self, orient="vertical")
		sep.grid(column=1, row=0, sticky="ns")
		"""
		#fen = tk.Tk()
		"""

		# edit: To change the color of the separator, you need to use a style
		sty = Style(root)
		sty.configure("TSeparator", background="red")

		
		# initial time display
		"""
		
		#self.now.set(current_iso8601())
	
	def onProgramClick(self, program):
		print("click program: ", program)
		
		for b in self.programbuttons:
			self.programbuttons[b].destroy()

		#if ("turnOn"  in self.programbuttons):
		#	self.programbuttons["turnOn"].destroy()
		#
		#if ("turnOff" in self.programbuttons):
		#	self.programbuttons["turnOff"].destroy()
		self.usetemp = tk.IntVar()
		program = self.programs[program]
		self.program = program
		framewidth = windowWidth*(.95-.27)
		

		if (program["type"] == "manual"):


			but =  tk.Button(self.activeProgramFrame, width=25, height=3, text="ON", fg="red", command=self.buttonClickOn)
			but.place(x=10, y=30)
			self.programbuttons['turnOn'] = but # tk.Button(self.activeProgramFrame, width=25, height=3, text="ON", fg="red", command=self.buttonClickOn)
				

			but = tk.Button(self.activeProgramFrame, width=25, height=3, text="OFF", fg="red", command=self.buttonClickOff)
			but.place(x=10, y=100)
			self.programbuttons['turnOff'] = but #pack(side=TOP, anchor=NW)
			
			##self.programbuttons['turnOff'] = tk.Button(self.activeProgramFrame, width=25, height=3, text="OFF", fg="red", command=self.buttonClickOff)
			#self.programbuttons['turnOff'].pack(side=TOP, anchor=NW)
			
			c1 = tk.Checkbutton(self.activeProgramFrame, text='Use temperaturecontrol',variable=self.usetemp, onvalue=1, offvalue=0, command=self.checkbox)
			c1.place(x=framewidth*.6 + 60, y=20)
			self.programbuttons['check'] = c1

			btn = tk.Button(self.activeProgramFrame, width=3, height=1, text="-", fg="red",font=("Arial Bold", 30), command=self.changeTemperatureDown)
			btn.place(x=framewidth*.6,y=50)
			self.programbuttons["minus"] = btn
			#separator = ttk.Separator(self.activeProgramFrame, orient='vertical')
			#separator.pack(side=RIGHT, fill="y", padx=10, pady=0)
			#self.programbuttons["sepa"] = separator

			lbl = tk.Label(self.activeProgramFrame, text=self.config["manualtemperature"], fg="white", bg="black", anchor="center", justify="center", font=("Arial Bold", 40))
			lbl.place(x=framewidth*.6 + 100,y=50)
			
			self.programbuttons["tlabel"] = lbl

			#separator = ttk.Separator(self.activeProgramFrame, orient='vertical')
			#separator.pack(side=RIGHT, fill="y", padx=10, pady=0)
			#self.programbuttons["sepb"] = separator

			btn = tk.Button(self.activeProgramFrame, width=3, height=1, text="+", fg="red",font=("Arial Bold", 30), command=self.changeTemperatureUp)
			btn.place(x=framewidth*.6 + 170,y=50)
			self.programbuttons["plus"] = btn
			self.oven.trackTemperature = 0
		elif (program["type"]=="graph"):
			self.oven.trackTemperature = 0

			but =  tk.Button(self.activeProgramFrame, width=25, height=3, text="RUN", fg="red", command=self.buttonClickStart)
			but.place(x=10, y=30)
			self.programbuttons['start'] = but # tk.Button(self.activeProgramFrame, width=25, height=3, text="ON", fg="red", command=self.buttonClickOn)
			self.programRunning = 0
			but =  tk.Button(self.activeProgramFrame, width=25, height=3, text="STOP", fg="red", command=self.buttonClickStop)
			but.place(x=10, y=100)
			but.place_forget()
			self.programbuttons['stop'] = but # tk.Button(self.activeProgramFrame, width=25, height=3, text="ON", fg="red", command=self.buttonClickOn)
		
		self.drawTemperatureGraph()

	def checkbox(self):
		print("check", self.usetemp.get())
		#self.config["manualtemperature"] = 
		self.oven.trackTemperature = self.usetemp.get()
		self.saveConfig()

	def changeTemperatureUp(self):
		lbl = self.programbuttons["tlabel"]
		self.config["manualtemperature"] = self.config["manualtemperature"] + 5
		lbl.configure(text=self.config["manualtemperature"])
		self.oven.targettemperature = self.config["manualtemperature"] 
		self.saveConfig()

	def changeTemperatureDown(self):
		lbl = self.programbuttons["tlabel"]
		self.config["manualtemperature"] = self.config["manualtemperature"] - 5
		lbl.configure(text=self.config["manualtemperature"])
		self.oven.targettemperature = self.config["manualtemperature"] 
		self.saveConfig()

	def buttonClickStart(self):
		self.programRunning = 1
		self.programstarttime = time.time()
		self.programbuttons['start'].config(state= DISABLED)
		self.programbuttons['stop'].place(x=10, y=100)
	def buttonClickStop(self):
		self.programRunning = 0
		self.programbuttons['stop'].place_forget()
		self.programbuttons['start'].config(state= NORMAL)

	def onUpdate(self):
		# update displayed time
		# self.now.set(current_iso8601())
		
		if (self.program["type"]=="graph"):
			prevtime = 0
			prevtemp = self.program["graph"][0]["temperature"]
			#prevy = self.canvas_height - self.program["graph"][0]["temperature"] * pixelsprdegree
			#startdisplaytime = nows
			if self.programRunning:
				targettemperature = 0
				nowtime = time.time() - self.programstarttime
				for t in self.program["graph"]:
					timesec = t["time"] * 60 * 60 
					if (timesec < nowtime): # now has passed the timesec time
						prevtime = timesec
						prevtemp = t["temperature"]
					else:
						nowfactor = (nowtime - prevtime) / (timesec - prevtime)
						targettemperature = prevtemp + (t["temperature"] - prevtemp) * nowfactor
						break
				self.oven.trackTemperature = 1
				self.oven.targettemperature = targettemperature
			else:
				self.oven.trackTemperature = 0


		self.oven.update()
		
		
		if (self.oven.open and not self.wasopen):
			self.temperatureLabel.config(bg="blue")
		elif (not self.oven.open and self.wasopen):
			self.temperatureLabel.config(bg="black")

		self.wasopen = self.oven.open

		if (not self.oven.open): 
			
			
			if (self.oven.heating and not self.washeating):
				self.temperatureLabel.config(bg="red")

			elif (not self.oven.heating and self.washeating): 
				self.temperatureLabel.config(bg="black")
			
			self.washeating = self.oven.heating

		

		self.logTemperature(self.oven.temperature, self.oven.cputemperature)
		self.temperatureLabel.configure(text='{0:.1f}'.format(self.oven.temperature)) 
		self.cpuTemperatureLabel.configure(text='{0:.1f}'.format(self.oven.cputemperature)) 

		"""rj = self.thermocouple.get_rj()
		gottemperature = 0
		try:
			tc = self.thermocouple.get()
			gottemperature = 1
		except MAX31855Error as e:
			tc = "Error: "+ e.value
			#running = False

		#print("tc: {} and rj: {}".format(tc, rj))
		
		if platform == "darwin": # simulate some stuff to display
			tc = math.cos(time.time()/60/40) * 300 + 400
			rj = math.sin(time.time()/60/30) * 25 + 25


		if gottemperature:
			self.temperatureLabel.configure(text='{0:.1f}'.format(tc)) 
		else:
			self.temperatureLabel.configure(text='X') 
			tc = 0
		

		self.cpuTemperatureLabel.configure(text='{0:.1f}'.format(rj)) 

		self.logTemperature(tc,rj)

		#self.temperatureLabel['text'] = tc
		#self.cpuTemperatureLabel['text'] = rj

		onoff = 0	
		if int(time.time() ) % 2 == 0:
			onoff = 1

		# GPIO.output(4,  onoff)
		# schedule timer to call myself after 1 second
		
		"""
		self.after(250, self.onUpdate)


root = tk.Tk()
root.geometry('400x300')
root.attributes('-fullscreen', True)
root.update()
#root.resizable(height = None, width = None)
windowWidth = root.winfo_width()
windowHeight = root.winfo_height()
#print(root.winfo_height())
app = Application(master=root)
#root.attributes('-fullscreen', True)
root.mainloop()

"""
from tkinter import *
from datetime import date

import time




window = Tk()

window.title("Welcome to LikeGeeks app")

window.geometry('350x200')

lbl = Label(window, text="Hello", font=("Arial Bold", 50))

lbl.grid(column=0, row=0)


def current_milli_time():
    return round(time.time() * 1000)

def clicked():
	#today = date.ctime()
	ms = time.time()*1000.0
	#print("Today's date:", today)
	lbl.configure(text="Button was clicked !!" +str( ms))

btn = Button(window, text="Click Me", command=clicked)

btn.grid(column=1, row=0)

chk_state = BooleanVar()
chk = Checkbutton(window, text='Choose', var=chk_state)

chk.grid(column=0, row=1)

def mainloop():
    print("Hello, World")
    ms = time.time()*1000.0
    lbl.configure(text="aa " +str( int(ms)))



tkinter.after(1000,mainloop)
window.mainloop()


"""