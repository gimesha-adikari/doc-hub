# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'settings_window.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_SettingsWindow(object):
    def setupUi(self, SettingsWindow):
        if not SettingsWindow.objectName():
            SettingsWindow.setObjectName(u"SettingsWindow")
        SettingsWindow.resize(600, 400)
        SettingsWindow.setModal(True)
        self.verticalLayout = QVBoxLayout(SettingsWindow)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(SettingsWindow)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.folders_list_widget = QListWidget(SettingsWindow)
        self.folders_list_widget.setObjectName(u"folders_list_widget")

        self.verticalLayout.addWidget(self.folders_list_widget)

        self.button_layout = QHBoxLayout()
        self.button_layout.setObjectName(u"button_layout")
        self.add_folder_button = QPushButton(SettingsWindow)
        self.add_folder_button.setObjectName(u"add_folder_button")

        self.button_layout.addWidget(self.add_folder_button)

        self.remove_folder_button = QPushButton(SettingsWindow)
        self.remove_folder_button.setObjectName(u"remove_folder_button")

        self.button_layout.addWidget(self.remove_folder_button)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.button_layout.addItem(self.horizontalSpacer)

        self.close_button = QPushButton(SettingsWindow)
        self.close_button.setObjectName(u"close_button")

        self.button_layout.addWidget(self.close_button)


        self.verticalLayout.addLayout(self.button_layout)


        self.retranslateUi(SettingsWindow)

        QMetaObject.connectSlotsByName(SettingsWindow)
    # setupUi

    def retranslateUi(self, SettingsWindow):
        SettingsWindow.setWindowTitle(QCoreApplication.translate("SettingsWindow", u"Settings", None))
        self.label.setText(QCoreApplication.translate("SettingsWindow", u"Watched Folders", None))
        self.add_folder_button.setText(QCoreApplication.translate("SettingsWindow", u"Add Folder...", None))
        self.remove_folder_button.setText(QCoreApplication.translate("SettingsWindow", u"Remove Selected", None))
        self.close_button.setText(QCoreApplication.translate("SettingsWindow", u"Close", None))
    # retranslateUi

