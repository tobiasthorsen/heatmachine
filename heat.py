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


