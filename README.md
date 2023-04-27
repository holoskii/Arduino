### Environment setup
sudo add-apt-repository universe
sudo apt update && sudo apt install git python3-pip fish terminator
sudo snap install code --classic
pip3 install matplotlib
git clone https://github.com/holoskii/arduino.git
cd ~/Arduino/env && ./install_fish.sh env_noenv.fish

cd ~/Arduino/ && wget -qO arduino-cli.tar.gz https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Linux_64bit.tar.gz && tar xf arduino-cli.tar.gz && rm arduino-cli.tar.gz && ~/Arduino/env/arduino-cli lib install MAX6675_Thermocouple

sudo apt dist-upgrade


### How to launch:
1. Allow port to be accessible
2. Compile and appload
3. Read the serial port, save output to the file
4. Launch arduino script that will read the file and plot a graph

# 1
ls -la /dev/ttyACM0 && sudo chmod a+rw /dev/ttyACM0 && ls -la /dev/ttyACM0 

# 2
~/Arduino/env/arduino-cli compile --fqbn arduino:avr:mega ~/Arduino/sketch --clean && ~/Arduino/env/arduino-cli upload ~/Arduino/sketch --fqbn arduino:avr:mega --port /dev/ttyACM0 --verbose

# 3
cat -v /dev/ttyACM0 | tee ~/Arduino/out.txt

# 4
cd ~/Arduino && python3 main.py out.txt


# Uppload and read
~/Arduino/env/arduino-cli compile --fqbn arduino:avr:mega ~/Arduino/sketch && ~/Arduino/env/arduino-cli upload ~/Arduino/sketch --fqbn arduino:avr:mega --port /dev/ttyACM0 --verbose && cat -v /dev/ttyACM0 | tee ~/Arduino/out.txt



### Design
1. Arduino side, control
We can only read once in 250ms (sensor limitation)
a. Read 3 times, 333ms apart
b. Read 4 times, 250ms apart
Find average to avoid noise, calculate PID. Optimal values are around 0.02, 0, 0.20 

Control value will be from 0 to 1000. It represents how many ms in a second the relay will be on. But avoid numbers from 1..100, and from 900..999 to avoid rapid switching

### Pinout
1. Substrate
Thermal module: 2 - GND, 3 - 5V, 4 - SCK, 5 - CS, 6 - SO
Relay: 22 - control pin (+), 23 - GND

2. Source
Thermal module: 8 - GND, 9 - 5V, 10 - SCK, 11 - CS, 12 - SO
Relay: 24 - control pin (+), 25 - GND




Relay
SSR-10DA
Switch time < 10ms

Temp sensor
