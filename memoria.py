import json
import os


ARQUIVO_MEMORIA = "memoria.json"


def carregar_memoria():

    if not os.path.exists(ARQUIVO_MEMORIA):
        return {}

    with open(
        ARQUIVO_MEMORIA,
        "r",
        encoding="utf-8"
    ) as arquivo:

        return json.load(arquivo)


def salvar_memoria(memoria):

    with open(
        ARQUIVO_MEMORIA,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            memoria,
            arquivo,
            ensure_ascii=False,
            indent=4
        )


def salvar_ultimo_produto(
    cliente_id,
    produto,
    preco
):

    memoria = carregar_memoria()

    cliente_id = str(cliente_id)

    if cliente_id not in memoria:
        memoria[cliente_id] = {}

    # Salva apenas o produto ENCONTRADO, sem alterar o produto mencionado
    memoria[cliente_id]["ultimo_produto_encontrado"] = produto
    memoria[cliente_id]["ultimo_preco_encontrado"] = preco

    # Mantém os campos antigos para compatibilidade com memórias existentes.
    memoria[cliente_id]["ultimo_produto"] = produto
    memoria[cliente_id]["ultimo_preco"] = preco

    salvar_memoria(memoria)


def salvar_ultimo_produto_mencionado(
    cliente_id,
    produto
):

    memoria = carregar_memoria()

    cliente_id = str(cliente_id)

    if cliente_id not in memoria:
        memoria[cliente_id] = {}

    memoria[cliente_id]["ultimo_produto_mencionado"] = produto

    salvar_memoria(memoria)


def obter_ultimo_produto(cliente_id):

    memoria = carregar_memoria()

    cliente_id = str(cliente_id)

    cliente = memoria.get(cliente_id)

    if not cliente:
        return None

    produto = cliente.get(
        "ultimo_produto_mencionado",
        cliente.get("ultimo_produto")
    )

    if produto is None:
        return None

    return {
        "produto": produto,
        "preco": cliente.get(
            "ultimo_preco_encontrado",
            cliente.get("ultimo_preco")
        )
    }


def obter_ultimo_produto_mencionado(cliente_id):

    memoria = carregar_memoria()

    cliente_id = str(cliente_id)

    cliente = memoria.get(cliente_id)

    if not cliente:
        return None

    return cliente.get(
        "ultimo_produto_mencionado",
        cliente.get("ultimo_produto")
    )


def obter_ultimo_produto_encontrado(cliente_id):

    memoria = carregar_memoria()

    cliente_id = str(cliente_id)

    cliente = memoria.get(cliente_id)

    if not cliente:
        return None

    produto = cliente.get(
        "ultimo_produto_encontrado",
        cliente.get("ultimo_produto")
    )

    if produto is None:
        return None

    return {
        "produto": produto,
        "preco": cliente.get(
            "ultimo_preco_encontrado",
            cliente.get("ultimo_preco")
        )
    }


def salvar_pedido(
    cliente_id,
    produto,
    quantidade,
    preco_unitario
):

    memoria = carregar_memoria()

    cliente_id = str(cliente_id)

    total = quantidade * preco_unitario

    if cliente_id not in memoria:
        memoria[cliente_id] = {}

    memoria[cliente_id]["pedido"] = {

        "produto": produto,

        "quantidade": quantidade,

        "preco_unitario": preco_unitario,

        "total": total,

        "estado": "aguardando_confirmacao"

    }

    salvar_memoria(memoria)


def obter_pedido(cliente_id):

    memoria = carregar_memoria()

    cliente_id = str(cliente_id)

    cliente = memoria.get(cliente_id)

    if not cliente:
        return None

    return cliente.get("pedido")


def atualizar_estado(
    cliente_id,
    estado
):

    memoria = carregar_memoria()

    cliente_id = str(cliente_id)

    if cliente_id not in memoria:
        return

    if "pedido" not in memoria[cliente_id]:
        return

    memoria[cliente_id]["pedido"]["estado"] = estado

    salvar_memoria(memoria)