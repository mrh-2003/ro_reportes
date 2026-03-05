import sqlite3

db = "ro_analysis.db"
tabla = "operaciones"

codigos = [
"0XXXXX20","0XXXXX39","1XXXXX58","2XXXXX92","3XXXXX69",
"4XXXXX46","4XXXXX53","4XXXXX08","4XXXXX04","4XXXXX54",
"4XXXXX34","4XXXXX95","4XXXXX97","4XXXXX32","4XXXXX12",
"4XXXXX22","7XXXXX73","7XXXXX50","7XXXXX17","201XXXXX429",
"202XXXXX749","204XXXXX071","204XXXXX847","205XXXXX093",
"205XXXXX613","205XXXXX371","206XXXXX587","206XXXXX998",
"206XXXXX141","206XXXXX128","206XXXXX624","206XXXXX822"
]

columnas = [
"NroDocSol",
"NroDocOrd",
"RUC_Ord",
"NroDocBen",
"RUC_Ben"
]

conn = sqlite3.connect(db)
cur = conn.cursor()

condiciones = []

for col in columnas:
    for codigo in codigos:
        condiciones.append(f"instr(COALESCE({col},''), '{codigo}') > 0")

where_match = " OR ".join(condiciones)

sql = f"""
DELETE FROM {tabla}
WHERE NOT ({where_match})
"""

cur.execute(sql)
conn.commit()

print("Filtrado terminado.")

conn.close()