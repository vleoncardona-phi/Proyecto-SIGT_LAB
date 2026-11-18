# =====================================================================
# Funciones completas e interoperables para exportar reportes en
# JSON, generar informes impresos en TXT, y crear/leer
# órdenes clínicas en estándar XML (HL7/FHIR ServiceRequest).
# =====================================================================

import os
import json
import datetime
import xml.etree.ElementTree as ET


def _convertir_objetos_fecha(obj):
    """
    Función auxiliar para serializar objetos datetime/date a formato de cadena ISO 8601.
    """
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError(f"Objeto del tipo {type(obj)} no es serializable en JSON")


def exportar_reporte_json(datos_paciente, ruta_salida="datos/reporte_paciente.json"):
    """
    Exporta la historia clínica consolidada y resultados epidemiológicos de un paciente
    a un archivo con formato estructurado JSON.
    """
    if not isinstance(datos_paciente, dict):
        print("Error: 'datos_paciente' debe ser un diccionario válido.")
        return False

    try:
        directorio = os.path.dirname(ruta_salida)
        if directorio:
            os.makedirs(directorio, exist_ok=True)

        with open(ruta_salida, "w", encoding="utf-8") as archivo:
            json.dump(
                datos_paciente,
                archivo,
                indent=4,
                ensure_ascii=False,
                default=_convertir_objetos_fecha
            )
        print(f"Reporte JSON generado exitosamente en: '{ruta_salida}'")
        return True

    except Exception as e:
        print(f"Error crítico al exportar reporte JSON en '{ruta_salida}': {e}")
        return False


def exportar_resumen_txt(datos_paciente, ruta_salida="datos/resumen_paciente.txt"):
    """
    Genera un informe impreso altamente legible en texto plano (.txt) con el desglose
    de paciente, muestra, antibiogramas, interpretación CMI y alertas MDR.
    """
    if not isinstance(datos_paciente, dict):
        print("Error: 'datos_paciente' debe ser un diccionario válido.")
        return False

    try:
        directorio = os.path.dirname(ruta_salida)
        if directorio:
            os.makedirs(directorio, exist_ok=True)

        fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(ruta_salida, "w", encoding="utf-8") as f:
            f.write("======================================================================\n")
            f.write("        SIGT-LAB | SISTEMA DE TRAZABILIDAD MICROBIOLÓGICA             \n")
            f.write("             INFORME CLÍNICO IMPRESO DE MICROBIOLOGÍA                 \n")
            f.write("======================================================================\n")
            f.write(f"Fecha de Emisión: {fecha_actual}\n")
            f.write("----------------------------------------------------------------------\n\n")

            # Sección 1: Datos del Paciente
            info_pac = datos_paciente.get("paciente", {})
            f.write("[1. DATOS DEL PACIENTE]\n")
            f.write(f"  • ID Paciente      : {info_pac.get('id_paciente', 'N/A')}\n")
            f.write(f"  • Nombre Completo  : {info_pac.get('nombre', 'N/A')}\n")
            f.write(f"  • Edad             : {info_pac.get('edad', 'N/A')} años\n")
            f.write(f"  • Servicio Hospital: {info_pac.get('servicio', 'N/A')}\n\n")

            # Sección 2: Muestra Médica e Aislamiento
            info_mue = datos_paciente.get("muestra", {})
            f.write("[2. DATOS DE LA MUESTRA E ISLADO]\n")
            f.write(f"  • Código Muestra   : {info_mue.get('id_muestra', 'N/A')}\n")
            f.write(f"  • Tipo de Muestra  : {info_mue.get('tipo_muestra', 'N/A')}\n")
            f.write(f"  • Microorganismo   : {info_mue.get('microorganismo', 'N/A')}\n")
            f.write(f"  • Tinción Gram     : {info_mue.get('gram', 'N/A')}\n")
            f.write(f"  • Fecha Aislamiento: {info_mue.get('fecha_aislamiento', 'N/A')}\n\n")

            # Sección 3: Alerta Epidemiológica MDR
            alerta = datos_paciente.get("alerta_mdr", {})
            f.write("[3. EVALUACIÓN DE RESISTENCIA Y ALERTAS]\n")
            if alerta.get("es_mdr", False):
                f.write("ALERTA CRÍTICA: CEPA MULTIDROGORESISTENTE (MDR) DETECTADA\n")
                f.write(f"  • Detalle Alerta   : {alerta.get('mensaje', 'Resistencia a >3 familias')}\n")
            else:
                f.write("Estado          : Cepa No MDR / Resistencia dentro de límites bajo control.\n\n")

            # Sección 4: Antibiograma y Concentración Mínima Inhibitoria (CMI)
            antibiograma = datos_paciente.get("antibiograma", [])
            f.write("[4. RESULTADOS DE ANTIBIOGRAMA (CMI)]\n")
            if antibiograma and isinstance(antibiograma, list):
                f.write(f"  {'Antibiótico':<25} | {'CMI (µg/mL)':<12} | {'Interpretación':<15}\n")
                f.write("  " + "-" * 58 + "\n")
                for item in antibiograma:
                    anti = str(item.get("antibiotico", "N/A"))[:24]
                    cmi = str(item.get("cmi_ug_ml", "N/A"))
                    inter = str(item.get("interpretacion", "N/A"))
                    f.write(f"  {anti:<25} | {cmi:<12} | {inter:<15}\n")
            else:
                f.write("  • No hay registros de antibiograma cargados.\n")

            # Sección 5: Notas y Observaciones de Incubación (MongoDB)
            notas = datos_paciente.get("notas_microbiologia", [])
            if notas:
                f.write("\n[5. OBS. DE MORFOLOGÍA E INCUBACIÓN]\n")
                for i, n in enumerate(notas, 1):
                    f.write(f"  Nota #{i}: {n.get('observacion_microscopia', 'N/A')} "
                            f"(Temp: {n.get('temperatura_c', 'N/A')}°C)\n")

            f.write("\n======================================================================\n")
            f.write("            FIN DEL INFORME - SIGT-LAB COMITÉ DE INFECCIONES           \n")
            f.write("======================================================================\n")

        print(f"Resumen TXT generado exitosamente en: '{ruta_salida}'")
        return True

    except Exception as e:
        print(f"Error al exportar resumen TXT en '{ruta_salida}': {e}")
        return False


