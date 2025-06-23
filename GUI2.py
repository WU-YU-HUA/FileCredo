# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ftp.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QLabel, QListWidget,
    QListWidgetItem, QMainWindow, QPushButton, QSizePolicy,
    QStatusBar, QTextEdit, QWidget, QLineEdit)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(460, 533)
        MainWindow.setAutoFillBackground(False)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.fromIP = QTextEdit(self.centralwidget)
        self.fromIP.setObjectName(u"fromIP")
        self.fromIP.setGeometry(QRect(180, 30, 161, 31))
        self.fromUsername = QTextEdit(self.centralwidget)
        self.fromUsername.setObjectName(u"fromUsername")
        self.fromUsername.setGeometry(QRect(180, 80, 161, 31))
        self.fromPassword = QLineEdit(self.centralwidget)
        self.fromPassword.setEchoMode(QLineEdit.EchoMode.Password)
        self.fromPassword.setObjectName(u"fromPassword")
        self.fromPassword.setGeometry(QRect(180, 130, 161, 31))
        self.label_2 = QLabel(self.centralwidget)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(110, 40, 58, 15))
        font = QFont()
        font.setFamilies([u"Arial"])
        font.setPointSize(10)
        self.label_2.setFont(font)
        self.label_2.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(110, 90, 58, 15))
        self.label_3.setFont(font)
        self.label_3.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.label_4 = QLabel(self.centralwidget)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(110, 140, 58, 15))
        self.label_4.setFont(font)
        self.label_4.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.pushButton = QPushButton(self.centralwidget)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setGeometry(QRect(260, 250, 111, 31))
        self.pushButton.setFont(font)
        self.fileFromButton = QPushButton(self.centralwidget)
        self.fileFromButton.setObjectName(u"fileFromButton")
        self.fileFromButton.setGeometry(QRect(100, 250, 131, 28))
        self.fileFromButton.setFont(font)
        self.label_5 = QLabel(self.centralwidget)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(110, 190, 58, 15))
        self.label_5.setFont(font)
        self.label_5.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.fromPort = QTextEdit(self.centralwidget)
        self.fromPort.setObjectName(u"fromPort")
        self.fromPort.setGeometry(QRect(180, 180, 161, 31))
        self.listWidget = QListWidget(self.centralwidget)
        self.listWidget.setObjectName(u"listWidget")
        self.listWidget.setGeometry(QRect(20, 300, 421, 241))
        self.listWidget.setMouseTracking(False)
        self.listWidget.setTabletTracking(False)
        self.listWidget.setAutoFillBackground(False)
        self.listWidget.setHorizontalScrollMode(QAbstractItemView.ScrollPerItem)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"IP", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"username", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"password", None))
        self.pushButton.setText(QCoreApplication.translate("MainWindow", u"START", None))
        self.fileFromButton.setText(QCoreApplication.translate("MainWindow", u"Select Folder", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"port", None))
    # retranslateUi

