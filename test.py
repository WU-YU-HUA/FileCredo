import paramiko

SSH_ROOT = "/volume1"
report_path = "/Credo_DTO_Auto/Report/"
extracted_path = "/Credo_DTO_Auto/Extracted_Log/"
result_path = "/Credo_DTO_Auto/Result/"

def connect_ssh(host="10.31.2.10", port=5207, username="harry_wu_dto", password="B4YT8+XL_:YA[SRe"):
    # 建立 SSHClient
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 自動加入新主機 key

    # 連線
    ssh.connect(hostname=host, port=port, username=username, password=password)

    return ssh
def connect_sftp():
    trans = paramiko.Transport(("10.31.2.10", 22))
    trans.connect(username="harry_wu_dto", password="B4YT8+XL_:YA[SRe")
    sftp = paramiko.SFTPClient.from_transport(trans)
    trans.set_keepalive(30)
    return sftp, trans

def ssh_command(ssh:paramiko.SSHClient, command:str):
    stdin, stdout, stderr = ssh.exec_command(command)
    print(stdout.read().decode())
    print(stderr.read().decode())
# 使用範例
ssh_client = connect_ssh()
sftp, trans = connect_sftp()
report = sftp.listdir(report_path)
print(report)

# stdin, stdout, stderr = ssh_client.exec_command(f'find {SSH_ROOT}{report_path}10_Pin_test_report -type f -name "*.csv"')
# output = stdout.read().decode()
# outputs = output.splitlines()
# print(len(outputs))
path = "/Credo_DTO_Auto/Extracted_Log/06_pc_test_report/400G_QDD_TO_2xQ56_Ursula/961400593780_P/MB4X215432000A/20240823_13_25_13/MB4X215432000A_20240823_13_25_13_pc_data.csv"
new_path = path.replace("Extracted_Log", "New")
dir = new_path.rsplit("/", 1)[0]
cmd = f"""
mkdir -p {dir}
mv {SSH_ROOT}{path} {SSH_ROOT}{new_path}
"""
ssh_command(ssh_client, cmd)

# 關閉連線
sftp.close()
trans.close()
ssh_client.close()