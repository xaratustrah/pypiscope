"""
A client/server code for Raspberry Pi ADC input

Xaratustrah@GitHUB
2016

"""
# force Matplotlib to use PyQt5 backend, call before importing pyplot and backends!
from matplotlib import use

use("Qt5Agg")
from PyQt5.QtWidgets import QMainWindow, QDialog, QInputDialog, QLineEdit
from PyQt5.QtCore import Qt, QCoreApplication, QThread, QTimer
from mainwindow_ui import Ui_MainWindow
from aboutdialog_ui import Ui_AbooutDialog
from zmq_listener import ZMQListener
from ipaddress import ip_address
from version import __version__


class mainWindow(QMainWindow, Ui_MainWindow):
    """
    The main class for the GUI window
    """

    def __init__(self):
        """
        The constructor and initiator.
        :return:
        """
        # initial setup
        super(mainWindow, self).__init__()
        self.setupUi(self)
        self.thread = QThread()

        self.connected = False

        # Connect signals
        self.connect_signals()

    def on_push_button_clicked(self):
        if self.pushButton.isChecked():

            try:
                host = str(ip_address(self.lineEdit_host.text()))
                port = self.lineEdit_port.text()
                if not port.isdigit():
                    raise ValueError

            except(ValueError):
                self.pushButton.setChecked(False)
                self.show_message('Please enter valid numeric IP address and port number.')
                return

            self.zeromq_listener_10001 = ZMQListener(host, port, '10001')
            self.zeromq_listener_10001.moveToThread(self.thread)
            self.zeromq_listener_10001.message.connect(self.signal_received_10001)
            self.zeromq_listener_10001.err_msg.connect(self.show_message)

            self.thread.started.connect(self.zeromq_listener_10001.loop)
            self.thread.start()

            self.pushButton.setText('Stop')
            self.show_message('Connected to server: {}:{}'.format(host, port))
        else:
            self.zeromq_listener_10001.running = False
            self.thread.terminate()
            self.pushButton.setText('Start')
            self.show_message('Disconnected.')

    def connect_signals(self):
        """
        Connects signals.
        :return:
        """

        # Action about and Action quit will be shown differently in OSX

        self.actionAbout.triggered.connect(self.show_about_dialog)
        self.actionQuit.triggered.connect(self.shutdown)
        self.pushButton.clicked.connect(self.on_push_button_clicked)

    def shutdown(self):
        self.zeromq_listener_10001.running = False
        self.thread.terminate()
        self.thread.quit()
        self.thread.wait()
        QCoreApplication.instance().quit()

    def signal_received_10001(self, message):
        # get the message and split it
        topic, time, stat_bits, value_str = message.split()
        current_range = int(stat_bits[-3:], 2)
        range_str = RANGE_DIC[current_range]

        self.label_time_stamp.setText(time)
        self.label_status.setText(stat_bits)
        self.label_range.setText(range_str)

        # do the calibration
        value_float = float(value_str) * CAL_SLOPE + CAL_ITCPT

        # convert binary to float value
        value = value_float * RAIL_VOLTAGE / ADC_QUANTIZATION

        # set to 2 decimal points
        value = int(value * 100) / 100

        # in case more digits are needed
        # self.lcdNumber.setDigitCount(8)
        if self.zeromq_listener_10001.running:
            #self.lcdNumber.display(value)
            #todo: do something
            print('do something')
        else:
            #self.lcdNumber.display(0)
            #todo: do something
            print('do something')

    def closeEvent(self, event):
        self.zeromq_listener_10001.running = False
        self.thread.terminate()
        self.thread.quit()
        self.thread.wait()

    def show_message(self, message):
        """
        Implementation of an abstract method:
        Show text in status bar
        :param message:
        :return:
        """
        self.statusbar.showMessage(message)

    def show_about_dialog(self):
        """
        Show about dialog
        :return:
        """
        about_dialog = QDialog()
        about_dialog.ui = Ui_AbooutDialog()
        about_dialog.ui.setupUi(about_dialog)
        about_dialog.ui.labelVersion.setText('Version: {}'.format(__version__))
        about_dialog.exec_()
        about_dialog.show()
