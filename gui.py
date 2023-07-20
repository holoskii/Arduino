from datetime import datetime
import time
from typing import List,Dict
import tkinter as tk
from tkinter import messagebox
import matplotlib.animation as animation
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from collections import defaultdict
import subprocess
from functools import partial
import numpy as np

file_path = '/home/maivas/Arduino/out.txt'

class Application(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.process_holder = [None]
        self.control_buttons:Dict[str, tk.Button] = {}
        self.parameters_entries:Dict[str, dict[str,tk.Entry]] = defaultdict(dict)
        self.temperature_interval_label:tk.Label = None
        self.temperature_median_label:tk.Label = None

        self.geometry("1600x900")
        self.title("Hohol production")

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.update_graph(None)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.ani = animation.FuncAnimation(self.fig, self.update_graph, interval=500)

        bottom_frame = tk.Frame(self, height=100)
        bottom_frame.pack(side=tk.BOTTOM, pady=10)

        self.setup_gui(bottom_frame)
        self.setup_buttons(bottom_frame)

    def setup_gui(self, parent):
        labels = ['Temperature', 'TempOffset', 'KP', 'KD']
        substate_default = ['460', '15', '0.02', '0.40']
        tk.Label(parent, text='Substrate').grid(row=0, column=1,padx=10,pady=10)
        for i in range(4):
            e = tk.Entry(parent)
            e.insert(0,substate_default[i])
            e.grid(row=i+1, column=1)
            self.parameters_entries['Substrate'][labels[i]] = e

        source_default = ['460', '15', '0.02', '0.40']
        tk.Label(parent, text='Source').grid(row=0, column=4, padx=10, pady=10)
        for i in range(4):
            tk.Label(parent, text=labels[i]).grid(row=i+1, column=3, padx=10, pady=10)
            e = tk.Entry(parent)
            e.insert(0,source_default[i])
            e.grid(row=i+1, column=4, padx=10, pady=10)
            self.parameters_entries['Source'][labels[i]] = e

        # Create entries in 3rd column
        labels_3rd = ['Name', 'Timer']
        for i in range(2):
            tk.Label(parent, text=labels_3rd[i]).grid(row=i+1, column=5, padx=10, pady=10)
            tk.Entry(parent).grid(row=i+1, column=6)

        tk.Label(parent, text='Time of sublimation').grid(row=3, column=5, padx=10, pady=10)
        self.temperature_interval_label = tk.Label(parent, text='None')
        self.temperature_interval_label.grid(row=3, column=6)

        tk.Label(parent, text='Median temperature').grid(row=4, column=5, padx=10, pady=10)
        self.temperature_median_label = tk.Label(parent, text='')
        self.temperature_median_label.grid(row=4, column=6)



    def status_button_callback(self):
        None
    
    def start_button_callback(self):
        print("Start button")
        command = "sleep 120"
        self.process_holder[0] = subprocess.Popen(command, shell=True)

    def stop_button_callback(self):
        print("Stopping the process")
        if self.process_holder[0] is not None:
            self.process_holder[0].terminate()
        self.process_holder[0] = None      

    def update_periodically(self):
        # print('update_periodically')
        if self.process_holder[0] is not None and self.process_holder[0].poll() is None:
            self.control_buttons['Status'].configure(bg="green")
        else:
            self.control_buttons['Status'].configure(bg="red")
        self.after(50, self.update_periodically)  

    def compile_button_callback(self):
        self.stop_button_callback()
        print("Arduino compiling")
        return_value: int = os.system("~/Arduino/env/arduino-cli compile --fqbn arduino:avr:mega ~/Arduino/sketch --clean")
        if return_value != 0:
            messagebox.showerror(title=None, message='pizes')

    def clear_button_callback(self):
        self.stop_button_callback()
        with open(file_path, 'w') as file:
            file.truncate(0)

    def setup_buttons(self, parent):
        button_properties = [
              ['Status', self.status_button_callback]
            , ['Start', self.start_button_callback]
            , ['Stop', self.stop_button_callback]
            , ['Compile', self.compile_button_callback]
            , ['Clear', self.clear_button_callback]]

        i: int = 0
        for button_property in button_properties:
            b = tk.Button(parent, command=button_property[1], text=button_property[0])
            b.grid(row=i, column=7, rowspan=1, padx=10, pady=10)
            self.control_buttons[button_property[0]]=b
            i+=1
        self.update_periodically()
    
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

        def find_temperature_interval(temp_values, X):
            left_boundary_index = None
            right_boundary_index = None

            for i, value in enumerate(temp_values):
                if left_boundary_index is None and value > X:
                    left_boundary_index = i
                elif left_boundary_index is not None and value >= X:
                    right_boundary_index = i

            return [left_boundary_index, right_boundary_index] if left_boundary_index is not None and right_boundary_index is not None else None
    
        temperature_interval = find_temperature_interval(reader.temp2_values, 430)
        if temperature_interval is not None:
            self.ax.axvline(x=reader.time_values[temperature_interval[0]], color='g', linestyle='--', label='Interval Start')
            self.ax.axvline(x=reader.time_values[temperature_interval[1]], color='m', linestyle='--', label='Interval Finish')
            self.ax.legend()
            if self.temperature_interval_label is not None:
                interval_sec: int = temperature_interval[1] - temperature_interval[0]
                text:str = f'{interval_sec // 60}m {interval_sec % 60}s'
                self.temperature_interval_label.config(text=text)

            if self.temperature_median_label is not None:
                interval_values = reader.temp2_values[temperature_interval[0]:temperature_interval[1]]
                median_value = np.median(interval_values)
                text = f'{median_value:.2f}°C'
                self.temperature_median_label.config(text=text)
        else:
            if self.temperature_interval_label is not None:
                self.temperature_interval_label.config(text='None')
            if self.temperature_median_label is not None:
                self.temperature_median_label.config(text='None')




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
