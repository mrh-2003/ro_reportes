import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class AnalizadorRO:
    def __init__(self, df_operaciones, clientes_muestra):
        self.df = df_operaciones.copy()
        self.clientes_muestra = clientes_muestra if clientes_muestra else []
        
        if 'MontoOpe' in self.df.columns:
            self.df['MontoOpe'] = pd.to_numeric(self.df['MontoOpe'], errors='coerce').fillna(0)
        if 'FechaOp' in self.df.columns:
            self.df['FechaOp'] = pd.to_datetime(self.df['FechaOp'], errors='coerce')
        if 'HoraOp' in self.df.columns:
            try:
                self.df['datetime'] = pd.to_datetime(
                    self.df['FechaOp'].astype(str) + ' ' + self.df['HoraOp'].astype(str),
                    errors='coerce'
                )
            except:
                self.df['datetime'] = self.df['FechaOp']
                
        # Normalizar documentos: Si NroDoc está vacío y RUC tiene valor, usar RUC
        roles = [('NroDocSol', 'RUC_Sol'), ('NroDocOrd', 'RUC_Ord'), ('NroDocBen', 'RUC_Ben')]
        for nro_col, ruc_col in roles:
            if nro_col in self.df.columns and ruc_col in self.df.columns:
                mask = self.df[nro_col].isna() | (self.df[nro_col].astype(str).str.strip() == '') | (self.df[nro_col].astype(str).str.lower() == 'nan')
                self.df.loc[mask, nro_col] = self.df.loc[mask, ruc_col]
                
        # Guardar copias raw para comprobaciones condicionales que evaluan estrictamente la muestra o RUC puros
        for rol in ['Sol', 'Ord', 'Ben']:
            if f'NroDoc{rol}' in self.df.columns:
                self.df[f'_NroDoc{rol}_raw'] = self.df[f'NroDoc{rol}']
                
        def format_doc_name(row, rol):
            doc = str(row.get(f'NroDoc{rol}', '')).strip() if pd.notna(row.get(f'NroDoc{rol}')) else ''
            doc = '' if doc.lower() == 'nan' else doc
            
            nomb = str(row.get(f'Nombres{rol}', '')).strip() if pd.notna(row.get(f'Nombres{rol}')) else ''
            pat = str(row.get(f'ApPaterno{rol}', '')).strip() if pd.notna(row.get(f'ApPaterno{rol}')) else ''
            mat = str(row.get(f'ApMaterno{rol}', '')).strip() if pd.notna(row.get(f'ApMaterno{rol}')) else ''
            
            nomb = '' if nomb.lower() == 'nan' else nomb
            pat = '' if pat.lower() == 'nan' else pat
            mat = '' if mat.lower() == 'nan' else mat
            
            names = [x for x in [nomb, pat, mat] if x]
            full = ' '.join(names)
            
            if doc and full:
                return f"{doc} - {full}"
            elif doc:
                return doc
            elif full:
                return full
            else:
                return np.nan

        # Sobrescribir las columnas base para extender el "Match de docuemntos" de forma universal por todo el sistema
        for rol in ['Sol', 'Ord', 'Ben']:
            if f'NroDoc{rol}' in self.df.columns:
                self.df[f'NroDoc{rol}'] = self.df.apply(lambda r: format_doc_name(r, rol), axis=1)
    
    def es_persona(self, tipo_per):
        if pd.isna(tipo_per) or tipo_per is None:
            return False
        return 'natural' in str(tipo_per).lower()
    
    def es_empresa(self, tipo_per):
        if pd.isna(tipo_per) or tipo_per is None:
            return False
        return 'jurídica' in str(tipo_per).lower()
        
    def filtrar_tipo_beneficiario(self, df, tipo):
        if tipo == 'todos':
            return df
            
        if 'RUC_Ben' not in df.columns:
            if tipo == 'empresa':
                return df.iloc[0:0]
            return df
            
        es_empresa_mask = df['RUC_Ben'].notna() & df['RUC_Ben'].astype(str).str.strip().str.startswith('2')
        
        if tipo == 'empresa':
            return df[es_empresa_mask]
        elif tipo == 'persona':
            return df[~es_empresa_mask]
        return df

    
    def filtrar_muestra_ejecutantes(self):
        return self.df[self.df['_NroDocSol_raw'].isin(self.clientes_muestra)]
    
    def filtrar_muestra_ordenantes(self):
        return self.df[
            (self.df['_NroDocOrd_raw'].isin(self.clientes_muestra)) |
            (self.df['RUC_Ord'].isin(self.clientes_muestra))
        ]
    
    def filtrar_muestra_beneficiarios(self):
        return self.df[
            (self.df['_NroDocBen_raw'].isin(self.clientes_muestra)) |
            (self.df['RUC_Ben'].isin(self.clientes_muestra))
        ]
    
    def _generar_ranking(self, df, columna, rename_id='cantidad_operaciones', rename_monto='monto_total'):
        if df.empty or columna not in df.columns:
            return pd.DataFrame()
        ranking = df.groupby(columna).agg({
            'id_operacion': 'count', 'MontoOpe': 'sum'
        }).rename(columns={'id_operacion': rename_id, 'MontoOpe': rename_monto})
        total_cant = ranking[rename_id].sum()
        total_monto = ranking[rename_monto].sum()
        ranking['porcentaje_cantidad'] = (ranking[rename_id] / total_cant * 100).round(2) if total_cant > 0 else 0.0
        ranking['porcentaje_monto'] = (ranking[rename_monto] / total_monto * 100).round(2) if total_monto > 0 else 0.0
        return ranking.sort_values(rename_id, ascending=False)

    def reporte_top10(self):
        resultados = {}
        columnas = ['CodUbigeo', 'TipDocSol', 'OcupSol', 'CIIUOcupSol', 'TipRelOrd', 'CondResidenciaOrd',
                   'TipPerOrd', 'TipDocOrd', 'OcupOrd', 'CIIUOcupOrd', 'TipDocBen', 'OcupBen',
                   'CIIUOcupBen', 'TipoFondo', 'TipoOpe', 'MonedaUtilizada', 'AlcanceOpe',
                   'IntermediarioOpe', 'FormaOpe', 'destipclasifpartyrelacionado']
        
        for col in columnas:
            df_col = self.df[self.df[col].notna()]
            if not df_col.empty:
                ranking = self._generar_ranking(df_col, col, 'cantidad_operaciones', 'monto_total')
                resultados[col] = ranking.head(10)
        return resultados
    
    def reporte_1_actividad_ejecutantes(self):
        return self._generar_ranking(self.filtrar_muestra_ejecutantes(), 'OcupSol')
    
    def reporte_2_vinculado_ejecutantes(self, tipo='todos'):
        df = self.filtrar_muestra_ejecutantes()
        return self._generar_ranking(df, 'destipclasifpartyrelacionado')
    
    def reporte_3_actividad_ben_ejecutantes(self, tipo='todos'):
        df = self.filtrar_muestra_ejecutantes()
        if df.empty or 'OcupBen' not in df.columns:
            return pd.DataFrame()
            
        ranking = self._generar_ranking(df, 'OcupBen')
        if ranking.empty:
            return ranking
            
        if 'MonedaUtilizada' in df.columns:
            df_soles = df[df['MonedaUtilizada'] == 'Sol peruano']
            df_dolares = df[df['MonedaUtilizada'] == 'Dólar estadounidense']
            
            soles_stats = df_soles.groupby('OcupBen')['MontoOpe'].agg(['mean', 'max']).rename(
                columns={'mean': 'promedio_soles', 'max': 'mayor_soles'}
            )
            dolares_stats = df_dolares.groupby('OcupBen')['MontoOpe'].agg(['mean', 'max']).rename(
                columns={'mean': 'promedio_dolares', 'max': 'mayor_dolares'}
            )
            
            ranking = ranking.join(soles_stats).join(dolares_stats)
            cols_to_fill = ['promedio_soles', 'mayor_soles', 'promedio_dolares', 'mayor_dolares']
            for c in cols_to_fill:
                if c in ranking.columns:
                    ranking[c] = ranking[c].fillna(0)
                    ranking[c] = ranking[c].round(2)
        return ranking
    
    def reporte_4_tipo_ope_ejecutantes(self, tipo='todos'):
        df = self.filtrar_muestra_ejecutantes() 
        return self._generar_ranking(df, 'TipoOpe')
    
    def reporte_5_beneficiarios_comunes(self):
        df = self.filtrar_muestra_ejecutantes()
        if df.empty:
            return pd.DataFrame()
            
        def get_full_name(r):
            nombres = str(r.get('NombresSol', '')).strip() if pd.notna(r.get('NombresSol')) else ''
            paterno = str(r.get('ApPaternoSol', '')).strip() if pd.notna(r.get('ApPaternoSol')) else ''
            materno = str(r.get('ApMaternoSol', '')).strip() if pd.notna(r.get('ApMaternoSol')) else ''
            
            nombres = '' if nombres.lower() == 'nan' else nombres
            paterno = '' if paterno.lower() == 'nan' else paterno
            materno = '' if materno.lower() == 'nan' else materno
            
            parts = [x for x in [nombres, paterno, materno] if x]
            return ' '.join(parts)
            
        def get_full_name_ben(r):
            nombres = str(r.get('NombresBen', '')).strip() if pd.notna(r.get('NombresBen')) else ''
            paterno = str(r.get('ApPaternoBen', '')).strip() if pd.notna(r.get('ApPaternoBen')) else ''
            materno = str(r.get('ApMaternoBen', '')).strip() if pd.notna(r.get('ApMaternoBen')) else ''
            
            nombres = '' if nombres.lower() == 'nan' else nombres
            paterno = '' if paterno.lower() == 'nan' else paterno
            materno = '' if materno.lower() == 'nan' else materno
            
            parts = [x for x in [nombres, paterno, materno] if x]
            return ' '.join(parts)
            
        def format_concat(doc, fullname):
            doc = str(doc).strip() if pd.notna(doc) else ''
            doc = '' if doc.lower() == 'nan' else doc
            
            if not doc and not fullname:
                return np.nan
            elif doc and fullname:
                return f"{doc} - {fullname}"
            else:
                return doc if doc else fullname

        df_temp = df.copy()
        df_temp['fullname_sol'] = df_temp.apply(get_full_name, axis=1)
        df_temp['fullname_ben'] = df_temp.apply(get_full_name_ben, axis=1)
        df_temp['ejecutante_concat'] = df_temp.apply(lambda r: format_concat(r.get('NroDocSol'), r.get('fullname_sol')), axis=1)
        
        df_temp = df_temp[df_temp['ejecutante_concat'].notna()]
        
        if df_temp.empty:
            return pd.DataFrame()

        resultado = df_temp.groupby('NroDocBen').agg({
            'fullname_ben': lambda x: x.mode()[0] if not x.mode().empty else '',
            'NroDocSol': lambda x: list(x.dropna().unique()),
            'ejecutante_concat': lambda x: list(x.unique()),
            'MontoOpe': 'sum', 
            'id_operacion': 'count',
            'OcupBen': lambda x: x.mode()[0] if not x.mode().empty else ''
        }).rename(columns={
            'fullname_ben': 'nombre_completo_beneficiario',
            'NroDocSol': 'documentos_ejecutantes',
            'ejecutante_concat': 'ejecutantes_detalles',
            'MontoOpe': 'monto_total', 
            'id_operacion': 'cantidad_operaciones'
        })
        
        resultado['num_ejecutantes'] = resultado['ejecutantes_detalles'].apply(len)
        return resultado[resultado['num_ejecutantes'] > 1].sort_values('num_ejecutantes', ascending=False)
    
    def reporte_6_cuentas_ben_comunes(self):
        df = self.filtrar_muestra_ejecutantes()
        if df.empty or 'CtaBen' not in df.columns:
            return pd.DataFrame()
            
        def get_full_name(r):
            nombres = str(r.get('NombresSol', '')).strip() if pd.notna(r.get('NombresSol')) else ''
            paterno = str(r.get('ApPaternoSol', '')).strip() if pd.notna(r.get('ApPaternoSol')) else ''
            materno = str(r.get('ApMaternoSol', '')).strip() if pd.notna(r.get('ApMaternoSol')) else ''
            
            nombres = '' if nombres.lower() == 'nan' else nombres
            paterno = '' if paterno.lower() == 'nan' else paterno
            materno = '' if materno.lower() == 'nan' else materno
            
            parts = [x for x in [nombres, paterno, materno] if x]
            return ' '.join(parts)
            
        def get_full_name_ben(r):
            nombres = str(r.get('NombresBen', '')).strip() if pd.notna(r.get('NombresBen')) else ''
            paterno = str(r.get('ApPaternoBen', '')).strip() if pd.notna(r.get('ApPaternoBen')) else ''
            materno = str(r.get('ApMaternoBen', '')).strip() if pd.notna(r.get('ApMaternoBen')) else ''
            
            nombres = '' if nombres.lower() == 'nan' else nombres
            paterno = '' if paterno.lower() == 'nan' else paterno
            materno = '' if materno.lower() == 'nan' else materno
            
            parts = [x for x in [nombres, paterno, materno] if x]
            return ' '.join(parts)
            
        def format_concat(doc, fullname):
            doc = str(doc).strip() if pd.notna(doc) else ''
            doc = '' if doc.lower() == 'nan' else doc
            
            if not doc and not fullname:
                return np.nan
            elif doc and fullname:
                return f"{doc} - {fullname}"
            else:
                return doc if doc else fullname

        df_temp = df[df['CtaBen'].notna()].copy()
        df_temp['fullname_sol'] = df_temp.apply(get_full_name, axis=1)
        df_temp['fullname_ben'] = df_temp.apply(get_full_name_ben, axis=1)
        df_temp['ejecutante_concat'] = df_temp.apply(lambda r: format_concat(r.get('NroDocSol'), r.get('fullname_sol')), axis=1)
        
        df_temp = df_temp[df_temp['ejecutante_concat'].notna()]
        
        if df_temp.empty:
            return pd.DataFrame()

        resultado = df_temp.groupby('CtaBen').agg({
            'fullname_ben': lambda x: x.mode()[0] if not x.mode().empty else '',
            'NroDocSol': lambda x: list(x.dropna().unique()),
            'ejecutante_concat': lambda x: list(x.unique()),
            'MontoOpe': 'sum', 
            'id_operacion': 'count'
        }).rename(columns={
            'fullname_ben': 'nombre_completo_beneficiario',
            'NroDocSol': 'documentos_ejecutantes',
            'ejecutante_concat': 'ejecutantes_detalles',
            'MontoOpe': 'monto_total', 
            'id_operacion': 'cantidad_operaciones'
        })
        
        resultado['num_ejecutantes'] = resultado['ejecutantes_detalles'].apply(len)
        return resultado[resultado['num_ejecutantes'] > 1].sort_values('num_ejecutantes', ascending=False)
    
    def reporte_7_actividad_ben_efectivo(self, tipo='todos'):
        df = self.filtrar_muestra_ejecutantes()
        df = df[df['TipoFondo'] == 'Operación realizada con fondos en efectivo']
        return self._generar_ranking(df, 'OcupBen')
    
    def reporte_8_ordenantes_comunes(self):
        df = self.filtrar_muestra_ejecutantes()
        if df.empty:
            return pd.DataFrame()
            
        def get_full_name(r):
            nombres = str(r.get('NombresSol', '')).strip() if pd.notna(r.get('NombresSol')) else ''
            paterno = str(r.get('ApPaternoSol', '')).strip() if pd.notna(r.get('ApPaternoSol')) else ''
            materno = str(r.get('ApMaternoSol', '')).strip() if pd.notna(r.get('ApMaternoSol')) else ''
            
            nombres = '' if nombres.lower() == 'nan' else nombres
            paterno = '' if paterno.lower() == 'nan' else paterno
            materno = '' if materno.lower() == 'nan' else materno
            
            parts = [x for x in [nombres, paterno, materno] if x]
            return ' '.join(parts)
            
        def get_full_name_ord(r):
            nombres = str(r.get('NombresOrd', '')).strip() if pd.notna(r.get('NombresOrd')) else ''
            paterno = str(r.get('ApPaternoOrd', '')).strip() if pd.notna(r.get('ApPaternoOrd')) else ''
            materno = str(r.get('ApMaternoOrd', '')).strip() if pd.notna(r.get('ApMaternoOrd')) else ''
            
            nombres = '' if nombres.lower() == 'nan' else nombres
            paterno = '' if paterno.lower() == 'nan' else paterno
            materno = '' if materno.lower() == 'nan' else materno
            
            parts = [x for x in [nombres, paterno, materno] if x]
            return ' '.join(parts)
            
        def format_concat(doc, fullname):
            doc = str(doc).strip() if pd.notna(doc) else ''
            doc = '' if doc.lower() == 'nan' else doc
            
            if not doc and not fullname:
                return np.nan
            elif doc and fullname:
                return f"{doc} - {fullname}"
            else:
                return doc if doc else fullname

        df_temp = df.copy()
        df_temp['fullname_sol'] = df_temp.apply(get_full_name, axis=1)
        df_temp['fullname_ord'] = df_temp.apply(get_full_name_ord, axis=1)
        df_temp['ejecutante_concat'] = df_temp.apply(lambda r: format_concat(r.get('NroDocSol'), r.get('fullname_sol')), axis=1)
        
        # Filtrar registros donde ejecutante está en blanco
        df_temp = df_temp[df_temp['ejecutante_concat'].notna()]
        
        if df_temp.empty:
            return pd.DataFrame()

        resultado = df_temp.groupby('NroDocOrd').agg({
            'fullname_ord': lambda x: x.mode()[0] if not x.mode().empty else '',
            'NroDocSol': lambda x: list(x.dropna().unique()),
            'ejecutante_concat': lambda x: list(x.unique()),
            'MontoOpe': 'sum', 
            'id_operacion': 'count',
            'OcupOrd': lambda x: x.mode()[0] if not x.mode().empty else ''
        }).rename(columns={
            'fullname_ord': 'nombre_completo_ordenante',
            'NroDocSol': 'documentos_ejecutantes',
            'ejecutante_concat': 'ejecutantes_detalles',
            'MontoOpe': 'monto_total', 
            'id_operacion': 'cantidad_operaciones'
        })
        
        resultado['num_ejecutantes'] = resultado['ejecutantes_detalles'].apply(len)
        return resultado[resultado['num_ejecutantes'] > 1].sort_values('num_ejecutantes', ascending=False)
    
    def reporte_9_actividad_ordenantes(self):
        return self._generar_ranking(self.filtrar_muestra_ordenantes(), 'OcupOrd')
    
    def reporte_10_vinculado_ordenantes(self, tipo='todos'):
        df = self.filtrar_muestra_ordenantes()
        if tipo == 'persona':
            df = df[df['TipPerOrd'].apply(self.es_persona).astype(bool)]
        elif tipo == 'empresa':
            df = df[df['TipPerOrd'].apply(self.es_empresa).astype(bool)]
        return self._generar_ranking(df, 'destipclasifpartyrelacionado')
    
    def reporte_11_actividad_ben_ordenantes(self, tipo='todos'):
        df = self.filtrar_muestra_ordenantes()
        if tipo == 'persona':
            df = df[df['TipPerOrd'].apply(self.es_persona).astype(bool)]
        elif tipo == 'empresa':
            df = df[df['TipPerOrd'].apply(self.es_empresa).astype(bool)]
            
        if df.empty or 'OcupBen' not in df.columns:
            return pd.DataFrame()
            
        ranking = self._generar_ranking(df, 'OcupBen')
        if ranking.empty:
            return ranking
            
        if 'MonedaUtilizada' in df.columns:
            df_soles = df[df['MonedaUtilizada'] == 'Sol peruano']
            df_dolares = df[df['MonedaUtilizada'] == 'Dólar estadounidense']
            
            soles_stats = df_soles.groupby('OcupBen')['MontoOpe'].agg(['mean', 'max']).rename(
                columns={'mean': 'promedio_soles', 'max': 'mayor_soles'}
            )
            dolares_stats = df_dolares.groupby('OcupBen')['MontoOpe'].agg(['mean', 'max']).rename(
                columns={'mean': 'promedio_dolares', 'max': 'mayor_dolares'}
            )
            
            ranking = ranking.join(soles_stats).join(dolares_stats)
            cols_to_fill = ['promedio_soles', 'mayor_soles', 'promedio_dolares', 'mayor_dolares']
            for c in cols_to_fill:
                if c in ranking.columns:
                    ranking[c] = ranking[c].fillna(0)
                    ranking[c] = ranking[c].round(2)
        return ranking
    
    def reporte_12_tipo_ope_ordenantes(self, tipo='todos'):
        df = self.filtrar_muestra_ordenantes()
        if tipo == 'persona':
            df = df[df['TipPerOrd'].apply(self.es_persona).astype(bool)]
        elif tipo == 'empresa':
            df = df[df['TipPerOrd'].apply(self.es_empresa).astype(bool)]
            
        if df.empty or 'TipoOpe' not in df.columns:
            return pd.DataFrame()
            
        ranking = self._generar_ranking(df, 'TipoOpe')
        if ranking.empty:
            return ranking
            
        if 'MonedaUtilizada' in df.columns:
            df_soles = df[df['MonedaUtilizada'] == 'Sol peruano']
            df_dolares = df[df['MonedaUtilizada'] == 'Dólar estadounidense']
            
            soles_stats = df_soles.groupby('TipoOpe')['MontoOpe'].agg(['mean', 'max']).rename(
                columns={'mean': 'promedio_soles', 'max': 'mayor_soles'}
            )
            dolares_stats = df_dolares.groupby('TipoOpe')['MontoOpe'].agg(['mean', 'max']).rename(
                columns={'mean': 'promedio_dolares', 'max': 'mayor_dolares'}
            )
            
            ranking = ranking.join(soles_stats).join(dolares_stats)
            cols_to_fill = ['promedio_soles', 'mayor_soles', 'promedio_dolares', 'mayor_dolares']
            for c in cols_to_fill:
                if c in ranking.columns:
                    ranking[c] = ranking[c].fillna(0)
                    ranking[c] = ranking[c].round(2)
        return ranking
    
    def reporte_13_beneficiarios_comunes_ordenantes(self):
        df = self.filtrar_muestra_ordenantes()
        if df.empty:
            return pd.DataFrame()
        resultado = df.groupby('NroDocBen').agg({
            'NroDocOrd': lambda x: list(x.unique()),
            'MontoOpe': 'sum', 'id_operacion': 'count',
            'NombresBen': lambda x: x.mode()[0] if not x.mode().empty else '',
            'OcupBen': lambda x: x.mode()[0] if not x.mode().empty else ''
        }).rename(columns={'NroDocOrd': 'ordenantes', 'MontoOpe': 'monto_total', 'id_operacion': 'cantidad_operaciones'})
        resultado['num_ordenantes'] = resultado['ordenantes'].apply(len)
        return resultado[resultado['num_ordenantes'] > 1].sort_values('num_ordenantes', ascending=False)
    
    def reporte_14_cuentas_ben_comunes_ordenantes(self):
        df = self.filtrar_muestra_ordenantes()
        if df.empty or 'CtaBen' not in df.columns:
            return pd.DataFrame()
            
        def get_full_name_ord(r):
            nombres = str(r.get('NombresOrd', '')).strip() if pd.notna(r.get('NombresOrd')) else ''
            paterno = str(r.get('ApPaternoOrd', '')).strip() if pd.notna(r.get('ApPaternoOrd')) else ''
            materno = str(r.get('ApMaternoOrd', '')).strip() if pd.notna(r.get('ApMaternoOrd')) else ''
            
            nombres = '' if nombres.lower() == 'nan' else nombres
            paterno = '' if paterno.lower() == 'nan' else paterno
            materno = '' if materno.lower() == 'nan' else materno
            
            parts = [x for x in [nombres, paterno, materno] if x]
            return ' '.join(parts)
            
        def get_full_name_ben(r):
            nombres = str(r.get('NombresBen', '')).strip() if pd.notna(r.get('NombresBen')) else ''
            paterno = str(r.get('ApPaternoBen', '')).strip() if pd.notna(r.get('ApPaternoBen')) else ''
            materno = str(r.get('ApMaternoBen', '')).strip() if pd.notna(r.get('ApMaternoBen')) else ''
            
            nombres = '' if nombres.lower() == 'nan' else nombres
            paterno = '' if paterno.lower() == 'nan' else paterno
            materno = '' if materno.lower() == 'nan' else materno
            
            parts = [x for x in [nombres, paterno, materno] if x]
            return ' '.join(parts)
            
        def format_concat(doc, fullname):
            doc = str(doc).strip() if pd.notna(doc) else ''
            doc = '' if doc.lower() == 'nan' else doc
            
            if not doc and not fullname:
                return np.nan
            elif doc and fullname:
                return f"{doc} - {fullname}"
            else:
                return doc if doc else fullname

        df_temp = df[df['CtaBen'].notna()].copy()
        df_temp['fullname_ord'] = df_temp.apply(get_full_name_ord, axis=1)
        df_temp['fullname_ben'] = df_temp.apply(get_full_name_ben, axis=1)
        df_temp['ordenante_concat'] = df_temp.apply(lambda r: format_concat(r.get('NroDocOrd'), r.get('fullname_ord')), axis=1)
        
        # Filtrar registros donde ordenante está en blanco
        df_temp = df_temp[df_temp['ordenante_concat'].notna()]
        
        if df_temp.empty:
            return pd.DataFrame()

        resultado = df_temp.groupby('CtaBen').agg({
            'fullname_ben': lambda x: x.mode()[0] if not x.mode().empty else '',
            'NroDocOrd': lambda x: list(x.dropna().unique()),
            'ordenante_concat': lambda x: list(x.unique()),
            'MontoOpe': 'sum', 
            'id_operacion': 'count'
        }).rename(columns={
            'fullname_ben': 'nombre_completo_beneficiario',
            'NroDocOrd': 'documentos_ordenantes',
            'ordenante_concat': 'ordenantes_detalles',
            'MontoOpe': 'monto_total', 
            'id_operacion': 'cantidad_operaciones'
        })
        
        resultado['num_ordenantes'] = resultado['ordenantes_detalles'].apply(len)
        return resultado[resultado['num_ordenantes'] > 1].sort_values('num_ordenantes', ascending=False)
    
    def reporte_15_actividad_ben_efectivo_ordenantes(self, tipo='todos'):
        df = self.filtrar_muestra_ordenantes()
        df = df[df['TipoFondo'] == 'Operación realizada con fondos en efectivo']
        if tipo == 'persona':
            df = df[df['TipPerOrd'].apply(self.es_persona).astype(bool)]
        elif tipo == 'empresa':
            df = df[df['TipPerOrd'].apply(self.es_empresa).astype(bool)]
            
        if df.empty or 'OcupBen' not in df.columns:
            return pd.DataFrame()
            
        ranking = self._generar_ranking(df, 'OcupBen')
        if ranking.empty:
            return ranking
            
        if 'MonedaUtilizada' in df.columns:
            df_soles = df[df['MonedaUtilizada'] == 'Sol peruano']
            df_dolares = df[df['MonedaUtilizada'] == 'Dólar estadounidense']
            
            soles_stats = df_soles.groupby('OcupBen')['MontoOpe'].agg(['mean', 'max']).rename(
                columns={'mean': 'promedio_soles', 'max': 'mayor_soles'}
            )
            dolares_stats = df_dolares.groupby('OcupBen')['MontoOpe'].agg(['mean', 'max']).rename(
                columns={'mean': 'promedio_dolares', 'max': 'mayor_dolares'}
            )
            
            ranking = ranking.join(soles_stats).join(dolares_stats)
            cols_to_fill = ['promedio_soles', 'mayor_soles', 'promedio_dolares', 'mayor_dolares']
            for c in cols_to_fill:
                if c in ranking.columns:
                    ranking[c] = ranking[c].fillna(0)
                    ranking[c] = ranking[c].round(2)
        return ranking
    
    def reporte_16_ejecutantes_comunes_ordenantes(self):
        df = self.filtrar_muestra_ordenantes()
        if df.empty:
            return pd.DataFrame()
            
        def get_full_name_sol(r):
            nombres = str(r.get('NombresSol', '')).strip() if pd.notna(r.get('NombresSol')) else ''
            paterno = str(r.get('ApPaternoSol', '')).strip() if pd.notna(r.get('ApPaternoSol')) else ''
            materno = str(r.get('ApMaternoSol', '')).strip() if pd.notna(r.get('ApMaternoSol')) else ''
            
            nombres = '' if nombres.lower() == 'nan' else nombres
            paterno = '' if paterno.lower() == 'nan' else paterno
            materno = '' if materno.lower() == 'nan' else materno
            
            parts = [x for x in [nombres, paterno, materno] if x]
            return ' '.join(parts)
            
        def get_full_name_ord(r):
            nombres = str(r.get('NombresOrd', '')).strip() if pd.notna(r.get('NombresOrd')) else ''
            paterno = str(r.get('ApPaternoOrd', '')).strip() if pd.notna(r.get('ApPaternoOrd')) else ''
            materno = str(r.get('ApMaternoOrd', '')).strip() if pd.notna(r.get('ApMaternoOrd')) else ''
            
            nombres = '' if nombres.lower() == 'nan' else nombres
            paterno = '' if paterno.lower() == 'nan' else paterno
            materno = '' if materno.lower() == 'nan' else materno
            
            parts = [x for x in [nombres, paterno, materno] if x]
            return ' '.join(parts)
            
        def format_concat(doc, fullname):
            doc = str(doc).strip() if pd.notna(doc) else ''
            doc = '' if doc.lower() == 'nan' else doc
            
            if not doc and not fullname:
                return np.nan
            elif doc and fullname:
                return f"{doc} - {fullname}"
            else:
                return doc if doc else fullname

        df_temp = df.copy()
        df_temp['fullname_sol'] = df_temp.apply(get_full_name_sol, axis=1)
        df_temp['fullname_ord'] = df_temp.apply(get_full_name_ord, axis=1)
        df_temp['ordenante_concat'] = df_temp.apply(lambda r: format_concat(r.get('NroDocOrd'), r.get('fullname_ord')), axis=1)
        
        df_temp = df_temp[df_temp['ordenante_concat'].notna()]
        
        if df_temp.empty:
            return pd.DataFrame()

        resultado = df_temp.groupby('NroDocSol').agg({
            'fullname_sol': lambda x: x.mode()[0] if not x.mode().empty else '',
            'NroDocOrd': lambda x: list(x.dropna().unique()),
            'ordenante_concat': lambda x: list(x.unique()),
            'MontoOpe': 'sum', 
            'id_operacion': 'count',
            'OcupSol': lambda x: x.mode()[0] if not x.mode().empty else ''
        }).rename(columns={
            'fullname_sol': 'nombre_completo_ejecutante',
            'NroDocOrd': 'documentos_ordenantes',
            'ordenante_concat': 'ordenantes_detalles',
            'MontoOpe': 'monto_total', 
            'id_operacion': 'cantidad_operaciones'
        })
        
        resultado['num_ordenantes'] = resultado['ordenantes_detalles'].apply(len)
        return resultado[resultado['num_ordenantes'] > 1].sort_values('num_ordenantes', ascending=False)
    
    def reporte_17_actividad_beneficiarios(self):
        return self._generar_ranking(self.filtrar_muestra_beneficiarios(), 'OcupBen')
    
    def reporte_18_vinculado_beneficiarios(self, tipo='todos'):
        df = self.filtrar_muestra_beneficiarios()
        df = self.filtrar_tipo_beneficiario(df, tipo)
        return self._generar_ranking(df, 'destipclasifpartyrelacionado')
    
    def reporte_19_actividad_ord_beneficiarios(self, tipo='todos'):
        df = self.filtrar_muestra_beneficiarios()
        df = self.filtrar_tipo_beneficiario(df, tipo)
            
        if df.empty or 'OcupOrd' not in df.columns:
            return pd.DataFrame()
            
        ranking = self._generar_ranking(df, 'OcupOrd')
        if ranking.empty:
            return ranking
            
        if 'MonedaUtilizada' in df.columns:
            df_soles = df[df['MonedaUtilizada'] == 'Sol peruano']
            df_dolares = df[df['MonedaUtilizada'] == 'Dólar estadounidense']
            
            soles_stats = df_soles.groupby('OcupOrd')['MontoOpe'].agg(['mean', 'max']).rename(
                columns={'mean': 'promedio_soles', 'max': 'mayor_soles'}
            )
            dolares_stats = df_dolares.groupby('OcupOrd')['MontoOpe'].agg(['mean', 'max']).rename(
                columns={'mean': 'promedio_dolares', 'max': 'mayor_dolares'}
            )
            
            ranking = ranking.join(soles_stats).join(dolares_stats)
            cols_to_fill = ['promedio_soles', 'mayor_soles', 'promedio_dolares', 'mayor_dolares']
            for c in cols_to_fill:
                if c in ranking.columns:
                    ranking[c] = ranking[c].fillna(0)
                    ranking[c] = ranking[c].round(2)
        return ranking
    
    def reporte_20_tipo_ope_beneficiarios(self, tipo='todos'):
        df = self.filtrar_muestra_beneficiarios()
        df = self.filtrar_tipo_beneficiario(df, tipo)
        return self._generar_ranking(df, 'TipoOpe')
    
    def reporte_21_ordenantes_comunes_beneficiarios(self):
        df = self.filtrar_muestra_beneficiarios()
        if df.empty:
            return pd.DataFrame()
            
        def get_full_name_ord(r):
            nombres = str(r.get('NombresOrd', '')).strip() if pd.notna(r.get('NombresOrd')) else ''
            paterno = str(r.get('ApPaternoOrd', '')).strip() if pd.notna(r.get('ApPaternoOrd')) else ''
            materno = str(r.get('ApMaternoOrd', '')).strip() if pd.notna(r.get('ApMaternoOrd')) else ''
            
            nombres = '' if nombres.lower() == 'nan' else nombres
            paterno = '' if paterno.lower() == 'nan' else paterno
            materno = '' if materno.lower() == 'nan' else materno
            
            parts = [x for x in [nombres, paterno, materno] if x]
            return ' '.join(parts)
            
        def get_full_name_ben(r):
            nombres = str(r.get('NombresBen', '')).strip() if pd.notna(r.get('NombresBen')) else ''
            paterno = str(r.get('ApPaternoBen', '')).strip() if pd.notna(r.get('ApPaternoBen')) else ''
            materno = str(r.get('ApMaternoBen', '')).strip() if pd.notna(r.get('ApMaternoBen')) else ''
            
            nombres = '' if nombres.lower() == 'nan' else nombres
            paterno = '' if paterno.lower() == 'nan' else paterno
            materno = '' if materno.lower() == 'nan' else materno
            
            parts = [x for x in [nombres, paterno, materno] if x]
            return ' '.join(parts)
            
        def format_concat(doc, fullname):
            doc = str(doc).strip() if pd.notna(doc) else ''
            doc = '' if doc.lower() == 'nan' else doc
            
            if not doc and not fullname:
                return np.nan
            elif doc and fullname:
                return f"{doc} - {fullname}"
            else:
                return doc if doc else fullname

        df_temp = df.copy()
        df_temp['fullname_ord'] = df_temp.apply(get_full_name_ord, axis=1)
        df_temp['fullname_ben'] = df_temp.apply(get_full_name_ben, axis=1)
        df_temp['beneficiario_concat'] = df_temp.apply(lambda r: format_concat(r.get('NroDocBen'), r.get('fullname_ben')), axis=1)
        
        df_temp = df_temp[df_temp['beneficiario_concat'].notna()]
        
        if df_temp.empty:
            return pd.DataFrame()

        resultado = df_temp.groupby('NroDocOrd').agg({
            'fullname_ord': lambda x: x.mode()[0] if not x.mode().empty else '',
            'NroDocBen': lambda x: list(x.dropna().unique()),
            'beneficiario_concat': lambda x: list(x.unique()),
            'MontoOpe': 'sum', 
            'id_operacion': 'count',
            'OcupOrd': lambda x: x.mode()[0] if not x.mode().empty else ''
        }).rename(columns={
            'fullname_ord': 'nombre_completo_ordenante',
            'NroDocBen': 'documentos_beneficiarios',
            'beneficiario_concat': 'beneficiarios_detalles',
            'MontoOpe': 'monto_total', 
            'id_operacion': 'cantidad_operaciones'
        })
        
        resultado['num_beneficiarios'] = resultado['beneficiarios_detalles'].apply(len)
        return resultado[resultado['num_beneficiarios'] > 1].sort_values('num_beneficiarios', ascending=False)
    
    def reporte_22_cuentas_ord_comunes_beneficiarios(self):
        df = self.filtrar_muestra_beneficiarios()
        if df.empty or 'CtaOrd' not in df.columns:
            return pd.DataFrame()
            
        def get_full_name_ord(r):
            nombres = str(r.get('NombresOrd', '')).strip() if pd.notna(r.get('NombresOrd')) else ''
            paterno = str(r.get('ApPaternoOrd', '')).strip() if pd.notna(r.get('ApPaternoOrd')) else ''
            materno = str(r.get('ApMaternoOrd', '')).strip() if pd.notna(r.get('ApMaternoOrd')) else ''
            
            nombres = '' if nombres.lower() == 'nan' else nombres
            paterno = '' if paterno.lower() == 'nan' else paterno
            materno = '' if materno.lower() == 'nan' else materno
            
            parts = [x for x in [nombres, paterno, materno] if x]
            return ' '.join(parts)
            
        def get_full_name_ben(r):
            nombres = str(r.get('NombresBen', '')).strip() if pd.notna(r.get('NombresBen')) else ''
            paterno = str(r.get('ApPaternoBen', '')).strip() if pd.notna(r.get('ApPaternoBen')) else ''
            materno = str(r.get('ApMaternoBen', '')).strip() if pd.notna(r.get('ApMaternoBen')) else ''
            
            nombres = '' if nombres.lower() == 'nan' else nombres
            paterno = '' if paterno.lower() == 'nan' else paterno
            materno = '' if materno.lower() == 'nan' else materno
            
            parts = [x for x in [nombres, paterno, materno] if x]
            return ' '.join(parts)
            
        def format_concat(doc, fullname):
            doc = str(doc).strip() if pd.notna(doc) else ''
            doc = '' if doc.lower() == 'nan' else doc
            
            if not doc and not fullname:
                return np.nan
            elif doc and fullname:
                return f"{doc} - {fullname}"
            else:
                return doc if doc else fullname

        df_temp = df[df['CtaOrd'].notna()].copy()
        df_temp['fullname_ord'] = df_temp.apply(get_full_name_ord, axis=1)
        df_temp['fullname_ben'] = df_temp.apply(get_full_name_ben, axis=1)
        df_temp['beneficiario_concat'] = df_temp.apply(lambda r: format_concat(r.get('NroDocBen'), r.get('fullname_ben')), axis=1)
        
        # Filtrar registros donde beneficiario está en blanco
        df_temp = df_temp[df_temp['beneficiario_concat'].notna()]
        
        if df_temp.empty:
            return pd.DataFrame()

        resultado = df_temp.groupby('CtaOrd').agg({
            'fullname_ord': lambda x: x.mode()[0] if not x.mode().empty else '',
            'NroDocBen': lambda x: list(x.dropna().unique()),
            'beneficiario_concat': lambda x: list(x.unique()),
            'MontoOpe': 'sum', 
            'id_operacion': 'count'
        }).rename(columns={
            'fullname_ord': 'nombre_completo_ordenante',
            'NroDocBen': 'documentos_beneficiarios',
            'beneficiario_concat': 'beneficiarios_detalles',
            'MontoOpe': 'monto_total', 
            'id_operacion': 'cantidad_operaciones'
        })
        
        resultado['num_beneficiarios'] = resultado['beneficiarios_detalles'].apply(len)
        return resultado[resultado['num_beneficiarios'] > 1].sort_values('num_beneficiarios', ascending=False)
    
    def reporte_23_actividad_sol_efectivo_beneficiarios(self, tipo='todos'):
        df = self.filtrar_muestra_beneficiarios()
        df = df[df['TipoFondo'] == 'Operación realizada con fondos en efectivo']
        df = self.filtrar_tipo_beneficiario(df, tipo)
        return self._generar_ranking(df, 'OcupSol')
    
    def reporte_24_ejecutantes_comunes_beneficiarios(self):
        df = self.filtrar_muestra_beneficiarios()
        if df.empty:
            return pd.DataFrame()
            
        def get_full_name_sol(r):
            nombres = str(r.get('NombresSol', '')).strip() if pd.notna(r.get('NombresSol')) else ''
            paterno = str(r.get('ApPaternoSol', '')).strip() if pd.notna(r.get('ApPaternoSol')) else ''
            materno = str(r.get('ApMaternoSol', '')).strip() if pd.notna(r.get('ApMaternoSol')) else ''
            
            nombres = '' if nombres.lower() == 'nan' else nombres
            paterno = '' if paterno.lower() == 'nan' else paterno
            materno = '' if materno.lower() == 'nan' else materno
            
            parts = [x for x in [nombres, paterno, materno] if x]
            return ' '.join(parts)
            
        def get_full_name_ben(r):
            nombres = str(r.get('NombresBen', '')).strip() if pd.notna(r.get('NombresBen')) else ''
            paterno = str(r.get('ApPaternoBen', '')).strip() if pd.notna(r.get('ApPaternoBen')) else ''
            materno = str(r.get('ApMaternoBen', '')).strip() if pd.notna(r.get('ApMaternoBen')) else ''
            
            nombres = '' if nombres.lower() == 'nan' else nombres
            paterno = '' if paterno.lower() == 'nan' else paterno
            materno = '' if materno.lower() == 'nan' else materno
            
            parts = [x for x in [nombres, paterno, materno] if x]
            return ' '.join(parts)
            
        def format_concat(doc, fullname):
            doc = str(doc).strip() if pd.notna(doc) else ''
            doc = '' if doc.lower() == 'nan' else doc
            
            if not doc and not fullname:
                return np.nan
            elif doc and fullname:
                return f"{doc} - {fullname}"
            else:
                return doc if doc else fullname

        df_temp = df.copy()
        df_temp['fullname_sol'] = df_temp.apply(get_full_name_sol, axis=1)
        df_temp['fullname_ben'] = df_temp.apply(get_full_name_ben, axis=1)
        df_temp['beneficiario_concat'] = df_temp.apply(lambda r: format_concat(r.get('NroDocBen'), r.get('fullname_ben')), axis=1)
        
        df_temp = df_temp[df_temp['beneficiario_concat'].notna()]
        
        if df_temp.empty:
            return pd.DataFrame()

        resultado = df_temp.groupby('NroDocSol').agg({
            'fullname_sol': lambda x: x.mode()[0] if not x.mode().empty else '',
            'NroDocBen': lambda x: list(x.dropna().unique()),
            'beneficiario_concat': lambda x: list(x.unique()),
            'MontoOpe': 'sum', 
            'id_operacion': 'count',
            'OcupSol': lambda x: x.mode()[0] if not x.mode().empty else ''
        }).rename(columns={
            'fullname_sol': 'nombre_completo_ejecutante',
            'NroDocBen': 'documentos_beneficiarios',
            'beneficiario_concat': 'beneficiarios_detalles',
            'MontoOpe': 'monto_total', 
            'id_operacion': 'cantidad_operaciones'
        })
        
        resultado['num_beneficiarios'] = resultado['beneficiarios_detalles'].apply(len)
        return resultado[resultado['num_beneficiarios'] > 1].sort_values('num_beneficiarios', ascending=False)
    
    def reporte_25_consolidado_actividades(self):
        resultados = []
        df_ej = self.filtrar_muestra_ejecutantes()
        if not df_ej.empty and 'OcupSol' in df_ej.columns:
            ej = df_ej.groupby('OcupSol').agg({'id_operacion': 'count', 'MontoOpe': 'sum'})
            ej['rol'] = 'Ejecutante'
            resultados.append(ej.rename_axis('actividad').reset_index())
        
        df_ord = self.filtrar_muestra_ordenantes()
        if not df_ord.empty and 'OcupOrd' in df_ord.columns:
            ord_df = df_ord.groupby('OcupOrd').agg({'id_operacion': 'count', 'MontoOpe': 'sum'})
            ord_df['rol'] = 'Ordenante'
            resultados.append(ord_df.rename_axis('actividad').reset_index())
        
        df_ben = self.filtrar_muestra_beneficiarios()
        if not df_ben.empty and 'OcupBen' in df_ben.columns:
            ben = df_ben.groupby('OcupBen').agg({'id_operacion': 'count', 'MontoOpe': 'sum'})
            ben['rol'] = 'Beneficiario'
            resultados.append(ben.rename_axis('actividad').reset_index())
        
        if not resultados:
            return pd.DataFrame()
        
        consolidado = pd.concat(resultados, ignore_index=True)
        final = consolidado.groupby('actividad').agg({
            'id_operacion': 'sum', 'MontoOpe': 'sum'
        }).rename(columns={'id_operacion': 'cantidad_operaciones', 'MontoOpe': 'monto_total'})
        
        total_cant = final['cantidad_operaciones'].sum()
        total_monto = final['monto_total'].sum()
        final['porcentaje_cantidad'] = (final['cantidad_operaciones'] / total_cant * 100).round(2)
        final['porcentaje_monto'] = (final['monto_total'] / total_monto * 100).round(2)
        return final.sort_values('cantidad_operaciones', ascending=False)
    
    def reporte_26_post_transf_internacional(self, dias=7):
        if 'datetime' not in self.df.columns:
            return pd.DataFrame(), pd.DataFrame(), {}
            
        df_base = self.df.dropna(subset=['datetime']).sort_values('datetime').reset_index(drop=True)
        tipo_transferencia = "Transferencias internacionales entre cuentas (recepción de fondos)"
        
        target_transfers = df_base[
            (df_base['TipoOpe'] == tipo_transferencia) & 
            (df_base['_NroDocBen_raw'].isin(self.clientes_muestra))
        ]
        
        resultado = []
        usados = set()
        grupo = 1
        
        total_recepciones = 0
        total_con_posterior = 0
        
        for idx in target_transfers.index:
            if idx in usados:
                continue
                
            fila_transf = df_base.loc[idx]
            inicio = fila_transf['datetime']
            fin = inicio + timedelta(days=dias)
            doc_titular = fila_transf['NroDocBen']
            
            bloque = df_base[(df_base['datetime'] >= inicio) & (df_base['datetime'] <= fin)]
            
            operaciones_grupo = []
            contador_recepciones = 1
            tiene_posterior = False
            
            for j, row in bloque.iterrows():
                if j in usados:
                    continue
                    
                doc_ben = row.get('NroDocBen')
                doc_ord = row.get('NroDocOrd')
                doc_sol = row.get('NroDocSol')
                
                horas = (row['datetime'] - inicio).total_seconds() / 3600.0
                es_transf = (row['TipoOpe'] == tipo_transferencia)
                
                if es_transf and doc_ben == doc_titular:
                    if horas <= 24:
                        obs = f"Recepcion ({contador_recepciones})"
                        rol_participacion = "BENEFICIARIO"
                        rol = "Transferencia_Base"
                        contador_recepciones += 1
                        total_recepciones += 1
                    else:
                        continue
                elif doc_ord == doc_titular:
                    obs = ""
                    rol_participacion = "ORDENANTE"
                    rol = "Operacion_Posterior"
                    tiene_posterior = True
                elif doc_sol == doc_titular:
                    obs = ""
                    rol_participacion = "SOLICITANTE"
                    rol = "Operacion_Posterior"
                    tiene_posterior = True
                else:
                    continue
                    
                usados.add(j)
                
                nueva = {
                    'Obs': obs,
                    'Grupo_ID': grupo,
                    'FechaOp': row.get('FechaOp', ''),
                    'HoraOp': row.get('HoraOp', ''),
                    'Horas_Desde_Transf': round(horas, 2),
                    'TipoOpe': row.get('TipoOpe', ''),
                    'MontoOpe': row.get('MontoOpe', 0),
                    'Rol': rol,
                    'Rol_Participacion': rol_participacion,
                    'Documento_Titular': doc_titular
                }
                operaciones_grupo.append(nueva)
                
            if len(operaciones_grupo) > 0:
                resultado.extend(operaciones_grupo)
                grupo += 1
                if tiene_posterior:
                    total_con_posterior += 1
                    
        df_resultado = pd.DataFrame(resultado)
        ranking = pd.DataFrame()
        
        if not df_resultado.empty:
            df_posteriores = df_resultado[df_resultado['Rol'] == 'Operacion_Posterior']
            if not df_posteriores.empty:
                ranking = df_posteriores['TipoOpe'].value_counts().to_frame('cantidad_operaciones')
                ranking.index.name = 'Tipo Operación Posterior'
                ranking['porcentaje'] = (ranking['cantidad_operaciones'] / ranking['cantidad_operaciones'].sum() * 100).round(2)
            
            df_resultado = df_resultado.sort_values(['Grupo_ID', 'Horas_Desde_Transf'])
            
        stats = {
            'total_recepciones': total_recepciones, 
            'total_con_posterior': total_con_posterior, 
            'dias_analisis': dias
        }
        
        return ranking, df_resultado, stats
    
    def reporte_27_porcentaje_efectivo(self):
        resultados = {}
        
        def procesar_rol(df, tipo_funcion, nombre_rol):
            df_filtrado = df[df['TipPerOrd'].apply(tipo_funcion).astype(bool)] if tipo_funcion else df
            if not df_filtrado.empty:
                total_ops = len(df_filtrado)
                monto_total = df_filtrado['MontoOpe'].sum()
                
                df_efectivo = df_filtrado[df_filtrado['TipoFondo'] == 'Operación realizada con fondos en efectivo']
                efectivo_ops = len(df_efectivo)
                monto_efectivo = df_efectivo['MontoOpe'].sum()
                
                resultados[nombre_rol] = {
                    'total_ops': total_ops,
                    'efectivo_ops': efectivo_ops,
                    'porc_ops': round(efectivo_ops/total_ops*100, 2) if total_ops > 0 else 0,
                    'monto_total': monto_total,
                    'monto_efectivo': monto_efectivo,
                    'porc_monto': round(monto_efectivo/monto_total*100, 2) if monto_total > 0 else 0
                }
                
        df_ej = self.filtrar_muestra_ejecutantes()
        procesar_rol(df_ej, self.es_persona, 'ejecutante_persona')
        
        df_ord = self.filtrar_muestra_ordenantes()
        procesar_rol(df_ord, self.es_empresa, 'ordenante_empresa')
        procesar_rol(df_ord, self.es_persona, 'ordenante_persona')
        
        df_ben = self.filtrar_muestra_beneficiarios()
        procesar_rol(df_ben, self.es_empresa, 'beneficiario_empresa')
        procesar_rol(df_ben, self.es_persona, 'beneficiario_persona')
        
        return resultados
    
    def reporte_28_plaza_efectivo(self):
        df = self.df[self.df['TipoFondo'] == 'Operación realizada con fondos en efectivo']
        return self._generar_ranking(df, 'CodUbigeo')
    
    def reporte_29_actividad_sol_mineria(self):
        df = self.filtrar_muestra_ejecutantes()
        df = df[df['OrigenFondos'].notna() & df['OrigenFondos'].str.contains('oro|auri|mine|mina', case=False)]
        return self._generar_ranking(df, 'OcupSol')
    
    def reporte_30_actividad_ord_mineria(self):
        df = self.filtrar_muestra_ordenantes()
        df = df[df['OrigenFondos'].notna() & df['OrigenFondos'].str.contains('oro|auri|mine|mina', case=False)]
        return self._generar_ranking(df, 'OcupOrd')
    
    def reporte_31_actividad_ben_mineria(self):
        df = self.filtrar_muestra_beneficiarios()
        df = df[df['OrigenFondos'].notna() & df['OrigenFondos'].str.contains('oro|auri|mine|mina', case=False)]
        return self._generar_ranking(df, 'OcupBen')
    
    def reporte_32_consolidado_mineria(self):
        df_min = self.df[self.df['OrigenFondos'].notna() & self.df['OrigenFondos'].str.contains('oro|auri|mine|mina', case=False)]
        if df_min.empty:
            return pd.DataFrame()
        
        resultados = []
        if 'OcupSol' in df_min.columns:
            sol = df_min.groupby('OcupSol').agg({'id_operacion': 'count', 'MontoOpe': 'sum'})
            sol['rol'] = 'Ejecutante'
            resultados.append(sol.rename_axis('actividad').reset_index())
        
        if 'OcupOrd' in df_min.columns:
            ord_df = df_min.groupby('OcupOrd').agg({'id_operacion': 'count', 'MontoOpe': 'sum'})
            ord_df['rol'] = 'Ordenante'
            resultados.append(ord_df.rename_axis('actividad').reset_index())
        
        if 'OcupBen' in df_min.columns:
            ben = df_min.groupby('OcupBen').agg({'id_operacion': 'count', 'MontoOpe': 'sum'})
            ben['rol'] = 'Beneficiario'
            resultados.append(ben.rename_axis('actividad').reset_index())
        
        if not resultados:
            return pd.DataFrame()
        
        consolidado = pd.concat(resultados, ignore_index=True)
        final = consolidado.groupby('actividad').agg({
            'id_operacion': 'sum', 'MontoOpe': 'sum'
        }).rename(columns={'id_operacion': 'cantidad_operaciones', 'MontoOpe': 'monto_total'})
        
        total_cant = final['cantidad_operaciones'].sum()
        total_monto = final['monto_total'].sum()
        final['porcentaje_cantidad'] = (final['cantidad_operaciones'] / total_cant * 100).round(2)
        final['porcentaje_monto'] = (final['monto_total'] / total_monto * 100).round(2)
        return final.sort_values('cantidad_operaciones', ascending=False)
    
    def reporte_33_misma_direccion(self):
        resultados = []
        df_sol_ord = self.df[(self.df['DireccionSol'].notna()) & (self.df['DireccionOrd'].notna()) & (self.df['DireccionSol'] == self.df['DireccionOrd'])]
        for dir in df_sol_ord['DireccionSol'].unique()[:50]:
            df_g = df_sol_ord[df_sol_ord['DireccionSol'] == dir]
            resultados.append({
                'direccion': dir, 'tipo': 'Sol-Ord', 'operaciones': len(df_g), 'monto': df_g['MontoOpe'].sum(), 
                'cant_ejecutantes': df_g['NroDocSol'].nunique(),
                'ejecutantes': ', '.join([str(x) for x in df_g['NroDocSol'].dropna().unique()]), 
                'cant_ordenantes': df_g['NroDocOrd'].nunique(),
                'ordenantes': ', '.join([str(x) for x in df_g['NroDocOrd'].dropna().unique()]), 
                'cant_beneficiarios': 0, 'beneficiarios': '-'
            })
            
        df_sol_ben = self.df[(self.df['DireccionSol'].notna()) & (self.df['DireccionBen'].notna()) & (self.df['DireccionSol'] == self.df['DireccionBen'])]
        for dir in df_sol_ben['DireccionSol'].unique()[:50]:
            df_g = df_sol_ben[df_sol_ben['DireccionSol'] == dir]
            resultados.append({
                'direccion': dir, 'tipo': 'Sol-Ben', 'operaciones': len(df_g), 'monto': df_g['MontoOpe'].sum(), 
                'cant_ejecutantes': df_g['NroDocSol'].nunique(),
                'ejecutantes': ', '.join([str(x) for x in df_g['NroDocSol'].dropna().unique()]), 
                'cant_ordenantes': 0, 'ordenantes': '-', 
                'cant_beneficiarios': df_g['NroDocBen'].nunique(),
                'beneficiarios': ', '.join([str(x) for x in df_g['NroDocBen'].dropna().unique()])
            })
            
        df_ord_ben = self.df[(self.df['DireccionOrd'].notna()) & (self.df['DireccionBen'].notna()) & (self.df['DireccionOrd'] == self.df['DireccionBen'])]
        for dir in df_ord_ben['DireccionOrd'].unique()[:50]:
            df_g = df_ord_ben[df_ord_ben['DireccionOrd'] == dir]
            resultados.append({
                'direccion': dir, 'tipo': 'Ord-Ben', 'operaciones': len(df_g), 'monto': df_g['MontoOpe'].sum(), 
                'cant_ejecutantes': 0, 'ejecutantes': '-', 
                'cant_ordenantes': df_g['NroDocOrd'].nunique(),
                'ordenantes': ', '.join([str(x) for x in df_g['NroDocOrd'].dropna().unique()]), 
                'cant_beneficiarios': df_g['NroDocBen'].nunique(),
                'beneficiarios': ', '.join([str(x) for x in df_g['NroDocBen'].dropna().unique()])
            })
            
        return pd.DataFrame(resultados)
    
    def reporte_34_mismo_telefono(self):
        resultados = []
        df_sol_ord = self.df[(self.df['TelefonoSol'].notna()) & (self.df['TelefonoOrd'].notna()) & (self.df['TelefonoSol'] == self.df['TelefonoOrd'])]
        for tel in df_sol_ord['TelefonoSol'].unique()[:50]:
            df_g = df_sol_ord[df_sol_ord['TelefonoSol'] == tel]
            resultados.append({
                'telefono': tel, 'tipo': 'Sol-Ord', 'operaciones': len(df_g), 'monto': df_g['MontoOpe'].sum(), 
                'cant_ejecutantes': df_g['NroDocSol'].nunique(),
                'ejecutantes': ', '.join([str(x) for x in df_g['NroDocSol'].dropna().unique()]), 
                'cant_ordenantes': df_g['NroDocOrd'].nunique(),
                'ordenantes': ', '.join([str(x) for x in df_g['NroDocOrd'].dropna().unique()]), 
                'cant_beneficiarios': 0, 'beneficiarios': '-'
            })
            
        df_sol_ben = self.df[(self.df['TelefonoSol'].notna()) & (self.df['TelefonoBen'].notna()) & (self.df['TelefonoSol'] == self.df['TelefonoBen'])]
        for tel in df_sol_ben['TelefonoSol'].unique()[:50]:
            df_g = df_sol_ben[df_sol_ben['TelefonoSol'] == tel]
            resultados.append({
                'telefono': tel, 'tipo': 'Sol-Ben', 'operaciones': len(df_g), 'monto': df_g['MontoOpe'].sum(), 
                'cant_ejecutantes': df_g['NroDocSol'].nunique(),
                'ejecutantes': ', '.join([str(x) for x in df_g['NroDocSol'].dropna().unique()]), 
                'cant_ordenantes': 0, 'ordenantes': '-', 
                'cant_beneficiarios': df_g['NroDocBen'].nunique(),
                'beneficiarios': ', '.join([str(x) for x in df_g['NroDocBen'].dropna().unique()])
            })
            
        df_ord_ben = self.df[(self.df['TelefonoOrd'].notna()) & (self.df['TelefonoBen'].notna()) & (self.df['TelefonoOrd'] == self.df['TelefonoBen'])]
        for tel in df_ord_ben['TelefonoOrd'].unique()[:50]:
            df_g = df_ord_ben[df_ord_ben['TelefonoOrd'] == tel]
            resultados.append({
                'telefono': tel, 'tipo': 'Ord-Ben', 'operaciones': len(df_g), 'monto': df_g['MontoOpe'].sum(), 
                'cant_ejecutantes': 0, 'ejecutantes': '-', 
                'cant_ordenantes': df_g['NroDocOrd'].nunique(),
                'ordenantes': ', '.join([str(x) for x in df_g['NroDocOrd'].dropna().unique()]), 
                'cant_beneficiarios': df_g['NroDocBen'].nunique(),
                'beneficiarios': ', '.join([str(x) for x in df_g['NroDocBen'].dropna().unique()])
            })
            
        return pd.DataFrame(resultados)
    
    def reporte_35_nacionalidad_sol_chinos(self):
        df = self.df[self.df['CIIUOcupSol'].notna()]
        if df.empty:
            return pd.DataFrame(), pd.DataFrame()
        ranking = df.groupby('CIIUOcupSol').agg({'id_operacion': 'count', 'MontoOpe': 'sum', 'NroDocSol': 'nunique'}).rename(columns={'id_operacion': 'cantidad_operaciones', 'MontoOpe': 'monto_total', 'NroDocSol': 'personas_unicas'})
        ranking['porcentaje_cantidad'] = (ranking['cantidad_operaciones'] / ranking['cantidad_operaciones'].sum() * 100).round(2)
        ranking['porcentaje_monto'] = (ranking['monto_total'] / ranking['monto_total'].sum() * 100).round(2)
        
        chinos = df[df['CIIUOcupSol'] == 'CN']
        vinculo = self._generar_ranking(chinos, 'destipclasifpartyrelacionado', 'cantidad_operaciones', 'monto_total')
        return ranking.sort_values('cantidad_operaciones', ascending=False), vinculo
    
    def reporte_36_nacionalidad_ord_chinos(self):
        df = self.df[self.df['CIIUOcupOrd'].notna()]
        if df.empty:
            return pd.DataFrame(), pd.DataFrame()
        ranking = df.groupby('CIIUOcupOrd').agg({'id_operacion': 'count', 'MontoOpe': 'sum', 'NroDocOrd': 'nunique'}).rename(columns={'id_operacion': 'cantidad_operaciones', 'MontoOpe': 'monto_total', 'NroDocOrd': 'personas_unicas'})
        ranking['porcentaje_cantidad'] = (ranking['cantidad_operaciones'] / ranking['cantidad_operaciones'].sum() * 100).round(2)
        ranking['porcentaje_monto'] = (ranking['monto_total'] / ranking['monto_total'].sum() * 100).round(2)
        
        chinos = df[df['CIIUOcupOrd'] == 'CN']
        vinculo = self._generar_ranking(chinos, 'destipclasifpartyrelacionado', 'cantidad_operaciones', 'monto_total')
        return ranking.sort_values('cantidad_operaciones', ascending=False), vinculo
    
    def reporte_37_nacionalidad_ben_chinos(self):
        df = self.df[self.df['CIIUOcupBen'].notna()]
        if df.empty:
            return pd.DataFrame(), pd.DataFrame()
        ranking = df.groupby('CIIUOcupBen').agg({'id_operacion': 'count', 'MontoOpe': 'sum', 'NroDocBen': 'nunique'}).rename(columns={'id_operacion': 'cantidad_operaciones', 'MontoOpe': 'monto_total', 'NroDocBen': 'personas_unicas'})
        ranking['porcentaje_cantidad'] = (ranking['cantidad_operaciones'] / ranking['cantidad_operaciones'].sum() * 100).round(2)
        ranking['porcentaje_monto'] = (ranking['monto_total'] / ranking['monto_total'].sum() * 100).round(2)
        
        chinos = df[df['CIIUOcupBen'] == 'CN']
        vinculo = self._generar_ranking(chinos, 'destipclasifpartyrelacionado', 'cantidad_operaciones', 'monto_total')
        return ranking.sort_values('cantidad_operaciones', ascending=False), vinculo
    
    def reporte_38_paises_recepcion(self):
        df_ben = self.filtrar_muestra_beneficiarios()
        df_recep = df_ben[df_ben['TipoOpe'] == 'Transferencias internacionales entre cuentas (recepción de fondos)']
        if df_recep.empty or 'CodPaisOrigen' not in df_recep.columns:
            return pd.DataFrame()
        ranking = df_recep.groupby('CodPaisOrigen').agg({'id_operacion': 'count', 'MontoOpe': 'sum', 'NroDocBen': 'nunique'}).rename(columns={'id_operacion': 'cantidad_operaciones', 'MontoOpe': 'monto_total', 'NroDocBen': 'clientes_unicos'})
        ranking['porcentaje_cantidad'] = (ranking['cantidad_operaciones'] / ranking['cantidad_operaciones'].sum() * 100).round(2)
        ranking['porcentaje_monto'] = (ranking['monto_total'] / ranking['monto_total'].sum() * 100).round(2)
        return ranking.sort_values('cantidad_operaciones', ascending=False)
    
    def reporte_39_paises_envio(self):
        df_ord = self.filtrar_muestra_ordenantes()
        df_envio = df_ord[df_ord['TipoOpe'] == 'Transferencias internacionales entre cuentas (envío de fondos)']
        if df_envio.empty or 'CodPaisDestino' not in df_envio.columns:
            return pd.DataFrame()
        ranking = df_envio.groupby('CodPaisDestino').agg({'id_operacion': 'count', 'MontoOpe': 'sum', 'NroDocOrd': 'nunique'}).rename(columns={'id_operacion': 'cantidad_operaciones', 'MontoOpe': 'monto_total', 'NroDocOrd': 'clientes_unicos'})
        ranking['porcentaje_cantidad'] = (ranking['cantidad_operaciones'] / ranking['cantidad_operaciones'].sum() * 100).round(2)
        ranking['porcentaje_monto'] = (ranking['monto_total'] / ranking['monto_total'].sum() * 100).round(2)
        return ranking.sort_values('cantidad_operaciones', ascending=False)
    
    def reporte_40_operaciones_entre_muestra(self):
        if not self.clientes_muestra:
            return pd.DataFrame(), pd.DataFrame(), {}
            
        def get_fn_sol(r):
            parts = [str(r.get(c, '')).strip() for c in ['NombresSol', 'ApPaternoSol', 'ApMaternoSol'] if pd.notna(r.get(c))]
            return ' '.join([p for p in parts if p.lower() != 'nan' and p])
            
        def get_fn_ord(r):
            parts = [str(r.get(c, '')).strip() for c in ['NombresOrd', 'ApPaternoOrd', 'ApMaternoOrd'] if pd.notna(r.get(c))]
            return ' '.join([p for p in parts if p.lower() != 'nan' and p])
            
        def get_fn_ben(r):
            parts = [str(r.get(c, '')).strip() for c in ['NombresBen', 'ApPaternoBen', 'ApMaternoBen'] if pd.notna(r.get(c))]
            return ' '.join([p for p in parts if p.lower() != 'nan' and p])

        df_entre = self.df[self.df['_NroDocSol_raw'].isin(self.clientes_muestra) | self.df['_NroDocOrd_raw'].isin(self.clientes_muestra) | self.df['_NroDocBen_raw'].isin(self.clientes_muestra)]
        resultados_inter = []
        resultados_intra = []
        
        for _, row in df_entre.iterrows():
            muestra_en_op = []
            doc_nombres = []
            docs_unicos = set()
            
            doc_sol_raw = row.get('_NroDocSol_raw')
            if doc_sol_raw in self.clientes_muestra:
                doc_sol = str(row.get('NroDocSol', ''))
                muestra_en_op.append(('Ejecutante', doc_sol))
                doc_nombres.append(f"Ejecutante: {doc_sol}")
                docs_unicos.add(doc_sol)
                
            doc_ord_raw = row.get('_NroDocOrd_raw')
            if doc_ord_raw in self.clientes_muestra:
                doc_ord = str(row.get('NroDocOrd', ''))
                muestra_en_op.append(('Ordenante', doc_ord))
                doc_nombres.append(f"Ordenante: {doc_ord}")
                docs_unicos.add(doc_ord)
                
            doc_ben_raw = row.get('_NroDocBen_raw')
            if doc_ben_raw in self.clientes_muestra:
                doc_ben = str(row.get('NroDocBen', ''))
                muestra_en_op.append(('Beneficiario', doc_ben))
                doc_nombres.append(f"Beneficiario: {doc_ben}")
                docs_unicos.add(doc_ben)
                
            if len(muestra_en_op) >= 2:
                es_misma_persona = len(docs_unicos) == 1
                
                ops_dict = {
                    'operacion_id': row.get('id_operacion'),
                    'tipo_operacion': row.get('TipoOpe'),
                    'monto': row.get('MontoOpe'),
                    'fecha': row.get('FechaOp'),
                    'relacion': ' <-> '.join([f"{r[0]}:{r[1]}" for r in muestra_en_op]),
                    'detalles_participantes': ' | '.join(doc_nombres),
                    'num_clientes_muestra': len(muestra_en_op)
                }
                
                if es_misma_persona:
                    resultados_intra.append(ops_dict)
                else:
                    resultados_inter.append(ops_dict)

        df_inter = pd.DataFrame(resultados_inter)
        df_intra = pd.DataFrame(resultados_intra)
        
        stats = {
            'total_operaciones_inter': len(df_inter), 
            'monto_total_inter': df_inter['monto'].sum() if not df_inter.empty else 0,
            'total_operaciones_intra': len(df_intra),
            'monto_total_intra': df_intra['monto'].sum() if not df_intra.empty else 0
        }
        return df_inter, df_intra, stats