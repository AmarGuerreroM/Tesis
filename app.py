# app.py

from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
# Importa todos los modelos, incluyendo Role
from models import db, User, Doctor, Appointment, Role 
from config import Config
from functools import wraps
import datetime # Necesario para manejar fechas y horas

app = Flask(__name__)
app.config.from_object(Config)

# Inicializa la DB con la app
db.init_app(app) 

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # La vista a la que redirigir si el usuario no está logueado

@login_manager.user_loader
def load_user(user_id):
    """Callback de Flask-Login para cargar un usuario dado su ID."""
    return User.query.get(int(user_id))

# Decoradores de roles para control de acceso
def role_required(role_name):
    """
    Decorador para restringir el acceso a rutas basadas en el rol del usuario.
    Los administradores siempre tienen acceso.
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Por favor, inicia sesión para acceder a esta página.', 'warning')
                return redirect(url_for('login', next=request.url))
            
            # Si el usuario es administrador, siempre tiene acceso
            if current_user.role == 'admin':
                return fn(*args, **kwargs)
            
            # Si no es administrador, verifica si tiene el rol requerido
            if current_user.role != role_name:
                flash('No tienes permiso para acceder a esta página.', 'danger')
                return redirect(url_for('dashboard')) # Redirige al dashboard por defecto
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

def admin_required(f):
    return role_required('admin')(f)

def patient_required(f):
    return role_required('patient')(f)

def doctor_required(f):
    return role_required('doctor')(f)

def secretary_required(f):
    return role_required('secretary')(f)


# --- RUTAS DE AUTENTICACIÓN ---
@app.route('/')
def index():
    """Redirige la ruta raíz al login."""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Maneja el inicio de sesión de usuarios."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        cedula = request.form.get('cedula')
        password = request.form.get('password')
        user = User.query.filter_by(cedula=cedula).first()

        if user and user.check_password(password): # Usa el método check_password del modelo User
            login_user(user)
            flash(f'¡Bienvenido de nuevo, {user.nombres} {user.apellidos}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Cédula o contraseña incorrecta.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Maneja el registro de nuevos usuarios (pacientes por defecto)."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        cedula = request.form.get('cedula')
        nombres = request.form.get('nombres')
        apellidos = request.form.get('apellidos')
        email = request.form.get('email')
        telefono = request.form.get('telefono')
        ciudad = request.form.get('ciudad')
        parroquia = request.form.get('parroquia')
        direccion = request.form.get('direccion')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('register.html')

        existing_user_cedula = User.query.filter_by(cedula=cedula).first()
        if existing_user_cedula:
            flash('Ya existe un usuario con esta cédula.', 'danger')
            return render_template('register.html')

        existing_user_email = User.query.filter_by(email=email).first()
        if existing_user_email:
            flash('Ya existe un usuario con este correo electrónico.', 'danger')
            return render_template('register.html')

        # Obtener el objeto Role para 'patient'
        patient_role = Role.query.filter_by(name='patient').first()
        if not patient_role:
            flash('Error interno: Rol de paciente no encontrado. Contacte al administrador.', 'danger')
            return render_template('register.html')

        new_user = User(
            cedula=cedula, nombres=nombres, apellidos=apellidos, email=email, 
            telefono=telefono, ciudad=ciudad, parroquia=parroquia, direccion=direccion, 
            role_obj=patient_role # Asigna el objeto Role directamente
        )
        new_user.set_password(password) # Hashea y establece la contraseña
        db.session.add(new_user)
        db.session.commit()
        flash('Registro exitoso. ¡Ahora puedes iniciar sesión!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Cierra la sesión del usuario actual."""
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('login'))

# --- RUTA DE DASHBOARD ---
@app.route('/dashboard')
@login_required
def dashboard():
    """Muestra el dashboard principal del usuario logueado."""
    return render_template('dashboard.html')

