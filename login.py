# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'login.ui'
#
# Created by: PyQt5 UI code generator 5.8.2
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileSystemModel, \
    QDialog, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, \
    QFrame, QTabWidget, QFileDialog, QMessageBox, QListWidgetItem, QListWidget
from PyQt5.QtCore import pyqtSlot
from PyQt5 import QtCore, QtWidgets
import requests
from mainwindow import Ui_MainWindow

url = 'https://www.royalroad.com/account/login'
url2 = 'https://royalroad.com'
suffix = '/my/bookmarks?page='

headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
           'accept-encoding': 'gzip',
           'accept-language': 'en-US,en;q=0.9',
           'cache-control': 'no-cache',
           'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
           'Content-Type': 'application/x-www-form-urlencoded',
           'Connection': 'keep-alive'}

class Ui_Form(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.title = 'RoyalRoad'
        self.left = 10
        self.top = 10
        self.setFixedSize(400,150)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)

        self.pushButton = QPushButton()
        self.pushButton.setGeometry(QtCore.QRect(150, 110, 75, 23))
        self.pushButton.setObjectName("Login")
        self.pushButton.setText("Login")
        self.pushButton.setMaximumWidth(75)
        self.pushButton.clicked.connect(self.login)

        self.pushButton_2 = QPushButton()
        self.pushButton_2.setGeometry(QtCore.QRect(240, 110, 75, 23))
        self.pushButton_2.setObjectName("Cancel")
        self.pushButton_2.setText("Cancel")
        self.pushButton_2.setMaximumWidth(75)

        self.lineEdit = QLineEdit()
        self.lineEdit.setGeometry(QtCore.QRect(230, 40, 113, 20))
        self.lineEdit.setObjectName("Username")
        self.lineEdit.setMaximumWidth(150)
        self.lineEdit.setAlignment(QtCore.Qt.AlignLeft)

        self.lineEdit_2 = QLineEdit()
        self.lineEdit_2.setGeometry(QtCore.QRect(230, 70, 113, 20))
        self.lineEdit_2.setObjectName("Password")
        self.lineEdit_2.setMaximumWidth(150)
        self.lineEdit_2.setAlignment(QtCore.Qt.AlignLeft)

        self.label = QLabel()
        self.label.setGeometry(QtCore.QRect(150, 50, 47, 13))
        self.label.setObjectName("label")
        self.label.setText("Username")
        self.label.setAlignment(QtCore.Qt.AlignRight)

        self.label_2 = QLabel()
        self.label_2.setGeometry(QtCore.QRect(150, 70, 47, 13))
        self.label_2.setObjectName("label_2")
        self.label_2.setText("Password")
        self.label_2.setAlignment(QtCore.Qt.AlignRight)

        self.userLayout = QHBoxLayout()
        self.userLayout.addWidget(self.label)
        self.userLayout.addWidget(self.lineEdit)

        self.passLayout = QHBoxLayout()
        self.passLayout.addWidget(self.label_2)
        self.passLayout.addWidget(self.lineEdit_2)

        self.buttonsLayout = QHBoxLayout()
        self.buttonsLayout.addWidget(self.pushButton)
        self.buttonsLayout.addWidget(self.pushButton_2)

        self.centralLayout = QVBoxLayout()
        self.centralLayout.addLayout(self.userLayout)
        self.centralLayout.addLayout(self.passLayout)
        self.centralLayout.addLayout(self.buttonsLayout)
        self.setLayout(self.centralLayout)

        self.show()

    @pyqtSlot()
    def login(self):
        username = self.lineEdit.text()
        password = self.lineEdit_2.text()

        payload = {'Username': username,
                   'Password': password}
        print("Attempting to log in to RoyalRoad...")
        print()
        login = False
        with requests.Session() as s:
            p = s.post(url, data=payload, headers=headers)
            if p.url.endswith("loginsuccess"):
                login = True
            else:
                print("Unsuccessful login. Please try again")

        self.main = Ui_MainWindow(username, password, self.db)
        self.hide()


    @pyqtSlot()
    def showSelf(self):
        self.show()
