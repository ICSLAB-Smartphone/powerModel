import sys
sys.path.append('/home/hacksang/Documents/powerModel')
import re
import time
import argparse
import subprocess
from src.log import logger
from configs import config
from device import Device
from cpuControl import CPUControl
from powerMonitor import PowerMonitor
from powerMonitor import PMType
import curses

def run_stress(benchmark, cpu_mask, timeout=10):
	subprocess.run(["adb", "shell", "nice", "-n", "-20", "taskset", cpu_mask,  "timeout", str(timeout), "/data/local/tmp/{}".format(benchmark)])

def draw_cpu():
	# Drawing a conceptual diagram of the CPU
	print("Arm Heterogeneous CPU Structure:")
	print("┌─────────────────────────┐")
	print("│ Heterogeneous CPU Cores │")
	print("├────────────┬────────────┤")
	print("│	 Big	│	Small   │")
	print("│  [4 Cores] │   [4 Cores]│")
	print("│			│			│")
	print("│	Test	│   Monitor  │")
	print("│ Program Run│ Program Run│")
	print("└────────────┴────────────┘")

draw_cpu()

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--device_id', type=str, default='10.255.4.199')
	parser.add_argument('--benchmark', type=str, default='dhrystone', choices=[
		'dhrystone', 'CPU2006', 'dhrystone64_bit.elf'
	])
	# the way we measure the power of mobile device
	parser.add_argument('--power_monitor', type=str, default='hardware', choices=[
		'hardware', 'software', 'idle'
	])
	args = parser.parse_args()

	device_id = args.device_id
	device = Device(device_id, 5555, 10)
	device.display_info()

	benchmark_path = {
		'dhrystone': config.RootPath + "benchmark/dhrystone/dhrystone",
		'dhrystone64_bit.elf': config.RootPath + "benchmark/dhrystone/dhrystone64_bit.elf",
		'CPU2006': config.RootPath + "benchmark/cpu2006/benchspec/CPU2006"
	}
	benchmark = args.benchmark

	power_monitor = args.power_monitor
	if power_monitor == "hardware":
		pm_type = PMType.Hardware
	elif power_monitor == "software":
		pm_type = PMType.Software
	elif power_monitor == "idle":
		pm_type = PMType.Idle

	cc = CPUControl(device)
	pm = PowerMonitor(pm_type)

	'''
	0. setup something for the vendor
	'''
	### msm
	device.run_shell_cmd("echo 0:4294967295 1:4294967295 2:4294967295 3:429496 7295 4:4294967295 5:4294967295 6:4294967295 7:4294967295 >/sys/module/msm_performance/parameters/cpu_max_freq")

	logger.debug("Disable Vendor Service")
	result = device.run_shell_cmd("getprop | grep hypnus")
	if "[1]" in result:
		### OPPO 
		logger.debug("disable hypnus")
		device.run_shell_cmd("setprop persist.sys.hypnus.daemon.enable 0")
		device.run_shell_cmd("setprop sys.enable.hypnus 0")
		device.run_shell_cmd("stop hypnusd")

	result = device.run_shell_cmd("getprop | grep perf-hal-")
	results = result.splitlines()
	for result in results:
		if "running" in result:
			match = re.search("perf-hal-\d-\d", result)
			if match != None:
				logger.debug("disable " + match.group(0))
				device.run_shell_cmd("stop " + match.group(0))

	logger.info(device.run_shell_cmd("getprop | grep hypnus").replace("\n", " "))
	logger.info(device.run_shell_cmd("getprop | grep perf-hal-").replace("\n", " "))

	### Check the temperature
	logger.debug("CPU Temperature")
	num_thermal_zone = int(device.run_shell_cmd("cat /sys/devices/virtual/thermal/thermal_zone*/temp | wc").split()[0])
	for i in range(num_thermal_zone):
		zone_type = device.run_shell_cmd("cat /sys/devices/virtual/thermal/thermal_zone" + str(i) + "/type")
		if "cpu" in zone_type:
			logger.info(zone_type + " : " + device.run_shell_cmd("cat /sys/devices/virtual/thermal/thermal_zone" + str(i) + "/temp"))


	'''
	1. push benchmark
	'''
	logger.debug("Push Benchmark")
	device.push_file(benchmark_path[benchmark], "/data/local/tmp/")
	device.run_shell_cmd("chmod +x /data/local/tmp/"+benchmark)

	'''
	2. control the CPU
	'''
	### store original cpus for recovery in the end
	result = device.run_shell_cmd("cd /dev/cpuset/; find . -type d")
	results = result.splitlines()
	original_cpus = {}
	for result in results:
		if "./" in result:
			group_name = result[2:]
			original_cpus[group_name] = device.run_shell_cmd("cat /dev/cpuset/{}/cpus".format(group_name))
			logger.info(group_name)
			logger.info(original_cpus[group_name])

	### pick the cpus where benchmark runs
	if cc.core_type == 2:
		benchmark_core_idx = [3, 7]
		awake_core_idx = [4, 0]
		senarios = ["LITTLE", "big"]
		cpu_mask = ["08", "80"]
	else:
		benchmark_core_idx = [3, 6, 7]
		awake_core_idx = [4, 0, 4]
		senarios = ["LITTLE", "big", "Super"]
		cpu_mask = ["08", "40", "80"]
	
	### disable cpus to make effective_cpus in each group change
	for idx in benchmark_core_idx:
		cc.disable_cpu(idx)

	logger.debug("Set cpus for other cgroup")
	for result in results:
		if "./" in result:
			group_name = result[2:]
			effective_cpus = device.run_shell_cmd("cat /dev/cpuset/{}/effective_cpus".format(group_name))
			device.run_shell_cmd("echo {} > /dev/cpuset/{}/cpus".format(effective_cpus, group_name))

	logger.debug("Create cpuset for benchmark")
	device.run_shell_cmd("mkdir /dev/cpuset/test-app")

	'''
	3. run the test
	'''
	for i in range(cc.core_type):
		logger.critical("Senario {}".format(senarios[i]))
		logger.debug("Disable non-awake core")
		cc.enable_cpu(awake_core_idx[i])	# make sure at least one cpu awake
		cc.set_cpu_clock(awake_core_idx[i], -1)
		logger.debug("Monitor runs on the core {}".format(awake_core_idx[i]))
		for j in range(8):
			if j != awake_core_idx[i]:		# keep awake cpu 
				cc.disable_cpu(j)
		logger.info("Online : " + device.run_shell_cmd("cat /sys/devices/system/cpu/online"))
		logger.info("Offline : " + device.run_shell_cmd("cat /sys/devices/system/cpu/offline"))
		
		### collect basic power
		pm.start()
		time.sleep(10)
		pm.stop()
		print(pm.power_data)
		basic_power = sum(pm.power_data) / len(pm.power_data)
		pm.power_data = []
		logger.debug("Basic Power : {}".format(basic_power))

		### Isolate the core idx
		logger.debug("Benchmark runs on the core {}".format(benchmark_core_idx[i]))
		cc.enable_cpu(benchmark_core_idx[i])
		cc.set_cpu_clock(benchmark_core_idx[i], -1)
		device.run_shell_cmd("echo 1 > /sys/devices/system/cpu/cpu0/core_ctrl/min_cpus")
		device.run_shell_cmd("echo 1 > /sys/devices/system/cpu/cpu0/core_ctrl/max_cpus")
		device.run_shell_cmd("echo 1 > /sys/devices/system/cpu/cpu4/core_ctrl/min_cpus")
		device.run_shell_cmd("echo 1 > /sys/devices/system/cpu/cpu4/core_ctrl/max_cpus")

		logger.info("Online : " + device.run_shell_cmd("cat /sys/devices/system/cpu/online"))
		logger.info("Offline : " + device.run_shell_cmd("cat /sys/devices/system/cpu/offline"))
		device.run_shell_cmd("echo {} > /dev/cpuset/test-app/cpus".format(benchmark_core_idx[i]))
		device.run_shell_cmd("echo 1 > /dev/cpuset/test-app/cpu_exclusive")
		#device.run_shell_cmd("ps -o pid,psr,comm,s -A | awk -v a='3' I#)

		### run the test on the core idx
		pm.start()
		run_stress(benchmark, cpu_mask[i])
		pm.stop()
		print(pm.power_data)
		run_power = sum(pm.power_data) / len(pm.power_data)
		extra_power = run_power - basic_power
		logger.debug("Running Power : {}".format(run_power))
		logger.debug("Extra Power : {}".format(extra_power))
		pm.power_data = []


		### Verify the system
		### 1. /proc/interrupts			   -> CPU online or not
		### 2. /cpufreq/stat/time_in_state -> freq doesn't change

	'''
		recover the system
	'''
	logger.debug("Recovery System")
	for i in range(8):
		cc.enable_cpu(i)
	### TODO
	device.run_shell_cmd("echo 0 > /sys/devices/system/cpu/cpu0/core_ctrl/min_cpus")
	device.run_shell_cmd("echo 4 > /sys/devices/system/cpu/cpu0/core_ctrl/max_cpus")
	device.run_shell_cmd("echo 0 > /sys/devices/system/cpu/cpu4/core_ctrl/min_cpus")
	device.run_shell_cmd("echo 4 > /sys/devices/system/cpu/cpu4/core_ctrl/max_cpus")

	device.run_shell_cmd("rm -rf /dev/cpuset/test-app")

	for key,value in original_cpus.items():
		device.run_shell_cmd("echo {} > /dev/cpuset/{}/cpus".format(value, key))
	logger.info(device.run_shell_cmd("find /dev/cpuset/ -name cpus | xargs cat"))


if __name__ == '__main__':
	try:
		#curses.wrapper(main)
		main()
	except KeyboardInterrupt:
		pass
