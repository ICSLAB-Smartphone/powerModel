import sys
sys.path.append('/home/hacksang/Documents/powerModel')
import re
import time
import argparse
import subprocess
from print_color import print
from src.log import logger
from configs import config
from device import Device
from cpuControl import CPUControl
def display_help(): 
	print(""" 可用命令： 
	   p - 显示所有CPU的可用governor和频率 (print)
	   c - 显示所有CPU的当前governor和频率 (current)
	   s <index> <frequency> - 设置指定CPU的频率 (set)
	   i <index> <increment> - 增加指定CPU的频率 (increment)
	   d <index> <decrement> - 减少指定CPU的频率 (decrement)
	   g <index> <governor> - 设置指定CPU的governor (governor)
	   h - help
	   q - 退出程序 """)

def display_governors_and_frequencies(): 
	# 显示所有CPU 可用governor和频率的代码 
	for policy in device._cpu_policies:
		print(policy, tag="CPU policy", tag_color='white', color='blue')
		print(device.run_shell_cmd("cat %s" %(config.CpuFreqPath + policy + '/affected_cpus')), tag="Affected CPU", tag_color='white', color='white')
		print(device.run_shell_cmd("cat %s" % (config.CpuFreqPath + policy + '/scaling_available_frequencies')), tag="CPU freqs", tag_color='white', color='white')
		print(device.run_shell_cmd("cat %s" % (config.CpuFreqPath + policy + '/scaling_available_governors')), tag="CPU governors", tag_color='white', color='white')

def display_cur_governors_and_frequencies(): 
	# 显示所有CPU 目前governor和频率的代码 
	for policy in device._cpu_policies:
		print(policy, tag="CPU policy", tag_color='white', color='blue')
		print(device.run_shell_cmd("cat %s" %(config.CpuFreqPath + policy + '/affected_cpus')), tag="Affected CPU", tag_color='white', color='white')
		print(device.run_shell_cmd("cat %s" % (config.CpuFreqPath + policy + '/scaling_cur_freq')), tag="CPU freqs", tag_color='white', color='white')
		print(device.run_shell_cmd("cat %s" % (config.CpuFreqPath + policy + '/scaling_governor')), tag="CPU freqs", tag_color='white', color='white')

def set_frequency(indices, frequency): 
	# 根据indices和frequency设置CPU频率 
	cc.set_cpu_freq(indices, frequency)

def increase_frequency(indices, increment): 
	# 根据indices和increment增加CPU频率 
	cur_freq = cc.get_cpu_clock_by_idx(indices)
	freq_list = cc.get_freq_list_by_idx(indices)
	freq_idx = freq_list.index(cur_freq)
	if freq_idx + increment > len(freq_list) - 1:
		pass
	else:
		cc.set_cpu_clock(indices, freq_idx + increment)

def decrease_frequency(indices, decrement): 
	# 根据indices和decrement减少CPU频率 
	cur_freq = cc.get_cpu_clock_by_idx(indices)
	freq_list = cc.get_freq_list_by_idx(indices)
	freq_idx = freq_list.index(cur_freq)
	if freq_idx - decrement < 0:
		pass
	else:
		cc.set_cpu_clock(indices, freq_idx - decrement)

def set_governor(indices, governor): 
	cc.set_cpu_governor(indices, governor)

def main():
	global device
	global cc
	device = Device(0, 0, usb_flag=True) #Usb Connect, make sure only have one device connected with usb
	#device.display_info()

	cc = CPUControl(device)

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

	'''
	1. control the CPU using while
	consider the initialization overhead, we choose while to process the command, or we have to initalize the device every time we want to change the frequencies 
	'''
	display_help()
	while True: 
		user_input = input("输入命令：") 
		command = user_input.split(' ')[0] 
		if command == 'p': 
			display_governors_and_frequencies() 
		elif command == 'c': 
			display_cur_governors_and_frequencies() 
		elif command == 's': 
			indices = int(user_input.split(' ')[1])
			frequency = int(user_input.split(' ')[-1]) 
			set_frequency(indices, frequency) 
		elif command == 'i': 
			indices = int(user_input.split(' ')[1])
			increment = int(user_input.split(' ')[-1]) 
			increase_frequency(indices, increment) 
		elif command == 'd': 
			indices = int(user_input.split(' ')[1])
			decrement = int(user_input.split(' ')[-1]) 
			decrease_frequency(indices, decrement) 
		elif command == 'g': 
			indices = int(user_input.split(' ')[1])
			governor = user_input.split(' ')[-1] 
			set_governor(indices, governor) 
		elif user_input == 'h': 
			display_help()
		elif user_input == 'q': 
			break 
		else: 
			print("无效命令，请重新输入")


	'''
		recover the system
	'''
	logger.debug("Recovery System")
	### TODO

if __name__ == '__main__':
	main()
