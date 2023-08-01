import os, subprocess

from file_manager import FileManager

class ProcessManager:
    @staticmethod
    def start_process():
        print("Starting background process")
        
        # 1. Add nessesary rights
        command = "sudo chmod a+rw /dev/ttyACM0"
        return_value: int = os.system(command)
        if return_value != 0:
            raise ValueError("Failed to execute \"{}\", return code = {}".format(command, return_value))
        
        # 2. Start background process reading the device
        #command = "cat -v /dev/ttyACM0 | tee -a ~/Arduino/data/data.txt"
        command = ["bash", "-c", "cat -v /dev/ttyACM0 | tee -a ~/Arduino/data/data.txt &"]
        subprocess.Popen(command)

        # 3. Check if the process is running
        if not ProcessManager.is_process_running():
            raise ValueError("Process is not running")
            
        

    @staticmethod
    def stop_process():
        print("Stopping background process")
        try:
            output = subprocess.check_output(f"pkill -f \"[cat] -v /dev/ttyACM0\"", shell=True)
        except:
            print('Failed to kill process')

    @staticmethod
    def is_process_running():
        try:
            output = subprocess.check_output(f"pgrep -f \"[cat] -v /dev/ttyACM0\"", shell=True)
            if output.strip():
                return True
        except Exception as e:
            return False
        return False
    
    @staticmethod
    def compile_flush_arduino(header_file_path, parameters_entries):
        # 1. Update header file with new parameters
        FileManager.write_to_header(header_file_path, parameters_entries)

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
