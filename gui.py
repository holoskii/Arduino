from datetime import datetime
import time
from typing import List,Dict
import tkinter as tk
from tkinter import messagebox
import matplotlib.animation as animation
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import subprocess
from functools import partial

# UI
# Status button: green/red
# start
# stop
# compile
# clear


# Keep track of sunprocess that reads serial
# Buttons clean file
# Start reading
# Compile new code and start reading

file_path = 'out.txt'

class Application(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.geometry("1600x900")

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.update_graph(None)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.ani = animation.FuncAnimation(self.fig, self.update_graph, interval=500)

        bottom_frame = tk.Frame(self, height=100)
        bottom_frame.pack(side=tk.BOTTOM, pady=10)
        
        self.setup_bottol_frame(bottom_frame)
        self.process: subprocess = None

    def update_periodically(self, process_holder):
        print('update_periodically')
        try:
            if process_holder[0] is not None and process_holder[0].poll() is None:
                self.buttons['Status'].configure(bg="green")
            else:
                self.buttons['Status'].configure(bg="red")
        except:
            print('Exception')
        self.after(500, self.update_periodically, process_holder)  # Reschedule event in 500 ms

    def status_button_callback(self, process_holder):
        None

    def compile_button_callback(self):
        print("Arduino compiling")
        return_value: int = os.system("~/Arduino/env/arduino-cli compile --fqbn arduino:avr:mega ~/Arduino/sketch --clean")
        if return_value != 0:
            messagebox.showerror(title=None, message='pizes')
    
    def start_button_callback(self, process_holder):
        print("Start button")
        command = "sleep 120"
        process_holder[0] = subprocess.Popen(command, shell=True)


    def stop_button_callback(self, process_holder):
        print("Stopping the process")
        if process_holder[0] is not None:
            process_holder[0].terminate()
        process_holder[0] = None
        

    def setup_bottol_frame(self, parent):
        # Define the command you want to execute
        command = "sleep 120"

        # Execute the command in the background
        self.process_holder = [None] # subprocess.Popen(command, shell=True)
        self.update_periodically(self.process_holder)

        # Create entries with labels and descriptions in 1st column
        labels_1st = ['Substrate1', 'Substrate2', 'Substrate3', 'Substrate4']

        tk.Label(parent, text='Substrate1').grid(row=0, column=1,padx=10,pady=10)
        for i in range(4):
            tk.Label(parent, text=labels_1st[i]).grid(row=i+1, column=0)
            tk.Entry(parent).grid(row=i+1, column=1)

        # Create entries with labels and descriptions in 2nd column
        labels_2nd = ['Source1', 'Source2', 'Source3', 'Source4']

        tk.Label(parent, text='Source').grid(row=0, column=4, padx=10, pady=10)
        for i in range(4):
            tk.Label(parent, text=labels_2nd[i]).grid(row=i+1, column=3, padx=10, pady=10)
            tk.Entry(parent).grid(row=i+1, column=4, padx=10, pady=10)

        # Create entries in 3rd column
        labels_3rd = ['Time1', 'Time1', 'Time1', 'Time1']

        for i in range(4):
            tk.Label(parent, text=labels_3rd[i]).grid(row=i+1, column=5, padx=10, pady=10)
            tk.Entry(parent).grid(row=i+1, column=6)

        self.buttons:Dict[str, tk.Button] = {}
        button_properties = [['Status', self.status_button_callback], ['Start', self.start_button_callback], ['Stop', self.stop_button_callback]]

        i: int = 0
        for button_property in button_properties:
            b = tk.Button(parent, command=partial(button_property[1], self.process_holder), text=button_property[0])
            b.grid(row=i+1, column=7, rowspan=1, padx=10, pady=10)
            self.buttons[button_property[0]]=b
            i+=1

        if self.process_holder[0] is not None and self.process_holder[0].poll() is None:
            self.buttons['Status'].configure(bg="green")
        else:
            self.buttons['Status'].configure(bg="red")

    
    def update_graph(self, i):


        reader = FileReader(file_path).read_file()

        self.ax.clear()
        self.ax.grid()
        self.ax.set_title(reader.title, fontsize = 20, y=1.04)
        self.ax.set_xlabel('Time, min', fontsize=20)
        self.ax.set_ylabel('Temperature, C', fontsize=20)
        if reader.max_time_value < 5:
            self.ax.set_xlim(0, 5)
        self.ax.scatter(reader.time_values, reader.control1_values, s=3, color = 'b')
        self.ax.scatter(reader.time_values, reader.control2_values, s=3, color = 'r')
        self.ax.scatter(reader.time_values, reader.temp1_values, label='Substrate', s=3, color = 'b')
        self.ax.scatter(reader.time_values, reader.temp2_values, label='Source',    s=3, color = 'r')
        self.ax.legend()


class FileReader:
    start_prefix: str = "START: "
    info_prefix:  str = "INFO: "

    def __init__(self, file_path: str):
        self.file_path:         str         = file_path
        self.last_point_time:   int         = 0
        self.time_values:       List[float] = []
        self.temp1_values:      List[float] = []
        self.control1_values:   List[float] = []
        self.temp2_values:      List[float] = []
        self.control2_values:   List[float] = []
        self.max_time_value:    float       = 0
        self.arduino_param_str: str         = 'No data'
        self.title:             str         = ''

    def read_file(self):
        start = time.time()
        with open(self.file_path, 'r') as file:
            for line in file:
                if line.startswith(self.start_prefix):
                    self.arduino_param_str = line[len(self.start_prefix):-1]
                    continue

                if not line.startswith(self.info_prefix):
                    continue    
                
                numbers: List[float] = []
                for part in line[len(self.info_prefix):].split(','):
                    numbers.append(float(part))

                if len(numbers) != 5:
                    print(f"Unexpected number count \"{len(numbers)}\" in info line \"{line}\"")
                    continue

                self.time_values    .append(self.last_point_time / 60)
                self.temp1_values   .append(numbers[1])
                self.control1_values.append(numbers[2])
                self.temp2_values   .append(numbers[3])
                self.control2_values.append(numbers[4])
                self.max_time_value = max(self.max_time_value, self.last_point_time / 60 )
                self.last_point_time += 1
        
        end = time.time()
        # print("File parsing time = {:.0f} ms".format(1000 * (end - start)))
    
        temp1 = self.temp1_values[-1] if len(self.temp1_values) > 0 else 0
        temp2 = self.temp2_values[-1] if len(self.temp2_values) > 0 else 0
        temps_str = "Substrate Blue {:3.01f}°C, Source Red: {:3.01f}°C".format(temp1, temp2)
        date_time_now = datetime.now()
        d = date_time_now.strftime("%H:%M:%S, %d %b, %Y")
        self.title = f'{self.arduino_param_str}\n{temps_str}; {d}'
        return self


app = Application()
app.mainloop()
