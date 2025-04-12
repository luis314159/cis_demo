-- Script para poblar la base de datos
-- Inserción de datos para tablas base (sin dependencias)

-- Tabla stage
INSERT INTO stage (stage_name) VALUES 
    ('CUTTING'),
    ('MACHINING'),
    ('WAREHOUSE'),
    ('BENT');

-- Tabla process
INSERT INTO process (process_name) VALUES 
    ('Incoming Inspection'),
    ('Cutting'),
    ('Bending'),
    ('Assembly'),
    ('Welding'),
    ('Mock up'),
    ('Sand Blast'),
    ('Pressure Test'),
    ('Painting'),
    ('Shipping');

-- Tabla product  
-- Se asignan IDs numéricos a los productos para cumplir con la inserción en dos columnas.
INSERT INTO product (product_id, product_name) VALUES 
    (1, 'TANKS'),
    (2, 'ENCLOSURES'),
    (3, 'ATC/COMPARTMENT'),
    (4, 'CLAMP/HEAD IRON'),
    (5, 'JUNCTION BOX');

-- Tabla status
INSERT INTO status (status_name) VALUES 
    ('Pending'),
    ('Ok'),
    ('Error');

-- Tabla correction_process  
-- Se asignan IDs numéricos a cada proceso de corrección.
INSERT INTO correction_process (correction_process_id, correction_process_description) VALUES 
    (1, 'REWORK'),
    (2, 'SCRAP');

-- Tabla image_type
INSERT INTO image_type (type_name) VALUES 
    ('SOLVED IMAGE'),
    ('LOCATION IMAGE'),
    ('BEFORE ERROR');

-- Tabla role
INSERT INTO role (role_name) VALUES 
    ('Inspector'),
    ('Operator');

-- Tablas con dependencias nivel 1

-- Tabla process_stage (relación entre procesos y etapas)
INSERT INTO process_stage (process_id, stage_id, "order") VALUES 
    (1, 1, 1),  -- Incoming Inspection - Stage 1
    (2, 1, 2),  -- Cutting - Stage 1
    (3, 2, 1),  -- Bending - Stage 2
    (4, 2, 2),  -- Assembly - Stage 2
    (5, 3, 1),  -- Welding - Stage 3
    (6, 3, 2),  -- Mock up - Stage 3
    (7, 4, 1),  -- Sand Blast - Stage 4
    (8, 4, 2),  -- Pressure Test - Stage 4
    (9, 4, 3),  -- Painting - Stage 4
    (10, 4, 4); -- Shipping - Stage 4

-- Tabla issue (problemas relacionados con procesos)
INSERT INTO issue (issue_description, process_id) VALUES 
    ('Material defect', 1),
    ('Wrong dimensions', 1),
    ('Cutting error', 2),
    ('Bending angle incorrect', 3),
    ('Assembly misalignment', 4),
    ('Welding defect', 5),
    ('Mock up failure', 6),
    ('Incomplete sand blasting', 7),
    ('Pressure leak', 8),
    ('Paint defect', 9),
    ('Packaging damage', 10);

-- Tabla job (trabajos relacionados con productos)
INSERT INTO job (job_code, status, created_at, product_id) VALUES 
    ('VA3300-001', 1, datetime('now', '-30 days'), 1),
    ('WN634C-001', 1, datetime('now', '-28 days'), 1),
    ('VA325E-001', 0, datetime('now', '-25 days'), 2),
    ('62094-001', 1, datetime('now', '-20 days'), 2),
    ('VA3300-002', 0, datetime('now', '-18 days'), 3),
    ('WN634C-002', 1, datetime('now', '-15 days'), 3),
    ('VA325E-002', 0, datetime('now', '-12 days'), 4),
    ('62094-002', 1, datetime('now', '-10 days'), 4),
    ('VA3300-003', 0, datetime('now', '-8 days'), 5),
    ('WN634C-003', 1, datetime('now', '-5 days'), 5);

