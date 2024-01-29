import sys
sys.path.append('/home/hacksang/Documents/powerModel')
import re
import time
import argparse
from src.log import logger
from device import Device
from cpuControl import CPUControl
from powerMonitor import PowerMonitor

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--device_id', type=str, default='192.168.1.41')
	args = parser.parse_args()

	device_id = args.device_id
	device = Device(device_id, 5555, 5)
	device.display_info()

	cc = CPUControl(device)
	pm = PowerMonitor()

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

	'''
	2. control the CPU
	'''

	'''
	3. run the test
	'''

if __name__ == '__main__':
	main()
