from PyQt5.QtWidgets import QMessageBox

class Notify: # класс для всплывающих уведомлений
    @staticmethod
    def popup(title, type, message): #метод, выводящий уведомление (заголовок, тип (error, info), текст)
        msg = QMessageBox()
        if type == "error":
            msg.setIcon(QMessageBox.Critical)
        elif type == "info":
            msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStyleSheet("""
            QPushButton {
                background-color: #1230AB;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border-radius: 15px;
            }
        """)
        msg.exec_()