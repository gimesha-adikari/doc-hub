# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMainWindow, QMenuBar,
    QPushButton, QSizePolicy, QSpacerItem, QSplitter,
    QStackedWidget, QStatusBar, QTabWidget, QTableWidget,
    QTableWidgetItem, QTextBrowser, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1200, 800)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.main_vertical_layout = QVBoxLayout(self.centralwidget)
        self.main_vertical_layout.setObjectName(u"main_vertical_layout")
        self.main_tab_widget = QTabWidget(self.centralwidget)
        self.main_tab_widget.setObjectName(u"main_tab_widget")
        self.tab_smart_search = QWidget()
        self.tab_smart_search.setObjectName(u"tab_smart_search")
        self.smart_search_layout = QVBoxLayout(self.tab_smart_search)
        self.smart_search_layout.setObjectName(u"smart_search_layout")
        self.search_top_bar_layout = QHBoxLayout()
        self.search_top_bar_layout.setObjectName(u"search_top_bar_layout")
        self.search_bar = QLineEdit(self.tab_smart_search)
        self.search_bar.setObjectName(u"search_bar")

        self.search_top_bar_layout.addWidget(self.search_bar)

        self.filter_button = QPushButton(self.tab_smart_search)
        self.filter_button.setObjectName(u"filter_button")

        self.search_top_bar_layout.addWidget(self.filter_button)

        self.settings_button = QPushButton(self.tab_smart_search)
        self.settings_button.setObjectName(u"settings_button")

        self.search_top_bar_layout.addWidget(self.settings_button)


        self.smart_search_layout.addLayout(self.search_top_bar_layout)

        self.search_splitter = QSplitter(self.tab_smart_search)
        self.search_splitter.setObjectName(u"search_splitter")
        self.search_splitter.setOrientation(Qt.Horizontal)
        self.results_table = QTableWidget(self.search_splitter)
        if (self.results_table.columnCount() < 4):
            self.results_table.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.results_table.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.results_table.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.results_table.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.results_table.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.results_table.setObjectName(u"results_table")
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.search_splitter.addWidget(self.results_table)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.preview_stack = QStackedWidget(self.search_splitter)
        self.preview_stack.setObjectName(u"preview_stack")
        self.page_text = QWidget()
        self.page_text.setObjectName(u"page_text")
        self.verticalLayout_2 = QVBoxLayout(self.page_text)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.file_preview_text = QTextBrowser(self.page_text)
        self.file_preview_text.setObjectName(u"file_preview_text")
        self.file_preview_text.setReadOnly(True)

        self.verticalLayout_2.addWidget(self.file_preview_text)

        self.preview_stack.addWidget(self.page_text)
        self.page_image = QWidget()
        self.page_image.setObjectName(u"page_image")
        self.verticalLayout_3 = QVBoxLayout(self.page_image)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.image_preview_label = QLabel(self.page_image)
        self.image_preview_label.setObjectName(u"image_preview_label")
        self.image_preview_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.image_preview_label)

        self.preview_stack.addWidget(self.page_image)
        self.page_default = QWidget()
        self.page_default.setObjectName(u"page_default")
        self.verticalLayout_4 = QVBoxLayout(self.page_default)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.default_preview_label = QLabel(self.page_default)
        self.default_preview_label.setObjectName(u"default_preview_label")
        self.default_preview_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_4.addWidget(self.default_preview_label)

        self.preview_stack.addWidget(self.page_default)
        self.search_splitter.addWidget(self.preview_stack)

        self.smart_search_layout.addWidget(self.search_splitter)

        self.main_tab_widget.addTab(self.tab_smart_search, "")
        self.tab_file_organizer = QWidget()
        self.tab_file_organizer.setObjectName(u"tab_file_organizer")
        self.file_organizer_layout = QVBoxLayout(self.tab_file_organizer)
        self.file_organizer_layout.setObjectName(u"file_organizer_layout")
        self.organizer_intro_label = QLabel(self.tab_file_organizer)
        self.organizer_intro_label.setObjectName(u"organizer_intro_label")
        self.organizer_intro_label.setAlignment(Qt.AlignCenter)

        self.file_organizer_layout.addWidget(self.organizer_intro_label)

        self.organizer_path_layout = QHBoxLayout()
        self.organizer_path_layout.setObjectName(u"organizer_path_layout")
        self.organizer_target_path_input = QLineEdit(self.tab_file_organizer)
        self.organizer_target_path_input.setObjectName(u"organizer_target_path_input")
        self.organizer_target_path_input.setReadOnly(True)

        self.organizer_path_layout.addWidget(self.organizer_target_path_input)

        self.organizer_browse_button = QPushButton(self.tab_file_organizer)
        self.organizer_browse_button.setObjectName(u"organizer_browse_button")

        self.organizer_path_layout.addWidget(self.organizer_browse_button)


        self.file_organizer_layout.addLayout(self.organizer_path_layout)

        self.run_organizer_button = QPushButton(self.tab_file_organizer)
        self.run_organizer_button.setObjectName(u"run_organizer_button")

        self.file_organizer_layout.addWidget(self.run_organizer_button)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.file_organizer_layout.addItem(self.verticalSpacer)

        self.main_tab_widget.addTab(self.tab_file_organizer, "")

        self.main_vertical_layout.addWidget(self.main_tab_widget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1200, 23))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.main_tab_widget.setCurrentIndex(0)
        self.preview_stack.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Document Hub", None))
        self.search_bar.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Search documents...", None))
        self.filter_button.setText(QCoreApplication.translate("MainWindow", u"F", None))
        self.settings_button.setText(QCoreApplication.translate("MainWindow", u"S", None))
        ___qtablewidgetitem = self.results_table.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"Name", None));
        ___qtablewidgetitem1 = self.results_table.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"Type", None));
        ___qtablewidgetitem2 = self.results_table.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"Size", None));
        ___qtablewidgetitem3 = self.results_table.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"Modified", None));
        self.file_preview_text.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Select a file to preview its content...", None))
        self.image_preview_label.setText("")
        self.default_preview_label.setText(QCoreApplication.translate("MainWindow", u"Preview not available for this file type.", None))
        self.main_tab_widget.setTabText(self.main_tab_widget.indexOf(self.tab_smart_search), QCoreApplication.translate("MainWindow", u"Smart Search", None))
        self.organizer_intro_label.setText(QCoreApplication.translate("MainWindow", u"Organize your messy folders with predefined rules.", None))
        self.organizer_target_path_input.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Path to folder to organize (e.g., /home/user/Downloads)", None))
        self.organizer_browse_button.setText(QCoreApplication.translate("MainWindow", u"Browse...", None))
        self.run_organizer_button.setText(QCoreApplication.translate("MainWindow", u"Run Organizer", None))
        self.main_tab_widget.setTabText(self.main_tab_widget.indexOf(self.tab_file_organizer), QCoreApplication.translate("MainWindow", u"File Organizer", None))
    # retranslateUi

