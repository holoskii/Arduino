# How to use
1. Rapidly smash bios(F12/DEL) key to enter the BIOS
2. Choose USB flash drive and press Enter to boot from it
3. Open the sketch from VS Code, set the required parameters
4. Save the doc with Ctrl+S
5. Open terminal, split it with Ctrl+Shift+O
6. In one split run ard_compile and ard_read (or ard_read_clear)
7. In second split run ard_plot

# Functions
ard_compile    # Compile and upload the sketch into Arduino
ard_read       # Read and save to file in append mode
ard_read_clear # Read and save to file, delete old data
ard_plot       # Run python script and show plot in real-time

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
