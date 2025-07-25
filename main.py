from flask import Flask, redirect, render_template, request, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, UserMixin, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import Markup
import os, re, datetime
app = Flask(__name__)
app.secret_key = 'f84c2a8ff832a0cb7f6f1983ed9b1e6a'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meubanco.db'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'capacitejaa@gmail.com'
app.config['MAIL_PASSWORD'] = 'xbvd jich mldl axfm'
db = SQLAlchemy(app)
lm = LoginManager(app)
lm.login_view = 'cadastroUsuario'
mail = Mail(app)

@lm.user_loader
def user_loader(id):
    return Usuario.query.get(int(id))

class Usuario (UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    userUsuario = db.Column(db.String(), nullable=False)
    emailUsuario = db.Column(db.String(100), nullable=True, unique=True)
    senhaUsuario = db.Column(db.String(), nullable=True)
    id_recuperacao = db.Column(db.String(), nullable=True)

class Posts(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    usuario = db.Column(db.String,nullable=False)
    mensagem = db.Column(db.String,nullable=False)
    arquivo = db.Column(db.String,nullable=True)
    extension_arquivo = db.Column(db.String,nullable=True)
    data_hora = db.Column(db.String,nullable=False)
    likes = db.Column(db.Integer,nullable=False)
    
class Likes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,nullable=True)
    post_id = db.Column(db.Integer, nullable=False)

    
with app.app_context():
    db.create_all()

def linkify(texto):
    texto = re.sub(
        r'(https?://[^\s]+)',
        r'<a href="\1" target="_blank">\1</a>',
        texto
    )

    texto = re.sub(
        r'\b(www\.[^\s]+)',
        r'<a href="http://\1" target="_blank">\1</a>',
        texto
    )
    return Markup(texto)

app.jinja_env.filters['linkify'] = linkify

@app.route('/', methods=['POST', 'GET'])
def register():
    usuarios = Usuario.query.all()
    return render_template('cadastro.html', usuarios=usuarios)

@app.route('/home')
def home():
    return render_template("index.html")

@app.route('/cursos', methods=['GET', 'POST'])
def cursos():
    posts = Posts.query.all()
    usuarios = Usuario.query.all()
    return render_template("cursos.html",posts=posts,usuarios=usuarios)

@app.route('/cursos/post', methods=['GET', 'POST'])
@login_required
def add():
    posts = Posts.query.all()
    usuarios = Usuario.query.all()
    if request.method == 'POST':
        usuario = current_user.userUsuario
        mensagem = request.form['posting']
        arquivo = request.files['arquivo']
        data_hora = str(datetime.date.today())
        if(arquivo):
            arquivo.save(os.path.join('static', arquivo.filename))
            nome_arquivo, extension_arquivo = os.path.splitext(arquivo.filename)
            db.session.add(Posts(usuario=usuario, mensagem=mensagem, arquivo=nome_arquivo, extension_arquivo=extension_arquivo, data_hora=data_hora, likes=0))
        else:
            db.session.add(Posts(usuario=usuario, mensagem=mensagem, data_hora=data_hora, likes=0))
        db.session.commit()
        return redirect('/cursos')
    return render_template("cursos.html",posts=posts,usuarios=usuarios)

@app.route('/cursos/download/<filename>')
def uploaded_file(filename):
    return send_from_directory('static', filename, as_attachment=False)

@app.route('/cursos/post/like/<id_post>', methods=['GET', 'POST'])
def like(id_post):
    if(request.method == 'POST'):
        id_post = int(id_post)
        user_id = current_user.id
        post = Posts.query.get_or_404(id_post)
        likes_register = Likes.query.filter_by(post_id=id_post, user_id=user_id).first()
        
        if likes_register is None:
            if request.form['like'] == "like":
                post.likes+=1
                db.session.add(Likes(user_id=user_id, post_id=id_post))
                db.session.commit()
        else:
            if request.form['like'] == "unlike":
                    post.likes-=1
                    db.session.delete(likes_register)
                    db.session.commit()
            
        return redirect('/cursos')
    return render_template("cursos.html", post=post, likes_register=likes_register)

@app.route('/artigos/<artigo>', methods=['GET'])
def gerenciar_artigos(artigo):
    artigo=artigo
    return render_template(artigo)

@app.route ('/redefinirSenha', methods=['GET'])
def redefinir():
    return render_template('esqueceuSenha.html')

@app.route ('/redefinirSenha/enviar_email', methods=['POST', 'GET'])
def enviar_email():
    if request.method == 'POST':
        if Usuario.query.filter_by(emailUsuario=request.form['email_AtualizarSenha']).first():
            msg = Message('Código de verificação requisitado',
            sender='capacitejaa@gmail.com',
            recipients=[request.form['email_AtualizarSenha']])
            msg.body = f'Seu código de verificação é: {123}'
            mail.send(msg)
            return redirect('/redefinirSenha/verificar_email')
        else:
            return render_template('esqueceuSenha.html',aviso2='Este email não se encontra no nosso banco de dados.')
    
    return render_template('esqueceuSenha.html')

@app.route ('/redefinirSenha/verificar_email', methods=['POST', 'GET'])
def verificar_email():
    if request.method == 'POST':
        if request.form['codigo'] == "123":
            return redirect('/redefinirSenha/mudar_senha')
        else:
            return render_template('verificar_email.html',aviso3='Código incorreto.')
    return render_template('verificar_email.html')

@app.route ('/redefinirSenha/mudar_senha', methods=['POST', 'GET'])
def mudar_senha():
    user = Usuario.query.get_or_404(current_user.id)
    if request.method == 'POST':
       nova_senha = request.form['nova_senha']
       user.senhaUsuario = generate_password_hash(nova_senha)
       db.session.commit()
       return redirect('/logar')
    return render_template('mudar_senha.html')

@app.route ('/ConferirId', methods=['GET', 'POST'])
def conferir():
    if request.method == 'POST':
        email_confirmacao = request.form['email_AtualizarSenha']
        id_Confirmacao = request.form['id_atualizarSenha']
        
        confirmar = db.session.query(Usuario).filter_by(emailUsuario=email_confirmacao).first()
        if confirmar and str(confirmar.id_recuperacao) == id_Confirmacao:
            return redirect(url_for('editar', usuario_id=confirmar.id))
        return render_template('esqueceuSenha.html', erro="ID ou email inválido")
        
    return render_template('esqueceuSenha.html')
 
@app.route('/editar/<int:usuario_id>', methods=['GET', 'POST'])

def editar(usuario_id):
   user = Usuario.query.get_or_404(usuario_id)
   
   if not user:
       return 'Usuário não encontrado', 404
   if request.method == 'POST':
       nova_senha = request.form['senhaNova']
       user.senhaUsuario = generate_password_hash(nova_senha)
       db.session.commit()
       return render_template('login.html')
   
   return render_template('editar.html', usuario=user)

@app.route('/cadastroUsuario', methods = ['GET', 'POST'])
def cadastrar():
    if request.method == 'POST' and not Usuario.query.filter_by(emailUsuario=request.form['email1']).first():
        
        userUsuario = request.form['user1']
        emailUsuario = request.form['email1']
        senhaUsuario = generate_password_hash(request.form['senha1'])
        id_recuperacao = request.form['atualizarSenha']
        
        novo_usuario = Usuario(userUsuario=userUsuario, emailUsuario=emailUsuario, senhaUsuario=senhaUsuario, id_recuperacao=id_recuperacao)
        db.session.add(novo_usuario)
        db.session.commit()
    else:
        return render_template('login.html',aviso='Esta conta já existe.')
        
        
        
    return render_template('login.html')
    

@app.route ('/logar', methods = ['GET', 'POST'])
def logar ():
    if request.method == 'GET':
        return render_template('login.html')
    
    if request.method == 'POST':
        username = request.form['user']
        senha =(request.form['senha'])
        
        user = db.session.query(Usuario).filter_by(userUsuario=username).first() #está buscando o usuário pelo email
        if user and check_password_hash(user.senhaUsuario, senha): #está comparando a senha do usuário
            login_user(user)
            return redirect('/home')
        
        else:
            return render_template('login.html',aviso='Credenciais incorretas.')

#Criar um botão para esse logout 
@app.route('/logout')
@login_required
def logout():
    logout_user()
    
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)