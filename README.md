# 📚 Proyecto Biblioteca-TES

Este es un sistema de gestión para una biblioteca virtual, desarrollado como parte de un proyecto académico. El objetivo es permitir la administración de libros, usuarios y procesos de login de forma eficiente.

## 🚀 Características
* **Login de usuarios:** Acceso seguro al sistema.
* **Catálogo Virtual:** Visualización de libros disponibles.
* **Arquitectura:** Desarrollado bajo estandar de tecnologia PWA.

## 🛠️ Tecnologías utilizadas
* **Lenguajes:** Python, FLASK, HTML, CSS
* **Herramientas:** Git, GitHub.
* **Diseño:** Boostrap 5.

## 📂 Cómo ejecutar el proyecto
1. Antes de correr el código, es necesario preparar el espacio de trabajo:
   - El usuario debe descargar el código a su máquina local.
   - Se recomienda usar la carpeta E_Virtual que ya se tiene definida en la estructura para aislar las librerías.
   - Utilizamos el comando python -m venv E_Virtual desde nuestro consola CMD para crear el entorno.
   1.1. Activacion del entorno:
     - Para Windows: E_Virtual\Scripts\activate
     - Para Mac o Linux: source E_Virtual/bin/activate
2. Instalacion de libreria Flask. (Framework principal utilizado)
   - Se recomienda instalar para las librerias:
      - Flask --- El framework principal.
      - Flask-SQLAlchemy ---- Para la gestión de la base de datos SQLite (BaseBiblioteca.db).
      - Flask-Mail --- Necesario para la funcionalidad de recuperación de credenciales por correo.
      - Flask-RESTful y Flask-CORS --- Para que las APIs de libros y usuarios funcionen correctamente.
3. Seguridad.
  - Actualemente se integro a la pltaforma la opción de envio de credenciales mediante correo electronico.
  - Para la cuarta y utlima fase se procedera con los metodos de seguridad para la plataforma.
4. Ejecucion.
  - Una vez todo instalado, se debe ejecutar el archivo principal desde la consola del CMD bajo el siguiente comando:
    - python Biblioteca.py
5. Datos de accesos iniciales.
   - Administrador:
     - Admin
     - 1234
   - Docente:
     - ireyes
     - 1234
   - Estudiante:
     - aureyes
     - 1324
       
## Estructura 
Proyecto_Biblioteca-TES/
├── static/                
│   └── css                      # Hojas de estilo (diseño)
│        └── dashboard.css       # Estilo de diseños de las vistas de index.
│        └── estilos_login.css   # Estilo de diseño de la vista de login.
│        └── imagen_login.css    # Estilo de diseño 
│        └── libreria.css        # Estilo de diseño de la vista de libreria.
│        └── mislibros.css       # Estilo de diseños de la vista de mis libros.
│
│   └── profiles_pics            # Carpeta Donde se almacenan las fotos de perfil cargadas
│   └── uploads                  # Carpeta Donde se almacenan los libros cargados.
│
├── templates/                   # Hojas de estilo (diseño)
│   └── login.html               # Vista de la pagina de login del usuario.
│   └── index_admin.html         # Vista de la pagina principal del administrador.
│   └── index_docente.html       # Vista de la pagina principal del docente.
│   └── index_estudiante.html    # Vista de la pagina principal del estudiante.
│   └── libreria.html            # Vista de la pagina donde se almacenan los libros publicados.
│   └── gestion_usuarios.html    # Vista de la pagina donde el administrador podra crear
│   └── mislibros.html           # Vista de la pagina donde el administrador y docente cargan y publican los libros a la plataforma.
│   └── perfil.html              # Vista del modulo donde se refleja los datos personales del usuario.
│   └── favoritos.html           # Vista donde se almacenan los libros añadidos como favoritos.
│   └── visor.html               # Vista que refleja los libros que se desean visualizar, sin la opcion de poder descargarlos.
│
├── BaseBiblioteca.db            # Base de datos de nuestra APP basado en SQLite
├── Biblioteca.py                # Archivo principal 
└── README.md                    # Documentación del proyecto
