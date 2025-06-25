from flask import Blueprint, render_template, request, redirect, url_for
from app.pedido.dao import PedidoDAO

pedido_bp = Blueprint('pedido', __name__)

@pedido_bp.route('/admin')
def painel_admin():
    status_filtro = request.args.get('status', '')
    pedidos = PedidoDAO.listar_pedidos(status_filtro)
    return render_template('pedido/painel_admin.html', pedidos=pedidos)

@pedido_bp.route('/admin/detalhes/<int:pedido_id>')
def detalhes_pedido(pedido_id):
    detalhes = PedidoDAO.detalhar_pedido(pedido_id)
    return render_template('pedido/detalhes_pedido.html', pedido=detalhes)

@pedido_bp.route('/admin/atualizar_status', methods=['POST'])
def atualizar_status():
    pedido_id = request.form.get('pedido_id', type=int)
    novo_status = request.form.get('status')
    PedidoDAO.atualizar_status(pedido_id, novo_status)
    return redirect(url_for('pedido.painel_admin'))