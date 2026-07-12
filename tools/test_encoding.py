import os

with open('UI/pages/view_home.py', 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

for line in lines:
    if "V" in line and "tejte" in line:
        print("REPR:")
        print(repr(line.strip()))
        
        # Test if it's cp1250 double encoded
        try:
            print("REPR FIXED CP1250:")
            print(repr(line.strip().encode('cp1250').decode('utf-8')))
        except Exception as e:
            print("CP1250 error:", e)
            
        try:
            print("REPR FIXED CP1252:")
            print(repr(line.strip().encode('cp1252').decode('utf-8')))
        except Exception as e:
            print("CP1252 error:", e)
