import os

archivos = [f for f in os.listdir('data') if f.endswith('.db')]
print("DBs en data/:", archivos)
