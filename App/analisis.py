import pandas as pd

trabajadores = pd.read_csv(r"C:\Users\marul\OneDrive\Documentos\Programación Avanzada\Proyecto_final\trabajadores.csv")
servicios = pd.read_csv(r"C:\Users\marul\OneDrive\Documentos\Programación Avanzada\Proyecto_final\servicios.csv")
contrataciones = pd.read_csv(r"C:\Users\marul\OneDrive\Documentos\Programación Avanzada\Proyecto_final\contrataciones.csv")

# Análisis de habilidades más demandadas
def habilidades_mas_demandadas(servicios, top_n=10):
    habilidades = servicios['habilidades_requeridas'].str.split(",").explode().str.strip()
    return habilidades.value_counts().head(top_n)

# Análisis de habilidades más ofrecidas (por trabajadores registrados)
def habilidades_mas_ofrecidas(trabajadores, top_n=10):
    habilidades = trabajadores['habilidades_ofrecidas'].str.split(",").explode().str.strip()
    return habilidades.value_counts().head(top_n)

# Análisis de habilidades con mayor brecha entre demanda y oferta
def brecha_demanda_oferta(servicios, trabajadores, top_n=10):
    demanda = servicios['habilidades_requeridas'].str.split(",").explode().str.strip().value_counts()
    oferta = trabajadores['habilidades_ofrecidas'].str.split(",").explode().str.strip().value_counts()
    brecha = (demanda - oferta).fillna(0).astype(int)
    return brecha.sort_values(ascending=False).head(top_n)

# Análisis de servicios publicados por mes
def servicios_por_mes(servicios):
    servicios['fecha_publicacion'] = pd.to_datetime(servicios['fecha_publicacion'])
    servicios_mes = servicios.groupby(servicios['fecha_publicacion'].dt.to_period('M')).size()
    return servicios_mes.reset_index(name='cantidad')

# Análisis de contrataciones realizadas por mes
def contrataciones_por_mes(contrataciones):
    contrataciones['fecha_contratacion'] = pd.to_datetime(contrataciones['fecha_contratacion'])
    contrataciones_mes = contrataciones.groupby(contrataciones['fecha_contratacion'].dt.to_period('M')).size()
    return contrataciones_mes.reset_index(name='cantidad')

# Recomendaciones para el usuario
def recomendar_habilidades(servicios, trabajadores, top_n=10):
    demanda = servicios['habilidades_requeridas'].str.split(",").explode().str.strip().value_counts()
    oferta = trabajadores['habilidades_ofrecidas'].str.split(",").explode().str.strip().value_counts()
    brecha = (demanda - oferta).fillna(0).astype(int)
    brecha_positiva = brecha[brecha > 0]
    recomendaciones = brecha_positiva.sort_values(ascending=False).head(top_n)
    return recomendaciones.reset_index().rename(columns={"index": "habilidad", 0: "brecha"})