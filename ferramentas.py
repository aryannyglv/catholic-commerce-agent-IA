from catalogo import produtos, atualizar_estoque


pedidos = []


def encontrar_produto(nome):
    
    # Validação: nome não pode ser None ou vazio
    if not nome:
        return None
    
    nome = nome.lower()

    for produto in produtos:

        nome_produto = produto.lower()

        if nome_produto in nome:
            return produto

        partes = nome_produto.split()

        if all(parte in nome for parte in partes[1:]):
            return produto

    return None


def consultar_produto(nome):

    produto = encontrar_produto(nome)

    if produto:
        return produtos[produto]

    return None


def consultar_estoque(nome):

    produto = encontrar_produto(nome)

    if produto:
        return produtos[produto]["estoque"]

    return None


def criar_pedido(nome, quantidade):

    # Validação 1: nome não pode ser None ou vazio
    if not nome:
        return {
            "erro": "Nome do produto é obrigatório."
        }

    # Validação 2: quantidade deve ser um número
    try:
        quantidade = int(quantidade)
    except (ValueError, TypeError):
        return {
            "erro": f"Quantidade deve ser um número inteiro. Recebido: {quantidade}"
        }

    # Validação 3: quantidade deve ser positiva
    if quantidade <= 0:
        return {
            "erro": "Quantidade deve ser maior que zero."
        }

    produto = encontrar_produto(nome)

    if not produto:
        return {
            "erro": "Produto não encontrado."
        }

    dados_produto = produtos[produto]
    estoque = dados_produto["estoque"]

    if quantidade > estoque:
        return {
            "erro": f"Estoque insuficiente. Temos apenas {estoque} unidades."
        }

    preco = dados_produto["preco"]
    total = preco * quantidade
    novo_estoque = estoque - quantidade

    # Atualiza o estoque diretamente na planilha Excel
    nome_exibicao = dados_produto.get("produto", produto)
    atualizar_estoque(nome_exibicao, novo_estoque)

    pedido = {
        "produto": nome_exibicao,
        "quantidade": quantidade,
        "preco": preco,
        "total": total
    }

    pedidos.append(pedido)

    return pedido