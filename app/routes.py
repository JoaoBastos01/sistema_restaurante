# app/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
import json
import psycopg2
from psycopg2 import extras

main_bp = Blueprint('main', __name__)

def conectar():
    return psycopg2.connect(
        dbname='restaurante',
        user='postgres',
        password='1234',
        host='localhost'
    )

# ← ROTA PARA A PÁGINA INICIAL (HERÓI)
@main_bp.route('/')
def index():
    return render_template('index.html')


# ← ROTA EXISTENTE: LISTAR CARDÁPIO
@main_bp.route('/cardapio')
def cardapio():
    # Supondo que aqui você já tenha lógica para buscar itens do cardápio
    conn = conectar()
    cur = conn.cursor(cursor_factory=extras.DictCursor)
    cur.execute("SELECT * FROM itens_cardapio ORDER BY nome")
    itens = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('cardapio.html', itens=itens)


# ← ROTA EXISTENTE: CRIAR NOVO PEDIDO
@main_bp.route('/novo_pedido', methods=['GET', 'POST'])
def novo_pedido():
    conn = conectar()
    cur = conn.cursor(cursor_factory=extras.DictCursor)

    if request.method == 'POST':
        try:
            # O HTML enviará algo como:
            # item_id: [1, 2, 3]
            # quantidade_1: 2
            # quantidade_2: 1
            # quantidade_3: 0
            cliente_id = request.form.get('cliente_id')
            # Lista para armazenar pares (item_id, quantidade)
            itens_pedido = []

            # Percorre a lista de IDs de item enviada pelo formulário
            for item_id_str in request.form.getlist('item_id'):
                item_id = int(item_id_str)
                quantidade = int(request.form.get(f'quantidade_{item_id}', 0))
                # Apenas insere no pedido se quantidade > 0
                if quantidade > 0:
                    itens_pedido.append({
                        'item_id': item_id,
                        'quantidade': quantidade
                    })

            # Se não houver nenhum item, volta com erro
            if not itens_pedido:
                flash('Você deve escolher pelo menos um item com quantidade maior que zero.', 'error')
                # Recarrega o GET com todos os itens
                cur.execute("SELECT * FROM itens_cardapio ORDER BY nome;")
                itens = cur.fetchall()
                return render_template('novo_pedido.html', itens=itens)

            # Chama a stored procedure registrar_pedido
            # Transformamos itens_pedido em JSON string para o PL/pgSQL consumir
            cur.execute("SELECT registrar_pedido(%s, %s);", 
                        (cliente_id, json.dumps(itens_pedido)))
            conn.commit()
            flash('Pedido registrado com sucesso!', 'success')
            return redirect(url_for('main.cardapio'))

        except Exception as e:
            conn.rollback()
            flash(f'Erro ao registrar pedido: {str(e)}', 'error')
            # Recarrega o GET
            cur.execute("SELECT * FROM itens_cardapio ORDER BY nome;")
            itens = cur.fetchall()
            return render_template('novo_pedido.html', itens=itens)
        finally:
            cur.close()
            conn.close()

    # Se for GET, apenas mostra o formulário
    cur.execute("SELECT * FROM itens_cardapio ORDER BY nome;")
    itens = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('novo_pedido.html', itens=itens)

@main_bp.route('/painel_admin')
def painel_admin():
    # Exemplo: aceita querystring ?status=em preparo
    status_filtro = request.args.get('status', 'em_preparo')
    conn = conectar()
    cur = conn.cursor(cursor_factory=extras.DictCursor)
    cur.execute("SELECT * FROM listar_pedidos(%s);", (status_filtro,))  
    # listar_pedidos pode ser a função/stored procedure que retorna pedidos por status
    pedidos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('painel_admin.html', pedidos=pedidos, status_atual=status_filtro)

@main_bp.route('/detalhes_pedido/<int:pedido_id>')
def detalhes_pedido(pedido_id):
    conn = conectar()
    cur = conn.cursor(cursor_factory=extras.DictCursor)

    # 1) Buscar dados básicos do pedido (JOIN com cliente, tabela pedidos)
    cur.execute("""
      SELECT p.id,
             u.nome AS cliente_nome,
             p.data_hora,
             p.status,
             calcular_total_pedido(p.id) AS total
      FROM pedidos p
      JOIN usuarios u ON u.id = p.cliente_id
      WHERE p.id = %s;
    """, (pedido_id,))
    pedido = cur.fetchone()

    if not pedido:
        cur.close()
        conn.close()
        flash('Pedido não encontrado.', 'error')
        return redirect(url_for('main.painel_admin'))

    # 2) Buscar itens do pedido (JOIN com itens_cardapio)
    cur.execute("""
      SELECT ic.nome AS item_nome,
             ic.preco AS preco_unitario,
             ip.quantidade
      FROM itens_pedido ip
      JOIN itens_cardapio ic ON ic.id = ip.item_id
      WHERE ip.pedido_id = %s;
    """, (pedido_id,))
    itens = cur.fetchall()

    # 3) Buscar histórico de logs (opcional, se você tiver trigger que grava logs em logs)
    cur.execute("""
      SELECT l.acao,
             l.data_hora
      FROM logs l
      WHERE l.pedido_id = %s
      ORDER BY l.data_hora DESC;
    """, (pedido_id,))
    logs = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('detalhes_pedido.html', pedido=pedido, itens=itens, logs=logs)

@main_bp.route('/trocar_status_pedido', methods=['POST'])
def trocar_status_pedido():
    pedido_id = request.form.get('pedido_id')
    novo_status = request.form.get('novo_status')
    try:
        conn = conectar()
        cur = conn.cursor()
        # Chama sua stored procedure que valida transições válidas
        cur.execute("SELECT trocar_status_pedido(%s, %s);", (pedido_id, novo_status))
        conn.commit()
        cur.close()
        conn.close()
        flash('Status alterado com sucesso.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao alterar status: {str(e)}', 'error')
    return redirect(request.referrer or url_for('main.painel_admin'))

@main_bp.route('/cancelar_pedido', methods=['POST'])
def cancelar_pedido():
    pedido_id = request.form.get('pedido_id')
    try:
        conn = conectar()
        cur = conn.cursor()
        # Supondo que você tenha uma procedure cancelamento que marca como “cancelado”
        cur.execute("SELECT cancelar_pedido(%s);", (pedido_id,))
        conn.commit()
        cur.close()
        conn.close()
        flash('Pedido cancelado com sucesso.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao cancelar pedido: {str(e)}', 'error')
    return redirect(request.referrer or url_for('main.painel_admin'))