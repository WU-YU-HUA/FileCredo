from dotenv import load_dotenv, set_key
import threading
import paramiko
import pandas
import io
from dateutil import parser
from datetime import datetime
import posixpath
import stat

file = "/Credo_SFTP_PE/Report/10_Pin_test_report_Prod/400G_QDD_TO_2xQ56_Ursula/961400000001_P/MB4X2155130277/"
# parts = file.strip("/").split("/")
# full_paths = [posixpath.join(*parts[:i+1]) for i in range(len(parts))]
# for path in reversed(full_paths):
#     print(path)

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

file = file.replace("/Credo_SFTP_PE/Report", "/Credo_DTO_Auto/Extracted_Log")
print(file)
build_path(file)