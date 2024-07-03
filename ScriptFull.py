from telegram import Bot
import time
import requests
from openai import OpenAI
import locale
import os
import re
from datetime import datetime
import telebot, types
import pandas as pd
import random
import pyodbc
from sqlalchemy import create_engine
import time
#import google.generativeai as genai


# Chave do Telegram
CHAVE_API = os.environ.get("SATURN_BOT_PROD")
bot = telebot.TeleBot(CHAVE_API)

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

#Chave da OpenAI
client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

#Ou concorrencia :D
#api_key = os.environ.get("GOOGLE_API_KEY")
#genai.configure(api_key=api_key)

#Variváveis
NUM_CARTAS_TOTAIS = 78
NUM_CARTAS_ESCOLHIDAS = 3

#Conecta com banco de dados
def connect_to_db():
    server = 'localhost\SQLEXPRESS'
    database = 'Tarot'
    username = 'sa'
    password = ''
    driver = 'ODBC Driver 17 for SQL Server'
    connection_string = f'DRIVER={{{driver}}};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}'
    
    while True:
        try:
            conn = pyodbc.connect(connection_string)
            #print("Conexão estabelecida com sucesso")
            return conn
        except pyodbc.Error as e:
            print(f"Falha na conexão: {e}")
            print("Tentando novamente em 30 segundos...")
            time.sleep(30)  

#Escolhe de 1 até 78 pra sortear a carta
def escolher_ids_aleatorios():
    return random.sample(range(1, NUM_CARTAS_TOTAIS + 1), NUM_CARTAS_ESCOLHIDAS)

# Query SQL
def ler_arquivo(ids_escolhidos):
    conn = connect_to_db()
    query = f"""
        SELECT * FROM [Tarot_SCHEMA].Cartas_Tarot
        WHERE ID IN ({','.join('?' for _ in ids_escolhidos)})
    """
    df = pd.read_sql(query, conn, params=ids_escolhidos)
    conn.close()
    return df

def tema_sem_carac_esp(tema):
    caracteres_invalidos = r'[<>:"/\\|?*]'
    tema_limpo = re.sub(caracteres_invalidos, '_', tema)
    return tema_limpo

