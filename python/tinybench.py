from functools import partial
from ctypes import alignment
from operator import truediv
from re import L
import sys
from typing_extensions import Self
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QCheckBox, QPushButton, QLineEdit, QLabel, QApplication, QWidget, QRadioButton, QButtonGroup, QComboBox, QTextEdit, QFrame
from PyQt5.QtCore import QThread, pyqtSignal
from teensy_server_driver import teensy_server_driver
import time
import threading
import random

# class WorkerThread(QThread):
    # def run(self):
    #     for i in range(4):
    #         a = random.randint(0,1)
    #         print(a)
    #         time.sleep(0.5)

class CollapsibleBox(QtWidgets.QWidget):
    def __init__(self, title="", parent=None):
        super(CollapsibleBox, self).__init__(parent)

        self.toggle_button = QtWidgets.QToolButton(
            text=title, checkable=True, checked=False
        )
        # self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        self.toggle_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonTextBesideIcon
        )
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow)
        self.toggle_button.pressed.connect(self.on_pressed)

        self.toggle_animation = QtCore.QParallelAnimationGroup(self)

        self.content_area = QtWidgets.QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.content_area.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        # self.content_area.setStyleSheet("border: none;")

        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)


        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self.content_area, b"maximumHeight")
        )

    @QtCore.pyqtSlot()
    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(
            QtCore.Qt.DownArrow if not checked else QtCore.Qt.RightArrow
        )
        self.toggle_animation.setDirection(
            QtCore.QAbstractAnimation.Forward
            if not checked
            else QtCore.QAbstractAnimation.Backward
        )
        self.toggle_animation.start()

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        collapsed_height = (
            self.sizeHint().height() - self.content_area.maximumHeight()
        )
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)

class repeatTimer():
    timerRunning = False
    def repeat_every (self, interval, worker_func, iterations = 0):
        self.timerRunning = True
        self.start(interval, worker_func, iterations)

    def start(self, interval, worker_func, iterations = 0):
        if (self.timerRunning) & (iterations != 1):
            self.timerInst = threading.Timer (
              interval, self.start,
              [interval, worker_func, 0 if iterations == 0 else iterations-1]
            )
            self.timerInst.start()

        # this 'if' stops the last update from running after timer is stopped
        if (self.timerRunning):
            thread = threading.Thread(target = worker_func)
            thread.start()

    def stop(self):
        self.timerRunning = False

