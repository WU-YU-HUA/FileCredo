from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QListView, QTreeView, QMessageBox
from GUI2 import Ui_MainWindow
from select_folder import RemoteFolderDialog
import os
from dotenv import load_dotenv, set_key
import threading
import paramiko
import pandas
import io
from dateutil import parser
from PySide6.QtCore import QObject, Signal
from datetime import datetime

def find_FP_folder(sftp:paramiko.sftp_client.SFTPClient, current_path, trans): #find csv
    arr_path = current_path.split('/')
    item = arr_path[-1]
    report_type = arr_path[3]
    info = item.split('_', 1)
    wo = info[0]
    fp = info[1]

    base_target_dir = f"/Credo_DTO/{report_type}/{wo}"
    path_components = [comp for comp in base_target_dir.split('/') if comp]
    current_remote_dir = '/' 
    for component in path_components:
        current_remote_dir = current_remote_dir + '/' + component
        try:
            sftp.stat(current_remote_dir)
        except FileNotFoundError:
            sftp.mkdir(current_remote_dir)
        
    csv_path = f"{base_target_dir}/{wo} REPORT TEMPLATE_{fp}.csv"

    #collect data
    all_data = []
    record_sn = {}
    find_csv_file(sftp=sftp, file_path=current_path, all_data=all_data, record_sn=record_sn, fp=fp)
    # build csv
    commit_df = pandas.DataFrame(all_data)
    commit_df.insert(0, 'No.', commit_df.index+1)
    csv = commit_df.to_csv(index=False)
    buffer = io.BytesIO(csv.encode('utf-8'))
    buffer.seek(0)

    sftp.putfo(buffer, csv_path)
    buffer.close()
    sftp.close()
    trans.close()

def find_csv_file(sftp:paramiko.sftp_client.SFTPClient, file_path, all_data, record_sn, fp, own_sn = ""):
    files = sftp.listdir(file_path)
    for file in files:
        new_path = f"{file_path}/{file}"

        if not "." in file: #find folder under FP
            if own_sn == "":
                find_csv_file(sftp=sftp, file_path=new_path, all_data=all_data, record_sn=record_sn, fp=fp ,own_sn=file[:14])
            else:
                find_csv_file(sftp=sftp, file_path=new_path, all_data=all_data, record_sn=record_sn, fp=fp ,own_sn=own_sn)

        if file.endswith('.csv'): #find csv under FP
            data = read_save_csv(sftp, new_path, fp)
            if data:
                if own_sn != "":
                    data['SN'] = own_sn

                if data['SN'] in record_sn:
                    index = record_sn[data['SN']]
                    all_data[index]['Testing Frequency'] += 1
                    if any("Error Message" in key for key in data):
                        all_data[index]['Error Message'] += data['Error Message']
                    if not all_data[index]['Board SN']:
                        all_data[index]['Board SN'] = data['Board SN']
                    if not all_data[index]['Log SN']:
                        all_data[index]['Log SN'] = data['Log SN']
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
                           
def read_save_csv(sftp:paramiko.sftp_client.SFTPClient, file_path, fp:str):
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
    #Get Board SN
    board_sn = ""
    vendor_sn = ""
    try: #以免檔案不存在
        board_sn, vendor_sn = read_board_vendor_sn(sftp, file_path.replace('test_log.csv', "all_log.txt"))
    except:
        pass
    
    if board_sn == "":
        try:
            board_sn, _ = read_board_vendor_sn(sftp, file_path.replace('test_log.csv', "log.txt"))
        except:
            pass
    
    #Get Error Message
    if fp.lower() == 'f':
        err_msg = ""
        try:
            err_msg = get_err_msg(sftp, file_path.replace('test_log.csv', "all_log.txt"))
        except:
            pass

        if err_msg == "":
            try:
                err_msg = get_err_msg(sftp, file_path.replace('test_log.csv', "log.txt"))
            except:
                pass
    
        data_ = {
            "SN": sn,
            "Part Number": part_num,
            "Script": script,
            "Testing Frequency": 1,
            "First Testing Date & Time": test_time,
            "Last Testing Date & Time" : test_time,
            "Board SN": board_sn,
            "Error Message": err_msg,
            "Log SN": vendor_sn
        }
    else:
        data_ = {
            "SN": sn,
            "Part Number": part_num,
            "Script": script,
            "Testing Frequency": 1,
            "First Testing Date & Time": test_time,
            "Last Testing Date & Time" : test_time,
            "Board SN": board_sn,
            "Log SN": vendor_sn
        }
    
    return data_

def read_board_vendor_sn(sftp:paramiko.sftp_client.SFTPClient, file_path):
    sn = ""
    vendor_sn = ""
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
        
        if "VendorSN" in content:
            try:
                vendor_sn = content.split("VendorSN:")[1].split("PCBA_SN")[0].strip()
            except:
                vendor_sn = ""
    return sn, vendor_sn

def get_err_msg(sftp:paramiko.sftp_client.SFTPClient, file_path):
    err_msg = []
    with sftp.open(file_path, 'r') as file:
        content = file.read().decode('utf-8')
        contents = content.split('\n')
        file.close()

    for content in contents:
        if content.startswith('[Err ]'):
            err_msg.append(content)
    return "\n".join(err_msg)

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
        # self.ui.selectFilesLabel.setText("尚未選取資料夾")
        self.ui.pushButton.setEnabled(False)
        

        self.file_paths = set()
        self.threads = []
        self.ui.fileFromButton.clicked.connect(self.select_remote_folders)
        self.ui.pushButton.clicked.connect(self.start_extract)
        self.ui.listWidget.itemDoubleClicked.connect(self.deleteText)
        self.signal_emitter = SignalEmitter()
        self.signal_emitter.all_done.connect(self.on_all_done)
    
    def connect_sftp(self):
        trans = paramiko.Transport((self.ui.fromIP.toPlainText(), int(self.ui.fromPort.toPlainText())))
        trans.connect(username=self.ui.fromUsername.toPlainText(), password=self.ui.fromPassword.text())
        sftp = paramiko.SFTPClient.from_transport(trans)
        return sftp, trans

    def set_init_data(self):
        self.ui.fromIP.setText(os.getenv('IP', ""))
        self.ui.fromUsername.setText(os.getenv("USERNAME", ""))
        self.ui.fromPassword.setText(os.getenv("PASSWORD", ""))
        self.ui.fromPort.setText(os.getenv('PORT', ""))

    def setLabelText(self):
        self.ui.listWidget.clear()
        for path in self.file_paths:
            self.ui.listWidget.addItem(path.split('/', 3)[-1])

    def deleteText(self, item):
        text = f"/Credo_SFTP_PE/Report/{item.text()}"
        if text in self.file_paths:
            self.file_paths.remove(text)
            self.ui.listWidget.takeItem(self.ui.listWidget.row(item))
        
        if len(self.file_paths) == 0:
            self.ui.pushButton.setEnabled(False)

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
        set_key(".env", "PASSWORD", self.ui.fromPassword.text())
        set_key(".env", "PORT", self.ui.fromPort.toPlainText())

    def start_extract(self):
        for file_path in self.file_paths:
            sftp, trans = self.connect_sftp()
            thread = threading.Thread(target=find_FP_folder, args=(sftp, file_path, trans))
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
        self.ui.listWidget.clear()
        self.ui.pushButton.setEnabled(True)
        self.ui.fileFromButton.setEnabled(True)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
