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

app = Flask(__name__)
app.config['SECRET_KEY'] = '12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'menumastery.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
csrf = CSRFProtect(app)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

UPLOAD_FOLDER = os.path.join('static', 'img', 'platos')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB máximo


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])  # Cambiado de username a email
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar sesión')

# Modelos de la base de datos
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

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), default='usuario')  # 'usuario' o 'admin'
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

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

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
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

# Crear las tablas en la base de datos
with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#creacion de usuario admin
def crear_admin_inicial():
    with app.app_context():
        if not Usuario.query.filter_by(email='admin@menumastery.com').first():
            admin = Usuario(
                nombre='Administrador',
                email='admin@menumastery.com',
                password=generate_password_hash('Admin123'),
                rol='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Usuario admin creado: admin@menumastery.com / Admin123")

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
            # Validar que se haya subido una imagen si es requerido
            imagen = request.files.get('imagen')
            if not imagen or imagen.filename == '':
                flash('Debe seleccionar una imagen para el plato', 'danger')
                return redirect(url_for('agregar_plato'))
            
            if not allowed_file(imagen.filename):
                flash('Formato de imagen no permitido. Use: PNG, JPG, JPEG o GIF', 'danger')
                return redirect(url_for('agregar_plato'))
            
            # Procesar la imagen
            filename = secure_filename(imagen.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            imagen.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
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
    try:
        # Eliminar la imagen asociada si existe
        if plato.imagen:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], plato.imagen))
            except Exception as e:
                print(f"Error al eliminar imagen: {str(e)}")
        
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


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))



@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/enviar-resena', methods=['POST'])
def enviar_resena():
    # Código para guardar la reseña
    return redirect(url_for('mis_reservas'))  # o a donde quieras redirigir



@app.route('/perfil')
def perfil():
    return render_template('perfil.html')

@app.route('/menu')
def menu():
    categorias = Categoria.query.options(db.joinedload(Categoria.platos)).all()
    return render_template('menu.html', menu=categorias)

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

@app.route('/carrito', methods=['GET', 'POST'])
def carrito():
    if 'user_id' not in session:
        flash('Por favor inicia sesión para ver tu carrito', 'info')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Procesar el pago y crear el pedido
        items = CarritoItem.query.filter_by(usuario_id=session['user_id']).all()
        
        if not items:
            flash('Tu carrito está vacío', 'warning')
            return redirect(url_for('carrito'))
        
        try:
            # Crear el pedido
            total = sum(item.plato.precio * item.cantidad for item in items) + 2000  # + envío
            nuevo_pedido = Pedido(
                usuario_id=session['user_id'],
                total=total,
                estado='completado' if request.form.get('payment_type') == 'online' else 'pendiente'
            )
            db.session.add(nuevo_pedido)
            db.session.flush()  # Para obtener el ID del pedido
            
            # Crear los items del pedido
            for item in items:
                pedido_item = PedidoItem(
                    pedido_id=nuevo_pedido.id,
                    plato_id=item.plato_id,
                    cantidad=item.cantidad,
                    precio_unitario=item.plato.precio
                )
                db.session.add(pedido_item)
                # Eliminar del carrito
                db.session.delete(item)
            
            db.session.commit()
            flash('Pedido realizado con éxito!', 'success')
            return redirect(url_for('historial_compras'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al procesar el pedido: {str(e)}', 'danger')
    
    # GET request
    items = CarritoItem.query.filter_by(usuario_id=session['user_id']).all()
    subtotal = sum(item.plato.precio * item.cantidad for item in items)
    total = subtotal + 2000  # Costo de envío fijo
    
    # Obtener historial de pedidos
    pedidos = Pedido.query.filter_by(usuario_id=session['user_id'])\
                        .order_by(Pedido.fecha.desc()).all()
    
    return render_template('carrocompras.html', 
                        cart_items=items,
                        pedidos=pedidos,
                        subtotal=subtotal, 
                        total=total)

@app.route('/historial')
def historial_compras():
    if 'user_id' not in session:
        flash('Por favor inicia sesión para ver tu historial', 'info')
        return redirect(url_for('login'))
    
    pedidos = Pedido.query.filter_by(usuario_id=session['user_id'])\
                        .order_by(Pedido.fecha.desc()).all()
    return render_template('historial.html', pedidos=pedidos)

# Rutas de autenticación
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('inicio'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            
            # Redirección basada en rol
            if user.rol == 'admin':
                return redirect(url_for('admin_panel'))
            return redirect(url_for('inicio'))
        
        flash('Credenciales incorrectas', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validaciones básicas
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('registro'))
        
        if Usuario.query.filter_by(email=email).first():
            flash('Este correo ya está registrado', 'danger')
            return redirect(url_for('registro'))
        
        try:
            nuevo_usuario = Usuario(
                nombre=nombre,
                email=email,
                password=generate_password_hash(password)
            )
            
            db.session.add(nuevo_usuario)
            db.session.commit()
            
            flash('Registro exitoso! Por favor inicia sesión', 'success')
            return redirect(url_for('login'))
        
        except Exception as e:
            db.session.rollback()
            flash('Error al registrar el usuario. Por favor intenta nuevamente.', 'danger')
    
    return render_template('registro.html')

from flask_login import logout_user

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



@app.route('/admin/productos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    if current_user.rol != 'admin':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    plato = Plato.query.get_or_404(id)
    form = PlatoForm(obj=plato)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(plato)
            db.session.commit()
            flash('Producto actualizado exitosamente!', 'success')
            return redirect(url_for('admin_productos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar producto: {str(e)}', 'danger')
    
    return render_template('admin/editar_producto.html', form=form, plato=plato)

@app.route('/admin/productos/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_producto(id):
    if current_user.rol != 'admin':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('inicio'))
    
    plato = Plato.query.get_or_404(id)
    try:
        db.session.delete(plato)
        db.session.commit()
        flash('Producto eliminado exitosamente!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar producto: {str(e)}', 'danger')
    
    return redirect(url_for('admin_productos'))

if __name__ == '__main__':    
    with app.app_context():
        db.create_all()  
        agregar_datos_iniciales()  
        crear_admin_inicial() 
    app.run(debug=True) 