// 1. Seleccionar la base de datos del proyecto
use ProF_Info120262

// 2. Crear explícitamente las 3 colecciones requeridas
db.createCollection("notas_microbiologia")
db.createCollection("archivos_adjuntos")
db.createCollection("telemetria_incubadora")

// 3. Crear índices en id_muestra para agilizar la trazabilidad con MySQL
db.notas_microbiologia.createIndex({ id_muestra: 1 })
db.archivos_adjuntos.createIndex({ id_muestra: 1 })
db.telemetria_incubadora.createIndex({ id_muestra: 1 })