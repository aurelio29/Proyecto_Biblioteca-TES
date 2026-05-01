import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename

# ==========================================================
# 1. CONFIGURACIÓN INICIAL
# ==========================================================
app = Flask(__name__)
app.secret_key = 'mi_llave_secreta_muy_segura' 
CORS(app)
api = Api(app)

# --- Carpetas de Almacenamiento ---
# Se crean las carpetas para libros y fotos de perfil si no existen
UPLOAD_FOLDER = 'static/uploads'
PROFILE_PICS_FOLDER = 'static/profile_pics'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROFILE_PICS_FOLDER'] = PROFILE_PICS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Límite de 16MB

for folder in [UPLOAD_FOLDER, PROFILE_PICS_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Configuración de Correo (Flask-Mail) ---
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='mazinkayser12@gmail.com', 
    MAIL_PASSWORD='bljslhjuvpwzxbzd', 
    MAIL_DEFAULT_SENDER='mazinkayser12@gmail.com'
)
mail = Mail(app)

# --- Base de Datos (SQLite) ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'BaseBiblioteca.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ==========================================================
# 2. MODELOS DE DATOS
# ==========================================================
class LibroModel(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    autor = db.Column(db.String(100), nullable=False)
    genero = db.Column(db.String(50))
    anio = db.Column(db.Integer)
    ruta_archivo = db.Column(db.String(255))
    publicado = db.Column(db.Integer, default=0) # 0: Borrador, 1: Público
    propietario_id = db.Column(db.Integer)

    def json(self):
        return {
            'id': self.id, 'titulo': self.titulo, 'autor': self.autor, 
            'genero': self.genero, 'anio': self.anio,
            'publicado': self.publicado, 'ruta': self.ruta_archivo
        }

class UsuarioModel(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    edad = db.Column(db.Integer)
    cedula = db.Column(db.String(20), unique=True, nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    id_usuario = db.Column(db.String(50), unique=True, nullable=False)
    contrasena = db.Column(db.String(100), nullable=False)
    rol = db.Column(db.String(20), default='usuario') # admin, docente, usuario
    foto = db.Column(db.String(255), default=None)

class FavoritoModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario_model.id'), nullable=False)
    libro_id = db.Column(db.Integer, db.ForeignKey('libro_model.id'), nullable=False)

# ==========================================================
# 3. RECURSOS API (Flask-Restful)
# ==========================================================
class BookList(Resource):
    def get(self):
        libros = LibroModel.query.filter_by(publicado=1).all()
        return [l.json() for l in libros]

class UsuariosListResource(Resource):
    def get(self):
        usuarios = UsuarioModel.query.all()
        return [{
            'id': u.id, 'nombres': u.nombres, 'apellidos': u.apellidos,
            'cedula': u.cedula, 'rol': u.rol, 'id_usuario': u.id_usuario, 'correo': u.correo
        } for u in usuarios]

class UsuarioResource(Resource):
    def get(self, id):
        user = UsuarioModel.query.get(id)
        return {'id': user.id, 'nombres': user.nombres, 'apellidos': user.apellidos, 
                'cedula': user.cedula, 'correo': user.correo, 'rol': user.rol, 
                'id_usuario': user.id_usuario, 'edad': user.edad} if user else ({'mensaje': 'No encontrado'}, 404)

api.add_resource(BookList, '/api/books')
api.add_resource(UsuariosListResource, '/api/admin/usuarios')
api.add_resource(UsuarioResource, '/api/admin/usuarios/<int:id>')

# ==========================================================
# 4. RUTAS DE VISTAS (Templates)
# ==========================================================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, c = request.form.get('usuario'), request.form.get('clave')
        # Login para Administrador Maestro
        if u == 'admin' and c == '1234':
            session.update({'usuario_id': 0, 'nombre': "Administrador", 'rol': 'admin'})
            return redirect(url_for('dashboard_vista'))
        
        user = UsuarioModel.query.filter_by(id_usuario=u, contrasena=c).first()
        if user:
            session.update({'usuario_id': user.id, 'nombre': f"{user.nombres} {user.apellidos}", 'rol': user.rol})
            return redirect(url_for('dashboard_vista'))
        return render_template('login.html', error="Credenciales incorrectas")
    return render_template('login.html')

@app.route('/api/recuperar', methods=['POST'])
def recuperar_credenciales():
    try:
        datos = request.get_json()
        correo = datos.get('correo')
        
        user = UsuarioModel.query.filter_by(correo=correo).first()
        
        if user:
            msg = Message('Recuperación de Credenciales - Biblioteca TES',
                          recipients=[correo])
            msg.body = f"Hola {user.nombres},\n\nTus credenciales son:\nUsuario: {user.id_usuario}\nClave: {user.contrasena}"
            
            # El error 500 suele ocurrir aquí
            mail.send(msg) 
            
            return jsonify({'mensaje': 'Credenciales enviadas correctamente.'}), 200
        
        return jsonify({'mensaje': 'El correo no está registrado.'}), 404

    except Exception as e:
        # Esto imprimirá el error real en tu terminal para que sepas qué falla
        print(f"Error detectado: {e}") 
        return jsonify({'mensaje': f'Error interno en el servidor de correo: {str(e)}'}), 500
    
@app.route('/dashboard')
def dashboard_vista():
    if 'usuario_id' not in session: return redirect(url_for('login'))
    rol = session.get('rol')
    datos = {'usuario_id': session['usuario_id'], 'nombre': session['nombre']}
    # Redirección según el rol del usuario
    if rol == 'admin': return render_template('index_admin.html', **datos)
    if rol == 'docente': return render_template('index_docente.html', **datos)
    return render_template('index_estudiante.html', **datos)

@app.route('/perfil/<int:id>')
def ver_perfil(id):
    if 'usuario_id' not in session: return redirect(url_for('login'))
    usuario = UsuarioModel.query.get(id)
    return render_template('perfil.html', user=usuario)

@app.route('/gestion_usuarios')
def vista_gestion_usuarios():
    if session.get('rol') != 'admin': return redirect(url_for('login'))
    return render_template('gestion_usuarios.html', nombre=session['nombre'])

@app.route('/libreria')
def vista_libreria():
    if 'usuario_id' not in session: return redirect(url_for('login'))
    return render_template('libreria.html', usuario_id=session['usuario_id'], nombre=session['nombre'], rol=session['rol'])

@app.route('/mislibros')
def vista_mis_libros():
    if 'usuario_id' not in session: return redirect(url_for('login'))
    return render_template('mislibros.html', usuario_id=session['usuario_id'], nombre=session['nombre'], rol=session['rol'])

@app.route('/visor/<int:id>')
def vista_visor(id):
    if 'usuario_id' not in session: 
        return redirect(url_for('login'))
    
    libro = LibroModel.query.get(id)
    if libro:
        # Renderizamos el visor y le pasamos los datos del libro
        return render_template('visor.html', id_libro=id, titulo=libro.titulo)
    return "Libro no encontrado", 404

# ==========================================================
# 5. ENDPOINTS DE ACCIÓN (Lógica)
# ==========================================================
@app.route('/api/perfil/actualizar/<int:id>', methods=['POST'])
def actualizar_perfil(id):
    if session.get('usuario_id') != id: return jsonify({'error': 'No autorizado'}), 403
    usuario = UsuarioModel.query.get(id)
    if usuario:
        # Actualización de datos personales (ID_Usuario no se edita)
        usuario.nombres = request.form.get('nombres')
        usuario.apellidos = request.form.get('apellidos')
        usuario.correo = request.form.get('correo')
        usuario.edad = request.form.get('edad')
        
        # Procesamiento de foto de perfil
        if 'foto' in request.files:
            file = request.files['foto']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"avatar_{id}_{file.filename}")
                file.save(os.path.join(app.config['PROFILE_PICS_FOLDER'], filename))
                usuario.foto = filename
        
        db.session.commit()
        session['nombre'] = f"{usuario.nombres} {usuario.apellidos}"
        return redirect(url_for('ver_perfil', id=id))
    return "Error", 404

@app.route('/api/subir_libro', methods=['POST'])
def subir_libro():
    if 'archivo' not in request.files: return jsonify({'mensaje': 'Sin archivo'}), 400
    file = request.files['archivo']
    user_id_actual = session.get('usuario_id') 

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        nombre_final = f"user_{user_id_actual}_{filename}" 
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_final))
        
        nuevo = LibroModel(
            titulo=filename, autor=session.get('nombre'),
            genero="Borrador", anio=2026, ruta_archivo=nombre_final,
            publicado=0, propietario_id=user_id_actual
        )
        db.session.add(nuevo)
        db.session.commit()
        return jsonify({'mensaje': 'Subido'}), 201
    return jsonify({'mensaje': 'Error en formato'}), 400

