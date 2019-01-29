# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.8.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, \
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import pyqtSlot
from PyQt5 import QtCore, QtWidgets
import requests
import pyrebase
import json
import re

class Ui_MainWindow(QWidget):
    def __init__(self, username, password, db):
        super().__init__()
        self.username = username
        self.password = password
        self.db = db
        self.title = 'RoyalRoad'
        self.left = 10
        self.top = 10
        self.setFixedSize(800,700)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)

        self.treeWidget = QTreeWidget()
        self.treeWidget.setGeometry(QtCore.QRect(30, 20, 311, 351))
        self.treeWidget.setObjectName("treeWidget")
        #self.treeWidget.setColumnCount(4)

        self.layout1 = QHBoxLayout()
        self.layout1.addWidget(self.treeWidget)

        self.pushButton = QPushButton()
        self.pushButton.setGeometry(QtCore.QRect(140, 390, 75, 23))
        self.pushButton.setObjectName("pushButton")
        self.pushButton.setText("Refresh")
        self.pushButton.clicked.connect(self.refresh)

        self.layout2 = QVBoxLayout()
        self.layout2.addWidget(self.pushButton)

        #self.menuBar = QMenuBar()
        #self.menuBar.setGeometry(QtCore.QRect(0, 0, 801, 21))
        #self.menuBar.setObjectName("menuBar")

        self.centralLayout = QVBoxLayout()
        self.centralLayout.addLayout(self.layout1)
        self.centralLayout.addLayout(self.layout2)
        self.setLayout(self.centralLayout)

        self.show()

    @pyqtSlot()
    def refresh(self):
        #from royalroadl import fetchall
        #fetchall(self.username, self.password)

        data = self.db.child("stories").get().each()

        for d in data:
            story = d.val()
            item = QTreeWidgetItem(self.treeWidget, [story['title']])
            item.addChild(QTreeWidgetItem(item, [story['authorLink']]))
            item.addChild(QTreeWidgetItem(item, [story['lastUpdated']]))
            item.addChild(QTreeWidgetItem(item, [story['storyLink']]))

            chapters = QTreeWidgetItem(item, ["Chapters"])
            item.addChild(chapters)

            data1 = self.db.child("stories").child(d.key()).child("chapters").get().each()

            for chap in data1:
                chapter = chap.val()
                chapters.addChild(QTreeWidgetItem(chapters, [chapter['title']]))
                chapters.addChild(QTreeWidgetItem(chapters, [chapter['chaptLink']]))
                chapters.addChild(QTreeWidgetItem(chapters, [chapter['storyLink']]))
                chapters.addChild(QTreeWidgetItem(chapters, [chapter['timePublished']]))


        self.treeWidget.addTopLevelItem(item)
