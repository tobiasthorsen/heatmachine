#!/usr/bin/env python3

# Display UTC.
# started with https://docs.python.org/3.4/library/tkinter.html#module-tkinter

import tkinter as tk
import time
import sys
import RPi.GPIO as GPIO
from tkinter.ttk import Separator, Style

from max31855 import MAX31855, MAX31855Error



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
		self.createWidgets()

	def createWidgets(self):
		"""self.now = tk.StringVar()
		self.time = tk.Label(self, font=('Helvetica', 24))
		self.time.pack(side="top")
		self.time["textvariable"] = self.now

		self.QUIT = tk.Button(self, text="QUIT", fg="red",
		                                    command=root.destroy)
		self.QUIT.pack(side="bottom")
"""
		left = tk.Frame(self, bg="black",width=100, height=100)
		#left.pack(fill="both", expand=True) # pack_propagate(False)
		left.pack_propagate(False)
		left.grid(column=0, row = 0, pady=5 ,padx=10, sticky="n")
		tk.Label(left, text="Left frame", fg="white", bg="black", anchor="center", justify="center").pack()


		right= tk.Frame(self, bg="black", width=100,height=100)
		right.pack_propagate(False)
		
		right.grid(column=2, row = 0, pady=5,padx=10, sticky="n")
		tk.Label(right, text="Right frame", fg="white", bg="black").pack()
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
		#self.onUpdate()
		#self.now.set(current_iso8601())

	def onUpdate(self):
		# update displayed time
		# self.now.set(current_iso8601())

		onoff = 0	
		if int(time.time() ) % 2 == 0:
			onoff = 1

		# GPIO.output(4,  onoff)
		# schedule timer to call myself after 1 second
		self.after(10, self.onUpdate)


root = tk.Tk()
root.geometry('640x480')
root.attributes('-fullscreen', True)
root.update()
#root.resizable(height = None, width = None)

print(root.winfo_height())
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