import sys
import math
import tkinter as tk
from tkinter.font import *

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master  
        self.pack()
        self.create_widgets()

        # Only run if we're on Windows.
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1) # Fixes blurry font.

        # Squad mortar range card with TOF.
        # (range, mils, TOF)
        self.range_card = ((50, 1579, 22.6),
                           (100, 1558, 22.7),
                           (150, 1538, 22.7),
                           (200, 1517, 22.6),
                           (250, 1496, 22.6),
                           (300, 1475, 22.6),
                           (350, 1453, 22.5),
                           (400, 1431, 22.5),
                           (450, 1409, 22.4),
                           (500, 1387, 0),
                           (550, 1364, 0),
                           (600, 1341, 0),
                           (650, 1317, 0),
                           (700, 1292, 0),
                           (750, 1267, 0),
                           (800, 1240, 0),
                           (850, 1212, 0),
                           (900, 1183, 0),
                           (950, 1152, 0),
                           (1000, 1118, 0),
                           (1050, 1081, 0),
                           (1100, 1039, 0),
                           (1150, 988, 0),
                           (1200, 918, 17.9),
                           (1250, 800, 16.2))

        self.min_range = 50
        self.max_range = 1250

    def grid_to_vec(self, grid):
        x = 0
        y = 0
        grid = grid.split("-")
        if len(grid) < 2 :
            print("Error!")
            exit(-1)

        if not grid[0][0].isalpha():
            exit(-1)

        if not grid[0][1:].isdigit():
            exit(-1)

        if not grid[1].isdigit():
            exit(-1)

        if not grid[2].isdigit():
            exit(-1)


        d = 300

        for i in range(len(grid)):

            # Grid zone designators.
            if i == 0:
                x = (ord(grid[0][0].lower())-65)*300
                y = (int(grid[0][1:])-1)*-300
                continue

            d /= 3

            if grid[i] in ("4", "5", "6"):
                y -= d

            if grid[i] in ("1", "2", "3"):
                y -= 2*d

            if grid[i] in ("2", "5", "8"):
                x += d

            if grid[i] in ("3", "6", "9"):
                x += 2*d

        return (x, y)

    def get_rn(self, pos1, pos2):
        rn = math.dist(pos1, pos2)
        rn = round(rn)

        self.rn1["state"] = "normal"
        self.rn1.delete(0, tk.END)
        self.rn1.insert(0, rn)
        self.rn1["state"] = "disabled"
        return rn

    def get_az(self, pos1, pos2):
        az = math.atan2(pos2[0]-pos1[0], pos2[1]-pos1[1])
        az = math.degrees(az)
        if az < 0:
            az += 360
        az = round(az)

        self.az1["state"] = "normal"
        self.az1.delete(0, tk.END)
        self.az1.insert(0, az)
        self.az1["state"] = "disabled"
        return az

    def get_el(self, pos1, pos2, rn):
        el = 0
        if self.min_range <= rn <= self.max_range:
            # Try and find exact elevation.
            for i in self.range_card:
                if rn == i[0]:
                    el = i[1]
                    continue

            # Interpolate
            if not el:
                for i in range(len(self.range_card)):
                    if self.range_card[i][0] < rn < self.range_card[i][0]+50:
                        e = (self.range_card[i+1][1] - self.range_card[i][1])/50
                        r = abs(self.range_card[i][0] - rn)
                        el = round(self.range_card[i][1]+e*r)
                        continue
                
        else:
            el = "----"


        self.el1["state"] = "normal"
        self.el1.delete(0, tk.END)
        self.el1.insert(0, el)
        self.el1["state"] = "disabled"
        return el

    def get_tof(self, pos1, pos2, rn):
        tof = 0

        if self.min_range <= rn <= self.max_range:
            # Try and find exact elevation.
            for i in self.range_card:
                if rn == i[0]:
                    tof = i[2]
                    continue

            # Interpolate
            if not tof:
                for i in range(len(self.range_card)):
                    if self.range_card[i][0] < rn < self.range_card[i][0]+50:
                        t = (self.range_card[i+1][2] - self.range_card[i][2])/50
                        r = abs(self.range_card[i][0] - rn)
                        tof = round(self.range_card[i][2]+t*r)
                        continue
                
        else:
            tof = "----"


        self.tof1["state"] = "normal"
        self.tof1.delete(0, tk.END)
        self.tof1.insert(0, tof)
        self.tof1["state"] = "disabled"

        return tof


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

        gun = "{}-{}-{}-{}-{}".format(gg1, gg2, gg3, gg4, gg5)
        tgt = "{}-{}-{}-{}-{}".format(tg1, tg2, tg3, tg4, tg5)

        #cords
        pos1 = self.grid_to_vec(gun)
        pos2 = self.grid_to_vec(tgt)

        # Get the distance of the target from the gun.
        rn = self.get_rn(pos1, pos2)

        # Get the azimuth of the target in degrees.
        self.get_az(pos1, pos2)

        # Get the elevation in mils.
        self.get_el(pos1, pos2, rn)

        # Get the TOF in seconds.
        self.get_tof(pos1, pos2, rn)

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
