import paramiko
import pandas
import io
import threading
import time
import stat

#####Threading#####

folder_list = ["01_GF_test_report", "02_lineside_test_report", "03_autotuning_test_report", 
               "05_function_test_report", "05_function_test_report_TST", "06_pc_test_report", 
               "08_tc_test_report", "10_Pin_test_report", "10_Pin_test_report_Prod", "12_WLT_test_report", "13_1pps_test_report"]


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

def find_target_folders(sftp:paramiko.sftp_client.SFTPClient, current_path, target_path:list):
    inthreads = []
    items = sftp.listdir(current_path)
    for item in items:
        if not "." in item:
            new_path = f"{current_path}/{item}"
            if item in target:
                sftp2, trans2 = connect_sftp()
                thread = threading.Thread(target=find_txt_csv, args=(sftp2, new_path, target_path))
                thread.start()
                inthreads.append(thread)
                print(new_path)
            else:
                find_target_folders(sftp, new_path, target_path)

    for inthread in inthreads:
        inthread.join()

def find_txt_csv(sftp, current_path, result_path:list):
    items = sftp.listdir(current_path)
    for item in items:
        new_path = f"{current_path}/{item}"
        if not "." in item:
            find_txt_csv(sftp, new_path, result_path)
        else:
            if item.endswith(('.csv')):
                result_path.append(new_path)
    return

def read_file_sftp(sftp:paramiko.sftp_client.SFTPClient, file_path):
    with sftp.open(file_path, 'r') as remote_file:
        file = remote_file.read().decode('utf-8')
        datas = pandas.read_csv(io.StringIO(file), header=None, sep='\t')
    data_list = []
    for data in datas[0]:
        data_list.append(data.split(','))

    df = pandas.DataFrame(data_list)
    return df
    


start = time.time()
path = "/Credo_SFTP_PE/Report"
target_path = {folder: [] for folder in folder_list}
threads = []
for folder in folder_list:
    sftp, trans = connect_sftp()
    path2 = f"{path}/{folder}"
    thread = threading.Thread(target=find_target_folders, args=(sftp, path2, target_path[folder]))
    threads.append(thread)
    thread.start()
    print(f"start: {folder}")

i = 1
for thread in threads:
    print(f"{i} Start")
    thread.join()
    print(f"{i} End")
    i += 1

# 所有 thread join 結束後統一寫 CSV
for folder, paths in target_path.items():
    df = pandas.DataFrame(paths)
    df.to_csv(f"{folder}.csv", index=False, header=False)

total_count = sum(len(v) for v in target_path.values())
print(f"總共有: {total_count} 個檔案")
end = time.time()
print(f"耗時: {end-start:.2f} 秒")
sftp.close()
trans.close()