# --- RUTAS DE GESTIÓN DE USUARIOS (ADMIN) ---
@app.route('/admin/users')
@admin_required
def list_users():
    """Muestra el listado de usuarios para el administrador."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_query = request.args.get('search', '', type=str)

    # Lógica para mostrar/ocultar columnas (se mantiene como antes)
    show_id = 'id' in request.args.getlist('columns') or not request.args.getlist('columns')
    show_cedula = 'cedula' in request.args.getlist('columns') or not request.args.getlist('columns')
    show_nombres = 'nombres' in request.args.getlist('columns') or not request.args.getlist('columns')
    show_apellidos = 'apellidos' in request.args.getlist('columns') or not request.args.getlist('columns')
    show_email = 'email' in request.args.getlist('columns') or not request.args.getlist('columns')
    show_telefono = 'telefono' in request.args.getlist('columns') or not request.args.getlist('columns')
    show_ciudad = 'ciudad' in request.args.getlist('columns') or not request.args.getlist('columns')
    show_parroquia = 'parroquia' in request.args.getlist('columns') or not request.args.getlist('columns')
    show_direccion = 'direccion' in request.args.getlist('columns') or not request.args.getlist('columns')
    show_role = 'role' in request.args.getlist('columns') or not request.args.getlist('columns')

    users_pagination = User.get_paginated_users(page, per_page, search_query)

    return render_template('admin/users/list.html', 
                           users_pagination=users_pagination,
                           search_query=search_query,
                           per_page=per_page,
                           show_id=show_id,
                           show_cedula=show_cedula,
                           show_nombres=show_nombres,
                           show_apellidos=show_apellidos,
                           show_email=show_email,
                           show_telefono=show_telefono,
                           show_ciudad=show_ciudad,
                           show_parroquia=show_parroquia,
                           show_direccion=show_direccion,
                           show_role=show_role)

@app.route('/admin/users/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    """Permite al administrador añadir nuevos usuarios (pacientes, doctores, secretarias)."""
    if request.method == 'POST':
        cedula = request.form.get('cedula')
        nombres = request.form.get('nombres')
        apellidos = request.form.get('apellidos')
        email = request.form.get('email')
        telefono = request.form.get('telefono')
        ciudad = request.form.get('ciudad')
        parroquia = request.form.get('parroquia')
        direccion = request.form.get('direccion')
        password = request.form.get('password')
        role_name = request.form.get('role') # Obtiene el nombre del rol del formulario
        specialty = request.form.get('specialty')
        license_number = request.form.get('license_number')

        # Validaciones de existencia (cédula y email)
        if User.query.filter_by(cedula=cedula).first():
            flash('Ya existe un usuario con esta cédula.', 'danger')
            return render_template('admin/users/add_edit.html', user=None, is_edit=False, roles=Role.query.all())
        if User.query.filter_by(email=email).first():
            flash('Ya existe un usuario con este correo electrónico.', 'danger')
            return render_template('admin/users/add_edit.html', user=None, is_edit=False, roles=Role.query.all())

        # Obtener el objeto Role basado en el nombre seleccionado
        selected_role = Role.query.filter_by(name=role_name).first()
        if not selected_role:
            flash(f'Error: Rol "{role_name}" no válido.', 'danger')
            return render_template('admin/users/add_edit.html', user=None, is_edit=False, roles=Role.query.all())

        new_user = User(
            cedula=cedula, nombres=nombres, apellidos=apellidos, email=email, 
            telefono=telefono, ciudad=ciudad, parroquia=parroquia, direccion=direccion, 
            role_obj=selected_role # Asigna el objeto Role
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit() # Commit para que new_user.id esté disponible

        if role_name == 'doctor':
            if not specialty or not license_number:
                flash('Especialidad y número de licencia son requeridos para doctores.', 'danger')
                db.session.delete(new_user) # Eliminar el usuario recién creado si faltan datos del doctor
                db.session.commit()
                return render_template('admin/users/add_edit.html', user=None, is_edit=False, roles=Role.query.all())
            
            # Verificar si ya existe un doctor con ese número de licencia
            existing_doctor_license = Doctor.query.filter_by(license_number=license_number).first()
            if existing_doctor_license:
                flash('Ya existe un doctor con este número de licencia.', 'danger')
                db.session.delete(new_user) # Eliminar el usuario recién creado si la licencia ya existe
                db.session.commit()
                return render_template('admin/users/add_edit.html', user=None, is_edit=False, roles=Role.query.all())

            new_doctor = Doctor(user_id=new_user.id, specialty=specialty, license_number=license_number)
            db.session.add(new_doctor)
            db.session.commit()

        flash('Usuario agregado exitosamente.', 'success')
        return redirect(url_for('list_users'))
    
    # Para GET request, pasar todos los roles disponibles al template
    roles = Role.query.all()
    return render_template('admin/users/add_edit.html', user=None, is_edit=False, roles=roles)

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Permite al administrador editar usuarios existentes."""
    user_to_edit = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user_to_edit.cedula = request.form.get('cedula')
        user_to_edit.nombres = request.form.get('nombres')
        user_to_edit.apellidos = request.form.get('apellidos')
        user_to_edit.email = request.form.get('email')
        user_to_edit.telefono = request.form.get('telefono')
        user_to_edit.ciudad = request.form.get('ciudad')
        user_to_edit.parroquia = request.form.get('parroquia')
        user_to_edit.direccion = request.form.get('direccion')
        new_password = request.form.get('password')
        role_name = request.form.get('role') # Obtiene el nombre del rol del formulario
        specialty = request.form.get('specialty')
        license_number = request.form.get('license_number')

        # Validar cédula y email únicos (excluyendo al usuario actual)
        if User.query.filter(User.cedula == user_to_edit.cedula, User.id != user_id).first():
            flash('Ya existe un usuario con esta cédula.', 'danger')
            return render_template('admin/users/add_edit.html', user=user_to_edit, is_edit=True, roles=Role.query.all())
        if User.query.filter(User.email == user_to_edit.email, User.id != user_id).first():
            flash('Ya existe un usuario con este correo electrónico.', 'danger')
            return render_template('admin/users/add_edit.html', user=user_to_edit, is_edit=True, roles=Role.query.all())

        if new_password:
            user_to_edit.set_password(new_password)
        
        # Obtener el objeto Role basado en el nombre seleccionado y asignarlo
        selected_role = Role.query.filter_by(name=role_name).first()
        if not selected_role:
            flash(f'Error: Rol "{role_name}" no válido.', 'danger')
            return render_template('admin/users/add_edit.html', user=user_to_edit, is_edit=True, roles=Role.query.all())
        user_to_edit.role_obj = selected_role # Asigna el objeto Role

        # Manejo del rol de doctor
        if role_name == 'doctor':
            if not user_to_edit.doctor_info: # Si no era doctor, crear un registro de doctor
                if not specialty or not license_number:
                    flash('Especialidad y número de licencia son requeridos para doctores.', 'danger')
                    return render_template('admin/users/add_edit.html', user=user_to_edit, is_edit=True, roles=Role.query.all())
                
                # Verificar si ya existe un doctor con ese número de licencia (excluyendo al propio user_to_edit si ya era doctor)
                existing_doctor_license = Doctor.query.filter(Doctor.license_number == license_number, Doctor.user_id != user_id).first()
                if existing_doctor_license:
                    flash('Ya existe un doctor con este número de licencia.', 'danger')
                    return render_template('admin/users/add_edit.html', user=user_to_edit, is_edit=True, roles=Role.query.all())

                new_doctor = Doctor(user_id=user_to_edit.id, specialty=specialty, license_number=license_number)
                db.session.add(new_doctor)
            else: # Si ya era doctor, actualizar sus datos
                user_to_edit.doctor_info.specialty = specialty
                user_to_edit.doctor_info.license_number = license_number
                # Validar licencia única para doctores que ya existen (excluyendo al propio)
                existing_doctor_license = Doctor.query.filter(Doctor.license_number == license_number, Doctor.user_id != user_id).first()
                if existing_doctor_license:
                    flash('Ya existe un doctor con este número de licencia.', 'danger')
                    return render_template('admin/users/add_edit.html', user=user_to_edit, is_edit=True, roles=Role.query.all())

        elif user_to_edit.doctor_info: # Si el rol cambia de doctor a otro, eliminar el registro de doctor
            db.session.delete(user_to_edit.doctor_info)
        
        db.session.commit()
        flash('Usuario actualizado exitosamente.', 'success')
        return redirect(url_for('list_users'))

    # Para GET request, pasar todos los roles disponibles al template
    roles = Role.query.all()
    return render_template('admin/users/add_edit.html', user=user_to_edit, is_edit=True, roles=roles)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Permite al administrador eliminar usuarios."""
    user_to_delete = User.query.get_or_404(user_id)
    
    # Si el usuario es un doctor, primero elimina su registro de doctor
    if user_to_delete.doctor_info:
        db.session.delete(user_to_delete.doctor_info)
    
    # Eliminar citas donde es paciente
    appointments_as_patient = Appointment.query.filter_by(patient_id=user_id).all()
    for appt in appointments_as_patient:
        db.session.delete(appt)

    # Si es doctor, eliminar citas donde es el doctor asignado
    if user_to_delete.role == 'doctor' and user_to_delete.doctor_info:
        appointments_as_doctor = Appointment.query.filter_by(doctor_id=user_to_delete.doctor_info.id).all()
        for appt in appointments_as_doctor:
            db.session.delete(appt)
            
    db.session.delete(user_to_delete)
    db.session.commit()
    flash('Usuario eliminado exitosamente.', 'info')
    return redirect(url_for('list_users'))


# --- RUTAS DE GESTIÓN DE DOCTORES (ADMIN) ---
@app.route('/admin/doctors')
@admin_required
def list_doctors():
    """Muestra el listado de doctores para el administrador."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_query = request.args.get('search', '', type=str)
    
    doctors_pagination = Doctor.get_paginated_doctors(page, per_page, search_query)

    return render_template('admin/doctors/list.html', 
                           doctors_pagination=doctors_pagination,
                           search_query=search_query,
                           per_page=per_page)

