from device import Device
def main():
    device = Device('192.168.1.249', 5555, 1)
    device.display_info()

if __name__ == '__main__':
    main()
