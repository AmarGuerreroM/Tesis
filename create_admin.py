# create_admin.py

# Importa la instancia de tu aplicación y la base de datos
from app import app, db 
# Importa todos tus modelos, incluyendo Role
from models import User, Doctor, Appointment, Role 
# Para hashear la contraseña del admin y manejar fechas
from werkzeug.security import generate_password_hash 
import datetime 

def create_initial_data():
    """
    Función para crear la base de datos, roles iniciales,
    un usuario administrador, un doctor de prueba, un paciente de prueba,
    y una cita de prueba.
    """
    with app.app_context(): # Es crucial usar app_context para interactuar con la DB
        # Crea todas las tablas si no existen. Esto también creará site.db si no existe.
        db.create_all() 

        print("Verificando y creando roles iniciales...")
        # Crear roles si no existen
        roles_to_create = ['admin', 'patient', 'doctor', 'secretary']
        for role_name in roles_to_create:
            existing_role = Role.query.filter_by(name=role_name).first()
            if not existing_role:
                new_role = Role(name=role_name)
                db.session.add(new_role)
                print(f'Rol "{role_name}" creado.')
        db.session.commit() # Guarda los roles antes de crear usuarios que los referencian

        # Obtener los objetos de rol para asignarlos a los usuarios
        admin_role_obj = Role.query.filter_by(name='admin').first()
        patient_role_obj = Role.query.filter_by(name='patient').first()
        doctor_role_obj = Role.query.filter_by(name='doctor').first()
        secretary_role_obj = Role.query.filter_by(name='secretary').first() # Por si lo necesitas más adelante

        # --- Crea el usuario administrador ---
        admin_cedula = '1234567890' # Cédula para el admin
        admin_password = 'amarycecilia25' # ¡CAMBIA ESTO A UNA CONTRASEÑA SEGURA EN PRODUCCIÓN!
        admin_email = 'tesis.serviturnos@gmail.com' # Email para el admin

        existing_admin = User.query.filter_by(cedula=admin_cedula).first()

        if not existing_admin:
            admin_user = User(
                cedula=admin_cedula,
                nombres='Administrador',
                apellidos='Principal',
                email=admin_email,
                telefono='0963988595',
                ciudad='Babahoyo',
                parroquia='Clemente Baquerizo',
                direccion='AV Universitaria',
                role_obj=admin_role_obj # Asigna el objeto Role
            )
            admin_user.set_password(admin_password) # Hashear la contraseña
            db.session.add(admin_user)
            db.session.commit() # Guarda el usuario para que tenga un ID
            print(f'Usuario administrador "{admin_cedula}" creado exitosamente.')
            print(f'Contraseña del administrador: {admin_password}') # Solo para desarrollo, no en producción
        else:
            print(f'El usuario administrador "{admin_cedula}" ya existe.')
            admin_user = existing_admin # Si ya existe, obtenlo

        # --- Crear un Doctor de prueba ---
        doctor_cedula = '1111111111'
        existing_doctor_user = User.query.filter_by(cedula=doctor_cedula).first()
        if not existing_doctor_user:
            doctor_user = User(
                cedula=doctor_cedula,
                nombres='Dr. Juan',
                apellidos='Perez',
                email='juan.perez@example.com',
                telefono='0987654321',
                ciudad='Guayaquil',
                parroquia='Norte',
                direccion='Av. Siempre Viva 456',
                role_obj=doctor_role_obj # Asigna el objeto Role
            )
            doctor_user.set_password('doctor_password') # Contraseña para el doctor
            db.session.add(doctor_user)
            db.session.commit() # Guarda el usuario para obtener su ID

            # Crear el registro en la tabla Doctor también
            new_doctor = Doctor(user_id=doctor_user.id, specialty='Cardiología', license_number='LIC12345')
            db.session.add(new_doctor)
            db.session.commit()
            print(f'Usuario doctor "{doctor_cedula}" creado exitosamente.')
            print(f'Contraseña del doctor: doctor_password')
        else:
            doctor_user = existing_doctor_user # Si ya existe, obtenlo
            new_doctor = Doctor.query.filter_by(user_id=doctor_user.id).first()
            if not new_doctor: # Si el usuario existe pero no el registro de doctor
                new_doctor = Doctor(user_id=doctor_user.id, specialty='Cardiología', license_number='LIC12345')
                db.session.add(new_doctor)
                db.session.commit()
            print(f'El usuario doctor "{doctor_cedula}" ya existe.')

        # --- Crear un Paciente de prueba ---
        patient_cedula = '2222222222'
        existing_patient_user = User.query.filter_by(cedula=patient_cedula).first()
        if not existing_patient_user:
            patient_user = User(
                cedula=patient_cedula,
                nombres='Ana',
                apellidos='García',
                email='ana.garcia@example.com',
                telefono='0912345678',
                ciudad='Cuenca',
                parroquia='Sur',
                direccion='Calle Falsa 123',
                role_obj=patient_role_obj # Asigna el objeto Role
            )
            patient_user.set_password('patient_password') # Contraseña para el paciente
            db.session.add(patient_user)
            db.session.commit() # Guarda el usuario para obtener su ID
            print(f'Usuario paciente "{patient_cedula}" creado exitosamente.')
            print(f'Contraseña del paciente: patient_password')
        else:
            patient_user = existing_patient_user
            print(f'El usuario paciente "{patient_cedula}" ya existe.')

        # --- Crear una Cita de prueba (si los usuarios existen) ---
        if patient_user and new_doctor:
            appointment_date = datetime.date.today() + datetime.timedelta(days=7) # Cita para la próxima semana
            appointment_time = datetime.time(10, 0) # 10:00 AM
            
            existing_appointment = Appointment.query.filter_by(
                patient_id=patient_user.id,
                doctor_id=new_doctor.id,
                date=appointment_date,
                time=appointment_time
            ).first()

            if not existing_appointment:
                new_appointment_obj = Appointment(
                    patient_id=patient_user.id,
                    doctor_id=new_doctor.id,
                    date=appointment_date,
                    time=appointment_time,
                    reason='Chequeo general y consulta por tos persistente.'
                )
                db.session.add(new_appointment_obj)
                db.session.commit()
                print('Cita de prueba creada exitosamente.')
            else:
                print('La cita de prueba ya existe.')
        else:
            print("No se pudo crear la cita de prueba: faltan el paciente o el doctor.")


if __name__ == '__main__':
    create_initial_data()