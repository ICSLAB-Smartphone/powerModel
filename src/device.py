from print_color import print
from adb_shell.adb_device import AdbDeviceUsb,AdbDeviceTcp
from configs import config


class Device:
    '''
        When we measure the power of the device, we must disconnect the usb with the device
        So we use tcp connect for convenience
    '''
    def __init__(self, ip, port, timeout=10):
        self._device = AdbDeviceTcp(ip, port, default_transport_timeout_s=timeout) 
        self._device.connect()
        
        self._device.root()
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
        return self._device.shell(cmd).strip()

