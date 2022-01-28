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
from tkinter.ttk import *
from sys import platform
from max31855 import MAX31855, MAX31855Error
from datetime import datetime
import random


#import datetime
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
		
		self.thermocouple = MAX31855(PIN_THERMO_PIN,PIN_THERMO_CLOCK,PIN_THERMO_DATA)
		if platform == "darwin":
			self.mode = "simulated"
		else:
			GPIO.setup(PIN_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
		self.temperature = 12.0
		self.cputemperature = 12.0
		self.heating = 0
		self.targettemperature = 2000
		self.trackTemperature = 0
		self.closed = 1
		self.thermocoupleOK = 1

	def update(self):
		if self.mode == "real":
			# get the temperature from the max31855
			rj = self.thermocouple.get_rj()
			gottemperature = 0
			try:
				tc = self.thermocouple.get()
				self.temperature = tc
				gottemperature = 1
				self.thermocoupleOK = 1
			except MAX31855Error as e:
				#self.temperature = -1
				self.thermocoupleOK = 0
				#tc = "Error: "+ e.value
				#running = False

			self.cputemperature = rj

			self.closed = GPIO.input(PIN_SWITCH) # input the lid status maybe
		else:
			# simulated oven
			#print("simul")
			if self.heating:
				self.temperature += 0.15
			else:
				self.temperature += (12 - self.temperature ) * 0.002
			
			if (random.randint(0,20) == 0):
				self.thermocoupleOK = 0
			else:
				self.thermocoupleOK = 1


		if (self.trackTemperature):
			#print("tracking",self.targettemperature)
			if (not self.heating and self.temperature < self.targettemperature-.2):
			
				self.heat()
			
			elif (self.heating and self.temperature > self.targettemperature + .2):
				self.cool()
		#elif (self.heating):
		#	self.cool()
		

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
		self.wasclosed = 0
		self.config = {}
		self.wasthermocoupleOK = 1
		self.showWarningTick = 0
		self.heataccum = 0
		self.programstarttime = time.time()
		self.mustreahtemperature = 0
		self.zoomlevel = 1.0
		self.programRunning = 0

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
		self.temparrayStartDraw = 0
		try:
			file = open('./temperatures.json', 'r')
			#print file
			self.temparray = json.load(file)
		except:
  			print("No temperature file. It will be created")
  		


	def logTemperature(self, _tempThermo, _tempInternal, heating):
		t = time.time() - self.lastTemperatureLogTime
		if (heating):
			self.heataccum += 1
		if (t >= 4):
			print("Logging temperature ", self.heataccum)
			self.temparray.append( {"time":int(time.time()), "tempThermo":_tempThermo, "tempInternal":_tempInternal, "heatcount": self.heataccum} )# Temperature(tempThermo, tempInternal))
			self.lastTemperatureLogTime=time.time()
			self.heataccum = 0
			self.drawTemperatureGraph()

			if len(self.temparray) % 10 == 0:
				self.saveTempArray()
				print ("saving tempoeratures: " , len(self.temparray))
			
	
	def drawTemperatureGraph(self) :
		#self.temperatureCanvas.create_line(0,0,100,100)
		self.temperatureCanvas.delete("all")
		self.temperatureCanvas.create_rectangle(0, 0, self.canvas_width, self.canvas_height, fill="#003366")
		# draw the grid first.

		nows = time.time()
		now = datetime.now()
		hoursprev = 1.0 * self.zoomlevel
		hoursahead = 1.0
		tempmax = 50
		tempmin = 0
		programtime = 0
		# look at graph to adjust tempmax and hours ahead and behind
		if (self.program["type"]=="graph"):
			programtime = (nows - self.programstarttime) / 60 / 60
			for t in self.program["graph"]:
				if (t["temperature"] > tempmax):
					tempmax = t["temperature"]
				if (t["time"]-programtime   > hoursahead):
					hoursahead = t["time"]-programtime
			if self.programRunning:
				
				if (programtime + .1 > hoursprev):
					hoursprev = programtime + .1
		
		
			#if (int(hoursahead) < hoursahead):
			#	hoursahead = int(hoursahead) + 1
		#hoursprev = hoursahead
		if (self.zoomlevel < 1):
			hoursahead = hoursahead*self.zoomlevel


		print("hoursahead: ", hoursahead, hoursprev, programtime)
		timestart = nows - hoursprev * 60 * 60 - now.second
		timeend = nows + hoursahead * 60 * 60 - now.second

		discardtime = 48 # disscard temperatures older than 48 hours
		discardtime = nows - discardtime * 60 * 60
		idx = 0
		while (len(self.temparray)>0 and self.temparray[0]["time"] < discardtime):
			self.temparray.pop(0)
			#print ("can delete", idx)
			#idx += 1 
		#print("deleted ", idx)


		# find tempmin and max
		idx = self.temparrayStartDraw
		while (idx<len(self.temparray)):
			t = self.temparray[idx]
			idx += 1
			if (t["time"]<timestart):
				self.temparrayStartDraw = idx

				continue
			if (t["tempThermo"] > tempmax):
				tempmax = t["tempThermo"]

			
		#for t in self.temparray:
		#	if (t["time"]<timestart):
		#		continue
		#	if (t["tempThermo"] > tempmax):
		#		tempmax = t["tempThermo"]
		#
		tempmax *= 1.1

		self.temperatureCanvas.create_text(self.canvas_width-20, 20, text=str(int(tempmax)), fill="yellow", font=('Helvetica 12 bold'))

		

		# draw hour lines
		t = timestart
		#timestartmin = (timestart/60)

		timeoff = ((nows - timestart) / 60) % 60 - now.minute # 60 - now.minute
		pixelsprminute = float(self.canvas_width) / (float(hoursahead) + float(hoursprev)) / 60
		pixelsprdegree = float(self.canvas_height) / (tempmax - tempmin)
		#print "pixelsprdegree " + str(pixelsprdegree)
		hour = int(now.hour - int(hoursprev) + 24) % 24 #  (int( now.hour - hoursprev + 1) + 24) % 24
		while t<timeend:
			# draw a line at this point + offset (each hour bar)
			x = ((t-timestart)/60 + timeoff) * pixelsprminute
			self.temperatureCanvas.create_line(x,0,x,self.canvas_height)
			timetext = str(hour % 24) + ":00"
			self.temperatureCanvas.create_text(x, 12, text=timetext, fill="white", font=('Helvetica 12 bold'))
			t+=(60*60)
			hour += 1

		# draw temperatures pr 100
		t = 0
		while (t<tempmax):
		
			y = (t - tempmin) * pixelsprdegree
			self.temperatureCanvas.create_line(0, y, self.canvas_width, y, fill="#2244aa")
			t+= 100
		

		# draw a bar at the now time.
		x = (nows-timestart) / 60 * pixelsprminute
		self.temperatureCanvas.create_line(x,0,x,self.canvas_height, fill="white")

		# draw a bar at the now time.
		if (self.programRunning):
			x = (self.programstarttime - timestart) / 60 * pixelsprminute
			self.temperatureCanvas.create_line(x,0,x,self.canvas_height, fill="green")
		
		nowx = x
		# draw the projected temperaturecurve
		
		prevx = -1
		prevy = 0
		if (self.program["type"]=="graph"):
			prevy = self.canvas_height - self.program["graph"][0]["temperature"] * pixelsprdegree
			startdisplaytime = nows
			if self.programRunning:
				startdisplaytime = self.programstarttime
			for t in self.program["graph"]:
				timesec = t["targettime"] * 60 * 60 + startdisplaytime
				x = (timesec - timestart ) / 60 * pixelsprminute
				y = self.canvas_height - t["temperature"] * pixelsprdegree
				
				self.temperatureCanvas.create_line(prevx,prevy,x,y, fill="gray")
				
				prevx = x
				prevy = y

				self.temperatureCanvas.create_line(x,y,x,y+15, fill="white")
				self.temperatureCanvas.create_text(x, y + 20, text=str(int(t["temperature"])), fill="white", font=('Helvetica 10'))

				try:
					if (t["mustreach"]):
						self.temperatureCanvas.create_oval(x-10,y-10,x+10,y+10)

				except:
					x = 0 #print("x")
		
		# draw the graphs..		
		prevx = nowx
		prevy = -1
		prevtime = 0
		heatcount = 0
		heatcountmax = 0
		dutyavg = self.canvas_height
		dx = 0

		#idx = self.temparrayStartDraw
		idx = len(self.temparray) - 1
		firstx = -1
		while (idx>=0): #len(self.temparray)):
			t = self.temparray[idx]
			idx -= 1
			
			#if (t["time"]<timestart):
			#	prevtime = t["time"]
			#	continue
			x = (t["time"] - timestart) / 60 * pixelsprminute
			
			if (x < 0): # we are outside
				break
			y = self.canvas_height - t["tempThermo"] * pixelsprdegree
			
			if (prevy < 0):
				prevy = y

			dx = x - prevx

			#print("draw" , idx, x, y, dx)

			if (firstx == -1):
				firstx = x


			try:
				heatcount = heatcount + int(t["heatcount"])
			except Exception as e:
				heatcount += 0
			
			
			if (dx<-1 ):#and x-prevx>1):

				dt = t["time"] - prevtime
				heatcountmax = dt * 4
				#print("deltatime: ", dt, heatcountmax, heatcount,dx)
				if (dx>-8):
					self.temperatureCanvas.create_line(prevx,prevy,x,y, fill="yellow")
				
				heaty =  self.canvas_height - (50 / heatcountmax) * heatcount
				prevduty = dutyavg
				dutyavg = (dutyavg * 5 + heaty) / 6
				accx = 0
				while (accx>dx):
					self.temperatureCanvas.create_line(x+accx,self.canvas_height,x + accx,heaty, fill="red")
					accx -= 1
				self.temperatureCanvas.create_line(prevx,prevduty, x, dutyavg, fill="white")
				prevx = x
				prevy = y
				prevtime = t["time"]
				heatcount = 0

			#print(t["time"])
		
		#//if firstx > 2 and self.temparrayStartDraw > 10:
		#	self.temparrayStartDraw -= 10


	
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
		
		temperatureFrame = tk.Frame(self, bg="black",width=windowWidth*.37, height=190)
		#left.pack(fill="both", expand=True) # pack_propagate(False)
		temperatureFrame.pack_propagate(False)
		temperatureFrame.grid(column=0, row = 0, pady=2 ,padx=2, sticky="n")
		self.temperatureHeadline = tk.Label(temperatureFrame, text="Kiln", fg="white", bg="black", anchor="center", justify="center")
		self.temperatureHeadline.pack()
		
		self.temperatureLabel = tk.Label(temperatureFrame, text="69", fg="white", bg="black", anchor="center", justify="center", font=("Arial Bold", 65))
		self.temperatureLabel.pack()
		self.temperatureLabel.configure(text="65") #//['text'] = 68
		
		
		self.ovenWarning = tk.Label(temperatureFrame, text="Warning - Thermocouple error", fg="white", bg="black", anchor="center", justify="center")
		self.ovenWarning.pack()
		self.ovenWarning.pack_forget()

		tk.Label(temperatureFrame, text="Cpu", fg="white", bg="black", anchor="center", justify="center").pack()
		self.cpuTemperatureLabel = tk.Label(temperatureFrame, text="24",  fg="white", bg="black", anchor="center", justify="center", font=("Arial Bold", 25))
		self.cpuTemperatureLabel.pack()

		self.activeProgramFrame = tk.Frame(self, bg="black", width=windowWidth*.57,height=190)
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
		btn = tk.Button(temperatureGraph, text="-", fg="red", width=1, height = 1,  font=("Arial Bold", 20), command=self.onZoomOut)
		btn.place(x=0, y=self.canvas_height - 40)

		btn = tk.Button(temperatureGraph, text="x", fg="red", width=1, height = 1,  font=("Arial Bold", 20), command=self.onZoomReset)
		btn.place(x=40, y=self.canvas_height - 40)

		btn = tk.Button(temperatureGraph, text="+", fg="red", width=1, height = 1,  font=("Arial Bold", 20), command=self.onZoomIn)
		btn.place(x=80, y=self.canvas_height - 40)

		programSelectFrame = tk.Frame(self, bg="black", width=windowWidth*(.95),height=100)
		programSelectFrame.pack_propagate(False)
		programSelectFrame.grid(column=0, columnspan=2, row = 2, pady=2,padx=2, sticky="n")

		separator = ttk.Separator(programSelectFrame, orient='vertical')
		separator.pack(side=LEFT, fill="y", padx=10, pady=0)

		for x in self.programs:
			btn = tk.Button(programSelectFrame, text=x, fg="red", width=12, height = 3, command=partial(self.onProgramClick, x))
			btn.pack(side=LEFT)
			separator = ttk.Separator(programSelectFrame, orient='vertical' )
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
	def onZoomOut(self):
		if (self.zoomlevel<1):
			self.zoomlevel = self.zoomlevel * 2
		else:
			self.zoomlevel += 1 #self.zoomlevel + 1
		print ("zoom out ", self.zoomlevel)
		self.temparrayStartDraw = 0
		self.drawTemperatureGraph()
		pass
	def onZoomIn(self):
		if (self.zoomlevel > 1.5):
			self.zoomlevel -= 1
		else:
			self.zoomlevel = self.zoomlevel / 2
		print ("zoom in ", self.zoomlevel)
		self.temparrayStartDraw = 0
		self.drawTemperatureGraph()
	def onZoomReset(self):
		self.zoomlevel = 1
		self.drawTemperatureGraph()


	def onProgramClick(self, program):
		print("click program: ", program)
		
		#self.buttonClickStop()

		for x in self.programs:
			if x == program:
				self.programs[x]["button"].configure(background = "green")	
			else:
				self.programs[x]["button"].configure(background = "white")

		#delete contents of activeprogramframe
		for b in self.programbuttons:
			self.programbuttons[b].destroy()

		self.usetemp = tk.IntVar()
		program = self.programs[program]
		self.program = program
		framewidth = windowWidth*(.95-.27)
		
		if (program["type"] == "manual"):

			style = Style()
 
			style.configure('TButton', font =
            				   ('calibri', 20, 'bold'),
                    			borderwidth = '4',
                    			foreground = "white",
                    			background = "red")

			but =  tk.Button(self.activeProgramFrame,  width=7, height=1, text="ON", command=self.buttonClickOn, font=("Arial Bold", 25))
			but.place(x=10, y=30)
			self.programbuttons['turnOn'] = but # tk.Button(self.activeProgramFrame, width=25, height=3, text="ON", fg="red", command=self.buttonClickOn)
				

			but = tk.Button(self.activeProgramFrame, width=7, height=1, text="OFF", command=self.buttonClickOff, font=("Arial Bold", 25))
			but.place(x=10, y=100)
			self.programbuttons['turnOff'] = but #pack(side=TOP, anchor=NW)
			
			##self.programbuttons['turnOff'] = tk.Button(self.activeProgramFrame, width=25, height=3, text="OFF", fg="red", command=self.buttonClickOff)
			#self.programbuttons['turnOff'].pack(side=TOP, anchor=NW)
			
			# auto button
			c1 = tk.Button(self.activeProgramFrame, text='AUTO', width=6, fg="white", bg="#888888", activebackground = "#999999", height = 1, command=self.checkbox, font=("Arial Bold", 30))
			c1.place(x=framewidth*.45 + 10, y=30)
			self.programbuttons['check'] = c1

			# plus button
			btn = tk.Button(self.activeProgramFrame, width=2, height=1, text="-", font=("Arial Bold", 25), command=self.changeTemperatureDown)
			btn.place(x=framewidth*.40,y=100)
			self.programbuttons["minus"] = btn
			#separator = ttk.Separator(self.activeProgramFrame, orient='vertical')
			#separator.pack(side=RIGHT, fill="y", padx=10, pady=0)
			#self.programbuttons["sepa"] = separator

			lbl = tk.Label(self.activeProgramFrame, text=self.config["manualtemperature"], fg="white", bg="black", anchor="center", justify="center", font=("Arial Bold", 30))
			lbl.place(x=framewidth*.45 + 60,y=100)
			
			self.programbuttons["tlabel"] = lbl

			#separator = ttk.Separator(self.activeProgramFrame, orient='vertical')
			#separator.pack(side=RIGHT, fill="y", padx=10, pady=0)
			#self.programbuttons["sepb"] = separator

			btn = tk.Button(self.activeProgramFrame, width=2, height=1, text="+", font=("Arial Bold", 25), command=self.changeTemperatureUp)
			btn.place(x=framewidth*.45 + 170,y=100)
			self.programbuttons["plus"] = btn
			self.oven.trackTemperature = 0
		elif (program["type"]=="graph"):
			self.oven.trackTemperature = 0

			but =  tk.Button(self.activeProgramFrame, width=20, height=3, text="RUN", fg="red", command=self.buttonClickStart)
			but.place(x=10, y=30)
			self.programbuttons['start'] = but # tk.Button(self.activeProgramFrame, width=25, height=3, text="ON", fg="red", command=self.buttonClickOn)
			self.programRunning = 0
			but =  tk.Button(self.activeProgramFrame, width=20, height=3, text="STOP", fg="red", command=self.buttonClickStop)
			but.place(x=10, y=100)
			but.place_forget()
			self.programbuttons['stop'] = but # tk.Button(self.activeProgramFrame, width=25, height=3, text="ON", fg="red", command=self.buttonClickOn)

			## max temperature
			maxtemp = 0
			maxhours = 0
			flex = 0
			for g in self.program["graph"]:
				if (g["temperature"] > maxtemp):
					maxtemp = g["temperature"]
				maxhours = g["time"]
				try:
					if (g["mustreach"]):
						flex = 1
				except Exception as e:
					print ("nothing")
				
				

			lbl = tk.Label(self.activeProgramFrame, text="Max temp: "+ str(maxtemp), fg="white", bg="black", anchor="center", justify="center", font=("Arial Bold", 25))
			lbl.place(x=225,y=30)
			self.programbuttons['l1'] = lbl
			txt = "Duration " + str(maxhours) + " hours"
			if (flex):
				txt = txt + " (flex)"
			lbl = tk.Label(self.activeProgramFrame, text=txt, fg="white", bg="black", anchor="center", justify="center", font=("Arial Bold", 16))
			lbl.place(x=225,y=70)
			self.programbuttons['l2'] = lbl
			lbl = tk.Label(self.activeProgramFrame, text="", fg="white", bg="black", anchor="center", justify="center", font=("Arial Bold", 16))
			lbl.place(x=225,y=92)
			self.programbuttons['runtime'] = lbl

			but =  tk.Button(self.activeProgramFrame, width=2, height=2, text="<<", fg="black", command=self.buttonClickTimeBackBig)
			but.place(x=300, y=92)
			but.place_forget()
			self.programbuttons['backbig'] = but # tk.Button(self.activeProgramFrame, width=25, height=3, text="ON", fg="red", command=self.buttonClickOn)
			but =  tk.Button(self.activeProgramFrame, width=2, height=2, text="<", fg="black", command=self.buttonClickTimeBack)
			but.place(x=350, y=92)
			but.place_forget()
			self.programbuttons['back'] = but # tk.Button(self.activeProgramFrame, width=25, height=3, text="ON", fg="red", command=self.buttonClickOn)

			but =  tk.Button(self.activeProgramFrame, width=2, height=2, text=">", fg="black", command=self.buttonClickTimeForward)
			but.place(x=400, y=92)
			but.place_forget()
			self.programbuttons['forward'] = but # tk.Button(self.activeProgramFrame, width=25, height=3, text="ON", fg="red", command=self.buttonClickOn)
			but =  tk.Button(self.activeProgramFrame, width=2, height=2, text=">>", fg="black", command=self.buttonClickTimeForwardBig)
			but.place(x=450, y=92)
			but.place_forget()
			self.programbuttons['forwardbig'] = but # tk.Button(self.activeProgramFrame, width=25, height=3, text="ON", fg="red", command=self.buttonClickOn)

			
			lbl = tk.Label(self.activeProgramFrame, text="", fg="white", bg="black", anchor="center", justify="center", font=("Arial Bold", 12))
			lbl.place(x=225,y=130)
			self.programbuttons['targ'] = lbl

			
			try:
				tmp = self.program["initialized"]
			except Exception as e:
				#self.program["initialized"]
				print("Initialize program", self.program)
				for p in self.program["graph"]:

					p["targettime"] = p["time"]
					mustreach = 0
					try:
						mustreach = p["mustreach"]
						#print("mustrie")
					except Exception as e:
						mustreach = 0
						#p["mustreach"] = 0
						
					print("init", p)
				self.program["initialized"] = 1

			#prevtemp = self.oven.temperature
			prevtemp = 0
			for p in self.program["graph"]:
				p["targettime"] = p["time"]
				if p["temperature"]>prevtemp:
					p["rise"] = 1
				else:
					p["rise"] = 0
				prevtemp = p["temperature"]
				p["encountered"] = 0

		self.drawTemperatureGraph()

	def buttonClickTimeForwardBig(self):
		self.programstarttime -= 60 * 30
		self.drawTemperatureGraph()

	def buttonClickTimeBackBig(self):
		self.programstarttime += 60 * 30
		if (self.programstarttime > time.time()):
			self.programstarttime = time.time()
		self.drawTemperatureGraph()
	def buttonClickTimeForward(self):
		self.programstarttime -= 60 * 5
		self.drawTemperatureGraph()

	def buttonClickTimeBack(self):
		self.programstarttime += 60 * 5
		if (self.programstarttime > time.time()):
			self.programstarttime = time.time()
		self.drawTemperatureGraph()


	def checkbox(self):
		if (self.usetemp.get() == 0):
			self.usetemp.set(1)
			
		else:
			self.usetemp.set(0)
			
		
		print("check", self.usetemp.get())
		if (self.usetemp.get()):
			print("setit")
			self.programbuttons['check'].configure(bg = "red", activebackground= "#ff3333")
			self.programbuttons['turnOn'].configure(state = DISABLED)
			self.programbuttons['turnOff'].configure(state = DISABLED)
		else:
			print("clear")
			self.programbuttons['check'].configure(bg = "#888888",  activebackground= "#999999")
			self.oven.cool()
			self.programbuttons['turnOn'].configure(state = NORMAL)
			self.programbuttons['turnOff'].configure(state = NORMAL)

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
		
		self.programbuttons['backbig'].place(x=350, y=102)
		self.programbuttons['back'].place(x=400, y=102)
		
		self.programbuttons['forward'].place(x=450, y=102)
		self.programbuttons['forwardbig'].place(x=500, y=102)
		

		

	def buttonClickStop(self):
		self.programRunning = 0
		self.programbuttons['stop'].place_forget()
		self.programbuttons['start'].config(state= NORMAL)
		self.oven.cool()
		self.programbuttons['targ'].configure(text = "")
		self.programbuttons['runtime'].configure(text = "")

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
					timesec = t["targettime"] * 60 * 60 
					if (timesec < nowtime): # now has passed the timesec time
						prevtime = timesec
						prevtemp = t["temperature"]
						if t["encountered"] == 0:
							#print("encountered ", t)
							# we encountered this point just now. Are we allowed>
							offsettime = 0
							try:
								if ( t['mustreach'] ): #t["mustreach"]) :# hasattr(t, 'mustreach')) :# and t["mustreach"]):
									print("mustreach ", t["mustreach"])
									if t["rise"] and self.oven.temperature<t["temperature"]:
										offsettime = 1
									elif not t["rise"] and self.oven.temperature>t["temperature"]:
										offsettime = 1
							except Exception as e:
								pass

							if offsettime:
								#print("do offset!")
								foundme = 0
								self.mustreahtemperature = t["temperature"]
								for off in self.program["graph"]:

									if (off == t):
										foundme = 1
									
									if (foundme):
										#print("set ", off["targettime"])
										off["targettime"] = float(off["targettime"]) + 1.0/60 #// move 1 minute ahead
										#print("after ", off["targettime"])
							else:
								t["encountered"]=1
								self.mustreahtemperature = 0

					else:

						nowfactor = (nowtime - prevtime) / (timesec - prevtime)
						targettemperature = prevtemp + (t["temperature"] - prevtemp) * nowfactor
						break
				if (self.mustreahtemperature):
					targettemperature = self.mustreahtemperature
				self.oven.trackTemperature = 1
				self.oven.targettemperature = targettemperature
				self.programbuttons['targ'].configure(text = "Target: " + '{0:.1f}'.format(targettemperature))
				h = int(nowtime/60/60)
				m = int((nowtime -  (h * 60 * 60))/60)
				s = int(nowtime - (h * 60 * 60 + m * 60))

				self.programbuttons['runtime'].configure(text = str(h) + ":" + str(m) + ":" + str(s))
			else:
				self.oven.trackTemperature = 0


		self.oven.update()
		
		
		if (self.oven.closed and not self.wasclosed):
			self.temperatureLabel.config(bg="black")
		elif (not self.oven.closed and self.wasclosed):
			self.temperatureLabel.config(bg="blue")

		self.wasclosed = self.oven.closed

		#if (self.oven.closed): 
			
			
		if (self.oven.heating and not self.washeating):
			self.temperatureLabel.config(bg="red")

		elif (not self.oven.heating and self.washeating): 
			self.temperatureLabel.config(bg="black")
		
		self.washeating = self.oven.heating

		#if (self.oven.thermocoupleOK and not  self.wasthermocoupleOK):
		#	self.ovenWarning.pack_forget()
		#	self.wasthermocoupleOK = 1
		#	print("NOT OK")
		#elif (not self.oven.thermocoupleOK and self.wasthermocoupleOK):
		#	self.ovenWarning.pack()
		#	self.wasthermocoupleOK = 0
		#	print("OK")

		if (not self.oven.thermocoupleOK):
			if (self.showWarningTick == 0):
				self.ovenWarning.pack()
				self.temperatureLabel.config(fg="blue")

			self.showWarningTick = 3

		if (self.showWarningTick > 0):
			self.showWarningTick = self.showWarningTick - 1
			if (self.showWarningTick == 0):
				self.ovenWarning.pack_forget()
				self.temperatureLabel.config(fg="white")

		self.logTemperature(self.oven.temperature, self.oven.cputemperature, self.oven.heating)
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
root.geometry('1024x700')
if not platform == "darwin":
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