# --- RUTAS DE GESTIÓN DE CITAS ---

@app.route('/appointments/request', methods=['GET', 'POST'])
@patient_required # Solo pacientes pueden solicitar citas
def request_appointment():
    """Permite a los pacientes solicitar una nueva cita."""
    # Obtener la lista de doctores para el dropdown
    doctors = Doctor.query.join(User).order_by(User.apellidos).all()

    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id', type=int)
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        reason = request.form.get('reason')

        if not doctor_id or not date_str or not time_str or not reason:
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('appointments/request.html', doctors=doctors)

        try:
            appointment_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            appointment_time = datetime.datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            flash('Formato de fecha u hora incorrecto. Use YYYY-MM-DD y HH:MM.', 'danger')
            return render_template('appointments/request.html', doctors=doctors)

        # Validaciones adicionales (ej. no agendar en el pasado)
        now = datetime.datetime.now()
        appointment_datetime = datetime.datetime.combine(appointment_date, appointment_time)

        if appointment_datetime < now:
            flash('No se puede agendar una cita en el pasado.', 'danger')
            return render_template('appointments/request.html', doctors=doctors)

        # Evitar citas duplicadas para el mismo doctor a la misma hora y fecha.
        existing_appointment = Appointment.query.filter_by(
            doctor_id=doctor_id,
            date=appointment_date,
            time=appointment_time
        ).first()

        if existing_appointment:
            flash('Ya existe una cita programada para este doctor a esa hora y fecha.', 'danger')
            return render_template('appointments/request.html', doctors=doctors)

        new_appointment = Appointment(
            patient_id=current_user.id,
            doctor_id=doctor_id,
            date=appointment_date,
            time=appointment_time,
            reason=reason,
            status='Pendiente' # Estado inicial
        )
        db.session.add(new_appointment)
        db.session.commit()
        flash('Su cita ha sido solicitada con éxito. Un administrador o secretaria la confirmará pronto.', 'success')
        return redirect(url_for('list_appointments'))

    return render_template('appointments/request.html', doctors=doctors)

