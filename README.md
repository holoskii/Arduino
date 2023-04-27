
### How to launch
# Compile and upload
ard_compile

# Read and save to file in append mode
ard_read

# Read and save to file, delete old data
ard_read_clear

# Show plot in real-time
ard_plot

### Pinout
1. Substrate
Thermal module: 2 - 6. 2 - GND, 3 - 5V, 4 - SCK, 5 - CS, 6 - SO
Relay: 22 - control pin (+), 23 - GND

2. Source
Thermal module: 8 - 12. 8 - GND, 9 - 5V, 10 - SCK, 11 - CS, 12 - SO
Relay: 24 - control pin (+), 25 - GND


### Design
1. Arduino side, control
Read temp 4 times, 250ms apart. Find average to avoid noise, calculate PID. Optimal values are around 0.02, 0, 0.20 

Control value will be from 0 to 1. It represents how many ms in a second the relay will be on. But avoid numbers from 0 to 0.1, and from 0.9 to 1 to avoid rapid switching


Relay
SSR-10DA
Switch time < 10ms

Temp sensor



### One time setup
sudo add-apt-repository universe
sudo apt update && sudo apt install git python3-pip fish terminator
sudo snap install code --classic
pip3 install matplotlib
git clone https://github.com/holoskii/arduino.git
rm -rf ~/.config/fish/ && cd ~/Arduino/env && ./install_fish.sh env_noenv.fish && omf reload

cd ~/Arduino/ && wget -qO arduino-cli.tar.gz https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Linux_64bit.tar.gz && tar xf arduino-cli.tar.gz && rm arduino-cli.tar.gz && ~/Arduino/env/arduino-cli lib install MAX6675_Thermocouple

sudo apt dist-upgrade
