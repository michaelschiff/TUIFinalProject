import threading
from GestureQueue import gesture_queue
import web
#import SerialReader
from my_senseid_bled import monitor
import time


def add_to_queue(s):
    print s
    gesture_queue.put(s)
    #time.sleep(2)

def get_from_queue():
    return gesture_queue.get()

#monitor = SerialReader.Monitor(add_to_queue)
#monitor = BGClient("/dev/tty.usbmodem1", 115200, add_to_queue)
monitor.callback = add_to_queue

urls = (
    '/', 'index',
    '/longpoll/', 'longpoll'
    )
render = web.template.render('templates/')

class longpoll:
    def GET(self):
        web.header('Content-type', 'text/javascript/')
        item = get_from_queue()
        yield str(item)

class index:
    def GET(self):
        return render.index()
    def POST(self):
        h = int(web.input().x)
        v = int(web.input().y)
        if v <= h and v <= -1*h + 500: monitor.set_data(4)
        elif v < h and v > -1*h + 500: monitor.set_data(3)
        elif v >= h and v >= -1*h + 500: monitor.set_data(2)
        elif v > h and v < -1*h + 500: monitor.set_data(1) 
        #if h>=250 and v < 250: monitor.set_data(4)
        #elif h>=250 and v >= 250: monitor.set_data(3)
        #elif h<250 and v < 250: monitor.set_data(2)
        #elif h<250 and v >= 250: monitor.set_data(1)
        monitor.print_data()

if __name__ == "__main__":
    t = threading.Thread(target=monitor.read)
    t.start()
    print "Serial Monitor Started"
    print "Starting Server"
    app = web.application(urls, globals())
    app.run()
