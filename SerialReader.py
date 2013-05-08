import serial

class Monitor:
    def __init__(self, callback):
        self.ser = serial.Serial('/dev/tty.usbserial-A700dY46', 9600)
        self.callback = callback
        self.data = {'x':'true', 'y':'true'}
    def set_data(self, key, value):
        self.data[key] = value
    def print_data(self):
        print self.data
    def read(self):
        while True:
            self.callback(self.ser.readline().strip())
            
if __name__ == "__main__":
    def f(s): print s
    monitor = Monitor(f)
    monitor.read()
