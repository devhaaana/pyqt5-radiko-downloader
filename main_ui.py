import sys
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDesktopWidget, QGroupBox, QVBoxLayout, QWidget, QPushButton, 
    QListWidget, QLabel, QHBoxLayout, QTextEdit, QFileDialog, QDateEdit, QLineEdit,
    QProgressDialog
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon, QPixmap
import qdarktheme

from radiko import *


class Radiko_Downloader_UI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.stations = {}
        self.selected_station = None
        self.selected_title = None
        self.start_time = None
        self.end_time = None
        self.folder_path = None
        self.init_path = './data/mp3/download.mp3'
        self.current_date = QDate.currentDate()
        
        self.init_UI()
        self.args = self.set_params()

        self.radiko = Radiko_Downloader(self.args)
        self.load_stations()
    
    def init_UI(self):
        self.setWindowTitle("Radiko Downloader")
        self.setWindowIcon(QIcon(f'./data/image/radiko-resize.png'))
        self.resize(1500, 1000)
        self.center()
        self.set_UI()
        self.show()

    def set_UI(self):
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout()

        self.top_group = QVBoxLayout()
        
        self.date_group = QGroupBox("Select Date")
        self.date_layout = QVBoxLayout()
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(self.current_date)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setCalendarPopup(True)
        self.date_edit.dateChanged.connect(self.fetch_program_schedule)
        self.date_layout.addWidget(QLabel("Select Broadcast Date:"))
        self.date_layout.addWidget(self.date_edit)
        self.date_group.setLayout(self.date_layout)

        self.channel_group = QGroupBox("Select Broadcast")
        self.channel_layout = QVBoxLayout()
        
        self.station_list = QListWidget()
        self.station_list.itemClicked.connect(self.on_station_selected)
        self.channel_layout.addWidget(QLabel("Select a Station:"))
        self.channel_layout.addWidget(self.station_list)
        
        self.title_list = QListWidget()
        self.title_list.itemClicked.connect(self.on_title_selected)
        self.channel_layout.addWidget(QLabel("Select Program:"))
        self.channel_layout.addWidget(self.title_list)
        self.channel_group.setLayout(self.channel_layout)

        self.top_group.addWidget(self.date_group)
        self.top_group.addWidget(self.channel_group)

        self.info_group = QGroupBox("Program Information")
        self.info_layout = QVBoxLayout()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedHeight(300)
        self.info_layout.addWidget(self.image_label)
        self.program_title_text = QTextEdit()
        self.program_title_text.setReadOnly(True)
        self.time_text = QTextEdit()
        self.time_text.setReadOnly(True)
        self.info_layout.addWidget(QLabel("Broadcast Time:"))
        self.info_layout.addWidget(self.time_text)
        self.program_pfm_text = QTextEdit()
        self.program_pfm_text.setReadOnly(True)
        self.info_layout.addWidget(QLabel("Performer:"))
        self.info_layout.addWidget(self.program_pfm_text)
        self.info_group.setLayout(self.info_layout)

        self.top_info_group = QGroupBox("Broadcast Information")
        self.top_info_layout = QHBoxLayout()
        
        self.top_info_layout.addLayout(self.top_group)
        self.top_info_layout.addWidget(self.info_group)
        
        self.top_info_group.setLayout(self.top_info_layout)
        
        self.setting_group = QGroupBox("Setup and Download")
        self.setting_layout = QVBoxLayout()

        self.file_layout = QHBoxLayout()

        self.file_path_line_edit = QLineEdit()
        self.file_path_line_edit.setPlaceholderText(self.init_path)
        self.file_path_line_edit.setReadOnly(True)
        self.file_path_line_edit.mousePressEvent = self.on_file_path_clicked
        self.file_layout.addWidget(self.file_path_line_edit)

        self.select_folder_button = QPushButton("📁 Save")
        self.select_folder_button.clicked.connect(self.start_download)
        self.file_layout.addWidget(self.select_folder_button)

        self.setting_layout.addLayout(self.file_layout)

        # Console Output
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.setting_layout.addWidget(QLabel("Console Output:"))
        self.setting_layout.addWidget(self.console_output)
        self.setting_group.setLayout(self.setting_layout)

        # 📌 Main layout
        self.main_layout.addWidget(self.top_info_group)
        self.main_layout.addWidget(self.setting_group)

        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)
        
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    def generate(self):
        process_text = 'File saving'
        self.progress = QProgressDialog(f'{process_text}. Please wait...', '', 0, 0, self)
        self.progress.setWindowTitle(process_text)
        self.progress.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setCancelButton(None)
        self.progress.show()

    def hide(self):
        self.progress.hide()

    def get_current_date(self):
        now = datetime.now()
        if now.hour < 5:
            return (now - timedelta(days=1)).strftime("%Y%m%d")
        return now.strftime("%Y%m%d")
    
    def get_select_date(self):
        return self.date_edit.date().toString("yyyyMMdd")
    
    def load_stations(self):
        try:
            stations = self.radiko.get_station_info(get_mode='stationID')
            
            if stations:
                for station in stations:
                    station_name = station['name']
                    station_id = station['id']
                    self.station_list.addItem(f"{station_name} ({station_id})")
            else:
                print("No stations found.")
        except Exception as e:
            print(f"Error in test function: {e}")

    def on_station_selected(self, item):
        self.selected_station = item.text().split("(")[-1].strip(")")
        self.fetch_program_schedule()

    def on_title_selected(self, item):
        self.selected_title = item.text()
        self.program_title_text.setText(self.selected_title)
        self.fetch_program_details(self.selected_title)

    def fetch_program_schedule(self):
        self.current_date = self.get_select_date()
        self.fetch_data(lambda xml_data: self.parse_program_data(xml_data))

    def fetch_program_details(self, title):
        self.fetch_data(lambda xml_data: self.parse_program_details_data(xml_data, title))

    def fetch_data(self, parse_function):
        selected_date = self.get_select_date() if self.date_edit else self.get_current_date()
        url = self.radiko.get_program_data(selected_station=self.selected_station, selected_date=selected_date, parse_function=parse_function)
            
    def parse_program_data(self, xml_data):
        self.title_list.clear()
        
        titles = self.radiko.get_program_title(xml_data)
        for title in titles:
            self.title_list.addItem(title)

    def parse_program_details_data(self, xml_data, selected_title):
        self.start_time, self.end_time, performer, img_url = self.radiko.get_program_time(xml_data, selected_title)
        self.update_ui(self.start_time, self.end_time, performer, img_url)

    def update_ui(self, start_time, end_time, performer, img_url):
        self.time_text.setText(f"{start_time} ~ {end_time}")
        self.program_pfm_text.setText(performer)
        self.set_program_image(img_url)

    def set_program_image(self, img_url):
        if img_url:
            pixmap = QPixmap()
            img = self.radiko.get_program_image(img_url=img_url)
            pixmap.loadFromData(img)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def select_folder(self):
        folder_path, _ = QFileDialog.getSaveFileName(self, "Set the save path", self.init_path, "MP3 Files (*.mp3)")

        if folder_path:
            if not folder_path.lower().endswith(".mp3"):
                folder_path += ".mp3"
            self.folder_path = folder_path
            self.file_path_line_edit.setText(self.folder_path)
            
        return folder_path
    
    def on_file_path_clicked(self, event=None):
        self.select_folder()
            
    def set_params(self):
        args = {
            'version': '1.0.0',
            'station': self.selected_station,
            'areaFree': False,
            'timeFree': False,
            'startTime': self.start_time,
            'endTime': self.end_time,
            'save_path': self.folder_path
        }
        
        return args

    def start_download(self):
        if not self.selected_station:
            self.console_output.append("❌ No station selected.")
            return None

        if not self.folder_path:
            self.folder_path = self.select_folder()
            if not self.folder_path:
                self.console_output.append("❌ Folder selection has been canceled.")
                return None
        else:
            self.console_output.append(f"📌 Set the save path: '{self.folder_path}'")
        
        args = self.set_params()
        
        try:
            self.radiko = Radiko_Downloader(args)
            self.console_output.append("📥 Start MP3 download...")
            self.generate()
            self.radiko.save_mp3_file()
            self.hide()
            self.console_output.append("✅ Download complete!")
        except Exception as e:
            self.console_output.append(f"❌ Download failed: {str(e)}")
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarktheme.load_stylesheet())
    window = Radiko_Downloader_UI()
    sys.exit(app.exec_())