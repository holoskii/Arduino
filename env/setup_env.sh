sudo add-apt-repository universe
sudo apt update && sudo apt install git python3-pip fish terminator python3-tk python3-pil python3-pil.imagetk
sudo snap install code --classic
pip3 install matplotlib customtkinter CTkMessagebox

cd ~
git clone https://github.com/holoskii/Arduino.git
rm -rf ~/.config/fish/ && cd ~/Arduino/env && ./install_fish.sh env_noenv.fish && omf reload

cd ~/Arduino/env && wget -qO arduino-cli.tar.gz https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Linux_64bit.tar.gz && tar xf arduino-cli.tar.gz && rm arduino-cli.tar.gz && ~/Arduino/env/arduino-cli lib install MAX6675_Thermocouple

sudo apt dist-upgrade
