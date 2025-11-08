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
    QPushButton, QSizePolicy, QSplitter, QStackedWidget,
    QStatusBar, QTabWidget, QTableWidget, QTableWidgetItem,
    QTextBrowser, QTreeView, QVBoxLayout, QWidget)

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
        self.search_bar_layout = QHBoxLayout()
        self.search_bar_layout.setObjectName(u"search_bar_layout")
        self.search_bar = QLineEdit(self.tab_smart_search)
        self.search_bar.setObjectName(u"search_bar")

        self.search_bar_layout.addWidget(self.search_bar)

        self.filter_button = QPushButton(self.tab_smart_search)
        self.filter_button.setObjectName(u"filter_button")

        self.search_bar_layout.addWidget(self.filter_button)

        self.settings_button = QPushButton(self.tab_smart_search)
        self.settings_button.setObjectName(u"settings_button")

        self.search_bar_layout.addWidget(self.settings_button)


        self.smart_search_layout.addLayout(self.search_bar_layout)

        self.tag_chip_layout = QHBoxLayout()
        self.tag_chip_layout.setObjectName(u"tag_chip_layout")

        self.smart_search_layout.addLayout(self.tag_chip_layout)

        self.main_search_splitter = QSplitter(self.tab_smart_search)
        self.main_search_splitter.setObjectName(u"main_search_splitter")
        self.main_search_splitter.setOrientation(Qt.Horizontal)
        self.left_container = QWidget(self.main_search_splitter)
        self.left_container.setObjectName(u"left_container")
        self.left_vertical_layout = QVBoxLayout(self.left_container)
        self.left_vertical_layout.setSpacing(6)
        self.left_vertical_layout.setObjectName(u"left_vertical_layout")
        self.left_vertical_layout.setContentsMargins(0, 0, 0, 0)
        self.explorer_tree_view = QTreeView(self.left_container)
        self.explorer_tree_view.setObjectName(u"explorer_tree_view")
        self.explorer_tree_view.setHeaderHidden(False)

        self.left_vertical_layout.addWidget(self.explorer_tree_view)

        self.results_table = QTableWidget(self.left_container)
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
        self.results_table.horizontalHeader().setStretchLastSection(True)

        self.left_vertical_layout.addWidget(self.results_table)

        self.main_search_splitter.addWidget(self.left_container)
        self.preview_tab_widget = QTabWidget(self.main_search_splitter)
        self.preview_tab_widget.setObjectName(u"preview_tab_widget")
        self.tab_preview = QWidget()
        self.tab_preview.setObjectName(u"tab_preview")
        self.preview_layout = QVBoxLayout(self.tab_preview)
        self.preview_layout.setObjectName(u"preview_layout")
        self.preview_stack = QStackedWidget(self.tab_preview)
        self.preview_stack.setObjectName(u"preview_stack")
        self.page_text = QWidget()
        self.page_text.setObjectName(u"page_text")
        self.page_text_layout = QVBoxLayout(self.page_text)
        self.page_text_layout.setObjectName(u"page_text_layout")
        self.file_preview_text = QTextBrowser(self.page_text)
        self.file_preview_text.setObjectName(u"file_preview_text")
        self.file_preview_text.setReadOnly(True)

        self.page_text_layout.addWidget(self.file_preview_text)

        self.preview_stack.addWidget(self.page_text)
        self.page_image = QWidget()
        self.page_image.setObjectName(u"page_image")
        self.page_image_layout = QVBoxLayout(self.page_image)
        self.page_image_layout.setObjectName(u"page_image_layout")
        self.image_preview_label = QLabel(self.page_image)
        self.image_preview_label.setObjectName(u"image_preview_label")
        self.image_preview_label.setAlignment(Qt.AlignCenter)

        self.page_image_layout.addWidget(self.image_preview_label)

        self.preview_stack.addWidget(self.page_image)
        self.page_default = QWidget()
        self.page_default.setObjectName(u"page_default")
        self.page_default_layout = QVBoxLayout(self.page_default)
        self.page_default_layout.setObjectName(u"page_default_layout")
        self.default_preview_label = QLabel(self.page_default)
        self.default_preview_label.setObjectName(u"default_preview_label")
        self.default_preview_label.setAlignment(Qt.AlignCenter)

        self.page_default_layout.addWidget(self.default_preview_label)

        self.preview_stack.addWidget(self.page_default)

        self.preview_layout.addWidget(self.preview_stack)

        self.preview_tab_widget.addTab(self.tab_preview, "")
        self.tab_ai_chat = QWidget()
        self.tab_ai_chat.setObjectName(u"tab_ai_chat")
        self.ai_chat_layout = QVBoxLayout(self.tab_ai_chat)
        self.ai_chat_layout.setObjectName(u"ai_chat_layout")
        self.ai_chat_area = QTextBrowser(self.tab_ai_chat)
        self.ai_chat_area.setObjectName(u"ai_chat_area")

        self.ai_chat_layout.addWidget(self.ai_chat_area)

        self.ai_input_layout = QHBoxLayout()
        self.ai_input_layout.setObjectName(u"ai_input_layout")
        self.ai_question_input = QLineEdit(self.tab_ai_chat)
        self.ai_question_input.setObjectName(u"ai_question_input")

        self.ai_input_layout.addWidget(self.ai_question_input)

        self.ai_ask_button = QPushButton(self.tab_ai_chat)
        self.ai_ask_button.setObjectName(u"ai_ask_button")

        self.ai_input_layout.addWidget(self.ai_ask_button)


        self.ai_chat_layout.addLayout(self.ai_input_layout)

        self.preview_tab_widget.addTab(self.tab_ai_chat, "")
        self.main_search_splitter.addWidget(self.preview_tab_widget)

        self.smart_search_layout.addWidget(self.main_search_splitter)

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
        self.organizer_source_path_input = QLineEdit(self.tab_file_organizer)
        self.organizer_source_path_input.setObjectName(u"organizer_source_path_input")
        self.organizer_source_path_input.setReadOnly(True)

        self.organizer_path_layout.addWidget(self.organizer_source_path_input)

        self.organizer_source_browse_button = QPushButton(self.tab_file_organizer)
        self.organizer_source_browse_button.setObjectName(u"organizer_source_browse_button")

        self.organizer_path_layout.addWidget(self.organizer_source_browse_button)


        self.file_organizer_layout.addLayout(self.organizer_path_layout)

        self.organizer_dest_layout = QHBoxLayout()
        self.organizer_dest_layout.setObjectName(u"organizer_dest_layout")
        self.organizer_dest_path_input = QLineEdit(self.tab_file_organizer)
        self.organizer_dest_path_input.setObjectName(u"organizer_dest_path_input")
        self.organizer_dest_path_input.setReadOnly(True)

        self.organizer_dest_layout.addWidget(self.organizer_dest_path_input)

        self.organizer_dest_browse_button = QPushButton(self.tab_file_organizer)
        self.organizer_dest_browse_button.setObjectName(u"organizer_dest_browse_button")

        self.organizer_dest_layout.addWidget(self.organizer_dest_browse_button)


        self.file_organizer_layout.addLayout(self.organizer_dest_layout)

        self.organizer_analyze_button = QPushButton(self.tab_file_organizer)
        self.organizer_analyze_button.setObjectName(u"organizer_analyze_button")

        self.file_organizer_layout.addWidget(self.organizer_analyze_button)

        self.organizer_table = QTableWidget(self.tab_file_organizer)
        if (self.organizer_table.columnCount() < 3):
            self.organizer_table.setColumnCount(3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.organizer_table.setHorizontalHeaderItem(0, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.organizer_table.setHorizontalHeaderItem(1, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.organizer_table.setHorizontalHeaderItem(2, __qtablewidgetitem6)
        self.organizer_table.setObjectName(u"organizer_table")
        self.organizer_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.organizer_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.organizer_table.horizontalHeader().setStretchLastSection(True)

        self.file_organizer_layout.addWidget(self.organizer_table)

        self.organizer_run_button = QPushButton(self.tab_file_organizer)
        self.organizer_run_button.setObjectName(u"organizer_run_button")

        self.file_organizer_layout.addWidget(self.organizer_run_button)

        self.main_tab_widget.addTab(self.tab_file_organizer, "")

        self.main_vertical_layout.addWidget(self.main_tab_widget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.main_tab_widget.setCurrentIndex(0)
        self.preview_tab_widget.setCurrentIndex(0)
        self.preview_stack.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Document Hub", None))
        self.search_bar.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Search documents, AI tags, or content...", None))
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
        self.default_preview_label.setText(QCoreApplication.translate("MainWindow", u"Preview not available for this file type.", None))
        self.preview_tab_widget.setTabText(self.preview_tab_widget.indexOf(self.tab_preview), QCoreApplication.translate("MainWindow", u"Preview", None))
        self.ai_chat_area.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Ask a question about the document in the 'Preview' tab to start chatting...", None))
        self.ai_question_input.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Ask a question...", None))
        self.ai_ask_button.setText(QCoreApplication.translate("MainWindow", u"Ask AI", None))
        self.preview_tab_widget.setTabText(self.preview_tab_widget.indexOf(self.tab_ai_chat), QCoreApplication.translate("MainWindow", u"AI Chat", None))
        self.main_tab_widget.setTabText(self.main_tab_widget.indexOf(self.tab_smart_search), QCoreApplication.translate("MainWindow", u"Smart Search", None))
        self.organizer_intro_label.setText(QCoreApplication.translate("MainWindow", u"Organize loose files in a folder using AI. This will ignore all sub-folders.", None))
        self.organizer_source_path_input.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Select a \"Source\" folder to organize (e.g., /home/user/Downloads)", None))
        self.organizer_source_browse_button.setText(QCoreApplication.translate("MainWindow", u"Browse Source...", None))
        self.organizer_dest_path_input.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Select a \"Destination\" folder for the organized files (e.g., /home/user/Documents)", None))
        self.organizer_dest_browse_button.setText(QCoreApplication.translate("MainWindow", u"Browse Destination...", None))
        self.organizer_analyze_button.setText(QCoreApplication.translate("MainWindow", u"1. Analyze Files", None))
        ___qtablewidgetitem4 = self.organizer_table.horizontalHeaderItem(0)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("MainWindow", u"Organize", None));
        ___qtablewidgetitem5 = self.organizer_table.horizontalHeaderItem(1)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("MainWindow", u"File Name", None));
        ___qtablewidgetitem6 = self.organizer_table.horizontalHeaderItem(2)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("MainWindow", u"Suggested Category", None));
        self.organizer_run_button.setText(QCoreApplication.translate("MainWindow", u"2. Organize Checked Files", None))
        self.main_tab_widget.setTabText(self.main_tab_widget.indexOf(self.tab_file_organizer), QCoreApplication.translate("MainWindow", u"File Organizer", None))
    # retranslateUi