class Window(QWidget):
    
    # Timers, used for repeated polling of ADC and GPIO
    adc_timer = repeatTimer()
    gpio_timer = repeatTimer()

    # Threads, used to perform Teensy comms in background threads
    adc_worker_thread = threading.Thread()
    gpio_worker_thread = threading.Thread()
    dac_worker_thread = threading.Thread()
    
    # 1-2 seconds is about as fast as it currently can go
    gpio_minimum_update_rate = 2.0
    adc_minimum_update_rate = 2.0

    # signals used by worker threads to notify main thread to update GUI
    gpio_update_signal = pyqtSignal(int, bool)
    adc_update_signal = pyqtSignal(int, float)

    adc_check_boxes = []
    adc_aliases = []
    adc_33v_radios = []
    adc_50v_radios = []
    adc_radio_groups = []
    adc_voltages = []
    
    gpio_check_boxes = []
    gpio_aliases = []
    gpio_btns = []
    gpio_radio_groups = []
    gpio_read_radios = []
    gpio_write_radios = []

    teensy = teensy_server_driver()
    blue  = "#7badce"
    green = "#98db77"
    red = "#e37f71"

    btn_style_green = "border-style: outset; border-width: 1px; border-radius : 5px; border-color : black; padding : 4px ; background-color : "+green+"; color : black;"    
    btn_style_red =   "border-style: outset; border-width: 1px; border-radius : 5px; border-color : black; padding : 4px ; background-color : "+red+"; color : black;"    

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Teensy 3.2 Dev Platform")

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(mainLayout)

        ##########################################################################################
        ##########################################################################################
        ####  I2C GUI

        boxI2C = CollapsibleBox("I2C")
        mainLayout.addWidget(boxI2C)
        gridI2C = QtWidgets.QGridLayout()
        gridI2C.setColumnStretch(0,0)
        gridI2C.setColumnStretch(1,0)
        gridI2C.setColumnStretch(2,1)
        gridI2C.setColumnStretch(3,0)
        gridI2C.setColumnStretch(4,1)
        gridI2C.setColumnStretch(5,0)
        gridI2C.setColumnStretch(6,0)
        gridI2C.setColumnStretch(7,0)
        gridI2C.setColumnStretch(8,0)

        new_btn = QLabel("Baud Rate")
        new_btn.setStyleSheet("border-style: none; padding : 4px ; background-color : #f4f4f4; color : black;")
        new_btn.setAlignment(QtCore.Qt.AlignRight)
        new_btn.setMinimumWidth(100)
        gridI2C.addWidget(new_btn, 0, 0, QtCore.Qt.AlignTop)

        I2CBaudRate = QComboBox()
        I2CBaudRate.addItem("100kHz")
        I2CBaudRate.addItem("400kHz")
        I2CBaudRate.addItem("1MHz")
        I2CBaudRate.setCurrentIndex(0)
        gridI2C.addWidget(I2CBaudRate, 0, 1, QtCore.Qt.AlignTop)


        ##### SCRIPT 1 #####

        self.I2CScript1Execute = QPushButton("Execute")
        self.I2CScript1Execute.setMaximumWidth(100)
        self.I2CScript1Execute.setStyleSheet(self.btn_style_red) 
        self.I2CScript1Execute.clicked.connect(partial(self.i2c_execute_script,1))
        gridI2C.addWidget(self.I2CScript1Execute, 1, 0)

        I2CAlias1 = QLineEdit()
        I2CAlias1.setText("Setup MAX5815 DAC")
        I2CAlias1.setAlignment(QtCore.Qt.AlignLeft)
        I2CAlias1.setStyleSheet("border-style: none; padding : 4px ; background-color : #ffffff; color : black;")
        I2CAlias1.setMaximumHeight(100)
        I2CAlias1.setMaximumWidth(150)
        gridI2C.addWidget(I2CAlias1, 1, 1, QtCore.Qt.AlignVCenter)

        lbl1a = QLabel()
        lbl1a.setText("Script 1\n[F1]")
        lbl1a.setAlignment(QtCore.Qt.AlignRight)
        lbl1a.setStyleSheet("border-style: none; padding : 4px ; background-color : #f4f4f4; color : black;")
        lbl1a.setAlignment(QtCore.Qt.AlignRight)
        lbl1a.setMaximumHeight(50)
        lbl1a.setMaximumWidth(75)
        gridI2C.addWidget(lbl1a, 1, 2, QtCore.Qt.AlignTop)

        self.I2CScript1 = QTextEdit()
        self.I2CScript1.setPlainText("BeginTx 31\nWrite 0b01010001 0b00000000 0b00000000\nWrite 0b01110111 0b00000000 0b00000000\nEndTx\nDelay 50")
        self.I2CScript1.setStyleSheet("border-style: none; padding : 4px ; background-color : #ffffff; color : black;")
        self.I2CScript1.setAlignment(QtCore.Qt.AlignLeft)
        self.I2CScript1.setMaximumHeight(80)
        gridI2C.addWidget(self.I2CScript1, 1, 3, QtCore.Qt.AlignTop)

        lbl1b = QLabel()
        lbl1b.setText("Response")
        lbl1b.setStyleSheet("border-style: none; padding : 4px ; background-color : #f4f4f4; color : black;")
        lbl1b.setAlignment(QtCore.Qt.AlignRight)
        lbl1b.setMaximumHeight(60)
        lbl1b.setMaximumWidth(100)
        gridI2C.addWidget(lbl1b, 1, 4, QtCore.Qt.AlignTop)

        self.I2CResponse1 = QTextEdit()
        self.I2CResponse1.setPlainText("")
        self.I2CResponse1.setStyleSheet("border-style: none; padding : 4px ; background-color : #ffffff; color : black;")
        self.I2CResponse1.setAlignment(QtCore.Qt.AlignLeft)
        # txtScript2.setMaximumWidth(250)
        self.I2CResponse1.setMaximumHeight(80)
        self.I2CResponse1.setReadOnly(True)
        gridI2C.addWidget(self.I2CResponse1, 1, 5, QtCore.Qt.AlignTop)


        ##### SCRIPT 2 #####

        self.I2CScript2Execute = QPushButton("Execute")
        self.I2CScript2Execute.setMaximumWidth(100)
        self.I2CScript2Execute.setStyleSheet(self.btn_style_red) 
        self.I2CScript2Execute.clicked.connect(partial(self.i2c_execute_script,2))
        gridI2C.addWidget(self.I2CScript2Execute, 2, 0)

        I2CAlias2 = QLineEdit()
        I2CAlias2.setText("Read MAX5815 Vref")
        I2CAlias2.setAlignment(QtCore.Qt.AlignLeft)
        I2CAlias2.setStyleSheet("border-style: none; padding : 4px ; background-color : #ffffff; color : black;")
        I2CAlias2.setMaximumHeight(100)
        I2CAlias2.setMaximumWidth(150)
        gridI2C.addWidget(I2CAlias2, 2, 1, QtCore.Qt.AlignVCenter)

        lbl2a = QLabel()
        lbl2a.setText("Script 2\n[F2]")
        lbl2a.setAlignment(QtCore.Qt.AlignRight)
        lbl2a.setStyleSheet("border-style: none; padding : 4px ; background-color : #f4f4f4; color : black;")
        lbl2a.setAlignment(QtCore.Qt.AlignRight)
        lbl2a.setMaximumHeight(50)
        lbl2a.setMaximumWidth(75)
        gridI2C.addWidget(lbl2a, 2, 2, QtCore.Qt.AlignTop)

        self.I2CScript2 = QTextEdit()
        self.I2CScript2.setPlainText("BeginTx 31\nWrite 0b01010001\nEndTx")
        self.I2CScript2.setStyleSheet("border-style: none; padding : 4px ; background-color : #ffffff; color : black;")
        self.I2CScript2.setAlignment(QtCore.Qt.AlignLeft)
        self.I2CScript2.setMaximumHeight(80)
        gridI2C.addWidget(self.I2CScript2, 2, 3, QtCore.Qt.AlignTop)

        lbl2b = QLabel()
        lbl2b.setText("Response")
        lbl2b.setStyleSheet("border-style: none; padding : 4px ; background-color : #f4f4f4; color : black;")
        lbl2b.setAlignment(QtCore.Qt.AlignRight)
        lbl2b.setMaximumHeight(60)
        lbl2b.setMaximumWidth(100)
        gridI2C.addWidget(lbl2b, 2, 4, QtCore.Qt.AlignTop)

        self.I2CResponse2 = QTextEdit()
        self.I2CResponse2.setPlainText("")
        self.I2CResponse2.setStyleSheet("border-style: none; padding : 4px ; background-color : #ffffff; color : blac;k")
        self.I2CResponse2.setAlignment(QtCore.Qt.AlignLeft)
        # txtScript2.setMaximumWidth(250)
        self.I2CResponse2.setMaximumHeight(80)
        self.I2CResponse2.setReadOnly(True)
        gridI2C.addWidget(self.I2CResponse2, 2, 5, QtCore.Qt.AlignTop)


        ##### SCRIPT 3 #####

        self.I2CScript3Execute = QPushButton("Execute")
        self.I2CScript3Execute.setMaximumWidth(100)
        self.I2CScript3Execute.setStyleSheet(self.btn_style_red) 
        self.I2CScript3Execute.clicked.connect(partial(self.i2c_execute_script,3))
        gridI2C.addWidget(self.I2CScript3Execute, 3, 0)

        I2CAlias3 = QLineEdit()
        I2CAlias3.setText("Set MAX5815 to 2.500V")
        I2CAlias3.setAlignment(QtCore.Qt.AlignLeft)
        I2CAlias3.setStyleSheet("border-style: none; padding : 4px ; background-color : #ffffff; color : black;")
        I2CAlias3.setMaximumHeight(100)
        I2CAlias3.setMaximumWidth(150)
        gridI2C.addWidget(I2CAlias3, 3, 1, QtCore.Qt.AlignVCenter)

        lbl3a = QLabel()
        lbl3a.setText("Script 3\n[F2]")
        lbl3a.setAlignment(QtCore.Qt.AlignRight)
        lbl3a.setStyleSheet("border-style: none; padding : 4px ; background-color : #f4f4f4; color : black;")
        lbl3a.setAlignment(QtCore.Qt.AlignRight)
        lbl3a.setMaximumHeight(50)
        lbl3a.setMaximumWidth(75)
        gridI2C.addWidget(lbl3a, 3, 2, QtCore.Qt.AlignTop)

        self.I2CScript3 = QTextEdit()
        self.I2CScript3.setPlainText("BeginTx 31\nWrite 0b00101111 0b10011100 0b01000000\nEndTx")
        self.I2CScript3.setStyleSheet("border-style: none; padding : 4px ; background-color : #ffffff; color : black;")
        self.I2CScript3.setAlignment(QtCore.Qt.AlignLeft)
        self.I2CScript3.setMaximumHeight(80)
        gridI2C.addWidget(self.I2CScript3, 3, 3, QtCore.Qt.AlignTop)

        lbl3b = QLabel()
        lbl3b.setText("Response")
        lbl3b.setStyleSheet("border-style: none; padding : 4px ; background-color : #f4f4f4; color : black;")
        lbl3b.setAlignment(QtCore.Qt.AlignRight)
        lbl3b.setMaximumHeight(60)
        lbl3b.setMaximumWidth(100)
        gridI2C.addWidget(lbl3b, 3, 4, QtCore.Qt.AlignTop)

        self.I2CResponse3 = QTextEdit()
        self.I2CResponse3.setPlainText("")
        self.I2CResponse3.setStyleSheet("border-style: none; padding : 4px ; background-color : #ffffff; color : black;")
        self.I2CResponse3.setAlignment(QtCore.Qt.AlignLeft)
        # txtScript2.setMaximumWidth(250)
        self.I2CResponse3.setMaximumHeight(80)
        self.I2CResponse3.setReadOnly(True)
        gridI2C.addWidget(self.I2CResponse3, 3, 5, QtCore.Qt.AlignTop)
        
        boxI2C.setContentLayout(gridI2C)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        mainLayout.addWidget(line)


        ##########################################################################################
        ##########################################################################################
        ####  SPI GUI

        boxSPI = CollapsibleBox("SPI")
        mainLayout.addWidget(boxSPI)
        gridSPI = QtWidgets.QGridLayout()
        gridSPI.setColumnStretch(0,0)
        gridSPI.setColumnStretch(1,0)
        gridSPI.setColumnStretch(2,0)
        gridSPI.setColumnStretch(3,0)
        gridSPI.setColumnStretch(4,0)
        gridSPI.setColumnStretch(5,0)
        gridSPI.setColumnStretch(6,0)
        gridSPI.setColumnStretch(7,0)
        gridSPI.setColumnStretch(8,0)
        gridSPI.setColumnStretch(9,1)

        new_btn = QLineEdit("CS Pin")
        new_btn.setStyleSheet("border-style: none; padding : 4px ; background-color : #f4f4f4; color : black;")
        new_btn.setAlignment(QtCore.Qt.AlignLeft)
        new_btn.setReadOnly(True)
        gridSPI.addWidget(new_btn, 0,0)

        SPIPin = QLineEdit("6")
        SPIPin.setAlignment(QtCore.Qt.AlignLeft)
        gridSPI.addWidget(SPIPin, 0,1)

        new_btn = QLineEdit("Baud Rate")
        new_btn.setStyleSheet("border-style: none; padding : 4px ; background-color : #f4f4f4; color : black;")
        new_btn.setAlignment(QtCore.Qt.AlignLeft)
        new_btn.setReadOnly(True)
        gridSPI.addWidget(new_btn, 1,0)

        SPIBaudRate = QComboBox()
        SPIBaudRate.addItem("100kHz")
        SPIBaudRate.addItem("400kHz")
        SPIBaudRate.addItem("1MHz")
        SPIBaudRate.setCurrentIndex(0)
        gridSPI.addWidget(SPIBaudRate, 1,1)

        new_btn = QLineEdit("Script 1 [F1]")
        new_btn.setStyleSheet("border-style: none; padding : 4px ; background-color : #f4f4f4; color : black;")
        new_btn.setAlignment(QtCore.Qt.AlignLeft)
        new_btn.setReadOnly(True)
        gridSPI.addWidget(new_btn, 2,0)

        txtScript1 = QLineEdit("Script 1")
        txtScript1.setStyleSheet("border-style: none; padding : 4px ; background-color : #f4f4f4; color : black;")
        txtScript1.setAlignment(QtCore.Qt.AlignLeft)
        txtScript1.setMaximumWidth(250)
        txtScript1.setReadOnly(True)
        gridSPI.addWidget(txtScript1, 2,1)

        new_btn = QLineEdit("Response")
        new_btn.setStyleSheet("border-style: none; padding : 4px ; background-color : #f4f4f4; color : black;")
        new_btn.setAlignment(QtCore.Qt.AlignLeft)
        new_btn.setReadOnly(True)
        gridSPI.addWidget(new_btn, 2,2)

        txtScript2 = QLineEdit("Script 1")
        txtScript2.setStyleSheet("border-style: none; padding : 4px ; background-color : #f4f4f4; color : black;")
        txtScript2.setAlignment(QtCore.Qt.AlignLeft)
        txtScript2.setMaximumWidth(250)
        txtScript1.setReadOnly(True)
        gridSPI.addWidget(txtScript2, 2,3)

        boxSPI.setContentLayout(gridSPI)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        mainLayout.addWidget(line)


        ##########################################################################################
        ##########################################################################################
        ####  ADC GUI

        boxADC = CollapsibleBox("ADC")
        mainLayout.addWidget(boxADC)

        gridADC = QtWidgets.QGridLayout()
        gridADC.setColumnStretch(0,0)
        gridADC.setColumnStretch(1,0)
        gridADC.setColumnStretch(2,0)
        gridADC.setColumnStretch(3,0)
        gridADC.setColumnStretch(4,0)
        gridADC.setColumnStretch(5,0)
        gridADC.setColumnStretch(6,0)
        gridADC.setColumnStretch(7,0)
        gridADC.setColumnStretch(8,0)
        gridADC.setColumnStretch(9,1)

        for i in range(8):
            if (i <=3):
                newCheck = QCheckBox("ADC{}".format(i))
            else:
                newCheck = QCheckBox("ADC{}".format(i+2))
            newCheck.setChecked(True)
            self.adc_check_boxes.append(newCheck)
            gridADC.addWidget(self.adc_check_boxes[i], i, 0)
        
            if (i <=3):
                self.adc_aliases.append(QLineEdit("Alias{}".format(i)))
            else:
                self.adc_aliases.append(QLineEdit("Alias{}".format(i+2)))
            self.adc_aliases[i].setMaximumWidth(75)
            gridADC.addWidget(self.adc_aliases[i], i,1)
        
            new_btn = QLineEdit("{}V".format(0.0))
            new_btn.setStyleSheet("border-style: outset; border-width: 1px; border-radius : 5px; border-color : black; padding : 4px ; background-color : "+self.blue+"; color : black;") 
            new_btn.setAlignment(QtCore.Qt.AlignRight)
            new_btn.setReadOnly(True)
            new_btn.setMaximumWidth(60)
            self.adc_voltages.append(new_btn)
            gridADC.addWidget(self.adc_voltages[i], i,2)

            adc_33v_radio = QRadioButton("3.3V")
            adc_33v_radio.setChecked(True)
            adc_50v_radio = QRadioButton("5.0V")
            adc_50v_radio.setChecked(False)
            self.adc_33v_radios.append(adc_33v_radio)
            self.adc_50v_radios.append(adc_50v_radio)
            btg_group = QButtonGroup()
            self.adc_radio_groups.append(btg_group)
            self.adc_radio_groups[i].addButton(self.adc_33v_radios[i], 1)
            self.adc_radio_groups[i].addButton(self.adc_50v_radios[i], 2)

            gridADC.addWidget(self.adc_33v_radios[i], i,3)
            gridADC.addWidget(self.adc_50v_radios[i], i,4)

        
        self.adc_update_once_btn = QPushButton("Update Now")
        self.adc_update_once_btn.setStyleSheet(self.btn_style_red) 
        gridADC.addWidget(self.adc_update_once_btn, 0, 5)
        self.adc_update_once_btn.clicked.connect(lambda: self.adc_update_once(self.adc_update_once_btn))

        self.adc_poll_button = QPushButton("Poll ADCs")
        self.adc_poll_button.setStyleSheet(self.btn_style_red) 

        self.adc_poll_button.clicked.connect(partial(self.toggle_adc_poll))
        self.adc_update_signal.connect(self.adc_update_gui)
        gridADC.addWidget(self.adc_poll_button, 0, 6)

        self.adc_poll_interval_btn = QLineEdit("1.0")
        self.adc_poll_interval_btn.setMaximumWidth(40)
        self.adc_poll_interval_btn.setAlignment(QtCore.Qt.AlignRight)
        self.adc_poll_interval_btn.setValidator(QtGui.QDoubleValidator(1.0, 1000.0, 1))
        gridADC.addWidget(self.adc_poll_interval_btn, 0, 7)

        gridADC.addWidget(QLabel("seconds"), 0,8)
        
        boxADC.setContentLayout(gridADC)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        mainLayout.addWidget(line)


        ##########################################################################################
        ##########################################################################################
        ####  DAC GUI

        boxDAC = CollapsibleBox("DAC")
        
        mainLayout.addWidget(boxDAC)

        gridDAC = QtWidgets.QGridLayout()
        gridDAC.setColumnStretch(0,0)
        gridDAC.setColumnStretch(1,0)
        gridDAC.setColumnStretch(2,0)
        gridDAC.setColumnStretch(3,0)
        gridDAC.setColumnStretch(4,0)
        gridDAC.setColumnStretch(5,1)

        DACAlias = QLineEdit("Alias")
        DACAlias.setStyleSheet("padding : 4px ; background-color : #f4f4f4; color : black;") 
        DACAlias.setMaximumWidth(75)
        gridDAC.addWidget(DACAlias, 0, 0, QtCore.Qt.AlignLeft)
    
        self.dac_update_once_btn = QPushButton("Update DAC")
        self.dac_update_once_btn.setStyleSheet(self.btn_style_red) 
        self.dac_update_once_btn.setMaximumWidth(100)
        gridDAC.addWidget(self.dac_update_once_btn, 0, 1, QtCore.Qt.AlignCenter)
        self.dac_update_once_btn.clicked.connect(lambda: self.dac_update_once(self.dac_update_once_btn))


        DACCode = QLabel()
        DACCode.setText("Code:\n(0-4095)")
        DACCode.setAlignment(QtCore.Qt.AlignRight)
        DACCode.setMinimumWidth(100)
        DACCode.setStyleSheet("border-style: none; padding : 4px ; background-color : #f4f4f4; color : black;")
        gridDAC.addWidget(DACCode, 0, 2, QtCore.Qt.AlignRight)

        self.DACCode = QLineEdit("1024")
        self.DACCode.setStyleSheet("padding : 4px ; background-color : #f4f4f4; color : black;") 
        # self.DACCode.setAlignment(QtCore.Qt.AlignLeft)
        self.DACCode.textChanged.connect(self.update_dac_vout_label)
        self.DACCode.setMaximumWidth(50)
        gridDAC.addWidget(self.DACCode, 0, 3, QtCore.Qt.AlignLeft)
    
        new_btn = QLabel()
        new_btn.setText("Vout:")
        # new_btn.setMaximumHeight(60)
        new_btn.setMinimumWidth(80)
        new_btn.setAlignment(QtCore.Qt.AlignRight)
        new_btn.setStyleSheet("border-style: none; padding : 4px ; background-color : #f4f4f4; color : black;")
        gridDAC.addWidget(new_btn, 0, 4, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)

        self.dac_vout_estimate = QLabel()
        self.update_dac_vout_label() # update label based on whatever is in the code text box
        # self.dac_vout_estimate.setMaximumHeight(60)
        self.dac_vout_estimate.setMaximumWidth(100)
        self.dac_vout_estimate.setAlignment(QtCore.Qt.AlignLeft)
        self.dac_vout_estimate.setStyleSheet("border-style: none; padding : 4px ; background-color : #f4f4f4; color : black;")
        gridDAC.addWidget(self.dac_vout_estimate, 0, 5, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
     
        boxDAC.setContentLayout(gridDAC)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        mainLayout.addWidget(line)


        ##########################################################################################
        ##########################################################################################
        ####  GPIO GUI

        boxGPIO = CollapsibleBox("GPIO")
        
        mainLayout.addWidget(boxGPIO)

        gridGPIO = QtWidgets.QGridLayout()
        gridGPIO.setColumnStretch(0,0)
        gridGPIO.setColumnStretch(1,0)
        gridGPIO.setColumnStretch(2,0)
        gridGPIO.setColumnStretch(3,0)
        gridGPIO.setColumnStretch(4,0)
        gridGPIO.setColumnStretch(5,0)
        gridGPIO.setColumnStretch(6,0)
        gridGPIO.setColumnStretch(7,0)
        gridGPIO.setColumnStretch(8,0)
        gridGPIO.setColumnStretch(9,1)

        for i in range(10):
            chk = QCheckBox("GPIO{}".format(i))
            chk.setChecked(True)
            self.gpio_check_boxes.append(chk)

            gridGPIO.addWidget(self.gpio_check_boxes[i], i, 0)
        
            new_alias = QLineEdit("Alias")
            new_alias.setMaximumWidth(75)
            new_alias.setStyleSheet("background-color : #ffffff;")
            self.gpio_aliases.append(new_alias)
            gridGPIO.addWidget(self.gpio_aliases[i], i,1)
        
            new_btn = QPushButton()
            new_btn.setText("False")
            new_btn.setStyleSheet(self.btn_style_red)
            new_btn.setMaximumWidth(75)
            new_btn.setMinimumWidth(75)
            self.gpio_btns.append(new_btn)
            self.gpio_btns[i].clicked.connect(partial(self.toggle_gpio_button,i))
            gridGPIO.addWidget(self.gpio_btns[i], i,2)

            read_radio = QRadioButton("Read")
            read_radio.setChecked(True)
            write_radio = QRadioButton("Write")
            write_radio.setChecked(False)
            self.gpio_read_radios.append(read_radio)
            self.gpio_write_radios.append(write_radio)
            btg_group = QButtonGroup()
            self.gpio_radio_groups.append(btg_group)
            self.gpio_radio_groups[i].addButton(self.gpio_read_radios[i], 1)
            self.gpio_radio_groups[i].addButton(self.gpio_write_radios[i], 2)

            gridGPIO.addWidget(self.gpio_read_radios[i], i,3)
            gridGPIO.addWidget(self.gpio_write_radios[i], i,4)
        
        self.gpio_update_once_btn = QPushButton("Update Now")
        self.gpio_update_once_btn.setStyleSheet(self.btn_style_red)
        self.gpio_update_once_btn.clicked.connect(lambda: self.gpio_update_once(self.gpio_update_once_btn))
        gridGPIO.addWidget(self.gpio_update_once_btn, 0, 5)

        self.GPIOPollEnable = QPushButton("Poll GPIOs")
        self.GPIOPollEnable.setStyleSheet(self.btn_style_red) 

        self.GPIOPollEnable.clicked.connect(partial(self.toggle_gpio_poll))
        self.gpio_update_signal.connect(self.gpio_update_gui)
        gridGPIO.addWidget(self.GPIOPollEnable, 0, 6)

        self.GPIOPollInterval = QLineEdit("1.0")
        self.GPIOPollInterval.setMaximumWidth(40)
        self.GPIOPollInterval.setAlignment(QtCore.Qt.AlignRight)
        self.GPIOPollInterval.setValidator(QtGui.QDoubleValidator(self.gpio_minimum_update_rate, 1000.0, 1))
        gridGPIO.addWidget(self.GPIOPollInterval, 0, 7)

        gridGPIO.addWidget(QLabel("seconds"), 0,8)
        
        boxGPIO.setContentLayout(gridGPIO)


        print("\n########################")
        if (self.teensy.find_board()):
            print("Found Teensy Server " + self.teensy.com_port)
        else:
            print("Teensy Server not found")
        if (self.teensy.ping_board()):
            print("Ping successful")
        else:
            print("Ping not successful")

        teensy_version = self.teensy.get_fw_version()
        print("Firmware version = " + str(teensy_version, 'UTF-8'))

        print("########################\n")

    # TinyBench should only run one action at a time
    # busy() returns true if any worker thread is active, false otherwise
    def busy(self):
        if (self.adc_worker_thread.is_alive()):
            return True
        if (self.gpio_worker_thread.is_alive()):
            return True
        if (self.dac_worker_thread.is_alive()):
            return True
        return False

    def adc_update_once(self, btn):
        setofints = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        for i in setofints:
            self.teensy.ping_board()
            self.teensy.ping_board()
        return
        if (self.busy()):
            return
        thread = threading.Thread(target = self.flash_button_green(btn))
        thread.start()  
        self.adc_worker_thread = threading.Thread(target = self.adc_update_worker)
        self.adc_worker_thread.start()

    def dac_update_once(self, btn):
        if (self.busy()):
            return
        thread = threading.Thread(target = self.flash_button_green(btn))
        thread.start()
        self.dac_worker_thread = threading.Thread(target = self.dac_update_worker)
        self.dac_worker_thread.start()

    def gpio_update_once(self, btn):
        if (self.busy()):
            return
        thread = threading.Thread(target = self.flash_button_green(btn))
        thread.start()
        self.gpio_worker_thread = threading.Thread(target = self.gpio_update_worker)
        self.gpio_worker_thread.start()

    def toggle_adc_poll(self):
        if (self.adc_timer.timerRunning):
            self.adc_timer.stop()
            self.adc_poll_button.setStyleSheet(self.btn_style_red)
        else:
            if float(self.adc_poll_interval_btn.text()) < self.adc_minimum_update_rate:
                self.adc_poll_interval_btn.setText(str(self.adc_minimum_update_rate))
            interval = float(self.adc_poll_interval_btn.text())
            self.adc_timer.repeat_every (interval, lambda: self.adc_update_once(self.adc_update_once_btn))
            self.adc_poll_button.setStyleSheet(self.btn_style_green)

    def toggle_gpio_poll(self):
        if (self.gpio_timer.timerRunning):
            self.gpio_timer.stop()
            self.GPIOPollEnable.setStyleSheet(self.btn_style_red)
        else:
            if float(self.GPIOPollInterval.text()) < self.gpio_minimum_update_rate:
                self.GPIOPollInterval.setText(str(self.gpio_minimum_update_rate))
            interval = float(self.GPIOPollInterval.text())
            self.gpio_timer.repeat_every (interval, lambda: self.gpio_update_once(self.gpio_update_once_btn))
            self.GPIOPollEnable.setStyleSheet(self.btn_style_green)

    def adc_update_worker(self):
        i = 0
        while (i < len(self.adc_check_boxes)):
            if (self.adc_check_boxes[i].checkState()):
                if (self.adc_radio_groups[i].checkedButton() == self.adc_33v_radios[i]):
                    scale = 3.3
                else:
                    scale = 5.0
                    scale = 3.3 # ??? temporary, waiting on PCB fix
                channel = i
                if (i>=4):
                    channel += 2
                code = self.teensy.get_adc(channel)
                value = scale * code / (65535.0)
                self.adc_update_signal.emit(i, value)
                # print(str(i) + "val="+str(value))
            i = i + 1

    def dac_update_worker(self):
        val = int (self.DACCode.text())
        self.teensy.set_dac(val)

    def gpio_update_worker(self):
        i = 0
        while (i < len(self.gpio_check_boxes)):
            if (self.gpio_check_boxes[i].checkState()):
                if (self.gpio_radio_groups[i].checkedButton() == self.gpio_read_radios[i]):
                    value = self.teensy.get_gpio(i)
                    self.gpio_update_signal.emit(i, value)
                if (self.gpio_radio_groups[i].checkedButton() == self.gpio_write_radios[i]):
                    value = self.gpio_btns[i].text()
                    value = eval(value)
                    thread = threading.Thread(target = self.teensy.set_gpio(i, value))
                    thread.start()
            i = i + 1

    def adc_update_gui(self, i, value):
        txt = str.format('{0:.3f}V',value)
        self.adc_voltages[i].setText(txt)
        app.processEvents()

    def update_dac_vout_label(self):
        value = int(self.DACCode.text())
        if (value < 0):
            value = 0
            self.DACCode.setText(str(value))
        elif (value > 4095):
            value = 4095
            self.DACCode.setText(str(value))
        vdac_estimate = 3.296 * ( value / 4095.0)
        self.dac_vout_estimate.setText("{0:.3g}".format(vdac_estimate))
        app.processEvents()

    def gpio_update_gui(self, i, val):
        self.gpio_btns[i].setText(str(val))
        if (val):
            self.gpio_btns[i].setStyleSheet(self.btn_style_green)
        else:
            self.gpio_btns[i].setStyleSheet(self.btn_style_red)
        app.processEvents()

    def flash_button_green(self, btn):
        btn.setStyleSheet(self.btn_style_green)
        app.processEvents()
        time.sleep(0.35)
        btn.setStyleSheet(self.btn_style_red)
        app.processEvents()

    def toggle_gpio_button(self, channel):
        btn_group = self.gpio_radio_groups[channel]
        if (btn_group.checkedButton() == self.gpio_write_radios[channel]):
            btn = self.gpio_btns[channel]
            # val = self.text()
            val = eval(btn.text())
            if (val):
                btn.setStyleSheet(self.btn_style_red)
                btn.setText("False")
            else:
                btn.setStyleSheet(self.btn_style_green)
                btn.setText("True")
            app.processEvents()

    def i2c_execute_script(self, num):
        # print ("execute I2C script #" + str(num))
        if (num == 1):
            thread = threading.Thread(target = self.flash_button_green(self.I2CScript1Execute))
            thread.start()
            commands = str(self.I2CScript1.toPlainText().lower())
        elif (num == 2):
            thread = threading.Thread(target = self.flash_button_green(self.I2CScript2Execute))
            thread.start()
            commands = str(self.I2CScript2.toPlainText().lower())
        elif (num == 3):
            thread = threading.Thread(target = self.flash_button_green(self.I2CScript3Execute))
            thread.start()
            commands = str(self.I2CScript3.toPlainText().lower())
        else:
            print("tinybench.py i2c_execute_script(): shouldn't get here")
            return

        commands = commands.splitlines()

        for command in commands:
            command.strip("\r\n ")
            tokens = command.split()
            if (tokens[0] == 'delay'):
                delaytime = int(tokens[1]) / 1000
                time.sleep(delaytime)
            elif (tokens[0] == 'begintx'):
                addr = int(tokens[1])
                self.teensy.i2c_begin(addr)
            elif (tokens[0] == 'endtx'):
                self.teensy.i2c_end()
            elif (tokens[0] == 'write'):
                for token in tokens[1:]:
                    msg = bytearray()
                    if (token[0:2] == '0b'):
                        toke = token.replace('0b','')
                        msg2 = f'{int(toke[0:4],2):x}' + f'{int(toke[4:8],2):x}'
                    self.teensy.i2c_write_bytes(msg2)
            elif (tokens[0] == 'read'):
                addr = int(tokens[1])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    # window.setStyleSheet("background-color: #444444; color: #f4f4f4;")
    # window.setStyleSheet("QPushButton {border-style: outset; border-width: 1px; border-radius : 5px; border-color : #f4f4f4; padding : 4px ; background-color : #caf4ca; color : #f4f4f4;}")
    window.resize(1100, 800)
    # window.setStyleSheet("font-size: 12px; background-color: #888888;")
    window.show()
    sys.exit(app.exec_())