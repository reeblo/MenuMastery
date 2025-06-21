from flask import Flask, render_template, request, redirect, url_for, flash, session
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

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'img', 'platos')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])  
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar sesión')

class RolUsuario(Enum):
    ADMIN = 'admin'
    COCINERO = 'cocinero'
    MESERO = 'mesero'
    CLIENTE = 'cliente'

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), default= RolUsuario.CLIENTE.value) 
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    foto = db.Column(db.String(200), default='default.png')

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
    personas = IntegerField('Número de personas', validators=[DataRequired()])  
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
    imagen = StringField('Nombre de la imagen (ej: plato1.jpg)')
    destacado = SelectField('Destacado', choices=[(False, 'No'), (True, 'Sí')], coerce=bool)
    categoria_id = SelectField('Categoría', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Guardar Plato')

class Plato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Float, nullable=False)
    imagen = db.Column(db.String(255))  # Unificado en un solo campo
    destacado = db.Column(db.Boolean, default=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    categoria = db.relationship('Categoria', backref='platos') 

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    mesa = db.Column(db.String(20)) 
    total = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), default='pendiente')
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.relationship('Usuario', backref='pedidos')

class PedidoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    plato_id = db.Column(db.Integer, db.ForeignKey('plato.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    plato = db.relationship('Plato')
    pedido = db.relationship('Pedido', backref='items')

class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False)
    personas = db.Column(db.Integer, nullable=False)
    comentarios = db.Column(db.Text)
    estado = db.Column(db.String(20), default='pendiente')
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
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

# crear tablas si no existen
with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
                rol=RolUsuario.COCINERO.value
            )
            db.session.add(cocinero)
        
        # Mesero
        if not Usuario.query.filter_by(email='mesero@menumastery.com').first():
            mesero = Usuario(
                nombre='Mesero',
                email='mesero@menumastery.com',
                password=generate_password_hash('Mesero123'),
                rol=RolUsuario.MESERO.value
            )
            db.session.add(mesero)
        db.session.commit()
        print("Usuarios iniciales creados:")
        print("- Cocinero: cocinero@menumastery.com / Cocinero123")
        print("- Mesero: mesero@menumastery.com / Mesero123")

