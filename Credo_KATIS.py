from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QListView, QTreeView, QMessageBox
from GUI import Ui_MainWindow
from select_folder import RemoteFolderDialog
import os
from dotenv import load_dotenv, set_key
import threading
import paramiko

target = {
    "200G_QSFP56_Gen3_Straight": "200G_Ursula_S cable",
    "200G_QSFP56_Gen3": "200G_Ursula_S cable",
    "400G_2xQ56_TO_2xQ56_Gen3": "400G_Ursula_X cable",
    "400G_QDD_TO_2xQ56_Ursula": "400G_Ursula_Y cable",
    "400G_QSFP-DD_Gen3": "400G_G3",
    "400G_QSFP-DD_Ursula_1PPS": "400G_Ursula_S cable",
}

class MainWindow(QMainWindow):
    def __init__(self):
        load_dotenv()
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.set_init_data()
        self.ui.selectFilesLabel.setText("尚未選取資料夾")
        self.ui.pushButton.setEnabled(False)
        

        self.file_paths = set()
        self.threads = []
        self.ui.fileFromButton.clicked.connect(self.select_remote_folders)
        self.ui.pushButton.clicked.connect(self.start_extract)
    
    def connect_sftp(self):
        trans = paramiko.Transport((self.ui.fromIP.toPlainText(), 22))
        trans.connect(username=self.ui.fromUsername.toPlainText(), password=self.ui.fromPassword.toPlainText())
        sftp = paramiko.SFTPClient.from_transport(trans)
        return sftp, trans

    def set_init_data(self):
        self.ui.fromIP.setText(os.getenv('IP', ""))
        self.ui.fromUsername.setText(os.getenv("USERNAME", ""))
        self.ui.fromPassword.setText(os.getenv("PASSWORD", ""))

    def setLabelText(self):
        text = "已選取:\n"
        files = "\n".join(self.file_paths)
        text += files
        self.ui.selectFilesLabel.setText(text)

    def select_remote_folders(self):
        try:
            sftp, trans = self.connect_sftp()
            dialog = RemoteFolderDialog(sftp, "/")
            if dialog.exec():
                folders = dialog.get_selected_folders()
                self.file_paths.update(folders)
                self.setLabelText()
                self.ui.pushButton.setEnabled(True)

            sftp.close()
            trans.close()
        except Exception as e:
            QMessageBox.critical(self, "連線錯誤", str(e))        

        set_key(".env", "IP", self.ui.fromIP.toPlainText())
        set_key(".env", "USERNAME", self.ui.fromUsername.toPlainText())
        set_key(".env", "PASSWORD", self.ui.fromPassword.toPlainText())

    def start_extract(self):
        for file_path in self.file_paths:
            sftp, trans = self.connect_sftp()
            thread = threading.Thread(target="", args=())
            self.threads.append(thread)
            thread.start()

        for thread in self.threads:
            thread.join()

        self.file_paths.clear()
        self.ui.selectFilesLabel.setText("已完成，請重新選取資料夾")
        self.ui.pushButton.setEnabled(False)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
