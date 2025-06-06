
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL
);

CREATE TABLE itens_cardapio (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    preco NUMERIC(10, 2) NOT NULL
);

CREATE TABLE estoque (
    item_id INTEGER PRIMARY KEY REFERENCES itens_cardapio(id),
    quantidade INTEGER NOT NULL CHECK (quantidade >= 0)
);

CREATE TABLE status_pedido (
    id SERIAL PRIMARY KEY,
    status TEXT NOT NULL UNIQUE
);

CREATE TABLE pedidos (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES usuarios(id),
    status TEXT REFERENCES status_pedido(status),
    total NUMERIC(10,2) DEFAULT 0,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE itens_pedido (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER REFERENCES pedidos(id),
    item_id INTEGER REFERENCES itens_cardapio(id),
    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
    preco_unitario NUMERIC(10, 2) NOT NULL
);

CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER,
    acao TEXT,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- População de status_pedido
INSERT INTO status_pedido (status) VALUES 
('em preparo'),
('entregue'),
('cancelado');

-- Stored Procedure: registrar_pedido
CREATE OR REPLACE FUNCTION registrar_pedido(p_cliente_id INTEGER, p_itens JSON)
RETURNS VOID AS $$
DECLARE
    pedido_id INTEGER;
    item JSON;
    v_item_id INTEGER;
    v_quantidade INTEGER;
    v_preco NUMERIC;
BEGIN
    INSERT INTO pedidos (cliente_id, status) VALUES (p_cliente_id, 'em preparo') RETURNING id INTO pedido_id;

    FOR item IN SELECT * FROM json_array_elements(p_itens)
    LOOP
        v_item_id := (item->>'item_id')::INTEGER;
        v_quantidade := (item->>'quantidade')::INTEGER;

        SELECT preco INTO v_preco FROM itens_cardapio WHERE id = v_item_id;

        INSERT INTO itens_pedido (pedido_id, item_id, quantidade, preco_unitario)
        VALUES (pedido_id, v_item_id, v_quantidade, v_preco);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Stored Procedure: calcular_total_pedido
CREATE OR REPLACE FUNCTION calcular_total_pedido(pedido_id INTEGER)
RETURNS NUMERIC AS $$
DECLARE
    total NUMERIC;
BEGIN
    SELECT SUM(quantidade * preco_unitario)
    INTO total
    FROM itens_pedido
    WHERE pedido_id = pedido_id;

    RETURN COALESCE(total, 0);
END;
$$ LANGUAGE plpgsql;

-- Stored Procedure: trocar_status_pedido
CREATE OR REPLACE FUNCTION trocar_status_pedido(pedido_id INTEGER, novo_status TEXT)
RETURNS VOID AS $$
DECLARE
    status_atual TEXT;
BEGIN
    SELECT status INTO status_atual FROM pedidos WHERE id = pedido_id;

    IF status_atual = 'entregue' THEN
        RAISE EXCEPTION 'Não é possível alterar um pedido já entregue.';
    ELSIF status_atual = 'cancelado' THEN
        RAISE EXCEPTION 'Não é possível reativar um pedido cancelado.';
    END IF;

    UPDATE pedidos SET status = novo_status WHERE id = pedido_id;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Log de alterações (trg_log_alteracao)
CREATE OR REPLACE FUNCTION log_alteracao_pedido()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO logs(pedido_id, acao, data_hora)
    VALUES (NEW.id, 'Atualizado para "' || NEW.status || '"', CURRENT_TIMESTAMP);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_alteracao
AFTER UPDATE ON pedidos
FOR EACH ROW
WHEN (OLD.status IS DISTINCT FROM NEW.status)
EXECUTE FUNCTION log_alteracao_pedido();

-- Trigger: Validação de estoque (trg_validar_estoque)
CREATE OR REPLACE FUNCTION validar_estoque()
RETURNS TRIGGER AS $$
DECLARE
    disponivel INTEGER;
BEGIN
    SELECT quantidade INTO disponivel FROM estoque WHERE item_id = NEW.item_id;

    IF disponivel IS NULL OR NEW.quantidade > disponivel THEN
        RAISE EXCEPTION 'Estoque insuficiente para o item %.', NEW.item_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validar_estoque
BEFORE INSERT ON itens_pedido
FOR EACH ROW
EXECUTE FUNCTION validar_estoque();

-- Trigger: Descontar estoque (trg_descontar_estoque)
CREATE OR REPLACE FUNCTION descontar_estoque()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE estoque
    SET quantidade = quantidade - NEW.quantidade
    WHERE item_id = NEW.item_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_descontar_estoque
AFTER INSERT ON itens_pedido
FOR EACH ROW
EXECUTE FUNCTION descontar_estoque();

-- Trigger: Validação de transição de status (trg_validar_status)
CREATE OR REPLACE FUNCTION validar_transicao_status()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status = 'entregue' THEN
        RAISE EXCEPTION 'Não é possível alterar um pedido já entregue.';
    ELSIF OLD.status = 'cancelado' THEN
        RAISE EXCEPTION 'Não é possível reativar um pedido cancelado.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validar_status
BEFORE UPDATE ON pedidos
FOR EACH ROW
WHEN (OLD.status IS DISTINCT FROM NEW.status)
EXECUTE FUNCTION validar_transicao_status();

-- Trigger: Log de cancelamento (trg_log_cancelamento)
CREATE OR REPLACE FUNCTION log_cancelamento()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'cancelado' THEN
        INSERT INTO logs(pedido_id, acao, data_hora)
        VALUES (NEW.id, 'Cancelado', CURRENT_TIMESTAMP);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_cancelamento
AFTER UPDATE ON pedidos
FOR EACH ROW
WHEN (NEW.status = 'cancelado')
EXECUTE FUNCTION log_cancelamento();
