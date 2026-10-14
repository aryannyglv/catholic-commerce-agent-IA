import json
from groq import Groq

from ferramentas import consultar_produto, consultar_estoque, criar_pedido
from memoria import (
    salvar_ultimo_produto,
    salvar_ultimo_produto_mencionado,
    obter_ultimo_produto_mencionado,
    obter_ultimo_produto_encontrado,
    salvar_pedido,
    obter_pedido,
    atualizar_estado
)

client = Groq()


def resolver_referencia_produto(nome, ultimo_produto_mencionado):
    referencias = {
        "ela", "ele", "dela", "dele", "essa", "esse",
        "essa camisa", "esse produto", "a dela", "o dele"
    }
    nome_normalizado = nome.strip().lower() if nome else ""
    if nome_normalizado in referencias and ultimo_produto_mencionado:
        return ultimo_produto_mencionado
    return nome


def detectar_confirmacao(mensagem):
    confirmacoes = {
        "sim", "simm", "sim!", "sim.", "pode", "pode fechar",
        "pode confirmar", "confirmo", "confirma", "quero",
        "tá bom", "ta bom", "beleza", "ok", "certo", "ótimo", "perfeito", "pode ser"
    }
    msg_normalizada = mensagem.strip().lower()
    if msg_normalizada in confirmacoes or (len(msg_normalizada) <= 20 and "sim" in msg_normalizada):
        return True
    return False


def detectar_recusa(mensagem):
    recusas = {
        "não", "nao", "não quero", "nao quero", "cancela", "cancelar",
        "desisti", "não quero mais", "nao quero mais", "esqueci",
        "muda de ideia", "acho que não", "acho que nao", "deixa"
    }
    msg_normalizada = mensagem.strip().lower()
    if msg_normalizada in recusas or msg_normalizada.startswith("não") or msg_normalizada.startswith("nao"):
        return True
    return False


