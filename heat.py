#!/usr/bin/env python3

# Display UTC.
# started with https://docs.python.org/3.4/library/tkinter.html#module-tkinter

import tkinter as tk
import time
import sys
import RPi.GPIO as GPIO
from tkinter.ttk import Separator, Style

from max31855 import MAX31855, MAX31855Error

windowWidth = 100
windowHeight = 100

def current_iso8601():
	"""Get current date and time in ISO8601"""
	# https://en.wikipedia.org/wiki/ISO_8601
	# https://xkcd.com/1179/
	return time.time()
	# return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

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


		self.turnOn = tk.Button(activeProgramFrame, width=25, height=2, text="ON", fg="red", command=self.buttonClickOn).pack()
		#self.turnOn.grid(column=0, row = 0)
		#sep = tk.Separator(activeProgramFrame,orient='horizontal')

		self.turnOff = tk.Button(activeProgramFrame, width=25, height=2, text="OFF", fg="red", command=self.buttonClickOff).pack()
		#self.turnOff.grid(column=0, row = 1)


		temperatureGraph = tk.Frame(self, bg="black", width=windowWidth*.94,height=270)
		temperatureGraph.pack_propagate(False)
		
		temperatureGraph.grid(column=0, columnspan=2, row = 1, pady=5,padx=10, sticky="n")


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
		try:
			tc = self.thermocouple.get()
		except MAX31855Error as e:
			tc = "Error: "+ e.value
			#running = False

		print("tc: {} and rj: {}".format(tc, rj))
		
		self.temperatureLabel.configure(text='{0:.1f}'.format(tc)) 
		self.cpuTemperatureLabel.configure(text='{0:.1f}'.format(rj)) 
		#self.temperatureLabel['text'] = tc
		#self.cpuTemperatureLabel['text'] = rj

		onoff = 0	
		if int(time.time() ) % 2 == 0:
			onoff = 1

		# GPIO.output(4,  onoff)
		# schedule timer to call myself after 1 second
		self.after(1000, self.onUpdate)


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