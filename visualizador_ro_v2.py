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
    def crear_barras_agrupadas(df, x_col, y_cols, title, x_label, y_label, usar_log=None):
        if usar_log is None:
            usar_log = st.session_state.get('vista_logaritmica', True)
        
        fig = go.Figure()
        colors = px.colors.qualitative.Set2
        
        for i, y_col in enumerate(y_cols):
            fig.add_trace(go.Bar(
                name=y_col,
                x=df[x_col],
                y=df[y_col],
                marker_color=colors[i % len(colors)]
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            yaxis_title=y_label,
            yaxis_type='log' if usar_log else 'linear',
            barmode='group',
            height=600,
            xaxis_tickangle=-45,
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def crear_grafo_red(df_relaciones, nodo_origen, nodo_destino, peso=None, titulo="Red de Relaciones"):
        G = nx.DiGraph()
        
        for _, row in df_relaciones.head(150).iterrows():
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
            w = edge.get('weight', 1)
            
            if G.has_edge(d, o):
                edge['color'] = '#FF5733'
                edge['title'] = f"🔄 Ida y vuelta<br>Monto Total: ${w:,.2f}"
            else:
                edge['color'] = '#97C2FC'
                edge['title'] = f"➡️ Dirección única<br>Monto: ${w:,.2f}"
                
            edge['arrows'] = 'to'
            edge['width'] = min(max(w / 10000, 1), 10)
        
        net.set_options('''
        {
          "physics": {
            "forceAtlas2Based": {
              "gravitationalConstant": -100,
              "centralGravity": 0.005,
              "springLength": 250,
              "springConstant": 0.18,
              "avoidOverlap": 1
            },
            "maxVelocity": 50,
            "solver": "forceAtlas2Based",
            "timestep": 0.35,
            "stabilization": {"iterations": 150}
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
    
    @staticmethod
    def crear_lineas_tiempo(df, x_col, y_col, title, group_col=None, usar_log=None):
        if usar_log is None:
            usar_log = st.session_state.get('vista_logaritmica', True)
        
        if group_col:
            fig = px.line(
                df,
                x=x_col,
                y=y_col,
                color=group_col,
                title=title,
                markers=True,
                log_y=usar_log
            )
        else:
            fig = px.line(
                df,
                x=x_col,
                y=y_col,
                title=title,
                markers=True,
                log_y=usar_log
            )
        
        fig.update_layout(
            height=600,
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def crear_scatter(df, x_col, y_col, title, size_col=None, color_col=None, usar_log=None):
        if usar_log is None:
            usar_log = st.session_state.get('vista_logaritmica', True)
        
        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            size=size_col,
            color=color_col,
            title=title,
            hover_data=df.columns,
            log_x=usar_log if df[x_col].min() > 0 else False,
            log_y=usar_log if df[y_col].min() > 0 else False
        )
        
        fig.update_layout(height=600)
        
        return fig
    
    @staticmethod
    def crear_heatmap(df, title):
        fig = px.imshow(
            df,
            title=title,
            color_continuous_scale='RdYlGn',
            aspect='auto'
        )
        
        fig.update_layout(height=600)
        
        return fig
    
    @staticmethod
    def crear_sunburst(df, path_cols, values_col, title):
        fig = px.sunburst(
            df,
            path=path_cols,
            values=values_col,
            title=title,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig.update_layout(height=700)
        
        return fig
    
    @staticmethod
    def crear_treemap(df, path_cols, values_col, title):
        fig = px.treemap(
            df,
            path=path_cols,
            values=values_col,
            title=title,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig.update_layout(height=700)
        
        return fig