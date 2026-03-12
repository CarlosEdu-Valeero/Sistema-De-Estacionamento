import os
import sys
import sqlite3
from datetime import datetime

if getattr(sys, 'frozen', False):
    pasta_do_programa = os.path.dirname(sys.executable)
else:
    pasta_do_programa = os.path.dirname(os.path.abspath(__file__))

ticket = os.path.join(pasta_do_programa, "ticket.txt")

BANCO_DADOS = 'estacionamento.db'

def inicializar_arquivos():
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rotativo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT, veiculo TEXT, data TEXT, entrada TEXT, saida TEXT, valor REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS precos_faixas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            minutos_limite INTEGER,
            valor REAL
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM precos_faixas")
    if cursor.fetchone()[0] == 0:
        config_padrao = [(30, 6.00), (40, 8.00), (60, 10.00), (105, 15.00), (9999, 20.00)]
        cursor.executemany("INSERT INTO precos_faixas (minutos_limite, valor) VALUES (?, ?)", config_padrao)
    
    conn.commit()
    conn.close()

def calcular_valor_atual(hora_entrada_str):
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    cursor.execute("SELECT minutos_limite, valor FROM precos_faixas ORDER BY minutos_limite ASC")
    regras = cursor.fetchall()
    conn.close()

    if not regras:
        return 0.0

    formato = '%H:%M:%S'
    try:
        h_entrada = datetime.strptime(hora_entrada_str, formato)
        agora = datetime.now()
        h_entrada = h_entrada.replace(year=agora.year, month=agora.month, day=agora.day)
        
        duracao = agora - h_entrada
        minutos = duracao.total_seconds() / 60

        if minutos <= 5: 
            return 0.0
        
        for limite, valor in regras:
            if minutos <= limite:
                return valor
        
        return regras[-1][1]
    except:
        return 0.0

def calcular_valor_simples(hora_entrada_str):
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    cursor.execute("SELECT minutos_limite, valor FROM precos_faixas ORDER BY minutos_limite ASC")
    regras = cursor.fetchall()
    conn.close()

    if not regras:
        return 0.0

    formato = '%H:%M:%S'
    agora = datetime.now()
    try:
        h_entrada = datetime.strptime(hora_entrada_str, formato)
        h_entrada = h_entrada.replace(year=agora.year, month=agora.month, day=agora.day)
        duracao = agora - h_entrada
        minutos = duracao.total_seconds() / 60

        if minutos <= 5: 
            return 0.0
        
        for limite, valor in regras:
            if minutos <= limite:
                return valor
        
        return regras[-1][1]
        
    except Exception as e:
        print(f"Erro no cálculo: {e}")
        return 0.0

def registrar_entrada(placa, veiculo):
    """Salva a entrada no banco"""
    hora_atual = datetime.now().strftime('%H:%M:%S')
    data_atual = datetime.now().strftime('%d/%m/%Y')
    
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO rotativo (placa, veiculo, data, entrada) VALUES (?, ?, ?, ?)", 
                   (placa, veiculo, data_atual, hora_atual))
    conn.commit()
    conn.close()
    return hora_atual

def dar_saida_banco(placa):
    """Registra ticket de saida"""
    hora_saida = datetime.now().strftime('%H:%M:%S')
    data_atual = datetime.now().strftime('%d/%m/%Y')
    
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT entrada, veiculo FROM rotativo 
        WHERE placa = ? AND data = ? AND saida IS NULL 
        ORDER BY id DESC LIMIT 1
    ''', (placa, data_atual))
    
    resultado = cursor.fetchone()
    
    if resultado:
        hora_entrada = resultado[0]
        veiculo = resultado[1]
        valor_final = calcular_valor_simples(hora_entrada)
        
        cursor.execute('''
            UPDATE rotativo 
            SET saida = ?, valor = ? 
            WHERE placa = ? AND data = ? AND saida IS NULL
        ''', (hora_saida, valor_final, placa, data_atual))
        
        conn.commit()
        conn.close()
        return hora_entrada, hora_saida, valor_final, veiculo
    
    conn.close()
    return None, None, 0, None

def gerar_layout_ticket(placa, veiculo, entrada, saida=None, valor=0):
    tempo_permanencia = ""
    if saida:
        ent = datetime.strptime(entrada, '%H:%M:%S')
        sai = datetime.strptime(saida, '%H:%M:%S')
        duracao = sai - ent
        horas, rem = divmod(duracao.seconds, 3600)
        minutos, _ = divmod(rem, 60)
        tempo_permanencia = f"PERMANENCIA: {horas}h {minutos}min"

    header = [
        "      ESTACIONAMENTO CENTRAL PARK      ",
        "      CNPJ: 28.789.115/0001-26         ",
        "    R. Mariano Torres, 114 - CTBA      ",
        "          Tel: (41) 0000-0000          ",
        "-" * 40
    ]
    
    body = [
        f"DATA: {datetime.now().strftime('%d/%m/%Y')}",
        f"PLACA:   {placa}",
        f"VEICULO: {veiculo}",
        f"ENTRADA: {entrada}",
    ]
    
    if saida:
        body.append(f"SAIDA:   {saida}")
        body.append(tempo_permanencia)
        body.append(f"TOTAL:   R$ {valor:.2f}")
    
    footer = [
        "-" * 40,
        "HORARIO: SEG 07:30-18H | TER-SEX 07:30-22H  ",
        "\n",
        "         FAVOR GUARDAR ESTE TICKET       ",
        "      PARA FAZER A RETIRADA DO VEICULO   ",
        "         OBRIGADO PELA PREFERENCIA       ",
        "\n\n\n" 
    ]
    
    return "\n".join(header + body + footer)

def buscar_por_data(data_alvo):
    """Retorna o histórico do dia"""
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    cursor.execute("SELECT id, placa, veiculo, entrada, saida, valor FROM rotativo WHERE data = ? ORDER BY id DESC", (data_alvo,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def buscar_dados_placa(placa):
    """Busca registro mais recente de uma placa específica hoje"""
    data_atual = datetime.now().strftime('%d/%m/%Y')
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT placa, veiculo, entrada, saida, valor FROM rotativo 
        WHERE placa = ? AND data = ? 
        ORDER BY id DESC LIMIT 1
    ''', (placa, data_atual))
    resultado = cursor.fetchone()
    conn.close()
    return resultado

def veiculo_no_patio(placa):
    """Verifica existencia sem saída para a placa no dia de hoje"""
    data_atual = datetime.now().strftime('%d/%m/%Y')
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id FROM rotativo 
        WHERE placa = ? AND data = ? AND saida IS NULL
    ''', (placa, data_atual))
    resultado = cursor.fetchone()
    conn.close()
    return resultado is not None