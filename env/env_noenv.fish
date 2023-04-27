# ======================================== Header ========================================
function impl_mixin_deps
end
function impl_config_fish
end
function impl_fish_home_path
   echo $HOME
end



# =======================================================================================

function ard_compile
   sudo chmod a+rw /dev/ttyACM0 && ~/Arduino/env/arduino-cli compile --fqbn arduino:avr:mega ~/Arduino/sketch --clean && ~/Arduino/env/arduino-cli upload ~/Arduino/sketch --fqbn arduino:avr:mega --port /dev/ttyACM0 --verbose
end

function ard_read
   sudo chmod a+rw /dev/ttyACM0 && cat -v /dev/ttyACM0 | tee -a ~/Arduino/out.txt
end

function ard_reset
   echo "" > ~/Arduino/out.txt
end

function ard_plot
   cd ~/Arduino && python3 main.py out.txt
end
