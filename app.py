from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from flask_login import LoginManager
from flask_login import UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SubmitField, DateField, TimeField
from wtforms.validators import DataRequired, Email
from wtforms import SelectField
from flask_login import login_required, current_user
from flask_login import login_user, current_user, login_required, logout_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from wtforms import StringField, PasswordField, SubmitField
from enum import Enum
from flask import Response
import time
from flask import jsonify
from flask_login import logout_user
from functools import wraps
from decimal import Decimal, ROUND_HALF_UP

from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    validators
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length
)

app = Flask(__name__)
app.config['SECRET_KEY'] = '12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'menumastery.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
csrf = CSRFProtect(app)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'info'  # o 'warning', 'danger', etc.

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'img', 'platos')
UPLOAD_FOLDER_USERS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img_users')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_USERS'] = UPLOAD_FOLDER_USERS
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])  
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar sesión')

class RolUsuario(Enum):
    ADMIN = 'admin'
    EMPLEADO = 'empleado'
    CLIENTE = 'cliente'
    USUARIO_MANAGER = 'usuario_manager'

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), default= RolUsuario.CLIENTE.value) 
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    foto = db.Column(db.String(200), default='default.jpeg')
    tipo_empleado = db.Column(db.String(20))

class RegistroForm(FlaskForm):
    nombre = StringField('Nombre completo', validators=[DataRequired()])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Ingresa un email válido')
    ])
    confirm_email = StringField('Confirmar Email', validators=[
        DataRequired(),
        EqualTo('email', message='Los emails deben coincidir')
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(),
        Length(min=8, message='La contraseña debe tener al menos 8 caracteres')
    ])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(),
        EqualTo('password', message='Las contraseñas deben coincidir')
    ])
    terms = BooleanField('Acepto los términos', validators=[
        DataRequired(message='Debes aceptar los términos y condiciones')
    ])
    submit = SubmitField('Registrarse')

class ReservaForm(FlaskForm):
    fecha = DateField('Fecha', format='%Y-%m-%d', validators=[DataRequired()])  
    hora = SelectField('Hora', choices=[
        ('12:00', '12:00 PM'),
        ('13:00', '1:00 PM'),
        ('14:00', '2:00 PM'),
        ('15:00', '3:00 PM'),
        ('18:00', '6:00 PM'),
        ('19:00', '7:00 PM'),
        ('20:00', '8:00 PM')
    ], validators=[DataRequired()])
    personas = SelectField('Numero de personas', choices=[
        (1, '1 persona'),
        (2, '2 personas'),
        (3, '3 personas'),
        (4, '4 personas'),
        (5, '5 personas'),
        (6, '6 personas'),
        (7, '7 personas'),
        (8, '8 personas'),
        (9, '9+ personas (reserva especial)')
    ], validators=[DataRequired()])
    mesa = SelectField('Mesa preferida', choices=[
        ('', 'Sin preferencia'),
        ('1', 'Mesa 1 - Ventana'),
        ('2', 'Mesa 2 - Ventana'),
        ('3', 'Mesa 3 - Centro'),
        ('4', 'Mesa 4 - Centro'),
        ('5', 'Mesa 5 - Terraza'),
        ('6', 'Mesa 6 - Terraza'),
        ('7', 'Mesa 7 - Privada'),
        ('8', 'Mesa 8 - Privada')
    ])
    comentarios = TextAreaField('Comentarios adicionales') 
    submit = SubmitField('Confirmar Reserva')

class Categoria(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    descripcion = db.Column(db.String(200))

class PlatoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    descripcion = TextAreaField('Descripción')
    precio = IntegerField('Precio', validators=[DataRequired()])
    stock = IntegerField('Stock disponible', validators=[DataRequired()])
    stock_minimo = IntegerField('Stock mínimo', validators=[DataRequired()])
    # Usar strings para evitar que 'False' se convierta en True con bool('False')
    destacado = SelectField('Destacado', choices=[('False', 'No'), ('True', 'Si')], coerce=str)
    categoria_id = SelectField('Categoría', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Guardar Plato')

class Plato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Float, nullable=False)
    imagen = db.Column(db.String(255)) 
    destacado = db.Column(db.Boolean, default=False)
    agotado = db.Column(db.Boolean, default=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    categoria = db.relationship('Categoria', backref='platos') 
    stock = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=5) 
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow)

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    usuario = db.relationship('Usuario', backref='pedidos')
    mesa = db.Column(db.String(20)) 
    total = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), default='pendiente')
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('PedidoItem', backref='pedido', lazy=True)

class PedidoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    plato_id = db.Column(db.Integer, db.ForeignKey('plato.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    plato = db.relationship('Plato')
    comentarios = db.Column(db.Text)

class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False)
    personas = db.Column(db.Integer, nullable=False)
    comentarios = db.Column(db.Text)
    estado = db.Column(db.String(20), default='pendiente')
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    mesa = db.Column(db.String(10))
    usuario = db.relationship('Usuario', backref='reservas')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

class CarritoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    plato_id = db.Column(db.Integer, db.ForeignKey('plato.id'), nullable=False)
    cantidad = db.Column(db.Integer, default=1)
    plato = db.relationship('Plato', backref='en_carritos')

class Resena(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    calificacion = db.Column(db.Integer, nullable=False)
    comentario = db.Column(db.Text, nullable=False)
    nombre = db.Column(db.String(100))
    aprobado = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class Notificacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mensaje = db.Column(db.String(255), nullable=False)
    tipo_destino = db.Column(db.String(20), nullable=False)
    visto = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'))  # opcional
    pedido = db.relationship('Pedido', backref='notificaciones')
    rol_destino = db.Column(db.String(50)) 

class MovimientoInventario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plato_id = db.Column(db.Integer, db.ForeignKey('plato.id'), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # 'entrada' o 'salida'
    cantidad = db.Column(db.Integer, nullable=False)
    stock_actual = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(200))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    plato = db.relationship('Plato', backref='movimientos')
    usuario = db.relationship('Usuario')

class RegistroActividad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    accion = db.Column(db.String(200))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    ip = db.Column(db.String(50))


@app.before_request
def make_session_permanent():
    session.permanent = True

@app.before_request
def ejecutar_limpieza_automatica():
    """Ejecuta limpieza automática una vez al día"""
    try:
        # Verificar si ya se ejecutó la limpieza hoy
        ultima_limpieza = session.get('ultima_limpieza_automatica')
        hoy = datetime.utcnow().date()
        
        if ultima_limpieza != str(hoy):
            # Ejecutar limpieza automática
            limpiar_datos_antiguos()
            # Marcar que se ejecutó hoy
            session['ultima_limpieza_automatica'] = str(hoy)
    except Exception:
        # Si hay error, continuar normalmente
        pass

@app.before_request
def check_maintenance_mode():
    # Rutas que siempre deben estar disponibles durante mantenimiento
    allowed_routes = ['login', 'static', 'logout']
    
    # Rutas administrativas que solo los admins pueden acceder durante mantenimiento
    admin_routes = ['admin_panel', 'configuracion_sistema', 'gestion_platos', 'agregar_plato', 
                   'editar_plato', 'eliminar_plato', 'gestion_inventario', 'ajustar_inventario', 
                   'historial_inventario', 'reportes']
    
    # Verificar si la ruta actual está permitida para todos
    if request.endpoint in allowed_routes:
        return
    
    # Verificar modo mantenimiento
    try:
        config = get_configuracion()
        if config.maintenance_mode:
            # Si es una ruta administrativa, verificar que sea admin
            if request.endpoint in admin_routes:
                if not current_user.is_authenticated or current_user.rol != 'admin':
                    return render_template('maintenance.html')
            # Para todas las demás rutas, mostrar página de mantenimiento
            elif not current_user.is_authenticated or current_user.rol != 'admin':
                return render_template('maintenance.html')
    except Exception:
        # Si hay error al obtener configuración, continuar normalmente
        pass


def redondear(valor):
    return float(Decimal(valor).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

# Función para limpiar datos antiguos
def limpiar_datos_antiguos():
    """Limpia reservas y pedidos antiguos según la configuración del sistema"""
    try:
        config = get_configuracion()
        
        if not config.limpieza_automatica_activa:
            return {"success": True, "message": "Limpieza automática desactivada"}
        
        fecha_limite_reservas = datetime.utcnow() - timedelta(days=config.reservas_dias_limpieza)
        fecha_limite_pedidos = datetime.utcnow() - timedelta(days=config.pedidos_dias_limpieza)
        
        # Limpiar reservas antiguas (solo las completadas o canceladas)
        reservas_eliminadas = Reserva.query.filter(
            Reserva.fecha < fecha_limite_reservas,
            Reserva.estado.in_(['completada', 'cancelada'])
        ).count()
        
        Reserva.query.filter(
            Reserva.fecha < fecha_limite_reservas,
            Reserva.estado.in_(['completada', 'cancelada'])
        ).delete(synchronize_session=False)
        
        # Limpiar pedidos antiguos (solo los entregados)
        pedidos_eliminados = Pedido.query.filter(
            Pedido.fecha < fecha_limite_pedidos,
            Pedido.estado == 'entregado'
        ).count()
        
        Pedido.query.filter(
            Pedido.fecha < fecha_limite_pedidos,
            Pedido.estado == 'entregado'
        ).delete(synchronize_session=False)
        
        # Limpiar notificaciones antiguas (más de 7 días)
        notificaciones_eliminadas = Notificacion.query.filter(
            Notificacion.fecha < datetime.utcnow() - timedelta(days=7)
        ).count()
        
        Notificacion.query.filter(
            Notificacion.fecha < datetime.utcnow() - timedelta(days=7)
        ).delete(synchronize_session=False)
        
        # Limpiar movimientos de inventario antiguos (más de 6 meses)
        movimientos_eliminados = MovimientoInventario.query.filter(
            MovimientoInventario.fecha < datetime.utcnow() - timedelta(days=180)
        ).count()
        
        MovimientoInventario.query.filter(
            MovimientoInventario.fecha < datetime.utcnow() - timedelta(days=180)
        ).delete(synchronize_session=False)
        
        db.session.commit()
        
        return {
            "success": True,
            "message": f"Limpieza completada: {reservas_eliminadas} reservas, {pedidos_eliminados} pedidos, {notificaciones_eliminadas} notificaciones, {movimientos_eliminados} movimientos eliminados"
        }
        
    except Exception as e:
        db.session.rollback()
        return {"success": False, "message": f"Error en limpieza: {str(e)}"}

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Decorador para verificar sesión de cliente
def login_cliente_requerido(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        if 'cliente_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorador

#crear usuario inicial.
def crear_admin_inicial():
    with app.app_context():
        #Administrador
        if not Usuario.query.filter_by(email='admin@menumastery.com').first():
            admin = Usuario(
                nombre='Administrador',
                email='admin@menumastery.com',
                password=generate_password_hash('Admin123'),
                rol=RolUsuario.ADMIN.value
            )
            db.session.add(admin)
            db.session.commit()
            print("Usuario admin creado: admin@menumastery.com / Admin123")
        
        # Cocinero
        if not Usuario.query.filter_by(email='cocinero@menumastery.com').first():
            cocinero = Usuario(
                nombre='Chef Principal',
                email='cocinero@menumastery.com',
                password=generate_password_hash('Cocinero123'),
                rol=RolUsuario.EMPLEADO.value,
                tipo_empleado='cocinero'
            )
            db.session.add(cocinero)
        
        # Mesero
        if not Usuario.query.filter_by(email='mesero@menumastery.com').first():
            mesero = Usuario(
                nombre='Mesero',
                email='mesero@menumastery.com',
                password=generate_password_hash('Mesero123'),
                rol=RolUsuario.EMPLEADO.value,
                tipo_empleado= 'mesero'
            )
            db.session.add(mesero)

        # Usuario Manager
        if not Usuario.query.filter_by(email='usermanager@menumastery.com').first():
            usuario_manager = Usuario(
                nombre='Usuario Manager',
                email='usermanager@menumastery.com',
                password=generate_password_hash('UserManager123'),
                rol=RolUsuario.USUARIO_MANAGER.value
            )
            db.session.add(usuario_manager)

        db.session.commit()
        print("Usuarios iniciales creados:")
        print("- Cocinero: cocinero@menumastery.com / Cocinero123")
        print("- Mesero: mesero@menumastery.com / Mesero123")
        print("- Usuario Manager: usermanager@menumastery.com / UserManager123")

#modulo administrador
@app.route('/admin/panel')
@login_required
def admin_panel():
    if not current_user.is_authenticated or current_user.rol != 'admin':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    # Estadísticas actualizadas
    total_usuarios = Usuario.query.count()
    pedidos_hoy = Pedido.query.filter(Pedido.fecha >= datetime.today().date()).count()
    productos_inventario = Plato.query.count()
    reservas_activas = Reserva.query.filter(Reserva.fecha >= datetime.now()).count()
    
    return render_template('admin/base.html', 
                        total_usuarios=total_usuarios,
                        pedidos_hoy=pedidos_hoy,
                        productos_inventario=productos_inventario,
                        reservas_activas=reservas_activas,
                        now=datetime.now())

@app.route('/admin/platos/agregar', methods=['GET', 'POST'])
@login_required
def agregar_plato():
    if current_user.rol != 'admin':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    form = PlatoForm()
    form.categoria_id.choices = [(c.id, c.nombre) for c in Categoria.query.order_by('nombre')]
    
    if form.validate_on_submit():
        try:
            # Verificar si se subi una imagen
            if 'imagen' not in request.files:
                flash('No se ha seleccionado ningún archivo de imagen', 'danger')
                return redirect(url_for('agregar_plato'))
            
            imagen = request.files['imagen']
            
            if imagen.filename == '':
                flash('No se ha seleccionado ningún archivo', 'danger')
                return redirect(url_for('agregar_plato'))
            
            if not allowed_file(imagen.filename):
                flash('Formato de imagen no permitido. Use: PNG, JPG, JPEG o GIF', 'danger')
                return redirect(url_for('agregar_plato'))
            
            filename = secure_filename(imagen.filename)

            # Crear directorio si no existe
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

            # Guardar la imagen
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagen.save(filepath)

            # Crear el plato
            nuevo_plato = Plato(
                nombre=form.nombre.data,
                descripcion=form.descripcion.data,
                precio=form.precio.data,
                imagen=filename,  # Guardamos solo el nombre del archivo
                destacado=True if form.destacado.data == 'True' else False,
                categoria_id=form.categoria_id.data,
                stock=form.stock.data,
                stock_minimo=form.stock_minimo.data
            )
            
            db.session.add(nuevo_plato)
            db.session.commit()
            
            flash('Plato agregado exitosamente!', 'success')
            return redirect(url_for('gestion_platos'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar plato: {str(e)}', 'danger')
    
    return render_template('admin/agregar_plato.html', form=form)

@app.route('/admin/platos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_plato(id):
    if current_user.rol != 'admin':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    plato = Plato.query.get_or_404(id)
    form = PlatoForm(obj=plato)
    form.categoria_id.choices = [(c.id, c.nombre) for c in Categoria.query.order_by('nombre')]
    
    if form.validate_on_submit():
        try:
            # Eliminar imagen si el checkbox está marcado
            if request.form.get('eliminar_imagen') == 'on' and plato.imagen:
                imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], plato.imagen)
                if os.path.exists(imagen_path):
                    try:
                        os.remove(imagen_path)
                    except Exception as e:
                        flash(f'Error al eliminar la imagen: {str(e)}', 'warning')
                plato.imagen = None

            # Procesar imagen si se sube una nueva
            imagen = request.files.get('imagen')
            if imagen and imagen.filename != '':
                if allowed_file(imagen.filename):
                    # Eliminar imagen anterior si existe
                    if plato.imagen:
                        try:
                            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], plato.imagen))
                        except:
                            pass
                    filename = secure_filename(imagen.filename)
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    imagen.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    plato.imagen = filename

            # Actualizar otros campos
            plato.nombre = form.nombre.data
            plato.descripcion = form.descripcion.data
            plato.precio = form.precio.data
            plato.destacado = True if str(form.destacado.data) == 'True' else False
            plato.categoria_id = form.categoria_id.data
            plato.stock = form.stock.data
            plato.stock_minimo = form.stock_minimo.data

            db.session.commit()
            flash('Plato actualizado exitosamente!', 'success')
            return redirect(url_for('gestion_platos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar plato: {str(e)}', 'danger')
    return render_template('admin/editar_plato.html', form=form, plato=plato)


@app.route('/admin/platos/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_plato(id):
    if current_user.rol != 'admin':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    plato = Plato.query.get_or_404(id)

    # Eliminar imagen si existe
    if plato.imagen:
        imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], plato.imagen)
        if os.path.exists(imagen_path):
            try:
                os.remove(imagen_path)
            except Exception as e:
                flash(f'Error al eliminar la imagen del plato: {str(e)}', 'warning')

    # Eliminar plato de la base de datos
    try:
        db.session.delete(plato)
        db.session.commit()
        flash('Plato eliminado exitosamente!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar plato: {str(e)}', 'danger')

    return redirect(url_for('gestion_platos'))


@app.route('/admin/gestion_platos')
@login_required
def gestion_platos():
    if current_user.rol != 'admin':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    platos = Plato.query.order_by(Plato.nombre).all()
    return render_template('admin/gestion_platos.html', platos=platos)

# categoria de platos ADMINISTRACION.
def agregar_datos_iniciales():
    with app.app_context(): 
        if not Categoria.query.first():
            categorias = [
                Categoria(nombre="Desayunos"),
                Categoria(nombre="Almuerzos"),
                Categoria(nombre="Cenas"),
                Categoria(nombre="Bebidas"),
                Categoria(nombre="Comidas rapidas"),
            ]
            db.session.add_all(categorias)
            db.session.commit()

        # Agregar algunos platos con inventario inicial
        if not Plato.query.first():
            desayuno = Categoria.query.filter_by(nombre="Desayunos").first()
            almuerzo = Categoria.query.filter_by(nombre="Almuerzos").first()
            
            platos = [
                Plato(
                    nombre="Huevos con tocino",
                    descripcion="Huevos revueltos con tocino crocante",
                    precio=12000,
                    categoria_id=desayuno.id,
                    stock=15,
                    stock_minimo=5
                ),
                Plato(
                    nombre="Pasta Alfredo",
                    descripcion="Pasta con salsa alfredo y pollo",
                    precio=18000,
                    categoria_id=almuerzo.id,
                    stock=8,
                    stock_minimo=3
                )
            ]
            db.session.add_all(platos)
            db.session.commit()

# rol requerido
def rol_requerido(rol_necesario):
    def decorador(func):
        @wraps(func)
        def envoltura(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Debes iniciar sesión para acceder a esta página.", "warning")
                return redirect(url_for('login'))
            if current_user.rol != rol_necesario:
                flash("No tienes permiso para acceder a esta sección.", "danger")
                return redirect(url_for('inicio'))
            return func(*args, **kwargs)
        return envoltura
    return decorador

# decorador para múltiples roles
def roles_requeridos(*roles_permitidos):
    def decorador(func):
        @wraps(func)
        def envoltura(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Debes iniciar sesión para acceder a esta página.", "warning")
                return redirect(url_for('login'))
            if current_user.rol not in roles_permitidos:
                flash("No tienes permiso para acceder a esta sección.", "danger")
                return redirect(url_for('inicio'))
            return func(*args, **kwargs)
        return envoltura
    return decorador

#modificaciones como modo empleado.
# Decorador para verificar tipo de empleado
def tipo_empleado_requerido(*tipos_permitidos):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.rol != RolUsuario.EMPLEADO.value:
                flash('Acceso no autorizado', 'danger')
                return redirect(url_for('inicio'))
            if current_user.tipo_empleado not in tipos_permitidos:
                flash('No tienes permiso para acceder a esta sección', 'danger')
                return redirect(url_for('empleado_dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Dashboard principal de empleados
# Módulo unificado de empleados
@app.route('/empleado/dashboard')
@login_required
@rol_requerido(RolUsuario.EMPLEADO.value)
def empleado_dashboard():
    if current_user.rol != RolUsuario.EMPLEADO.value:
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    hoy = datetime.now().date()
    
    # Obtener notificaciones no vistas y recientes
    notificaciones_no_vistas = Notificacion.query.filter_by(
        tipo_destino=current_user.tipo_empleado,
        visto=False
    ).count()
    
    notificaciones_recientes = Notificacion.query.filter_by(
        tipo_destino=current_user.tipo_empleado
    ).order_by(Notificacion.fecha.desc()).limit(5).all()
    
    if current_user.tipo_empleado == 'cocinero':
        pedidos_count = Pedido.query.filter_by(estado='pendiente').count()
        platos_agotados_count = Plato.query.filter_by(agotado=True).count()
        return render_template('empleado/dashboard.html',
                            pedidos_pendientes_count=pedidos_count,
                            platos_agotados_count=platos_agotados_count,
                            notificaciones_no_vistas=notificaciones_no_vistas,
                            notificaciones_recientes=notificaciones_recientes)
    elif current_user.tipo_empleado == 'mesero':
        pedidos_count = Pedido.query.filter_by(estado='listo').count()
        reservas_count = Reserva.query.filter(
            db.func.date(Reserva.fecha) == hoy,
            Reserva.estado == 'confirmada'
        ).count()
        return render_template('empleado/dashboard.html',
                            pedidos_listos_count=pedidos_count,
                            reservas_hoy_count=reservas_count,
                            notificaciones_no_vistas=notificaciones_no_vistas,
                            notificaciones_recientes=notificaciones_recientes)
    
    flash('Tu cuenta de empleado no está! configurada correctamente', 'warning')
    return redirect(url_for('inicio'))

# Módulo de pedidos unificado
@app.route('/empleado/pedidos')
@login_required
@rol_requerido(RolUsuario.EMPLEADO.value)
def empleado_pedidos():
    print("Tipo de empleado:", current_user.tipo_empleado)
    if current_user.tipo_empleado == 'cocinero':
        pedidos = Pedido.query.filter_by(estado='pendiente').order_by(Pedido.fecha.asc()).all()
        plantilla = 'empleado/pedidos_cocina.html'
        return render_template(plantilla, pedidos=pedidos)
    else:
        # Pedidos listos para servir (de todos los usuarios)
        pedidos_listos = Pedido.query.filter_by(estado='listo').order_by(Pedido.fecha.desc()).all()
        # Pedidos realizados por el mesero actual
        pedidos_mesero = Pedido.query.filter_by(usuario_id=current_user.id).order_by(Pedido.fecha.desc()).all()
        # Obtener notificaciones para meseros
        notificaciones = Notificacion.query.filter_by(
            rol_destino='MESERO',
            visto=False
        ).order_by(Notificacion.fecha.desc()).all()
        # Marcar como vistas
        for notificacion in notificaciones:
            notificacion.visto = True
        db.session.commit()
        plantilla = 'empleado/pedidos_mesero.html'
        return render_template(plantilla, pedidos_listos=pedidos_listos, pedidos_mesero=pedidos_mesero)

# Módulo de disponibilidad (solo cocineros)
@app.route('/empleado/disponibilidad')
@login_required
@tipo_empleado_requerido('cocinero')
def control_disponibilidad():
    # Filtrar según parámetro de URL
    filtro = request.args.get('filtro')
    
    if filtro == 'agotados':
        platos = Plato.query.filter_by(agotado=True).order_by(Plato.nombre).all()
    else:
        platos = Plato.query.order_by(Plato.nombre).all()
    
    platos_agotados_count = Plato.query.filter_by(agotado=True).count()
    
    return render_template('empleado/disponibilidad.html', 
                        platos=platos, 
                        platos_agotados_count=platos_agotados_count,
                        filtro_actual=filtro)

# Módulo de reservas (solo meseros)
@app.route('/empleado/reservas')
@login_required
@tipo_empleado_requerido('mesero')
def empleado_reservas():
    hoy = datetime.now().date()
    
    # Obtener reservas para hoy y futuras, ordenadas por fecha
    reservas = Reserva.query.filter(
        db.func.date(Reserva.fecha) >= hoy
    ).order_by(
        Reserva.fecha.asc(),
        Reserva.estado.asc()
    ).all()
    
    # Estadísticas para el dashboard
    reservas_hoy = Reserva.query.filter(
        db.func.date(Reserva.fecha) == hoy
    ).count()
    
    reservas_confirmadas = Reserva.query.filter(
        db.func.date(Reserva.fecha) == hoy,
        Reserva.estado == 'confirmada'
    ).count()
    
    return render_template(
        'empleado/reservas.html',
        reservas=reservas,
        hoy=hoy,
        reservas_hoy=reservas_hoy,
        reservas_confirmadas=reservas_confirmadas
    )

@app.route('/reserva/<int:id>/marcar-como-completada', methods=['POST'])
@login_required
@tipo_empleado_requerido('mesero')
def marcar_como_completada(id):
    reserva = Reserva.query.get_or_404(id)
    reserva.estado = 'completada'
    db.session.commit()
    
    # Crear notificación
    notificacion = Notificacion(
        mensaje=f"Reserva #{reserva.id} completada - Mesa {reserva.mesa}",
        tipo_destino='mesero',
        visto=False,
        fecha=datetime.utcnow()
    )
    db.session.add(notificacion)
    db.session.commit()
    
    flash('Reserva marcada como completada', 'success')
    return redirect(url_for('empleado_reservas'))



# En las funciones que crean notificaciones:
def notificar_empleados(pedido):
    try:
        mensaje = f"Nuevo pedido #{pedido.id} - Mesa {pedido.mesa or 'Sin asignar'}"
        
        # Notificar a cocineros
        noti_cocinero = Notificacion(
            mensaje=mensaje,
            tipo_destino='cocinero',
            pedido_id=pedido.id,
            visto=False,
            fecha=datetime.utcnow()
        )
        db.session.add(noti_cocinero)
        
        # Notificar a meseros
        noti_mesero = Notificacion(
            mensaje=mensaje,
            tipo_destino='mesero',
            pedido_id=pedido.id,
            visto=False,
            fecha=datetime.utcnow()
        )
        db.session.add(noti_mesero)
        
        db.session.commit()
        return True
    
    except Exception as e:
        app.logger.error(f'Error al crear notificaciones: {str(e)}')
        db.session.rollback()
        return False



#modulo del cocinero
@app.route('/pedido/<int:id>/completar', methods=['POST'])
@login_required
def completar_pedido(id):
    if current_user.rol != RolUsuario.EMPLEADO.value or current_user.tipo_empleado != 'cocinero':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    pedido = Pedido.query.get_or_404(id)
    pedido.estado = 'listo'
    db.session.commit()
    flash('Pedido marcado como listo para servir', 'success')
    return redirect(url_for('empleado_pedidos'))

#modulo del mesero


@app.route('/cambiar_estado_plato/<int:id>', methods=['POST'])
@login_required
@tipo_empleado_requerido('cocinero')
def cambiar_estado_plato(id):
    try:
        plato = Plato.query.get_or_404(id)
        nuevo_estado = request.form.get('estado') == 'agotado'
        
        # Cambiar el estado del plato
        plato.agotado = nuevo_estado
        db.session.commit()
        
        # Crear notificación de cambio de estado
        estado = "agotado" if nuevo_estado else "disponible"
        mensaje = f"El plato {plato.nombre} ha sido marcado como {estado}"
        
        notificacion = Notificacion(
            mensaje=mensaje,
            tipo_destino='cocinero',
            visto=False,
            fecha=datetime.utcnow()
        )
        db.session.add(notificacion)
        db.session.commit()
        
        flash(f'Estado de {plato.nombre} actualizado correctamente a {estado}', 'success')
        return redirect(url_for('control_disponibilidad'))
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error al cambiar estado del plato: {str(e)}')
        flash(f'Error al actualizar el estado del plato: {str(e)}', 'danger')
        return redirect(url_for('control_disponibilidad'))

# Módulo del mesero - Reservas



@app.route('/reserva/<int:id>/confirmar', methods=['POST'])
@login_required
@rol_requerido(RolUsuario.EMPLEADO.value)
def confirmar_reserva(id):
    reserva = Reserva.query.get_or_404(id)
    reserva.estado = 'confirmada'
    db.session.commit()
    flash('Reserva confirmada exitosamente', 'success')
    return redirect(url_for('empleado_reservas'))

@app.route('/reserva/<int:id>/cancelar', methods=['POST'])
@login_required
@rol_requerido(RolUsuario.EMPLEADO.value)
def cancelar_reserva(id):
    reserva = Reserva.query.get_or_404(id)
    reserva.estado = 'cancelada'
    db.session.commit()
    flash('Reserva cancelada exitosamente', 'warning')
    return redirect(url_for('empleado_reservas'))

@app.route('/reserva/<int:id>/asignar-mesa', methods=['POST'])
@login_required
@rol_requerido(RolUsuario.EMPLEADO.value)
def asignar_mesa(id):
    reserva = Reserva.query.get_or_404(id)
    mesa = request.form.get('mesa')
    
    if not mesa:
        flash('Debe especificar un número de mesa', 'danger')
        return redirect(url_for('empleado_reservas'))
    
    reserva.mesa = mesa
    db.session.commit()
    flash(f'Mesa {mesa} asignada a la reserva #{reserva.id}', 'success')
    return redirect(url_for('empleado_reservas'))

@app.route('/mesero/verificar-reserva', methods=['GET', 'POST'])
@login_required
@tipo_empleado_requerido('mesero')
def verificar_reserva():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        fecha = request.form.get('fecha')
        
        if nombre and fecha:
            try:
                fecha_busqueda = datetime.strptime(fecha, '%Y-%m-%d').date()
                reservas = Reserva.query.filter(
                    Reserva.usuario.has(Usuario.nombre.ilike(f'%{nombre}%')),
                    db.func.date(Reserva.fecha) == fecha_busqueda
                ).order_by(Reserva.fecha.asc()).all()
                
                if reservas:
                    flash(f'Se encontraron {len(reservas)} reservas', 'success')
                    return render_template('empleado/resultados_verificacion.html', reservas=reservas)
                else:
                    flash('No se encontraron reservas con esos datos', 'warning')
            except ValueError:
                flash('Formato de fecha incorrecto', 'danger')
    
    return redirect(url_for('empleado_reservas'))

#stream de pedidos para mesero y coinero
@app.route('/stream-reservas')
@login_required
def stream_reservas():
    def event_stream():
        last_count = 0
        while True:
            if current_user.rol == RolUsuario.EMPLEADO.value and current_user.tipo_empleado == 'mesero':
                hoy = datetime.now().date()
                count = Reserva.query.filter(
                    Reserva.fecha >= datetime.combine(hoy, datetime.min.time())
                ).count()
                
                if count != last_count:
                    yield f"data: actualizar\n\n"
                    last_count = count
            time.sleep(5)

    return Response(event_stream(), mimetype="text/event-stream")


def notificar_roles(pedido):
    mensaje = f"Nuevo pedido confirmado por {current_user.nombre} - Mesa {pedido.mesa}"
    for rol in ['MESERO', 'COCINERO']:
        noti = Notificacion(mensaje=mensaje, rol_destino=rol, pedido=pedido)
        db.session.add(noti)

@app.route('/notificaciones/mesero')
@login_required
@rol_requerido(RolUsuario.EMPLEADO.value)
def notificaciones_mesero():
    # Obtener conteo de notificaciones no vistas
    count = Notificacion.query.filter_by(
        rol_destino='MESERO',
        visto=False
    ).count()
    
    # Obtener Última notificación no vista
    last_notification = Notificacion.query.filter_by(
        rol_destino='MESERO',
        visto=False
    ).order_by(Notificacion.fecha.desc()).first()
    
    return jsonify({
        'count': count,
        'last_message': last_notification.mensaje if last_notification else None
    })

@app.route('/pedidos/mesero/count')
@login_required
@rol_requerido(RolUsuario.EMPLEADO.value)
def pedidos_mesero_count():
    count = Pedido.query.filter_by(estado='listo').count()
    return jsonify({'count': count})

# EnrutaciÃ³n inicial
@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/informacion')
def informacion():
    return render_template('informacion.html')

@app.route('/ping-session')
def ping_session():
    return jsonify(success=True)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

#modulo de reseñas
@app.route('/enviar-resena', methods=['POST'])
def enviar_resena():
    # CÃ³digo para guardar la reseña
    return redirect(url_for('mis_reservas'))  # o a donde quieras redirigir

#modulo de perfil
@app.route('/perfil')
@login_required
def perfil():
    modo = request.args.get('modo', 'ver')
    form = CambioPasswordForm()
    
    # Obtener las reservas del usuario actual
    reservas_usuario = Reserva.query.filter_by(usuario_id=current_user.id).all()
    
    # Obtener compras para el historial (si es necesario)
    compras = []  # Aquí deberías cargar las compras del usuario si las tienes
    
    return render_template('perfil.html', 
                        modo=modo, 
                        form=form,
                        reservas_usuario=reservas_usuario,
                        compras=compras)

@app.route('/perfil/actualizar', methods=['POST'])
@login_required
def actualizar_perfil():
    current_user.nombre = request.form['nombre']
    current_user.email = request.form['email']

    foto = request.files.get('foto')
    if foto and foto.filename != '':
        if allowed_file(foto.filename):
            filename = secure_filename(foto.filename)
            os.makedirs(app.config['UPLOAD_FOLDER_USERS'], exist_ok=True)
            ruta = os.path.join(app.config['UPLOAD_FOLDER_USERS'], filename)
            foto.save(ruta)
            current_user.foto = filename
        else:
            flash('Formato de imagen no permitido', 'danger')

    try:
        db.session.commit()
        flash('Perfil actualizado correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar el perfil: {str(e)}', 'danger')

    return redirect(url_for('perfil'))#modulo de contacto
@app.route('/contacto', methods=['GET', 'POST'], endpoint='contacto')
def contacto():
    resenas = Resena.query.filter_by(aprobado=True).order_by(Resena.fecha.desc()).limit(5).all()
    
    if request.method == 'POST':
        if 'enviar_resena' in request.form:  
            try:
                nueva_resena = Resena(
                    calificacion=int(request.form['rating']),
                    comentario=request.form['comentario'],
                    nombre=request.form.get('nombre', 'Anónimo'),
                    aprobado=False
                )
                db.session.add(nueva_resena)
                db.session.commit()
                flash('Gracias por tu reseña! Será publicada despuÃ©s de ser aprobada.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error al enviar la reseña: {str(e)}', 'danger')
        
        elif 'enviar_contacto' in request.form:  # Formulario de contacto
            flash('Mensaje enviado con éxito. Nos pondremos en contacto pronto!', 'success')
        
        return redirect(url_for('contacto'))
    
    return render_template('contacto.html', resenas=resenas)

#modulo de carro de compras. 
@app.route('/carrito/', methods=['GET', 'POST'])
@login_required
def carrito():
    if request.method == 'POST':
        return procesar_pedido()
    
    # Obtener items con las relaciones necesarias
    items = CarritoItem.query.filter_by(usuario_id=current_user.id)\
                    .join(Plato)\
                    .options(
                        db.joinedload(CarritoItem.plato).joinedload(Plato.categoria)
                    ).all()
    
    # Crear una estructura de datos serializable
    items_data = []
    for item in items:
        item_data = {
            'id': item.id,
            'cantidad': item.cantidad,
            'plato': {
                'id': item.plato.id,
                'nombre': item.plato.nombre,
                'precio': float(item.plato.precio),
                'imagen': item.plato.imagen if item.plato.imagen else 'default-dish.jpg',
                'categoria': {
                    'id': item.plato.categoria.id,
                    'nombre': item.plato.categoria.nombre
                }
            }
        }
        items_data.append(item_data)

    # Calcular totales
    subtotal = sum(item['plato']['precio'] * item['cantidad'] for item in items_data)
    envio = 2000  # Costo fijo de envío
    total = subtotal + envio

    # Detectar reserva activa del usuario para auto-asignar mesa
    ahora = datetime.utcnow()
    reserva_activa = Reserva.query\
        .filter(
            Reserva.usuario_id == current_user.id,
            Reserva.estado.in_(['pendiente', 'confirmada']),
            Reserva.fecha >= ahora
        )\
        .order_by(Reserva.fecha.asc())\
        .first()
    mesa_reserva_usuario = reserva_activa.mesa if reserva_activa and reserva_activa.mesa else None

    # Obtener mesas disponibles (no reservadas ni ocupadas en pedidos pendientes)
    todas_mesas = ['1','2','3','4','5','6','7','8']
    mesas_ocupadas = set([r.mesa for r in Reserva.query.filter(Reserva.mesa.isnot(None), Reserva.estado != 'cancelada').all()])
    mesas_pedidos = set([p.mesa for p in Pedido.query.filter(Pedido.estado=='pendiente').all() if p.mesa])
    mesas_disponibles = [m for m in todas_mesas if m not in mesas_ocupadas and m not in mesas_pedidos]
    # Si el usuario tiene una mesa reservada, incluirla aunque esté ocupada, para preselección
    if mesa_reserva_usuario and mesa_reserva_usuario not in mesas_disponibles:
        mesas_disponibles = [mesa_reserva_usuario] + [m for m in mesas_disponibles if m != mesa_reserva_usuario]

    return render_template('carrocompras.html',
                        items=items_data,
                        subtotal=subtotal,
                        envio=envio,
                        total=total,
                        mesas_disponibles=mesas_disponibles,
                        mesa_reserva_usuario=mesa_reserva_usuario)

@app.route('/agregar-al-carrito/<int:plato_id>', methods=['POST'])
@login_required
def agregar_al_carrito(plato_id):
    plato = Plato.query.get_or_404(plato_id)
    
    try:
        # Verificar si el plato ya está! en el carrito
        item_existente = CarritoItem.query.filter_by(
            usuario_id=current_user.id,
            plato_id=plato_id
        ).first()

        if item_existente:
            item_existente.cantidad += 1
        else:
            nuevo_item = CarritoItem(
                usuario_id=current_user.id,
                plato_id=plato_id,
                cantidad=1
            )
            db.session.add(nuevo_item)
        
        db.session.commit()
        
        # Obtener conteo actualizado del carrito
        cart_count = CarritoItem.query.filter_by(usuario_id=current_user.id).count()
        
        return jsonify({
            "success": True,
            "message": f'"{plato.nombre}" agregado al carrito',
            "cart_count": cart_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Error al agregar al carrito: {str(e)}"
        }), 400

@app.route('/actualizar-cantidad/<int:item_id>', methods=['POST'])
@login_required
def actualizar_cantidad(item_id):
    try:
        item = CarritoItem.query.filter_by(id=item_id, usuario_id=current_user.id).first_or_404()
        
        action = request.form.get('action')
        if action == 'increase':
            item.cantidad += 1
        elif action == 'decrease':
            item.cantidad = max(1, item.cantidad - 1)
        
        db.session.commit()
        
        items = CarritoItem.query.filter_by(usuario_id=current_user.id).all()
        subtotal = sum(float(item.plato.precio) * item.cantidad for item in items)
        return jsonify({
            'success': True,
            'newQuantity': item.cantidad,
            'subtotal': float(item.plato.precio) * item.cantidad,
            'newTotals': {
                'subtotal': subtotal,
                'servicio': subtotal * 0.1,
                'total': subtotal * 1.1
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/eliminar-del-carrito/<int:item_id>', methods=['POST'])
@login_required
def eliminar_del_carrito(item_id):
    item = CarritoItem.query.filter_by(
        id=item_id,
        usuario_id=current_user.id
    ).first_or_404()

    try:
        db.session.delete(item)
        db.session.commit()
        flash('Ítem eliminado del carrito', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar Ítem', 'danger')
    
    return redirect(url_for('carrito'))

@app.route('/confirmar-pedido', methods=['POST'])
@login_required
def confirmar_pedido():
    items_carrito = CarritoItem.query.filter_by(usuario_id=current_user.id).all()

    if not items_carrito:
        flash('Tu carrito está vacío', 'warning')
        return redirect(url_for('carrito'))

    try:
        in_restaurant = request.form.get('in_restaurant') == 'True'

        if not in_restaurant:
            flash('Próximamente domicilios. Tu pedido no ha sido procesado.', 'info')
            return redirect(url_for('carrito'))

        # Asignar mesa automáticamente desde reserva activa si existe
        mesa = request.form.get('mesa')
        if not mesa:
            ahora = datetime.utcnow()
            reserva_activa = Reserva.query \
                .filter(
                    Reserva.usuario_id == current_user.id,
                    Reserva.estado.in_(['pendiente', 'confirmada']),
                    Reserva.fecha >= ahora
                ) \
                .order_by(Reserva.fecha.asc()) \
                .first()
            if reserva_activa and reserva_activa.mesa:
                mesa = reserva_activa.mesa
            else:
                flash('Debe seleccionar una mesa disponible', 'danger')
                return redirect(url_for('carrito'))

        # Calcular totales
        subtotal = sum(item.plato.precio * item.cantidad for item in items_carrito)
        servicio = subtotal * 0.1  # 10% de servicio
        total = subtotal + servicio

        # Crear pedido
        nuevo_pedido = Pedido(
            usuario_id=current_user.id,
            mesa=mesa,
            total=total,
            estado='pendiente',
            fecha=datetime.utcnow()
        )
        db.session.add(nuevo_pedido)
        db.session.flush()  # Obtener el ID

        # Mover items del carrito al pedido
        for item in items_carrito:
            pedido_item = PedidoItem(
                pedido_id=nuevo_pedido.id,
                plato_id=item.plato_id,
                cantidad=item.cantidad,
                precio_unitario=item.plato.precio,
                comentarios=request.form.get('comentarios', '')
            )
            db.session.add(pedido_item)
            db.session.delete(item)

        # Crear notificaciones mÃ¡s detalladas
        mensaje_cocinero = f"Nuevo pedido #{nuevo_pedido.id} - {len(items_carrito)} platos - Mesa: {mesa or 'Sin asignar'}"
        mensaje_mesero = f"Pedido #{nuevo_pedido.id} listo para preparar - Mesa: {mesa or 'Sin asignar'}"

        noti_cocinero = Notificacion(
            mensaje=mensaje_cocinero,
            tipo_destino='cocinero',
            pedido_id=nuevo_pedido.id,
            visto=False,
            fecha=datetime.utcnow()
        )

        noti_mesero = Notificacion(
            mensaje=mensaje_mesero,
            tipo_destino='mesero',
            pedido_id=nuevo_pedido.id,
            visto=False,
            fecha=datetime.utcnow()
        )

        db.session.add_all([noti_cocinero, noti_mesero])
        db.session.commit()

        flash('Su pedido se ha realizado con exito', 'success')
        return redirect(url_for('historial_compras'))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error al confirmar pedido: {str(e)}')
        flash(f'Error al confirmar pedido: {str(e)}', 'danger')
        return redirect(url_for('carrito'))
    
@app.route('/stream-pedidos')
@login_required
def stream_pedidos():
    def event_stream():
        last_count = 0
        while True:
                if current_user.is_authenticated and current_user.rol == RolUsuario.EMPLEADO.value:

                    count = Notificacion.query.filter_by(
                        tipo_destino=current_user.tipo_empleado,
                        visto=False
                    ).count()
                
                    if count != last_count:
                        yield f"data: actualizar\n\n"
                        last_count = count
                time.sleep(2)

    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/historial-compras')
@login_required
def historial_compras():
    pedidos = Pedido.query.filter_by(usuario_id=current_user.id)\
                        .order_by(Pedido.fecha.desc()).all()
    return render_template('historial_compras.html', pedidos=pedidos)


# Funciones auxiliares
def procesar_pedido():
    items = CarritoItem.query.filter_by(usuario_id=current_user.id).all()
    
    if not items:
        flash('Tu carrito está¡ vací­o', 'warning')
        return redirect(url_for('carrito'))
    
    try:
        # Calcular totales
        subtotal = sum(item.plato.precio * item.cantidad for item in items)
        envio = 2000  # Costo fijo de envío
        total = subtotal + envio

        mesa = request.form.get('mesa')
        if not mesa:
            ahora = datetime.utcnow()
            reserva_activa = Reserva.query \
                .filter(
                    Reserva.usuario_id == current_user.id,
                    Reserva.estado.in_(['pendiente', 'confirmada']),
                    Reserva.fecha >= ahora
                ) \
                .order_by(Reserva.fecha.asc()) \
                .first()
            if reserva_activa and reserva_activa.mesa:
                mesa = reserva_activa.mesa
        # Crear pedido
        nuevo_pedido = Pedido(
            usuario_id=current_user.id,
            mesa=mesa,
            total=total,
            estado='pendiente',
            comentarios=request.form.get('comentarios', '')
        )
        db.session.add(nuevo_pedido)
        db.session.flush()

        # Agregar items al pedido
        for item in items:
            pedido_item = PedidoItem(
                pedido_id=nuevo_pedido.id,
                plato_id=item.plato_id,
                cantidad=item.cantidad,
                precio_unitario=item.plato.precio
            )
            db.session.add(pedido_item)
            db.session.delete(item)

        db.session.commit()
        
        flash('Su pedido se ha realizado con exito', 'success')
        return redirect(url_for('historial_compras'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error al procesar el pedido: {str(e)}', 'danger')
        return redirect(url_for('carrito'))

#perfil de usuario.

# modulo de login/Rutas de autenticación
#registro 
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    form = RegistroForm()  # Usa el formulario Flask-WTF
    
    if form.validate_on_submit():
        # Verificar si el email ya existe
        if Usuario.query.filter_by(email=form.email.data).first():
            flash('Este correo ya está¡ registrado', 'danger')
            return redirect(url_for('registro'))
        
        try:
            nuevo_usuario = Usuario(
                nombre=form.nombre.data,
                email=form.email.data,
                password=generate_password_hash(form.password.data),
                rol=RolUsuario.CLIENTE.value
            )
            
            db.session.add(nuevo_usuario)
            db.session.commit()
            
            flash('Registro exitoso! Por favor inicia sesión', 'success')
            return redirect(url_for('login'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar el usuario: {str(e)}', 'danger')
    
    return render_template('registro.html', form=form)  # Pasa el formulario a la plantilla

# ingreso de usuario
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.rol == RolUsuario.ADMIN.value:
            return redirect(url_for('admin_panel'))
        elif current_user.rol == RolUsuario.EMPLEADO.value:
            if current_user.tipo_empleado == 'cocinero':
                return redirect(url_for('pantalla_cocina'))
            else:
                return redirect(url_for('empleado_dashboard'))
        elif current_user.rol == RolUsuario.USUARIO_MANAGER.value:
            return redirect(url_for('usuario_manager_dashboard'))
        return redirect(url_for('inicio'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            
            if user.rol == RolUsuario.ADMIN.value:
                return redirect(url_for('admin_panel'))
            elif user.rol == RolUsuario.EMPLEADO.value:
                if user.tipo_empleado == 'cocinero':
                    return redirect(url_for('pantalla_cocina'))
                else:
                    return redirect(url_for('empleado_dashboard'))
            elif user.rol == RolUsuario.USUARIO_MANAGER.value:
                return redirect(url_for('usuario_manager_dashboard'))
            return redirect(url_for('inicio'))
        
        flash('Credenciales incorrectas', 'danger')
    
    return render_template('login.html', form=form)

# cierre de sesion
@app.route('/logout')
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('inicio'))

# Rutas de usuario
@app.route('/mis_reservas')
@login_required
def mis_reservas():
    if 'user_id' not in session:
        flash('Por favor inicia sesion para ver tus reservas', 'info')
        return redirect(url_for('login'))
    
    reservas = Reserva.query.filter_by(usuario_id=session['user_id']).order_by(Reserva.fecha.desc()).all()
    return render_template('mis_reservas.html', reservas=reservas)


# Ruta para historial de clientes
@app.route('/historial')
@login_required
def historial_cliente():
    pedidos = Pedido.query.filter_by(usuario_id=current_user.id).order_by(Pedido.fecha.desc()).all()
    return render_template('historial_cliente.html', pedidos=pedidos)


@app.route('/notificaciones/no-vistas')
@login_required
def notificaciones_no_vistas():
    if current_user.rol != RolUsuario.EMPLEADO.value or current_user.tipo_empleado not in ['mesero', 'cocinero']:
        return jsonify({'count': 0})
    
    count = Notificacion.query.filter_by(
        rol_destino=current_user.rol.upper(),
        visto=False
    ).count()
    
    return jsonify({'count': count})

@app.route('/empleado/menu', endpoint='empleado_menu')
@login_required
@tipo_empleado_requerido('mesero')
def empleado_menu():
    categorias = Categoria.query.options(db.joinedload(Categoria.platos)).all()
    return render_template('empleado/menu.html', menu=categorias)

@app.route('/empleado/marcar-notificaciones-vistas', methods=['POST'])
@login_required
@rol_requerido(RolUsuario.EMPLEADO.value)
def marcar_notificaciones_vistas():
    Notificacion.query.filter_by(
        tipo_destino=current_user.tipo_empleado,
        visto=False
    ).update({'visto': True})
    db.session.commit()
    return jsonify({'success': True})


# Agregar pruebas unitarias para verificar el flujo
def test_notificaciones_pedido(self):
    with self.client:
        # Login como cliente
        self.login_cliente()
        
        # Agregar items al carrito
        self.agregar_al_carrito()
        
        # Confirmar pedido
        response = self.confirmar_pedido()
        
        # Verificar que se crearon notificaciones
        notis_cocinero = Notificacion.query.filter_by(tipo_destino='cocinero').count()
        notis_mesero = Notificacion.query.filter_by(tipo_destino='mesero').count()
        
        self.assertEqual(notis_cocinero, 1)
        self.assertEqual(notis_mesero, 1)

@app.route('/pedido/<int:pedido_id>')
@login_required
def detalle_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    return render_template('detalle_pedido.html', pedido=pedido)


@app.route('/entregar_pedido/<int:id>', methods=['POST'])
@login_required
def entregar_pedido(id):
    pedido = Pedido.query.get_or_404(id)

    # Aquí puedes aplicar lógica de control de acceso si quieres limitar quién puede entregar
    # Ejemplo: solo cocineros o administradores

    pedido.estado = 'entregado'  # o el valor que manejes en tu app
    db.session.commit()
    flash('El pedido ha sido marcado como entregado.', 'success')
    return redirect(url_for('stream_pedidos'))  # o a donde quieras volver

@app.route('/admin/inventario')
@login_required
def gestion_inventario():
    if current_user.rol != 'admin':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    filtro = request.args.get('filtro', 'todos')
    
    if filtro == 'agotados':
        platos = Plato.query.filter(Plato.stock <= 0).order_by(Plato.nombre).all()
    elif filtro == 'bajos':
        platos = Plato.query.filter(Plato.stock <= Plato.stock_minimo).order_by(Plato.nombre).all()
    else:
        platos = Plato.query.order_by(Plato.nombre).all()
    
    # Estadísticas para el dashboard
    total_platos = Plato.query.count()
    platos_agotados = Plato.query.filter(Plato.stock <= 0).count()
    platos_bajo_stock = Plato.query.filter(Plato.stock <= Plato.stock_minimo).count()
    
    return render_template('admin/inventario.html',
                         platos=platos,
                         filtro_actual=filtro,
                         total_platos=total_platos,
                         platos_agotados=platos_agotados,
                         platos_bajo_stock=platos_bajo_stock)

@app.route('/admin/inventario/ajustar/<int:id>', methods=['GET', 'POST'])
@login_required
def ajustar_inventario(id):
    if current_user.rol != 'admin':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    plato = Plato.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            tipo_operacion = request.form.get('tipo_operacion')
            cantidad = int(request.form.get('cantidad'))
            motivo = request.form.get('motivo', 'Ajuste manual')
            
            if tipo_operacion == 'entrada':
                plato.stock += cantidad
            elif tipo_operacion == 'salida':
                plato.stock = max(0, plato.stock - cantidad)
            
            plato.fecha_actualizacion = datetime.utcnow()
            plato.agotado = plato.stock <= 0
            
            # Registrar movimiento en el historial
            movimiento = MovimientoInventario(
                plato_id=plato.id,
                tipo=tipo_operacion,
                cantidad=cantidad,
                stock_actual=plato.stock,
                motivo=motivo,
                usuario_id=current_user.id
            )
            
            db.session.add(movimiento)
            db.session.commit()
            
            flash(f'Inventario de {plato.nombre} actualizado correctamente', 'success')
            return redirect(url_for('gestion_inventario'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar inventario: {str(e)}', 'danger')
    
    return render_template('admin/ajustar_inventario.html', plato=plato)

@app.route('/admin/inventario/historial')
@login_required
def historial_inventario():
    if current_user.rol != 'admin':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    movimientos = MovimientoInventario.query.order_by(MovimientoInventario.fecha.desc()).all()
    return render_template('admin/historial_inventario.html', movimientos=movimientos)

# Módulo de Usuario Manager
@app.route('/usuario-manager/dashboard')
@login_required
def usuario_manager_dashboard():
    if current_user.rol != RolUsuario.USUARIO_MANAGER.value:
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    # Estadísticas de usuarios
    total_usuarios = Usuario.query.count()
    usuarios_activos = Usuario.query.filter(Usuario.rol != 'admin').count()
    empleados = Usuario.query.filter_by(rol=RolUsuario.EMPLEADO.value).count()
    clientes = Usuario.query.filter_by(rol=RolUsuario.CLIENTE.value).count()
    
    return render_template('usuario_manager/dashboard.html',
                        total_usuarios=total_usuarios,
                        usuarios_activos=usuarios_activos,
                        empleados=empleados,
                        clientes=clientes)

@app.route('/usuario-manager/usuarios')
@login_required
def gestion_usuarios():
    if current_user.rol != RolUsuario.USUARIO_MANAGER.value:
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    usuarios = Usuario.query.filter(Usuario.rol != 'admin').order_by(Usuario.nombre).all()
    return render_template('usuario_manager/gestion_usuarios.html', usuarios=usuarios)

@app.route('/usuario-manager/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    if current_user.rol != RolUsuario.USUARIO_MANAGER.value:
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    usuario = Usuario.query.get_or_404(id)
    
    # No permitir editar administradores
    if usuario.rol == 'admin':
        flash('No se puede editar un administrador', 'danger')
        return redirect(url_for('gestion_usuarios'))
    
    if request.method == 'POST':
        try:
            usuario.nombre = request.form['nombre']
            usuario.email = request.form['email']
            usuario.rol = request.form['rol']
            
            # Si es empleado, asignar tipo
            if usuario.rol == RolUsuario.EMPLEADO.value:
                usuario.tipo_empleado = request.form.get('tipo_empleado')
            else:
                usuario.tipo_empleado = None
            
            db.session.commit()
            flash('Usuario actualizado exitosamente', 'success')
            return redirect(url_for('gestion_usuarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar usuario: {str(e)}', 'danger')
    
    return render_template('usuario_manager/editar_usuario.html', usuario=usuario)

@app.route('/usuario-manager/usuarios/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_usuario(id):
    if current_user.rol != RolUsuario.USUARIO_MANAGER.value:
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    usuario = Usuario.query.get_or_404(id)
    
    # No permitir eliminar administradores
    if usuario.rol == 'admin':
        flash('No se puede eliminar un administrador', 'danger')
        return redirect(url_for('gestion_usuarios'))
    
    try:
        # Verificar si el usuario tiene pedidos o reservas
        pedidos = Pedido.query.filter_by(usuario_id=usuario.id).count()
        reservas = Reserva.query.filter_by(usuario_id=usuario.id).count()
        
        if pedidos > 0 or reservas > 0:
            flash('No se puede eliminar un usuario con pedidos o reservas activas', 'warning')
            return redirect(url_for('gestion_usuarios'))
        
        db.session.delete(usuario)
        db.session.commit()
        flash('Usuario eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar usuario: {str(e)}', 'danger')
    
    return redirect(url_for('gestion_usuarios'))

@app.route('/usuario-manager/usuarios/crear', methods=['GET', 'POST'])
@login_required
def crear_usuario():
    if current_user.rol != RolUsuario.USUARIO_MANAGER.value:
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    if request.method == 'POST':
        try:
            # Verificar si el email ya existe
            if Usuario.query.filter_by(email=request.form['email']).first():
                flash('Este correo ya está registrado', 'danger')
                return redirect(url_for('crear_usuario'))
            
            nuevo_usuario = Usuario(
                nombre=request.form['nombre'],
                email=request.form['email'],
                password=generate_password_hash(request.form['password']),
                rol=request.form['rol']
            )
            
            # Si es empleado, asignar tipo
            if nuevo_usuario.rol == RolUsuario.EMPLEADO.value:
                nuevo_usuario.tipo_empleado = request.form.get('tipo_empleado')
            
            db.session.add(nuevo_usuario)
            db.session.commit()
            
            flash('Usuario creado exitosamente', 'success')
            return redirect(url_for('gestion_usuarios'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear usuario: {str(e)}', 'danger')
    
    return render_template('usuario_manager/crear_usuario.html')

@app.route('/admin/reportes')
@login_required
def reportes():
    if current_user.rol != 'admin':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    estado = request.args.get('estado')
    
    query = Pedido.query
    
    # Apply filters if they exist
    if fecha_desde:
        try:
            fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d')
            query = query.filter(Pedido.fecha >= fecha_desde)
        except ValueError:
            flash('Formato de fecha desde incorrecto', 'warning')
    
    if fecha_hasta:
        try:
            fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            query = query.filter(Pedido.fecha <= fecha_hasta)
        except ValueError:
            flash('Formato de fecha hasta incorrecto', 'warning')
    
    if estado:
        query = query.filter(Pedido.estado == estado)
    
    pedidos = query.order_by(Pedido.fecha.desc()).all()
    
    return render_template('admin/reportes.html', pedidos=pedidos)

# Modelo para configuración del sistema
class Configuracion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), default="Mi Plataforma")
    admin_email = db.Column(db.String(100), default="admin@ejemplo.com")
    theme_color = db.Column(db.String(7), default="#3498db")
    maintenance_mode = db.Column(db.Boolean, default=False)
    # Configuración de limpieza automática
    reservas_dias_limpieza = db.Column(db.Integer, default=30)  # Días después de los cuales limpiar reservas
    pedidos_dias_limpieza = db.Column(db.Integer, default=90)   # Días después de los cuales limpiar pedidos
    limpieza_automatica_activa = db.Column(db.Boolean, default=True)  # Activar/desactivar limpieza automática

# FunciÃ³n para obtener la configuración actual (singleton)
def get_configuracion():
    config = Configuracion.query.first()
    if not config:
        config = Configuracion()
        db.session.add(config)
        db.session.commit()
    return config

# Context processor para pasar la configuración a todas las plantillas
@app.context_processor
def inject_config():
    config = get_configuracion()
    return dict(
        site_name=config.site_name,
        admin_email=config.admin_email,
        theme_color=config.theme_color,
        maintenance_mode=config.maintenance_mode,
        reservas_dias_limpieza=config.reservas_dias_limpieza,
        pedidos_dias_limpieza=config.pedidos_dias_limpieza,
        limpieza_automatica_activa=config.limpieza_automatica_activa
    )

@app.route('/admin/configuracion', methods=['GET', 'POST'])
@login_required
def configuracion_sistema():
    if current_user.rol != 'admin':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))

    config = get_configuracion()
    if request.method == 'POST':
        config.site_name = request.form.get('siteName', config.site_name)
        config.admin_email = request.form.get('adminEmail', config.admin_email)
        config.theme_color = request.form.get('themeColor', config.theme_color)
        config.maintenance_mode = request.form.get('maintenanceMode') == 'on'
        
        # Configuración de limpieza automática
        config.reservas_dias_limpieza = int(request.form.get('reservasDiasLimpieza', config.reservas_dias_limpieza))
        config.pedidos_dias_limpieza = int(request.form.get('pedidosDiasLimpieza', config.pedidos_dias_limpieza))
        config.limpieza_automatica_activa = request.form.get('limpiezaAutomaticaActiva') == 'on'
        
        db.session.commit()
        flash('configuración actualizada correctamente', 'success')
        return redirect(url_for('configuracion_sistema'))

    return render_template('admin/configuracion.html', config=config)

@app.route('/admin/limpiar-datos', methods=['POST'])
@login_required
def limpiar_datos_manual():
    if current_user.rol != 'admin':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    resultado = limpiar_datos_antiguos()
    
    if resultado['success']:
        flash(resultado['message'], 'success')
    else:
        flash(resultado['message'], 'danger')
    
    return redirect(url_for('configuracion_sistema'))

@app.route('/admin/migrar-db')
@login_required
def migrar_base_datos():
    if current_user.rol != 'admin':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    try:
        migrar_configuracion()
        flash('Migración de base de datos completada exitosamente', 'success')
    except Exception as e:
        flash(f'Error en migración: {str(e)}', 'danger')
    
    return redirect(url_for('configuracion_sistema'))

#prueba cosina
# Ruta para la pantalla de cocina
@app.route('/cocina/pantalla')
@login_required
@tipo_empleado_requerido('cocinero')
def pantalla_cocina():
    return render_template('empleado/pantalla_cocina.html')

# API para obtener pedidos para la cocina
@app.route('/api/pedidos-cocina')
@login_required
@tipo_empleado_requerido('cocinero')
def api_pedidos_cocina():
    # Obtener todos los pedidos que no estÃ©n entregados
    pedidos = Pedido.query.filter(Pedido.estado.in_(['pendiente', 'preparando', 'listo']))\
                        .order_by(Pedido.fecha.asc()).all()
    
    # Formatear los datos para la API
    pedidos_data = []
    for pedido in pedidos:
        pedido_data = {
            'id': pedido.id,
            'mesa': pedido.mesa,
            'estado': pedido.estado,
            'fecha': pedido.fecha.isoformat(),
            'items': []
        }
        
        for item in pedido.items:
            pedido_data['items'].append({
                'plato_nombre': item.plato.nombre,
                'cantidad': item.cantidad,
                'comentarios': item.comentarios
            })
            
        pedidos_data.append(pedido_data)
    
    return jsonify(pedidos_data)

# Ruta para cambiar el estado de un pedido
@app.route('/pedido/<int:pedido_id>/cambiar-estado', methods=['POST'])
@login_required
@tipo_empleado_requerido('cocinero')
def cambiar_estado_pedido(pedido_id):
    try:
        pedido = Pedido.query.get_or_404(pedido_id)
        
        # Manejar tanto JSON como form data
        if request.is_json:
            nuevo_estado = request.json.get('estado')
        else:
            nuevo_estado = request.form.get('estado')
        
        if nuevo_estado not in ['pendiente', 'preparando', 'listo', 'entregado']:
            return jsonify({'error': 'Estado no válido'}), 400
        
        pedido.estado = nuevo_estado
        db.session.commit()
        
        # Crear notificación si el pedido está listo
        if nuevo_estado == 'listo':
            notificacion = Notificacion(
                mensaje=f"Pedido #{pedido.id} listo para servir - Mesa {pedido.mesa or 'Sin asignar'}",
                tipo_destino='mesero',
                pedido_id=pedido.id,
                visto=False,
                fecha=datetime.utcnow()
            )
            db.session.add(notificacion)
            db.session.commit()
        
        return jsonify({'success': True, 'nuevo_estado': nuevo_estado})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al cambiar estado: {str(e)}'}), 500

# Public routes added by fix
@app.route('/menu', endpoint='menu')
def menu():
    categorias = Categoria.query.options(db.joinedload(Categoria.platos)).all()
    return render_template('menu.html', menu=categorias)


@app.route('/reservas', methods=['GET', 'POST'])
@login_required
def reservas():
    form = ReservaForm()
    # Determinar mesas ocupadas para la fecha/hora seleccionada
    mesas_todas = [
        ('1', 'Mesa 1 - Ventana'),
        ('2', 'Mesa 2 - Ventana'),
        ('3', 'Mesa 3 - Centro'),
        ('4', 'Mesa 4 - Centro'),
        ('5', 'Mesa 5 - Terraza'),
        ('6', 'Mesa 6 - Terraza'),
        ('7', 'Mesa 7 - Privada'),
        ('8', 'Mesa 8 - Privada')
    ]
    mesas_disponibles = mesas_todas
    if form.fecha.data and form.hora.data:
        try:
            fecha_reserva = datetime.strptime(f"{form.fecha.data} {form.hora.data}", "%Y-%m-%d %H:%M")
            ocupadas = Reserva.query.filter(
                Reserva.fecha == fecha_reserva,
                Reserva.estado != 'cancelada'
            ).with_entities(Reserva.mesa).all()
            ocupadas_set = set([m[0] for m in ocupadas if m[0]])
            mesas_disponibles = [(num, label) for num, label in mesas_todas if num not in ocupadas_set]
        except Exception:
            pass
    form.mesa.choices = [('', 'Sin preferencia')] + mesas_disponibles
    if form.validate_on_submit():
        try:
            fecha_reserva = datetime.strptime(f"{form.fecha.data} {form.hora.data}", "%Y-%m-%d %H:%M")
            if form.mesa.data:
                reserva_existente = Reserva.query.filter(
                    Reserva.fecha == fecha_reserva,
                    Reserva.mesa == form.mesa.data,
                    Reserva.estado != 'cancelada'
                ).first()
                if reserva_existente:
                    flash(f"La mesa {form.mesa.data} ya está reservada para esa hora", 'warning')
                    return redirect(url_for('reservas'))
            nueva_reserva = Reserva(
                fecha=fecha_reserva,
                personas=int(form.personas.data),
                mesa=form.mesa.data if form.mesa.data else None,
                comentarios=form.comentarios.data,
                usuario_id=current_user.id,
                estado='pendiente'
            )
            db.session.add(nueva_reserva)
            db.session.commit()
            flash('Reserva realizada con éxito!', 'success')
            return redirect(url_for('perfil', modo='editar'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al procesar la reserva: {str(e)}', 'danger')
    return render_template('reservas.html', form=form)

# Serve user profile images
@app.route('/user_images/<path:filename>', endpoint='serve_user_image')
def serve_user_image(filename):
    try:
        directory = app.config['UPLOAD_FOLDER_USERS']
        return send_from_directory(directory, filename)
    except Exception as e:
        # Fallback: return 404 if image not found
        return ("", 404)

# Empleado: Carrito del mesero
@app.route('/empleado/carro', endpoint='empleado_carrito')
@login_required
@tipo_empleado_requerido('mesero')
def empleado_carrito():
    # Obtener items del carrito del mesero actual
    items = CarritoItem.query.filter_by(usuario_id=current_user.id) \
        .join(Plato) \
        .options(db.joinedload(CarritoItem.plato).joinedload(Plato.categoria)) \
        .all()

    subtotal = sum(float(item.plato.precio) * item.cantidad for item in items)
    servicio = subtotal * 0.10
    total = subtotal + servicio

    # Calcular mesas disponibles similares al carrito de cliente
    todas_mesas = ['1','2','3','4','5','6','7','8']
    mesas_ocupadas = set([r.mesa for r in Reserva.query.filter(Reserva.mesa.isnot(None), Reserva.estado != 'cancelada').all()])
    mesas_pedidos = set([p.mesa for p in Pedido.query.filter(Pedido.estado=='pendiente').all() if p.mesa])
    mesas_disponibles = [m for m in todas_mesas if m not in mesas_ocupadas and m not in mesas_pedidos]

    return render_template(
        'empleado/carro.html',
        items=items,
        subtotal=subtotal,
        servicio=servicio,
        total=total,
        mesas_disponibles=mesas_disponibles
    )
    
    
#cambio de contraseña
class CambioPasswordForm(FlaskForm):
    password_actual = PasswordField('Contraseña actual', validators=[DataRequired()])
    nueva_password = PasswordField('Nueva contraseña', validators=[
        DataRequired(),
        Length(min=8, message="La contraseña debe tener al menos 8 caracteres")
    ])
    confirmar_password = PasswordField('Confirmar nueva contraseña', validators=[
        DataRequired(),
        EqualTo('nueva_password', message="Las contraseñas no coinciden")
    ])
    submit = SubmitField('Actualizar contraseña')


@app.route('/cambiar-contraseña', methods=['GET', 'POST'])
@login_required
def cambiar_contraseña():
    form = CambioPasswordForm()
    if form.validate_on_submit():
        # Verificar contraseña actual
        if not check_password_hash(current_user.password, form.password_actual.data):
            flash('La contraseña actual no es correcta', 'danger')
            return redirect(url_for('cambiar_contraseña'))

        # Guardar nueva contraseña
        current_user.password = generate_password_hash(form.nueva_password.data)
        try:
            db.session.commit()
            flash('Contraseña actualizada correctamente', 'success')
            return redirect(url_for('perfil'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la contraseña: {str(e)}', 'danger')

    return render_template('cambiar_contraseña.html', form=form)


#actualizar foto de perfil
@app.route('/actualizar-foto', methods=['POST'])
@login_required
def actualizar_foto():
    if 'foto' in request.files:
        foto = request.files['foto']
        if foto.filename != '':
            filename = secure_filename(foto.filename)
            # CORREGIR: Usar UPLOAD_FOLDER_USERS en lugar de UPLOAD_FOLDER
            ruta = os.path.join(app.config['UPLOAD_FOLDER_USERS'], filename)
            foto.save(ruta)
            current_user.foto = filename
            db.session.commit()
            flash("Foto actualizada correctamente", "success")
    return redirect(url_for('perfil'))

@app.route('/reserva/<int:id>/cancelar-cliente', methods=['POST'])
@login_required
def cancelar_reserva_cliente(id):
    reserva = Reserva.query.get_or_404(id)
    
    # Verificar que la reserva pertenece al usuario actual
    if reserva.usuario_id != current_user.id:
        flash('No tienes permiso para cancelar esta reserva', 'danger')
        return redirect(url_for('perfil', modo='editar'))
    
    try:
        # Verificar si la cancelación es con menos de 1 hora de anticipación
        ahora = datetime.utcnow()
        diferencia = reserva.fecha - ahora
        
        if diferencia.total_seconds() < 3600:  # Menos de 1 hora
            flash('Cancelación con menos de 1 hora de anticipación. Puede haber penalización.', 'warning')
        
        reserva.estado = 'cancelada'
        db.session.commit()
        
        flash('Reserva cancelada exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cancelar la reserva: {str(e)}', 'danger')
    
    return redirect(url_for('perfil', modo='editar'))

@app.route('/reserva/<int:id>/modificar', methods=['GET', 'POST'])
@login_required
def modificar_reserva_cliente(id):
    reserva = Reserva.query.get_or_404(id)
    
    # Verificar que la reserva pertenece al usuario actual
    if reserva.usuario_id != current_user.id:
        flash('No tienes permiso para modificar esta reserva', 'danger')
        return redirect(url_for('perfil', modo='editar'))
    
    form = ReservaForm(obj=reserva)
    
    # Pre-cargar los datos actuales
    if request.method == 'GET':
        form.fecha.data = reserva.fecha.date()
        form.hora.data = reserva.fecha.strftime('%H:%M')
        form.personas.data = str(reserva.personas)
        form.mesa.data = reserva.mesa or ''
        form.comentarios.data = reserva.comentarios or ''
    
    if form.validate_on_submit():
        try:
            fecha_reserva = datetime.strptime(f"{form.fecha.data} {form.hora.data}", "%Y-%m-%d %H:%M")
            
            # Verificar disponibilidad si se cambió la mesa
            if form.mesa.data and form.mesa.data != reserva.mesa:
                reserva_existente = Reserva.query.filter(
                    Reserva.fecha == fecha_reserva,
                    Reserva.mesa == form.mesa.data,
                    Reserva.estado != 'cancelada',
                    Reserva.id != reserva.id
                ).first()
                if reserva_existente:
                    flash(f"La mesa {form.mesa.data} ya está reservada para esa hora", 'warning')
                    return redirect(url_for('modificar_reserva_cliente', id=id))
            
            # Actualizar la reserva
            reserva.fecha = fecha_reserva
            reserva.personas = int(form.personas.data)
            reserva.mesa = form.mesa.data if form.mesa.data else None
            reserva.comentarios = form.comentarios.data
            
            db.session.commit()
            flash('Reserva modificada exitosamente', 'success')
            return redirect(url_for('perfil', modo='editar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al modificar la reserva: {str(e)}', 'danger')
    
    return render_template('reservas.html', form=form, modificar=True, reserva=reserva)

@app.route('/fix_category_typo')
def fix_category_typo():
    with app.app_context():
        categoria = Categoria.query.filter_by(nombre='Comodas rapidas').first()
        if categoria:
            categoria.nombre = 'Comidas rapidas'
            db.session.commit()
            return 'Typo fixed!'
        return 'Typo not found.'

def migrar_configuracion():
    """Migra la tabla configuracion para agregar las nuevas columnas"""
    try:
        # Verificar si las columnas ya existen
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('configuracion')]
        
        # Agregar columnas que no existen
        if 'reservas_dias_limpieza' not in columns:
            db.engine.execute('ALTER TABLE configuracion ADD COLUMN reservas_dias_limpieza INTEGER DEFAULT 30')
            print("Columna reservas_dias_limpieza agregada")
        
        if 'pedidos_dias_limpieza' not in columns:
            db.engine.execute('ALTER TABLE configuracion ADD COLUMN pedidos_dias_limpieza INTEGER DEFAULT 90')
            print("Columna pedidos_dias_limpieza agregada")
        
        if 'limpieza_automatica_activa' not in columns:
            db.engine.execute('ALTER TABLE configuracion ADD COLUMN limpieza_automatica_activa BOOLEAN DEFAULT 1')
            print("Columna limpieza_automatica_activa agregada")
        
        print("Migración de configuración completada exitosamente")
        
    except Exception as e:
        print(f"Error en migración: {str(e)}")
        # Si hay error, intentar crear la tabla desde cero
        try:
            db.drop_all()
            db.create_all()
            print("Tablas recreadas desde cero")
        except Exception as e2:
            print(f"Error al recrear tablas: {str(e2)}")

if __name__ == '__main__':    
    with app.app_context():
        db.create_all()  
        migrar_configuracion()  # Ejecutar migración
        agregar_datos_iniciales()  
        crear_admin_inicial() 
    app.run(debug=True)
