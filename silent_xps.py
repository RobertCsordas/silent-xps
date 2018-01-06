#!/usr/bin/env python3

# The BIOS of Dell XPS 9560 frequently forgets to stop the fan when the fan is on lower speed and the CPU is cool
# enough. This is very annoying, as once the fan turns on, it rarely shuts down.
# Fortunately the fan immediately stops if "smbios-thermal-ctl --set-thermal-mode=quiet" command is run. But next time
# the CPU heats up, it starts over again. This tool is supposed to run the command periodically, but only in a given
# range of temperatures. There are some zones that results in oscillations (smbios-thermal-ctl turns off the fan for
# a second, and then it turns back on). On even higher temperatures, the command does nothing.
# So in order to avoid oscillations, we need a bit more sophisticated method than running smbios-thermal-ctl
# periodically.

import os
import subprocess
import time
import argparse
import json
import sys

parser = argparse.ArgumentParser(description='XPS BIOS fan control helper')
parser.add_argument('-config', type=str, help='Config file to load. Other flags has priority over -config.')
opt = parser.parse_args()


if opt.config:
    with open(opt.config) as f:
        stop_ranges = json.load(f)
else:
    stop_ranges = [{
        "max": 49
    }]

LOW_FOR_SECONDS_ON_TURNOFF = 30
DELAY_LONG = 60
DELAY_SHORT = 5


def run(command):
    return subprocess.run([s for s in command.split(" ") if s], stdout=subprocess.PIPE).stdout.decode('utf-8').split("\n")


def parse_line(l, endchar = "C"):
    colon_pos = l.find(":")
    end_pos = l.find(endchar, colon_pos+1)
    return float(l[colon_pos+1:end_pos-1].strip())


def get_info():
    sensors_out = run("sensors")
    sensors_out = [s.strip() for s in sensors_out]

    temp_info={"cpu":[]}
    fan_info=[]

    next = None
    for l in sensors_out:
        #print(l)
        if l.startswith("Core"):
            temp=parse_line(l)
            temp_info["cpu"].append(temp)
        elif l.startswith("pch_skylake"):
            next = "pch"
        elif l.startswith("temp"):
            if next is not None:
                if next not in temp_info:
                    temp_info[next]=[]
                temp_info[next].append(parse_line(l))
        elif l.endswith("RPM"):
            fan_info.append(parse_line(l,"R"))
        elif not l:
            next = None

    return temp_info, fan_info


def is_gpu_running():
    switchdev = "/proc/acpi/bbswitch"
    if not os.path.isfile(switchdev):
        return True

    with open(switchdev) as dev:
        state = dev.readline().strip()

    return state.split(" ")[-1]!="OFF"


def get_max(info):
    m1 = []
    for _, t in info.items():
        m1.append(max(t))
    return max(m1)


def find_temp_range(temp, range_list):
    for s in range_list:
        if not "min" in s:
            if temp <= s["max"]:
                return s
        elif not "max" in s:
            if temp > s["min"]:
                return s
        elif s["min"] < temp and s["max"]>= temp:
            return s
    return None


def stop_fan():
    print("Requesting fan stop")
    run("smbios-thermal-ctl --set-thermal-mode=quiet")
    pass


def cmd_exists(cmd):
    try:
        subprocess.check_output("which "+cmd, shell=True, stderr=subprocess.STDOUT)
        return True
    except:
        return False


first_stop_seen = None
temp_ok_threshold = None

if not cmd_exists("smbios-thermal-ctl"):
    print("smbios-thermal-ctl not installed. Please install libsmbios package.")
    sys.exit(-1)

if not cmd_exists("sensors"):
    print("sensors not installed. Please install lm_sensors package.")
    sys.exit(-1)

if os.geteuid() != 0:
    print("Must run this as root for smbios-thermal-ctl to work.")
    sys.exit(-1)

while True:
    temp_info, fan_info = get_info()
    max_temp = get_max(temp_info)
    max_fan = max(fan_info)
    if max_fan > 0:
        t_range = find_temp_range(max_temp, stop_ranges)
        if t_range is not None and "threshold" in t_range:
            temp_ok_threshold = t_range["threshold"]

        if t_range or (temp_ok_threshold is not None and temp_ok_threshold>=max_temp):
            if first_stop_seen is None:
                first_stop_seen = time.time()
            elif time.time() - first_stop_seen >= LOW_FOR_SECONDS_ON_TURNOFF:
                stop_fan()
                first_stop_seen = None
                temp_ok_threshold = None
            time.sleep(DELAY_SHORT)
        else:
            first_stop_seen = None
            temp_ok_threshold = None
            time.sleep(DELAY_LONG)

    else:
        time.sleep(DELAY_LONG)
