content = "= Vendor SN           : {1: 'BX2X2153122JD-T1', 3: 'BX2X2153122JD-S1'}"

print(content.split("'")[1].split("-")[0].strip())