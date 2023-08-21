# How to use GUI
1. Open file app.py in ARDUINO/app
2. Press Ctrl+F5 to start GUI app
3. Set the desired parameters or load them from profile
4. Press 'compile' to flush Arduino
5. Press 'start' to start reading Arduino output and display it
6. 'stop' button disables reading from Arduino, the board keeps working and sending info
7. 'clear' button clears the data file

# Functions (prefer using GUI)
<pre>
ard_compile    # Compile and upload the sketch into Arduino  
ard_read       # Read and save to file in append mode  
ard_read_clear # Read and save to file, delete old data  
ard_plot       # Run python script and show plot in real-time 
ard_update_me  # Pull new code from git, update fish. Make sure internet connection is on 
</pre>

# Notes
If there are strange issues and you suspect timer corruption, use change ENABLE_TIMER to 0 in sketch.ino

# Setup
## Hardware setup
1. Substrate
Thermal module: 2 - 6. 2 - GND, 3 - 5V, 4 - SCK, 5 - CS, 6 - SO
Relay: 22 - control pin (+), 23 - GND
2. Source
Thermal module: 8 - 12. 8 - GND, 9 - 5V, 10 - SCK, 11 - CS, 12 - SO
Relay: 24 - control pin (+), 25 - GND

## One time software setup, run both:
./Arduino/env/setup_env.sh
omf reload

## If there are any issue with the shell, run:
rm -rf ~/.config/fish/ && cd ~/Arduino/env && ./install_fish.sh env_noenv.fish && omf reload
