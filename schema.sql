
DROP DATABASE IF EXISTS restaurante;

CREATE DATABASE restaurante;

\c restaurante;

CREATE TABLE status_pedido (
  status     TEXT       PRIMARY KEY,
  description TEXT
);

INSERT INTO status_pedido(status, description) VALUES
  ('pendente',    'Pedido recebido, aguardando preparo'),
  ('em_preparo',  'Pedido em preparo'),
  ('pronto',      'Pedido pronto para entrega'),
  ('entregue',    'Pedido entregue ao cliente'),
  ('cancelado',   'Pedido cancelado')
ON CONFLICT DO NOTHING;


CREATE TABLE IF NOT EXISTS usuarios (
  id         SERIAL    PRIMARY KEY,
  name       TEXT      NOT NULL,
  email      TEXT      NOT NULL UNIQUE,
  password   TEXT      NOT NULL,
  role       TEXT      NOT NULL CHECK(role IN ('admin','cliente')),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS itens_cardapio (
  id          SERIAL    PRIMARY KEY,
  name        TEXT      NOT NULL,
  description TEXT,
  price       NUMERIC(8,2) NOT NULL CHECK(price >= 0),
  available   BOOLEAN   NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS estoque (
  item_id   INT   PRIMARY KEY
              REFERENCES itens_cardapio(id) ON DELETE CASCADE,
  quantity  INT   NOT NULL CHECK(quantity >= 0)
);

CREATE TABLE IF NOT EXISTS pedidos (
  id          SERIAL     PRIMARY KEY,
  cliente_id  INT        NOT NULL
                      REFERENCES usuarios(id),
  total       NUMERIC(10,2) NOT NULL DEFAULT 0
                      CHECK(total >= 0),
  status      TEXT       NOT NULL
                      REFERENCES status_pedido(status),
  created_at  TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS itens_pedido (
  id         SERIAL   PRIMARY KEY,
  pedido_id  INT      NOT NULL
                     REFERENCES pedidos(id)
                     ON DELETE CASCADE,
  item_id    INT      NOT NULL
                     REFERENCES itens_cardapio(id),
  quantidade INT      NOT NULL CHECK(quantidade > 0),
  price_at_momento NUMERIC(8,2) NOT NULL
                     CHECK(price_at_momento >= 0)
);

CREATE TABLE IF NOT EXISTS logs (
  id          SERIAL     PRIMARY KEY,
  pedido_id   INT        NOT NULL
                      REFERENCES pedidos(id)
                      ON DELETE CASCADE,
  action      TEXT       NOT NULL,
  action_time TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pedidos_status     ON pedidos(status);
CREATE INDEX IF NOT EXISTS idx_itens_pedido_pedido ON itens_pedido(pedido_id);

CREATE OR REPLACE FUNCTION validar_estoque()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.quantidade > (SELECT quantity FROM estoque WHERE item_id = NEW.item_id) THEN
    RAISE EXCEPTION 'Estoque insuficiente para o item %', NEW.item_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validar_estoque
BEFORE INSERT ON itens_pedido
FOR EACH ROW EXECUTE FUNCTION validar_estoque();

-- 9. descontar_estoque
CREATE OR REPLACE FUNCTION descontar_estoque()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE estoque SET quantity = quantity - NEW.quantidade
  WHERE item_id = NEW.item_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_descontar_estoque
AFTER INSERT ON itens_pedido
FOR EACH ROW EXECUTE FUNCTION descontar_estoque();

-- 10. validar_transicao_status
CREATE OR REPLACE FUNCTION validar_transicao_status()
RETURNS TRIGGER AS $$
BEGIN
  IF OLD.status IN ('entregue','cancelado') THEN
    RAISE EXCEPTION 'Não é possível alterar um pedido já %', OLD.status;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM (VALUES
      ('pendente','em_preparo'),
      ('em_preparo','pronto'),
      ('pronto','entregue'),
      ('pendente','cancelado'),
      ('em_preparo','cancelado'),
      ('pronto','cancelado')
    ) AS t(from_status,to_status)
    WHERE t.from_status = OLD.status AND t.to_status = NEW.status
  ) THEN
    RAISE EXCEPTION 'Transição inválida: % -> %', OLD.status, NEW.status;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validar_status
BEFORE UPDATE OF status ON pedidos
FOR EACH ROW EXECUTE FUNCTION validar_transicao_status();

-- 11. log_alteracao_pedido
CREATE OR REPLACE FUNCTION log_alteracao_pedido()
RETURNS TRIGGER AS $$
DECLARE action_desc TEXT;
BEGIN
  IF OLD.status <> NEW.status THEN
    action_desc := format('Pedido %s atualizado para "%s"', NEW.id, NEW.status);
  ELSE
    action_desc := format('Pedido %s atualizado', NEW.id);
  END IF;
  INSERT INTO logs(pedido_id, action) VALUES (NEW.id, action_desc);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_alteracao
AFTER UPDATE ON pedidos
FOR EACH ROW EXECUTE FUNCTION log_alteracao_pedido();

-- 12. log_cancelamento
CREATE OR REPLACE FUNCTION log_cancelamento()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status = 'cancelado' AND OLD.status <> 'cancelado' THEN
    INSERT INTO logs(pedido_id, action)
      VALUES (NEW.id, format('Pedido %s cancelado', NEW.id));
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_cancelamento
AFTER UPDATE OF status ON pedidos
FOR EACH ROW EXECUTE FUNCTION log_cancelamento();

-- 13. calcular_total_pedido
CREATE OR REPLACE FUNCTION calcular_total_pedido(p_pedido_id INT)
RETURNS NUMERIC AS $$
DECLARE v_total NUMERIC;
BEGIN
  SELECT COALESCE(SUM(quantidade * price_at_momento),0)
    INTO v_total
    FROM itens_pedido
    WHERE pedido_id = p_pedido_id;
  RETURN v_total;
END;
$$ LANGUAGE plpgsql;

-- 14. listar_pedidos
CREATE OR REPLACE FUNCTION listar_pedidos(p_status TEXT)
RETURNS TABLE(
  pedido_id INT,
  cliente_id INT,
  total NUMERIC,
  pedido_status TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
) AS $$
BEGIN
  RETURN QUERY SELECT p.id, p.cliente_id, p.total, p.status, p.created_at, p.updated_at FROM pedidos p WHERE p.status = p_status;
END;
$$ LANGUAGE plpgsql;

-- 15. trocar_status_pedido
CREATE OR REPLACE PROCEDURE trocar_status_pedido(p_pedido_id INT, p_novo_status TEXT)
LANGUAGE plpgsql AS $$
BEGIN
  UPDATE pedidos
    SET status = p_novo_status,
        updated_at = NOW()
    WHERE id = p_pedido_id;
END;
$$;

-- 16. registrar_pedido
CREATE OR REPLACE PROCEDURE registrar_pedido(p_cliente_id INT, p_itens JSONB)
LANGUAGE plpgsql AS $$
DECLARE
  v_pedido_id INT;
  v_item RECORD;
BEGIN
  INSERT INTO pedidos(cliente_id, status)
    VALUES (p_cliente_id, 'pendente')
    RETURNING id INTO v_pedido_id;

  FOR v_item IN
    SELECT * FROM jsonb_to_recordset(p_itens)
      AS x(item_id INT, quantidade INT)
  LOOP
    INSERT INTO itens_pedido(pedido_id, item_id, quantidade, price_at_momento)
      VALUES (
        v_pedido_id,
        v_item.item_id,
        v_item.quantidade,
        (SELECT price FROM itens_cardapio WHERE id = v_item.item_id)
      );
  END LOOP;

  UPDATE pedidos
    SET total = calcular_total_pedido(v_pedido_id),
        updated_at = NOW()
    WHERE id = v_pedido_id;
END;

$$;

INSERT INTO itens_cardapio (name, description, price, available) VALUES
  ('Pizza Margherita', 'Molho de tomate, mussarela, manjericão', 32.50, TRUE),
  ('Hambúrguer Artesanal', 'Pão brioche, hambúrguer 180g, queijo cheddar', 28.00, TRUE),
  ('Refrigerante', 'Lata 350ml', 6.00, TRUE);

  INSERT INTO usuarios (name, email, password, role) VALUES
  ('João Cliente', 'joao@email.com', 'senha123', 'cliente');

  INSERT INTO estoque (item_id, quantity) VALUES
  (1, 10), 
  (2, 10), 
  (3, 20)