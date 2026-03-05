# db_manager_ro.py
import sqlite3
import pandas as pd
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path='ro_analysis.db'):
        self.db_path = db_path
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def cargar_datos(self, df, codigo_carga, nombre_archivo):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT id_carga FROM cargas WHERE codigo_carga = ?', (codigo_carga,))
            if cursor.fetchone():
                return False, "El código de carga ya existe"
            
            cursor.execute(
                'INSERT INTO cargas (codigo_carga, nombre_archivo, num_registros) VALUES (?, ?, ?)',
                (codigo_carga, nombre_archivo, len(df))
            )
            id_carga = cursor.lastrowid
            
            df['id_carga'] = id_carga
            df.to_sql('operaciones', conn, if_exists='append', index=False)
            
            conn.commit()
            conn.close()
            return True, id_carga
        except Exception as e:
            return False, str(e)
    
    def get_cargas(self):
        conn = self.get_connection()
        df = pd.read_sql_query('SELECT * FROM cargas ORDER BY fecha_carga DESC', conn)
        conn.close()
        return df
    
    def get_todos_documentos(self):
        codigos = [
                    "0XXXXX20","0XXXXX39","1XXXXX58","2XXXXX92","3XXXXX69",
                    "4XXXXX46","4XXXXX53","4XXXXX08","4XXXXX04","4XXXXX54",
                    "4XXXXX34","4XXXXX95","4XXXXX97","4XXXXX32","4XXXXX12",
                    "4XXXXX22","7XXXXX73","7XXXXX50","7XXXXX17","201XXXXX429",
                    "202XXXXX749","204XXXXX071","204XXXXX847","205XXXXX093",
                    "205XXXXX613","205XXXXX371","206XXXXX587","206XXXXX998",
                    "206XXXXX141","206XXXXX128","206XXXXX624","206XXXXX822"
                    ]
        return codigos
    
    def get_todas_operaciones(self, filtros=None):
        conn = self.get_connection()
        
        query = 'SELECT * FROM operaciones WHERE 1=1'
        params = []
        
        if filtros:
            if 'fecha_min' in filtros:
                query += ' AND FechaOp >= ?'
                params.append(str(filtros['fecha_min']))
            if 'fecha_max' in filtros:
                query += ' AND FechaOp <= ?'
                params.append(str(filtros['fecha_max']))
            if 'monto_min' in filtros:
                query += ' AND MontoOpe >= ?'
                params.append(filtros['monto_min'])
            if 'monto_max' in filtros:
                query += ' AND MontoOpe <= ?'
                params.append(filtros['monto_max'])
            if 'moneda_utilizada' in filtros:
                placeholders = ','.join(['?' for _ in filtros['moneda_utilizada']])
                query += f' AND MonedaUtilizada IN ({placeholders})'
                params.extend(filtros['moneda_utilizada'])
            if 'tipo_fondo' in filtros:
                placeholders = ','.join(['?' for _ in filtros['tipo_fondo']])
                query += f' AND TipoFondo IN ({placeholders})'
                params.extend(filtros['tipo_fondo'])
            if 'forma_ope' in filtros:
                placeholders = ','.join(['?' for _ in filtros['forma_ope']])
                query += f' AND FormaOpe IN ({placeholders})'
                params.extend(filtros['forma_ope'])
            if 'tipo_ope' in filtros:
                placeholders = ','.join(['?' for _ in filtros['tipo_ope']])
                query += f' AND TipoOpe IN ({placeholders})'
                params.extend(filtros['tipo_ope'])
            if 'destipclasifpartyrelacionado' in filtros:
                placeholders = ','.join(['?' for _ in filtros['destipclasifpartyrelacionado']])
                query += f' AND destipclasifpartyrelacionado IN ({placeholders})'
                params.extend(filtros['destipclasifpartyrelacionado'])
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df