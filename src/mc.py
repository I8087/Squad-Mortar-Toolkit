import sys
import math
import socket
import pickle
import tkinter as tk
from tkinter import ttk
from tkinter.font import *


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master  
        self.pack()
        self.create_widgets()

        self.FLAGS = {"GUN": b"AA",
                      "TGT": b"BB",
                      "EOM": b"CC"}

        self.fdc = None

        self.set_status = ""
        self.set_eom = ""

        # Only run if we're on Windows.
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1) # Fixes blurry font.

    def connect(self):
        # Open up a socket.
        self.fdc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.after(1000, self.update)


    def update(self):
        print("Updating!")
        data = {"NAME": self.id1.get(),
                "GRID": self.grid1.get(),
                "AMMO": self.ammo.get(),
                "STATUS": self.status1.get(),
                "CAPABLE": self.mission.get(),
                "MISSION": self.tgt_id.get()}

        if not self.id1.get():
            pass

        if not self.grid1.get():
            data["GRID"] = "N/A"

        if not self.ammo.get():
            data["AMMO"] = "N/A"

        if not self.status1.get():
            data["STATUS"] = "OUT OF ACTION"

        if not self.mission.get() or self.tgt_id.get():
            data["CAPABLE"] = "NO"


        self.fdc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.fdc.connect((self.fdc_ip.get(), int(self.fdc_port.get())))


        # SEND DATA TO THE FDC.
        if self.set_eom:
            self.fdc.sendall(self.FLAGS["EOM"]+pickle.dumps({"ID": self.set_eom,
                                                             "GUN": data["NAME"],
                                                             "STATUS": "EOM"}))
            self.set_eom = ""

        elif self.set_status:
            self.fdc.sendall(self.FLAGS["TGT"]+pickle.dumps({"ID": data["MISSION"],
                                                          "GUN": data["NAME"],
                                                          "STATUS": self.set_status}))
            self.set_status = ""

        else:
            self.fdc.sendall(self.FLAGS["GUN"]+pickle.dumps(data))


        # RECEIVE DATA FROM THE FDC.
        try:
            self.fdc.settimeout(4)
            data = self.fdc.recv(2048)
        except:
            data = None



        if not data:
            pass

        elif data[:2] == self.FLAGS["EOM"]:
            print("EOM!")
            data = pickle.loads(data[2:])

            self.set_eom = data["ID"]

            if data["ID"] == self.tgt_id.get():
                self.eom()



        elif data[:2] == self.FLAGS["TGT"]:
            data = pickle.loads(data[2:])
            print(data)

            if not self.tgt_id.get():
                self.process(data)
                self.set_status = "RECEIVED"

        else:
            print(data)

        self.fdc.shutdown(1)
        self.fdc.close()


        # Threading problem. Needs to be time took since last update + 5,
        # otherwise they can back up and freeze the system.
        self.after(3000, self.update)


    def eom(self):
        self.tgt_id["state"] = "normal"
        self.tgt_id.delete(0, tk.END)
        self.tgt_id["state"] = "disabled"

        self.moc["state"] = "normal"
        self.moc.delete(0, tk.END)
        self.moc["state"] = "disabled"

        self.shell["state"] = "normal"
        self.shell.delete(0, tk.END)
        self.shell["state"] = "disabled"

        self.rnds["state"] = "normal"
        self.rnds.delete(0, tk.END)
        self.rnds["state"] = "disabled"

        self.rn["state"] = "normal"
        self.rn.delete(0, tk.END)
        self.rn["state"] = "disabled"

        self.az["state"] = "normal"
        self.az.delete(0, tk.END)
        self.az["state"] = "disabled"

        self.el["state"] = "normal"
        self.el.delete(0, tk.END)
        self.el["state"] = "disabled"

        self.set_status = ""

    def process(self, msn):
        self.tgt_id["state"] = "normal"
        self.tgt_id.delete(0, tk.END)
        self.tgt_id.insert(0, msn["ID"])
        self.tgt_id["state"] = "disabled"

        self.moc["state"] = "normal"
        self.moc.delete(0, tk.END)
        self.moc.insert(0, msn["MOC"])
        self.moc["state"] = "disabled"

        self.shell["state"] = "normal"
        self.shell.delete(0, tk.END)
        self.shell.insert(0, msn["SHELL"])
        self.shell["state"] = "disabled"

        self.rnds["state"] = "normal"
        self.rnds.delete(0, tk.END)
        self.rnds.insert(0, msn["ROUNDS"])
        self.rnds["state"] = "disabled"

        self.rn["state"] = "normal"
        self.rn.delete(0, tk.END)
        self.rn.insert(0, msn["RANGE"])
        self.rn["state"] = "disabled"

        self.az["state"] = "normal"
        self.az.delete(0, tk.END)
        self.az.insert(0, msn["AZIMUTH"])
        self.az["state"] = "disabled"

        self.el["state"] = "normal"
        self.el.delete(0, tk.END)
        self.el.insert(0, msn["ELEVATION"])
        self.el["state"] = "disabled"

        self.set_status = "RECEIVED"

    def do_shot(self):
        self.set_status = "SHOT"

    def do_complete(self):
        self.set_status = "COMPLETE"

    def create_widgets(self):
        # Configure the font.
        font = Font(family="system", size=12)


        # UNIT ID
        self.lb1 = tk.Label(self, text="Unit ID: ", font=font)
        self.lb1.grid(row=0, column=0)
        self.id1 = tk.Entry(self, width=20, font=font)
        self.id1.grid(row=0, column=1)

        # UNIT GRID
        self.lb2 = tk.Label(self, text="GRID: ", font=font)
        self.lb2.grid(row=1, column=0)
        self.grid1 = tk.Entry(self, width=20, font=font)
        self.grid1.grid(row=1, column=1)

        # AMMO COUNT
        self.lb3 = tk.Label(self, text="AMMO: ", font=font)
        self.lb3.grid(row=2, column=0)
        self.ammo = tk.Entry(self, width=20, font=font)
        self.ammo.grid(row=2, column=1)

        # UNIT STATUS
        self.lb4 = tk.Label(self, text="STATUS: ", font=font)
        self.lb4.grid(row=3, column=0)
        self.status1 = ttk.Combobox(self, state="readonly", width=20, font=font, values=("OUT OF ACTION",
                                                                              "MOVING",
                                                                              "EMPLACING",
                                                                              "EMPLACED"))
        self.status1.grid(row=3, column=1)


        # CAN THE UNIT PROCESS MISSIONS?
        self.lb5 = tk.Label(self, text="MISSION CAPABLE: ", font=font)
        self.lb5.grid(row=4, column=0)
        self.mission = ttk.Combobox(self, state="readonly", font=font, values=("YES",
                                                                              "NO"))
        self.mission.grid(row=4, column=1)


        # FDC IP
        self.lb6 = tk.Label(self, text="FDC IP: ", font=font)
        self.lb6.grid(row=5, column=0)
        self.fdc_ip = tk.Entry(self, width=20, font=font)
        self.fdc_ip.grid(row=5, column=1)

        # FDC PORT
        self.lb6 = tk.Label(self, text="FDC PORT: ", font=font)
        self.lb6.grid(row=6, column=0)
        self.fdc_port = tk.Entry(self, width=20, font=font)
        self.fdc_port.grid(row=6, column=1)


        # TARGET ID
        self.lb6 = tk.Label(self, text="TARGET ID: ", font=font)
        self.lb6.grid(row=0, column=8)
        self.tgt_id = tk.Entry(self, width=10, state="readonly", font=font)
        self.tgt_id.grid(row=0, column=9)


        # METHOD OF CONTROL
        self.lb6 = tk.Label(self, text="MOC: ", font=font)
        self.lb6.grid(row=1, column=8)
        self.moc = tk.Entry(self, width=10, state="readonly", font=font)
        self.moc.grid(row=1, column=9)

        # SHELL TYPE
        self.lb6 = tk.Label(self, text="SHELL: ", font=font)
        self.lb6.grid(row=2, column=8)
        self.shell = tk.Entry(self, width=10, state="readonly", font=font)
        self.shell.grid(row=2, column=9)

        # NUMBER OF ROUNDS
        self.lb7 = tk.Label(self, text="ROUNDS: ", font=font)
        self.lb7.grid(row=3, column=8)
        self.rnds = tk.Entry(self, width=10, state="readonly", font=font)
        self.rnds.grid(row=3, column=9)

        # RANGE IN METERS
        self.lb8 = tk.Label(self, text="RANGE: ", font=font)
        self.lb8.grid(row=4, column=8)
        self.rn = tk.Entry(self, width=10, state="readonly", font=font)
        self.rn.grid(row=4, column=9)

        # AZIMUTH IN DEGREES CARDINAL.
        self.lb9 = tk.Label(self, text="AZIMUTH: ", fg="blue", font=font)
        self.lb9.grid(row=5, column=8)
        self.az = tk.Entry(self, width=10, fg="blue", state="disable", font=font)
        self.az.grid(row=5, column=9)

        # TUBE ELEVATION IN MILS.
        self.lb10 = tk.Label(self, text="ELEVATION: ", fg="red", font=font)
        self.lb10.grid(row=6, column=8)
        self.el = tk.Entry(self, width=10, state="disable", fg="red", font=font)
        self.el.grid(row=6, column=9)

        self.cnt = tk.Button(self, text="CONNECT",
                              command=self.connect, font=font)
        self.cnt.grid(row=8, column=6)

        self.shot1 = tk.Button(self, text="SHOT",
                              command=self.do_shot, font=font)
        self.shot1.grid(row=8, column=7, padx=2, pady=10)

        self.shot2 = tk.Button(self, text="COMPLETE",
                                command=self.do_complete, font=font)
        self.shot2.grid(row=8, column=8, padx=2, pady=10)

        self.quit = tk.Button(self, text="QUIT",
                              command=self.master.destroy, font=font)
        self.quit.grid(row=8, column=10, padx=2, pady=10)


root = tk.Tk()
app = Application(master=root)
app.master.title("Squad Mortar Toolkit - Mortar Calculator Software")
app.mainloop()
