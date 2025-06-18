from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QListView, QTreeView, QMessageBox
from GUI import Ui_MainWindow
from select_folder import RemoteFolderDialog
from credo import find_target_folders
import os
from dotenv import load_dotenv, set_key
import threading
import paramiko
import pandas
import io
from dateutil import parser
from PySide6.QtCore import QObject, Signal
from datetime import datetime

target = {
    "200G_QSFP56_Gen3_Straight": "200G_Ursula_S cable",
    "200G_QSFP56_Gen3": "200G_Ursula_S cable",
    "400G_2xQ56_TO_2xQ56_Gen3": "400G_Ursula_X cable",
    "400G_QDD_TO_2xQ56_Ursula": "400G_Ursula_Y cable",
    "400G_QSFP-DD_Gen3": "400G_G3",
    "400G_QSFP-DD_Ursula_1PPS": "400G_Ursula_S cable",
}

def find_FP_folder(sftp:paramiko.sftp_client.SFTPClient, current_path): #find csv
    items = sftp.listdir(current_path)
    for item in items:
        new_path = f"{current_path}/{item}"
        if not "." in item:
            if item.lower().endswith(('_f', '_p')):
                info = item.split('_')
                wo = info[0]
                fp = info[1]
                #沒資料夾的話產生資料夾
                try:
                    sftp.stat(f"/Credo_DTO/EXTRACT DATA_{wo}")
                except FileNotFoundError:
                    sftp.mkdir(f"/Credo_DTO/EXTRACT DATA_{wo}")
                csv_path = f"/Credo_DTO/EXTRACT DATA_{wo}/{wo} REPORT TEMPLATE_{fp}.csv"
                #collect data
                all_data = []
                record_sn = {}
                find_csv_file(sftp, new_path, all_data, record_sn)
                # build csv
                commit_df = pandas.DataFrame(all_data)
                commit_df.insert(0, 'No.', commit_df.index+1)
                csv = commit_df.to_csv(index=False)
                buffer = io.BytesIO(csv.encode('utf-8'))
                buffer.seek(0)

                sftp.putfo(buffer, csv_path)
                buffer.close()
            else:
                if not item.startswith("EXTRACT"):
                    find_FP_folder(sftp, new_path)

def find_csv_file(sftp:paramiko.sftp_client.SFTPClient, file_path, all_data, record_sn):
    files = sftp.listdir(file_path)
    for file in files:
        new_path = f"{file_path}/{file}"

        if not "." in file: #find folder under FP
            find_csv_file(sftp, new_path, all_data, record_sn)

        if file.endswith('.csv'): #find csv under FP
            data = read_save_csv(sftp, new_path)
            if data:
                if data['SN'] in record_sn:
                    index = record_sn[data['SN']]
                    all_data[index]['Testing Frequency'] += 1
                else:
                    record_sn[data['SN']] = len(all_data)
                    all_data.append(data) 

                if any("Board SN" in key for key in data):
                    index = record_sn[data['SN']]
                    first1 = all_data[index]['First Testing Date & Time']
                    first2 = data['First Testing Date & Time']
                    last1 = all_data[index]['Last Testing Date & Time']
                    last2 = data['Last Testing Date & Time']

                    first1 = ensure_datetime(first1)
                    first2 = ensure_datetime(first2)
                    last1 = ensure_datetime(last1)
                    last2 = ensure_datetime(last2)
                    all_data[index]['First Testing Date & Time'] = pick_earlier(first1, first2)
                    all_data[index]['Last Testing Date & Time'] = pick_later(last1, last2)


def ensure_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return parser.parse(value)

def pick_earlier(a, b):
    if a is None:
        return b
    if b is None:
        return a
    
    return min(a, b)

def pick_later(a, b):
    if a is None:
        return b
    if b is None:
        return a

    return max(a, b)
                           
