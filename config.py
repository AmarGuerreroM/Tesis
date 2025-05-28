# config.py

import os

class Config:
    # Obtiene la ruta base del directorio actual
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Configuración de la base de datos SQLite
    # SQLite guarda la base de datos en un archivo local
    # 'sqlite:///' + ruta_al_archivo
    # En este caso, el archivo 'site.db' se creará en la raíz del proyecto
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'site.db')
    
    # Desactiva el seguimiento de modificaciones de SQLAlchemy para ahorrar recursos
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Clave secreta para la seguridad de las sesiones de Flask
    # ¡IMPORTANTE!: En producción, esto debe ser una cadena aleatoria y compleja.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_clave_secreta_muy_dificil_de_adivinar_para_desarrollo'
    
    # Si SECRET_KEY no está definido como variable de entorno, usa el valor por defecto.
    # En producción, se recomienda usar variables de entorno para las claves secretas.