from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.usuario.dao import UsuarioDAO

usuario_bp = Blueprint('usuario', __name__)

@usuario_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = UsuarioDAO.autenticar(email, senha)
        if usuario:
            session['usuario_id'] = usuario[0]
            session['nome'] = usuario[1]
            session['is_admin'] = usuario[3]
            return redirect(url_for('cardapio.cardapio'))
        else:
            flash('Login inválido!')
    return render_template('usuario/login.html')

@usuario_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('usuario.login'))
