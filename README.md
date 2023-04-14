### How to launch:
1. Allow port to be accessible
2. Compile and appload
3. Read the serial port, save output to the file
4. Launch arduino script that will read the file and plot a graph

# 1
ls -la /dev/ttyACM0 && sudo chmod a+rw /dev/ttyACM0 && ls -la /dev/ttyACM0 

# 2
~/Arduino-IDE/arduino-cli compile --fqbn arduino:avr:mega ~/Arduino/sketch && ~/Arduino-IDE/arduino-cli upload ~/Arduino/sketch --fqbn arduino:avr:mega --port /dev/ttyACM0 --verbose

# 3
cat -v /dev/ttyACM0 | tee ~/Arduino/out.txt

# 4
cd ~/Arduino && python3 main.py out.txt



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