def read_save_csv(sftp:paramiko.sftp_client.SFTPClient, file_path):
    if sftp.stat(file_path).st_size == 0:
        return None
    
    with sftp.open(file_path, 'r') as f:
        file = f.read().decode('utf-8', errors='ignore')
        datas = pandas.read_csv(io.StringIO(file), header=None, sep='\t', on_bad_lines='skip')
    
    try:
        data_list= []
        for data in datas[0]:
            data_list.append(data.split(','))
    except:
        return None

    df = pandas.DataFrame(data_list)
    
    titles = df.iloc[0]
    col_partnum = find_column_index(titles, 'Part Num')
    col_time = find_column_index(titles, 'Test Time')
    col_script = find_column_index(titles, 'Script Ver')
    csv_data = df.iloc[1:]
    part_num = find_index_data(csv_data, col_partnum)
    test_time = find_index_data(csv_data, col_time)
    script = find_index_data(csv_data, col_script)
    sn = file_path.split('/')[-1].split('_')[0]

    data_ = {
        "SN": sn,
        "Part Number": part_num,
        "Script": script,
        "Testing Frequency": 1,
        "Testing Date & Time": test_time
    }

    if file_path.split('/')[3] in ['05_function_test_report_TST', '10_Pin_test_report']:
        board_sn = ""
        board_sn_path = file_path.replace('test_log.csv', "all_log.txt")
        try: #以免檔案不存在
            board_sn = read_board_sn(sftp, board_sn_path)
        except:
            pass
        
        data_ = {
            "SN": sn,
            "Part Number": part_num,
            "Script": script,
            "Testing Frequency": 1,
            "First Testing Date & Time": test_time,
            "Last Testing Date & Time" : test_time,
            "Board SN": board_sn
        }
    
    return data_

def read_board_sn(sftp:paramiko.sftp_client.SFTPClient, file_path):
    sn = ""
    with sftp.open(file_path, 'r') as file:
        content = file.read().decode('utf-8')
        contents = content.split('\n')
        file.close()
    for content in contents:
        if "Board SN" in content:
            try:
                sn = content.split('|')[2].strip()
            except:
                sn = ""
    return sn

def find_column_index(df, target):
    matches = df[df == target]
    if not matches.empty:
        return matches.index[0]
    else:
        return None
    
def find_index_data(df, index):
    if index is None:
        return None
    
    for i in range(len(df)):
        try:
            data = df.iloc[i][index]
            if data is not None and data != "":
                return data
        except:
            return None
        
    return None

class SignalEmitter(QObject):
    all_done = Signal()

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
        self.signal_emitter = SignalEmitter()
        self.signal_emitter.all_done.connect(self.on_all_done)
    
    def connect_sftp(self):
        trans = paramiko.Transport((self.ui.fromIP.toPlainText(), int(self.ui.fromPort.toPlainText())))
        trans.connect(username=self.ui.fromUsername.toPlainText(), password=self.ui.fromPassword.toPlainText())
        sftp = paramiko.SFTPClient.from_transport(trans)
        return sftp, trans

    def set_init_data(self):
        self.ui.fromIP.setText(os.getenv('IP', ""))
        self.ui.fromUsername.setText(os.getenv("USERNAME", ""))
        self.ui.fromPassword.setText(os.getenv("PASSWORD", ""))
        self.ui.fromPort.setText(os.getenv('PORT', ""))

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
        set_key(".env", "PORT", self.ui.fromPort.toPlainText())

    def start_extract(self):
        for file_path in self.file_paths:
            sftp, trans = self.connect_sftp()
            thread = threading.Thread(target=self.find_target_folders, args=(sftp, file_path))
            self.threads.append(thread)
            thread.start()

        threading.Thread(target=self.wait_all_done).start()
        self.ui.pushButton.setEnabled(False)
        self.ui.fileFromButton.setEnabled(False)

    def wait_all_done(self):
        for thread in self.threads:
            thread.join()
        self.signal_emitter.all_done.emit()        

    def on_all_done(self):
        self.file_paths.clear()
        self.ui.selectFilesLabel.setText("已完成，請重新選取資料夾")
        self.ui.pushButton.setEnabled(False)

    def find_target_folders(self, sftp:paramiko.sftp_client.SFTPClient, current_path): #find target folders
        inthreads = []
        items = sftp.listdir(current_path)
        for item in items:
            if not "." in item:
                new_path = f"{current_path}/{item}"
                if item in target:
                    sftp2, trans = self.connect_sftp()
                    thread = threading.Thread(target=find_FP_folder, args=(sftp2, new_path))
                    inthreads.append(thread)
                    thread.start()
                else:
                    self.find_target_folders(sftp, new_path)

        for inthread in inthreads:
            inthread.join()

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
