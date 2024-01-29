import sys
sys.path.append('/home/hacksang/Documents/powerModel')
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
	device = Device(device_id, 5555, 1)
	device.display_info()

	cc = CPUControl(device)
	pm = PowerMonitor()
	pm.start()
	time.sleep(1)
	pm.stop()
	logger.debug(pm.power_data)

if __name__ == '__main__':
	main()
