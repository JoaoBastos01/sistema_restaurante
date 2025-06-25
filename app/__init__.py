from flask import Flask
from .config import Config
from app.cardapio.routes import cardapio_bp
from app.pedido.routes import pedido_bp
from app.usuario.routes import usuario_bp
from app.main import main_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = "BS_Enterprises"
    
    app.register_blueprint(main_bp)
    app.register_blueprint(cardapio_bp)
    app.register_blueprint(pedido_bp)
    app.register_blueprint(usuario_bp)
    
    return app