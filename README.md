Dell XPS fan control helper tool
================================

The problem
-----------

The BIOS of Dell XPS 9560 frequently forgets to stop the fan when the fan is on lower speed and the CPU is cool
enough. This is very annoying, as once the fan turns on, it rarely shuts down. There exists a custom fan control
daemon called i8k, but it turns off BIOS fan control which is very dangerous and suppors only 2 fan speeds.

How it works
------------

Fortunately the fan immediately stops if "smbios-thermal-ctl --set-thermal-mode=quiet" command is run. But next time
the CPU heats up, it starts over again. This tool is supposed to run the command periodically, but only in a given
range of temperatures. There are some zones that results in oscillations (smbios-thermal-ctl turns off the fan for
a second, and then it turns back on). On even higher temperatures, the command does nothing.
So in order to avoid oscillations, we need a bit more sophisticated method than running smbios-thermal-ctl
periodically.

Tested for 15 9560.

Installation
------------

Run ./install.sh as root. This will set up the config file, the systemd scripts and the script itself.

You can try editing /etc/silent_xps.json if you run in some oscillation problems.

Requirements
------------

Python 3 for running the script, lm_sensors for reading the temperatures and libsmbios for smbios-thermal-ctl tool.
