pip install -r requirements.txt
pyinstaller --noconfirm --noconsole --onefile --name "Test Log Extractor" .\Credo_KATIS.py && move ".\dist\Test Log Extractor.exe" ".\" && rmdir /s /q ".\dist" && rmdir /s /q ".\build" && del ".\Test Log Extractor.spec"

# Google Drive Tutorial
https://docs.google.com/presentation/d/1LJTLxaF-eHbOcDzfGSt_cr8vDIF0nx9kEoc1pRMOKL4/edit?usp=drive_link