-- Tabla user (usuarios con roles)
-- Se corrige el nombre de la columna 'password' a 'hashed_pwd' según la definición de la tabla.
INSERT INTO "user" (
    employee_number, 
    username, 
    email, 
    first_name, 
    middle_name, 
    first_surname, 
    second_surname, 
    hashed_pwd, 
    active, 
    created_at, 
    modified_at, 
    last_login, 
    role_id
) VALUES 
    (10001, 'inspector1', 'inspector1@example.com', 'John', NULL, 'Smith', NULL, 'hashed_pwd_1', 1, datetime('now', '-60 days'), NULL, NULL, 1),
    (10002, 'inspector2', 'inspector2@example.com', 'Mary', 'Jane', 'Johnson', NULL, 'hashed_pwd_2', 1, datetime('now', '-58 days'), NULL, NULL, 1),
    (10003, 'operator1', 'operator1@example.com', 'Robert', NULL, 'Brown', 'Jr', 'hashed_pwd_3', 1, datetime('now', '-55 days'), NULL, NULL, 2),
    (10004, 'operator2', 'operator2@example.com', 'Susan', NULL, 'Miller', NULL, 'hashed_pwd_4', 1, datetime('now', '-50 days'), NULL, NULL, 2),
    (10005, 'operator3', 'operator3@example.com', 'James', 'T', 'Wilson', NULL, 'hashed_pwd_5', 1, datetime('now', '-45 days'), NULL, NULL, 2);

-- Tablas con dependencias nivel 2

-- Tabla item (elementos relacionados con jobs y procesos)
INSERT INTO item (
    item_name, espesor, longitud, ancho, alto, 
    volumen, area_superficial, cantidad, material, ocr, 
    job_id, process_id
) VALUES 
    ('Tank panel', 0.5, 100, 80, 2, 16000, 16320, 1, 'Steel', 'TK-PNL-001', 1, 1),
    ('Tank base', 0.8, 90, 90, 5, 40500, 16650, 1, 'Steel', 'TK-BS-001', 1, 2),
    ('Enclosure frame', 0.3, 120, 60, 60, 432000, 15840, 2, 'Aluminum', 'ENC-FR-001', 3, 3),
    ('Compartment door', 0.4, 50, 40, 2, 4000, 4160, 4, 'Steel', 'COMP-DR-001', 5, 4),
    ('Head iron', 1.0, 30, 10, 5, 1500, 700, 8, 'Iron', 'HD-IR-001', 7, 5),
    ('Junction box frame', 0.2, 40, 30, 15, 18000, 2700, 3, 'Aluminum', 'JB-FR-001', 9, 6);

-- Tabla defect_record (registros de defectos)
INSERT INTO defect_record (
    product_id, job_id, 
    inspector_user_id, issue_by_user_id, issue_id, 
    correction_process_id, status_id, date_opened, date_closed
) VALUES 
    (1, 1, 1, 3, 1, 1, 1, datetime('now', '-29 days'), NULL),
    (1, 2, 1, 3, 3, 1, 2, datetime('now', '-27 days'), datetime('now', '-26 days')),
    (2, 3, 2, 4, 4, 1, 3, datetime('now', '-24 days'), NULL),
    (2, 4, 2, 4, 5, 2, 2, datetime('now', '-19 days'), datetime('now', '-18 days')),
    (3, 5, 1, 5, 6, 1, 1, datetime('now', '-17 days'), NULL);

-- Tablas con dependencias nivel 3

-- Tabla object (objetos relacionados con elementos)
INSERT INTO object (item_id, current_stage, rework, scrap) VALUES 
    (1, 1, 0, NULL),
    (2, 2, 1, NULL),
    (3, 2, 0, NULL),
    (4, 3, 1, NULL),
    (5, 4, 0, 1),
    (6, 4, 2, NULL);

-- Tabla defect_image (imágenes relacionadas con registros de defectos)
INSERT INTO defect_image (defect_record_id, image_type_id, image_url) VALUES 
    (1, 3, '/images/defects/def_1_before.jpg'),
    (1, 2, '/images/defects/def_1_location.jpg'),
    (2, 3, '/images/defects/def_2_before.jpg'),
    (2, 1, '/images/defects/def_2_solved.jpg'),
    (3, 3, '/images/defects/def_3_before.jpg'),
    (3, 2, '/images/defects/def_3_location.jpg'),
    (4, 3, '/images/defects/def_4_before.jpg'),
    (4, 1, '/images/defects/def_4_solved.jpg'),
    (5, 3, '/images/defects/def_5_before.jpg'),
    (5, 2, '/images/defects/def_5_location.jpg');