@app.route('/api/mis_libros/<int:user_id>')
def api_get_mis_libros(user_id):
    libros = LibroModel.query.filter_by(propietario_id=user_id).all()
    return jsonify([l.json() for l in libros])

@app.route('/api/ver_libro/<int:id>')
def ver_libro_api(id):
    libro = LibroModel.query.get(id)
    if libro:
        # as_attachment=False es la clave para que se abra en el navegador
        return send_from_directory(
            app.config['UPLOAD_FOLDER'], 
            libro.ruta_archivo, 
            as_attachment=False 
        )
    return "Archivo no encontrado", 404

@app.route('/api/publicar/<int:id>', methods=['PUT'])
def publicar_libro(id):
    libro = LibroModel.query.get(id)
    if libro:
        libro.publicado = 1
        db.session.commit()
        return jsonify({'mensaje': 'Publicado'})
    return "Error", 404

@app.route('/api/deshabilitar/<int:id>', methods=['PUT'])
def deshabilitar_libro(id):
    libro = LibroModel.query.get(id)
    if libro:
        libro.publicado = 0
        db.session.commit()
        return jsonify({'mensaje': 'Deshabilitado'})
    return "Error", 404

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/favoritos')
def vista_favoritos():
    if 'usuario_id' not in session: return redirect(url_for('login'))
    return render_template('favoritos.html', 
                           usuario_id=session['usuario_id'], 
                           nombre=session['nombre'], 
                           rol=session['rol'])

