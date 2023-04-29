# ======================================== Header ========================================
function impl_mixin_deps
end
function impl_config_fish
end
function impl_fish_home_path
   echo $HOME
end



# =======================================================================================

# Make sure that the port is accessible: sudo chmod a+rw /dev/ttyACM0

# Reload fish functions
function ard_update_me
   cd ~/Arduino && git pull
   rm -rf ~/.config/fish/ && cd ~/Arduino/env && ./install_fish.sh env_noenv.fish && omf reload
end

# Compile and appload
function ard_compile
   sudo chmod a+rw /dev/ttyACM0 && ~/Arduino/env/arduino-cli compile --fqbn arduino:avr:mega ~/Arduino/sketch --clean && ~/Arduino/env/arduino-cli upload ~/Arduino/sketch --fqbn arduino:avr:mega --port /dev/ttyACM0 --verbose
end

# Read the serial port, save output to the file in append mode
function ard_read
   sudo chmod a+rw /dev/ttyACM0 && cat -v /dev/ttyACM0 | tee -a ~/Arduino/out.txt
end

function ard_read_clear
   sudo chmod a+rw /dev/ttyACM0 && cat -v /dev/ttyACM0 | tee ~/Arduino/out.txt
end

# Plot in real-time
function ard_plot
   cd ~/Arduino && python3 main.py out.txt
end
