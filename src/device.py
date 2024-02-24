import os
from print_color import print
from adb_shell import adb_device
from adb_shell.adb_device import AdbDeviceUsb,AdbDeviceTcp
from adb_shell.auth.keygen import keygen
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from src.log import logger
from configs import config
import subprocess


class Device:
	'''
		When we measure the power of the device, we must disconnect the usb with the device
		So we use tcp connect for convenience
	'''
	def __init__(self, ip, port, timeout=10, usb_flag=False):
		# Load the public and private keys
		adbkey = './adbkey'
		if not os.path.exists(adbkey):
			keygen(adbkey)
		with open(adbkey) as f:
			priv = f.read()
		with open(adbkey + '.pub') as f:
			 pub = f.read()
		signer = PythonRSASigner(pub, priv)
		adb_device._maxdata = 2048
		
		self._usb_flag = usb_flag
		if usb_flag:
			#self._device = AdbDeviceUsb() 
			### adb_shell lib cannot run parallel with "adb shell command"
			pass
		else:
			self._device = AdbDeviceTcp(ip, port, default_transport_timeout_s=timeout) 
			self._device.connect(rsa_keys=[signer])
			self._device.root()

		output = self.run_shell_cmd('root')
		if 'cannot' in output:
			logger.warning("Adb root failed")
			self._root = False
		else:
			logger.debug("Adb root success")
			self._root = True

		''' Get basic information using adb shell '''
		self._system_version = self.run_shell_cmd("getprop ro.build.version.release")
		self._sdk_version = self.run_shell_cmd("getprop ro.build.version.sdk")
		self._phone_brand = self.run_shell_cmd('getprop ro.product.brand')
		self._phone_model = self.run_shell_cmd('getprop ro.product.model')
		self._build_type = self.run_shell_cmd('getprop ro.build.type')
		self._cpu_abi = self.run_shell_cmd('getprop ro.product.cpu.abi')
		self._cpu_range = self.run_shell_cmd('cat %s' %(config.CpuRootPath + 'possible'))
		self._cpu_policies = self.run_shell_cmd('ls %s | grep policy' %config.CpuFreqPath).splitlines()
		self._cpu_governors = self.run_shell_cmd('cat %s' %(config.CpuFreqPath + 'policy0/scaling_available_governors'))

		self._gpu_model = self.run_shell_cmd('cat %s' %(config.GpuRootPath + 'gpu_model'))
		self._gpu_freqs = self.run_shell_cmd('cat %s' %(config.GpuRootPath + 'gpu_available_frequencies'))
		self._gpu_governors = self.run_shell_cmd('cat %s' %(config.GpuFreqPath + 'available_governors'))

		self._mem_total = str(round(int(self.run_shell_cmd('cat /proc/meminfo').splitlines()[0].split()[1])/1024/1024, 2))

	def display_info(self):
		print("----------------------------Basic Info---------------------------", color='cyan', background='grey')
		#print("Adb root: \t\t\t %s" % str(self._root))
		#print("system version : \t\t %s" % self._system_version)
		print(self._system_version, tag="system version", tag_color='green', color='white')
		print(self._sdk_version, tag="sdk version", tag_color='green', color='white')
		print(self._build_type, tag="build type", tag_color='green', color='white')
		print(self._phone_brand, tag="phone brand", tag_color='green', color='white')
		print(self._phone_model, tag="phone model", tag_color='green', color='white')
		print("----------------------------CPU Info-----------------------------", color='cyan', background='grey')
		print(self._cpu_abi, tag="CPU architecture", tag_color='green', color='white')
		for policy in self._cpu_policies:
			print(policy, tag="CPU policy", tag_color='white', color='blue')
			print(self.run_shell_cmd("cat %s" %(config.CpuFreqPath + policy + '/affected_cpus')), tag="Affected CPU", tag_color='white', color='white')
			print(self.run_shell_cmd("cat %s" % (config.CpuFreqPath + policy + '/scaling_available_frequencies')), tag="CPU freqs", tag_color='white', color='white')
		print(self._cpu_governors, tag="CPU governors", tag_color='green', color='white')
		print("----------------------------GPU Info-----------------------------", color='cyan', background='grey')
		print(self._gpu_model, tag="GPU model", tag_color='green', color='white')
		print(self._gpu_freqs, tag="GPU freqs", tag_color='green', color='white')
		print("----------------------------Mem Info-----------------------------", color='cyan', background='grey')
		print(self._mem_total + " GB", tag="Mem total", tag_color='green', color='white')

	def run_shell_cmd(self, cmd):
		if 'root' in cmd:
			info = subprocess.check_output(['adb', 'root'])
			return info.decode('utf-8').strip()
		elif self._usb_flag:	#non root command we all use su to execute
			if not self._root:
				cmds = ['su', cmd, 'exit']
			else:
				cmds = [cmd]
			obj = subprocess.Popen("adb shell", shell= True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			info = obj.communicate(("\n".join(cmds) + "\n").encode('utf-8'));
			return info[0].decode('utf-8').strip()
		else:
			if not self._root:
				return self._device.shell("su -c \'" + cmd + " \'").strip()
			else:
				return self._device.shell(cmd).strip()

	def push_file(self, src, dest):
		subprocess.run(["adb", "push", src ,dest])

