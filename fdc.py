import sys
import socket
import pickle
import math
import tkinter as tk
from tkinter import ttk
from tkinter.font import *

class Application(tk.Frame):

    # Initialization function for the program.
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()


        # Socket placeholder.
        self.serversocket = None

        # Dictionary of guns connected to the fdc.
        self.guns = {}

        # Dictionary of active missions.
        self.mission_list = {}

        # List of individual active missions that will be sent down to each gun.
        self.mission_queue = []

        # List of individual end of missions that will be sent down to each gun.
        self.eom_queue = []

        # Flags for sending pickle data between different programs within toolchain.
        self.FLAGS = {"GUN": b"AA",
                      "TGT": b"BB",
                      "EOM": b"CC"}

        # Only run if we're on Windows.
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1) # Fixes blurry font.


        # Squad mortar range card.
        # (range, mils, TOF)
        # NOTE: TOF is based on the average time of flight for three HE rounds.
        #       Any zeros means that no test have been conducted for that range.
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
        """Takes a Squad grid and converts it into a vector point."""

        x = 0
        y = 0

        grid = grid.split("-")
        if len(grid) < 1 :
            print("Error!")
            exit(-1)

        d = 300

        for i in range(len(grid)):

            # Grid zone designators.
            if i == 0:
                x = (ord(grid[0][0].upper())-65)*300
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

    def vec_to_grid(self, cords):
        """Takes a vector point and converts it into a Squad grid."""

        grid = ""

        # For a more accurate conversion, round to the thousands place.
        x = round(cords[0], 3)
        y = abs(round(cords[1], 3))

        d = 300

        grid += chr(65+int(x//d))
        x -= (x//d)*d

        grid += "{:.0f}".format(y//d+1)
        y -= (y//d)*d

        while x > 1 or y > 1:
            d /= 3
            g = 55

            while x >= d:
                    x -= d
                    g += 1

            while y >= d:
                    y -= d
                    g -= 3


            grid += "-{}".format(chr(g))

        return grid

    def get_rn(self, gun, tgt, offset=False):
        """Gets the range between the gun and target."""

        if offset:
            tgt_grid = tgt
        else:
            tgt_grid = self.mission_list[tgt]["GRID"]

        rn = math.dist(self.grid_to_vec(self.guns[gun]["GRID"]),
                       self.grid_to_vec(tgt_grid))

        return round(rn)

    def get_az(self, gun, tgt, offset=False):
        """Gets the azimuth between the gun and target."""

        g = self.grid_to_vec(self.guns[gun]["GRID"])

        if offset:
            t = self.grid_to_vec(tgt)
        else:
            t = self.grid_to_vec(self.mission_list[tgt]["GRID"])

        az = math.atan2(t[0]-g[0], t[1]-g[1])
        az = math.degrees(az)
        if az < 0:
            az += 360

        return round(az)

    def get_el(self, gun, tgt, rn):
        """Gets the elevation of the gun based on the range."""

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

        return el

    # Direction in cardinal degrees, range in meters, and vector
    # coordinates of current.
    def aimpoint_offset(self, di, rn, grid):
        """Calculates a new location based on direction and distance."""

        cords = self.grid_to_vec(grid)

        if not 0 <= di <= 360:
            print("aimpoint_offset: Invalid direction!")
            return

        if 0 <= di <= 90:
            x_neg = False
            y_neg = False
            x = (di/45)
            y = 2 - x
        elif 91 <= di <= 179:
            di -= 90
            x_neg = False
            y_neg = True
            y = (di/45)
            x = 2 - y
        elif 180 <= di <= 270:
            di -= 180
            x_neg = True
            y_neg = True
            x = (di/45)
            y = 2 - x
        elif 271 <= di <= 360:
            di -= 270
            x_neg = True
            y_neg = False
            y = (di/45)
            x = 2 - y

        x, y = math.sqrt(rn**2/2*x), math.sqrt(rn**2/2*y)

        if round(rn) != round(math.sqrt(x**2+y**2)):
            print("critical aimpoint_offset error!")
            return

        if x_neg:
            x *= -1

        if y_neg:
            y *= -1

        return self.vec_to_grid((cords[0]+x, cords[1]+y))

    def correction_offset(self, grid, di, dev_cor="0", rn_cor="0"):
        """Calculates grid corrections and adjustments based on the observer's azimuth."""

        # Try to do a deviation correction.
        if dev_cor != "0":
            temp_di = di
            if dev_cor[0] == "R":
                temp_di += 90
            elif dev_cor[0] == "L":
                temp_di += 270
            else:
                print("ERROR!")
                return

            # Make sure we stay within an actual azimuth.
            if temp_di >= 360:
                    temp_di -= 360

            print(temp_di)
            grid = self.aimpoint_offset(temp_di, int(dev_cor[1:]), grid)

        # Try to do a range correction.
        if rn_cor != "0":
            temp_di = di
            if rn_cor[0] == "+":
                pass
            elif rn_cor[0] == "-":
                temp_di += 180
            else:
                print("ERROR!")
                return

            # Make sure we stay within an actual azimuth.
            if temp_di >= 360:
                    temp_di -= 360

            print(temp_di)
            grid = self.aimpoint_offset(temp_di, int(rn_cor[1:]), grid)

        return grid

    # Calc the gun data.
    def calc(self, gun, tgt, offset):
        """Calculates a gun's firing data."""

        rn = 0

        # Calculate for a sheath.
        if offset != -1:
            new_tgt = self.aimpoint_offset(offset, 10, self.mission_list[tgt]["GRID"])
            rn = self.get_rn(gun, new_tgt, offset=True)
            az = self.get_az(gun, new_tgt, offset=True)

        if not self.min_range <= rn <= self.max_range:
            rn = self.get_rn(gun, tgt)
            az = self.get_az(gun, tgt)

        # Only the range matters in elevation.
        el = self.get_el(gun, tgt, rn)

        return (rn, az, el)

    def update(self):
        """The program's main thread for multitasking, including target clean up, gui updates, and networking."""

        try:
            (client, address) = self.serversocket.accept()
        except:
            client = None

        if client:
            with client:
                newdata = None
                data = bytes()
                print("Connection from {}:{}".format(*address))
                while True:
                    try:
                        newdata = client.recv(2048)
                    except:
                        newdata = None
                    if not newdata: break
                    data += newdata


                # Deal with test messages.
                if not data:
                    pass


                elif data[:2] == self.FLAGS["GUN"]:

                    # Update gun list.
                    data = pickle.loads(data[2:])
                    self.guns[data["NAME"]] = data


                    sentdata = False

                    for i in range(len(self.eom_queue)):
                        if self.eom_queue[i]["GUN"] == data["NAME"]:
                            client.sendall(self.FLAGS["EOM"]+pickle.dumps(self.eom_queue[i]))
                            sentdata = True
                            break

                    if not sentdata:
                        for i in range(len(self.mission_queue)):
                            print(self.mission_queue[i]["GUN"])
                            print(data["NAME"])
                            if self.mission_queue[i]["GUN"] == data["NAME"]:
                                print(self.mission_queue[i])
                                client.sendall(self.FLAGS["TGT"]+pickle.dumps(self.mission_queue[i]))
                                break

                elif data[:2] == self.FLAGS["TGT"]:
                    data = pickle.loads(data[2:])

                    if data["STATUS"] == "RECEIVED":
                        for i in range(len(self.mission_queue)):
                            if self.mission_queue[i]["GUN"] == data["GUN"] and self.mission_queue[i]["ID"] == data["ID"]:
                                self.mission_list[data["ID"]]["GUN_STATUS"][data["GUN"]] = data["STATUS"]
                                del self.mission_queue[i]
                                break
                    else:
                        for i in self.mission_list:
                            if data["GUN"] in self.mission_list[i]["GUN_LIST"] and self.mission_list[i]["ID"] == data["ID"]:
                                self.mission_list[data["ID"]]["GUN_STATUS"][data["GUN"]] = data["STATUS"]



                elif data[:2] == self.FLAGS["EOM"]:
                    data = pickle.loads(data[2:])
                    print("EOM STUFF!")

                    for i in range(len(self.eom_queue)):
                        print(self.eom_queue)
                        if self.eom_queue[i]["GUN"] == data["GUN"] and self.eom_queue[i]["ID"] == data["ID"]:
                            del self.eom_queue[i]
                            break

                else:
                    print("Unknown data message!")

        self.update_guns()
        self.update_status()
        self.process_missions()
        self.update_mission_list()

        self.after(1000, self.update)

    def host(self):
        """Activated when the host button is clicked.
        This function sets up a socket server for communicating with the guns.
        """

        if not self.port_setting.get():
            self.port_setting.delete(0, tk.END)
            self.port_setting.insert(0, "844")

        h = self.ip_setting.get()
        p = int(self.port_setting.get())

        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.setblocking(0)
        self.serversocket.bind((h, p))
        self.serversocket.listen(10)

        # Disable the appropriate fields.
        self.host["state"] = "disabled"
        self.ip_setting["state"] = "disabled"
        self.port_setting["state"] = "disabled"

        # Check for updates every second.
        self.after(1000, self.update)

    def update_status(self):
        """Makes sure the status of each mission is accurately displayed."""

        for i in self.mission_list:
            print(self.mission_list[i]["GUN_STATUS"])
            # Don't change the status if it's in the queue.
            if self.mission_list[i]["GUN_STATUS"] == {}:
                continue

            if self.mission_list[i]["STATUS"] == "COMPLETE":
                continue

            s_sending = 0
            s_received = 0
            s_shot = 0
            s_complete = 0
            s_count = 0

            for n in self.mission_list[i]["GUN_STATUS"]:
                if self.mission_list[i]["GUN_STATUS"][n] == "SENDING":
                    s_sending += 1
                if self.mission_list[i]["GUN_STATUS"][n] == "RECEIVED":
                    s_received += 1
                if self.mission_list[i]["GUN_STATUS"][n] == "SHOT":
                    s_shot += 1
                if self.mission_list[i]["GUN_STATUS"][n] == "COMPLETE":
                    s_complete += 1

                s_count += 1

            if s_complete == s_count:
                self.mission_list[i]["STATUS"] = "COMPLETE"
            elif s_sending:
                self.mission_list[i]["STATUS"] = "SENDING"
            elif s_received == s_count:
                self.mission_list[i]["STATUS"] = "RECEIVED"
            elif s_shot:
                self.mission_list[i]["STATUS"] = "SHOT"


    def update_guns(self):
        #Update tree
        self.tree.delete(*self.tree.get_children())
        for i in self.guns:
                self.tree.insert("", "end", text=self.guns[i]["NAME"], values=(self.guns[i]["GRID"],
                                                                               self.guns[i]["AMMO"],
                                                                               self.guns[i]["STATUS"],
                                                                               self.guns[i]["CAPABLE"],
                                                                               self.guns[i]["MISSION"]))


    def process(self):
        self.mission_list[self.tgt_id.get()] = {"ID": self.tgt_id.get(),
                                                "GRID": self.tgt_grid.get(),
                                                "GUNS": self.num_guns.get(),
                                                "MOC": self.moc.get(),
                                                "SHELL": self.shell.get(),
                                                "ROUNDS": self.rnds.get(),
                                                "STATUS": "WAITING",
                                                "GUN_LIST": [],
                                                "GUN_STATUS": {}}

        for i in (self.tgt_id, self.tgt_grid, self.num_guns, self.moc,
                  self.shell, self.rnds):
            i.delete(0, tk.END)

        self.update_mission_list()



    def update_mission_list(self):
        #Update the mission list
        self.missions.delete(*self.missions.get_children())
        for i in self.mission_list:
                self.missions.insert("", "end", text=self.mission_list[i]["ID"], values=(self.mission_list[i]["GRID"],
                                                                                         self.mission_list[i]["GUNS"],
                                                                                         self.mission_list[i]["MOC"],
                                                                                         self.mission_list[i]["SHELL"],
                                                                                         self.mission_list[i]["ROUNDS"],
                                                                                         self.mission_list[i]["STATUS"]))


    # This functions finds missions in waiting and assigns guns to them.
    def process_missions(self):
        for i in self.mission_list:
            if self.mission_list[i]["STATUS"] == "WAITING":

                # Make sure the guns are mission capable.
                guns = [x for x in self.guns if self.guns[x]["CAPABLE"] == "YES"]
                guns = [x for x in guns if self.min_range <= self.get_rn(x, i) <= self.max_range]
                print("guns -> {}" % guns)

                if len(guns) >= int(self.mission_list[i]["GUNS"]):
                    self.mission_list[i]["STATUS"] = "SENDING"
                    guns = guns[:int(self.mission_list[i]["GUNS"])]
                    self.mission_list[i]["GUN_LIST"] = guns

                    # Calc a bcs sheath offset.
                    g_offset = 360/len(guns)

                    # Don't use a sheath if there's only one gun!
                    if len(guns) == 1:
                        g_offset = -1

                    for n in range(len(guns)):
                        if g_offset == -1:
                            r = self.calc(guns[n], i, -1)
                        else:
                            r = self.calc(guns[n], i, g_offset*n)

                        self.queue_mission(guns[n], i, r)
                        self.guns[guns[n]]["CAPABLE"] = "NO"
                        self.mission_list[i]["GUN_STATUS"][guns[n]] = "SENDING"
                    self.update_mission_list()
                    return

    # Ends the selected mission.
    def correct(self):
        tgt = self.tgt_id2.get()

        if not tgt:
            return

        dev_cor = self.dev_cor.get()
        rn_cor = self.rn_cor.get()

        if not dev_cor:
            dev_cor = "0"

        if not rn_cor:
            rn_cor = "0"

        self.mission_list[tgt]["GRID"] = self.correction_offset(self.mission_list[tgt]["GRID"],
                                                                int(self.dir_cor.get()),
                                                                dev_cor,
                                                                rn_cor)


        for i in self.mission_list[tgt]["GUN_LIST"]:
            self.eom_queue.append({"GUN": i,
                                   "ID": tgt})

        self.mission_list[tgt]["STATUS"] = "WAITING"
        self.mission_list[tgt]["GUN_LIST"] = []
        self.mission_list[tgt]["GUN_STATUS"] = {}

        self.dir_cor["state"] = "normal"
        self.dir_cor.delete(0, tk.END)

        self.dev_cor["state"] = "normal"
        self.dev_cor.delete(0, tk.END)

        self.rn_cor["state"] = "normal"
        self.rn_cor.delete(0, tk.END)


    # Ends the selected mission.
    def eom(self):
        tgt = self.tgt_id2.get()

        if not tgt:
            return

        for i in self.mission_list[tgt]["GUN_LIST"]:
            self.eom_queue.append({"GUN": i,
                                   "ID": tgt})

        for i in range(len(self.mission_queue)):
            if self.mission_queue[i]["ID"] == tgt:
                self.mission_queue[i] = None

        self.mission_queue = [i for i in self.mission_queue if i]

        del self.mission_list[tgt]

        self.tgt_id2["state"] = "normal"
        self.tgt_id2.delete(0, tk.END)
        self.tgt_id2["state"] = "disabled"

        self.tgt_grid2["state"] = "normal"
        self.tgt_grid2.delete(0, tk.END)
        self.tgt_grid2["state"] = "disabled"

        self.num_guns2["state"] = "normal"
        self.num_guns2.delete(0, tk.END)
        self.num_guns2["state"] = "disabled"

        self.moc2["state"] = "normal"
        self.moc2.delete(0, tk.END)
        self.moc2["state"] = "disabled"

        self.shell2["state"] = "normal"
        self.shell2.delete(0, tk.END)
        self.shell2["state"] = "disabled"

        self.rnds2["state"] = "normal"
        self.rnds2.delete(0, tk.END)
        self.rnds2["state"] = "disabled"

        # Disable corrections.
        self.dir_cor["state"] = "normal"
        self.dir_cor.delete(0, tk.END)
        self.dir_cor["state"] = "disabled"

        self.dev_cor["state"] = "normal"
        self.dev_cor.delete(0, tk.END)
        self.dev_cor["state"] = "disabled"

        self.rn_cor["state"] = "normal"
        self.rn_cor.delete(0, tk.END)
        self.rn_cor["state"] = "disabled"

        self.cor_button["state"] = "disabled"


        self.update_guns()
        self.update_status()
        self.update_mission_list()

    # Adds a mission to a queue that will be sent over network to the gun.
    def queue_mission(self, gun, tgt, data):
        self.mission_queue.append({"GUN": gun,
                                   "ID": tgt,
                                   "GRID": self.mission_list[tgt]["GRID"],
                                   "MOC": self.mission_list[tgt]["MOC"],
                                   "SHELL": self.mission_list[tgt]["SHELL"],
                                   "ROUNDS": self.mission_list[tgt]["ROUNDS"],
                                   "STATUS": self.mission_list[tgt]["STATUS"],
                                   "RANGE": data[0],
                                   "AZIMUTH":data[1],
                                   "ELEVATION": data[2]}
                                   )


    # This function is initiated when a mouse click is detected in the mission list.
    def selectItem(self, event):
        curItem = self.missions.item(self.missions.focus())
        tgt = curItem["text"]
        if not tgt:
            return

        self.tgt_id2["state"] = "normal"
        self.tgt_id2.delete(0, tk.END)
        self.tgt_id2.insert(0, self.mission_list[tgt]["ID"])
        self.tgt_id2["state"] = "disabled"

        self.tgt_grid2["state"] = "normal"
        self.tgt_grid2.delete(0, tk.END)
        self.tgt_grid2.insert(0, self.mission_list[tgt]["GRID"])
        self.tgt_grid2["state"] = "disabled"

        self.num_guns2["state"] = "normal"
        self.num_guns2.delete(0, tk.END)
        self.num_guns2.insert(0, self.mission_list[tgt]["GUNS"])
        self.num_guns2["state"] = "disabled"

        self.moc2["state"] = "normal"
        self.moc2.delete(0, tk.END)
        self.moc2.insert(0, self.mission_list[tgt]["MOC"])
        self.moc2["state"] = "disabled"

        self.shell2["state"] = "normal"
        self.shell2.delete(0, tk.END)
        self.shell2.insert(0, self.mission_list[tgt]["SHELL"])
        self.shell2["state"] = "disabled"

        self.rnds2["state"] = "normal"
        self.rnds2.delete(0, tk.END)
        self.rnds2.insert(0, self.mission_list[tgt]["ROUNDS"])
        self.rnds2["state"] = "disabled"

        # Make sure that corrections can be made.
        self.dir_cor["state"] = "normal"
        self.dev_cor["state"] = "normal"
        self.rn_cor["state"] = "normal"
        self.cor_button["state"] = "normal"



    # Builds the gui.
    def create_widgets(self):
        # Configure the font.
        font = Font(family="system", size=12)

        self.lb4 = tk.Label(self, text="FDC SETTINGS", font=font)
        self.lb4.grid(row=0, column=1)

        self.lb1 = tk.Label(self, text="UNIT ID: ", font=font)
        self.lb1.grid(row=1, column=0)
        self.unit_id = tk.Entry(self, width=20, font=font)
        self.unit_id.grid(row=1, column=1)

        self.lb1 = tk.Label(self, text="IP: ", font=font)
        self.lb1.grid(row=2, column=0)
        self.ip_setting = tk.Entry(self, width=20, font=font)
        self.ip_setting.grid(row=2, column=1)

        self.lb2 = tk.Label(self, text="Port ", font=font)
        self.lb2.grid(row=3, column=0)
        self.port_setting = tk.Entry(self, width=20, font=font)
        self.port_setting.grid(row=3, column=1)

        self.lb4 = tk.Label(self, text="MISSION GENERATOR", font=font)
        self.lb4.grid(row=0, column=3)

        self.lb2 = tk.Label(self, text="TARGET ID: ", font=font)
        self.lb2.grid(row=1, column=2)
        self.tgt_id = tk.Entry(self, width=20, font=font)
        self.tgt_id.grid(row=1, column=3)

        self.lb2 = tk.Label(self, text="TARGET GRID: ", font=font)
        self.lb2.grid(row=2, column=2)
        self.tgt_grid = tk.Entry(self, width=20, font=font)
        self.tgt_grid.grid(row=2, column=3)

        self.lb2 = tk.Label(self, text="GUNS: ", font=font)
        self.lb2.grid(row=3, column=2)
        self.num_guns = tk.Entry(self, width=20, font=font)
        self.num_guns.grid(row=3, column=3)

        self.lb4 = tk.Label(self, text="MOC: ", font=font)
        self.lb4.grid(row=4, column=2)

        self.moc = ttk.Combobox(self, state="readonly",
                                width=10, font=font,
                                values=("WR",
                                        "DNL",
                                        "AMC"))
        self.moc.grid(row=4, column=3)

        self.lb4 = tk.Label(self, text="SHELL: ", font=font)
        self.lb4.grid(row=5, column=2)
        self.shell = ttk.Combobox(self, state="readonly", width=10, font=font, values=("HE", "SMK"))
        self.shell.grid(row=5, column=3)

        self.lb2 = tk.Label(self, text="ROUNDS: ", font=font)
        self.lb2.grid(row=6, column=2)
        self.rnds = tk.Entry(self, width=20, font=font)
        self.rnds.grid(row=6, column=3)

        self.lb4 = tk.Label(self, text="SELECTED MISSION", font=font)
        self.lb4.grid(row=0, column=5)

        self.lb2 = tk.Label(self, text="TARGET ID: ", font=font)
        self.lb2.grid(row=1, column=4)
        self.tgt_id2 = tk.Entry(self, width=20, font=font, state="disabled")
        self.tgt_id2.grid(row=1, column=5)

        self.lb2 = tk.Label(self, text="TARGET GRID: ", font=font)
        self.lb2.grid(row=2, column=4)
        self.tgt_grid2 = tk.Entry(self, width=20, font=font, state="disabled")
        self.tgt_grid2.grid(row=2, column=5)

        self.lb2 = tk.Label(self, text="GUNS: ", font=font)
        self.lb2.grid(row=3, column=4)
        self.num_guns2 = tk.Entry(self, width=20, font=font, state="disabled")
        self.num_guns2.grid(row=3, column=5)

        self.lb4 = tk.Label(self, text="MOC: ", font=font)
        self.lb4.grid(row=4, column=4)
        self.moc2 = tk.Entry(self, width=20, font=font, state="disabled")
        self.moc2.grid(row=4, column=5)

        self.lb4 = tk.Label(self, text="SHELL: ", font=font)
        self.lb4.grid(row=5, column=4)
        self.shell2 = tk.Entry(self, width=20, font=font, state="disabled")
        self.shell2.grid(row=5, column=5)

        self.lb2 = tk.Label(self, text="ROUNDS: ", font=font)
        self.lb2.grid(row=6, column=4)
        self.rnds2 = tk.Entry(self, width=20, font=font, state="disabled")
        self.rnds2.grid(row=6, column=5)


        self.lb4 = tk.Label(self, text="MISSION CORRECTIONS", font=font)
        self.lb4.grid(row=0, column=7)

        self.lb2 = tk.Label(self, text="DIRECTION: ", font=font)
        self.lb2.grid(row=1, column=6)
        self.dir_cor = tk.Entry(self, width=20, font=font, state="disabled")
        self.dir_cor.grid(row=1, column=7)

        self.lb2 = tk.Label(self, text="DEVIATION: ", font=font)
        self.lb2.grid(row=2, column=6)
        self.dev_cor = tk.Entry(self, width=20, font=font, state="disabled")
        self.dev_cor.grid(row=2, column=7)

        self.lb2 = tk.Label(self, text="RANGE: ", font=font)
        self.lb2.grid(row=3, column=6)
        self.rn_cor = tk.Entry(self, width=20, font=font, state="disabled")
        self.rn_cor.grid(row=3, column=7)

        self.process = tk.Button(self, text="GENERATE",
                              command=self.process, font=font)
        self.process.grid(row=7, column=3)


        self.process = tk.Button(self, text="PROCESS",
                                 command=self.process, font=font)
        self.process.grid(row=7, column=5)

        self.cor_button = tk.Button(self, text="CORRECT",
                                    command=self.correct,
                                    font=font, state="disabled")
        self.cor_button.grid(row=7, column=7)

        self.process = tk.Button(self, text="EOM",
                              command=self.eom, font=font)
        self.process.grid(row=7, column=8)

        self.host = tk.Button(self, text="HOST",
                              command=self.host, font=font)
        self.host.grid(row=7, column=9)

        self.quit = tk.Button(self, text="QUIT",
                              command=self.master.destroy, font=font)
        self.quit.grid(row=7, column=10)

        # Create the tree view.
        self.tree = ttk.Treeview(root, columns=("GRID", "AMMO", "STATUS", "CAPABLE", "MISSION"))
        self.tree.heading("#0", text="UNIT")
        self.tree.heading("GRID", text="GRID")
        self.tree.heading("AMMO", text="AMMO")
        self.tree.heading("STATUS", text="STATUS")
        self.tree.heading("CAPABLE", text="CAPABLE")
        self.tree.heading("MISSION", text="MISSION")

        self.tree.pack(side="left")


        # Create the tree view.
        self.missions = ttk.Treeview(root, columns=("GRID", "GUNS", "MOC", "SHELL", "ROUNDS", "STATUS"))
        self.missions.heading("#0", text="Target Number")
        self.missions.heading("GRID", text="GRID")
        self.missions.heading("GUNS", text="GUNS")
        self.missions.heading("MOC", text="MOC")
        self.missions.heading("SHELL", text="SHELL")
        self.missions.heading("ROUNDS", text="ROUNDS")
        self.missions.heading("STATUS", text="STATUS")
        self.missions.column("#0", width=100)
        self.missions.column("GRID", width=100)
        self.missions.column("GUNS", width=100)
        self.missions.column("MOC", width=100)
        self.missions.column("SHELL", width=100)
        self.missions.column("ROUNDS", width=100)
        self.missions.column("STATUS", width=100)

        self.missions.bind('<ButtonRelease-1>', self.selectItem)

        self.missions.pack(side="right")

        self.after(1000, self.process_missions)


root = tk.Tk()
app = Application(master=root)
app.master.title("Squad FDC")
app.mainloop()
