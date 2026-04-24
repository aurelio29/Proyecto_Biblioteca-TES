from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from flask import send_from_directory
import os

# 1. CONFIGURACIÓN INICIAL
app = Flask(__name__)
app.secret_key = 'mi_llave_secreta_muy_segura' 
CORS(app)
api = Api(app)

# 2. CONFIGURACIÓN DE ARCHIVOS
UPLOAD_FOLDER = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Máximo 16MB
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 3. CONFIGURACIÓN DE CORREO
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'mazinkayser12@gmail.com' 
app.config['MAIL_PASSWORD'] = 'mjozovaqotayvbkd' 
app.config['MAIL_DEFAULT_SENDER'] = 'mazinkayser12@gmail.com'
mail = Mail(app)

# 4. CONFIGURACIÓN DE BASE DE DATOS
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'BaseBiblioteca.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 5. MODELO DE LIBRO ACTUALIZADO
class LibroModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    autor = db.Column(db.String(100), nullable=False)
    genero = db.Column(db.String(50))
    anio = db.Column(db.Integer)
    ruta_archivo = db.Column(db.String(255))
    publicado = db.Column(db.Integer, default=0) # 0: Privado, 1: Público
    propietario_id = db.Column(db.Integer)

    # El método JSON ahora incluye el estado de publicación
    def json(self):
        return {
            'id': self.id, 
            'titulo': self.titulo, 
            'autor': self.autor, 
            'genero': self.genero, 
            'anio': self.anio,
            'publicado': self.publicado, 
            'ruta': self.ruta_archivo
        }

class UsuarioModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    edad = db.Column(db.Integer)
    cedula = db.Column(db.String(20), unique=True, nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    id_usuario = db.Column(db.String(50), unique=True, nullable=False)
    contrasena = db.Column(db.String(100), nullable=False)

# 6. RECURSOS API (Librería General)
class BookList(Resource):
    def get(self):
        # CAMBIO CLAVE: Solo enviamos a la librería los libros con publicado = 1
        libros = LibroModel.query.filter_by(publicado=1).all()
        return [l.json() for l in libros]

class Book(Resource):
    def get(self, id):
        libro = LibroModel.query.get(id)
        return libro.json() if libro else ({'mensaje': 'Libro no encontrado'}, 404)

api.add_resource(BookList, '/api/books')
api.add_resource(Book, '/api/books/<int:id>')

# 7. RUTAS DE VISTA
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('usuario')
        c = request.form.get('clave')
        if u == 'admin' and c == '1234':
            session['usuario_id'] = 0
            session['nombre'] = "Administrador"
            return redirect(url_for('dashboard_vista'))
        user = UsuarioModel.query.filter_by(id_usuario=u, contrasena=c).first()
        if user:
            session['usuario_id'] = user.id
            session['nombre'] = f"{user.nombres} {user.apellidos}"
            return redirect(url_for('dashboard_vista'))
        return render_template('login.html', error="Usuario o clave incorrectos")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard_vista():
    if 'usuario_id' not in session: return redirect(url_for('login'))
    return render_template('index.html', usuario_id=session['usuario_id'], nombre=session['nombre'])

@app.route('/libreria')
def vista_libreria():
    if 'usuario_id' not in session: return redirect(url_for('login'))
    return render_template('libreria.html', usuario_id=session['usuario_id'], nombre=session['nombre'])

@app.route('/mislibros')
def vista_mis_libros():
    if 'usuario_id' not in session: return redirect(url_for('login'))
    return render_template('mislibros.html', usuario_id=session['usuario_id'], nombre=session['nombre'])

# 8. ENDPOINTS DE ACCIÓN (Usuarios, Archivos y Publicación)
@app.route('/api/usuarios', methods=['POST'])
def registrar_usuario():
    datos = request.get_json()
    nuevo = UsuarioModel(
        nombres=datos['nombres'], apellidos=datos['apellidos'],
        edad=datos['edad'], cedula=datos['cedula'],
        correo=datos['correo'], id_usuario=datos['id_usuario'],
        contrasena=datos['contrasena']
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({'mensaje': 'Usuario creado exitosamente'}), 201

@app.route('/api/recuperar', methods=['POST'])
def recuperar_credenciales():
    datos = request.get_json()
    correo = datos.get('correo')
    user = UsuarioModel.query.filter_by(correo=correo).first()
    if user:
        msg = Message('Tus Credenciales - Biblioteca TES', recipients=[correo])
        msg.body = f"Hola {user.nombres}, tu usuario es: {user.id_usuario} y tu clave: {user.contrasena}"
        mail.send(msg)
        return jsonify({'mensaje': 'Credenciales enviadas al correo.'})
    return jsonify({'mensaje': 'Correo no encontrado.'}), 404

@app.route('/api/mis_libros/<int:user_id>')
def api_get_mis_libros(user_id):
    # En Mis Libros el usuario ve todos sus libros (privados y públicos)
    libros = LibroModel.query.filter_by(propietario_id=user_id).all()
    return jsonify([l.json() for l in libros])

@app.route('/api/subir_libro', methods=['POST'])
def subir_libro():
    if 'archivo' not in request.files: return jsonify({'mensaje': 'No hay archivo'}), 400
    file = request.files['archivo']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        nombre_final = f"user_{session.get('usuario_id', 0)}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_final))
        
        nuevo = LibroModel(
            titulo=filename, autor=session.get('nombre', 'Anónimo'),
            genero="Borrador", anio=2026, ruta_archivo=nombre_final,
            publicado=0, propietario_id=session.get('usuario_id', 0)
        )
        db.session.add(nuevo)
        db.session.commit()
        return jsonify({'mensaje': 'Archivo subido correctamente'}), 201
    return jsonify({'mensaje': 'Formato inválido'}), 400

@app.route('/api/publicar/<int:id>', methods=['PUT'])
def publicar_libro_api(id):
    libro = LibroModel.query.get(id)
    if libro:
        libro.publicado = 1  # Cambiamos estado a público
        db.session.commit()
        print(f"--- LIBRO PUBLICADO: {libro.titulo} ---")
        return jsonify({'mensaje': 'El libro ahora es público'})
    return jsonify({'mensaje': 'Libro no encontrado'}), 404

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/descargar/<int:id>')
def descargar_archivo(id):
    libro = LibroModel.query.get(id)
    if libro and libro.ruta_archivo:
        # Buscamos el archivo en la carpeta static/uploads
        return send_from_directory(
            app.config['UPLOAD_FOLDER'], 
            libro.ruta_archivo, 
            as_attachment=True # Esto obliga al navegador a descargarlo en lugar de abrirlo
        )
    return jsonify({'mensaje': 'Archivo no encontrado'}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)