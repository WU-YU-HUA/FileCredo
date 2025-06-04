import paramiko
import pandas
import io
import threading
import time
import stat
import os
from collections import Counter

#####Threading#####

folder_list = ["02_lineside_test_report", "08_tc_test_report"]

target = {
    "200G_QSFP56_Gen3_Straight": "200G_Ursula_S cable",
    "200G_QSFP56_Gen3": "200G_Ursula_S cable",
    "400G_2xQ56_TO_2xQ56_Gen3": "400G_Ursula_X cable",
    "400G_QDD_TO_2xQ56_Ursula": "400G_Ursula_Y cable",
    "400G_QSFP-DD_Gen3": "400G_G3",
    "400G_QSFP-DD_Ursula_1PPS": "400G_Ursula_S cable",
}

def find_target_folders(current_path): #find target folders
    inthreads = []
    items = os.listdir(current_path)
    for item in items:
        if not "." in item:
            new_path = f"{current_path}/{item}"
            if item in target:
                thread = threading.Thread(target=find_FP_folder, args=(new_path,))
                inthreads.append(thread)
                thread.start()
            else:
                find_target_folders(new_path)

    for inthread in inthreads:
        inthread.join()

def find_FP_folder(current_path): #find csv
    items = os.listdir(current_path)
    for item in items:
        new_path = f"{current_path}/{item}"
        if not "." in item:
            if item.lower().endswith(('_f', '_p')):
                info = item.split('_')
                wo = info[0]
                fp = info[1]
                #沒資料夾的話產生資料夾
                if not os.path.exists(f"{current_path}/EXTRACT DATA_{wo}"):
                    os.makedirs(f"{current_path}/EXTRACT DATA_{wo}")
                csv_path = f"{current_path}/EXTRACT DATA_{wo}/{wo} REPORT TEMPLATE_{fp}.csv"
                all_data = []
                record_sn = {}
                find_csv_file(new_path, all_data, record_sn)
                #build csv
                commit_df = pandas.DataFrame(all_data)
                commit_df.insert(0, 'No.', commit_df.index+1)
                commit_df.to_csv(csv_path, index=False)
            else:
                if not item.startswith("EXTRACT"):
                    find_FP_folder(new_path)
    return

def find_csv_file(file_path, all_data, record_sn):
    files = os.listdir(file_path)
    for file in files:
        new_path = f"{file_path}/{file}"

        if not "." in file: #find folder under FP
            find_csv_file(new_path, all_data, record_sn)

        if file.endswith('csv'): #find csv under FP
            data = read_save_csv(new_path)
            if data:
                if data['SN'] in record_sn:
                    index = record_sn[data['SN']]
                    all_data[index]['Testing Frequency'] += 1
                else:
                    record_sn[data['SN']] = len(all_data)
                    all_data.append(data)
    
def read_save_csv(file_path):
    if os.path.getsize(file_path) == 0:
        return None
    datas = pandas.read_csv(file_path, header=None, sep='\t')
    data_list= []
    for data in datas[0]:
        data_list.append(data.split(','))

    df = pandas.DataFrame(data_list)
    
    titles = df.iloc[0]
    col_partnum = find_column_index(titles, 'Part Num')
    col_time = find_column_index(titles, 'Test Time')
    col_script = find_column_index(titles, 'Script Ver')
    df = df.iloc[1:]
    part_num = find_index_data(df, col_partnum)
    test_time = find_index_data(df, col_time)
    script = find_index_data(df, col_script)
    
    sn = file_path.split('/')[-1].split('_')[0]
    data = {
        "SN": sn,
        "Part Number": part_num,
        "Script": script,
        "Testing Frequency": 1,
        "Testing Date & Time": test_time
    }
    return data

def find_column_index(df, target):
    matches = df[df == target]
    if not matches.empty:
        return matches.index[0]
    else:
        return None
    
def find_index_data(df, index):
    if index == None:
        return None
    for i in df.index:
        data = df.iloc[i][index]
        if data is not None and data != "":
            return data

def main():
    start = time.time()
    path = "."
    threads = []
    for folder in folder_list:
        path2 = f"{path}/{folder}"
        thread = threading.Thread(target=find_target_folders, args=(path2,))
        threads.append(thread)
        thread.start()
        print(f"start: {folder}")

    i = 1
    for thread in threads:
        thread.join()
        print(f"{i} End")
        i += 1

    end = time.time()
    print(f"耗時: {end-start:.2f} 秒")

if __name__ == "__main__":
    main()

def read_file_sftp(sftp:paramiko.sftp_client.SFTPClient, file_path):
    with sftp.open(file_path, 'r') as remote_file:
        file = remote_file.read().decode('utf-8')
        datas = pandas.read_csv(io.StringIO(file), header=None, sep='\t')
    data_list = []
    for data in datas[0]:
        data_list.append(data.split(','))

    df = pandas.DataFrame(data_list)
    return df