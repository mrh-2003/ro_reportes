#!/usr/bin/env python3
import os
import sys
import subprocess

def verificar_python():
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("Error: Se requiere Python 3.8 o superior")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} detectado")
    return True

def instalar_dependencias():
    print("\n📦 Instalando dependencias...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_ro_v2.txt", "--quiet"])
        print("✓ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError:
        print("✗ Error al instalar dependencias")
        return False

def crear_base_datos():
    print("\n🗄️ Creando base de datos...")
    try:
        from create_database_ro import create_database
        create_database()
        print("✓ Base de datos creada correctamente")
        return True
    except Exception as e:
        print(f"✗ Error al crear base de datos: {str(e)}")
        return False

def iniciar_aplicacion():
    print("\n🚀 Iniciando aplicación Streamlit...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app_ro_v2_main.py"])
    except KeyboardInterrupt:
        print("\n\n👋 Aplicación cerrada")
    except Exception as e:
        print(f"✗ Error al iniciar aplicación: {str(e)}")

def main():
    print("="*60)
    print("   SISTEMA DE ANÁLISIS RO v2 - 40 REPORTES")
    print("="*60)
    
    if not verificar_python():
        return
    
    if not instalar_dependencias():
        return
    
    if not os.path.exists('ro_analysis.db'):
        if not crear_base_datos():
            return
    else:
        print("\n✓ Base de datos existente encontrada")
    
    print("\n" + "="*60)
    print("   SISTEMA LISTO PARA USAR")
    print("="*60)
    print("\nPresione Ctrl+C para detener en cualquier momento")
    print("\nLa aplicación se abrirá en su navegador...")
    
    iniciar_aplicacion()

if __name__ == "__main__":
    main()
