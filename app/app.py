from tkinter import *
from tkinter import filedialog
from tkinter import ttk

from multiprocessing import Process
import requests as req
import json
from os.path import basename
import time
from datetime import datetime as dt

from app.parser import read_file


def update(file, race_id):
    try:
        data = read_file(file, race_id)
        if not len(data):
            return True
        # res = req.post(
        #     "https://kilometrezero.org/rs/data/create_results.php",
        #     data=json.dumps(data),
        # )  # PRO
        res = req.post(
            "http://kilometrezero.local/rs/data/create_results.php",
            data=json.dumps(data),
        )  # DEV
        # res = req.post(
        #     "https://kilometrezero.org/working/rs/data/create_results.php",
        #     data=json.dumps(data),
        # )  # PRE
        return True
    except ValueError as value_error:
        print(value_error)
        print("source json file can't be parsed")
        return False
    except UnicodeError as unicode_error:
        print(unicode_error)
        print("source json file can't be parsed")
        return False
    except FileNotFoundError as fnf_error:
        print(fnf_error)
        print("File not found")
        return False
    except req.exceptions.RequestException as e:
        print("[Connection Error]: trying to connect again")
        return True
    except Exception as exc:
        print("[Unhandled error raised] ", exc)
        return False


def run_sync(file, race_id):
    while True:
        success = update(file, race_id)

        if not success:
            print("not success, why?")
            break

        time.sleep(30)


class Application:
    def __init__(self):
        self.root = Tk()
        self.root.title("KM0 - WebSync")

        mainframe = Frame(self.root)
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)
        mainframe.pack(pady=20, padx=20)

        ttk.Style().configure(
            "black/green.TButton", foreground="black", background="green"
        )

        ttk.Style().configure("black/red.TButton", foreground="black", background="red")

        self.file_label = ttk.Label(mainframe, text="no file selected")

        # FILE CHOSER
        self.file = None

        self.file_label.grid(row=1, column=1)

        ttk.Button(mainframe, text="Chose file", command=self.chose_file).grid(
            row=2, column=1
        )

        # RACE CHOSER
        self.race = None
        self.races = self.get_races()

        self.race_var = StringVar(self.root)
        races = [race["name"] for race in self.races]
        self.race_var.set(races[0])
        self.race_var.trace("w", self.on_races_store_changed)

        popupMenu = OptionMenu(mainframe, self.race_var, *races)
        popupMenu.grid(row=3, column=1)

        # RUN BUTTON
        self.running = False
        self.run_button = ttk.Button(
            mainframe,
            text="RUN",
            width=12,
            command=self.on_run,
            state=DISABLED,
            style="black/green.TButton",
        )

        self.run_button.grid(row=4, column=1)

        self.sync = False

    def chose_file(self, *args, **kwargs):
        self.file = filedialog.askopenfilename(
            initialdir="/",
            title="Select file",
            filetypes=(
                ("json files", "*.json"),
                ("html files", "*.html"),
                ("text files", "*.txt"),
                ("all files", "*"),
            ),
        )

        if self.file:
            self.file_label["text"] = basename(self.file)
            self.check_conditions()

    def check_conditions(self):
        if self.race and self.file:
            self.run_button.config(state=NORMAL)
        else:
            self.run_button.config(state=DISABLED)

    def get_races(self):
        # r = req.get("https://kilometrezero.org/rs/data/races.php?all=true")  # PRO
        r = req.get("http://kilometrezero.local/rs/data/races.php?all=true")  # DEV
        # r = req.get("https://kilometrezero.org/working/rs/data/races.php?all=true") # PRE
        return sorted(
            json.loads(r.text),
            key=lambda race: dt.fromtimestamp(int(int(race["date"]) / 1000)),
            reverse=True,
        )

    def on_races_store_changed(self, *args):
        race_name = self.race_var.get()
        self.race = [race for race in self.races if race["name"] == race_name][0]["id"]
        self.check_conditions()

    def on_run(self):
        if self.running:
            self.run_button.config(text="RUN", style="black/green.TButton")
            self.running = False
            self.sync.terminate()
        else:
            self.run_button.config(text="STOP", style="black/red.TButton")
            self.running = True
            self.sync = Process(
                target=run_sync,
                args=(
                    self.file,
                    self.race,
                ),
            )
            self.sync.start()

    def start(self):
        self.root.mainloop()
