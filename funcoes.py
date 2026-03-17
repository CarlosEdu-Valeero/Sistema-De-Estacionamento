import sqlite3
import os
import sys
from datetime import datetime, time

BANCO_DADOS = 'estacionamento.db'

def inicializar_arquivos():
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS rotativo (
        id INTEGER PRIMARY KEY AUTOINCREMENT, placa TEXT, veiculo TEXT, 
        data TEXT, entrada TEXT, saida TEXT, valor REAL, tamanho INTEGER)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS mensalistas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, endereco TEXT, 
        bairro TEXT, cidade TEXT, uf TEXT, cep TEXT, telefone TEXT, 
        cpf TEXT, placa TEXT, veiculo TEXT, data_vencimento TEXT, valor_mensalidade REAL)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS precos_tamanhos (
        tamanho INTEGER PRIMARY KEY, v15 REAL, v30 REAL, v45 REAL, 
        v60 REAL, v75 REAL, v_extra REAL, v_diaria REAL)''')
    
    cursor.execute("SELECT COUNT(*) FROM precos_tamanhos")
    if cursor.fetchone()[0] == 0:
        valores = [
            (1, 6.0, 6.0, 8.0, 10.0, 15.0, 0.0, 20.0),
            (2, 10.0, 10.0, 10.0, 10.0, 22.0, 5.0, 40.0),
            (3, 18.0, 18.0, 18.0, 18.0, 22.0, 5.0, 45.0)
        ]
        cursor.executemany("INSERT INTO precos_tamanhos VALUES (?,?,?,?,?,?,?,?)", valores)
    
    try: cursor.execute("ALTER TABLE rotativo ADD COLUMN tamanho INTEGER DEFAULT 1")
    except: pass
    conn.commit(); conn.close()

def e_mensalista(placa):
    conn = sqlite3.connect(BANCO_DADOS); cursor = conn.cursor()
    cursor.execute("SELECT nome FROM mensalistas WHERE placa = ?", (placa.upper(),))
    res = cursor.fetchone(); conn.close()
    return res[0] if res else None

def obter_tabela_precos():
    conn = sqlite3.connect(BANCO_DADOS); cursor = conn.cursor()
    cursor.execute("SELECT * FROM precos_tamanhos"); res = cursor.fetchall()
    conn.close(); return res

def atualizar_precos(tamanho, vals):
    conn = sqlite3.connect(BANCO_DADOS); cursor = conn.cursor()
    cursor.execute("""UPDATE precos_tamanhos SET v15=?, v30=?, v45=?, v60=?, v75=?, v_extra=?, v_diaria=?
                      WHERE tamanho=?""", (*vals, tamanho))
    conn.commit(); conn.close()

def calcular_valor_estacionamento(hora_ent_str, tamanho, placa):
    if e_mensalista(placa): return 0.0
    conn = sqlite3.connect(BANCO_DADOS); cursor = conn.cursor()
    cursor.execute("SELECT * FROM precos_tamanhos WHERE tamanho=?", (tamanho,))
    p = cursor.fetchone(); conn.close()
    
    fmt = '%H:%M:%S'
    h_ent = datetime.strptime(hora_ent_str, fmt)
    agora = datetime.now()
    duracao = agora - datetime.combine(agora.date(), h_ent.time())
    minutos = int(duracao.total_seconds() / 60)
    
    if minutos <= 5: return 0.0
    if minutos <= 15: v = p[1]
    elif minutos <= 30: v = p[2]
    elif minutos <= 45: v = p[3]
    elif minutos <= 60: v = p[4]
    elif minutos <= 75: v = p[5]
    else: v = p[7]

    if agora.hour >= 18:
        limite = datetime.combine(agora.date(), time(18, 0, 0))
        inicio = max(datetime.combine(agora.date(), h_ent.time()), limite)
        min_extra = int((agora - inicio).total_seconds() / 60)
        if min_extra > 0: v += (min_extra // 15) * p[6]
    return v

def registrar_entrada(p, v, t):
    h, d = datetime.now().strftime('%H:%M:%S'), datetime.now().strftime('%d/%m/%Y')
    conn = sqlite3.connect(BANCO_DADOS); cursor = conn.cursor()
    cursor.execute("INSERT INTO rotativo (placa, veiculo, data, entrada, tamanho) VALUES (?,?,?,?,?)", (p, v, d, h, t))
    ultimo_id= cursor.lastrowid
    conn.commit(); conn.close(); return h, ultimo_id

def dar_saida_banco(placa):
    h_sai, d = datetime.now().strftime('%H:%M:%S'), datetime.now().strftime('%d/%m/%Y')
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    
    cursor.execute("SELECT entrada, veiculo, tamanho, id FROM rotativo WHERE placa=? AND saida IS NULL", (placa,))
    res = cursor.fetchone()
    
    if res:
        v = calcular_valor_estacionamento(res[0], res[2], placa)
        cursor.execute("UPDATE rotativo SET saida=?, valor=? WHERE id=?", (h_sai, v, res[3]))
        
        conn.commit()
        conn.close()
        return res[0], h_sai, v, res[1], res[3]
    conn.close()
    return None, None, 0, None, None

def salvar_mensalista(d):
    conn = sqlite3.connect(BANCO_DADOS); cursor = conn.cursor()
    cursor.execute("INSERT INTO mensalistas (nome, endereco, bairro, cidade, uf, cep, telefone, cpf, placa, veiculo, data_vencimento, valor_mensalidade) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", 
                   (d['Nome'], d['Endereço'], d['Bairro'], d['Cidade'], d['UF'], d['CEP'], d['Telefone'], d['CPF'], d['Placa'], d['Veículo'], d['Data Vencimento'], d['Valor da Mensalidade']))
    conn.commit(); conn.close()

def gerar_layout_ticket(placa, veiculo, ent, sai=None, valor=0, id_controle=None):
    nome_m = e_mensalista(placa)
    header = [
        "      ESTACIONAMENTO CENTRAL PARK      ",
        "      CNPJ: 28.789.115/0001-26         ",
        "    R. Mariano Torres, 114 - CTBA      ",
        "          Tel: (41) 0000-0000          ",
        "-" * 39
    ]
    if nome_m: header.append(f"*** MENSALISTA: {nome_m} ***")
    
    body = [
        f"DATA:     {datetime.now().strftime('%d/%m/%Y')}",
        f"ID CONTROLE: {id_controle}",
        f"PLACA:    {placa}",
        f"VEICULO:  {veiculo}",
        f"ENTRADA:  {ent}"
    ]
    
    if sai:
        body.append(f"SAIDA:    {sai}")
        try:
            duracao = datetime.strptime(sai, '%H:%M:%S') - datetime.strptime(ent, '%H:%M:%S')
            h, m = divmod(duracao.seconds // 60, 60)
            body.append(f"PERMAN.:  {h}h {m}min")
        except: pass
        body.append(f"VALOR:    R$ {valor:.2f}")
        if nome_m: body.append("(ISENTO - PAGO MENSAL)")

    footer = ["-" * 39, "HORARIO: SEG 07:30-18H | TER-SEX 07:30-22H", "", "      FAVOR GUARDAR ESTE TICKET        ", 
              "   PARA FAZER A RETIRADA DO VEICULO    ", "      OBRIGADO PELA PREFERENCIA        ", "\n\n\n"]
    
    return "\n".join(header + body + footer)

def buscar_por_data(data):
    conn = sqlite3.connect(BANCO_DADOS); cursor = conn.cursor()
    cursor.execute("SELECT id, placa, veiculo, entrada, saida, valor, tamanho FROM rotativo WHERE data=? ORDER BY id DESC", (data,))
    res = cursor.fetchall(); conn.close(); return res

def buscar_todos_recente(limite=100):
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    cursor.execute("SELECT id, placa, veiculo, entrada, saida, valor, tamanho FROM rotativo ORDER BY id DESC LIMIT ?", (limite,))
    res = cursor.fetchall()
    conn.close()
    return res

def buscar_por_termo(termo):
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    query = """
        SELECT id, placa, veiculo, entrada, saida, valor, tamanho 
        FROM rotativo 
        WHERE id = ? OR placa LIKE ? 
        ORDER BY id DESC
    """
    cursor.execute(query, (termo, f'%{termo}%'))
    res = cursor.fetchall()
    conn.close()
    return res

def veiculo_no_patio(p):
    conn = sqlite3.connect(BANCO_DADOS); cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM rotativo WHERE placa=? AND data=? AND saida IS NULL", (p, datetime.now().strftime('%d/%m/%Y')))
    res = cursor.fetchone(); conn.close(); return res is not None