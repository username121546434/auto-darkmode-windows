import datetime
import sys
from typing import Literal
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtWidgets import QWidget
from task_scheduler import create_or_update_task, delete_task
import geocoder
import requests
import darkdetect

system_theme_args = 'add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize' \
            ' /v SystemUsesLightTheme /t REG_DWORD /d {lightmode} /f'
app_theme_args = 'add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize' \
            ' /v AppsUseLightTheme /t REG_DWORD /d {lightmode} /f'

DARK_MODE_NAME = 'Change to darkmode'
LIGHT_MODE_NAME = 'Change to lightmode'
current_location = geocoder.ip('me').latlng


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout()
        w = QWidget()
        w.setLayout(layout)
        self.setCentralWidget(w)

        layout.addWidget(QLabel('Turn dark mode on at:'))
        self.dark_mode_time = QTimeEdit(datetime.time(20, 0))
        layout.addWidget(self.dark_mode_time)

        layout.addWidget(QLabel('Turn light mode on at:'))
        self.light_mode_time = QTimeEdit(datetime.time(6, 0))
        layout.addWidget(self.light_mode_time)

        self.save_btn = QPushButton('Save')
        self.save_btn.clicked.connect(self.on_save_btn_click)
        layout.addWidget(self.save_btn)

        self.auto_btn = QPushButton('Sync with sunrise/sunset')
        self.auto_btn.clicked.connect(self.sync_to_sunrise_sunset)
        layout.addWidget(self.auto_btn)

        self.change_system_theme = change_system_theme = QAction('Change the system theme', self)
        change_system_theme.setCheckable(True)
        change_system_theme.setChecked(True)
        
        self.change_app_theme = change_app_theme = QAction('Change the themes of apps', self)
        change_app_theme.setCheckable(True)
        change_app_theme.setChecked(True)

        menu = self.menuBar()

        self.advanced_menu = menu.addMenu('&Advanced')
        self.advanced_menu.addAction(change_system_theme)
        self.advanced_menu.addAction(change_app_theme)

    def on_save_btn_click(self, *args, **kw):
        if not self.change_app_theme.isChecked() and not self.change_system_theme.isChecked():
            delete_task(DARK_MODE_NAME)
            delete_task(LIGHT_MODE_NAME)
            return

        dark_mode_actions = []        
        light_mode_actions = []        
        if self.change_app_theme.isChecked():
            dark_mode_actions.append(('reg', app_theme_args.format(lightmode=0)))
            light_mode_actions.append(('reg', app_theme_args.format(lightmode=1)))
        if self.change_system_theme.isChecked():
            dark_mode_actions.append(('reg', system_theme_args.format(lightmode=0)))
            light_mode_actions.append(('reg', system_theme_args.format(lightmode=1)))
        
        light_mode_time = self.light_mode_time.time().toPyTime()
        dark_mode_time = self.dark_mode_time.time().toPyTime()

        create_or_update_task(
            'Change to darkmode',
            'Automatically sets the computer to darkmode at night',
            dark_mode_time,
            dark_mode_actions
        )
        create_or_update_task(
            'Change to lightmode',
            'Automatically sets the computer to lightmode at morning',
            light_mode_time,
            light_mode_actions
        )
        self.statusBar().showMessage('Succesfully saved', 2000)
    
    def sync_to_sunrise_sunset(self):
        response = requests.get('https://api.sunrise-sunset.org/json', {
            'lat': current_location[0],
            'lng': current_location[1],
            'formatted': 0
        })
        times = response.json()['results']
        sunrise_day = datetime.datetime.fromisoformat(times['sunrise']).astimezone()
        sunset_day = datetime.datetime.fromisoformat(times['sunset']).astimezone()

        sunrise = datetime.time.fromisoformat(sunrise_day.isoformat().split('T')[1])
        sunset = datetime.time.fromisoformat(sunset_day.isoformat().split('T')[1])


        self.dark_mode_time.setTime(sunset)
        self.light_mode_time.setTime(sunrise)
    
    def on_theme_change(self, theme: Literal['Light', 'Dark']):
        if theme == 'Dark':
            app.setStyle('Fusion')
        elif theme == 'Light':
            app.setStyle('Windows')
        

app = QApplication(sys.argv)

window = MainWindow()
if darkdetect.isDark():
    app.setStyle('Fusion')
window.show()

app.exec()