@app.route('/api/favoritos/<int:user_id>', methods=['GET'])
def obtener_favoritos(user_id):
    # Consulta que une Favoritos con Libros para traer la información completa
    favs = db.session.query(LibroModel).join(FavoritoModel).filter(FavoritoModel.usuario_id == user_id).all()
    return jsonify([l.json() for l in favs])

@app.route('/api/favoritos/agregar', methods=['POST'])
def agregar_favorito():
    datos = request.get_json()
    uid = datos.get('usuario_id')
    lid = datos.get('libro_id')
    
    # Verificar si ya es favorito para no duplicar
    existe = FavoritoModel.query.filter_by(usuario_id=uid, libro_id=lid).first()
    if not existe:
        nuevo_fav = FavoritoModel(usuario_id=uid, libro_id=lid)
        db.session.add(nuevo_fav)
        db.session.commit()
        return jsonify({'mensaje': 'Añadido a favoritos'}), 201
    return jsonify({'mensaje': 'Ya está en favoritos'}), 200

@app.route('/api/favoritos/eliminar', methods=['DELETE'])
def eliminar_favorito():
    datos = request.get_json()
    uid = datos.get('usuario_id')
    lid = datos.get('libro_id')
    
    fav = FavoritoModel.query.filter_by(usuario_id=uid, libro_id=lid).first()
    if fav:
        db.session.delete(fav)
        db.session.commit()
        return jsonify({'mensaje': 'Eliminado de favoritos'})
    return jsonify({'mensaje': 'No encontrado'}), 404

# ==========================================================
# 6. INICIO DE APLICACIÓN
# ==========================================================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Creación automática del administrador maestro si no existe
        if not UsuarioModel.query.get(0):
            admin = UsuarioModel(id=0, nombres='Administrador', apellidos='Sistema', cedula='0000000000', 
                                 correo='admin@biblioteca.tes', id_usuario='admin', contrasena='1234', rol='admin', edad=30)
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)