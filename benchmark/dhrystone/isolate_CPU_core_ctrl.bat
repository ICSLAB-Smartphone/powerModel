adb shell "echo 0 > /sys/devices/system/cpu/cpu7/core_ctl/min_cpus"
adb shell "echo 0 > /sys/devices/system/cpu/cpu7/core_ctl/max_cpus"

adb shell "echo 4 > /sys/devices/system/cpu/cpu0/core_ctl/min_cpus"
adb shell "echo 4 > /sys/devices/system/cpu/cpu0/core_ctl/max_cpus"
adb shell "echo 3 > /sys/devices/system/cpu/cpu4/core_ctl/min_cpus"
adb shell "echo 3 > /sys/devices/system/cpu/cpu4/core_ctl/max_cpus"

pause