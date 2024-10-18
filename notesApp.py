import sys
import pandas as pd
import sqlite3
from PyQt6 import QtWidgets as qw
from PyQt6.QtWidgets import (QMessageBox, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QCheckBox)
from PyQt6.QtCore import Qt, QDate, pyqtSignal

class SQLiteConnection:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.connection.row_factory = sqlite3.Row

    def get_cursor(self):
        return self.connection.cursor()

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()

class MyWindow(qw.QWidget):
    def __init__(self, username):
        super().__init__()
        self.setWindowTitle(f"NoteBook App. User - {username}")
        self.resize(800, 800)
        self.sqlite = SQLiteConnection("notesApp.db")
        self.user_session = username

        self.create_btn = QPushButton("Create")
        self.delete_btn = QPushButton("Delete")
        self.update_btn = QPushButton("Update")
        self.export_btn = QPushButton("Export")
        self.logout_btn = QPushButton("Logout")
        
        self.initUI()
        self.loadData()

    def initUI(self):
        self.Mainlayout = QVBoxLayout()
        self.setLayout(self.Mainlayout)

        row1 = QHBoxLayout()
        welcome_label = QLabel(f"Hello, {self.user_session}")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row1.addWidget(welcome_label)

        row2 = QHBoxLayout()
        row2.addWidget(self.create_btn)
        row2.addWidget(self.update_btn)
        row2.addWidget(self.delete_btn)
        row2.addWidget(self.export_btn)
        row2.addWidget(self.logout_btn)

        self.table = qw.QTableWidget()
        self.table.setColumnCount(5)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 250)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 60)
        self.table.setHorizontalHeaderLabels(["ID", "Title", "Description", "Date", "Action"])

        self.Mainlayout.addLayout(row1)
        self.Mainlayout.addLayout(row2)
        self.Mainlayout.addWidget(self.table)

        self.create_btn.clicked.connect(self.gotoCreate)
        self.update_btn.clicked.connect(self.gotoUpdate)
        self.delete_btn.clicked.connect(self.deleteData)
        self.export_btn.clicked.connect(self.exportData)
        self.logout_btn.clicked.connect(self.logoutUser)

    def gotoCreate(self):
        self.createClass = Create(self.user_session)
        self.createClass.newSignal.connect(self.loadData)
        self.createClass.show()

    def loadData(self):
        try:
            cursor = self.sqlite.get_cursor()
            cursor.execute("SELECT id, title, description, upload_date FROM notes WHERE uname = ?", (self.user_session,))
            rows = cursor.fetchall()
            self.table.clear()
            self.table.setHorizontalHeaderLabels(["ID","Title", "Description", "Date", "Action"])
            self.table.setRowCount(0)

            if rows:
                self.table.setRowCount(len(rows))
                for row_index, row_data in enumerate(rows):
                    for column_index, value in enumerate(row_data):
                        item = qw.QTableWidgetItem(str(value))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                        self.table.setItem(row_index, column_index, item)

                    btn = QCheckBox()
                    self.table.setCellWidget(row_index, 4, btn)

            else:
                QMessageBox.information(self, "No notes found", "You haven't created any notes yet.")

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Error fetching data: {e}")

    def gotoUpdate(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.critical(self, "No row Selected", "Please Select a row you want to update")
            return
        note_id = int(self.table.item(selected_row, 0).text())
        self.updateClass = Update(note_id, self.user_session)
        self.updateClass.signal.connect(self.loadData)
        self.updateClass.show()

    def deleteData(self):
        check_box_selected = []
        for row in range(self.table.rowCount()):
            checkBox = self.table.cellWidget(row, 4)
            if checkBox is not None and checkBox.isChecked():
                note_id = int(self.table.item(row, 0).text())
                check_box_selected.append(note_id)

        if not check_box_selected:
            QMessageBox.critical(self, "No CheckBox Selected", "Please Select a CheckBox you want to delete")
            return
        
        confirm = QMessageBox.question(self, "Delete Note", f"Do you really want to delete these note IDs: {check_box_selected}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if confirm == QMessageBox.StandardButton.Yes:
            cursor = self.sqlite.get_cursor()
            try:
                for note_id in check_box_selected:
                    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
                self.sqlite.commit()
                self.loadData()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Error deleting data: {e}")

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            for widget in self.findChildren(QPushButton):
                if widget.hasFocus():
                    widget.click()
                    break  
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.sqlite.close()
        event.accept()

    def exportData(self):
        row = self.table.rowCount()
        col = self.table.columnCount()
        data = []
        colName = []

        for j in range(col - 1):
            headItem = self.table.horizontalHeaderItem(j)
            if headItem is not None:
                colName.append(headItem.text())

        for i in range(row):
            rowData = []
            for j in range(col - 1):
                item = self.table.item(i, j)
                if item is not None:
                    rowData.append(item.text())
                else:
                    rowData.append(None)
            data.append(rowData)

        try:
            df = pd.DataFrame(data, columns=colName)
            df.to_csv("notes_data.csv", index=False)
        except Exception as e:
            print("Error ->", e)

    def logoutUser(self):
        self.close()
        self.user_session = ""
        self.loginWindow = Login()
        self.loginWindow.show()

class Signup(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Signup Form")
        self.resize(300, 250)

        self.name = QLineEdit()
        self.username = QLineEdit()
        self.passwd = QLineEdit()
        self.passwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.cpasswd = QLineEdit()
        self.cpasswd.setEchoMode(QLineEdit.EchoMode.Password)
        self.signup_btn = QPushButton("Sign Up")
        self.login_btn = QPushButton("Login")

        self.sqlite = SQLiteConnection("notesApp.db")
        self.initUI()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            for widget in self.findChildren(QPushButton):
                if widget.hasFocus():
                    widget.click()  
                    break  
            super().keyPressEvent(event)

    def checkInput(self):
        for line_edit in self.findChildren(QLineEdit):
            if line_edit.text().strip() == "":
                QMessageBox.warning(self, "Empty fields", "Can't leave any field blank")
                return False
        return True

    def initUI(self):
        self.main_layout = QVBoxLayout()

        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: black; 
                font-weight: bold; 
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.signup_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Name: "))
        row1.addWidget(self.name)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Username: "))
        row2.addWidget(self.username)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Password: "))
        row3.addWidget(self.passwd)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Confirm Password: "))
        row4.addWidget(self.cpasswd)

        row5 = QHBoxLayout()
        row5.addWidget(self.signup_btn)

        row6 = QHBoxLayout()
        row6.addWidget(QLabel("Already have an account? "))
        row6.addWidget(self.login_btn)
        
        self.main_layout.addLayout(row1)
        self.main_layout.addLayout(row2)
        self.main_layout.addLayout(row3)
        self.main_layout.addLayout(row4)
        self.main_layout.addLayout(row5)
        self.main_layout.addLayout(row6)

        self.setLayout(self.main_layout)
        self.signup_btn.clicked.connect(self.insertData)
        self.login_btn.clicked.connect(self.gotoLogin)

    def insertData(self):
        name = self.name.text()
        username = self.username.text()
        passwd = self.passwd.text()
        cpasswd = self.cpasswd.text()

        if not self.checkInput():
            return

        if passwd != cpasswd:
            QMessageBox.critical(self, "Error", "Passwords do not match!")
            return

        cursor = self.sqlite.get_cursor()
        try:
            cursor.execute("INSERT INTO signup (name, uname, passwd) VALUES (?, ?, ?)", (name, username, passwd))
            self.sqlite.commit()
            QMessageBox.information(self, "Success", "Signup successful!")
            self.gotoLogin()
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Error", "Username already exists.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Error: {e}")
        finally:
            cursor.close()

    def gotoLogin(self):
        self.close()
        self.loginWindow = Login()
        self.loginWindow.show()

class Login(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login Form")
        self.resize(300, 150)

        self.username = QLineEdit()
        self.passwd = QLineEdit()
        self.passwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_btn = QPushButton("Login")
        self.signup_btn = QPushButton("Signup")

        self.sqlite = SQLiteConnection("notesApp.db")
        self.initUI()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            for widget in self.findChildren(QPushButton):
                if widget.hasFocus():
                    widget.click()  
                    break  
            super().keyPressEvent(event)

    def initUI(self):
        self.main_layout = QVBoxLayout()

        self.signup_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: black; 
                font-weight: bold; 
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        
        self.signup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Username: "))
        row1.addWidget(self.username)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Password: "))
        row2.addWidget(self.passwd)

        row3 = QHBoxLayout()
        row3.addWidget(self.login_btn)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Don't have an account? "))
        row4.addWidget(self.signup_btn)

        self.main_layout.addLayout(row1)
        self.main_layout.addLayout(row2)
        self.main_layout.addLayout(row3)
        self.main_layout.addLayout(row4)

        self.setLayout(self.main_layout)
        self.login_btn.clicked.connect(self.checkLogin)
        self.signup_btn.clicked.connect(self.gotoSignup)

    def checkLogin(self):
        username = self.username.text()
        passwd = self.passwd.text()

        if not username or not passwd:
            QMessageBox.warning(self, "Input Error", "Please fill all fields.")
            return

        cursor = self.sqlite.get_cursor()
        cursor.execute("SELECT * FROM signup WHERE uname = ? AND passwd = ?", (username, passwd))
        result = cursor.fetchone()

        if result:
            self.gotoMainWindow(username)
        else:
            QMessageBox.critical(self, "Error", "Invalid credentials.")

        cursor.close()

    def gotoMainWindow(self, username):
        self.close()
        self.mainWindow = MyWindow(username)
        self.mainWindow.show()

    def gotoSignup(self):
        self.close()
        self.signupWindow = Signup()
        self.signupWindow.show()

class Create(QWidget):
    newSignal = pyqtSignal()

    def __init__(self, username):
        super().__init__()
        self.setWindowTitle("Create Note")
        self.resize(400, 300)
        self.username = username

        self.title = QLineEdit()
        self.description = QTextEdit()
        self.create_btn = QPushButton("Create Note")
        self.cancel_btn = QPushButton("Cancel")

        self.sqlite = SQLiteConnection("notesApp.db")
        self.initUI()

    def initUI(self):
        self.main_layout = QVBoxLayout()
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Title: "))
        row1.addWidget(self.title)

        self.main_layout.addLayout(row1)
        self.main_layout.addWidget(QLabel("Description: "))
        self.main_layout.addWidget(self.description)
        row2 = QHBoxLayout()
        row2.addWidget(self.create_btn)
        row2.addWidget(self.cancel_btn)

        self.main_layout.addLayout(row2)
        self.setLayout(self.main_layout)

        self.create_btn.clicked.connect(self.insertNote)
        self.cancel_btn.clicked.connect(self.close)

    def insertNote(self):
        title = self.title.text()
        description = self.description.toPlainText()
        upload_date = QDate.currentDate().toString("yyyy-MM-dd")

        if not title or not description:
            QMessageBox.warning(self, "Input Error", "Title and Description cannot be empty.")
            return

        cursor = self.sqlite.get_cursor()
        try:
            cursor.execute("INSERT INTO notes (uname, title, description, upload_date) VALUES (?, ?, ?, ?)", (self.username, title, description, upload_date))
            self.sqlite.commit()
            QMessageBox.information(self, "Success", "Note created successfully!")
            self.newSignal.emit()  # Emit signal to refresh the notes
            self.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Error creating note: {e}")
        finally:
            cursor.close()

class Update(QWidget):
    signal = pyqtSignal()

    def __init__(self, note_id, username):
        super().__init__()
        self.setWindowTitle("Update Note")
        self.resize(400, 300)
        self.note_id = note_id
        self.username = username

        self.title = QLineEdit()
        self.description = QTextEdit()
        self.update_btn = QPushButton("Update Note")
        self.cancel_btn = QPushButton("Cancel")

        self.sqlite = SQLiteConnection("notesApp.db")
        self.initUI()
        self.loadNote()

    def initUI(self):
        self.main_layout = QVBoxLayout()
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Title: "))
        row1.addWidget(self.title)

        self.main_layout.addLayout(row1)
        self.main_layout.addWidget(QLabel("Description: "))
        self.main_layout.addWidget(self.description)
        row2 = QHBoxLayout()
        row2.addWidget(self.update_btn)
        row2.addWidget(self.cancel_btn)

        self.main_layout.addLayout(row2)
        self.setLayout(self.main_layout)

        self.update_btn.clicked.connect(self.updateNote)
        self.cancel_btn.clicked.connect(self.close)

    def loadNote(self):
        cursor = self.sqlite.get_cursor()
        cursor.execute("SELECT title, description FROM notes WHERE id = ?", (self.note_id,))
        note = cursor.fetchone()
        if note:
            self.title.setText(note['title'])
            self.description.setPlainText(note['description'])
        cursor.close()

    def updateNote(self):
        title = self.title.text()
        description = self.description.toPlainText()

        if not title or not description:
            QMessageBox.warning(self, "Input Error", "Title and Description cannot be empty.")
            return

        cursor = self.sqlite.get_cursor()
        try:
            cursor.execute("UPDATE notes SET title = ?, description = ? WHERE id = ?", (title, description, self.note_id))
            self.sqlite.commit()
            QMessageBox.information(self, "Success", "Note updated successfully!")
            self.signal.emit()  # Emit signal to refresh the notes
            self.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Error updating note: {e}")
        finally:
            cursor.close()

def setup_database():
    conn = sqlite3.connect("notesApp.db")
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS signup (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        uname TEXT UNIQUE NOT NULL,
        passwd TEXT NOT NULL
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uname TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        upload_date TEXT NOT NULL
    )''')

    conn.commit()
    conn.close()

def main():
    setup_database()
    app = qw.QApplication(sys.argv)
    login = Login()
    login.show()  
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
