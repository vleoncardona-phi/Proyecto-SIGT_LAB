USE ProF_Info120262;

CREATE TABLE IF NOT EXISTS administradores (id_admin VARCHAR(30) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    usuario_login VARCHAR(50) NOT NULL UNIQUE,
    correo VARCHAR(100) NOT NULL);

CREATE TABLE IF NOT EXISTS usuarios (id_usuario VARCHAR(30) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    tarjeta_profesional VARCHAR(50) NOT NULL UNIQUE,
    rol ENUM('Administrador', 'Bacteriologo') NOT NULL DEFAULT 'Bacteriologo',
    estado ENUM('Activo', 'Inactivo') NOT NULL DEFAULT 'Activo');

CREATE TABLE IF NOT EXISTS pacientes (id_paciente VARCHAR(30) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    edad INT NOT NULL CHECK (edad >= 0 AND edad <= 120),
    servicio_hospitalario ENUM('UCI', 'Urgencias', 'Hospitalizacion') NOT NULL);

CREATE TABLE IF NOT EXISTS muestras_cultivos (id_muestra VARCHAR(30) PRIMARY KEY,
    id_paciente VARCHAR(30) NOT NULL,
    id_usuario VARCHAR(30) NOT NULL,
    tipo_muestra ENUM('Sangre/Hemocultivo', 'Orina', 'Esputo', 'Liquido Cefalorraquideo') NOT NULL,
    microorganismo_aislado VARCHAR(100) NOT NULL,
    tincion_gram ENUM('Positivo', 'Negativo') NOT NULL,
    fecha_aislamiento DATE NOT NULL,
    CONSTRAINT fk_muestra_paciente FOREIGN KEY (id_paciente) 
        REFERENCES pacientes(id_paciente) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_muestra_usuario FOREIGN KEY (id_usuario) 
        REFERENCES usuarios(id_usuario) ON DELETE RESTRICT ON UPDATE CASCADE);

CREATE TABLE IF NOT EXISTS antibiogramas (id_antibiograma INT AUTO_INCREMENT PRIMARY KEY,
    id_muestra VARCHAR(30) NOT NULL,
    antibiotico VARCHAR(80) NOT NULL,
    familia_antibiotico VARCHAR(80) NOT NULL,
    cmi_ug_ml DECIMAL(8, 3) NOT NULL,
    interpretacion ENUM('Sensible', 'Intermedio', 'Resistente') NOT NULL,
    CONSTRAINT fk_antibiograma_muestra FOREIGN KEY (id_muestra) 
        REFERENCES muestras_cultivos(id_muestra) ON DELETE CASCADE ON UPDATE CASCADE);