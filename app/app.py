import numpy as np, tkinter as tk
import matplotlib.animation as mpl_animation
from tkinter import messagebox
from typing import Dict
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from file_manager import FileParser,FileManager
from process_manager import ProcessManager

class Application(tk.Tk):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Global variables
        self.data_file_path   = 'out.txt'
        self.header_file_path = 'sketch/parameters.h'

        # Initialize attributes
        self.control_buttons: Dict[str, tk.Button] = {}
        self.parameters_entries: Dict[str, Dict[str, tk.Entry]] = {'Substrate': {}, 'Source': {}, 'Additional': {}}
        self.info_labels = {}

        # Configure the window
        self.geometry("1600x900")
        self.title("Hohol production")

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.update_graph(None)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.ani = mpl_animation.FuncAnimation(self.fig, self.update_graph, interval=500)

        bottom_frame = tk.Frame(self, height=100)
        bottom_frame.pack(side=tk.BOTTOM, pady=10)

        # Set up GUI components
        self.setup_buttons_and_callbacks(bottom_frame)    
        self.setup_gui(bottom_frame)    
        for child in bottom_frame.winfo_children():
            child.grid_configure(padx=10, pady=10)

    # ========== Buttons and callbacks ==========
    def setup_buttons_and_callbacks(self, parent):
        # Callbacks
        def execute_with_error_handling(func):
            try:
                func()
            except Exception as e:
                messagebox.showerror(title=None, message="Gabella, \"{}\"".format(e))
        
        def compile_button_callback():
            def action():
                ProcessManager.stop_process()
                ProcessManager.compile_flush_arduino(
                    self.header_file_path, 
                    self.parameters_entries
                )
            execute_with_error_handling(action)

        # Linking callbacks and buttons
        button_properties = [
            ['Status', lambda: None],
            ['Start', lambda: execute_with_error_handling(ProcessManager.start_process)],
            ['Stop', lambda: ProcessManager.stop_process()],
            ['Compile', compile_button_callback],
            ['Clear', lambda: FileManager.clear_file(self.data_file_path)]
        ]

        for i, (button_text, button_callback) in enumerate(button_properties):
            b = tk.Button(parent, text=button_text, command=button_callback)
            b.grid(row=i, column=0)
            self.control_buttons[button_text] = b

        # Update color of a status button
        def status_updater(control_buttons):
            status_color = "green" if ProcessManager.is_process_running() else "red"
            control_buttons['Status'].configure(bg=status_color)
            control_buttons['Status'].after(50, lambda: status_updater(control_buttons))
        
        status_updater(self.control_buttons)

        # Save/Load buttons
        for i in range(5):
            filename = f"data/{i}.pkl"
            save_button = tk.Button(parent, text=f"Save {i+1}", command=lambda fn=filename: FileManager.save_data(self.parameters_entries, fn))
            save_button.grid(row=i, column=10)
            load_button = tk.Button(parent, text=f"Load {i+1}", command=lambda fn=filename: FileManager.load_data(self.parameters_entries, fn))
            load_button.grid(row=i, column=11)


    # ========== Labels and entries ==========
    def setup_gui(self, parent):
        def create_entry(parent, default_value, row, column):
            e = tk.Entry(parent)
            e.insert(0, default_value)
            e.grid(row=row, column=column)
            return e

        # Parameter entries
        common_labels = ['Temperature', 'TempOffset', 'KP', 'KD']
        sections = [
            {'name': 'Substrate',  'labels': common_labels,                      'defaults': ['460', '15', '0.02', '0.40'], 'column': 1},
            {'name': 'Source',     'labels': common_labels,                      'defaults': ['460', '15', '0.02', '0.40'], 'column': 3},
            {'name': 'Additional', 'labels': ['Name', 'Timer', 'Interval temp'], 'defaults': ['Mykhaylo', '30', '460'],     'column': 6},
        ]

        for section in sections:
            tk.Label(parent, text=section['name']).grid(row=0, column=section['column'])
            for i, (label, default) in enumerate(zip(section['labels'], section['defaults'])):
                if section['name'] != 'Substrate':
                    tk.Label(parent, text=label).grid(row=i+1, column=section['column'] - 1)
                self.parameters_entries[section['name']][label] = create_entry(parent, default, i+1, section['column'])


        # Informational labels
        labels_info = ['Time of sublimation', 'Median source temperature', 'Median substrate temperature']

        for row, label_info in enumerate(labels_info, start=1):
            tk.Label(parent, text=label_info).grid(row=row, column=7)
            self.info_labels[label_info] = tk.Label(parent, text='None')
            self.info_labels[label_info].grid(row=row, column=8)

        # Try to load data from the previous session
        FileManager.load_data(self.parameters_entries, "data/current.pkl", False)


    def update_graph(self, i):
        if len(self.parameters_entries['Substrate']) > 0:
            FileManager.save_data(self.parameters_entries, "data/current.pkl")

        def find_temperature_interval(temp_values, X):
            left_boundary_index = None
            right_boundary_index = None
            for i, value in enumerate(temp_values):
                if left_boundary_index is None and value > X:
                    left_boundary_index = i
                elif left_boundary_index is not None and value >= X:
                    right_boundary_index = i
            return [left_boundary_index, right_boundary_index] if left_boundary_index is not None and right_boundary_index is not None else None

        reader = FileParser(self.data_file_path).read_file()

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

            try:
                interval_sec = temperature_interval[1] - temperature_interval[0]
                text = f'{interval_sec // 60}m {interval_sec % 60}s'
                self.info_labels['Time of sublimation'].config(text=text)

                for info_label, data_source in {'Median substrate temperature': reader.temp1_values, 'Median source temperature': reader.temp2_values}.items():
                    interval_values = data_source[temperature_interval[0]:temperature_interval[1]]
                    median_value = np.median(interval_values)
                    deviation_value = np.std(interval_values)
                    text = f'{median_value:.2f}°C\\{deviation_value:.2f}°C'
                    self.info_labels[info_label].config(text=text)
            except Exception as e:
                print('Caught exception ' + str(e))

        else:
            for label_name, label_widget in self.info_labels.items():
                if label_widget is not None:
                    label_widget.config(text='None')

        self.fig.canvas.draw()


app = Application()
app.mainloop()
