from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QSplitter, QMainWindow, QComboBox, QCheckBox, QScrollArea
from PyQt5.QtCore import Qt
from db import Database
from notify import Notify

class TableEditor(QMainWindow): #окно подключения к бд
    def __init__(self):
        super().__init__()
        self.initUI()
        self.connection=None
        #стили
        self.setStyleSheet("""
            QPushButton {
                background-color: #1230AB;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border-radius: 15px;
            }
            QLabel {font-size: 16px;}
            QLineEdit {
                border-radius: 7px;
            }
        """)
        
    def initUI(self): #инициализация окна
        self.setWindowTitle("Table Editor")
        
        self.connect_params_label = QLabel("Введите параметры подключения к базе данных.\nЕсли подключения или базы не существует, то они будут созданы.")
        
        self.host_label = QLabel("Host:")
        self.host_inp = QLineEdit(self, text="localhost")
        
        self.db_label = QLabel("Название базы данных:")
        self.db_inp = QLineEdit(self, text="postgres")
        
        self.user_label = QLabel("Пользователь:")
        self.user_inp = QLineEdit(self, text="postgres")
        
        self.pass_label = QLabel("Пароль:")
        self.pass_inp = QLineEdit(self, text="postgres")
        
        self.connect_btn = QPushButton("Подключиться")
        self.connect_btn.setFixedSize(200, 40)
        self.connect_btn.clicked.connect(self.connect)
        
        layout = QVBoxLayout()
        layout.addWidget(self.connect_params_label)
        layout.addWidget(self.host_label)
        layout.addWidget(self.host_inp)
        layout.addWidget(self.db_label)
        layout.addWidget(self.db_inp)
        layout.addWidget(self.user_label)
        layout.addWidget(self.user_inp)
        layout.addWidget(self.pass_label)
        layout.addWidget(self.pass_inp)
        layout.addWidget(self.connect_btn, alignment=Qt.AlignCenter)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
    
    def connect(self): #подключение к бд
        host = self.host_inp.text()
        database = self.db_inp.text()
        user = self.user_inp.text()
        password = self.pass_inp.text()
        
        if ':' in host:
            host, port = host.split(':')
        else:
            host, port = host, 5432
        try:
            self.connection = Database(host, port, database, user, password)
            res=self.connection.connect()
            if isinstance(res, Exception):
                if "does not exist" or "can't decode" in str(res):
                    self.connection.create_database()
                else:
                    Notify.popup("Ошибка", "error", f"Ошибка подключения: {res}")
            else:
                Notify.popup("Успех", "info", "Подключение успешно")
                self.tables_window = TableWindow(self.connection)
                self.tables_window.show()
                self.close()
        except Exception as e:
                Notify.popup("Ошибка", "error", f"Ошибка создания базы данных: {e}")