# Gera o conselho
def gerar_conselho(tema, cartas_selecionadas):
    cartas_info = ""
    for _, carta in cartas_selecionadas.iterrows():
        cartas_info += f"{carta['Carta']}: {carta['Significado_Normal']} ({'Sim' if carta['Sim_Ou_Nao'] == 'Sim' else 'Não'}).\n"

    prompt = f"Você é um tarólogo. Dê um conselho curto (máximo de 280 caracteres) sobre o tema {tema}, considerando as cartas: {', '.join(cartas_selecionadas['Carta'])}. Informações das cartas: {cartas_info}"

    agora = datetime.now()
    tema_limpo = tema_sem_carac_esp(tema)
    data_hora_formatada = agora.strftime("%Y-%m-%d_%H-%M-%S")
    nome_arquivo = f"conselho_{tema_limpo}_{data_hora_formatada}.txt"

    conselho = ''  # Inicializa a variável conselho
    #try:
    #    model = genai.GenerativeModel('gemini-1.5-flash')
    #    resposta = model.generate_content(prompt)
    #    conselho = resposta.text 
    # A API do Gemini é gratuita por até 50 requests por dia

    try:
        resposta = client.chat.completions.create(
            model="gpt-3.5-turbo",  
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        conselho = resposta.choices[0].message.content # Acessa o conteúdo correto da resposta
        #response.choices[0].message.content
    except Exception as e:
        conselho = f"Não foi possível gerar um conselho devido ao seguinte erro: {e}"

    try:
        with open(nome_arquivo, "w", encoding="utf-8") as arquivo:
            arquivo.write(conselho)
    except Exception as e:
        print(f"Não foi possível salvar o arquivo devido ao seguinte erro: {e}")

    return conselho

# Resposta padrão para o usuário
def mostrar_cartas_selecionadas(cartas, conselho):
    resposta = ""
    for _, carta in cartas.iterrows():
        resposta += f"Nome: {carta['Carta']}\n"
        resposta += f"Elemento: {carta['Elemento']}\n"
        #resposta += f"Planeta: {carta['Planeta']}\n"
        resposta += f"Signo Astrológico: {carta['Signo_Astrologico']}\n"
        resposta += f"Kabbalah: {carta['Cabala_Kabbalah']}\n \n \n"
        #resposta += f"Sim ou Não: {carta['Sim_Ou_Nao']}\n"
        #resposta += f"Significado: {carta['Significado_Normal']}\n\n"
    resposta += f"Conselho: {conselho}\n\n"
    return resposta

# Qual o pergunta/tema do usuário
def processar_escolha(chat_id, tema_ou_pergunta):
    ids_escolhidos = escolher_ids_aleatorios()
    cartas_escolhidas = ler_arquivo(ids_escolhidos)
    conselho = gerar_conselho(tema_ou_pergunta, cartas_escolhidas)
    resposta = mostrar_cartas_selecionadas(cartas_escolhidas, conselho)

    salvar_conselho(tema_ou_pergunta, conselho)

    bot.send_message(chat_id, resposta)
    exibir_menu_por_novo_conselho(chat_id)  # Retornar ao menu após mostrar o conselho

# Função para salvar o conselho em um arquivo de texto
def salvar_conselho(tema_ou_pergunta, conselho):
    agora = datetime.now()
    tema_limpo = tema_sem_carac_esp(tema_ou_pergunta)
    data_hora_formatada = agora.strftime("%Y-%m-%d_%H-%M-%S")
    nome_arquivo = f"conselho_{tema_limpo}_{data_hora_formatada}.txt"
    with open(nome_arquivo, 'w', encoding='utf-8') as arquivo:
        arquivo.write(f"Tema ou pergunta: {tema_ou_pergunta}\n")
        arquivo.write(f"Conselho: {conselho}\n")

# Pergunta o tema pro usuário
def exibir_menu_por_novo_conselho(chat_id):
    texto = """
    Pense em uma pergunta sobre os temas ou digite sua própria pergunta:
    /opcao1 Amor 💞❤️💑
    /opcao2 Dinheiro 💰💸💳
    /opcao3 Amigos 🗣🤝🤩
    /opcao4 Carreira 👔💼🖥️
    /opcao5 Estudos 📒🎓🔬
    /opcao6 Espiritualidade ☮️🕉️☸️✝️☪️🕎
    /opcao7 Digite sua própria pergunta ❔🤔💡
    /sair Para sair
    """
    bot.send_message(chat_id, texto)

# Menu e capturar a escolha do usuário
@bot.message_handler(commands=["iniciar"])
def exibir_menu(mensagem):
    exibir_menu_por_novo_conselho(mensagem.chat.id)

# Garante que o usuário vai colocar a opção correta
@bot.message_handler(commands=["opcao1", "opcao2", "opcao3", "opcao4", "opcao5", "opcao6"])
def handle_opcao(mensagem):
    temas = {
        "opcao1": "Amor",
        "opcao2": "Dinheiro",
        "opcao3": "Amigos",
        "opcao4": "Carreira",
        "opcao5": "Estudos",
        "opcao6": "Espiritualidade"
    }
    comando = mensagem.text.split()[0][1:] 
    if comando in temas:
        tema = temas[comando]
        processar_escolha(mensagem.chat.id, tema)
    else:
        bot.send_message(mensagem.chat.id, "Comando inválido. Por favor, selecione uma opção válida.")

# Pega a possivel pergunta
@bot.message_handler(commands=["opcao7"])
def handle_opcao7(mensagem):
    bot.send_message(mensagem.chat.id, "Digite sua pergunta:")
    bot.register_next_step_handler(mensagem, processar_pergunta_personalizada)

def processar_pergunta_personalizada(mensagem):
    pergunta_personalizada = mensagem.text
    processar_escolha(mensagem.chat.id, pergunta_personalizada)

# Encerra o conselho
@bot.message_handler(commands=["sair"])
def sair(mensagem):
    bot.send_message(mensagem.chat.id, "Volte sempre!")

# Função para verificar se a mensagem não é um comando
def verificar(mensagem):
    comandos = ["/iniciar", "/opcao1", "/opcao2", "/opcao3", "/opcao4", "/opcao5", "/opcao6", "/opcao7", "/sair"]
    return not any(mensagem.text.startswith(comando) for comando in comandos)

# Inicio
@bot.message_handler(func=verificar)
def responder(mensagem):
    texto = """
    /iniciar seu Oráculo 🪐💟🔮♠♥♦♣ 
    """
    bot.reply_to(mensagem, texto)

bot.polling()