def exportar_orden_xml(datos_muestra, ruta_salida="datos/orden_servicio.xml"):
    """
    Genera un recurso de Orden Clínica de Laboratorio basado en el estándar
    internacional HL7/FHIR (ServiceRequest) en formato XML.
    """
    if not isinstance(datos_muestra, dict):
        print("Error: 'datos_muestra' debe ser un diccionario válido.")
        return False

    try:
        directorio = os.path.dirname(ruta_salida)
        if directorio:
            os.makedirs(directorio, exist_ok=True)

        root = ET.Element("ServiceRequest", {
            "version": "4.0.1"
        })

        id_elem = ET.SubElement(root, "id")
        id_elem.set("value", str(datos_muestra.get("id_muestra", "MUE_2026_001")))

        status_elem = ET.SubElement(root, "status")
        status_elem.set("value", str(datos_muestra.get("status", "active")))

        intent_elem = ET.SubElement(root, "intent")
        intent_elem.set("value", "order")

        category_elem = ET.SubElement(root, "category")
        cat_coding = ET.SubElement(category_elem, "coding")
        cat_display = ET.SubElement(cat_coding, "display")
        cat_display.set("value", "Microbiology Laboratory Order")

        code_elem = ET.SubElement(root, "code")
        text_elem = ET.SubElement(code_elem, "text")
        text_elem.set("value", str(datos_muestra.get("tipo_muestra", "Hemocultivo")))

        subject_elem = ET.SubElement(root, "subject")
        patient_ref = ET.SubElement(subject_elem, "reference")
        patient_ref.set("value", f"Patient/{datos_muestra.get('id_paciente', 'PAC_1001')}")

        occurrence_elem = ET.SubElement(root, "occurrenceDateTime")
        fecha_req = datos_muestra.get("fecha_aislamiento", datetime.date.today().isoformat())
        occurrence_elem.set("value", str(fecha_req))

        requester_elem = ET.SubElement(root, "requester")
        req_display = ET.SubElement(requester_elem, "display")
        req_display.set("value", str(datos_muestra.get("medico_solicitante", "Dr. Infectólogo de Turno")))

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(ruta_salida, encoding="utf-8", xml_declaration=True)

        print(f"Orden XML HL7/FHIR generada exitosamente en: '{ruta_salida}'")
        return True

    except Exception as e:
        print(f"Error al exportar orden XML HL7/FHIR en '{ruta_salida}': {e}")
        return False


def leer_orden_xml(ruta_xml):
    """
    Lee, analiza y extrae los datos clave de un archivo XML basado en el estándar
    HL7/FHIR ServiceRequest.
    """
    if not os.path.exists(ruta_xml):
        print(f"El archivo XML '{ruta_xml}' no existe.")
        return None

    try:
        tree = ET.parse(ruta_xml)
        root = tree.getroot()

        for elem in root.iter():
            if "}" in elem.tag:
                elem.tag = elem.tag.split("}", 1)[1]

        id_node = root.find("id")
        status_node = root.find("status")
        patient_ref_node = root.find("subject/reference")
        code_text_node = root.find("code/text")
        fecha_node = root.find("occurrenceDateTime")
        requester_node = root.find("requester/display")

        orden_dict = {
            "id_muestra": id_node.attrib.get("value") if id_node is not None and "value" in id_node.attrib else "N/A",
            "status": status_node.attrib.get("value") if status_node is not None and "value" in status_node.attrib else "N/A",
            "id_paciente": patient_ref_node.attrib.get("value") if patient_ref_node is not None and "value" in patient_ref_node.attrib else "N/A",
            "tipo_muestra": code_text_node.attrib.get("value") if code_text_node is not None and "value" in code_text_node.attrib else "N/A",
            "fecha_orden": fecha_node.attrib.get("value") if fecha_node is not None and "value" in fecha_node.attrib else "N/A",
            "medico_solicitante": requester_node.attrib.get("value") if requester_node is not None and "value" in requester_node.attrib else "N/A"
        }

        print(f"Orden XML '{ruta_xml}' leída e interpretada correctamente.")
        return orden_dict

    except ET.ParseError as pe:
        print(f"Error de sintaxis XML en '{ruta_xml}': {pe}")
        return None
    except Exception as e:
        print(f"Error inesperado al leer el archivo XML '{ruta_xml}': {e}")
        return None
