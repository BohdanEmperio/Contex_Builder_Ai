DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

QPushButton#NavBtn {
    background-color: #313244;
    color: #cdd6f4;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}
QPushButton#NavBtn:hover {
    background-color: #45475a;
}
QPushButton#NavBtn[active="true"] {
    background-color: #89b4fa;
    color: #11111b;
    font-weight: 700;
}

QLabel#PageTitle {
    color: #89b4fa;
    font-size: 18px;
    font-weight: 700;
    padding: 4px 0px;
}

QGroupBox {
    border: 1px solid #45475a;
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px 10px 10px 10px;
    font-weight: 600;
    color: #cdd6f4;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #1e1e2e;
}

QLineEdit, QComboBox, QSpinBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 7px 10px;
    min-height: 20px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #89b4fa;
}

QPushButton#BlueBtn {
    background-color: #89b4fa;
    color: #11111b;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 700;
}
QPushButton#BlueBtn:hover {
    background-color: #a6c8ff;
}

QPushButton#GreenBtn {
    background-color: #a6e3a1;
    color: #11111b;
    border: none;
    border-radius: 6px;
    padding: 9px 16px;
    font-weight: 700;
}
QPushButton#GreenBtn:hover {
    background-color: #bef0b9;
}

QPushButton#RedBtn {
    background-color: #f38ba8;
    color: #11111b;
    border: none;
    border-radius: 6px;
    padding: 9px 16px;
    font-weight: 700;
}
QPushButton#RedBtn:hover {
    background-color: #f7a8be;
}

QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #585b70;
    background-color: #313244;
}
QCheckBox::indicator:checked {
    background-color: #89b4fa;
    border-color: #89b4fa;
}

QListWidget {
    background-color: #262738;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 4px;
}
QListWidget::item {
    padding: 4px 6px;
}
QListWidget::item:selected {
    background-color: #45475a;
    color: #ffffff;
}

QPlainTextEdit#LogBox {
    background-color: #262738;
    color: #a6adc8;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
}

QLabel#TokenInfoBox {
    background-color: #262738;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px 12px;
    color: #cdd6f4;
}
"""