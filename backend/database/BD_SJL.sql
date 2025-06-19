-- Eliminar la base de datos completas esto para los entornos de producción 
DROP DATABASE IF EXISTS railway;
-- Crear la base de datos si es que esta no existe todavía 
CREATE DATABASE IF NOT EXISTS railway;
USE railway;

-- Tabla de personas (información base)
CREATE TABLE personas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,             
    apellido_paterno VARCHAR(100) NOT NULL,   
    apellido_materno VARCHAR(100),            
    curp VARCHAR(18) UNIQUE NOT NULL,         
    rfc VARCHAR(13) UNIQUE,                   
    calle VARCHAR(255) NOT NULL,              
    numero_exterior VARCHAR(20) NOT NULL,     	
    numero_interior VARCHAR(20),              
    colonia VARCHAR(100) NOT NULL,            
    municipio VARCHAR(100) NOT NULL,          
    estado VARCHAR(100) NOT NULL,             
    codigo_postal VARCHAR(10) NOT NULL,       
    telefono VARCHAR(20),                     
    email VARCHAR(100) UNIQUE NOT NULL,       
    grupo_vulnerable BOOLEAN DEFAULT FALSE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )ENGINE=INNODB DEFAULT CHARSET=utf8mb4; 

-- Tabla de usuarios (acceso al sistema)
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    persona_id INT NOT NULL,
    contrasena_hash VARCHAR(255) NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    ultimo_acceso TIMESTAMP NULL,
    FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE
) ENGINE=INNODB DEFAULT CHARSET=utf8mb4;

-- Tabla de roles
CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    descripcion VARCHAR(255)
) ENGINE=INNODB DEFAULT CHARSET=utf8mb4;

-- Tabla de relación usuarios-roles
CREATE TABLE usuarios_roles (
    usuario_id INT NOT NULL,		
    rol_id INT NOT NULL,
    fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    asignado_por INT,
    PRIMARY KEY (usuario_id, rol_id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (asignado_por) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=INNODB DEFAULT CHARSET=utf8mb4;

-- Tabla de demandas
CREATE TABLE demandas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    folio VARCHAR(50) UNIQUE NOT NULL,
    demandante_id INT NOT NULL,
    demandado_id INT NOT NULL,
    representante_id INT,
    autoridad_asignada_id INT,
    pretensiones TEXT NOT NULL,
    hechos TEXT NOT NULL,
    fundamento_derecho TEXT NOT NULL,
    tipo_accion VARCHAR(100) NOT NULL,
    valor_demandado DECIMAL(12,2),
    estatus VARCHAR(50) DEFAULT 'registrada',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (demandante_id) REFERENCES personas(id) ON DELETE RESTRICT,
    FOREIGN KEY (demandado_id) REFERENCES personas(id) ON DELETE RESTRICT,
    FOREIGN KEY (representante_id) REFERENCES personas(id) ON DELETE SET NULL,
    FOREIGN KEY (autoridad_asignada_id) REFERENCES personas(id) ON DELETE SET NULL
) ENGINE=INNODB DEFAULT CHARSET=utf8mb4;

-- Tabla de pruebas
CREATE TABLE pruebas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    demanda_id INT NOT NULL,
    descripcion TEXT NOT NULL,
    tipo ENUM('documental', 'testimonial', 'pericial', 'otro') NOT NULL,
    hechos_que_demuestra TEXT,
    fecha_presentacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (demanda_id) REFERENCES demandas(id) ON DELETE CASCADE
) ENGINE=INNODB DEFAULT CHARSET=utf8mb4;

-- Tabla de testigos
CREATE TABLE testigos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prueba_id INT NOT NULL,
    persona_id INT NOT NULL,
    declaracion TEXT,
    FOREIGN KEY (prueba_id) REFERENCES pruebas(id) ON DELETE CASCADE,
    FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE
) ENGINE=INNODB DEFAULT CHARSET=utf8mb4;

-- Tabla de notificaciones
CREATE TABLE notificaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    demanda_id INT NOT NULL,
    persona_id INT NOT NULL,
    tipo ENUM('emplazamiento', 'sentencia', 'auto', 'otro') NOT NULL,
    contenido TEXT NOT NULL,
    fecha_notificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metodo ENUM('electrónico', 'personal', 'edictos') NOT NULL,
    recibido BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (demanda_id) REFERENCES demandas(id) ON DELETE CASCADE,
    FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE
) ENGINE=INNODB DEFAULT CHARSET=utf8mb4;




-- SELECT * FROM personas;
-- SELECT * FROM usuarios;
-- SELECT * FROM roles;
-- SELECT * FROM usuarios_roles;

