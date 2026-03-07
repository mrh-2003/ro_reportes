import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import io
import base64
from db_manager_ro import DatabaseManager
from analizador_ro_v2 import AnalizadorRO
from visualizador_ro_v2 import Visualizador
import plotly.graph_objects as go
import streamlit.components.v1 as components

st.set_page_config(page_title="Sistema RO v2", layout="wide", page_icon="🔍")

if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()
if 'clientes_muestra' not in st.session_state:
    st.session_state.clientes_muestra = []
if 'vista_logaritmica' not in st.session_state:
    st.session_state.vista_logaritmica = True
if 'filtros_modificados' not in st.session_state:
    st.session_state.filtros_modificados = False
if 'filtros_aplicados' not in st.session_state:
    st.session_state.filtros_aplicados = {}

def aplicar_filtros_generales(df_todas_operaciones):
    with st.sidebar:
        st.header("🔍 Filtros Generales")
        st.info("💡 Modifique los filtros y presione 'Aplicar Filtros'")
        filtros_temp = {}
        st.subheader("📅 Rangos de Fecha")
        st.caption("Columna: FechaOp")
        
        if 'FechaOp' in df_todas_operaciones.columns:
            try:
                fecha_min_bd = pd.to_datetime(df_todas_operaciones['FechaOp']).min().date()
                fecha_max_bd = pd.to_datetime(df_todas_operaciones['FechaOp']).max().date()
            except:
                fecha_min_bd = date.today()
                fecha_max_bd = date.today()
        else:
            fecha_min_bd = date.today()
            fecha_max_bd = date.today()
        
        fecha_min = st.date_input("Fecha Mínima", value=fecha_min_bd, key="fecha_min_input")
        fecha_max = st.date_input("Fecha Máxima", value=fecha_max_bd, key="fecha_max_input")
        
        if fecha_min > fecha_min_bd or fecha_max < fecha_max_bd:
            st.session_state.filtros_modificados = True
        if fecha_min > fecha_min_bd:
            filtros_temp['fecha_min'] = fecha_min
        if fecha_max < fecha_max_bd:
            filtros_temp['fecha_max'] = fecha_max
        
        st.subheader("💰 Rangos de Monto")
        st.caption("Columna: MontoOpe")
        
        if 'MontoOpe' in df_todas_operaciones.columns:
            monto_min_bd = float(df_todas_operaciones['MontoOpe'].min())
            monto_max_bd = float(df_todas_operaciones['MontoOpe'].max())
        else:
            monto_min_bd = 0.0
            monto_max_bd = 1000000.0
        
        col1, col2 = st.columns(2)
        with col1:
            monto_min = st.number_input("Monto Mínimo", min_value=0.0, value=monto_min_bd, step=100.0, format="%.2f", key="monto_min_input")
        with col2:
            monto_max = st.number_input("Monto Máximo", min_value=0.0, value=monto_max_bd, step=100.0, format="%.2f", key="monto_max_input")
        
        if monto_min > monto_min_bd or monto_max < monto_max_bd:
            st.session_state.filtros_modificados = True
        if monto_min > monto_min_bd:
            filtros_temp['monto_min'] = monto_min
        if monto_max < monto_max_bd:
            filtros_temp['monto_max'] = monto_max
        
        st.subheader("🏦 Filtros de Operación")
        st.caption("Columna: MonedaUtilizada")
        opciones_moneda = ["Sol peruano", "Dólar estadounidense", "Euro", "Libra esterlina (de Gran Bretaña)"]
        moneda_util = st.multiselect("Moneda Utilizada", options=opciones_moneda, default=opciones_moneda, key="moneda_input")
        if len(moneda_util) < len(opciones_moneda) and len(moneda_util) > 0:
            filtros_temp['moneda_utilizada'] = moneda_util
            st.session_state.filtros_modificados = True
        
        st.caption("Columna: TipoFondo")
        opciones_fondo = ["Operación realizada con fondos en efectivo", "Operación realizada con fondos que no son efectivo"]
        tipo_fondo = st.multiselect("Tipo Fondo", options=opciones_fondo, default=opciones_fondo, key="fondo_input")
        if len(tipo_fondo) < len(opciones_fondo) and len(tipo_fondo) > 0:
            filtros_temp['tipo_fondo'] = tipo_fondo
            st.session_state.filtros_modificados = True
        
        st.caption("Columna: FormaOpe")
        opciones_forma = ["Otros", "Medios o plataformas virtuales", "Presencialmente (a través de la ventanilla)", "Procesamiento por lotes (batch)"]
        forma_ope = st.multiselect("Forma Operación", options=opciones_forma, default=opciones_forma, key="forma_input")
        if len(forma_ope) < len(opciones_forma) and len(forma_ope) > 0:
            filtros_temp['forma_ope'] = forma_ope
            st.session_state.filtros_modificados = True
        
        st.caption("Columna: TipoOpe")
        if 'TipoOpe' in df_todas_operaciones.columns:
            opciones_tipo_ope = sorted(df_todas_operaciones['TipoOpe'].dropna().unique().tolist())
            if len(opciones_tipo_ope) > 0 and len(opciones_tipo_ope) < 50:
                tipo_ope_sel = st.multiselect("Tipo de Operación", options=opciones_tipo_ope, default=opciones_tipo_ope, key="tipo_ope_input")
                if len(tipo_ope_sel) < len(opciones_tipo_ope) and len(tipo_ope_sel) > 0:
                    filtros_temp['tipo_ope'] = tipo_ope_sel
                    st.session_state.filtros_modificados = True
        
        st.caption("Columna: destipclasifpartyrelacionado")
        if 'destipclasifpartyrelacionado' in df_todas_operaciones.columns:
            opciones_vinculo = sorted(df_todas_operaciones['destipclasifpartyrelacionado'].dropna().unique().tolist())
            if len(opciones_vinculo) > 0:
                vinculo_sel = st.multiselect("Tipo Vínculo", options=opciones_vinculo, default=opciones_vinculo, key="vinculo_input")
                if len(vinculo_sel) < len(opciones_vinculo) and len(vinculo_sel) > 0:
                    filtros_temp['destipclasifpartyrelacionado'] = vinculo_sel
                    st.session_state.filtros_modificados = True
        
        st.divider()
        st.subheader("📊 Opciones de Visualización")
        usar_log = st.checkbox("Generar vista logarítmica", value=True, key="vista_log")
        st.session_state.vista_logaritmica = usar_log
        st.divider()
        
        boton_aplicar = st.button("✅ Aplicar Filtros", type="primary", disabled=not st.session_state.filtros_modificados, use_container_width=True)
        if boton_aplicar:
            st.session_state.filtros_aplicados = filtros_temp.copy()
            st.session_state.filtros_modificados = False
            st.rerun()
        
        return st.session_state.filtros_aplicados

