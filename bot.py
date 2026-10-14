import os
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from telegram.request import HTTPXRequest

from agente import agente


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🙏 *Bem-vindo à Santo Estilo!*\n\n"
        "Olá! Sou o assistente virtual da loja. ✨\n\n"
        "🛍️ *Posso ajudar você com:*\n"
        "• Consultar produtos\n"
        "• Ver preços e estoque\n"
        "• Fazer um pedido\n\n"
        "Como posso ajudar?",
        parse_mode="Markdown"
    )


async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pergunta = update.message.text
    cliente_id = update.effective_chat.id

    try:
        # Executa a função do agente em uma thread separada para não travar o bot
        resposta = await asyncio.to_thread(agente, pergunta, cliente_id)

        print("PERGUNTA:", pergunta)
        print("RESPOSTA DO AGENTE:", repr(resposta))

        if not resposta:
            resposta = "Desculpe, não consegui gerar uma resposta."

        await update.message.reply_text(
            resposta,
            parse_mode="Markdown"
        )

    except Exception as erro:
        print("ERRO NO AGENTE:", repr(erro))
        await update.message.reply_text(
            "Desculpe, aconteceu um erro ao processar sua mensagem."
        )


def main():
    token = os.getenv("TELEGRAM_TOKEN")

    if not token:
        raise RuntimeError("TELEGRAM_TOKEN não configurado.")

    request_config = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0
    )

    app = (
        Application.builder()
        .token(token)
        .request(request_config)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            responder
        )
    )

    print("Bot iniciado...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()