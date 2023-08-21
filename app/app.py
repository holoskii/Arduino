from typing import Dict
import numpy as np
import customtkinter as ctk
import matplotlib.style as mplstyle
import matplotlib.animation as mpl_animation
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from CTkMessagebox import CTkMessagebox

from file_manager import FileParser,FileManager
from process_manager import ProcessManager
from my_timer import Timer

class Application(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        mplstyle.use('fast')
 
        # Global variables
        self.data_file_path   = 'data/data.txt'
        self.header_file_path = 'sketch/parameters.h'

        # Initialize attributes
        self.control_buttons: Dict[str, ctk.CTkButton] = {}
        self.parameters_entries: Dict[str, Dict[str, ctk.CTkEntry]] = {'Substrate': {}, 'Source': {}, 'Additional': {}, 'Savenames': {}}
        self.info_labels = {}

        # Configure the window
        self.geometry("1600x900")
        self.title("Hohol production")

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.update_graph(None)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

        self.ani = mpl_animation.FuncAnimation(self.fig, self.update_graph, interval=920)

        bottom_frame = ctk.CTkFrame(self, height=100)
        bottom_frame.pack(side=ctk.BOTTOM, pady=10)

        # Set up GUI components
        self.setup_buttons_and_callbacks(bottom_frame)
        self.setup_gui(bottom_frame)
        self.finalize_setup(bottom_frame)

    # ========== Buttons and callbacks ==========
    def setup_buttons_and_callbacks(self, parent):
        # Callbacks
        def execute_with_error_handling(func):
            print("execute_with_error_handling")
            try:
                func()
            except Exception as e:
                CTkMessagebox(title="Error", message="Gabella, \"{}\"".format(e))

        def compile_button_callback():
            print("compile_button_callback")
            def action():
                ProcessManager.stop_process()
                ProcessManager.compile_flush_arduino(
                    self.header_file_path,
                    self.parameters_entries
                )
            execute_with_error_handling(action)

        # Linking callbacks and buttons
        button_properties = [
            ['Status',  0, 0, lambda: None],
            ['Start',   1, 0, lambda: execute_with_error_handling(ProcessManager.start_process)],
            ['Stop',    2, 0, lambda: ProcessManager.stop_process()],
            ['Compile', 3, 0, lambda: compile_button_callback()],
            ['Clear',   4, 0, lambda: FileManager.clear_file(self.data_file_path)],
            ['Save',    4, 6, lambda: FileManager.save_graph_data(self.data_file_path, self.parameters_entries)]
        ]

        for i, (button_text, row, column, button_callback) in enumerate(button_properties):
            b = ctk.CTkButton(parent, text=button_text, command=button_callback)
            b.grid(row=row, column=column)
            self.control_buttons[button_text] = b

        # Save/Load buttons
        for i in range(5):
            filename = f"savefiles/{i}.pkl"
            save_name_entry = ctk.CTkEntry(parent)
            save_name_entry.grid(row=i, column=10)
            save_name_entry.insert(0, f"EmptyName#{i}")
            self.parameters_entries['Savenames'][f"{i}"] = save_name_entry

            save_button = ctk.CTkButton(parent, text=f"Save {i+1}", command=lambda fn=filename: FileManager.save_data(self.parameters_entries, fn))
            save_button.grid(row=i, column=11)
            load_button = ctk.CTkButton(parent, text=f"Load {i+1}", command=lambda fn=filename: FileManager.load_data(self.parameters_entries, fn))
            load_button.grid(row=i, column=12)


    # ========== Labels and entries ==========
    def setup_gui(self, parent):
        def create_entry(parent, default_value, row, column):
            e = ctk.CTkEntry(parent)
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
            ctk.CTkLabel(parent, text=section['name']).grid(row=0, column=section['column'])
            for i, (label, default) in enumerate(zip(section['labels'], section['defaults'])):
                if section['name'] != 'Substrate':
                    ctk.CTkLabel(parent, text=label).grid(row=i+1, column=section['column'] - 1)
                self.parameters_entries[section['name']][label] = create_entry(parent, default, i+1, section['column'])


        # Informational labels
        labels_info = ['Time of sublimation', 'Median source temperature', 'Median substrate temperature']

        for row, label_info in enumerate(labels_info, start=1):
            ctk.CTkLabel(parent, text=label_info).grid(row=row, column=7)
            self.info_labels[label_info] = ctk.CTkLabel(parent, text='None')
            self.info_labels[label_info].grid(row=row, column=8)


    def finalize_setup(self, bottom_frame):
        # Apply style for better looks
        for child in bottom_frame.winfo_children():
            child.grid_configure(padx=10, pady=10)

        # Try to load data from the previous session
        FileManager.load_data(self.parameters_entries, "savefiles/current.pkl", False, True)

        # Update color of a status button
        def status_updater(control_buttons):
            status_color = "green" if ProcessManager.is_process_running() else "red"
            control_buttons['Status'].configure(fg_color=status_color)
            control_buttons['Status'].after(100, lambda: status_updater(control_buttons))
        status_updater(self.control_buttons)

        # Update color of a status button
        def parameter_saver(self):
            if len(self.parameters_entries['Substrate']) > 0:
                FileManager.save_data(self.parameters_entries, "savefiles/current.pkl")
            self.after(1000, lambda: parameter_saver(self))
        parameter_saver(self)


    def update_graph(self, i):
        try:
            # Read new data and update graph with it
            reader = FileParser(self.data_file_path).read_file()
        except Exception as error:
            print("Exception occured during file parsing:", error)
            print("Try clearing the file")


        timer = Timer()

        self.ax.clear()

        timer.stop("Graph clear time")
        timer.start()

        self.ax.grid()
        self.ax.set_title(reader.title, fontsize=20, y=1.04)
        self.ax.set_xlabel('Time, min', fontsize=20)
        self.ax.set_ylabel('Temperature, C', fontsize=20)

        if reader.max_time_value < 5:
            self.ax.set_xlim(0, 5)

        timer.stop("Graph setup time")
        timer.start()


        self.ax.scatter(reader.time_values, reader.control1_values, s=3, color='b')
        self.ax.scatter(reader.time_values, reader.control2_values, s=3, color='r')
        self.ax.plot(reader.time_values, reader.temp1_values, label='Substrate', linewidth=3, color='b')
        self.ax.plot(reader.time_values, reader.temp2_values, label='Source', linewidth=3, color='r')

        timer.stop("Scatter time")
        timer.start()

        self.ax.legend()

        # Update labels with info
        def find_temperature_interval(temp_values, X):
            left_boundary_index = None
            right_boundary_index = None
            for i, value in enumerate(temp_values):
                if left_boundary_index is None and value > X:
                    left_boundary_index = i
                elif left_boundary_index is not None and value >= X:
                    right_boundary_index = i
            return [left_boundary_index, right_boundary_index] if left_boundary_index is not None and right_boundary_index is not None else None

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
                self.info_labels['Time of sublimation'].configure(text = text)

                for info_label, data_source in {'Median substrate temperature': reader.temp1_values, 'Median source temperature': reader.temp2_values}.items():
                    interval_values = data_source[temperature_interval[0]:temperature_interval[1]]
                    median_value = np.median(interval_values)
                    deviation_value = np.std(interval_values)
                    text = f'{median_value:.2f}°C\\{deviation_value:.2f}°C'
                    self.info_labels[info_label].configure(text = text)
            except Exception as e:
                print('Caught exception ' + str(e))

        else:
            for label_name, label_widget in self.info_labels.items():
                if label_widget is not None:
                    label_widget.configure(text = 'None')

        timer.stop("Additional plot calculations\n")
        # timer.start()
        # self.fig.canvas.draw()
        # timer.stop("Canvas draw")


app = Application()
app.mainloop()
