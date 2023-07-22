import os, signal, subprocess, numpy as np, tkinter as tk
import time, matplotlib.animation as mpl_animation
from tkinter import messagebox
from typing import List, Dict
from datetime import datetime
from collections import defaultdict
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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
        self.parameters_entries: Dict[str, Dict[str, tk.Entry]] = defaultdict(dict)
        self.timer_entry: tk.Entry = None
        self.temperature_interval_entry: tk.Entry = None
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
        self.setup_buttons(bottom_frame)


    def setup_gui(self, parent):
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
        tk.Label(parent, text='Interval target temp').grid(row=0, column=5, padx=10, pady=10)
        e = tk.Entry(parent)
        e.grid(row=0, column=6)
        e.insert(0, self.source_default[0])
        self.temperature_interval_entry = e

        tk.Label(parent, text='Name').grid(row=1, column=5, padx=10, pady=10)
        tk.Entry(parent).grid(row=1, column=6)

        tk.Label(parent, text='Timer (in min)').grid(row=2, column=5, padx=10, pady=10)
        e = tk.Entry(parent)
        e.grid(row=2, column=6)
        e.insert(0, '30')
        self.timer_entry = e

        # Temperature of sublimation label
        tk.Label(parent, text='Time of sublimation').grid(row=3, column=5, padx=10, pady=10)
        self.temperature_interval_label = tk.Label(parent, text='None')
        self.temperature_interval_label.grid(row=3, column=6)

        # Median temperature label
        tk.Label(parent, text='Median temperature').grid(row=0, column=8, padx=10, pady=10)
        self.source_temperature_median_label = tk.Label(parent, text='')
        self.source_temperature_median_label.grid(row=0, column=9)

        tk.Label(parent, text='Median temperature').grid(row=1, column=8, padx=10, pady=10)
        self.substrate_temperature_median_label = tk.Label(parent, text='')
        self.substrate_temperature_median_label.grid(row=1, column=9)


    def write_to_header(self):
        # Get values from the Entry fields
        substrate_values = [self.parameters_entries['Substrate'][label].get() for label in self.labels]
        source_values = [self.parameters_entries['Source'][label].get() for label in self.labels]

        # Verify the values are valid floats
        for value in substrate_values + source_values + [self.timer_entry.get()]:
            try:
                float(value)
            except ValueError:
                raise ValueError("Invalid float value: {}".format(value))

        # Create the lines for the header file
        header_lines = []
        header_lines.append("/* DO NOT EDIT, AUTOGENERATED FROM gui.py */\n\n")
        header_lines.append("static constexpr int        SUBSTRATE_TEMP        = {};\n".format(substrate_values[0]))
        header_lines.append("static constexpr int        SUBSTRATE_TEMP_OFFSET = {};\n".format(substrate_values[1]))
        header_lines.append("static constexpr double     SUBSTRATE_KP          = {};\n".format(substrate_values[2]))
        header_lines.append("static constexpr double     SUBSTRATE_KD          = {};\n".format(substrate_values[3]))
        header_lines.append("\n")
        header_lines.append("static constexpr int        SOURCE_TEMP           = {};\n".format(source_values[0]))
        header_lines.append("static constexpr int        SOURCE_TEMP_OFFSET    = {};\n".format(source_values[1]))
        header_lines.append("static constexpr double     SOURCE_KP             = {};\n".format(source_values[2]))
        header_lines.append("static constexpr double     SOURCE_KD             = {};\n".format(source_values[3]))
        header_lines.append("\n")
        header_lines.append("static constexpr unsigned long DEPOSITION_TIME_MS = {};\n".format(int(self.timer_entry.get()) * 60 * 1000))

        # Write to the header file
        with open(self.header_file_path, "w") as header_file:
            header_file.writelines(header_lines)

        print("Header file has been written: \n>>>")
        with open(self.header_file_path, "r") as header_file:
            print(header_file.read())
        print("<<<")


    # ========== Callbacks ==========

    def status_button_callback(self):
        None

    def start_button_callback(self):
        try:
            print("Starting background process")
            
            # 1. Add nessesary rights
            command = "sudo chmod a+rw /dev/ttyACM0"
            return_value: int = os.system(command)
            if return_value != 0:
                raise ValueError("Failed to execute \"{}\", return code = {}".format(command, return_value))
            
            # 2. Start background process reading the device
            #command = "cat -v /dev/ttyACM0 | tee -a ~/Arduino/out.txt"
            command = ["bash", "-c", "cat -v /dev/ttyACM0 | tee -a ~/Arduino/out.txt &"]
            subprocess.Popen(command)

            # 3. Check if the process is running
            if not self.is_process_running():
                raise ValueError("Process is not running")
            
        except Exception as e:
                messagebox.showerror(title=None, message="Gabella, \"{}\"".format(e))

    def stop_button_callback(self):
        print("Stopping background process")
        try:
            output = subprocess.check_output(f"pkill -f \"[cat] -v /dev/ttyACM0\"", shell=True)
        except:
            print('Failed to kill process')

    def is_process_running(self):
        try:
            output = subprocess.check_output(f"pgrep -f \"[cat] -v /dev/ttyACM0\"", shell=True)
            if output.strip():
                return True
        except Exception as e:
            return False
        return False

    def update_periodically(self):
        if self.is_process_running():
            self.control_buttons['Status'].configure(bg="green")
        else:
            self.control_buttons['Status'].configure(bg="red")
        self.after(50, self.update_periodically)

    def compile_button_callback(self):
        try:
            self.stop_button_callback()

            # 1. Update header file with new parameters
            self.write_to_header()

            # 2. Compile the code
            print("Arduino compiling")
            return_value: int = os.system("~/Arduino/env/arduino-cli compile --fqbn arduino:avr:mega ~/Arduino/sketch --clean")
            if return_value != 0:
                raise ValueError("Failed to compile code, return code = {}".format(return_value))
            
            # 3. Add nessesary rights
            command = "sudo chmod a+rw /dev/ttyACM0"
            return_value: int = os.system(command)
            if return_value != 0:
                raise ValueError("Failed to execute \"{}\", return code = {}".format(command, return_value))

            # 4. Flush the Arduino
            print("Arduino flushing")
            return_value: int = os.system("~/Arduino/env/arduino-cli upload ~/Arduino/sketch --fqbn arduino:avr:mega --port /dev/ttyACM0 --verbose")
            if return_value != 0:
                raise ValueError("Failed to flush Arduino, return code = {}".format(return_value))

        except Exception as e:
                messagebox.showerror(title=None, message="Gabella, \"{}\"".format(e))

    def clear_button_callback(self):
        print("Clearing file")
        self.stop_button_callback()
        with open(self.output_file_path, 'w') as file:
            file.truncate(0)

    def setup_buttons(self, parent):
        button_properties = [
            ['Status', self.status_button_callback],
            ['Start', self.start_button_callback],
            ['Stop', self.stop_button_callback],
            ['Compile', self.compile_button_callback],
            ['Clear', self.clear_button_callback]]

        i: int = 0
        for button_property in button_properties:
            b = tk.Button(parent, command=button_property[1], text=button_property[0])
            b.grid(row=i, column=7, rowspan=1, padx=10, pady=10)
            self.control_buttons[button_property[0]] = b
            i += 1
        
        self.update_periodically()

    def update_graph(self, i):
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

        reader = FileReader(self.output_file_path).read_file()

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
                float(self.temperature_interval_entry.get()))
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

class FileReader:
    start_prefix: str = "START: "
    info_prefix:  str = "INFO: "

    def __init__(self, output_file_path: str):
        self.output_file_path:  str         = output_file_path
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
        with open(self.output_file_path, 'r') as file:
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