@app.route('/appointments')
@login_required
def list_appointments():
    """Muestra el listado de citas según el rol del usuario."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_query = request.args.get('search', '', type=str)
    
    # Obtener citas paginadas según el rol del usuario
    if current_user.role == 'admin' or current_user.role == 'secretary':
        appointments_pagination = Appointment.get_paginated_appointments(page, per_page, search_query)
    elif current_user.role == 'patient':
        appointments_pagination = Appointment.get_paginated_appointments(page, per_page, search_query, user_role='patient', user_id=current_user.id)
    elif current_user.role == 'doctor':
        appointments_pagination = Appointment.get_paginated_appointments(page, per_page, search_query, user_role='doctor', user_id=current_user.id)
    else:
        flash('No tienes permiso para ver citas.', 'danger')
        return redirect(url_for('dashboard'))

    return render_template('appointments/list.html', 
                           appointments_pagination=appointments_pagination,
                           search_query=search_query,
                           per_page=per_page)

@app.route('/appointments/edit/<int:appointment_id>', methods=['GET', 'POST'])
@login_required # Todos los roles relevantes deberían poder editar/cancelar (con lógica de permisos)
def edit_appointment(appointment_id):
    """Permite ver detalles y editar/cancelar una cita."""
    appointment = Appointment.query.get_or_404(appointment_id)

    # Control de permisos:
    # - Admin y Secretaria pueden editar/cancelar cualquier cita
    # - Paciente solo puede ver/cancelar sus propias citas
    # - Doctor solo puede ver/confirmar/completar/cancelar sus citas
    if current_user.role == 'patient' and appointment.patient_id != current_user.id:
        flash('No tienes permiso para editar esta cita.', 'danger')
        return redirect(url_for('list_appointments'))
    
    if current_user.role == 'doctor':
        doctor_obj = Doctor.query.filter_by(user_id=current_user.id).first()
        if not doctor_obj or appointment.doctor_id != doctor_obj.id:
            flash('No tienes permiso para editar esta cita.', 'danger')
            return redirect(url_for('list_appointments'))

    # Si se intenta guardar la edición (POST request)
    if request.method == 'POST':
        # Los campos que se pueden editar dependen del rol
        if current_user.role == 'admin' or current_user.role == 'secretary':
            patient_id = request.form.get('patient_id', type=int)
            doctor_id = request.form.get('doctor_id', type=int)
            date_str = request.form.get('date')
            time_str = request.form.get('time')
            reason = request.form.get('reason')
            status = request.form.get('status')

            if not patient_id or not doctor_id or not date_str or not time_str or not reason or not status:
                flash('Todos los campos son obligatorios.', 'danger')
                doctors = Doctor.query.join(User).order_by(User.apellidos).all()
                patients = User.query.filter_by(role_obj=Role.query.filter_by(name='patient').first()).order_by(User.apellidos).all()
                return render_template('appointments/edit.html', appointment=appointment, doctors=doctors, patients=patients, now=datetime.datetime.now())

            try:
                appointment.date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                appointment.time = datetime.datetime.strptime(time_str, '%H:%M').time()
            except ValueError:
                flash('Formato de fecha u hora incorrecto. Use YYYY-MM-DD y HH:MM.', 'danger')
                doctors = Doctor.query.join(User).order_by(User.apellidos).all()
                patients = User.query.filter_by(role_obj=Role.query.filter_by(name='patient').first()).order_by(User.apellidos).all()
                return render_template('appointments/edit.html', appointment=appointment, doctors=doctors, patients=patients, now=datetime.datetime.now())
            
            # Validar que la nueva fecha/hora no choque con otra cita del mismo doctor (excluyendo la cita actual)
            existing_collision = Appointment.query.filter(
                Appointment.doctor_id == doctor_id,
                Appointment.date == appointment.date,
                Appointment.time == appointment.time,
                Appointment.id != appointment_id
            ).first()
            if existing_collision:
                flash('La nueva fecha y hora para este doctor ya están ocupadas por otra cita.', 'danger')
                doctors = Doctor.query.join(User).order_by(User.apellidos).all()
                patients = User.query.filter_by(role_obj=Role.query.filter_by(name='patient').first()).order_by(User.apellidos).all()
                return render_template('appointments/edit.html', appointment=appointment, doctors=doctors, patients=patients, now=datetime.datetime.now())

            appointment.patient_id = patient_id
            appointment.doctor_id = doctor_id
            appointment.reason = reason
            appointment.status = status
            flash('Cita actualizada exitosamente.', 'success')

        elif current_user.role == 'doctor':
            status = request.form.get('status')
            reason = request.form.get('reason') 
            if not status or not reason:
                 flash('El estado y la razón son obligatorios.', 'danger')
                 return render_template('appointments/edit.html', appointment=appointment, now=datetime.datetime.now())
            
            appointment.status = status
            appointment.reason = reason
            flash('Estado de la cita actualizado exitosamente.', 'success')

        elif current_user.role == 'patient':
            if 'cancel_action' in request.form:
                appointment.status = 'Cancelada'
                flash('Su cita ha sido cancelada.', 'info')
            else:
                flash('Solo puedes cancelar tu cita.', 'warning')
                return redirect(url_for('list_appointments'))

        db.session.commit()
        return redirect(url_for('list_appointments'))
    
    # Si es GET request, preparar datos para el formulario
    doctors = Doctor.query.join(User).order_by(User.apellidos).all()
    # Filtra los usuarios para obtener solo pacientes
    patients = User.query.filter_by(role_obj=Role.query.filter_by(name='patient').first()).order_by(User.apellidos).all()

    return render_template('appointments/edit.html', 
                           appointment=appointment, 
                           doctors=doctors, 
                           patients=patients,
                           now=datetime.datetime.now() # Pasa la fecha y hora actual para comparaciones en el template
                           )

@app.route('/appointments/delete/<int:appointment_id>', methods=['POST'])
@login_required 
def delete_appointment(appointment_id):
    """Permite eliminar o cancelar una cita según el rol."""
    appointment = Appointment.query.get_or_404(appointment_id)

    # Control de permisos:
    if current_user.role == 'patient' and appointment.patient_id != current_user.id:
        flash('No tienes permiso para eliminar esta cita.', 'danger')
        return redirect(url_for('list_appointments'))
    
    if current_user.role == 'doctor':
        doctor_obj = Doctor.query.filter_by(user_id=current_user.id).first()
        if not doctor_obj or appointment.doctor_id != doctor_obj.id:
            flash('No tienes permiso para eliminar esta cita.', 'danger')
            return redirect(url_for('list_appointments'))

    # Si es un paciente o doctor cancelando, cambia el estado a 'Cancelada'
    if current_user.role == 'patient' or current_user.role == 'doctor':
        appointment.status = 'Cancelada'
        db.session.commit()
        flash('Cita cancelada exitosamente.', 'info')
    else: # Admin o Secretaria pueden eliminarla completamente
        db.session.delete(appointment)
        db.session.commit()
        flash('Cita eliminada permanentemente.', 'info')

    return redirect(url_for('list_appointments'))


@app.route('/api/doctor_schedule/<int:doctor_id>/<string:date_str>')
@login_required 
def get_doctor_schedule(doctor_id, date_str):
    """
    API para obtener horarios disponibles de un doctor en una fecha específica.
    Utilizado por el formulario de solicitud de cita.
    """
    try:
        selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido'}), 400

    # Definir la jornada laboral del doctor (ej. 9 AM - 5 PM)
    # Esto es una simplificación; en un sistema real, tendrías un modelo de horarios de disponibilidad
    start_time = datetime.time(9, 0)
    end_time = datetime.time(17, 0)
    appointment_duration_minutes = 30 # Citas cada 30 minutos

    # Obtener citas existentes para el doctor en la fecha seleccionada
    booked_appointments = Appointment.query.filter_by(
        doctor_id=doctor_id,
        date=selected_date
    ).filter(Appointment.status.in_(['Pendiente', 'Confirmada'])).all()

    booked_times = {appt.time for appt in booked_appointments}

    available_times = []
    current_time_slot = datetime.datetime.combine(selected_date, start_time)
    end_datetime_slot = datetime.datetime.combine(selected_date, end_time)

    while current_time_slot < end_datetime_slot:
        if current_time_slot.time() not in booked_times:
            # Asegurarse de no ofrecer horarios en el pasado
            if current_time_slot > datetime.datetime.now():
                available_times.append(current_time_slot.strftime('%H:%M'))
        current_time_slot += datetime.timedelta(minutes=appointment_duration_minutes)
    
    if not available_times:
        return jsonify({'message': 'No hay horarios disponibles para este doctor en esta fecha.'}), 200

    return jsonify({'available_times': available_times}), 200


if __name__ == '__main__':
    with app.app_context():
        # Antes de crear todas las tablas, asegúrate de que los roles existan
        # Esto es crucial para que los usuarios puedan ser asignados a un rol.
        roles_to_create = ['admin', 'patient', 'doctor', 'secretary']
        for role_name in roles_to_create:
            existing_role = Role.query.filter_by(name=role_name).first()
            if not existing_role:
                new_role = Role(name=role_name)
                db.session.add(new_role)
        db.session.commit() # Guarda los roles antes de crear las tablas si es la primera vez

        db.create_all() # Asegura que todas las tablas (incluyendo users, doctors, appointments) se creen si no existen
    app.run(debug=True)