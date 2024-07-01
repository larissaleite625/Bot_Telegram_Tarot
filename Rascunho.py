import telebot
from config import TOKEN, CHAT_ID, CHAT_ID2

CHAVE_API = TOKEN

bot = telebot.TeleBot(CHAVE_API)

@bot.message_handler(commands=["pizza"]) # Menu lanche
def pizza(mensagem):
    bot.send_message(mensagem.chat.id, "Saindo a pizza pra sua casa: Tempo de espera em 20min")

@bot.message_handler(commands=["hamburguer"]) # Menu principal
def hamburguer(mensagem):
    bot.send_message(mensagem.chat.id, "Saindo o Brabo: em 10min chega ai")

@bot.message_handler(commands=["salada"]) 
def salada(mensagem):
    bot.send_message(mensagem.chat.id, "Não tem salada não, clique aqui para iniciar: /iniciar")

@bot.message_handler(commands=["opcao1"])
def opcao1(mensagem):
    texto = """
    O que você quer? (Clique em uma opção)
    /pizza Pizza
    /hamburguer Hamburguer
    /salada Salada"""
    bot.send_message(mensagem.chat.id, texto)

@bot.message_handler(commands=["opcao2"])
def opcao2(mensagem):
    bot.send_message(mensagem.chat.id, "Para enviar uma reclamação, mande um e-mail para reclamação@balbalba.com")

def verificar(mensagem):
    return True

@bot.message_handler(func=verificar)
def responder(mensagem):
    texto = """
    Escolha uma opção para continuar (Clique no item):
     /opcao1 Fazer um pedido
     /opcao2 Reclamar de um pedido
Responder qualquer outra coisa não vai funcionar, clique em uma das opções"""
    bot.reply_to(mensagem, texto)

bot.polling()
