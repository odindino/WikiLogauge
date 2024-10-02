import struct
import sys,os
from PyQt6 import QtWidgets, uic, QtCore, QtTest
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
from time import time, sleep

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        uic.loadUi("EntryLockGaugeReader.ui", self)
        # 設定QStatusBar
        self.status = self.statusBar()
        self.status.showMessage('Welcome!', msecs=1000)
        # Load the UI Page by PyQt6
        self.setWindowTitle("WRHGauge.")
        self.timer = QtCore.QTimer()
        if not os.path.exists(self.lineEdit_savepath.text()):
            self.logfile = open(self.lineEdit_savepath.text(), 'a', newline='')
            self.writer.writerow(['time'+'\t'+'pressure'])
            self.logfile.close()
        self.gaugevalue = [[0.,0.]]
        self.addData = False
        self.pressure = 1000

        # 搜尋所有串列埠
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_list.addItem(port.device)

        mplblock = self.verticalLayout_mpl
        dynamic_canvas = FigureCanvas(Figure())
        mplblock.addWidget(NavigationToolbar(dynamic_canvas, self))
        mplblock.addWidget(dynamic_canvas)

        self._dynamicPressure_ax = dynamic_canvas.figure.subplots()
        dynamic_canvas.figure.subplots_adjust(left=0.12, right=0.86, top=0.95, bottom=0.2)
        self._dynamicPressure_ax.set_xticklabels(self._dynamicPressure_ax.get_xticks(), rotation = 15)
        self._dynamicPressure_ax.set_xlabel('Time')
        self._dynamicPressure_ax.set_ylabel('Pressure(mbar)')
        self._dynamicPressure_ax.xaxis.set_major_locator(plt.MaxNLocator(5))
        self._dynamicPressure_ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y/%m/%d %H:%M:%S"))
        self._line, = self._dynamicPressure_ax.plot([], [], color = 'b', label = 'Pressure (mBar)')
        self._dynamicPressure_ax.legend(loc='upper left')
        self.timelist = []
        self.pressurelist = []

    # Signals
        self.pushButton_start.clicked.connect(self.start)
        self.pushButton_clear.clicked.connect(self.clear)
        self.timer.timeout.connect(self.update)
        self.comboBox_dynamic_or_log.currentIndexChanged.connect(self.show_log)

    # Slot
    def start(self):
        try:
             # 讀取 serial port
            port = self.port_list.currentText()
            self.status.showMessage('Open Serial...', msecs=1000)
            self.port = serial.Serial(port, 9600, timeout=0.1)
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
        self.pressurelist = self.pressurelist[-3:]

    def update(self):
        self.read_gauge_pressure()
        self.updateDatetime()
        self.label_pressure.setText(str(self.pressure))
        self.label_time.setText(self.timeString)
        self.timeString = mdates.datestr2num(self.timeString)
        if self.addData == False:
            return
        self.pressurelist.append(self.pressure)
        self.timelist.append(self.timeString)
        if self.comboBox_dynamic_or_log.currentText() == 'Dynamic Data':
            self.update_ax()
        else:
            return
    
    def update_ax(self):
        self._line.set_data(self.timelist, self.pressurelist)
        self._dynamicPressure_ax.set_ylim(0.95*min(self.pressurelist), (1.05*max(self.pressurelist)))
        if len(self.pressurelist)>1800:
            self.timelist = self.timelist[-1800:]
            self.pressurelist = self.Fpressurelist[-1800:]
        if len(self.pressurelist)>1:
            self._dynamicPressure_ax.set_xlim(self.timelist[0], self.timelist[-1])
        self._line.figure.canvas.draw()

    def read_gauge_pressure(self):
        # port = self.port_list.currentText()
        # self.gauge = serial.Serial(port, 9600, timeout=0.1)
        command = '?V752'
        try:
            if self.port.isOpen():
                self.port.write((command+'\r').encode('ascii'))
                QtTest.QTest.qWait(100)
                return_string = self.port.read_all().decode('ascii', errors='ignore')
                if not return_string[1:5] == command[1:]: 
                    raise IOError
                if ';' in return_string:
                    pressure = return_string[6:return_string.index(';')]
                    self.pressure = float(pressure)
        except:
            return

    def updateDatetime(self):
        now = QtCore.QDateTime.currentDateTime()
        self.timeString = now.toString("yyyy/MM/dd hh:mm:ss")
        # self.timeString = now.toString("hh:mm:ss")
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
        self.pressurelist = self.pressurelist[:-60]+self.pressurelist[-1:]
    def reduceMinute(self):
        self.timelist = self.timelist[:-60]+self.timelist[-1:]
        # self.PREpressurelist = self.PREpressurelist[:-60]+self.PREpressurelist[-1:]
        self.pressurelist = self.pressurelist[:-60]+self.pressurelist[-1:]

    def SaveLog(self):
        self.status.showMessage('Saveing Log...', msecs=1000)
        self.logfile = open(self.lineEdit_savepath.text(), 'a', newline='')
        self.writer = csv.writer(self.logfile, delimiter='\t')
        self.writer.writerow([self.timeString, '{:.2e}'.format(self.pressure)])
        self.logfile.close()

    def show_log(self):
        if self.comboBox_dynamic_or_log.currentText() == 'Log Data':
            timeloglist = []
            pressureloglist = []
            # 打開CSV檔案進行讀取
            with open('Ion Gauge Pressure Log.csv', 'r') as file:
                reader = csv.reader(file, delimiter='\t')  # 假設CSV檔案的字段已制表符分隔
                # 逐行讀取數據
                for row in reader:
                    timeString = row[0]
                    timeString = mdates.datestr2num(timeString)
                    timeloglist.append(timeString)
                    pressureloglist.append(float(row[1]))
            self._line.set_data(timeloglist, pressureloglist)
            self._dynamicPressure_ax.set_ylim(0.95*min(pressureloglist), (1.05*max(pressureloglist)))
            self._dynamicPressure_ax.set_xlim(timeloglist[0], timeloglist[-1])
            self._line.figure.canvas.draw()
        else:
            self.update_ax()

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
