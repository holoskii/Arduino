#!/usr/bin/fish

# Dry run handling:
set dry_run $argv[2]
function execute
   if test -n "$dry_run"
      echo "NOT Executing: $argv"
   else
      echo "Executing: $argv"
      eval $argv
   end
end

# First arg has to be set:
if test -z $argv[1]
   set -l this_script (realpath (status current-filename))
   set -l this_dir (dirname $this_script)
   echo "Usage: $this_script <env.fish>, for example:"
   for f in $this_dir/env_*.fish
      set -l relpath (realpath --relative-to=$this_dir $f)
      echo "   $this_script $relpath"
   end
   exit 1
end


# set fish_trace 2



function discover --argument-names path prefix
   echo "$prefix$path:" >&2
   echo (realpath $path)
   source $path
   set discovered (impl_mixin_deps)
   for f in $discovered
      discover $f "$prefix   "
   end
end

# Grab all info from the provided env file:
source $argv[1]
set -l fish_install_dir (realpath -m (impl_fish_home_path)/.config/fish/)
set -l config_fish_files (impl_config_fish)
mkdir -p $fish_install_dir/conf.d
echo "Installing from "(set_color -o brwhite)$argv[1](set_color normal)" to "(set_color -o brwhite)$fish_install_dir(set_color normal)":"
echo

# Main:
echo (set_color -o bryellow)Recursively discovering files to install:(set_color normal)
set files_to_install (discover $argv[1] "   " | sort -u)

echo
echo (set_color -o bryellow)Installing...(set_color normal)
for f in $files_to_install
   execute cp -n $f $fish_install_dir/conf.d
end
execute "echo \"# This is an equivalent of .bashrc\" >> $fish_install_dir/config.fish"
execute "echo >> $fish_install_dir/config.fish"
for f in $config_fish_files
   execute "echo \"# Autogenerated from $f:\" >> $fish_install_dir/config.fish"
   execute "cat $f >> $fish_install_dir/config.fish"
   execute "echo >> $fish_install_dir/config.fish"
end