# models.py

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound # Importar para manejar el caso de no encontrar doctor

# Define el objeto 'db' de SQLAlchemy aquí.
# NO importes 'db' desde 'app.py' en este archivo.
db = SQLAlchemy()


# Modelo para Roles de Usuario
class Role(db.Model):
    __tablename__ = 'roles' # Nombre de la tabla explícito

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return f'<Role {self.name}>'

# Modelo para Usuario
class User(db.Model, UserMixin):
    __tablename__ = 'users' # Nombre de la tabla explícito

    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(20), unique=True, nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False) # Contraseña hasheada
    telefono = db.Column(db.String(20), nullable=True)
    ciudad = db.Column(db.String(100), nullable=True)
    parroquia = db.Column(db.String(100), nullable=True)
    direccion = db.Column(db.String(255), nullable=True)
    
    # Clave foránea para el rol (apuntando a la tabla 'roles')
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    
    # Relación con el modelo Role
    role_obj = db.relationship('Role', backref=db.backref('users', lazy=True))

    # Propiedad para acceder al nombre del rol directamente
    @property
    def role(self):
        return self.role_obj.name if self.role_obj else None

    def set_password(self, password):
        """Hashea y establece la contraseña del usuario."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica si la contraseña proporcionada coincide con el hash almacenado."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.nombres} {self.apellidos} ({self.role})>'
    
    def get_id(self):
        """Método requerido por Flask-Login para obtener el ID del usuario."""
        return str(self.id)

    @classmethod
    def get_paginated_users(cls, page, per_page, search_query=None):
        """Obtiene usuarios paginados con opción de búsqueda."""
        query = cls.query.join(Role) # Unir con la tabla Role para poder buscar por nombre de rol
        if search_query:
            search_pattern = f'%{search_query}%'
            query = query.filter(
                or_(
                    cls.cedula.ilike(search_pattern),
                    cls.nombres.ilike(search_pattern),
                    cls.apellidos.ilike(search_pattern),
                    cls.email.ilike(search_pattern),
                    cls.telefono.ilike(search_pattern),
                    cls.ciudad.ilike(search_pattern),
                    cls.parroquia.ilike(search_pattern),
                    cls.direccion.ilike(search_pattern),
                    Role.name.ilike(search_pattern) # Buscar también por nombre de rol
                )
            )
        return query.order_by(cls.apellidos.asc(), cls.nombres.asc()).paginate(page=page, per_page=per_page, error_out=False)


# Modelo para Doctores
class Doctor(db.Model):
    __tablename__ = 'doctors' # Nombre de la tabla explícito

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False) # Clave foránea al ID del usuario
    specialty = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    
    # Relación con el modelo User. Permite acceder a los datos de usuario del doctor.
    # 'uselist=False' porque un User solo puede ser un Doctor (o no serlo).
    user = db.relationship('User', backref=db.backref('doctor_info', uselist=False)) 
    
    # Relación con las citas que este doctor tiene asignadas
    # CAMBIO AQUÍ: Usar back_populates en lugar de backref
    appointments = db.relationship('Appointment', back_populates='doctor_obj', lazy=True)

    def __repr__(self):
        return f'<Doctor {self.user.nombres} {self.user.apellidos} - {self.specialty}>'

    @classmethod
    def get_paginated_doctors(cls, page, per_page, search_query=None):
        """Obtiene doctores paginados con opción de búsqueda."""
        # Unir explícitamente con la tabla User para evitar ambigüedades
        query = cls.query.join(User, cls.user_id == User.id)
        if search_query:
            search_pattern = f'%{search_query}%'
            query = query.filter(
                or_(
                    User.cedula.ilike(search_pattern),
                    User.nombres.ilike(search_pattern),
                    User.apellidos.ilike(search_pattern),
                    cls.specialty.ilike(search_pattern),
                    cls.license_number.ilike(search_pattern)
                )
            )
        # Ordenar por apellidos y luego nombres del usuario asociado al doctor
        return query.order_by(User.apellidos.asc(), User.nombres.asc()).paginate(page=page, per_page=per_page, error_out=False)


# Modelo para Citas Médicas
class Appointment(db.Model):
    __tablename__ = 'appointments' # Nombre de la tabla explícito

    id = db.Column(db.Integer, primary_key=True)
    
    # Clave foránea al ID del paciente (modelo User)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Clave foránea al ID del doctor (modelo Doctor)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    
    reason = db.Column(db.Text, nullable=False)
    
    status = db.Column(db.String(50), default='Pendiente', nullable=False) # Ej: Pendiente, Confirmada, Completada, Cancelada
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones:
    # `patient` para acceder a los datos del usuario paciente (modelo User)
    patient = db.relationship('User', foreign_keys=[patient_id], backref=db.backref('appointments_as_patient', lazy=True))
    # `doctor_obj` para acceder a los datos del doctor (modelo Doctor)
    # CAMBIO AQUÍ: backref ahora apunta a 'appointments_as_doctor' en Doctor
    doctor_obj = db.relationship('Doctor', foreign_keys=[doctor_id], backref=db.backref('appointments_as_doctor', lazy=True))


    def __repr__(self):
        return f'<Appointment {self.id} - {self.patient.nombres} {self.patient.apellidos} con Dr. {self.doctor_obj.user.apellidos}>'

    @classmethod
    def get_paginated_appointments(cls, page, per_page, search_query=None, user_role=None, user_id=None):
        """Obtiene citas paginadas con filtros de búsqueda y por rol de usuario."""
        
        # Realizar los joins explícitamente para evitar ambigüedades de 'users.id'
        # Unir Appointment con Patient (User)
        query = cls.query.join(User, cls.patient_id == User.id)
        # Unir Appointment con Doctor
        query = query.join(Doctor, cls.doctor_id == Doctor.id)
        # Unir Doctor con su User asociado (para acceder a nombres del doctor en la búsqueda)
        # Usamos un alias para la tabla User del doctor para evitar conflictos con la tabla User del paciente
        DoctorUser = db.aliased(User) # Creamos un alias para la tabla User cuando se usa para el Doctor
        query = query.join(DoctorUser, Doctor.user_id == DoctorUser.id)

        if search_query:
            search_pattern = f'%{search_query}%'
            query = query.filter(
                or_(
                    User.nombres.ilike(search_pattern), # Nombre del paciente
                    User.apellidos.ilike(search_pattern), # Apellido del paciente
                    User.cedula.ilike(search_pattern), # Cédula del paciente
                    DoctorUser.nombres.ilike(search_pattern), # Nombre del doctor (usando el alias)
                    DoctorUser.apellidos.ilike(search_pattern), # Apellido del doctor (usando el alias)
                    Doctor.specialty.ilike(search_pattern), # Especialidad del doctor
                    cls.reason.ilike(search_pattern), # Motivo de la cita
                    cls.status.ilike(search_pattern) # Estado de la cita
                )
            )

        # Filtrar por rol de usuario
        if user_role == 'patient':
            query = query.filter(cls.patient_id == user_id)
        elif user_role == 'doctor':
            # Necesitamos encontrar el ID del doctor en la tabla 'doctors' basado en el user_id
            doctor_record = Doctor.query.filter_by(user_id=user_id).first()
            if doctor_record:
                query = query.filter(cls.doctor_id == doctor_record.id)
            else:
                # Si el user_id no corresponde a un doctor registrado, no se encuentran citas.
                # Devolver una paginación vacía en este caso.
                return cls.query.filter(False).paginate(page=page, per_page=per_page, error_out=False)

        # Ordenar los resultados por fecha y hora ascendente
        query = query.order_by(cls.date.asc(), cls.time.asc())

        return query.paginate(page=page, per_page=per_page, error_out=False)
