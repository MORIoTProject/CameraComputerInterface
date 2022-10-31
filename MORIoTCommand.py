import time
from typing import Callable, Optional

import serial
from serial import SerialTimeoutException


class Command:
    PACKET_HEADER = 0
    PACKET_ID = 1
    PACKET_COMMAND = 2
    PACKET_LENGTH_H = 3
    PACKET_LENGTH_L = 4
    PACKET_DATA = 5

    def __init__(self, port_name: str, system_id: int):
        self.port_name = port_name
        self.ser = serial.Serial(port=port_name, baudrate=115200, timeout=1, writeTimeout=1)
        self.id = system_id

    def write(self, command, status, length, data):
        time.sleep(0.01)
        print("write start")
        # print([0x00, 0xea, self.id, command, (length >> 8) & 0xff, length & 0xff])
        print(data)
        try:
            print("Header:{}".format(
                self.ser.write([0x00, 0xea, self.id, command, (length >> 8) & 0xff, length & 0xff, status])
            ))
            if length != 0:
                print("Data:{}".format(self.ser.write(data)))
        except SerialTimeoutException as e:
            print(" SerialTimeoutException")
            print(e)
            self.ser.close()
            time.sleep(10)
            print("reopen SerialTimeoutException")
            self.ser.open()
        print("write end")

    def read(self, callback_data: Callable[[write, int, int, Optional[list]], None]):
        command_clear_counter = 0
        packet_type = self.PACKET_HEADER
        packet_length = 0
        packet_already_length = 0
        packet_id = 0
        packet_command = 0
        packet_array = []
        while 1:
            ch = self.ser.read(1)
            if len(ch) == 0:
                print("timeout")
                command_clear_counter += 1
                if packet_type != self.PACKET_HEADER and command_clear_counter >= 5:
                    packet_type = self.PACKET_HEADER
                    print("Command Timeout Clear")
                    command_clear_counter = 0
                    if packet_id == self.id:
                        print("Retry")
                        self.ser.write([0x00, 0xea, self.id, packet_command, 0, 0, 255])

                if command_clear_counter >= 120:
                    print("Command Timeout Clear")
                    print("Port Reset")
                    command_clear_counter = 0
                    self.ser.close()
                    time.sleep(10)
                    self.ser.open()
            else:
                command_clear_counter = 0
                print(ch)
                if packet_type == self.PACKET_HEADER:
                    if ch[0] == 0xea:
                        packet_type = self.PACKET_ID
                        print("PACKET_ID")
                elif packet_type == self.PACKET_ID:
                    packet_id = ch[0]
                    packet_type = self.PACKET_COMMAND
                elif packet_type == self.PACKET_COMMAND:
                    packet_command = ch[0]
                    packet_type = self.PACKET_LENGTH_H
                elif packet_type == self.PACKET_LENGTH_H:
                    packet_length = ch[0] * 256
                    packet_type = self.PACKET_LENGTH_L
                elif packet_type == self.PACKET_LENGTH_L:
                    packet_length = ch[0] + packet_length
                    if packet_length == 0:
                        print("Complete id:{},command:{},length:{}".format(packet_id, packet_command, packet_length))
                        packet_type = self.PACKET_HEADER
                        if packet_id == self.id:
                            callback_data(self.write, packet_command, packet_length, None)
                    else:
                        packet_array = []
                        packet_already_length = 0
                        packet_type = self.PACKET_DATA
                elif packet_type == self.PACKET_DATA:
                    packet_array.append(ch[0])
                    packet_already_length += 1
                    if packet_already_length == packet_length:
                        print("Complete id:{},command:{},length:{}".format(packet_id, packet_command, packet_length))
                        packet_type = self.PACKET_HEADER
                        if packet_id == self.id:
                            callback_data(self.write, packet_command, packet_length, packet_array)
