import sqlite3
import pandas as pd
from passlib.context import CryptContext
from datetime import datetime

# Rutas
db_path    = "app/db.sqlite3"
excel_path = "LISTADO DE PERSONAL OPERATIVO.xlsx"

# Configurar hashing con bcrypt (mismo esquema de tu módulo)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# 1) Conectar a la base de datos
conn   = sqlite3.connect(db_path)
cursor = conn.cursor()

# 2) Leer raw para detectar encabezado real
df_raw = pd.read_excel(excel_path, header=None)
header_row = None
for idx, row in df_raw.iterrows():
    if str(row[0]).strip() == 'N°E' and str(row[1]).strip().upper() == 'EMPLEADO':
        header_row = idx
        break
if header_row is None:
    raise ValueError("No se encontró la fila de encabezados 'N°E','EMPLEADO','PUESTO'.")

# 3) Leer con encabezados correctos
df = pd.read_excel(excel_path, skiprows=header_row+1)
df.columns = ["employee_number", "full_name", "role_name"]

# 4) Filtrar filas válidas (número de empleado numérico y nombre no nulo)
df = df[df["employee_number"].apply(lambda x: str(x).isnumeric()) & df["full_name"].notna()]
df["employee_number"] = df["employee_number"].astype(int)
df["full_name"]       = df["full_name"].astype(str)
df["role_name"]       = df["role_name"].astype(str)

# 5) Función para dividir nombres y apellidos compuestos
def split_name(full_name):
    parts = full_name.strip().split()
    partículas = {'DE','DEL','LA','LAS','LOS','SAN','SANTA'}
    if len(parts) > 4 and parts[1].upper() not in partículas:
        given_count = 2
    else:
        given_count = 1
    surname_tokens = parts[:-given_count]
    given_tokens   = parts[-given_count:]
    if len(surname_tokens) > 1 and surname_tokens[1].upper() in partículas:
        first_surname  = surname_tokens[0]
        second_surname = " ".join(surname_tokens[1:])
    elif surname_tokens and surname_tokens[0].upper() in partículas:
        if len(surname_tokens) >= 4 and surname_tokens[-2].upper() in partículas:
            maternal_count = 2
        else:
            maternal_count = 1
        first_surname  = " ".join(surname_tokens[:-maternal_count])
        second_surname = " ".join(surname_tokens[-maternal_count:])
    else:
        first_surname  = surname_tokens[0] if surname_tokens else ""
        second_surname = surname_tokens[1] if len(surname_tokens) > 1 else ""
    first_name  = given_tokens[0] if given_tokens else ""
    middle_name = " ".join(given_tokens[1:]) if len(given_tokens) > 1 else ""
    return pd.Series({
        "first_name":     first_name,
        "middle_name":    middle_name,
        "first_surname":  first_surname,
        "second_surname": second_surname
    })

# 6) Aplicar separación y crear username
df_names = df["full_name"].apply(split_name)
df = pd.concat([df, df_names], axis=1)
df["username"] = df["employee_number"].astype(str)

# 7) Insertar roles únicos desde el Excel
unique_roles = df["role_name"].str.strip().unique()
for role in unique_roles:
    cursor.execute(
        "INSERT OR IGNORE INTO role (role_name) VALUES (?)",
        (role.strip(),)
    )
# Confirmar inserción de roles antes de cargar role_id\conn.commit()

# 8) Cargar roles desde DB para mapear role_id
cursor.execute("SELECT role_id, role_name FROM role")
role_rows = cursor.fetchall()
role_dict = {name.strip().upper(): rid for rid, name in role_rows}

df["role_id"] = df["role_name"].apply(lambda rn: role_dict.get(rn.strip().upper()))

# 9) Inicializar columna para debug df["inserted_user_id"]
df["inserted_user_id"] = None

# 10) Valores por defecto para user insert
default_password = "Arga2025"
default_hashed   = hash_password(default_password)
default_active   = True
now_str          = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 11) Función para mostrar DataFrame antes y después de INSERT
def display_df(df, title):
    print(f"\n======= {title} =======")
    print(df[[
        "employee_number", "username",
        "first_name", "middle_name",
        "first_surname", "second_surname",
        "role_name", "role_id", "inserted_user_id"
    ]].to_string(index=False))
    print("========================================\n")

# Mostrar antes de INSERT
display_df(df, "Antes de INSERT")

# 12) Insertar usuarios y capturar new user_id
inserted = 0
for idx, row in df.iterrows():
    if pd.notna(row["role_id"]):
        cursor.execute(
            """
            INSERT OR IGNORE INTO user (
                employee_number, username, email,
                first_name, middle_name, first_surname, second_surname,
                hashed_password, is_active, created_at, role_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
            row["employee_number"], row["username"], None,
            row["first_name"], row["middle_name"],
            row["first_surname"], row["second_surname"],
            default_hashed, default_active, now_str,
            int(row["role_id"])
        ))
        new_id = cursor.lastrowid
        df.at[idx, "inserted_user_id"] = new_id
        print(f"✅ Insertó {row['employee_number']} como user_id {new_id}")
        inserted += 1
    else:
        print(f"[⚠️] No insertado {row['employee_number']}: rol '{row['role_name']}' no encontrado")

# 13) Mostrar después y finalizar
# Asegurar commit de usuarios
conn.commit()

display_df(df, "Después de INSERT")
conn.close()
print(f"\n✅ Procesados {inserted} usuarios con role_id válido.")
