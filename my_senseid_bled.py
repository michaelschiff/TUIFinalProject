import bglib, serial, time, datetime

class BGClient:
    def __init__(self, port_name, baud_rate, callback, packet_mode=False, enable_debug=False):
        self.callback = callback
        self.data_dict = 0

        # basic initialization
        self.port_name = port_name
        self.baud_rate = baud_rate

        # set up the bluegiga controller
        self.ble = bglib.BGLib()
        self.ble.packet_mode = packet_mode
        self.ble.debug = enable_debug

        # make a serial port
        self.ser = serial.Serial(port=self.port_name, baudrate=self.baud_rate, timeout=1, writeTimeout=1)
        
        self.peripheral_list = []
        self.connection_handle = 0
        self.att_handle_start = 0
        self.att_handle_end = 0
        self.att_handles = {'gesture': 0,
                            'gesture_ccc': 0,
                            'heading': 0,
                            'heading_ccc': 0,
                            'gps_x': 0,
                            'gps_y': 0}

        #state types
        self.STATE_STANDBY = 0
        self.STATE_CONNECTING = 1
        self.STATE_FINDING_SERVICES = 2
        self.STATE_FINDING_ATTRIBUTES = 3
        self.STATE_LISTENING_MEASUREMENTS = 4
        
        #set our state
        self.state = self.STATE_STANDBY
    
    def print_data(self):
        print self.data_dict

    def set_data(self, val):
        self.data_dict = val
    
    def my_timeout(self, sender, args):
        self.ble.send_command(self.ser, self.ble.ble_cmd_system_reset(0))
        self.ble.check_activity(self.ser, 1)
        print "BGAPI parser timed out.  Make sure the BLE device is in a known/idle state."

    def my_ble_evt_gap_scan_response(self, sender, args):
        advertisement = args['data']
        if advertisement == [ord(x) for x in list("Senseid")]:
            print "Found Senseid Device"
            self.ble.send_command(self.ser, self.ble.ble_cmd_gap_connect_direct(args['sender'], 0, 0x20, 0x30, 0x100, 0))
            self.ble.check_activity(self.ser, 1)
            self.state = self.STATE_CONNECTING

    def my_ble_evt_connection_status(self, sender, args):
        if (args['flags'] & 0x05) == 0x05:
            #print "Connected to %s" % ':'.join(['%02X' % b for b in args['address'][::-1]])
            self.connection_handle = args['connection']
            self.ble.send_command(self.ser, self.ble.ble_cmd_attclient_read_by_group_type(args['connection'], 0x0001, 0xFFFF, [0x00, 0x28]))
            self.ble.check_activity(self.ser, 1)
            self.state = self.STATE_FINDING_SERVICES

    def my_ble_evt_attclient_group_found(self, sender, args):
        print "Found Service: " + str(args['uuid'])
        if args['uuid'] == [0xe2, 0x85, 0xa7, 0xc5, 0x8d, 0x72, 0x7a, 0xbd, 0x66, 0x43, 0xab, 0x6f, 0x46, 0x08, 0x32, 0x0c]:
            #print "Found attribute group for Senseid service: start=%d, end=%d" % (args['start'], args['end'])
            self.att_handle_start = args['start']
            self.att_handle_end = args['end']

    def my_ble_evt_attclient_find_information_found(self, sender, args):
        if args['uuid'] == [0x44, 0x4f, 0xe6, 0xbe, 0x46, 0x4b, 0xa0, 0xbb, 0x8c, 0x4e, 0x9b, 0x2c, 0x67, 0x97, 0xc6, 0xd1]:
            print "Found gesture characteristic: handle=%d" % args['chrhandle']
            self.att_handles['gesture'] = args['chrhandle']
        elif args['uuid'] == [0xc7, 0x40, 0xd6, 0x34, 0x69, 0xdd, 0xdb, 0x87, 0xa8, 0x4a, 0xff, 0x4d, 0x93, 0x58, 0x21, 0xce]:
            print "Found heading characteristic: handle=%d" % args['chrhandle']
            self.att_handles['heading'] = args['chrhandle']
        elif args['uuid'] == [0x79, 0xfe, 0x7b, 0x34, 0xd2, 0xb0, 0x9c, 0xb0, 0x69, 0x4f, 0xd3, 0x42, 0xad, 0x03, 0xde, 0x46]:
            print "Found gps_x characteristic: handle=%d" % args['chrhandle']
            self.att_handles['gps_x'] = args['chrhandle']
        elif args['uuid'] == [0xbf, 0x22, 0xb9, 0xa3, 0x93, 0x3b, 0x8f, 0xab, 0x72, 0x4c, 0x03, 0xbe, 0x9d, 0x0e, 0x36, 0x88]:
            print "Found gps_y characteristic: handle=%d" % args['chrhandle']
            self.att_handles['gps_y'] = args['chrhandle']
        elif args['uuid'] == [0x02, 0x29]:
            if self.att_handles['gesture'] > 0 and self.att_handles['gesture_ccc'] == 0:
                print "Found gesture_ccc characteristic: handle=%d" % args['chrhandle']
                self.att_handles['gesture_ccc'] = args['chrhandle']
            elif self.att_handles['heading'] > 0 and self.att_handles['heading_ccc'] == 0:
                print "FOund heading_ccc characteristic: handle=%d" % args['chrhandle']
                self.att_handles['heading_ccc'] = args['chrhandle']
            else:
                print "Error: Unkown client configuration characteristic"


    def my_ble_evt_attclient_procedure_completed(self, sender, args):
        if self.state == self.STATE_FINDING_SERVICES:
            if self.att_handle_end > 0:
                self.state = self.STATE_FINDING_ATTRIBUTES
                self.ble.send_command(self.ser, self.ble.ble_cmd_attclient_find_information(self.connection_handle, self.att_handle_start, self.att_handle_end))
                self.ble.check_activity(self.ser, 1)
            else:
                print "Could not find the Senseid device"
        elif self.state == self.STATE_FINDING_ATTRIBUTES:
            if self.att_handles['gesture_ccc'] > 0:
                self.state = self.STATE_LISTENING_MEASUREMENTS
                self.ble.send_command(self.ser, self.ble.ble_cmd_attclient_attribute_write(self.connection_handle, self.att_handles['gesture_ccc'], [0x01]))
                self.ble.check_activity(self.ser, 1)
            else:
                print "Could not find Senseid gesture attribute"

    def my_ble_evt_attclient_attribute_value(self, sender, args):
        if args['connection'] == self.connection_handle and args['atthandle'] == self.att_handles['gesture']:
            message = "".join([chr(x) for x in args['value']])
            #print "Notification: " + message
            self.callback(message)
            self.ble.send_command(self.ser, self.ble.ble_cmd_attclient_write_command(self.connection_handle, self.att_handles['gps_x'], [self.data_dict]))
            self.ble.check_activity(self.ser, 1)

    def read(self):
        self.ble.on_timeout += self.my_timeout

        self.ble.ble_evt_gap_scan_response += self.my_ble_evt_gap_scan_response
        self.ble.ble_evt_connection_status += self.my_ble_evt_connection_status
        self.ble.ble_evt_attclient_group_found += self.my_ble_evt_attclient_group_found
        self.ble.ble_evt_attclient_find_information_found += self.my_ble_evt_attclient_find_information_found
        self.ble.ble_evt_attclient_procedure_completed += self.my_ble_evt_attclient_procedure_completed
        self.ble.ble_evt_attclient_attribute_value += self.my_ble_evt_attclient_attribute_value

        self.ser.flushInput()
        self.ser.flushOutput()

        self.ble.send_command(self.ser, self.ble.ble_cmd_connection_disconnect(0))
        self.ble.check_activity(self.ser, 1)

        self.ble.send_command(self.ser, self.ble.ble_cmd_gap_set_mode(0,0))
        self.ble.check_activity(self.ser, 1)

        self.ble.send_command(self.ser, self.ble.ble_cmd_gap_end_procedure())
        self.ble.check_activity(self.ser, 1)

        self.ble.send_command(self.ser, self.ble.ble_cmd_gap_set_scan_parameters(0xC8, 0xC8, 1))
        self.ble.check_activity(self.ser, 1)

        self.ble.send_command(self.ser, self.ble.ble_cmd_gap_discover(2))
        self.ble.check_activity(self.ser, 1)

        while 1:
            self.ble.check_activity(self.ser)
            time.sleep(0.01)


monitor = BGClient("/dev/tty.usbmodem1", 115200, lambda x: x)

if __name__ == "__main__":
    x = BGClient("/dev/tty.usbmodem1", 115200)
    x.main()
