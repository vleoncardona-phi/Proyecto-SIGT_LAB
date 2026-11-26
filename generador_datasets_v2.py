"""
MÓDULO GENERADOR DE DATASETS DE PRUEBA (generador_datasets_v2.py)
Proyecto: SIGT-LAB - Sistema de Gestión y Trazabilidad Microbiológica
Autores del equipo: [Completar con los 4 nombres completos]
Responsable de QA y Dominio Clínico: Integrante 4

Descripción:
Genera los datasets sintéticos en la carpeta datos/ alineados con el esquema
MySQL (esquema_mysql.sql), las colecciones de MongoDB y la tabla de puntos de
corte CLSI M100 requerida por analisis.py. Incluye filas trampa de QA que
deben ser filtradas por precarga.py antes del INSERT.
"""

import csv
import json
import os

os.makedirs("datos", exist_ok=True)


def guardar_csv(nombre_archivo, datos, campos):
    """Exporta una lista de diccionarios a un archivo CSV en datos/."""
    ruta = os.path.join("datos", nombre_archivo)
    with open(ruta, mode="w", newline="", encoding="utf-8") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=campos)
        writer.writeheader()
        writer.writerows(datos)


def guardar_json(nombre_archivo, datos):
    """Exporta una estructura de datos a un archivo JSON en datos/."""
    ruta = os.path.join("datos", nombre_archivo)
    with open(ruta, mode="w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=4, ensure_ascii=False)


# -----------------------------------------------------------------------------
# 1. DATOS ESTRUCTURADOS (MySQL) -> Exportación a CSV
# -----------------------------------------------------------------------------
pacientes = [
    {"id_paciente": 1001, "nombre": "Ana Ruiz", "edad": 54, "servicio_hospitalario": "UCI"},
    {"id_paciente": 1002, "nombre": "Luis Gomez", "edad": 30, "servicio_hospitalario": "Urgencias"},
    {"id_paciente": 1003, "nombre": "Marta Diaz", "edad": 65, "servicio_hospitalario": "Hospitalizacion"},
    # Filas trampa de QA (deben ser rechazadas por precarga.py / validaciones.py)
    {"id_paciente": 1004, "nombre": "Paciente QA 1", "edad": -5, "servicio_hospitalario": "UCI"},
    {"id_paciente": 1005, "nombre": "Paciente QA 2", "edad": "veinte", "servicio_hospitalario": "Urgencias"},
]

muestras = [
    {
        "id_muestra": "MUE_2026_041",
        "id_paciente": 1001,
        "id_usuario": "usr_bacteriologo1",
        "tipo_muestra": "Sangre/Hemocultivo",
        "microorganismo_aislado": "Pseudomonas aeruginosa",
        "tincion_gram": "Negativo",
        "fecha_aislamiento": "2026-11-10",
    },
    {
        "id_muestra": "MUE_2026_042",
        "id_paciente": 1002,
        "id_usuario": "usr_bacteriologo1",
        "tipo_muestra": "Orina",
        "microorganismo_aislado": "Escherichia coli",
        "tincion_gram": "Negativo",
        "fecha_aislamiento": "2026-11-11",
    },
    {
        "id_muestra": "MUE_2026_043",
        "id_paciente": 1003,
        "id_usuario": "usr_bacteriologo2",
        "tipo_muestra": "Esputo",
        "microorganismo_aislado": "Staphylococcus aureus",
        "tincion_gram": "Positivo",
        "fecha_aislamiento": "2026-11-12",
    },
    # Fila trampa de QA (fecha imposible y tinción fuera de catálogo MySQL)
    {
        "id_muestra": "MUE_QA_001",
        "id_paciente": 1004,
        "id_usuario": "usr_bacteriologo1",
        "tipo_muestra": "Liquido Cefalorraquideo",
        "microorganismo_aislado": "Desconocido",
        "tincion_gram": "No informado",
        "fecha_aislamiento": "31/02/2026",
    },
]

antibiogramas = [
    # Perfil MDR (Alerta activa: 3 familias resistentes en P. aeruginosa)
    {"id_antibiograma": 1, "id_muestra": "MUE_2026_041", "antibiotico": "Ceftazidima", "familia_antibiotico": "Cefalosporinas", "cmi_ug_ml": 32.0, "interpretacion": "Resistente"},
    {"id_antibiograma": 2, "id_muestra": "MUE_2026_041", "antibiotico": "Ciprofloxacina", "familia_antibiotico": "Fluoroquinolonas", "cmi_ug_ml": 4.0, "interpretacion": "Resistente"},
    {"id_antibiograma": 3, "id_muestra": "MUE_2026_041", "antibiotico": "Meropenem", "familia_antibiotico": "Carbapenemicos", "cmi_ug_ml": 8.0, "interpretacion": "Resistente"},
    # Perfil No MDR / Control BLEE (1 familia resistente en E. coli)
    {"id_antibiograma": 4, "id_muestra": "MUE_2026_042", "antibiotico": "Ceftriaxona", "familia_antibiotico": "Cefalosporinas", "cmi_ug_ml": 16.0, "interpretacion": "Resistente"},
    {"id_antibiograma": 5, "id_muestra": "MUE_2026_042", "antibiotico": "Meropenem", "familia_antibiotico": "Carbapenemicos", "cmi_ug_ml": 0.5, "interpretacion": "Sensible"},
    # Perfil MRSA (Control S. aureus resistente a oxacilina)
    {"id_antibiograma": 6, "id_muestra": "MUE_2026_043", "antibiotico": "Oxacilina", "familia_antibiotico": "Penicilinas", "cmi_ug_ml": 4.0, "interpretacion": "Resistente"},
    # Fila trampa de QA (CMI negativa sobre muestra inválida)
    {"id_antibiograma": 7, "id_muestra": "MUE_QA_001", "antibiotico": "Penicilina", "familia_antibiotico": "Penicilinas", "cmi_ug_ml": -2.5, "interpretacion": "Sensible"},
]

guardar_csv(
    "pacientes.csv",
    pacientes,
    ["id_paciente", "nombre", "edad", "servicio_hospitalario"],
)
guardar_csv(
    "muestras.csv",
    muestras,
    [
        "id_muestra",
        "id_paciente",
        "id_usuario",
        "tipo_muestra",
        "microorganismo_aislado",
        "tincion_gram",
        "fecha_aislamiento",
    ],
)
guardar_csv(
    "antibiogramas.csv",
    antibiogramas,
    [
        "id_antibiograma",
        "id_muestra",
        "antibiotico",
        "familia_antibiotico",
        "cmi_ug_ml",
        "interpretacion",
    ],
)

# -----------------------------------------------------------------------------
# 2. DATOS NO ESTRUCTURADOS (MongoDB) -> Exportación a JSON
# -----------------------------------------------------------------------------
notas = [
    {
        "id_nota": "NOT_BAC_882",
        "id_muestra": "MUE_2026_041",
        "id_usuario": "usr_bacteriologo1",
        "fecha_registro": "2026-11-10",
        "observacion_microscopia": "Bacilos Gram negativos. Cultivo con pigmento verde (piocianina) y olor frutal dulce.",
        "etiquetas": ["UCI", "Resistencia_Alta", "Gram_Negativo", "MDR_Sospecha"],
        "morfologia_colonia": {
            "color": "Verde-azulado",
            "hemolisis": "Beta-hemolítico",
            "borde": "Irregular",
        },
        "condiciones_incubacion": {
            "temperatura_c": 37.0,
            "co2_pct": 5.0,
        },
    },
    {
        "id_nota": "NOT_BAC_883",
        "id_muestra": "MUE_2026_043",
        "id_usuario": "usr_bacteriologo2",
        "fecha_registro": "2026-11-12",
        "observacion_microscopia": "Cocos Gram positivos agrupados en racimos. Colonias doradas con beta-hemólisis.",
        "etiquetas": ["Hospitalizacion", "Gram_Positivo", "MRSA"],
        "morfologia_colonia": {
            "color": "Amarillo-dorado",
            "hemolisis": "Beta-hemolítico",
            "borde": "Circular",
        },
        "condiciones_incubacion": {
            "temperatura_c": 36.5,
            "co2_pct": 5.0,
        },
    },
]

guardar_json("notas_microbiologia.json", notas)

# -----------------------------------------------------------------------------
# 3. TABLA DE PUNTOS DE CORTE CLSI M100 -> Exportación a JSON
# -----------------------------------------------------------------------------
puntos_corte = {
    "Ceftazidima": {
        "familia": "Cefalosporinas",
        "sensible_max": 8.0,
        "resistente_min": 32.0,
        "fuente": "CLSI M100 (referencia académica P. aeruginosa)",
    },
    "Ciprofloxacina": {
        "familia": "Fluoroquinolonas",
        "sensible_max": 0.5,
        "resistente_min": 2.0,
        "fuente": "CLSI M100 (referencia académica P. aeruginosa)",
    },
    "Meropenem": {
        "familia": "Carbapenemicos",
        "sensible_max": 2.0,
        "resistente_min": 8.0,
        "fuente": "CLSI M100 (referencia académica P. aeruginosa / Enterobacterales)",
    },
    "Ceftriaxona": {
        "familia": "Cefalosporinas",
        "sensible_max": 1.0,
        "resistente_min": 4.0,
        "fuente": "CLSI M100 (referencia académica Enterobacterales)",
    },
    "Oxacilina": {
        "familia": "Penicilinas",
        "sensible_max": 2.0,
        "resistente_min": 4.0,
        "fuente": "CLSI M100 (referencia académica S. aureus)",
    },
    "Penicilina": {
        "familia": "Penicilinas",
        "sensible_max": 0.12,
        "resistente_min": 0.25,
        "fuente": "CLSI M100 (referencia académica)",
    },
}

guardar_json("puntos_corte.json", puntos_corte)

if __name__ == "__main__":
    print("Datasets corregidos y puntos_corte.json generados con éxito en 'datos/'.")