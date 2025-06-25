from flask import Blueprint, render_template, request, redirect, url_for
from app.cardapio.dao import ItemCardapioDAO
from app.pedido.dao import PedidoDAO
from app.db import get_connection
import json

cardapio_bp = Blueprint('cardapio', __name__)

@cardapio_bp.route('/')
def cardapio():
    conn = get_connection()
    dao = ItemCardapioDAO(conn)
    itens = dao.listar_itens_disponiveis()
    conn.close()
    return render_template('cardapio/cardapio.html', itens=itens)
@cardapio_bp.route('/pedido/novo')
def novo_pedido():
    conn = get_connection()
    dao = ItemCardapioDAO(conn)
    itens = dao.listar_itens_disponiveis()
    conn.close()
    return render_template('pedido/novo_pedido.html', itens=itens)

@cardapio_bp.route('/pedido/registrar', methods=['POST'])
def registrar_pedido():
    cliente_id = 1  # fixo por enquanto
    itens = []
    for item_id in request.form.getlist("item_id"):
        quantidade = request.form.get(f"quantidade_{item_id}", type=int)
        if quantidade and quantidade > 0:
            itens.append({"item_id": int(item_id), "quantidade": quantidade})

    conn = get_connection()
    pedido_dao = PedidoDAO(conn)
    pedido_dao.registrar(cliente_id, itens)
    conn.close()

    return redirect(url_for('cardapio.cardapio'))