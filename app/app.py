import os, signal, subprocess, pickle, numpy as np, tkinter as tk
import time, matplotlib.animation as mpl_animation
from tkinter import messagebox
from typing import List, Dict
from datetime import datetime
from collections import defaultdict
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from file_manager import FileParser,FileManager
from process_manager import ProcessManager

# ========== Main application class ==========

class Application(tk.Tk):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ========== User parameters ==========
        self.substate_default = ['460', '15', '0.02', '0.40']
        self.source_default   = ['460', '15', '0.02', '0.40']

        # Global variables
        self.output_file_path = 'out.txt'
        self.header_file_path = 'sketch/parameters.h'

        # Initialize attributes
        self.process_holder = [None]
        self.control_buttons: Dict[str, tk.Button] = {}
        self.parameters_entries: Dict[str, Dict[str, tk.Entry]] = {'Substrate': {}, 'Source': {}, 'Additional': {}}
        self.temperature_interval_label: tk.Label = None
        self.source_temperature_median_label: tk.Label = None
        self.substrate_temperature_median_label: tk.Label = None

        # Configure the window
        self.geometry("1600x900")
        self.title("Hohol production")

        # Set up the graph
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.update_graph(None)

        # Set up the canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Set up animation
        self.ani = mpl_animation.FuncAnimation(self.fig, self.update_graph, interval=500)

        # Set up the bottom frame
        bottom_frame = tk.Frame(self, height=100)
        bottom_frame.pack(side=tk.BOTTOM, pady=10)

        # Set up GUI components
        self.setup_gui(bottom_frame)    



    def setup_gui(self, parent):
        button_properties = [
            ['Status', self.status_button_callback],
            ['Start', self.start_button_callback],
            ['Stop', self.stop_button_callback],
            ['Compile', self.compile_button_callback],
            ['Clear', self.clear_button_callback]]

        i: int = 0
        for button_property in button_properties:
            b = tk.Button(parent, command=button_property[1], text=button_property[0])
            b.grid(row=i, column=0, rowspan=1, padx=10, pady=10)
            self.control_buttons[button_property[0]] = b
            i += 1
        
        self.update_periodically()

        # Labels and default values for the substrate and source entries
        self.labels = ['Temperature', 'TempOffset', 'KP', 'KD']

        # Substrate entries
        tk.Label(parent, text='Substrate').grid(row=0, column=1, padx=10, pady=10)
        for i in range(4):
            e = tk.Entry(parent)
            e.insert(0, self.substate_default[i])
            e.grid(row=i+1, column=1)
            self.parameters_entries['Substrate'][self.labels[i]] = e

        # Source entries
        tk.Label(parent, text='Source').grid(row=0, column=4, padx=10, pady=10)
        for i in range(4):
            tk.Label(parent, text=self.labels[i]).grid(row=i+1, column=3, padx=10, pady=10)
            e = tk.Entry(parent)
            e.insert(0, self.source_default[i])
            e.grid(row=i+1, column=4, padx=10, pady=10)
            self.parameters_entries['Source'][self.labels[i]] = e

        # Additional entries in the 3rd column
        # Additional entries
        additional_labels = ['Name', 'Timer', 'Interval temp', ]
        additional_defaults = [self.source_default[0], '', '30']
        for i, label in enumerate(additional_labels):
            tk.Label(parent, text=label).grid(row=i+1, column=5, padx=10, pady=10)
            e = tk.Entry(parent)
            e.grid(row=i+1, column=6)
            e.insert(0, additional_defaults[i])
            self.parameters_entries['Additional'][label] = e

        # Temperature of sublimation label
        tk.Label(parent, text='Time of sublimation').grid(row=1, column=7, padx=10, pady=10)
        self.temperature_interval_label = tk.Label(parent, text='None')
        self.temperature_interval_label.grid(row=1, column=8)

        # Median temperature label
        tk.Label(parent, text='Median temperature').grid(row=2, column=7, padx=10, pady=10)
        self.source_temperature_median_label = tk.Label(parent, text='')
        self.source_temperature_median_label.grid(row=2, column=8)

        tk.Label(parent, text='Median temperature').grid(row=3, column=7, padx=10, pady=10)
        self.substrate_temperature_median_label = tk.Label(parent, text='')
        self.substrate_temperature_median_label.grid(row=3, column=8)

        FileManager.load_data(self.parameters_entries, "data/current.pkl")

        # Save/Load buttons
        for i in range(5):
            filename = f"data/{i}.pkl"
            save_button = tk.Button(parent, text=f"Save {i+1}", command=lambda fn=filename: FileManager.save_data(self.parameters_entries, fn))
            save_button.grid(row=i+1, column=10, padx=10, pady=10)
            load_button = tk.Button(parent, text=f"Load {i+1}", command=lambda fn=filename: FileManager.load_data(self.parameters_entries, fn))
            load_button.grid(row=i+1, column=11, padx=10, pady=10)


        



    # ========== Callbacks ==========

    def status_button_callback(self):
        None

    def start_button_callback(self):
        try:
            ProcessManager.start_process()
        except Exception as e:
                messagebox.showerror(title=None, message="Gabella, \"{}\"".format(e))

    def stop_button_callback(self):
        ProcessManager.stop_process()
        
    def update_periodically(self):
        if ProcessManager.is_process_running():
            self.control_buttons['Status'].configure(bg="green")
        else:
            self.control_buttons['Status'].configure(bg="red")
        self.after(50, self.update_periodically)

    def compile_button_callback(self):
        try:
            self.stop_button_callback()
            ProcessManager.compile_flush_arduino(self.header_file_path, self.parameters_entries, self.labels)

        except Exception as e:
                messagebox.showerror(title=None, message="Gabella, \"{}\"".format(e))

    def clear_button_callback(self):
        print("Clearing file")
        FileManager.clear_file(self.output_file_path)

    def update_graph(self, i):
        if len(self.parameters_entries['Substrate']) > 0:
            FileManager.save_data(self.parameters_entries, "data/current.pkl")

        # print('Update graph')

        def find_temperature_interval(temp_values, X):
            left_boundary_index = None
            right_boundary_index = None
            for i, value in enumerate(temp_values):
                if left_boundary_index is None and value > X:
                    left_boundary_index = i
                elif left_boundary_index is not None and value >= X:
                    right_boundary_index = i
            return [left_boundary_index, right_boundary_index] if left_boundary_index is not None and right_boundary_index is not None else None

        reader = FileParser(self.output_file_path).read_file()

        self.ax.clear()
        self.ax.grid()
        self.ax.set_title(reader.title, fontsize=20, y=1.04)
        self.ax.set_xlabel('Time, min', fontsize=20)
        self.ax.set_ylabel('Temperature, C', fontsize=20)

        if reader.max_time_value < 5:
            self.ax.set_xlim(0, 5)

        self.ax.scatter(reader.time_values, reader.control1_values, s=3, color='b')
        self.ax.scatter(reader.time_values, reader.control2_values, s=3, color='r')
        self.ax.scatter(reader.time_values, reader.temp1_values, label='Substrate', s=3, color='b')
        self.ax.scatter(reader.time_values, reader.temp2_values, label='Source', s=3, color='r')
        self.ax.legend()

        temperature_interval = None
        try:
            temperature_interval = find_temperature_interval(reader.temp2_values, 
                float(self.parameters_entries['Additional']['Interval temp'].get()))
        except:
            print('Failed to compute interval')
        
        if temperature_interval is not None:
            self.ax.axvline(x=reader.time_values[temperature_interval[0]], color='g', linestyle='--', label='Interval Start')
            self.ax.axvline(x=reader.time_values[temperature_interval[1]], color='m', linestyle='--', label='Interval Finish')
            self.ax.legend()

            if self.temperature_interval_label is not None:
                interval_sec = temperature_interval[1] - temperature_interval[0]
                text = f'{interval_sec // 60}m {interval_sec % 60}s'
                self.temperature_interval_label.config(text=text)

            if self.source_temperature_median_label is not None:
                interval_values = reader.temp2_values[temperature_interval[0]:temperature_interval[1]]
                median_value = np.median(interval_values)
                deviation_value = np.std(interval_values)
                text = f'{median_value:.2f}°C\\{deviation_value:.2f}°C'
                self.source_temperature_median_label.config(text=text)

            if self.substrate_temperature_median_label is not None:
                interval_values = reader.temp1_values[temperature_interval[0]:temperature_interval[1]]
                median_value = np.median(interval_values)
                deviation_value = np.std(interval_values)
                text = f'{median_value:.2f}°C\\{deviation_value:.2f}°C'
                self.substrate_temperature_median_label.config(text=text)
        else:
            if self.temperature_interval_label is not None:
                self.temperature_interval_label.config(text='None')
            if self.source_temperature_median_label is not None:
                self.source_temperature_median_label.config(text='None')
            if self.substrate_temperature_median_label is not None:
                self.substrate_temperature_median_label.config(text='None')

        self.fig.canvas.draw()

# ========== Class that parses file ==========


app = Application()
app.mainloop()


# FileManager
# Parsing
# Writing header
# Saving/Loading saves

# Process manager

# Callbacks