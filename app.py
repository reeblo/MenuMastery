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

app = Flask(__name__)
app.config['SECRET_KEY'] = '12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'menumastery.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Modelos de la base de datos
class ReservaForm(FlaskForm):
    fecha = DateField('Fecha', format='%Y-%m-%d', validators=[DataRequired()])  # Añade esto
    hora = SelectField('Hora', choices=[
        ('12:00', '12:00 PM'),
        ('13:00', '1:00 PM'),
        ('14:00', '2:00 PM'),
        ('15:00', '3:00 PM'),
        ('18:00', '6:00 PM'),
        ('19:00', '7:00 PM'),
        ('20:00', '8:00 PM')
    ], validators=[DataRequired()])
    personas = IntegerField('Número de personas', validators=[DataRequired()])  # Añade esto
    comentarios = TextAreaField('Comentarios adicionales')  # Añade esto
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
    contraseña = db.Column(db.String(200), nullable=False)  # Usa solo un nombre (consistencia)

    # Propiedad para compatibilidad con Flask-Login
    @property
    def password(self):
        return self.contraseña

    @password.setter
    def password(self, value):
        self.contraseña = generate_password_hash(value)

class Plato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Float, nullable=False)
    imagen = db.Column(db.String(100))
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

# Añade este nuevo modelo para el historial
class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), default='pendiente')
    items = db.relationship('PedidoItem', backref='pedido', lazy=True)

class PedidoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    plato_id = db.Column(db.Integer, db.ForeignKey('plato.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    plato = db.relationship('Plato', backref='en_pedidos')

# Crear las tablas en la base de datos
with app.app_context():
    db.create_all()

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

# Llamar a la función para agregar datos iniciales
agregar_datos_iniciales()

# Rutas principales
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
    categorias = Categoria.query.all()
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


@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    resenas = Resena.query.filter_by(aprobado=True).order_by(Resena.fecha.desc()).limit(5).all()
    
    if request.method == 'POST':
        if 'enviar_resena' in request.form:  # Formulario de reseñas
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
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and check_password_hash(usuario.password, password):
            session['user_id'] = usuario.id
            session['user_nombre'] = usuario.nombre
            session['user_email'] = usuario.email
            
            # Completar reserva pendiente si existe
            if 'reserva_temp' in session:
                temp_reserva = session.pop('reserva_temp')
                return redirect(url_for('reservas'))
            
            flash('Inicio de sesión exitoso!', 'success')
            return redirect(url_for('inicio'))
        
        flash('Correo o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

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

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('inicio'))

# Rutas de usuario
@app.route('/mis_reservas')
def mis_reservas():
    if 'user_id' not in session:
        flash('Por favor inicia sesión para ver tus reservas', 'info')
        return redirect(url_for('login'))
    
    reservas = Reserva.query.filter_by(usuario_id=session['user_id']).order_by(Reserva.fecha.desc()).all()
    return render_template('mis_reservas.html', reservas=reservas)

# Manejo de errores
@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def error_servidor(e):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crea las tablas si no existen
        agregar_datos_iniciales()  # Ahora sí puedes usar queries
    app.run(debug=True)