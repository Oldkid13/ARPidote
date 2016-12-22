#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import struct
import binascii
import mainwindow
import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QListWidget, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon
import os


class ARPPoisoningDetector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = mainwindow.Ui_MainWindow()
        self.ui.setupUi(self)
        self.init_detector()

    def init_detector(self):
        self.source_mac = ""
        self.source_ip = ""
        self.dest_mac = ""
        self.dest_ip = ""
        self.raw_socket = self.create_socket()
        self.arp_map = dict()
        self.ui.StartDetect.clicked.connect(self.start_detector)

        self.packet_receiver = PacketReceiver()
        self.packet_receiver.packetsignal.connect(self.handle_packet)

        self.ui.statusBar.showMessage("Basladi", 1500)

    def ethernet_packet(self, packet):
        ethernet_header = packet[0][0:14]
        return struct.unpack("!6s6s2s", ethernet_header)

    def start_detector(self):
        self.packet_receiver.start()

    def handle_packet(self, packet):
        ethernet_packet = self.ethernet_packet(packet)
        arp_packet = self.arp_packet(packet)
        self.split_arp_packet(arp_packet)
        if ethernet_packet[2] == b'\x08\x06':
            self.print_arp_details(arp_packet)
            self.check_poison()

    def arp_packet(self, packet):
        arp_header = packet[0][14:42]
        return struct.unpack("2s2s1s1s2s6s4s6s4s", arp_header)

    def check_poison(self):
        if self.source_mac in self.arp_map:
            if self.arp_map[self.source_mac] == self.source_ip:
                self.ui.statusBar.showMessage(self.source_mac + "zaten var.", 1500)
            else:
                self.ui.statusBar.showMessage(" zehirleniyoruz !!!", 1500)
        else:
            self.arp_map[self.source_mac] = (self.source_ip)
            self.ui.statusBar.showMessage(self.source_mac + "olusturuldu.", 1500)

    def is_arp_packet(self, ethernet_packet):
        return ethernet_packet[2] != '\x08\x06'

    def create_socket(self):
        return socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))

    def split_arp_packet(self, arp_packet):
        self.source_mac = self.get_source_mac(arp_packet)
        self.source_ip = self.get_source_ip(arp_packet)
        self.dest_mac = self.get_dest_mac(arp_packet)
        self.dest_ip = self.get_dest_ip(arp_packet)

    def get_source_mac(self, arp_packet):
        return binascii.hexlify(arp_packet[5]).decode("utf-8")

    def get_source_ip(self, arp_packet):
        return str(socket.inet_ntoa(arp_packet[6]))

    def get_dest_mac(self, arp_packet):
        return binascii.hexlify(arp_packet[7]).decode("utf-8")

    def get_dest_ip(self, arp_packet):
        return str(socket.inet_ntoa(arp_packet[8]))

    def print_arp_details(self, arp_packet):
        output = ""
        output += "Source MAC: " + self.get_source_mac(arp_packet) + "\n"
        output += "Source IP : " + self.get_source_ip(arp_packet) + "\n"
        output += "Dest MAC  : " + self.get_dest_mac(arp_packet) + "\n"
        output += "Dest IP   : " + self.get_dest_ip(arp_packet) + "\n"
        output += "*************************************************\n\n"
        self.ui.listWidget.addItem(output)


class PacketReceiver(QThread):
    packetsignal = pyqtSignal(tuple)

    def __init__(self):
        QThread.__init__(self)
        self.raw_socket = self.create_socket();

    def create_socket(self):
        return socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))

    def run(self):
        while True:
            self.packetsignal.emit(self.raw_socket.recvfrom(2048))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myapp = ARPPoisoningDetector()
    # myapp.setWindowIcon(QIcon(dirs["app_icon"]))
    myapp.show()
    sys.exit(app.exec_())
