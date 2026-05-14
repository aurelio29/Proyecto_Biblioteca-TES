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
    MAIL_PASSWORD='', 
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
    descripcion = db.Column(db.Text, default="")
    ciudad = db.Column(db.String(100), default="")
    pais = db.Column(db.String(100), default="")
    carrera = db.Column(db.String(100), default="")
    rol = db.Column(db.String(20), default='estudiante')
    foto = db.Column(db.String(255), default=None)
    activo = db.Column(db.Boolean, default=True)

class FavoritoModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario_model.id'), nullable=False)
    libro_id = db.Column(db.Integer, db.ForeignKey('libro_model.id'), nullable=False)

class MensajeModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emisor_id = db.Column(db.Integer, nullable=False)
    receptor_id = db.Column(db.Integer, nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=db.func.current_timestamp())
    leido = db.Column(db.Boolean, default=False)

    def json(self):
        return {
            'id': self.id, 'emisor_id': self.emisor_id, 
            'receptor_id': self.receptor_id, 'contenido': self.contenido,
            'fecha': self.fecha.strftime('%Y-%m-%d %H:%M:%S')
        }

class AmistadModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario_model.id'), nullable=False)
    amigo_id = db.Column(db.Integer, db.ForeignKey('usuario_model.id'), nullable=False)
    estado = db.Column(db.String(20), default='pendiente') # pendiente, aceptada

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
            'cedula': u.cedula, 'rol': u.rol, 'id_usuario': u.id_usuario, 'correo': u.correo, 'activo': bool(u.activo),
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
            if not user.activo:
                return render_template('login.html', error="Tu cuenta ha sido inhabilitada. Contacta al administrador.")
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
            
            mail.send(msg) 
            
            return jsonify({'mensaje': 'Credenciales enviadas correctamente.'}), 200
        
        return jsonify({'mensaje': 'El correo no está registrado.'}), 404

    except Exception as e:
        print(f"Error detectado: {e}") 
        return jsonify({'mensaje': f'Error interno en el servidor de correo: {str(e)}'}), 500
    
@app.route('/dashboard')
def dashboard_vista():
    if 'usuario_id' not in session: return redirect(url_for('login'))
    rol = session.get('rol')
    datos = {'usuario_id': session['usuario_id'], 'nombre': session['nombre']}
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
        usuario.nombres = request.form.get('nombres')
        usuario.apellidos = request.form.get('apellidos')
        usuario.edad = request.form.get('edad')
        usuario.descripcion = request.form.get('descripcion')
        usuario.ciudad = request.form.get('ciudad')
        usuario.pais = request.form.get('pais')
        usuario.carrera = request.form.get('carrera')
        
        if 'foto' in request.files:
            file = request.files['foto']
            if file and allowed_file(file.filename):
                if usuario.foto:
                    old_path = os.path.join(app.config['PROFILE_PICS_FOLDER'], usuario.foto)
                    if os.path.exists(old_path):
                        os.remove(old_path)

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
        return send_from_directory(
            app.config['UPLOAD_FOLDER'], 
            libro.ruta_archivo, 
            as_attachment=False 
        )
    return "Archivo no encontrado", 404

@app.route('/api/usuarios/buscar')
def buscar_usuarios_chat():
    q = request.args.get('q', '')
    usuarios = UsuarioModel.query.filter(
        UsuarioModel.nombres.ilike(f"%{q}%"), 
        UsuarioModel.id != session.get('usuario_id')
    ).all()
    return jsonify([{'id': u.id, 'nombres': u.nombres} for u in usuarios])

@app.route('/mensajeria')
def vista_mensajeria():
    if 'usuario_id' not in session: return redirect(url_for('login'))
    return render_template('mensajeria.html', 
                           usuario_id=session['usuario_id'], 
                           nombre=session['nombre'])

@app.route('/api/mensajes/enviar', methods=['POST'])
def enviar_mensaje():
    datos = request.get_json()
    nuevo_msj = MensajeModel(
        emisor_id=session.get('usuario_id'),
        receptor_id=datos.get('receptor_id'),
        contenido=datos.get('contenido')
    )
    db.session.add(nuevo_msj)
    db.session.commit()
    return jsonify({'mensaje': 'Enviado'})

@app.route('/api/mensajes/<int:contacto_id>')
def obtener_mensajes(contacto_id):
    mi_id = session.get('usuario_id')
    mensajes = MensajeModel.query.filter(
        ((MensajeModel.emisor_id == mi_id) & (MensajeModel.receptor_id == contacto_id)) |
        ((MensajeModel.emisor_id == contacto_id) & (MensajeModel.receptor_id == mi_id))
    ).order_by(MensajeModel.fecha.asc()).all()
    return jsonify([m.json() for m in mensajes])

