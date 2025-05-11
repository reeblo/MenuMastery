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

def load_user(user_id):
    return Usuario.query.get(int(user_id))


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)

# Configuración de la base de datos SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'menumastery.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)  # ← Solo esta línea debe quedarse

# Modelos de la base de datos

class ReservaForm(FlaskForm):
    fecha = DateField('Fecha', validators=[DataRequired()])
    hora = TimeField('Hora', validators=[DataRequired()])
    personas = IntegerField('Número de personas', validators=[DataRequired()])
    comentarios = TextAreaField('Comentarios')
    nombre = StringField('Nombre', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    telefono = StringField('Teléfono', validators=[DataRequired()])
    submit = SubmitField('Confirmar Reserva')

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    contraseña = db.Column(db.String(200), nullable=False)

class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    descripcion = db.Column(db.String(200))

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


@app.route('/perfil')
def perfil():
    return render_template('perfil.html')

@app.route('/menu')
def menu():
    categorias = Categoria.query.all()
    return render_template('menu.html', menu=categorias)

@app.route('/reservas', methods=['GET', 'POST'])
def reservas():
    if request.method == 'POST':
        try:
            fecha_str = request.form['fecha']
            hora_str = request.form['hora']
            fecha_reserva = datetime.strptime(f"{fecha_str} {hora_str}", "%Y-%m-%d %H:%M")
            personas = int(request.form['personas'])
            
            if 'user_id' not in session:
                # Guardar datos de reserva temporalmente
                session['reserva_temp'] = {
                    'fecha': fecha_str,
                    'hora': hora_str,
                    'personas': personas,
                    'comentarios': request.form.get('comentarios', '')
                }
                flash('Por favor inicia sesión o regístrate para completar la reserva', 'info')
                return redirect(url_for('login'))
            
            nueva_reserva = Reserva(
                fecha=fecha_reserva,
                personas=personas,
                comentarios=request.form.get('comentarios', ''),
                usuario_id=session['user_id']
            )
            
            db.session.add(nueva_reserva)
            db.session.commit()
            
            flash('Reserva realizada con éxito!', 'success')
            return redirect(url_for('mis_reservas'))
        
        except Exception as e:
            db.session.rollback()
            flash('Error al procesar la reserva. Por favor intenta nuevamente.', 'danger')
    
    return render_template('reservas.html')

@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        if 'enviar_resena' in request.form:
            # Procesar reseña
            try:
                nueva_resena = Resena(
                    calificacion=int(request.form['rating']),
                    comentario=request.form['comentario'],
                    nombre=request.form.get('nombre', 'Anónimo'),
                    aprobado=False  # Las reseñas requieren aprobación
                )
                db.session.add(nueva_resena)
                db.session.commit()
                flash('Gracias por tu reseña! Será publicada después de ser aprobada.', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Error al enviar la reseña. Por favor intenta nuevamente.', 'danger')
        
        elif 'enviar_contacto' in request.form:
            # Procesar mensaje de contacto (simulado)
            flash('Mensaje enviado con éxito. Nos pondremos en contacto pronto!', 'success')
        
        return redirect(url_for('contacto.html'))
    
    # Obtener reseñas aprobadas
    resenas = Resena.query.filter_by(aprobado=True).order_by(Resena.fecha.desc()).limit(5).all()
    return render_template('contacto.html', resenas=resenas)

@app.route('/carrito')
def carrito():
    if 'user_id' not in session:
        flash('Por favor inicia sesión para ver tu carrito', 'info')
        return redirect(url_for('login'))
    
    items = CarritoItem.query.filter_by(usuario_id=session['user_id']).all()
    subtotal = sum(item.plato.precio * item.cantidad for item in items)
    total = subtotal + 2000  # Costo de envío fijo
    
    return render_template('carrocompras.html', items=items, subtotal=subtotal, total=total)

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