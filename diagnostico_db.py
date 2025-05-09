from app import create_app, db
from sqlalchemy import inspect

app = create_app()

with app.app_context():
    # Muestra la URI que se está usando
    print("🔌 URI de conexión:", app.config["SQLALCHEMY_DATABASE_URI"])

    # Muestra el motor de conexión
    print("🛠️ Motor de conexión:", db.engine)

    # Muestra las tablas registradas en SQLAlchemy
    inspector = inspect(db.engine)
    tablas = inspector.get_table_names()
    print("📋 Tablas en la base de datos:", tablas)

    # Muestra la base de datos actual
    from sqlalchemy import text
    result = db.session.execute(text("SELECT current_database();")).fetchone()

    print("Base de datos actual:", result[0])