@app.route('/api/amistad/enviar', methods=['POST'])
def enviar_solicitud():
    datos = request.get_json()
    nueva = AmistadModel(
        usuario_id=session.get('usuario_id'),
        amigo_id=datos.get('amigo_id'),
        estado='aceptada'
    )
    db.session.add(nueva)
    db.session.commit()
    return jsonify({'mensaje': 'Solicitud enviada'})

@app.route('/api/amistad/mis-contactos')
def obtener_contactos():
    mi_id = session.get('usuario_id')
    contactos = AmistadModel.query.filter_by(usuario_id=mi_id).all()
    lista = []
    for c in contactos:
        u = UsuarioModel.query.get(c.amigo_id)
        if u:
            lista.append({'id': u.id, 'nombres': u.nombres})
    return jsonify(lista)

@app.route('/api/notificaciones/conteo')
def conteo_notificaciones():
    mi_id = session.get('usuario_id')
    if not mi_id: 
        return jsonify({'total': 0})
    mensajes_nuevos = MensajeModel.query.filter_by(receptor_id=mi_id, leido=False).count()
    
    solicitudes_nuevas = AmistadModel.query.filter_by(amigo_id=mi_id, estado='pendiente').count()
    return jsonify({
        'mensajes': mensajes_nuevos,
        'solicitudes': solicitudes_nuevas,
        'total': mensajes_nuevos + solicitudes_nuevas
    })

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
    favs = db.session.query(LibroModel).join(FavoritoModel).filter(FavoritoModel.usuario_id == user_id).all()
    return jsonify([l.json() for l in favs])

@app.route('/api/favoritos/agregar', methods=['POST'])
def agregar_favorito():
    datos = request.get_json()
    uid = datos.get('usuario_id')
    lid = datos.get('libro_id')

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
    
@app.route('/api/usuarios', methods=['POST'])
def registrar_usuario():
    try:
        datos = request.get_json()
        existe_user = UsuarioModel.query.filter_by(id_usuario=datos.get('id_usuario')).first()
        existe_correo = UsuarioModel.query.filter_by(correo=datos.get('correo')).first()
        
        if existe_user or existe_correo:
            return jsonify({'error': 'El ID de usuario o el correo ya están registrados.'}), 400

        nuevo_usuario = UsuarioModel(
            nombres=datos.get('nombres'),
            apellidos=datos.get('apellidos'),
            edad=datos.get('edad'),
            cedula=datos.get('cedula'),
            correo=datos.get('correo'),
            id_usuario=datos.get('id_usuario'),
            contrasena=datos.get('contrasena'),
            rol='usuario'
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        return jsonify({'mensaje': 'Registro completado exitosamente'}), 201
    except Exception as e:
        print(f"Error en registro: {e}")
    return jsonify({'error': 'No se pudo completar el registro en la base de datos.'}), 500

    
@app.route('/api/admin/usuarios/estado/<int:id>', methods=['PUT'])
def cambiar_estado_usuario(id):
    try:
        usuario = UsuarioModel.query.get(id)
        if not usuario or id == 0:
            return jsonify({'error': 'No permitido o usuario no encontrado'}), 403

        usuario.activo = not usuario.activo
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Estado actualizado', 
            'nuevo_estado': bool(usuario.activo)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/usuarios/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def gestionar_usuario_especifico(id):
    usuario = UsuarioModel.query.get(id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    if request.method == 'GET':
        return jsonify({
            'id': usuario.id, 'nombres': usuario.nombres, 'apellidos': usuario.apellidos,
            'cedula': usuario.cedula, 'correo': usuario.correo, 'rol': usuario.rol,
            'id_usuario': usuario.id_usuario, 'edad': usuario.edad
        })

    if request.method == 'PUT':
        datos = request.get_json()
        usuario.nombres = datos.get('nombres')
        usuario.apellidos = datos.get('apellidos')
        usuario.cedula = datos.get('cedula')
        usuario.correo = datos.get('correo')
        usuario.rol = datos.get('rol')
        
        if datos.get('contrasena'):
            usuario.contrasena = datos.get('contrasena')
            
        db.session.commit()
        return jsonify({'mensaje': 'Usuario actualizado correctamente'})

    if request.method == 'DELETE':
        if id == 0:
            return jsonify({'error': 'No se puede eliminar al admin maestro'}), 403
        db.session.delete(usuario)
        db.session.commit()
        return jsonify({'mensaje': 'Eliminado'})
# ==========================================================
# 6. INICIO DE APLICACIÓN
# ==========================================================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not UsuarioModel.query.get(0):
            admin = UsuarioModel(id=0, nombres='Administrador', apellidos='Sistema', cedula='0000000000', 
                                 correo='admin@biblioteca.tes', id_usuario='admin', contrasena='1234', rol='admin', edad=30)
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)