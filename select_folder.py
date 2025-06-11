import paramiko
import sys
import stat
from PySide6.QtWidgets import (
    QDialog, QTreeView, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QApplication, QMainWindow, QLabel, QWidget
)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, QModelIndex


class RemoteFolderDialog(QDialog):
    def __init__(self, sftp, start_path="/", parent=None):
        super().__init__(parent)
        self.setWindowTitle("選取遠端資料夾")
        self.resize(600, 400)

        self.sftp = sftp
        self.start_path = start_path
        self.selected_folders = set()

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["遠端目錄"])

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setSelectionMode(QTreeView.ExtendedSelection)
        self.tree.doubleClicked.connect(self.expand_folder)

        self.load_remote_dir(self.start_path, self.model.invisibleRootItem())

        self.ok_button = QPushButton("確認")
        self.cancel_button = QPushButton("取消")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tree)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def load_remote_dir(self, path, parent_item):
        try:
            for item in self.sftp.listdir_attr(path):
                if stat.S_ISDIR(item.st_mode):
                    folder_item = QStandardItem(item.filename)
                    folder_item.setData(f"{path}/{item.filename}".replace("//", "/"), Qt.UserRole)
                    folder_item.setEditable(False)
                    folder_item.setSelectable(True)
                    folder_item.setCheckable(False)
                    parent_item.appendRow(folder_item)
        except Exception as e:
            QMessageBox.warning(self, "錯誤", f"無法讀取目錄: {e}")

    def expand_folder(self, index: QModelIndex):
        item = self.model.itemFromIndex(index)
        if item and item.hasChildren():
            return
        path = item.data(Qt.UserRole)
        self.load_remote_dir(path, item)

    def get_selected_folders(self):
        for index in self.tree.selectionModel().selectedRows():
            item = self.model.itemFromIndex(index)
            path = item.data(Qt.UserRole)
            if path:
                self.selected_folders.add(path)
        return list(self.selected_folders)