class TableWindow(QMainWindow): #окно работы с таблицами
    def __init__(self, connection):
        super().__init__()
        self.connection = connection
        self.initUI()
        #стили
        self.setStyleSheet("""
            QPushButton {
                background-color: #1230AB;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border-radius: 15px;
            }
            QLabel {font-size: 16px;}
            QLineEdit {
                border-radius: 7px;
            }
            QScrollArea {border: none;}
        """)

    def initUI(self): #инициализация окна
        dbname=self.connection.dbname
        self.setWindowTitle(f"{dbname}")
        self.resize(800, 600)
        
        self.splitter = QSplitter(Qt.Horizontal)
        
        self.table_list_scroll=QScrollArea()
        self.table_list_scroll.setWidgetResizable(True)
        self.table_list_scroll.setMinimumWidth(200)
        
        self.table_list = QWidget()
        self.table_list_layout = QVBoxLayout(self.table_list)
        self.table_list_scroll.setWidget(self.table_list)
        
        self.table_info=QWidget()
        self.table_info_layout=QVBoxLayout(self.table_info)
        self.table_info_label=QLabel("Выберите таблицу или создайте новую", alignment=Qt.AlignCenter)
        self.table_info_label.setStyleSheet("font-weight: bold;")
        self.add_table_btn=QPushButton("Создать таблицу")
        self.add_table_btn.setFixedSize(200, 40)
        self.add_table_btn.clicked.connect(self.add_table)
        self.table_info_layout.addWidget(self.table_info_label, alignment=Qt.AlignCenter)
        self.table_info_layout.addWidget(self.add_table_btn, alignment=Qt.AlignCenter)
        self.table_info_layout.addStretch()
        
        self.splitter.addWidget(self.table_list_scroll)
        self.splitter.addWidget(self.table_info)
        
        self.load_table_btns()
        self.table_list_layout.addStretch()
        
        layout = QHBoxLayout()
        layout.addWidget(self.splitter)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
    def load_table_btns(self): #загрузка кнопок с таблицами
        try:
            names = self.connection.get_tables()
            for name in names:
                btn = QPushButton(name)
                self.table_list_layout.addWidget(btn)
                btn.clicked.connect(lambda _, name=name: self.change_table(name))
        except Exception as e:
            Notify.popup("Ошибка", "error", f"Ошибка при чтении таблиц: {e}")
    
    def get_columns(self, table_name): #получение информации о таблице
        try:
            self.connection.table_info(table_name)
            self.connection.table_constraint(table_name)
        except Exception as e:
            Notify.popup("Ошибка", "error", f"Ошибка при чтении информации о таблице: {e}")
        
    def add_table(self): #переключение на создание таблицы
        self.create_table_window()
        self.splitter.replaceWidget(1, self.table_creation)
        
    def change_table(self, table_name): #переключение на изменение таблицы
        self.edit_table_window(table_name)
        self.splitter.replaceWidget(1, self.table_edit)
        
    def create_table_window(self): #виджет для создания таблицы
        self.table_creation = QWidget()
        self.table_creation_layout=QVBoxLayout(self.table_creation)
        
        self.table_name_input = QLineEdit()
        self.table_name_input.setPlaceholderText("Название таблицы")
        
        self.column_scroll_area = QScrollArea()
        self.column_scroll_area.setWidgetResizable(True)
        
        self.column_container = QWidget()
        self.columns_layout = QVBoxLayout(self.column_container)
        self.column_scroll_area.setWidget(self.column_container)
        
        self.add_column_btn = QPushButton("+")
        self.add_column_btn.setFixedSize(30, 30)
        self.add_column_btn.clicked.connect(self.add_column)

        self.btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.cancel_cnhanges)
        self.cancel_btn.setFixedSize(90, 40)
        self.btn_layout.addWidget(self.cancel_btn)
        self.btn_layout.addStretch()
        self.apply_btn = QPushButton("Применить")
        self.apply_btn.clicked.connect(self.create_table)
        self.apply_btn.setFixedSize(110, 40)
        self.btn_layout.addWidget(self.apply_btn)

        self.table_creation_layout.addWidget(QLabel("Создание новой таблицы"))
        self.table_creation_layout.addWidget(self.table_name_input)
        self.table_creation_layout.addWidget(self.column_scroll_area)
        self.table_creation_layout.addWidget(self.add_column_btn, alignment=Qt.AlignCenter)
        self.table_creation_layout.addLayout(self.btn_layout)
    
    def create_table(self): #создание таблицы
        table_name = self.table_name_input.text()
        if not table_name:
            Notify.popup("Ошибка", "error", "Название таблицы не может быть пустым")
            return
        
        columns = []
        for i in range(self.columns_layout.count()):
            widget = self.columns_layout.itemAt(i).widget()
            column_layout = widget.layout()
            column_name = column_layout.itemAt(0).widget().text()
            column_type = column_layout.itemAt(1).widget().currentText()
            primary_key = column_layout.itemAt(2).widget().isChecked()
            if not column_name or not column_type:
                Notify.popup("Ошибка", "error", "Название столбца и тип не могут быть пустыми")
                return
            columns.append({"name": column_name, 
                            "type": column_type, 
                            "p_key": primary_key})
        res = self.connection.create_table(table_name, columns)
        if isinstance(res, Exception):
            Notify.popup("Ошибка", "error", f"Ошибка при создании таблицы: {res}")
        else:
            Notify.popup("Успех", "info", "Таблица успешно создана")
            self.initUI()
        
    def add_column(self, name=None, type=None, p_key=None): #добавление столбцов в интерфейс
        column_widget = QWidget()
        column_layout = QHBoxLayout(column_widget)
        
        column_name_input = QLineEdit()
        column_name_input.setPlaceholderText("Название столбца")
        if name: #если открыто в окне редактирования и название уже есть, загружаем его
            column_name_input.setText(name)
            column_name_input.setProperty("orig_name", name)
        
        column_type_input = QComboBox()
        column_type_input.addItems(["INT", "REAL", "TEXT", "DATE", "TIMESTAMP"])
        if type: #если открыто в окне редактирования и тип уже есть
            column_type_input.setCurrentText(type)
        
        primary_key_checkbox = QCheckBox("PRIMARY KEY")
        if p_key: #если первичный ключ уже есть
            primary_key_checkbox.setChecked(p_key)
        
        remove_column_btn = QPushButton("-")
        remove_column_btn.clicked.connect(lambda: self.remove_column(column_widget))
        remove_column_btn.setFixedSize(30, 30)
        
        column_layout.addWidget(column_name_input)
        column_layout.addWidget(column_type_input)
        column_layout.addWidget(primary_key_checkbox)
        column_layout.addWidget(remove_column_btn)
        
        self.columns_layout.addWidget(column_widget)
    
    def remove_column(self, column_widget): #удаление столбца
        self.columns_layout.removeWidget(column_widget)
        column_widget.deleteLater()
        
    def cancel_cnhanges(self): #отмена редактирования
        self.initUI()
    
    def edit_table_window(self, table_name): #виджет для редактирования таблицы
        self.table_edit = QWidget()
        self.table_edit_layout=QVBoxLayout(self.table_edit)
        
        self.table_name_input = QLineEdit()
        self.table_name_input.setText(table_name)
        
        self.column_scroll_area = QScrollArea()
        self.column_scroll_area.setWidgetResizable(True)
        
        self.column_container = QWidget()
        self.columns_layout = QVBoxLayout(self.column_container)
        self.column_scroll_area.setWidget(self.column_container)
        
        self.add_column_btn = QPushButton("+")
        self.add_column_btn.setFixedSize(30, 30)
        self.add_column_btn.clicked.connect(self.add_column)

        self.btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.cancel_cnhanges)
        self.cancel_btn.setFixedSize(90, 40)
        self.apply_btn = QPushButton("Применить")
        self.apply_btn.clicked.connect(lambda: self.edit_table(table_name))
        self.apply_btn.setFixedSize(110, 40)
        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(lambda: self.delete_table(table_name))
        self.delete_btn.setFixedSize(90, 40)
        self.btn_layout.addWidget(self.delete_btn)
        self.btn_layout.addStretch()
        self.btn_layout.addWidget(self.apply_btn)
        self.btn_layout.addWidget(self.cancel_btn)

        self.table_edit_layout.addWidget(QLabel("Редактирование таблицы"))
        self.table_edit_layout.addWidget(self.table_name_input)
        self.table_edit_layout.addWidget(self.column_scroll_area)
        self.table_edit_layout.addWidget(self.add_column_btn, alignment=Qt.AlignCenter)
        self.table_edit_layout.addLayout(self.btn_layout)
        
        self.load_columns(table_name)
        
    def load_columns(self, table_name): #загрузка существующих столбцов
        try:
            columns = self.connection.table_info(table_name)
            constraints = self.connection.table_constraint(table_name)
        
            for column in columns:
                name = column[0]
                col_type = column[1]
                is_primary_key = name in constraints
                self.add_column(name, col_type, is_primary_key)
        except Exception as e:
            Notify.popup("Ошибка", "error", f"Ошибка при чтении столбцов: {e}")
            
    def edit_table(self, table_name): #изменение таблицы
        new_table_name = self.table_name_input.text()
        columns = []
        
        for i in range(self.columns_layout.count()):
            widget = self.columns_layout.itemAt(i).widget()
            column_layout = widget.layout()
            column_name = column_layout.itemAt(0).widget().text()
            column_type = column_layout.itemAt(1).widget().currentText()
            primary_key = column_layout.itemAt(2).widget().isChecked()
            
            orig_name = column_layout.itemAt(0).widget().property("orig_name")
            
            if not column_name or not column_type:
                Notify.popup("Ошибка", "error", "Название столбца и тип не могут быть пустыми")
                return
            columns.append({"name": column_name if column_name != orig_name else orig_name, 
                            "orig_name": orig_name,
                            "type": column_type, 
                            "p_key": primary_key})
        
        res = self.connection.edit_table_content(table_name, new_table_name, columns)
        if isinstance(res, Exception):
            Notify.popup("Ошибка", "error", f"Ошибка при изменении таблицы: {res}")
        else:
            Notify.popup("Успех", "info", "Таблица успешно изменена")
            self.initUI()
       
        
    def delete_table(self, table_name): #удаление таблицы
        res = self.connection.delete_table(table_name)
        
        if isinstance(res, Exception):
            Notify.popup("Ошибка", "error", f"Ошибка при удалении таблицы: {res}")
        else:
            Notify.popup("Успех", "info", "Таблица успешно удалена")
            self.initUI()
