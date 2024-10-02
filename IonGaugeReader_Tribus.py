import struct
import sys,os
from PyQt6 import QtWidgets, uic, QtCore
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as FigureCanvas, 
    NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import serial
import serial.tools.list_ports
import csv
from decimal import Decimal
from time import time, sleep
from datetime import datetime

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        uic.loadUi("IonGaugeReader_Tribus.ui", self)
        # 設定QStatusBar
        self.status = self.statusBar()
        self.status.showMessage('Welcome!', msecs=1000)
        # Data Package [Device Address, Function Code(always 0x17), Reading Data(4 bytes), Writing Data(5+n bytes), CRC(2 bytes)]
        # CRC: use the massage bytes to calculate the CRC
        getINFID   =[0x01, 0x17, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0xB3, 0xB5]
        # getPREID   =[0x02, 0x17, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0xBC, 0xF1]
        getINFName =[0x01, 0x17, 0x00, 0x10, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0xB2, 0xB9]
        # getPREName =[0x02, 0x17, 0x00, 0x10, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0xBD, 0xFD]
        getINFGauge=[0x01, 0x17, 0x00, 0x98, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0xBB, 0x19]
        # getPREGauge=[0x02, 0x17, 0x00, 0x98, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0xB4, 0x5D]
        getINFTC = [0x01, 0x17, 0x00, 0xBA, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x38 , 0xD8]
        getINFTC = [0x01, 0x17, 0x00, 0x92, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3B , 0x66]
        # self.PREID = [getPREID]
        self.INFID = [getINFID]
        # self.PREName = [getPREName]
        self.INFName = [getINFName]
        # self.PREGauge = [getPREGauge]
        self.INFGauge = [getINFGauge]
        self.TC = [getINFTC]
        # self.PREgaugevalue = [[0.,0.]]
        self.INFgaugevalue = [[0.,0.]]
        self.TCvalue = [[0., 0.]]
        self.addData = False

        # Load the UI Page by PyQt6
        self.setWindowTitle("Ion Gauge Reader.")
        self.timer = QtCore.QTimer()
        if not os.path.exists(self.lineEdit_savepath.text()):
            self.logfile = open(self.lineEdit_savepath.text(), 'a', newline='')
            self.writer.writerow(['time'+'\t'+'INFpressure'])
            self.logfile.close()
            

        # 搜尋所有串列埠
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_list.addItem(port.device)

        mplblock = self.verticalLayout_mpl
        dynamic_canvas = FigureCanvas(Figure())
        mplblock.addWidget(NavigationToolbar(dynamic_canvas, self))
        mplblock.addWidget(dynamic_canvas)

        self._dynamicPressure_ax = dynamic_canvas.figure.subplots()
        self._dynamicTemperature_ax = self._dynamicPressure_ax.twinx()
        dynamic_canvas.figure.subplots_adjust(left=0.12, right=0.86, top=0.95, bottom=0.2)
        self._dynamicPressure_ax.set_xticklabels(self._dynamicPressure_ax.get_xticks(), rotation = 15)
        self._dynamicPressure_ax.set_xlabel('Time')
        self._dynamicPressure_ax.set_ylabel('Pressure(mbar)')
        self._dynamicTemperature_ax.set_ylabel('Temperature(°C)')
        self._dynamicPressure_ax.xaxis.set_major_locator(plt.MaxNLocator(5))
        self._dynamicPressure_ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y/%m/%d %H:%M:%S"))
        self._line, = self._dynamicPressure_ax.plot([], [], color = 'b', label = 'Pressure (mBar)')
        self._line2, = self._dynamicTemperature_ax.plot([],[], color ='r', label = 'Temperature (°C)')
        self._dynamicPressure_ax.legend(loc='upper left')
        self._dynamicTemperature_ax.legend(loc='upper right')
        self.timelist = []
        # self.PREpressurelist = []
        self.INFpressurelist = []
        self.temperaturelist = []
        # 創建三個空列表來儲存讀取數據
        timeloglist = []
        INFpressureloglist = []
        temperatureloglist = []

    # Signals
        self.pushButton_start.clicked.connect(self.start)
        self.pushButton_clear.clicked.connect(self.clear)
        self.timer.timeout.connect(self.update)
        self.comboBox_dynamic_or_log.currentIndexChanged.connect(self.show_log)

    # Slot
    def start(self):
        # # 開始記錄
        # self.pushButton_start.setDisabled(True)
        # # 讀取 serial port
        # port = self.port_list.currentText()
        # self.port = serial.Serial(port, 19200, timeout=0.1)
        # # 設定擷取數據的時間，實際會比設定的再多1秒
        # #self.timestep = int(self.lineEdit_timeinterval.text()) * 1000
        # self.timestep = 1000
        # # 啟動QT計時器
        # self.timer.start(self.timestep)
        # if self.port.isOpen():
        #     self.status.showMessage('Open Serial...', msecs=1000)
        #     ID=self.INFID
        #     Name=self.INFName
        #     for i in range(len(ID)):
        #         self.port.write(ID[i])
        #         sleep(0.1)
        #         tmp=self.port.read_all()
        #         if len(tmp)>0 and tmp[3:6].decode("utf-8")=="PVC":
        #             self.port.write(Name[i])
        #             sleep(0.1)
        #             tmpName=self.port.readall()
        try:
             # 讀取 serial port
            port = self.port_list.currentText()
            self.port = serial.Serial(port, 9600, timeout=0.1)
            self.status.showMessage('Open Serial...', msecs=1000)
            ID=self.INFID
            Name=self.INFName
            for i in range(len(ID)):
                self.port.write(ID[i])
                sleep(0.1)
                tmp=self.port.read_all()
                print('tmp =')
                print(tmp)
                if len(tmp)>0 and tmp[3:6].decode("utf-8")=="PVC":
                    self.port.write(Name[i])
                    sleep(0.1)
                    tmpName=self.port.readall()
                print('tmpName =')
                print(tmpName)
            self.pushButton_start.setDisabled(True)
            # 設定擷取數據的時間，實際會比設定的再多1秒
            #self.timestep = int(self.lineEdit_timeinterval.text()) * 1000
            self.timestep = 1000
            # 啟動QT計時器
            self.timer.start(self.timestep)
        except Exception as e:
            self.status.showMessage('Failed in Open Serial', msecs=1000)
        
    def clear(self):
        self.timelist = self.timelist[-3:]
        # self.PREpressurelist = self.PREpressurelist[-3:]
        self.INFpressurelist = self.INFpressurelist[-3:]
        self.temperaturelist = self.temperaturelist[-3:]
        #self.start()
        self.update_ax()

    def update(self):
        self.read_gauge_pressure()
        # PREgaugevalue = self.PREgaugevalue[0][1]
        try:
            INFgaugevalue = self.INFgaugevalue[0][1]
        except Exception as e:
            INFgaugevalue = self.INFpressurelist[-1]
        # PREfilamentCurrent = "{:.1f}".format(self.PREgaugevalue[0][0])
        INFfilamentCurrent = "{:.1f}".format(self.INFgaugevalue[0][0])
        # if self.current_index == 0:
            # filamentCurrent = str(PREfilamentCurrent)
        # else:
        filamentCurrent = str(INFfilamentCurrent)
        self.status.showMessage('Filament = '+filamentCurrent+'mA', msecs=1000)
        try:
            temperature = self.TCvalue[0][0]
        except Exception as e:
            temperature = self.temperaturelist[-1]
        self.updateDatetime()
        # self.PREpressure = float(PREgaugevalue)
        self.INFpressure = float(INFgaugevalue)
        self.temperature = float(temperature)
        # if self.current_index == 0:
            # pressure = '%.2E' % self.PREpressure+' mBar'
            #self.label_pressure.setText('%.2E' % self.PREpressure)
        # else:
        pressure = '%.2E' % self.INFpressure+' mBar'
            #self.label_pressure.setText('%.2E' % self.INFpressure)
        self.label_pressure.setText(pressure)
        #self.lineEdit_time.setText(self.timeString)
        self.label_time.setText(self.timeString)
        #self.writer.writerow([self.timeString, self.pressure])
        self.timeString = mdates.datestr2num(self.timeString)
        # self.PREpressurelist.append(self.PREpressure)
        if self.addData == False:
            return
        self.INFpressurelist.append(self.INFpressure)
        self.temperaturelist.append(self.temperature)
        self.timelist.append(self.timeString)
        # if self.current_index == 0:
        #     self._line.set_data(self.timelist, self.PREpressurelist)
        #     self._dynamicPressure_ax.set_ylim(0.95*min(self.PREpressurelist), (1.05*max(self.PREpressurelist)))
        # else:
        if self.comboBox_dynamic_or_log.currentText() == 'Dynamic Data':
            self.update_ax()
        else:
            return

    def update_ax(self):
        self._line.set_data(self.timelist, self.INFpressurelist)
        self._dynamicPressure_ax.set_ylim(0.95*min(self.INFpressurelist), (1.05*max(self.INFpressurelist)))
        self._line2.set_data(self.timelist, self.temperaturelist)
        if len(self.INFpressurelist)>1800:
            self.timelist = self.timelist[-1800:]
            self.INFpressurelist = self.INFpressurelist[-1800:]
            self.temperaturelist = self.temperaturelist[-1800:]
        if len(self.INFpressurelist)>1:
            self._dynamicPressure_ax.set_xlim(self.timelist[0], self.timelist[-1])
            self._dynamicTemperature_ax.relim()
            self._dynamicTemperature_ax.autoscale()
        self._line.figure.canvas.draw()
        self._line2.figure.canvas.draw()

    def read_gauge_pressure(self):
        # PREGauge = self.PREGauge
        # for i in range(len(PREGauge)):
        #     self.port.write(PREGauge[i])
        #     sleep(0.05)
        #     tmpGauge = self.port.read_all()
        #     self.PREgaugevalue[i]=struct.unpack('2f',tmpGauge[3:11])
        # sleep(0.1)
        INFGauge = self.INFGauge
        for i in range(len(INFGauge)):
            self.port.write(INFGauge[i])
            sleep(0.1)
            tmpGauge = self.port.read_all()
            self.INFgaugevalue[i]=struct.unpack('2f',tmpGauge[3:11])
        sleep(0.1)
        for i in range(len(self.TC)):
            self.port.write(self.TC[i])
            sleep(0.1)
            tmpTC = self.port.read_all()
            self.TCvalue[i]=struct.unpack('2f',tmpTC[3:11])

    def updateDatetime(self):
        now = QtCore.QDateTime.currentDateTime()
        self.timeString = now.toString("yyyy/MM/dd hh:mm:ss")
        if now.time().second() %10 == 0:
            self.addData = True
        else:
            self.addData = False
            # self.reduceSecond()
        if now.time().minute() == 0 and self.AutoSaveLog.isChecked() and now.time().second() == 0:
            self.SaveLog()
            # self.reduceMinute()

    def reduceSecond(self):
        self.timelist = self.timelist[:-60]+self.timelist[-1:]
        # self.PREpressurelist = self.PREpressurelist[:-60]+self.PREpressurelist[-1:]
        self.INFpressurelist = self.INFpressurelist[:-60]+self.INFpressurelist[-1:]
        self.temperaturelist = self.temperaturelist[:-60]+self.temperaturelist[-1:]
    def reduceMinute(self):
        self.timelist = self.timelist[:-60]+self.timelist[-1:]
        # self.PREpressurelist = self.PREpressurelist[:-60]+self.PREpressurelist[-1:]
        self.INFpressurelist = self.INFpressurelist[:-60]+self.INFpressurelist[-1:]
        self.temperaturelist = self.temperaturelist[:-60]+self.temperaturelist[-1:]

    def SaveLog(self):
        self.status.showMessage('Saveing Log...', msecs=1000)
        self.logfile = open(self.lineEdit_savepath.text(), 'a', newline='')
        self.writer = csv.writer(self.logfile, delimiter='\t')
        self.writer.writerow([self.timeString, '{:.2e}'.format(self.INFpressure), '{:.1f}'.format(self.temperature)])
        self.logfile.close()

    def show_log(self):
        if self.comboBox_dynamic_or_log.currentText() == 'Log Data':
            timeloglist = []
            INFpressureloglist = []
            temperatureloglist = []
            # 打開CSV檔案進行讀取
            with open('Ion Gauge Pressure Log.csv', 'r') as file:
                reader = csv.reader(file, delimiter='\t')  # 假設CSV檔案的字段已制表符分隔
                # 逐行讀取數據
                for row in reader:
                    timeString = row[0]
                    timeString = mdates.datestr2num(timeString)
                    timeloglist.append(timeString)
                    INFpressureloglist.append(float(row[1]))
                    try:
                        temperatureloglist.append(float(row[2]))
                    except Exception as e:
                         temperatureloglist.append(0)
            self._line.set_data(timeloglist, INFpressureloglist)
            self._dynamicPressure_ax.set_ylim(0.95*min(INFpressureloglist), (1.05*max(INFpressureloglist)))
            self._line2.set_data(timeloglist, temperatureloglist)
            self._dynamicPressure_ax.set_xlim(timeloglist[0], timeloglist[-1])
            self._dynamicTemperature_ax.relim()
            self._dynamicTemperature_ax.autoscale()
            self._line.figure.canvas.draw()
            self._line2.figure.canvas.draw()
        else:
            self.update_ax()

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
