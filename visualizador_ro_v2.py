import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
from pyvis.network import Network
import pandas as pd
import streamlit as st

class Visualizador:
    @staticmethod
    def crear_barras(df, x_col, y_col, title, x_label, y_label, usar_log=None):
        if usar_log is None:
            usar_log = st.session_state.get('vista_logaritmica', True)
        
        if isinstance(df, pd.Series):
            df = df.reset_index()
            if len(df.columns) == 2:
                x_col = df.columns[0]
                y_col = df.columns[1]
        
        fig = px.bar(
            df.head(20),
            x=x_col,
            y=y_col,
            title=title,
            labels={x_col: x_label, y_col: y_label},
            color=y_col,
            color_continuous_scale='Viridis',
            log_y=usar_log,
            text=y_col
        )
        
        fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
        fig.update_layout(
            xaxis_tickangle=-45,
            height=600,
            hovermode='x unified',
            showlegend=False,
            xaxis_title=x_label,
            yaxis_title=y_label
        )
        
        return fig
    
    @staticmethod
    def crear_pie(df, values_col, names_col, title):
        if isinstance(df, pd.Series):
            df = df.reset_index()
            if len(df.columns) == 2:
                names_col = df.columns[0]
                values_col = df.columns[1]
        
        fig = px.pie(
            df.head(10),
            values=values_col,
            names=names_col,
            title=title,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            height=600,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.02
            )
        )
        
        return fig

    @staticmethod
    def crear_grafo_red(df_relaciones, nodo_origen, nodo_destino, peso=None, titulo="Red de Relaciones"):
        G = nx.DiGraph()
        
        # Agrupar repetidos (por si el df viene con múltiples operaciones de la misma pareja)
        if peso and peso in df_relaciones.columns:
            df_grouped = df_relaciones.groupby([nodo_origen, nodo_destino], dropna=True)[peso].sum().reset_index()
        else:
            df_grouped = df_relaciones.drop_duplicates(subset=[nodo_origen, nodo_destino]).copy()
            df_grouped[peso] = 1.0 if peso else 1.0

        for _, row in df_grouped.head(150).iterrows():
            origen = str(row[nodo_origen])[:20]
            destino = str(row[nodo_destino])[:20]
            w = float(row[peso]) if peso and peso in row else 1.0
            
            if G.has_edge(origen, destino):
                G[origen][destino]['weight'] += w
            else:
                G.add_edge(origen, destino, weight=w)
        
        net = Network(height='800px', width='100%', bgcolor='#222222', font_color='white', directed=True)
        net.from_nx(G)
        
        for node in net.nodes:
            node_id = node['id']
            degree = G.in_degree(node_id) + G.out_degree(node_id)
            node['size'] = degree * 5 + 15
            node['title'] = f"<b>{node_id}</b><br>Conexiones: {degree}"
            node['color'] = {
                'border': '#2B7CE9',
                'background': '#97C2FC',
                'highlight': {'border': '#2B7CE9', 'background': '#D2E5FF'}
            }
        
        for edge in net.edges:
            o = edge['from']
            d = edge['to']
            # PyVis renames the 'weight' payload to 'width' during from_nx
            w = edge.get('width', 1.0)
            
            edge['label'] = f"${w:,.2f}"
            
            if G.has_edge(d, o):
                edge['color'] = '#FF5733'
                edge['font'] = {'color': '#FF5733', 'strokeWidth': 2, 'strokeColor': '#222222', 'align': 'middle', 'size': 14}
                edge['title'] = f"🔄 Movimiento bidireccional\nMonto: ${w:,.2f}"
            else:
                edge['color'] = '#97C2FC'
                edge['font'] = {'color': '#97C2FC', 'strokeWidth': 2, 'strokeColor': '#222222', 'align': 'middle', 'size': 14}
                edge['title'] = f"➡️ Dirección única\nMonto: ${w:,.2f}"
                
            edge['arrows'] = 'to'
            edge['width'] = min(max(w / 10000, 1), 10)
        
        net.set_options('''
        {
          "physics": {
            "repulsion": {
              "centralGravity": 0.0,
              "springLength": 300,
              "springConstant": 0.05,
              "nodeDistance": 300,
              "damping": 0.09
            },
            "maxVelocity": 50,
            "minVelocity": 0.1,
            "solver": "repulsion",
            "stabilization": {"enabled": true, "iterations": 200}
          },
          "nodes": {
            "font": {"size": 16, "color": "white"}
          },
          "edges": {
            "smooth": {"type": "curvedCW", "roundness": 0.2}
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "navigationButtons": true,
            "keyboard": true
          }
        }
        ''')
        return net