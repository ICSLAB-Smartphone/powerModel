import os

ProjectName = "PowerModel"
cur_path =  os.path.abspath(os.path.dirname(__file__))
RootPath = cur_path[:(cur_path.find(ProjectName) + len(ProjectName) + 1)]
DataPath = RootPath + "build/data/"

CpuFreqPath = "/sys/devices/system/cpu/cpufreq/"
CpuRootPath = "/sys/devices/system/cpu/"

GpuFreqPath = "/sys/class/kgsl/kgsl-3d0/devfreq/"
GpuRootPath = "/sys/class/kgsl/kgsl-3d0/"
