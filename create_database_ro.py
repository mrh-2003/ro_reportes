import sqlite3

def create_database():
    conn = sqlite3.connect('ro_analysis.db')
    cursor = conn.cursor()
    
    cursor.execute('''DROP TABLE IF EXISTS operaciones''')
    cursor.execute('''DROP TABLE IF EXISTS cargas''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cargas (
        id_carga INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_carga TEXT UNIQUE NOT NULL,
        nombre_archivo TEXT,
        fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        num_registros INTEGER
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS operaciones (
        id_operacion INTEGER PRIMARY KEY AUTOINCREMENT,
        id_carga INTEGER,
        CodUbigeo TEXT,
        FechaOp DATE,
        HoraOp TEXT,
        TipoFondo TEXT,
        TipoOpe TEXT,
        DesTipOpe TEXT,
        OrigenFondos TEXT,
        MonedaUtilizada TEXT,
        MonedaUtilizadaCambio TEXT,
        MontoOpe REAL,
        MontoOpeCambio REAL,
        AlcanceOpe TEXT,
        CodPaisOrigen TEXT,
        CodPaisDestino TEXT,
        IntermediarioOpe TEXT,
        FormaOpe TEXT,
        DesFormaOpe TEXT,
        TipDocSol TEXT,
        NroDocSol TEXT,
        RUC_Sol TEXT,
        ApPaternoSol TEXT,
        ApMaternoSol TEXT,
        NombresSol TEXT,
        OcupSol TEXT,
        CIIUOcupSol TEXT,
        DireccionSol TEXT,
        DepSol TEXT,
        ProvSol TEXT,
        DisSol TEXT,
        TelefonoSol TEXT,
        CodigoGenerado_Sol TEXT,
        TipRelOrd TEXT,
        CondResidenciaOrd TEXT,
        TipPerOrd TEXT,
        TipDocOrd TEXT,
        NroDocOrd TEXT,
        RUC_Ord TEXT,
        ApPaternoOrd TEXT,
        ApMaternoOrd TEXT,
        NombresOrd TEXT,
        OcupOrd TEXT,
        CIIUOcupOrd TEXT,
        DesOcupOrd TEXT,
        CargoOrd TEXT,
        DireccionOrd TEXT,
        DepOrd TEXT,
        ProvOrd TEXT,
        DisOrd TEXT,
        TelefonoOrd TEXT,
        EmpresaSupOrd TEXT,
        TipoCtaOrd TEXT,
        CtaOrd TEXT,
        EntidadExtOrd TEXT,
        CodigoGenerado_Ord TEXT,
        TipDocBen TEXT,
        NroDocBen TEXT,
        RUC_Ben TEXT,
        ApPaternoBen TEXT,
        ApMaternoBen TEXT,
        NombresBen TEXT,
        OcupBen TEXT,
        CIIUOcupBen TEXT,
        DireccionBen TEXT,
        DepBen TEXT,
        ProvBen TEXT,
        DisBen TEXT,
        TelefonoBen TEXT,
        EmpresaSupBen TEXT,
        TipoCtaBen TEXT,
        CtaBen TEXT,
        EntidadExtBen TEXT,
        CodigoGenerado_Ben TEXT,
        codunicocli_p TEXT,
        codunicocli_b TEXT,
        destipclasifpartyrelacionado TEXT,
        FOREIGN KEY (id_carga) REFERENCES cargas (id_carga)
    )
    ''')
    
    indices = [
        'CREATE INDEX IF NOT EXISTS idx_fecha ON operaciones(FechaOp)',
        'CREATE INDEX IF NOT EXISTS idx_monto ON operaciones(MontoOpe)',
        'CREATE INDEX IF NOT EXISTS idx_tipo_ope ON operaciones(TipoOpe)',
        'CREATE INDEX IF NOT EXISTS idx_nrodoc_sol ON operaciones(NroDocSol)',
        'CREATE INDEX IF NOT EXISTS idx_nrodoc_ord ON operaciones(NroDocOrd)',
        'CREATE INDEX IF NOT EXISTS idx_nrodoc_ben ON operaciones(NroDocBen)',
        'CREATE INDEX IF NOT EXISTS idx_tipo_fondo ON operaciones(TipoFondo)',
        'CREATE INDEX IF NOT EXISTS idx_moneda ON operaciones(MonedaUtilizada)',
        'CREATE INDEX IF NOT EXISTS idx_vinculo ON operaciones(destipclasifpartyrelacionado)'
    ]
    
    for idx in indices:
        cursor.execute(idx)
    
    conn.commit()
    conn.close()
    print("Base de datos creada exitosamente")

if __name__ == "__main__":
    create_database()