#modulo administrador
@app.route('/admin/panel')
@login_required
def admin_panel():
    if not current_user.is_authenticated or current_user.rol != 'admin':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    # Agregar estadísticas
    total_usuarios = Usuario.query.count()
    pedidos_hoy = Pedido.query.filter(Pedido.fecha >= datetime.today().date()).count()
    productos_inventario = Plato.query.count()
    reservas_activas = Reserva.query.filter(Reserva.fecha >= datetime.now()).count()
    
    return render_template('admin/base.html', 
                        total_usuarios=total_usuarios,
                        pedidos_hoy=pedidos_hoy,
                        productos_inventario=productos_inventario,
                        reservas_activas=reservas_activas)

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
            # Validar que se haya subido unUPLOAD_FOLDER = os.path.join('static', 'img', 'platos')a imagen si es requerido
            imagen = request.files.get('imagen')
            if not imagen or imagen.filename == '':
                flash('Debe seleccionar una imagen para el plato', 'danger')
                return redirect(url_for('agregar_plato'))
            
            if not allowed_file(imagen.filename):
                flash('Formato de imagen no permitido. Use: PNG, JPG, JPEG o GIF', 'danger')
                return redirect(url_for('agregar_plato'))
            
            # Procesar la imagen
            filename = secure_filename(imagen.filename)
            try:
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            except OSError as e:
                flash(f'Error al crear carpeta de imagenes: {str(e)}', 'danger')
                return redirect(url_for('agregar_plato'))
            
            # Crear el plato
            nuevo_plato = Plato(
                nombre=form.nombre.data,
                descripcion=form.descripcion.data,
                precio=form.precio.data,
                imagen=filename,
                destacado=form.destacado.data,
                categoria_id=form.categoria_id.data
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
            # Procesar imagen si se subió una nueva
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
            plato.destacado = form.destacado.data
            plato.categoria_id = form.categoria_id.data
            
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

# Funciones de ayuda
def agregar_datos_iniciales():
    with app.app_context():  # ¡Contexto crítico aquí!
        if not Categoria.query.first():
            categorias = [
                Categoria(nombre="Desayunos"),
                Categoria(nombre="Almuerzos"),
                # ... más datos
            ]
            db.session.add_all(categorias)
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
                return redirect(url_for('index'))
            return func(*args, **kwargs)
        return envoltura
    return decorador

#modulo del cocinero
@app.route('/cocinero/pedidos')
@login_required
@rol_requerido(RolUsuario.COCINERO.value)
def cocinero_pedidos():
    pedidos = Pedido.query.filter_by(estado='pendiente').order_by(Pedido.fecha.asc()).all()
    return render_template('cocinero/pedidos.html', pedidos=pedidos)


@app.route('/pedido/<int:id>/completar', methods=['POST'])
@login_required
def completar_pedido(id):
    if current_user.rol != RolUsuario.COCINERO.value:
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    pedido = Pedido.query.get_or_404(id)
    pedido.estado = 'listo'
    db.session.commit()
    flash('Pedido marcado como listo para servir', 'success')
    return redirect(url_for('cocinero_pedidos'))

#modulo del mesero
@app.route('/mesero/pedidos')
@login_required
@rol_requerido(RolUsuario.MESERO.value)
def mesero_pedidos():
    pedidos = Pedido.query.filter_by(estado='listo').order_by(Pedido.fecha.asc()).all()
    return render_template('mesero/pedidos.html', pedidos=pedidos)

@app.route('/pedido/<int:id>/entregar', methods=['POST'])
@login_required
def entregar_pedido(id):
    if current_user.rol != RolUsuario.MESERO.value:
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    pedido = Pedido.query.get_or_404(id)
    pedido.estado = 'completado'
    db.session.commit()
    flash('Pedido marcado como entregado', 'success')
    return redirect(url_for('mesero_pedidos'))

#stream de pedidos para mesero y coinero
@app.route('/stream-pedidos')
@login_required
def stream_pedidos():
    def event_stream():
        last_count = 0
        while True:
            if current_user.rol == RolUsuario.COCINERO.value:
                count = Pedido.query.filter_by(estado='pendiente').count()
            elif current_user.rol == RolUsuario.MESERO.value:
                count = Pedido.query.filter_by(estado='listo').count()
            else:
                break
            
            if count != last_count:
                yield f"data: {count}\n\n"
                last_count = count
            time.sleep(2)

    return Response(event_stream(), mimetype="text/event-stream")

# Enrutación inicial
@app.route('/')
def inicio():
    return render_template('index.html')

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

#modulo de reseñas
@app.route('/enviar-resena', methods=['POST'])
def enviar_resena():
    # Código para guardar la reseña
    return redirect(url_for('mis_reservas'))  # o a donde quieras redirigir

#modulo de perfil
@app.route('/perfil')
@login_required
def perfil():
    modo = request.args.get('modo', 'ver')
    return render_template('perfil.html', modo=modo)

@app.route('/perfil/actualizar', methods=['POST'])
@login_required
def actualizar_perfil():
    current_user.nombre = request.form['nombre']
    current_user.email = request.form['email']

    foto = request.files.get('foto')
    if foto and foto.filename != '':
        filename = secure_filename(foto.filename)
        ruta = os.path.join('static/perfiles', filename)
        foto.save(ruta)
        current_user.foto = filename

    db.session.commit()
    flash('Datos actualizados con éxito')
    return redirect(url_for('perfil'))


#modulo de menu
@app.route('/menu')
def menu():
    categorias = Categoria.query.options(db.joinedload(Categoria.platos)).all()
    return render_template('menu.html', menu=categorias)

#modulo de reservas
@app.route('/reservas', methods=['GET', 'POST'])
def reservas():
    form = ReservaForm()  # Crea una instancia del formulario
    
    if form.validate_on_submit():  # Esto reemplaza request.method == 'POST'
        try:
            fecha_reserva = datetime.strptime(
                f"{form.fecha.data} {form.hora.data}", 
                "%Y-%m-%d %H:%M"
            )
            
            if 'user_id' not in session:
                session['reserva_temp'] = {
                    'fecha': form.fecha.data.strftime('%Y-%m-%d'),
                    'hora': form.hora.data.strftime('%H:%M'),
                    'personas': form.personas.data,
                    'comentarios': form.comentarios.data
                }
                flash('Por favor inicia sesión o regístrate para completar la reserva', 'info')
                return redirect(url_for('login'))
            
            nueva_reserva = Reserva(
                fecha=fecha_reserva,
                personas=form.personas.data,
                comentarios=form.comentarios.data,
                usuario_id=session['user_id']
            )
            
            db.session.add(nueva_reserva)
            db.session.commit()
            
            flash('Reserva realizada con éxito!', 'success')
            return redirect(url_for('mis_reservas'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al procesar la reserva: {str(e)}', 'danger')
    
    return render_template('reservas.html', form=form)  # Pasa el formulario a la plantilla 

#modulo de contacto
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
                flash('Gracias por tu reseña! Será publicada después de ser aprobada.', 'success')
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
    
    items = CarritoItem.query.filter_by(usuario_id=current_user.id)\
                        .join(Plato)\
                        .order_by(Plato.nombre).all()
    
    #cualculo de totales
    subtotal = sum(item.plato.precio * item.cantidad for item in items)
    envio = 2000
    total = subtotal + envio

    return render_template('carrocompras.html',
                        cart_items=items,
                        subtotal=subtotal,
                        envio=envio,
                        total=total)

@app.route('/carrito/agregar/<int:plato_id>', methods=['POST'])
@login_required
def agregar_al_carrito(plato_id):
    plato = Plato.query.get_or_404(plato_id)
    item_existente = CarritoItem.query.filter_by(
        usuario_id=current_user.id,
        plato_id=plato_id
    ).first()

    try:
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
        flash(f'"{plato.nombre}" agregado al carrito', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al agregar al carrito', 'danger')
    
    return redirect(request.referrer or url_for('menu'))

@app.route('/carrito/actualizar/<int:item_id>', methods=['POST'])
@login_required
def actualizar_carrito(item_id):
    data = request.get_json()
    item = CarritoItem.query.filter_by(
        id=item_id,
        usuario_id=current_user.id
    ).first_or_404()

    try:
        item.cantidad = int(data['cantidad'])
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/carrito/eliminar/<int:item_id>', methods=['POST'])
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
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
@login_required

@app.route('/carrito/vaciar', methods=['POST'])
def vaciar_carrito():
    try:
        CarritoItem.query.filter_by(usuario_id=current_user.id).delete()
        db.session.commit()
        flash('Carrito vaciado correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al vaciar el carrito', 'danger')
    
    return redirect(url_for('carrito'))

# Funciones auxiliares
def procesar_pedido():
    items = CarritoItem.query.filter_by(usuario_id=current_user.id).all()
    
    if not items:
        flash('Tu carrito está vacío', 'warning')
        return redirect(url_for('carrito'))
    
    try:
        # Calcular totales
        subtotal = sum(item.plato.precio * item.cantidad for item in items)
        envio = 2000  # Costo fijo de envío
        total = subtotal + envio

        # Crear pedido
        nuevo_pedido = Pedido(
            usuario_id=current_user.id,
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
        
        if request.form.get('payment_type') == 'online':
            return iniciar_pago_online(nuevo_pedido)
        else:
            flash('Pedido realizado con éxito!', 'success')
            return redirect(url_for('historial_compras'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error al procesar el pedido: {str(e)}', 'danger')
        return redirect(url_for('carrito'))

@app.route('/historial')
def historial_compras():
    if 'user_id' not in session:
        flash('Por favor inicia sesión para ver tu historial', 'info')
        return redirect(url_for('login'))
    
    pedidos = Pedido.query.filter_by(usuario_id=session['user_id'])\
                        .order_by(Pedido.fecha.desc()).all()
    return render_template('historial.html', pedidos=pedidos)

#perfil de usuario.
@app.route('/perfil/foto', methods=['POST'])
@login_required
def subir_foto():
    file = request.files.get('foto')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Actualiza en la base de datos
        current_user.foto = f'uploads/{filename}'
        db.session.commit()

        flash('Foto actualizada con éxito')
    else:
        flash('Formato de imagen no permitido')
    return redirect(url_for('perfil'))

@app.route('/perfil/actualizar', methods=['POST'])
@login_required
def actualizar_datos():
    nuevo_nombre = request.form.get('nombre')
    nuevo_email = request.form.get('email')

    if not nuevo_nombre or not nuevo_email:
        flash('Todos los campos son obligatorios.', 'warning')
        return redirect(url_for('perfil'))

    current_user.nombre = nuevo_nombre
    current_user.email = nuevo_email
    db.session.commit()

    flash('Datos actualizados con éxito.', 'success')
    return redirect(url_for('perfil'))

# modulo de login/Rutas de autenticación
#registro 
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    form = RegistroForm()  # Usa el formulario Flask-WTF
    
    if form.validate_on_submit():
        # Validar que los emails coincidan
        if form.email.data != form.confirm_email.data:
            flash('Los emails no coinciden', 'danger')
            return redirect(url_for('registro'))
            
        # Validar que las contraseñas coincidan
        if form.password.data != form.confirm_password.data:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('registro'))
            
        # Verificar si el email ya existe
        if Usuario.query.filter_by(email=form.email.data).first():
            flash('Este correo ya está registrado', 'danger')
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
        elif current_user.rol == RolUsuario.COCINERO.value:
            return redirect(url_for('cocinero_pedidos'))
        elif current_user.rol == RolUsuario.MESERO.value:
            return redirect(url_for('mesero_pedidos'))
        return redirect(url_for('inicio'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            
            # Redirección basada en rol
            if user.rol == RolUsuario.ADMIN.value:
                return redirect(url_for('admin_panel'))
            elif user.rol == RolUsuario.COCINERO.value:
                return redirect(url_for('cocinero_pedidos'))
            elif user.rol == RolUsuario.MESERO.value:
                return redirect(url_for('mesero_pedidos'))
            return redirect(url_for('inicio'))
            
        
        flash('Credenciales incorrectas', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/carrito/confirmar', methods=['POST'])
@login_required
def confirmar_pedido():
    # 1. Crear el pedido en la base de datos
    nuevo_pedido = Pedido(
        usuario_id=current_user.id,
        estado='pendiente',  # Estado inicial para que el cocinero lo vea
        # ... otros campos
    )
    db.session.add(nuevo_pedido)
    db.session.commit()

    # 2. Notificar a cocineros/meseros (vía SSE o WebSocket)
    # (Se implementa en el paso 3 del plan anterior)
    return redirect(url_for('historial_compras'))

# cierre de sesion
@app.route('/logout')
def logout():
    logout_user()
    session.clear()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('inicio'))

# Rutas de usuario
@app.route('/mis_reservas')
def mis_reservas():
    if 'user_id' not in session:
        flash('Por favor inicia sesión para ver tus reservas', 'info')
        return redirect(url_for('login'))
    
    reservas = Reserva.query.filter_by(usuario_id=session['user_id']).order_by(Reserva.fecha.desc()).all()
    return render_template('mis_reservas.html', reservas=reservas)

if __name__ == '__main__':    
    with app.app_context():
        db.create_all()  
        agregar_datos_iniciales()  
        crear_admin_inicial() 
    app.run(debug=True) 