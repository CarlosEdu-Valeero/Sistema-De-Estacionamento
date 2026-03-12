import os
import sys
import sqlite3
from datetime import datetime

if getattr(sys, 'frozen', False):
    pasta_do_programa = os.path.dirname(sys.executable)
else:
    pasta_do_programa = os.path.dirname(os.path.abspath(__file__))

ticket = os.path.join(pasta_do_programa, "ticket.txt")

# VALORES (Mudar aqui caso haja alteração no preço)
VALOR_HORA = 10.00
VALOR_PERIODO = 20.00
TOLERANCIA_MINUTOS = 5

BANCO_DADOS = 'estacionamento.db'

def inicializar_arquivos():
    """Cria banco de dados e tabela se não existirem"""
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rotativo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT,
            veiculo TEXT,
            data TEXT,
            entrada TEXT,
            saida TEXT,
            valor REAL
        )
    ''')
    conn.commit()
    conn.close()

def calcular_valor_simples(hora_entrada_str):
    """Calcula o valor com tolerância na primeira hora"""
    formato = '%H:%M:%S'
    h_entrada = datetime.strptime(hora_entrada_str, formato)
    agora_str = datetime.now().strftime('%H:%M:%S')
    h_saida = datetime.strptime(agora_str, formato)
    
    duracao = h_saida - h_entrada
    total_segundos = duracao.total_seconds()
    
    if total_segundos < 0: return 0.0
    minutos = total_segundos / 60

    # VALORES
    if minutos <= 5:
        return 0.0
    elif minutos <= 30:
        return 6.00  # Até 30 min: R$ 6,00
    elif minutos <= 40:
        return 8.00  # Até 40 min: R$ 8,00
    elif minutos <= 60: 
        return 10.00 # Até 60 min: R$ 10,00
    elif minutos <= 80: 
        return 15.00 # De 1h20 até 1h45: R$ 15,00
    else:
        return 20.00 # Acima de 1h45: R$ 20,00 (Período)
        

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