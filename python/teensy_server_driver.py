import serial, serial.tools.list_ports
import time

class teensy_server_driver():
    def find_board(self):
        ports = serial.tools.list_ports.comports(include_links=False)
        for port in ports :
            # print('Trying port: '+ port.device)
            self.teensy = serial.Serial(port=port.device, baudrate=115200, timeout=.1)
            self.teensy.setDTR(False)
            time.sleep(0.25)
            self.teensy.flushInput()
            self.teensy.setDTR(True)
            self.teensy.write(b'000000')
            time.sleep(0.05)
            data = self.teensy.readline()
            if data == b'PING':
                self.com_port = port.device
                return True
        return False

    def ping_board(self):
        self.teensy.write(b'000000')
        time.sleep(0.05)
        data = self.teensy.readline()
        if data == b'PING':
            return True
        return False

    def get_fw_version(self):
        self.teensy.write(b'010000')
        time.sleep(0.25)
        data = self.teensy.readline()
        return(data)

    def set_gpio(self, channel, value):
        message = bytearray(b'050000')
        
        message[2:3] = str(channel).encode('ascii')
        
        if (value):
            message[3:4] = b'1'
        else:
            message[3:4] = b'0'
        self.teensy.write(message)

    def get_gpio(self, channel):
        message = bytearray(b'040000')
        
        message[2:3] = str(channel).encode('ascii')
        
        self.teensy.write(message)
        time.sleep(0.05)
        data = self.teensy.readline()
        data2 = data.rstrip(b'\r\n')
        if (data2.isdigit()):
            inti = int(data2)
        else:
            print("get_gpio(): invalid data for int: " + str(data))

        if (inti == 0):
            return False
        elif (inti == 1):
            return True
        return False

    def set_dac(self, value):
        message = bytearray(b'030000')
        fff = "{0:0>4}".format(value)
        message[2:6] = str(fff).encode('ascii')
        self.teensy.write(message)

    def get_adc(self, channel):
        message = bytearray(b'020000')
        message[2:3] = str(channel).encode('ascii')
        self.teensy.write(message)
        # time.sleep(0.05)
        data = self.teensy.readline()
        data2 = data.rstrip(b'\r\n')
        if (data2.isdigit()):
            inti = int(data2)
        else:
            print("get_adc(): invalid data for int: " + str(data))
        return inti

    def i2c_begin(self, address):
        if ((address < 0) | (address > 255)):
            return
        message = bytearray(b'060000')
        message[2:4] = str(address).encode('ascii')
        self.teensy.write(message)
        
    def i2c_end(self):
        message = bytearray(b'080000')
        self.teensy.write(message)

    def i2c_write_bytes(self, data):
        message = bytearray(b'070000')
        message[2:4] = str(data).encode('ascii')
        # print("i2c_write(): " + str(message))
        self.teensy.write(message)

    def i2c_start(self, address):
        if ((address < 0) | (address > 255)):
            return
        # brd.DACPing(2)
        # System.out.println("    DAC2 Ping successful... ");
        # Perform software reset of DAC
        dac_addr = 31
        
        ############ SW_RESET 0b01010001, 0b00000000, 0b00000000
        message = bytearray(b'060000')
        message[2:4] = str(dac_addr).encode('ascii')
        self.teensy.write(message)
        
        message = bytearray(b'070000')
        dac_sw_reseta = (hex(0b01010001)).replace('0x','')
        message[2:4] = str(dac_sw_reseta).encode('ascii')
        self.teensy.write(message)

        message = bytearray(b'070000')
        self.teensy.write(message)
        
        message = bytearray(b'070000')
        self.teensy.write(message)

        message = bytearray(b'080000')
        self.teensy.write(message)

        ############ REF_SET 0b01110111, 0b00000000, 0b00000000
        message = bytearray(b'060000')
        message[2:4] = str(dac_addr).encode('ascii')
        self.teensy.write(message)

        message = bytearray(b'070000')
        dac_ref_seta = 0b0111
        message[2:3] = str(dac_ref_seta).encode('ascii')
        dac_ref_setb = 0b0111
        message[3:4] = str(dac_ref_setb).encode('ascii')
        self.teensy.write(message)

        message = bytearray(b'070000')
        self.teensy.write(message)

        message = bytearray(b'070000')
        self.teensy.write(message)

        message = bytearray(b'080000')
        self.teensy.write(message)

        # message = bytearray(b'060000')
        # message[2:4] = str(dac_addr).encode('ascii')
        # self.teensy.write(message)
        # message = bytearray(b'070000')
        # self.teensy.write(message)
        # message = bytearray(b'080000')
        # self.teensy.write(message)

        # message = bytearray(b'060000')
        # message[2:4] = str(dac_addr).encode('ascii')
        # self.teensy.write(message)
        # message = bytearray(b'070000')
        # self.teensy.write(message)
        # message = bytearray(b'080000')
        # self.teensy.write(message)

        # Perform reference set of DAC
        message = bytearray(b'060000')
        message[2:4] = str(dac_addr).encode('ascii')
        self.teensy.write(message)

        message = bytearray(b'070000')
        dac_ref_seta = 0b0111
        message[2:3] = str(dac_ref_seta).encode('ascii')
        dac_ref_setb = 0b0111
        message[3:4] = str(dac_ref_setb).encode('ascii')
        self.teensy.write(message)

        message = bytearray(b'070000')
        self.teensy.write(message)

        message = bytearray(b'070000')
        self.teensy.write(message)

        message = bytearray(b'080000')
        self.teensy.write(message)

        message = bytearray(b'060000')
        message[2:4] = str(dac_addr).encode('ascii')
        self.teensy.write(message)
        message = bytearray(b'070000')
        self.teensy.write(message)
        message = bytearray(b'080000')
        self.teensy.write(message)

        message = bytearray(b'060000')
        message[2:4] = str(dac_addr).encode('ascii')
        self.teensy.write(message)
        message = bytearray(b'070000')
        self.teensy.write(message)
        message = bytearray(b'080000')
        self.teensy.write(message)

