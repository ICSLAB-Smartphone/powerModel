import argparse
import Monsoon.HVPM as HVPM
import Monsoon.sampleEngine as sampleEngine
import Monsoon.Operations as op

parser = argparse.ArgumentParser()
parser.add_argument('--voltage', type=str, required=True, help="Voltage to supply smarthphone")
args = parser.parse_args()
volt = float(args.voltage)

Mon = HVPM.Monsoon()
Mon.setup_usb()
Mon.calibrateVoltage()

Mon.setVout(volt)
