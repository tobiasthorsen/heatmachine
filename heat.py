#!/usr/bin/env python3

# Display UTC.
# started with https://docs.python.org/3.4/library/tkinter.html#module-tkinter

import tkinter as tk
import time
import sys
import RPi.GPIO as GPIO
import json
import math
from tkinter.ttk import Separator, Style
from sys import platform
from max31855 import MAX31855, MAX31855Error
from datetime import datetime
print (platform)
windowWidth = 100
windowHeight = 100

def current_iso8601():
	"""Get current date and time in ISO8601"""
	# https://en.wikipedia.org/wiki/ISO_8601
	# https://xkcd.com/1179/
	return time.time()
	# return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

class Temperature:
  def __init__(self, tempThermo, tempInternal):
    self.tempThermo = tempThermo
    self.tempInternal = tempInternal



class Application(tk.Frame):
	def __init__(self, master=None):
		tk.Frame.__init__(self, master)
		self.pack()
		#GPIO.setmode(GPIO.BOARD)
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(4, GPIO.OUT)
		GPIO.output(4,  0)
		self.thermocouple = MAX31855(15,14,18)
		self.setupTemperatureArray()
		self.createWidgets()
		self.onUpdate() #// start updating
	
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
		if (t >= 1):
			self.temparray.append( {"time":int(time.time()), "tempThermo":_tempThermo, "tempInternal":_tempInternal} )# Temperature(tempThermo, tempInternal))
			self.lastTemperatureLogTime=time.time()
			#self.drawTemperatureGraph()

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
		hoursprev = 7
		hoursahead = 1
		timestart = nows - hoursprev * 60 * 60 - now.second
		timeend = nows + hoursahead * 60 * 60 - now.second

		tempmax = 0
		tempmin = 0

		# find tempmin and max
		for t in self.temparray:
			if (t["time"]<timestart):
				continue
			if (t["tempThermo"] > tempmax):
				tempmax = t["tempThermo"]

		tempmax+= 10
		
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
				if (dx < 4):
					self.temperatureCanvas.create_line(prevx,prevy,x,y, fill="yellow")
				prevx = x
				prevy = y

			#print(t["time"])
		
	
	def saveTempArray(self):
		#print json.dumps(self.temparray)
		tempfile = open('./temperatures.json', 'w')
		json.dump(self.temparray, tempfile)

	def buttonClickOn(self):
		GPIO.output(4,  1)

	def buttonClickOff(self):
		GPIO.output(4,  0)

	def createWidgets(self):
		"""self.now = tk.StringVar()
		self.time = tk.Label(self, font=('Helvetica', 24))
		self.time.pack(side="top")
		self.time["textvariable"] = self.now

"""
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

		activeProgramFrame = tk.Frame(self, bg="black", width=windowWidth*.67,height=190)
		activeProgramFrame.pack_propagate(False)
		
		activeProgramFrame.grid(column=1, row = 0, pady=2,padx=2, sticky="n")
		tk.Label(activeProgramFrame, text="Actions", fg="white", bg="black").pack()


		self.turnOn = tk.Button(activeProgramFrame, width=25, height=3, text="ON", fg="red", command=self.buttonClickOn)
		self.turnOn.pack()
		#self.turnOn.grid(column=0, row = 0)
		#sep = tk.Separator(activeProgramFrame,orient='horizontal')

		self.turnOff = tk.Button(activeProgramFrame, width=25, height=3, text="OFF", fg="red", command=self.buttonClickOff)
		self.turnOff.pack()
		#self.turnOff.grid(column=0, row = 1)


		temperatureGraph = tk.Frame(self, bg="black", width=windowWidth*.95,height=270)
		temperatureGraph.pack_propagate(False)
		
		temperatureGraph.grid(column=0, columnspan=2, row = 1, pady=0,padx=0, sticky="n")

		self.canvas_width = windowWidth*.95
		self.canvas_height = 270
		self.temperatureCanvas = tk.Canvas(temperatureGraph, width=self.canvas_width, height=self.canvas_height)
		self.temperatureCanvas.pack()

		self.QUIT = tk.Button(self, text="QUIT", fg="red", command=root.destroy)
		#self.QUIT.pack(side="bottom")
		self.QUIT.grid(column = 0, row = 2,  pady=5,padx=10, sticky="n")
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
	
	
	def onUpdate(self):
		# update displayed time
		# self.now.set(current_iso8601())
		rj = self.thermocouple.get_rj()
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