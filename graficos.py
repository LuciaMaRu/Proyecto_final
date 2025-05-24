import matplotlib.pyplot as plt
import pandas as pd
from analisis import*

# ------------------------- Funciones de Gráficos -------------------------

def graficar_habilidades_mas_demandadas(servicios, top_n=10):
    habilidades = servicios['habilidades_requeridas'].str.split(",").explode().str.strip().value_counts().head(top_n)
    habilidades.plot(kind='bar', figsize=(10,6))
    plt.title('Top Habilidades Más Demandadas')
    plt.xlabel('Habilidad')
    plt.ylabel('Cantidad de servicios')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

def graficar_habilidades_mas_ofrecidas(trabajadores, top_n=10):
    habilidades = trabajadores['habilidades_ofrecidas'].str.split(",").explode().str.strip().value_counts().head(top_n)
    habilidades.plot(kind='bar', color='green', figsize=(10,6))
    plt.title('Top Habilidades Más Ofrecidas')
    plt.xlabel('Habilidad')
    plt.ylabel('Cantidad de trabajadores')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

def graficar_servicios_por_mes(servicios):
    servicios['fecha_publicacion'] = pd.to_datetime(servicios['fecha_publicacion'])
    servicios_mes = servicios.groupby(servicios['fecha_publicacion'].dt.to_period('M')).size()
    servicios_mes.plot(kind='line', marker='o', figsize=(10,6))
    plt.title('Servicios Publicados por Mes')
    plt.xlabel('Mes')
    plt.ylabel('Cantidad de servicios')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def graficar_contrataciones_por_mes(contrataciones):
    contrataciones['fecha_contratacion'] = pd.to_datetime(contrataciones['fecha_contratacion'])
    contrataciones_mes = contrataciones.groupby(contrataciones['fecha_contratacion'].dt.to_period('M')).size()
    contrataciones_mes.plot(kind='line', marker='o', color='red', figsize=(10,6))
    plt.title('Contrataciones Realizadas por Mes')
    plt.xlabel('Mes')
    plt.ylabel('Cantidad de contrataciones')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def graficar_brecha_demanda_oferta(servicios, trabajadores, top_n=10):
    demanda = servicios['habilidades_requeridas'].str.split(",").explode().str.strip().value_counts()
    oferta = trabajadores['habilidades_ofrecidas'].str.split(",").explode().str.strip().value_counts()
    
    brecha = (demanda - oferta).fillna(0).astype(int)
    brecha_positiva = brecha[brecha > 0].sort_values(ascending=False).head(top_n)

    brecha_positiva.plot(kind='bar', color='orange', figsize=(10,6))
    plt.title('Brecha Demanda vs Oferta (Habilidades con mayor oportunidad)')
    plt.xlabel('Habilidad')
    plt.ylabel('Diferencia (más demanda que oferta)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()