import subprocess
from src.log import logger
from configs import config

class CPUControl:
	def __init__(self, device):
		self.device = device

		self.cpu_core_path = "/sys/devices/system/cpu/"
		little_clock_path = config.CpuFreqPath + "policy0/scaling_available_frequencies"
		big_clock_path = config.CpuFreqPath + "policy4/scaling_available_frequencies"
		sbig_clock_path = config.CpuFreqPath + "policy7/scaling_available_frequencies"
		
		self.little_governor_path = config.CpuFreqPath + "policy0/scaling_governor"
		self.big_governor_path = config.CpuFreqPath + "policy4/scaling_governor"
		self.sbig_governor_path = config.CpuFreqPath + "policy7/scaling_governor"

		self.little_min_freq = config.CpuFreqPath + "policy0/scaling_min_freq"
		self.big_min_freq = config.CpuFreqPath + "policy4/scaling_min_freq"
		self.sbig_min_freq = config.CpuFreqPath + "policy7/scaling_min_freq"

		self.little_max_freq = config.CpuFreqPath + "policy0/scaling_max_freq"
		self.big_max_freq = config.CpuFreqPath + "policy4/scaling_max_freq"
		self.sbig_max_freq = config.CpuFreqPath + "policy7/scaling_max_freq"

		self.clock_data = []
		self._cpu_policies = self.device.run_shell_cmd('ls %s | grep policy' %config.CpuFreqPath).splitlines()
		self.core_type = len(self._cpu_policies)

		#set governor userspace
		logger.debug("Set Governor")
		if self.core_type == 3:
			logger.debug("Performance for " + str(self.core_type) + " Cluster")
			self.device.run_shell_cmd('echo performance > ' + self.little_governor_path)
			self.device.run_shell_cmd('echo performance > ' + self.big_governor_path)
			self.device.run_shell_cmd('echo performance > ' + self.sbig_governor_path)
		else:
			logger.debug("UserSpace for " + str(self.core_type) + " Cluster")
			self.device.run_shell_cmd('echo userspace > ' + self.little_governor_path)
			self.device.run_shell_cmd('echo userspace > ' + self.big_governor_path)

		# get available freq
		self.little_clock_list = self.device.run_shell_cmd('cat ' + little_clock_path)
		self.little_clock_list = self.little_clock_list.split()
		self.big_clock_list = self.device.run_shell_cmd('cat ' + big_clock_path)
		self.big_clock_list = self.big_clock_list.split()

		logger.debug("Set CPU_Min_FREQ and CPU_Max_Freq")
		self.device.run_shell_cmd('echo ' + self.little_clock_list[0] + ' > ' + self.little_min_freq)
		self.device.run_shell_cmd('echo ' + self.little_clock_list[-1] + ' > ' + self.little_max_freq)
		
		self.device.run_shell_cmd('echo ' + self.big_clock_list[0] + ' > ' + self.big_min_freq)
		self.device.run_shell_cmd('echo ' + self.big_clock_list[-1] + ' > ' + self.big_max_freq)

		logger.debug("Set Freq to Max")
		self.set_little_cpu_clock(-1)
		self.set_big_cpu_clock(-1)
		if self.core_type == 3:	
			self.sbig_clock_list = self.device.run_shell_cmd('cat ' + sbig_clock_path)
			self.sbig_clock_list = self.sbig_clock_list.split()
			self.device.run_shell_cmd('echo performance > ' + self.sbig_governor_path)
			self.device.run_shell_cmd('echo ' + self.sbig_clock_list[0] + ' > ' + self.sbig_min_freq)
			self.device.run_shell_cmd('echo ' + self.sbig_clock_list[-1] + ' > ' + self.sbig_max_freq)
			self.set_sbig_cpu_clock(-1)
		else:  #big.LITTLE
			self.sbig_clock_list = []

	def set_cpu_clock(self, idx, i):
		if self.core_type == 2:
			if idx < 4:
				self.set_little_cpu_clock(i)
			else:
				self.set_big_cpu_clock(i)
		else:
			if idx < 4:
				self.set_little_cpu_clock(i)
			elif idx < 7:
				self.set_big_cpu_clock(i)
			else:
				self.set_sbig_cpu_clock(i)

	def set_cpu_freq(self, idx, freq): 
		self.device.run_shell_cmd("echo {} > {}cpu{}/cpufreq/scaling_setspeed".format(freq, self.cpu_core_path, idx))

	def set_little_cpu_clock(self, i):
		self.little_clk = i
		little_setspeed_path = config.CpuFreqPath + "policy0/scaling_setspeed"
		little_curfreq_path = config.CpuFreqPath + "policy0/scaling_cur_freq"
		if self.core_type == 3:
			self.device.run_shell_cmd('echo ' + self.little_clock_list[i] + ' > ' + self.little_max_freq)
		else:
			self.device.run_shell_cmd('echo ' + self.little_clock_list[i] + ' > ' + little_setspeed_path)

	def set_big_cpu_clock(self, i):
		self.big_clk = i
		big_setspeed_path = config.CpuFreqPath + "policy4/scaling_setspeed"
		big_curfreq_path = config.CpuFreqPath + "policy4/scaling_cur_freq"
		if self.core_type == 3:
			self.device.run_shell_cmd('echo ' + self.big_clock_list[i] + ' > ' + self.big_max_freq)
		else:
			self.device.run_shell_cmd('echo ' + self.big_clock_list[i] + ' > ' + big_setspeed_path)

	def set_sbig_cpu_clock(self, i):
		self.sbig_clk = i
		sbig_setspeed_path = config.CpuFreqPath + "policy7/scaling_setspeed"
		sbig_curfreq_path = config.CpuFreqPath + "policy7/scaling_cur_freq"
		if self.core_type == 3:
			self.device.run_shell_cmd('echo ' + self.sbig_clock_list[i] + ' > ' + self.sbig_max_freq)
		else:
			self.device.run_shell_cmd('echo ' + self.sbig_clock_list[i] + ' > ' + sbig_setspeed_path)


	def get_cpu_util(self):
		util_avgs = self.device.run_shell_cmd('cat /proc/sched_debug | grep -v autogroup | grep -A 14 cfs_rq | grep util_avg | awk \'{print $3}\'').splitlines()
		#print(util_avgs)
		util_avg_int = []
		util_avg_int = [int(i) for i in util_avgs]
		#util_avgs = util_avgs.splitlines()
		lc_util = int(sum(util_avg_int[:4]) / 500) * 500 
		bc_util = round(sum(util_avg_int[-4:]), -3)

		lc_max_util = int(max(util_avg_int[:4]) / 200) * 200
		bc_max_util = int(max(util_avg_int[-4:]) / 250) * 250
		#subprocess.run(['adb' ,  '-s', self.device_id,'shell','su', '-c',  '\'echo', str(self.little_clock_list[i], 'utf-8'), '>', little_getspeed_path + '\''])
		return (lc_max_util, bc_max_util)
	
	def get_cpu_util_time(self):
		curr_user = []
		curr_nice = []
		curr_system = []
		curr_idle = []
		curr_iowait = []
		curr_irq = []
		curr_softirq = []
		self.util_data = []
		results = self.device.run_shell_cmd('cat /proc/stat')
		results = results.splitlines()[1:]

		#print(results)
		for i in range(8):
			curr_user.append(int(results[i].split()[1]))
			curr_nice.append(int(results[i].split()[2]))
			curr_system.append(int(results[i].split()[3]))
			curr_idle.append(int(results[i].split()[4]))
			curr_iowait.append(int(results[i].split()[5]))
			curr_irq.append(int(results[i].split()[6]))
			curr_softirq.append(int(results[i].split()[7]))

		#little cluster utilization
		little_util = 0
		big_util = 0
		sbig_util = 0
		for i in range(8):
			curr_time = curr_user[i] + curr_nice[i] + curr_system[i] + curr_idle[i] + curr_iowait[i] + curr_irq[i] + curr_softirq[i]
			initial_time = self.initial_user[i] + self.initial_nice[i] + self.initial_system[i] + self.initial_idle[i] + self.initial_iowait[i] + self.initial_irq[i] + self.initial_softirq[i]
			interval = curr_time - initial_time
			cpu_util = ((curr_user[i] + curr_system[i] + curr_nice[i]) - (self.initial_user[i] + self.initial_system[i] + self.initial_nice[i])) / interval
			if self.core_type == 2:
				if i < 4:
					little_util = cpu_util + little_util
				else:
					big_util = cpu_util + big_util
			else:
				if i < 4:
					little_util = cpu_util + little_util
				elif i < 7:
					big_util = cpu_util + big_util
				else:
					sbig_util = cpu_util + sbig_util

			self.util_data.append(cpu_util)

			#print(cpu_util)

		self.initial_user = curr_user
		self.initial_nice = curr_nice
		self.initial_system = curr_system
		self.initial_idle = curr_idle
		self.initial_iowait = curr_iowait
		self.initial_irq = curr_irq
		self.initial_softirq = curr_softirq
		if self.core_type == 3:
			return (little_util, big_util, sbig_util)
		else:
			return (little_util, big_util)

	def get_little_cpu_clock(self):
		little_curfreq_path = config.CpuFreqPath + "policy0/scaling_cur_freq"
		little_cpu_clock = self.device.run_shell_cmd('cat ' + little_curfreq_path)
		#little_cpu_clock = little_cpu_clock.decode('utf-8')
		return int(little_cpu_clock)
		#subprocess.run(['adb' ,  '-s', self.device_id,'shell', 'su', '-c', '\'echo', str(self.little_clock_list[i], 'utf-8'), '>', little_getspeed_path + '\''])

	def get_big_cpu_clock(self):
		big_curfreq_path = config.CpuFreqPath + "policy4/scaling_cur_freq"
		big_cpu_clock = self.device.run_shell_cmd('cat ' + big_curfreq_path)
		#big_cpu_clock = big_cpu_clock.decode('utf-8')
		return int(big_cpu_clock)
		#subprocess.run(['adb' ,  '-s', self.device_id,'shell','su', '-c',  '\'echo', str(self.big_clock_list[i], 'utf-8'), '>', big_getspeed_path + '\''])

	def get_sbig_cpu_clock(self):
		sbig_curfreq_path = config.CpuFreqPath + "policy7/scaling_cur_freq"
		sbig_cpu_clock = self.device.run_shell_cmd('cat ' + sbig_curfreq_path)
		#sbig_cpu_clock = sbig_cpu_clock.decode('utf-8')
		return int(sbig_cpu_clock)
		#subprocess.run(['adb' ,  '-s', self.device_id,'shell', 'su', '-c', '\'echo', str(self.sbig_clock_list[i], 'utf-8'), '>', sbig_getspeed_path + '\''])

	def get_cpu_clock(self):
		if self.core_type == 2:
			return (self.get_little_cpu_clock(), self.get_big_cpu_clock())
		else:
			return (self.get_little_cpu_clock(), self.get_big_cpu_clock(), self.get_sbig_cpu_clock())

	def get_cpu_clock_by_idx(self, idx):
		return self.device.run_shell_cmd("cat {}cpu{}/cpufreq/scaling_cur_freq".format(self.cpu_core_path, idx))

	def get_freq_list_by_idx(self, idx):
		return self.device.run_shell_cmd("cat {}cpu{}/cpufreq/scaling_available_frequencies".format(self.cpu_core_path, idx)).split()

	def set_governor(self, governor):
		self.device.run_shell_cmd('echo ' + governor + ' > ' + self.little_governor_path)
		self.device.run_shell_cmd('echo ' + governor + ' > ' + self.big_governor_path)
		if self.core_type == 3:	# big. Little
			self.device.run_shell_cmd('echo ' + governor + ' > ' + self.sbig_governor_path)
		
	def set_cpu_governor(self, idx, governor):
		logger.info("echo {} > {}cpu{}/cpufreq/scaling_governor".format(governor, self.cpu_core_path, idx))
		self.device.run_shell_cmd("echo {} > {}cpu{}/cpufreq/scaling_governor".format(governor, self.cpu_core_path, idx))

	def get_governor(self):
		return self.device.run_shell_cmd('cat ' + self.little_governor_path)
	
	def disable_cpu(self, cpu_id):
		self.device.run_shell_cmd("echo 0 > {}cpu{}/online".format(self.cpu_core_path, cpu_id))

	def enable_cpu(self, cpu_id):
		self.device.run_shell_cmd("echo 1 > {}cpu{}/online".format(self.cpu_core_path, cpu_id))


	def increase_frequency(indices, increment): 
		# 根据indices和increment增加CPU频率 
		pass 

	def decrease_frequency(indices, decrement): 
		# 根据indices和decrement减少CPU频率 
		pass 
