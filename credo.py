import paramiko
import pandas
import io
import threading
import time

# folder_list = ["01_GF_test_report", "02_lineside_test_report", "03_autotuning_test_report", 
#                "05_function_test_report", "05_function_test_report_TST", "06_pc_test_report", 
#                "08_tc_test_report", "10_Pin_test_report", "10_Pin_test_report_Prod", "12_WLT_test_report", "13_1pps_test_report"]
folder_list = ["03_autotuning_test_report"]
target = {
    "200G_QSFP56_Gen3_Straight": "200G_Ursula_S cable",
    "200G_QSFP56_Gen3": "200G_Ursula_S cable",
    "400G_2xQ56_TO_2xQ56_Gen3": "400G_Ursula_X cable",
    "400G_QDD_TO_2xQ56_Ursula": "400G_Ursula_Y cable",
    "400G_QSFP-DD_Gen3": "400G_G3",
    "400G_QSFP-DD_Ursula_1PPS": "400G_Ursula_S cable",
}

def connect_sftp():
    trans = paramiko.Transport(("10.31.2.10", 22))
    trans.connect(username=r"bizlinktech\harry_wu", password="H@rrywu201314nana")
    sftp = paramiko.SFTPClient.from_transport(trans)
    return sftp, trans

def find_target_folders(sftp:paramiko.sftp_client.SFTPClient, current_path): #find target folders
    inthreads = []
    items = sftp.listdir(current_path)
    for item in items:
        if not "." in item:
            new_path = f"{current_path}/{item}"
            if item in target:
                sftp2, trans = connect_sftp()
                thread = threading.Thread(target=find_FP_folder, args=(sftp2, new_path))
                inthreads.append(thread)
                thread.start()
            else:
                find_target_folders(sftp, new_path)

    for inthread in inthreads:
        inthread.join()

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
                    sftp.stat(f"{current_path}/EXTRACT DATA_{wo}")
                except FileNotFoundError:
                    sftp.mkdir(f"{current_path}/EXTRACT DATA_{wo}")
                csv_path = f"{current_path}/EXTRACT DATA_{wo}/{wo} REPORT TEMPLATE_{fp}.csv"
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
    return

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
    return data_

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

def main():
    start = time.time()
    path = "/Credo_SFTP_PE/Report"
    threads = []
    for folder in folder_list:
        sftp, trans = connect_sftp()
        path2 = f"{path}/{folder}"
        thread = threading.Thread(target=find_target_folders, args=(sftp, path2))
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