def pagina_carga_datos():
    st.title("📤 Carga de Datos RO")
    codigo_carga = st.text_input("Código de Carga (identificador único)", key="codigo_carga")
    archivo = st.file_uploader("Seleccionar archivo Excel del RO", type=['xlsx', 'xls'])
    
    if archivo and codigo_carga:
        if st.button("Cargar Datos", type="primary"):
            try:
                df = pd.read_excel(archivo)
                st.write("Vista previa de los datos:")
                st.dataframe(df.head())
                if 'FechaOp' in df.columns:
                    df['FechaOp'] = pd.to_datetime(df['FechaOp'], errors='coerce')
                if 'MontoOpe' in df.columns:
                    df['MontoOpe'] = pd.to_numeric(df['MontoOpe'], errors='coerce')
                if 'MontoOpeCambio' in df.columns:
                    df['MontoOpeCambio'] = pd.to_numeric(df['MontoOpeCambio'], errors='coerce')
                
                exito, resultado = st.session_state.db_manager.cargar_datos(df, codigo_carga, archivo.name)
                if exito:
                    st.success(f"✅ Datos cargados exitosamente. ID de carga: {resultado}")
                    st.session_state.clientes_muestra = []
                    st.balloons()
                else:
                    st.error(f"❌ Error al cargar datos: {resultado}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    st.divider()
    st.subheader("Cargas Existentes")
    df_cargas = st.session_state.db_manager.get_cargas()
    if not df_cargas.empty:
        st.dataframe(df_cargas, use_container_width=True)
    else:
        st.info("No hay cargas registradas")
    
    st.divider()
    st.subheader("⚙️ Configuración de Clientes Muestra")
    
    todos_documentos = st.session_state.db_manager.get_todos_documentos()
    
    if not st.session_state.clientes_muestra and todos_documentos:
        st.session_state.clientes_muestra = todos_documentos

    clientes_seleccionados = st.multiselect(
        "Documentos de clientes (Puede eliminar o agregar de la lista)",
        options=todos_documentos,
        default=st.session_state.clientes_muestra
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Guardar Clientes Muestra", type="primary"):
            st.session_state.clientes_muestra = clientes_seleccionados
            st.success(f"✅ {len(clientes_seleccionados)} clientes guardados en la muestra")
            st.rerun()
    with col2:
        if st.button("Restaurar Todos los Clientes"):
            st.session_state.clientes_muestra = todos_documentos
            st.rerun()
            
    if st.session_state.clientes_muestra:
        st.write(f"**Clientes en muestra activos:** {len(st.session_state.clientes_muestra)}")

def mostrar_info_columnas(columnas):
    st.info(f"📋 **Columnas usadas:** {', '.join(columnas)}")

def mostrar_tabla_con_toggle(df, nombre_base, mostrar_grafico=True):
    if df.empty:
        st.warning(f"No hay datos para {nombre_base}")
        return
    
    tab1, tab2 = st.tabs(["📊 Por Cantidad", "💰 Por Monto"])
    with tab1:
        if 'cantidad_operaciones' in df.columns:
            df_cant = df.sort_values('cantidad_operaciones', ascending=False).head(20)
            st.dataframe(df_cant, use_container_width=True, height=400)
            if mostrar_grafico and len(df_cant) > 0:
                fig = Visualizador.crear_barras(df_cant.reset_index(), df_cant.index.name if df_cant.index.name else 'index', 'cantidad_operaciones', f'Top 20 - {nombre_base} (Por Cantidad)', df_cant.index.name if df_cant.index.name else 'Categoría', 'Cantidad de Operaciones')
                st.plotly_chart(fig, use_container_width=True)
    with tab2:
        if 'monto_total' in df.columns:
            df_monto = df.sort_values('monto_total', ascending=False).head(20)
            st.dataframe(df_monto, use_container_width=True, height=400)
            if mostrar_grafico and len(df_monto) > 0:
                fig = Visualizador.crear_barras(df_monto.reset_index(), df_monto.index.name if df_monto.index.name else 'index', 'monto_total', f'Top 20 - {nombre_base} (Por Monto)', df_monto.index.name if df_monto.index.name else 'Categoría', 'Monto Total')
                st.plotly_chart(fig, use_container_width=True)

def mostrar_grafo_relaciones(df_ops, col_origen, col_destino, viz):
    if df_ops.empty or col_origen not in df_ops.columns or col_destino not in df_ops.columns:
        return
    
    df_edges = df_ops.rename(columns={col_origen: 'origen', col_destino: 'destino', 'MontoOpe': 'monto'})
    
    if not df_edges.empty:
        st.subheader("🕸️ Red de Relaciones")
        net = viz.crear_grafo_red(df_edges, 'origen', 'destino', 'monto')
        net.save_graph('temp_graph.html')
        with open('temp_graph.html', 'r', encoding='utf-8') as f:
            components.html(f.read(), height=850)

def ejecutar_analisis(tipo_analisis, analizador, viz, df_operaciones, dias_analisis=7):
    st.divider()
    if tipo_analisis == "Top 10 - Todas las Columnas":
        st.header("📊 Top 10 - Todas las Columnas")
        mostrar_info_columnas(["Todas las columnas principales"])
        resultados = analizador.reporte_top10()
        for col, df in resultados.items():
            with st.expander(f"📌 {col}"):
                mostrar_tabla_con_toggle(df, col)
    elif tipo_analisis == "1. Actividad Más Común Ejecutantes":
        st.header("👤 Reporte 1: Actividad Más Común Ejecutantes")
        mostrar_info_columnas(["OcupSol", "NroDocSol (muestra)"])
        resultado = analizador.reporte_1_actividad_ejecutantes()
        mostrar_tabla_con_toggle(resultado, "Actividad Ejecutantes")
    elif tipo_analisis == "2. Vinculado Ejecutantes (para quién ejecutan)":
        st.header("🔗 Reporte 2: Vinculado Ejecutantes")
        mostrar_info_columnas(["destipclasifpartyrelacionado", "NroDocSol (muestra)", "TipPerOrd"])
        mostrar_tabla_con_toggle(analizador.reporte_2_vinculado_ejecutantes('todos'), "Todos") 
    elif tipo_analisis == "3. Actividad Económica Beneficiarios (a quién ejecutan)":
        st.header("💼 Reporte 3: Actividad Económica Beneficiarios")
        mostrar_info_columnas(["OcupBen", "NroDocSol (muestra)", "TipPerOrd"])
        mostrar_tabla_con_toggle(analizador.reporte_3_actividad_ben_ejecutantes('todos'), "Todos") 
    elif tipo_analisis == "4. Tipo Operación Ejecutantes (mediante qué ejecutan)":
        st.header("📋 Reporte 4: Tipo Operación Ejecutantes")
        mostrar_info_columnas(["TipoOpe", "NroDocSol (muestra)", "TipPerOrd"])
        mostrar_tabla_con_toggle(analizador.reporte_4_tipo_ope_ejecutantes('todos'), "Todos") 
    elif tipo_analisis == "5. Beneficiarios en Común (ejecutantes)":
        st.header("👥 Reporte 5: Beneficiarios en Común")
        mostrar_info_columnas(["NroDocBen", "NroDocSol (muestra)", "NombresBen", "OcupBen"])
        resultado = analizador.reporte_5_beneficiarios_comunes()
        if not resultado.empty:
            st.dataframe(resultado, use_container_width=True, height=400)
            df_rel = analizador.filtrar_muestra_ejecutantes()
            df_rel = df_rel[df_rel['NroDocBen'].isin(resultado.index)]
            mostrar_grafo_relaciones(df_rel, 'NroDocSol', 'NroDocBen', viz)
        else:
            st.info("No hay beneficiarios en común")
    elif tipo_analisis == "6. Cuentas Beneficiarias en Común (ejecutantes)":
        st.header("🏦 Reporte 6: Cuentas Beneficiarias en Común")
        mostrar_info_columnas(["CtaBen", "NroDocSol (muestra)", "NombresBen", "ApPaternoBen", "ApMaternoBen", "NombresSol", "ApPaternoSol", "ApMaternoSol"])
        resultado = analizador.reporte_6_cuentas_ben_comunes()
        if not resultado.empty:
            st.dataframe(resultado, use_container_width=True, height=400)
            df_rel = analizador.filtrar_muestra_ejecutantes()
            df_rel = df_rel[df_rel['CtaBen'].isin(resultado.index)]
            mostrar_grafo_relaciones(df_rel, 'NroDocSol', 'CtaBen', viz)
        else:
            st.info("No hay cuentas en común")
    elif tipo_analisis == "7. Actividad Económica Ben. en Efectivo (ejecutantes)":
        st.header("💵 Reporte 7: Actividad Ben. en Efectivo")
        mostrar_info_columnas(["OcupBen", "TipoFondo", "NroDocSol (muestra)"])
        mostrar_tabla_con_toggle(analizador.reporte_7_actividad_ben_efectivo('todos'), "Todos")
    elif tipo_analisis == "8. Ordenantes en Común (ejecutantes)":
        st.header("👥 Reporte 8: Ordenantes en Común")
        mostrar_info_columnas(["NroDocOrd", "NroDocSol (muestra)", "NombresOrd", "ApPaternoOrd", "ApMaternoOrd", "NombresSol", "ApPaternoSol", "ApMaternoSol"])
        resultado = analizador.reporte_8_ordenantes_comunes()
        if not resultado.empty:
            st.dataframe(resultado, use_container_width=True, height=400)
            df_rel = analizador.filtrar_muestra_ejecutantes()
            df_rel = df_rel[df_rel['NroDocOrd'].isin(resultado.index)]
            mostrar_grafo_relaciones(df_rel, 'NroDocSol', 'NroDocOrd', viz)
        else:
            st.info("No hay ordenantes en común")
    elif tipo_analisis == "9. Actividad Más Común Ordenantes":
        st.header("👤 Reporte 9: Actividad Ordenantes")
        mostrar_info_columnas(["OcupOrd", "NroDocOrd (muestra)"])
        resultado = analizador.reporte_9_actividad_ordenantes()
        mostrar_tabla_con_toggle(resultado, "Actividad Ordenantes")
    elif tipo_analisis == "10. Vinculado Ordenantes (a quién remiten)":
        st.header("🔗 Reporte 10: Vinculado Ordenantes")
        mostrar_info_columnas(["destipclasifpartyrelacionado", "NroDocOrd (muestra)", "TipPerOrd"])
        t1, t2, t3 = st.tabs(["👥 Todos", "👤 Solo Personas Naturales", "🏢 Solo Personas Jurídicas"])
        with t1: mostrar_tabla_con_toggle(analizador.reporte_10_vinculado_ordenantes('todos'), "Todos")
        with t2: mostrar_tabla_con_toggle(analizador.reporte_10_vinculado_ordenantes('persona'), "Persona Natural")
        with t3: mostrar_tabla_con_toggle(analizador.reporte_10_vinculado_ordenantes('empresa'), "Persona Jurídica")
    elif tipo_analisis == "11. Actividad Económica Ben. (ordenantes remiten)":
        st.header("💼 Reporte 11: Actividad Ben. (Ordenantes)")
        mostrar_info_columnas(["OcupBen", "NroDocOrd (muestra)", "TipPerOrd"])
        t1, t2, t3 = st.tabs(["👥 Todos", "👤 Solo Personas Naturales", "🏢 Solo Personas Jurídicas"])
        with t1: mostrar_tabla_con_toggle(analizador.reporte_11_actividad_ben_ordenantes('todos'), "Todos")
        with t2: mostrar_tabla_con_toggle(analizador.reporte_11_actividad_ben_ordenantes('persona'), "Persona Natural")
        with t3: mostrar_tabla_con_toggle(analizador.reporte_11_actividad_ben_ordenantes('empresa'), "Persona Jurídica")
    elif tipo_analisis == "12. Tipo Operación Ordenantes (mediante qué remiten)":
        st.header("📋 Reporte 12: Tipo Operación Ordenantes")
        mostrar_info_columnas(["TipoOpe", "NroDocOrd (muestra)", "TipPerOrd"])
        t1, t2, t3 = st.tabs(["👥 Todos", "👤 Solo Personas Naturales", "🏢 Solo Personas Jurídicas"])
        with t1: mostrar_tabla_con_toggle(analizador.reporte_12_tipo_ope_ordenantes('todos'), "Todos")
        with t2: mostrar_tabla_con_toggle(analizador.reporte_12_tipo_ope_ordenantes('persona'), "Persona Natural")
        with t3: mostrar_tabla_con_toggle(analizador.reporte_12_tipo_ope_ordenantes('empresa'), "Persona Jurídica")
    elif tipo_analisis == "13. Beneficiarios en Común (ordenantes)":
        st.header("👥 Reporte 13: Beneficiarios en Común (Ordenantes)")
        mostrar_info_columnas(["NroDocBen", "NroDocOrd (muestra)"])
        resultado = analizador.reporte_13_beneficiarios_comunes_ordenantes()
        if not resultado.empty:
            st.dataframe(resultado, use_container_width=True, height=400)
            df_rel = analizador.filtrar_muestra_ordenantes()
            df_rel = df_rel[df_rel['NroDocBen'].isin(resultado.index)]
            mostrar_grafo_relaciones(df_rel, 'NroDocOrd', 'NroDocBen', viz)
        else:
            st.info("No hay beneficiarios en común")
    elif tipo_analisis == "14. Cuentas Beneficiarias en Común (ordenantes)":
        st.header("🏦 Reporte 14: Cuentas Ben. en Común (Ordenantes)")
        mostrar_info_columnas(["CtaBen", "NroDocOrd (muestra)", "NombresBen", "ApPaternoBen", "ApMaternoBen", "NombresOrd", "ApPaternoOrd", "ApMaternoOrd"])
        resultado = analizador.reporte_14_cuentas_ben_comunes_ordenantes()
        if not resultado.empty:
            st.dataframe(resultado, use_container_width=True, height=400)
            df_rel = analizador.filtrar_muestra_ordenantes()
            df_rel = df_rel[df_rel['CtaBen'].isin(resultado.index)]
            mostrar_grafo_relaciones(df_rel, 'NroDocOrd', 'CtaBen', viz)
        else:
            st.info("No hay cuentas en común")
    elif tipo_analisis == "15. Actividad Económica Ben. en Efectivo (ordenantes)":
        st.header("💵 Reporte 15: Actividad Ben. Efectivo (Ordenantes)")
        mostrar_info_columnas(["OcupBen", "TipoFondo", "NroDocOrd (muestra)"])
        t1, t2, t3 = st.tabs(["👥 Todos", "👤 Solo Personas Naturales", "🏢 Solo Personas Jurídicas"])
        with t1: mostrar_tabla_con_toggle(analizador.reporte_15_actividad_ben_efectivo_ordenantes('todos'), "Todos")
        with t2: mostrar_tabla_con_toggle(analizador.reporte_15_actividad_ben_efectivo_ordenantes('persona'), "Persona Natural")
        with t3: mostrar_tabla_con_toggle(analizador.reporte_15_actividad_ben_efectivo_ordenantes('empresa'), "Persona Jurídica")
    elif tipo_analisis == "16. Ejecutantes en Común (ordenantes)":
        st.header("👥 Reporte 16: Ejecutantes en Común (Ordenantes)")
        mostrar_info_columnas(["NroDocSol", "NroDocOrd (muestra)", "NombresSol", "ApPaternoSol", "ApMaternoSol", "NombresOrd", "ApPaternoOrd", "ApMaternoOrd"])
        resultado = analizador.reporte_16_ejecutantes_comunes_ordenantes()
        if not resultado.empty:
            st.dataframe(resultado, use_container_width=True, height=400)
            df_rel = analizador.filtrar_muestra_ordenantes()
            df_rel = df_rel[df_rel['NroDocSol'].isin(resultado.index)]
            mostrar_grafo_relaciones(df_rel, 'NroDocOrd', 'NroDocSol', viz)
        else:
            st.info("No hay ejecutantes en común")
    elif tipo_analisis == "17. Actividad Más Común Beneficiarios":
        st.header("👤 Reporte 17: Actividad Beneficiarios")
        mostrar_info_columnas(["OcupBen", "NroDocBen (muestra)"])
        resultado = analizador.reporte_17_actividad_beneficiarios()
        mostrar_tabla_con_toggle(resultado, "Actividad Beneficiarios")
    elif tipo_analisis == "18. Vinculado Beneficiarios (de quién reciben)":
        st.header("🔗 Reporte 18: Vinculado Beneficiarios")
        mostrar_info_columnas(["destipclasifpartyrelacionado", "NroDocBen (muestra)", "TipPerOrd"])
        t1, t2, t3 = st.tabs(["👥 Todos", "👤 Solo Personas Naturales", "🏢 Solo Personas Jurídicas"])
        with t1: mostrar_tabla_con_toggle(analizador.reporte_18_vinculado_beneficiarios('todos'), "Todos")
        with t2: mostrar_tabla_con_toggle(analizador.reporte_18_vinculado_beneficiarios('persona'), "Persona Natural")
        with t3: mostrar_tabla_con_toggle(analizador.reporte_18_vinculado_beneficiarios('empresa'), "Persona Jurídica")
    elif tipo_analisis == "19. Actividad Económica Ord. (beneficiarios reciben de)":
        st.header("💼 Reporte 19: Actividad Ord. (Beneficiarios)")
        mostrar_info_columnas(["OcupOrd", "NroDocBen (muestra)", "TipPerOrd"])
        t1, t2, t3 = st.tabs(["👥 Todos", "👤 Solo Personas Naturales", "🏢 Solo Personas Jurídicas"])
        with t1: mostrar_tabla_con_toggle(analizador.reporte_19_actividad_ord_beneficiarios('todos'), "Todos")
        with t2: mostrar_tabla_con_toggle(analizador.reporte_19_actividad_ord_beneficiarios('persona'), "Persona Natural")
        with t3: mostrar_tabla_con_toggle(analizador.reporte_19_actividad_ord_beneficiarios('empresa'), "Persona Jurídica")
    elif tipo_analisis == "20. Tipo Operación Beneficiarios (mediante qué reciben)":
        st.header("📋 Reporte 20: Tipo Operación Beneficiarios")
        mostrar_info_columnas(["TipoOpe", "NroDocBen (muestra)", "TipPerOrd"])
        t1, t2, t3 = st.tabs(["👥 Todos", "👤 Solo Personas Naturales", "🏢 Solo Personas Jurídicas"])
        with t1: mostrar_tabla_con_toggle(analizador.reporte_20_tipo_ope_beneficiarios('todos'), "Todos")
        with t2: mostrar_tabla_con_toggle(analizador.reporte_20_tipo_ope_beneficiarios('persona'), "Persona Natural")
        with t3: mostrar_tabla_con_toggle(analizador.reporte_20_tipo_ope_beneficiarios('empresa'), "Persona Jurídica")
    elif tipo_analisis == "21. Ordenantes en Común (beneficiarios)":
        st.header("👥 Reporte 21: Ordenantes en Común (Beneficiarios)")
        mostrar_info_columnas(["NroDocOrd", "NroDocBen (muestra)", "NombresOrd", "ApPaternoOrd", "ApMaternoOrd", "NombresBen", "ApPaternoBen", "ApMaternoBen"])
        resultado = analizador.reporte_21_ordenantes_comunes_beneficiarios()
        if not resultado.empty:
            st.dataframe(resultado, use_container_width=True, height=400)
            df_rel = analizador.filtrar_muestra_beneficiarios()
            df_rel = df_rel[df_rel['NroDocOrd'].isin(resultado.index)]
            mostrar_grafo_relaciones(df_rel, 'NroDocOrd', 'NroDocBen', viz)
        else:
            st.info("No hay ordenantes en común")
    elif tipo_analisis == "22. Cuentas Ordenantes en Común (beneficiarios)":
        st.header("🏦 Reporte 22: Cuentas Ord. en Común (Beneficiarios)")
        mostrar_info_columnas(["CtaOrd", "NroDocBen (muestra)", "NombresOrd", "ApPaternoOrd", "ApMaternoOrd", "NombresBen", "ApPaternoBen", "ApMaternoBen"])
        resultado = analizador.reporte_22_cuentas_ord_comunes_beneficiarios()
        if not resultado.empty:
            st.dataframe(resultado, use_container_width=True, height=400)
            df_rel = analizador.filtrar_muestra_beneficiarios()
            df_rel = df_rel[df_rel['CtaOrd'].isin(resultado.index)]
            mostrar_grafo_relaciones(df_rel, 'CtaOrd', 'NroDocBen', viz)
        else:
            st.info("No hay cuentas en común")
    elif tipo_analisis == "23. Actividad Económica Ej. en Efectivo (beneficiarios)":
        st.header("💵 Reporte 23: Actividad Ej. Efectivo (Beneficiarios)")
        mostrar_info_columnas(["OcupSol", "TipoFondo", "NroDocBen (muestra)"])
        t1, t2, t3 = st.tabs(["👥 Todos", "👤 Solo Personas Naturales", "🏢 Solo Personas Jurídicas"])
        with t1: mostrar_tabla_con_toggle(analizador.reporte_23_actividad_sol_efectivo_beneficiarios('todos'), "Todos")
        with t2: mostrar_tabla_con_toggle(analizador.reporte_23_actividad_sol_efectivo_beneficiarios('persona'), "Persona Natural")
        with t3: mostrar_tabla_con_toggle(analizador.reporte_23_actividad_sol_efectivo_beneficiarios('empresa'), "Persona Jurídica")
    elif tipo_analisis == "24. Ejecutantes en Común (beneficiarios)":
        st.header("👥 Reporte 24: Ejecutantes en Común (Beneficiarios)")
        mostrar_info_columnas(["NroDocSol", "NroDocBen (muestra)", "NombresSol", "ApPaternoSol", "ApMaternoSol", "NombresBen", "ApPaternoBen", "ApMaternoBen"])
        resultado = analizador.reporte_24_ejecutantes_comunes_beneficiarios()
        if not resultado.empty:
            st.dataframe(resultado, use_container_width=True, height=400)
            df_rel = analizador.filtrar_muestra_beneficiarios()
            df_rel = df_rel[df_rel['NroDocSol'].isin(resultado.index)]
            mostrar_grafo_relaciones(df_rel, 'NroDocSol', 'NroDocBen', viz)
        else:
            st.info("No hay ejecutantes en común")
    elif tipo_analisis == "25. Consolidado Actividades (Ej+Ord+Ben)":
        st.header("📊 Reporte 25: Consolidado Actividades")
        mostrar_info_columnas(["OcupSol", "OcupOrd", "OcupBen"])
        resultado = analizador.reporte_25_consolidado_actividades()
        mostrar_tabla_con_toggle(resultado, "Consolidado Actividades")
    elif tipo_analisis == "26. Post Transferencia Internacional":
        st.header("🌍 Reporte 26: Post Transferencia Internacional")
        mostrar_info_columnas(["TipoOpe", "FechaOp", "HoraOp", "NroDocBen (muestra)"])
        ranking, ejemplos, stats = analizador.reporte_26_post_transf_internacional(dias_analisis)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Recepciones", stats['total_recepciones'])
        with col2:
            st.metric("Con Operación Posterior", stats['total_con_posterior'])
            
        if not ranking.empty:
            st.write("---")
            fig = Visualizador.crear_pie(ranking.reset_index(), 'cantidad_operaciones', ranking.index.name, 'Operaciones Posteriores')
            fig.update_layout(
                height=700,
                margin=dict(t=50, b=150, l=0, r=0),
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.15,
                    xanchor="center",
                    x=0.5
                )
            )
            st.plotly_chart(fig, use_container_width=True)
        if not ranking.empty:
            st.subheader("Ranking de Operaciones")
            st.dataframe(ranking, use_container_width=True)
        if not ejemplos.empty:
            st.subheader("Detalle Completo de Operaciones y Flujos")
            st.dataframe(ejemplos, use_container_width=True, height=400)
    elif tipo_analisis == "27. Porcentaje de Efectivo por Rol":
        st.header("💵 Reporte 27: Porcentaje de Efectivo")
        mostrar_info_columnas(["TipoFondo", "TipPerOrd", "clientes muestra"])
        resultados = analizador.reporte_27_porcentaje_efectivo()
        for rol, datos in resultados.items():
            with st.expander(f"📌 {rol.replace('_', ' ').title()}", expanded=True):
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Total Operaciones", f"{datos['total_ops']:,}")
                c2.metric("Op. Efectivo", f"{datos['efectivo_ops']:,}")
                c3.metric("% Operaciones", f"{datos['porc_ops']:.2f}%")
                c4.metric("Monto Efectivo", f"${datos['monto_efectivo']:,.2f}")
                c5.metric("% Monto", f"{datos['porc_monto']:.2f}%")
    elif tipo_analisis == "28. Plaza más Usada para Efectivo":
        st.header("🏙️ Reporte 28: Plaza Efectivo")
        mostrar_info_columnas(["CodUbigeo", "TipoFondo"])
        resultado = analizador.reporte_28_plaza_efectivo()
        mostrar_tabla_con_toggle(resultado, "Plaza Efectivo")
    elif tipo_analisis == "29. Actividad Ejecutante con Minería":
        st.header("⛏️ Reporte 29: Actividad Ejecutante + Minería")
        mostrar_info_columnas(["OcupSol", "OrigenFondos"])
        resultado = analizador.reporte_29_actividad_sol_mineria()
        mostrar_tabla_con_toggle(resultado, "Actividad Minería")
    elif tipo_analisis == "30. Actividad Ordenante con Minería":
        st.header("⛏️ Reporte 30: Actividad Ordenante + Minería")
        mostrar_info_columnas(["OcupOrd", "OrigenFondos"])
        resultado = analizador.reporte_30_actividad_ord_mineria()
        mostrar_tabla_con_toggle(resultado, "Actividad Minería")
    elif tipo_analisis == "31. Actividad Beneficiario con Minería":
        st.header("⛏️ Reporte 31: Actividad Beneficiario + Minería")
        mostrar_info_columnas(["OcupBen", "OrigenFondos"])
        resultado = analizador.reporte_31_actividad_ben_mineria()
        mostrar_tabla_con_toggle(resultado, "Actividad Minería")
    elif tipo_analisis == "32. Consolidado Minería":
        st.header("⛏️ Reporte 32: Consolidado Minería")
        mostrar_info_columnas(["OcupSol", "OcupOrd", "OcupBen", "OrigenFondos"])
        resultado = analizador.reporte_32_consolidado_mineria()
        mostrar_tabla_con_toggle(resultado, "Consolidado Minería")
    elif tipo_analisis == "33. Misma Dirección":
        st.header("🏠 Reporte 33: Misma Dirección")
        mostrar_info_columnas(["DireccionSol", "DireccionOrd", "DireccionBen"])
        resultado = analizador.reporte_33_misma_direccion()
        if not resultado.empty:
            st.dataframe(resultado, use_container_width=True, height=400)
        else:
            st.info("No hay coincidencias de dirección")
    elif tipo_analisis == "34. Mismo Teléfono":
        st.header("📞 Reporte 34: Mismo Teléfono")
        mostrar_info_columnas(["TelefonoSol", "TelefonoOrd", "TelefonoBen"])
        resultado = analizador.reporte_34_mismo_telefono()
        if not resultado.empty:
            st.dataframe(resultado, use_container_width=True, height=400)
        else:
            st.info("No hay coincidencias de teléfono")
    elif tipo_analisis == "35. Nacionalidad Ejecutantes (Chinos)":
        st.header("🌏 Reporte 35: Nacionalidad Ejecutantes")
        mostrar_info_columnas(["CIIUOcupSol", "destipclasifpartyrelacionado"])
        ranking, vinculo = analizador.reporte_35_nacionalidad_sol_chinos()
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Ranking General")
            if not ranking.empty:
                st.dataframe(ranking, use_container_width=True)
        with col2:
            st.subheader("Chinos (CN) - Vínculo")
            if not vinculo.empty:
                st.dataframe(vinculo, use_container_width=True)
                fig = Visualizador.crear_pie(vinculo.reset_index(), 'cantidad_operaciones', vinculo.index.name, 'Vínculo Chinos')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos de chinos")
    elif tipo_analisis == "36. Nacionalidad Ordenantes (Chinos)":
        st.header("🌏 Reporte 36: Nacionalidad Ordenantes")
        mostrar_info_columnas(["CIIUOcupOrd", "destipclasifpartyrelacionado"])
        ranking, vinculo = analizador.reporte_36_nacionalidad_ord_chinos()
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Ranking General")
            if not ranking.empty:
                st.dataframe(ranking, use_container_width=True)
        with col2:
            st.subheader("Chinos (CN) - Vínculo")
            if not vinculo.empty:
                st.dataframe(vinculo, use_container_width=True)
                fig = Visualizador.crear_pie(vinculo.reset_index(), 'cantidad_operaciones', vinculo.index.name, 'Vínculo Chinos')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos de chinos")
    elif tipo_analisis == "37. Nacionalidad Beneficiarios (Chinos)":
        st.header("🌏 Reporte 37: Nacionalidad Beneficiarios")
        mostrar_info_columnas(["CIIUOcupBen", "destipclasifpartyrelacionado"])
        ranking, vinculo = analizador.reporte_37_nacionalidad_ben_chinos()
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Ranking General")
            if not ranking.empty:
                st.dataframe(ranking, use_container_width=True)
        with col2:
            st.subheader("Chinos (CN) - Vínculo")
            if not vinculo.empty:
                st.dataframe(vinculo, use_container_width=True)
                fig = Visualizador.crear_pie(vinculo.reset_index(), 'cantidad_operaciones', vinculo.index.name, 'Vínculo Chinos')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos de chinos")
    elif tipo_analisis == "38. Países Recepción Internacional":
        st.header("🌍 Reporte 38: Países Recepción")
        mostrar_info_columnas(["CodPaisOrigen", "TipoOpe", "NroDocBen (muestra)"])
        resultado = analizador.reporte_38_paises_recepcion()
        mostrar_tabla_con_toggle(resultado, "Países Recepción")
    elif tipo_analisis == "39. Países Envío Internacional":
        st.header("🌍 Reporte 39: Países Envío")
        mostrar_info_columnas(["CodPaisDestino", "TipoOpe", "NroDocOrd (muestra)"])
        resultado = analizador.reporte_39_paises_envio()
        mostrar_tabla_con_toggle(resultado, "Países Envío")
    elif tipo_analisis == "40. Operaciones Entre Clientes Muestra":
        st.header("🔄 Reporte 40: Operaciones Entre Clientes Muestra")
        mostrar_info_columnas(["NroDocSol", "NroDocOrd", "NroDocBen", "clientes muestra", "detalles_participantes"])
        df_inter, df_intra, stats = analizador.reporte_40_operaciones_entre_muestra()
        
        st.subheader("👥 Operaciones Cruzadas (Diferentes Personas)")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Operaciones Cruzadas", f"{stats.get('total_operaciones_inter', 0):,}")
        with col2:
            st.metric("Monto Total Cruzadas", f"${stats.get('monto_total_inter', 0):,.2f}")
            
        if not df_inter.empty:
            st.dataframe(df_inter, use_container_width=True, height=400)
        else:
            st.info("No hay operaciones cruzadas entre diferentes clientes de la muestra")
            
        st.write("---")
        st.subheader("👤 Operaciones Propias (Misma Persona)")
        col3, col4 = st.columns(2)
        with col3:
            st.metric("Total Operaciones Propias", f"{stats.get('total_operaciones_intra', 0):,}")
        with col4:
            st.metric("Monto Total Propias", f"${stats.get('monto_total_intra', 0):,.2f}")
            
        if not df_intra.empty:
            st.dataframe(df_intra, use_container_width=True, height=400)
        else:
            st.info("No hay operaciones hacia sí mismo (Misma Persona)")

def pagina_analisis():
    st.title("📊 Análisis de Datos RO")
    if not st.session_state.clientes_muestra:
        st.warning("⚠️ No hay clientes en la muestra. Por favor configure los clientes en 'Carga de Datos'")
        return
    if 'df_analisis' not in st.session_state:
        st.session_state.df_analisis = None
    
    df_todas_operaciones = st.session_state.db_manager.get_todas_operaciones(None)
    if df_todas_operaciones.empty:
        st.warning("No hay datos cargados en el sistema. Por favor cargue un archivo primero.")
        return
    
    st.success(f"📊 Base de datos: {len(df_todas_operaciones):,} operaciones | 🎯 Muestra: {len(st.session_state.clientes_muestra)} clientes")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Monto Total", f"${df_todas_operaciones['MontoOpe'].sum():,.2f}")
    with col2:
        st.metric("Clientes Únicos", df_todas_operaciones['codunicocli_p'].nunique())
    with col3:
        if 'FechaOp' in df_todas_operaciones.columns:
            st.metric("Período", f"{df_todas_operaciones['FechaOp'].min()} a {df_todas_operaciones['FechaOp'].max()}")
    
    st.divider()
    filtros = aplicar_filtros_generales(df_todas_operaciones)
    df_operaciones = st.session_state.db_manager.get_todas_operaciones(filtros)
    
    if df_operaciones.empty:
        st.warning("No hay operaciones con los filtros aplicados.")
        return
    
    st.info(f"🔍 Operaciones después de filtros: {len(df_operaciones):,}")
    st.session_state.df_analisis = df_operaciones
    
    st.subheader("Seleccione el Reporte a Ejecutar")
    reportes = [
        "TODOS (Ver múltiples reportes)",
        "Top 10 - Todas las Columnas", "1. Actividad Más Común Ejecutantes", "2. Vinculado Ejecutantes (para quién ejecutan)",
        "3. Actividad Económica Beneficiarios (a quién ejecutan)", "4. Tipo Operación Ejecutantes (mediante qué ejecutan)",
        "5. Beneficiarios en Común (ejecutantes)", "6. Cuentas Beneficiarias en Común (ejecutantes)",
        "7. Actividad Económica Ben. en Efectivo (ejecutantes)", "8. Ordenantes en Común (ejecutantes)",
        "9. Actividad Más Común Ordenantes", "10. Vinculado Ordenantes (a quién remiten)",
        "11. Actividad Económica Ben. (ordenantes remiten)", "12. Tipo Operación Ordenantes (mediante qué remiten)",
        "13. Beneficiarios en Común (ordenantes)", "14. Cuentas Beneficiarias en Común (ordenantes)",
        "15. Actividad Económica Ben. en Efectivo (ordenantes)", "16. Ejecutantes en Común (ordenantes)",
        "17. Actividad Más Común Beneficiarios", "18. Vinculado Beneficiarios (de quién reciben)",
        "19. Actividad Económica Ord. (beneficiarios reciben de)", "20. Tipo Operación Beneficiarios (mediante qué reciben)",
        "21. Ordenantes en Común (beneficiarios)", "22. Cuentas Ordenantes en Común (beneficiarios)",
        "23. Actividad Económica Ej. en Efectivo (beneficiarios)", "24. Ejecutantes en Común (beneficiarios)",
        "25. Consolidado Actividades (Ej+Ord+Ben)", "26. Post Transferencia Internacional",
        "27. Porcentaje de Efectivo por Rol", "28. Plaza más Usada para Efectivo",
        "29. Actividad Ejecutante con Minería", "30. Actividad Ordenante con Minería",
        "31. Actividad Beneficiario con Minería", "32. Consolidado Minería",
        "33. Misma Dirección", "34. Mismo Teléfono",
        "35. Nacionalidad Ejecutantes (Chinos)", "36. Nacionalidad Ordenantes (Chinos)",
        "37. Nacionalidad Beneficiarios (Chinos)", "38. Países Recepción Internacional",
        "39. Países Envío Internacional", "40. Operaciones Entre Clientes Muestra"
    ]
    
    analisis_sel = st.selectbox("Seleccione el reporte", reportes, label_visibility="collapsed")
    
    if analisis_sel == "TODOS (Ver múltiples reportes)":
        opciones_reales = reportes[1:]
        st.info("💡 Seleccione el rango de reportes que desea generar en lote")
        rango_min, rango_max = st.slider("Rango de reportes", 1, len(opciones_reales), (1, len(opciones_reales)))
        
        dias_analisis = 7
        reportes_seleccionados = opciones_reales[rango_min-1:rango_max]
        
        if any("26." in rep for rep in reportes_seleccionados):
            dias_analisis = st.slider("Días para analizar operaciones posteriores (Reporte 26)", 1, 30, 7)
            
        if st.button("🚀 Ejecutar Análisis", type="primary", use_container_width=True):
            if st.session_state.df_analisis is not None and not st.session_state.df_analisis.empty:
                analizador = AnalizadorRO(st.session_state.df_analisis, st.session_state.clientes_muestra)
                viz = Visualizador()
                for rep in reportes_seleccionados:
                    ejecutar_analisis(rep, analizador, viz, st.session_state.df_analisis, dias_analisis)
            else:
                st.error("No hay datos para analizar.")
    else:
        dias_analisis = 7
        if analisis_sel == "26. Post Transferencia Internacional":
            dias_analisis = st.slider("Días para analizar operaciones posteriores", 1, 30, 7)
        
        if st.button("🚀 Ejecutar Análisis", type="primary", use_container_width=True):
            if st.session_state.df_analisis is not None and not st.session_state.df_analisis.empty:
                analizador = AnalizadorRO(st.session_state.df_analisis, st.session_state.clientes_muestra)
                viz = Visualizador()
                ejecutar_analisis(analisis_sel, analizador, viz, st.session_state.df_analisis, dias_analisis)
            else:
                st.error("No hay datos para analizar.")

def main():
    st.sidebar.title("🔍 Sistema RO v2")
    menu = st.sidebar.radio("Menú", ["Carga de Datos", "Análisis"])
    if menu == "Carga de Datos":
        pagina_carga_datos()
    elif menu == "Análisis":
        pagina_analisis()

if __name__ == "__main__":
    main()