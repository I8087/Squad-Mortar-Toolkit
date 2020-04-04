import sys
import math
import tkinter as tk
from tkinter import *
from tkinter.font import *
import keyboard

from smt_lib import *

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()

        keyboard.add_hotkey("ctrl+left alt", self.onCall)

        self.centered = BooleanVar()
        
        self.create_widgets()

        # Only run if we're on Windows.
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1) # Fixes blurry font.

    def calc(self):

        # Get gun grid.
        gg1 = self.gg1.get()
        gg2 = self.gg2.get()
        gg3 = self.gg3.get()
        gg4 = self.gg4.get()
        gg5 = self.gg5.get()

        # gg1 required.

        if not gg2:
            gg2 = "7"

        if not gg3:
            gg3 = "7"

        if not gg4:
            gg4 = "7"

        if not gg5:
            gg5 = "7"

        # Get tgt grid.
        tg1 = self.tg1.get()
        tg2 = self.tg2.get()
        tg3 = self.tg3.get()
        tg4 = self.tg4.get()
        tg5 = self.tg5.get()

        # tg1 required.

        if not tg2:
            tg2 = "7"

        if not tg3:
            tg3 = "7"

        if not tg4:
            tg4 = "7"

        if not tg5:
            tg5 = "7"

        # Format the grids.
        gun = "{}-{}-{}-{}-{}".format(gg1, gg2, gg3, gg4, gg5)
        tgt = "{}-{}-{}-{}-{}".format(tg1, tg2, tg3, tg4, tg5)

        # Calculate the firing data.
        try:
            rn, az, el, tof = calc_data(gun, tgt, center=self.centered.get())
        except OutOfRangeError as e:
            rn = get_rn(gun, tgt, center=self.centered)
            az = get_az(gun, tgt, center=self.centered)
            el = "- - - -"
            tof = "- - - -"

        self.rn1["state"] = "normal"
        self.rn1.delete(0, tk.END)
        self.rn1.insert(0, rn)
        self.rn1["state"] = "disabled"

        self.az1["state"] = "normal"
        self.az1.delete(0, tk.END)
        self.az1.insert(0, az)
        self.az1["state"] = "disabled"

        self.el1["state"] = "normal"
        self.el1.delete(0, tk.END)
        self.el1.insert(0, el)
        self.el1["state"] = "disabled"

        self.tof1["state"] = "normal"
        self.tof1.delete(0, tk.END)
        self.tof1.insert(0, tof)
        self.tof1["state"] = "disabled"

    def onCall(self):
        #print(root.state())
        
        #if root.state() == "withdrawn":
        self.master.update()
        self.master.deiconify()
        self.master.attributes('-topmost', True)
        #else:
        #    self.master.withdraw()
        #   self.master.update()

    def create_widgets(self):
        # Configure the font.
        font = Font(family="system", size=12)

        
        self.lb1 = tk.Label(self, text="Gun Grid: ", font=font)
        self.lb1.grid(row=0, column=0)
        self.gg1 = tk.Entry(self, width=3, font=font)
        self.gg1.grid(row=0, column=1)
        self.lb2 = tk.Label(self, text=" - ", font=font)
        self.lb2.grid(row=0, column=2)
        self.gg2 = tk.Entry(self, width=1, font=font)
        self.gg2.grid(row=0, column=3)
        self.lb3 = tk.Label(self, text=" - ", font=font)
        self.lb3.grid(row=0, column=4)
        self.gg3 = tk.Entry(self, width=1, font=font)
        self.gg3.grid(row=0, column=5)
        self.lb5 = tk.Label(self, text=" - ", font=font)
        self.lb5.grid(row=0, column=6)
        self.gg4 = tk.Entry(self, width=1, font=font)
        self.gg4.grid(row=0, column=7)
        self.lb6 = tk.Label(self, text=" - ", font=font)
        self.lb6.grid(row=0, column=8)
        self.gg5 = tk.Entry(self, width=1, font=font)
        self.gg5.grid(row=0, column=9)

        self.lb7 = tk.Label(self, text="Target Grid: ", font=font)
        self.lb7.grid(row=1, column=0)
        self.tg1 = tk.Entry(self, width=3, font=font)
        self.tg1.grid(row=1, column=1)
        self.lb8 = tk.Label(self, text=" - ", font=font)
        self.lb8.grid(row=1, column=2)
        self.tg2 = tk.Entry(self, width=1, font=font)
        self.tg2.grid(row=1, column=3)
        self.lb9 = tk.Label(self, text=" - ", font=font)
        self.lb9.grid(row=1, column=4)
        self.tg3 = tk.Entry(self, width=1, font=font)
        self.tg3.grid(row=1, column=5)
        self.lb10 = tk.Label(self, text=" - ", font=font)
        self.lb10.grid(row=1, column=6)
        self.tg4 = tk.Entry(self, width=1, font=font)
        self.tg4.grid(row=1, column=7)
        self.lb11 = tk.Label(self, text=" - ", font=font)
        self.lb11.grid(row=1, column=8)
        self.tg5 = tk.Entry(self, width=1, font=font)
        self.tg5.grid(row=1, column=9)

        self.centerbox = Checkbutton(self, text="CENTER GRID", variable=self.centered,
                                     onvalue=True, offvalue=False)
        self.centerbox.grid(row=3, column=0)

        self.lb12 = tk.Label(self, text="RANGE: ", font=font)
        self.lb12.grid(row=0, column=11)
        self.rn1 = tk.Entry(self, width=10, state="readonly", font=font)
        self.rn1.grid(row=0, column=12)

        self.lb13 = tk.Label(self, text="TOF: ", font=font)
        self.lb13.grid(row=1, column=11)
        self.tof1 = tk.Entry(self, width=10, state="readonly", font=font)
        self.tof1.grid(row=1, column=12)

        self.lb14 = tk.Label(self, text="Azimuth: ", fg="blue", font=font)
        self.lb14.grid(row=2, column=11)
        self.az1 = tk.Entry(self, width=10, state="disable", font=font)
        self.az1.grid(row=2, column=12)

        self.lb15 = tk.Label(self, text="Elevation: ", fg="red", font=font)
        self.lb15.grid(row=3, column=11)
        self.el1 = tk.Entry(self, width=10, state="disable", font=font)
        self.el1.grid(row=3, column=12)

        self.quit = tk.Button(self, text="QUIT",
                              command=self.master.destroy, font=font)
        self.quit.grid(row=4, column=12)

        self.calc = tk.Button(self, text="CALC",
                              command=self.calc, font=font)
        self.calc.grid(row=4, column=11)

root = tk.Tk()
app = Application(master=root)
app.master.title("Squad Mortar Toolkit - Standalone Mortar Calculator")
app.mainloop()