def agente(pergunta, cliente_id):
    # =========================
    # CARREGAR MEMÓRIA
    # =========================
    ultimo_produto_mencionado = obter_ultimo_produto_mencionado(cliente_id)
    ultimo_produto_encontrado = obter_ultimo_produto_encontrado(cliente_id)
    pedido_atual = obter_pedido(cliente_id)

    # =========================
    # PROCESSAR CONFIRMAÇÃO OU RECUSA
    # =========================
    if pedido_atual and pedido_atual.get("estado") == "aguardando_confirmacao":
        if detectar_confirmacao(pergunta):
            atualizar_estado(cliente_id, "confirmado")
            return (
                f"✅ Pedido confirmado! 😊\n\n"
                f"Resumo do pedido:\n"
                f"Produto: {pedido_atual['produto']}\n"
                f"Quantidade: {pedido_atual['quantidade']}\n"
                f"Preço unitário: R$ {pedido_atual['preco_unitario']:.2f}\n"
                f"Valor total: R$ {pedido_atual['total']:.2f}\n\n"
                f"Agora vou precisar dos seus dados para a entrega. Qual é o seu nome?"
            )

        if detectar_recusa(pergunta):
            atualizar_estado(cliente_id, "cancelado")
            return "Tudo bem! Seu pedido foi cancelado.\n\nComo posso ajudar você agora?"

    contexto_memoria = ""
    if ultimo_produto_mencionado:
        contexto_memoria += f"\nÚLTIMO PRODUTO MENCIONADO:\nProduto: {ultimo_produto_mencionado}\n"
    if ultimo_produto_encontrado:
        contexto_memoria += (
            f"\nÚLTIMO PRODUTO ENCONTRADO NO CATÁLOGO:\n"
            f"Produto: {ultimo_produto_encontrado['produto']}\n"
            f"Preço: R$ {ultimo_produto_encontrado['preco']:.2f}\n"
        )
    if pedido_atual:
        contexto_memoria += (
            f"\nPEDIDO ATUAL:\n"
            f"Produto: {pedido_atual['produto']}\n"
            f"Quantidade: {pedido_atual['quantidade']}\n"
            f"Preço unitário: R$ {pedido_atual['preco_unitario']:.2f}\n"
            f"Total: R$ {pedido_atual['total']:.2f}\n"
            f"Estado: {pedido_atual['estado']}\n"
        )

    mensagens = [
        {
            "role": "system",
            "content": (
                "Você é o atendente virtual de uma loja de camisetas católicas.\n\n"
                "REGRAS IMPORTANTES:\n"
                "1. Nunca invente produtos, preços ou estoque.\n"
                "2. Use as ferramentas para consultar informações dos produtos quando precisar de preço ou estoque.\n"
                "3. Utilize a memória fornecida para entender mensagens anteriores.\n"
                "4. Se o produto mencionado pelo cliente não existir no catálogo, informe que ele não foi encontrado.\n"
                "5. Quando um pedido for registrado via ferramenta, confirme com o cliente informando produto, quantidade e valor total.\n\n"
                f"MEMÓRIA DO CLIENTE:\n{contexto_memoria}"
            )
        },
        {"role": "user", "content": pergunta}
    ]

    ferramentas = {
        "consultar_produto": consultar_produto,
        "consultar_estoque": consultar_estoque,
        "criar_pedido": criar_pedido
    }

    tools = [
        {
            "type": "function",
            "function": {
                "name": "consultar_produto",
                "description": "Consulta informações de um produto, incluindo preço e estoque.",
                "parameters": {
                    "type": "object",
                    "properties": {"nome": {"type": "string", "description": "Nome do produto."}},
                    "required": ["nome"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "consultar_estoque",
                "description": "Consulta a quantidade disponível de um produto.",
                "parameters": {
                    "type": "object",
                    "properties": {"nome": {"type": "string", "description": "Nome do produto."}},
                    "required": ["nome"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "criar_pedido",
                "description": "Cria um pedido para um produto. Verifica estoque e retorna os detalhes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nome": {"type": "string", "description": "Nome do produto."},
                        "quantidade": {"type": "integer", "description": "Quantidade de unidades a pedir."}
                    },
                    "required": ["nome", "quantidade"]
                }
            }
        }
    ]

    # Limite máximo de chamadas seguidas para evitar travamento em loop infinito
    MAX_LOOPS = 5

    for _ in range(MAX_LOOPS):
        resposta = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=mensagens,
            tools=tools,
            tool_choice="auto"
        )

        mensagem = resposta.choices[0].message
        mensagens.append(mensagem)

        # Se a IA não chamou nenhuma ferramenta, retornamos a resposta direta dela
        if not mensagem.tool_calls:
            return mensagem.content or "Como posso ajudar você?"

        # Se houver chamadas de ferramenta, executamos cada uma
        for chamada in mensagem.tool_calls:
            nome_funcao = chamada.function.name
            try:
                argumentos = json.loads(chamada.function.arguments)
            except Exception:
                argumentos = {}

            if argumentos.get("nome"):
                argumentos["nome"] = resolver_referencia_produto(
                    argumentos["nome"],
                    ultimo_produto_mencionado
                )

            if nome_funcao == "criar_pedido" and not argumentos.get("nome") and ultimo_produto_mencionado:
                argumentos["nome"] = ultimo_produto_mencionado

            if nome_funcao in ("consultar_produto", "consultar_estoque", "criar_pedido") and argumentos.get("nome"):
                salvar_ultimo_produto_mencionado(cliente_id, argumentos["nome"])

            funcao_para_chamar = ferramentas.get(nome_funcao)
            if funcao_para_chamar:
                resultado = funcao_para_chamar(**argumentos)
            else:
                resultado = {"erro": "Ferramenta não encontrada."}

            if resultado is None:
                resultado = {"erro": "Produto não encontrado no catálogo."}

            if nome_funcao == "consultar_produto" and isinstance(resultado, dict) and "erro" not in resultado:
                salvar_ultimo_produto(
                    cliente_id,
                    resultado.get("produto", argumentos.get("nome")),
                    resultado.get("preco")
                )

            if nome_funcao == "criar_pedido" and isinstance(resultado, dict) and "erro" not in resultado:
                produto = resultado.get("produto")
                quantidade = resultado.get("quantidade")
                preco_unitario = resultado.get("preco")

                if produto and quantidade:
                    if not preco_unitario:
                        info_prod = consultar_produto(produto)
                        if info_prod:
                            preco_unitario = info_prod.get("preco")

                    if preco_unitario:
                        salvar_pedido(cliente_id, produto, quantidade, preco_unitario)

            mensagens.append({
                "role": "tool",
                "tool_call_id": chamada.id,
                "content": json.dumps(resultado, ensure_ascii=False)
            })

    return "Desculpe, a requisição demorou muito para responder. Pode tentar novamente?"