from dotenv import load_dotenv, set_key
import threading
import paramiko
import pandas
import io
from dateutil import parser
from datetime import datetime
import posixpath
import stat

#Remote Relative
def remote_dir_exists(sftp, path: str) -> bool:
    try:
        return stat_isdir(sftp.stat(path))
    except FileNotFoundError:
        return False
    except IOError:
        return False

def stat_isdir(st):
    """檢查 stat 回傳結果是否為資料夾"""
    return stat.S_ISDIR(st.st_mode)

def connect_sftp():
    trans = paramiko.Transport(("10.31.2.10", 22))
    trans.connect(username="harry_wu", password="H@rrywu201314nana")
    sftp = paramiko.SFTPClient.from_transport(trans)
    trans.set_keepalive(30)
    return sftp, trans

def build_path(path:str):
    ssh = None
    sftp = None
    trans = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("10.31.2.10", port=5207, username="harry_wu", password="H@rrywu201314nana")
        cmd = f"mkdir -p '{path}'"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        err = stderr.read().decode().strip()
        if err:
            raise Exception(err)
    except Exception as e:
        sftp, trans = connect_sftp()
        parts = path.strip("/").split("/")
        full_paths = [posixpath.join(*parts[:i+1]) for i in range(len(parts))]
        null_paths = []
        for full_path in reversed(full_paths):
            if remote_dir_exists(sftp, full_path):
                break
            else:
                null_paths.append(full_path)

        for null_path in reversed(null_paths):
            sftp.mkdir(null_path)
    finally:
        if ssh:
            ssh.close()
        if sftp:
            sftp.close()
        if trans:
            trans.close()

#Work Relative
def find_target(sftp:paramiko.sftp_client.SFTPClient, cur_path, trans):
    try:
        if not "." in cur_path:
            folders = sftp.listdir(cur_path)
            for folder in folders:
                path = f"{cur_path}/{folder}"
                sftp2, trans2 = connect_sftp()

                if path.lower().endswith(("_p", "_f")):
                    find_FP_folder(sftp2, path, trans2)
                elif path.lower().endswith(("_p_r", "_f_r")):
                    pass
                else:
                    thread = threading.Thread(target=find_target, args=(sftp2, path, trans2))
                    threads.append(thread)
                    thread.start()
    finally:
        try:
            sftp.close()
        except:
            pass
        try:
            trans.close()
        except:
            pass

def find_FP_folder(sftp:paramiko.sftp_client.SFTPClient, current_path, trans): #find csv
    arr_path = current_path.split('/')
    item = arr_path[-1]
    report_type = arr_path[3]
    info = item.split('_', 1)
    wo = info[0]
    fp = info[1]
    if arr_path[3] == "13_1pps_test_report":
        base_target_dir = f"/Credo_DTO_Auto/Result/{report_type}/{arr_path[4]}/{wo}" 
    else:
        base_target_dir = f"/Credo_DTO_Auto/Result/{report_type}/{wo}" 
    path_components = [comp for comp in base_target_dir.split('/') if comp]
    current_remote_dir = '/' 
    for component in path_components:
        current_remote_dir = current_remote_dir + '/' + component
        try:
            sftp.stat(current_remote_dir)
        except FileNotFoundError:
            sftp.mkdir(current_remote_dir)
    
    csv_path = f"{base_target_dir}/{wo} REPORT TEMPLATE_{fp}_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.csv"

    #collect data
    all_data = []
    record_sn = {}
    find_csv_file(sftp=sftp, file_path=current_path, all_data=all_data, record_sn=record_sn, fp=fp)
    # build csv
    if all_data:
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
                find_csv_file(sftp=sftp, file_path=new_path, all_data=all_data, record_sn=record_sn, fp=fp ,own_sn=file[:15])
            else:
                find_csv_file(sftp=sftp, file_path=new_path, all_data=all_data, record_sn=record_sn, fp=fp ,own_sn=own_sn)
        else:
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

            new_file = new_path.replace("/Credo_DTO_Auto/Report", "/Credo_DTO_Auto/Extracted_Log")
            try:
                sftp.rename(oldpath=new_path, newpath=new_file)
            except:
                build_path(file_path.replace("/Credo_DTO_Auto/Report", "/Credo_DTO_Auto/Extracted_Log"))
                sftp.rename(oldpath=new_path, newpath=new_file)

def ensure_datetime(value):
    if value is None:
        return None
    try:
        if isinstance(value, datetime):
            return value
        return parser.parse(value)
    except:
        return None

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
    _ = ""
    try: #以免檔案不存在
        board_sn, vendor_sn = read_board_vendor_sn(sftp, file_path.replace('test_log.csv', "all_log.txt"))
    except:
        pass
    
    if board_sn == "":
        try:
            board_sn, _ = read_board_vendor_sn(sftp, file_path.replace('test_log.csv', "log.txt"))
        except:
            pass
        if vendor_sn == "":
            vendor_sn = _
        
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
            "Log SN": vendor_sn,
            "Part Number": part_num,
            "Script": script,
            "Testing Frequency": 1,
            "First Testing Date & Time": test_time,
            "Last Testing Date & Time" : test_time,
            "Board SN": board_sn,
            "Error Message": err_msg,
        }
    else:
        data_ = {
            "SN": sn,
            "Log SN": vendor_sn,
            "Part Number": part_num,
            "Script": script,
            "Testing Frequency": 1,
            "First Testing Date & Time": test_time,
            "Last Testing Date & Time" : test_time,
            "Board SN": board_sn,     
        }

        if "1pps_latency_report" in file_path.split('/'):
            latency = read_latency(sftp, file_path.replace('test_log.csv', "log.txt"))
            data_["Latency_1"] = latency[0]
            data_["Latency_2"] = latency[1]
            data_["Latency_3"] = latency[2]
            data_["Latency_4"] = latency[3]

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
                vendor_sn = content.split("VendorSN:")[1].split("PCBA_SN")[0].strip().split('-')[0]
            except:
                vendor_sn = ""

        if "Vendor SN" in content and vendor_sn == "":#11_MIS
            try:
                vendor_sn = content.split("'")[1].split("-")[0].strip()
            except:
                vendor_sn = ""

    return sn, vendor_sn

def read_latency(sftp:paramiko.sftp_client.SFTPClient, file_path):
    with sftp.open(file_path, 'r') as file:
        content = file.read().decode('utf-8')
        contents = content.split('\n')
        file.close()
    latency = [""] * 4
    i = 0
    for content in contents:
        if "1pps delay =" in content:
            latency[i] = content.split("=")[1].strip()
            i = (i + 1) % 4
    
    return latency

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


def main():
    root = "/Credo_DTO_Auto/Report"
    folders = ['10_Pin_test_report', '08_tc_test_report', '06_pc_test_report', '05_function_test_report_TST', '05_function_test_report', '02_lineside_test_report', '03_autotuning_test_report', '11_MIS_test_report', '07_outscripts', '13_1pps_test_report', '12_WLT_test_report', '01_GF_test_report', '10_Pin_test_report_Prod', '05_function_test_report_Bending']
    folders = ['06_pc_test_report'] #暫時
    roots = [f"{root}/{folder}" for folder in folders]
    
    for r in roots:
        sftp, trans = connect_sftp()
        thread = threading.Thread(target=find_target, args=(sftp, r, trans))
        threads.append(thread)
        thread.start()
    for thread in threads:
            thread.join()

threads = []   
main()