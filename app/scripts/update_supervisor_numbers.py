from sqlmodel import Session, select
from models.users import User, Role
from database import engine  # Ajusta esta importación según la estructura de tu proyecto

def update_supervisors():
    """Actualiza los números de supervisor para usuarios con rol de supervisor."""
    with Session(engine) as session:
        # Primero obtenemos el ID del rol supervisor
        supervisor_role = session.exec(
            select(Role).where(Role.role_name.ilike("supervisor"))
        ).first()
        
        if not supervisor_role:
            print("No se encontró el rol de supervisor en la base de datos.")
            return
        
        # Consultamos todos los usuarios con rol de supervisor
        supervisors = session.exec(
            select(User).where(User.role_id == supervisor_role.role_id)
        ).all()
        
        print(f"Se encontraron {len(supervisors)} usuarios con rol de supervisor.")
        
        # Actualizamos el supervisor_number para cada supervisor si no tiene uno
        counter = 0
        for supervisor in supervisors:
            if not supervisor.supervisor_number:
                # Generar un número de supervisor único basado en su ID
                supervisor.supervisor_number = f"SUP-{supervisor.user_id:04d}"
                counter += 1
                
        if counter > 0:
            print(f"Actualizando {counter} supervisores con números de supervisor...")
            session.commit()
            print("¡Actualización completada con éxito!")
        else:
            print("No hay supervisores que necesiten actualización.")

if __name__ == "__main__":
    update_supervisors()