import customtkinter as ctk
from tkinter import messagebox 
from tkcalendar import DateEntry
import funcoes
import sqlite3
import win32print
from datetime import datetime

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        funcoes.inicializar_arquivos()

        self.title("CENTRAL PARK - Mariano Torres, 114")
        self.geometry("900x600")
        ctk.set_appearance_mode("light")
        
        self.bind('<F1>', lambda event: self.executar_entrada())
        self.bind('<F2>', lambda event: self.executar_saida())
        self.bind('<Escape>', lambda event: self.limpar_placa())

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frame_menu = ctk.CTkFrame(self, width=320, corner_radius=0)
        self.frame_menu.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.btn_mensalistas = ctk.CTkButton(self.frame_menu, text="MENSALISTAS", fg_color="#34495e", command=self.abrir_mensalistas)
        self.btn_mensalistas.pack(pady=10, padx=30, fill="x")

        self.btn_config = ctk.CTkButton(self.frame_menu, text="Configurar Preços", fg_color="transparent", 
                                       border_width=1, text_color="black", command=self.abrir_config_precos)
        self.btn_config.pack(pady=5, padx=30, fill="x")

        self.lbl_ativos = ctk.CTkLabel(self.frame_menu, text="No Pátio: 0", font=("Arial", 18, "bold"), text_color="#3498db")
        self.lbl_ativos.pack(pady=(20, 5))
        
        self.lbl_finalizados = ctk.CTkLabel(self.frame_menu, text="Saíram Hoje: 0", font=("Arial", 14))
        self.lbl_finalizados.pack(pady=5)

        ctk.CTkLabel(self.frame_menu, text="PLACA DO VEÍCULO", font=("Arial", 12, "bold")).pack(pady=(20, 0))
        self.entry_placa = ctk.CTkEntry(self.frame_menu, width=220, height=50, font=("Arial", 26, "bold"), justify="center")
        self.entry_placa.pack(pady=5)
        self.entry_placa.focus()
        self.entry_placa.bind('<KeyRelease>', self.formatar_placa)

        ctk.CTkLabel(self.frame_menu, text="MODELO VEÍCULO", font=("Arial", 12)).pack(pady=(10, 0))
        self.entry_veiculo = ctk.CTkEntry(self.frame_menu, width=220, height=35, font=("Arial", 16))
        self.entry_veiculo.pack(pady=5)
        self.entry_veiculo.bind('<KeyRelease>', self.buscar_sugestoes)

        self.frame_sugestoes = ctk.CTkScrollableFrame(self.frame_menu, width=210, height=0)

        ctk.CTkLabel(self.frame_menu, text="TAMANHO / CATEGORIA", font=("Arial", 12)).pack(pady=(10, 0))
        self.op_tamanho = ctk.CTkOptionMenu(self.frame_menu, values=["1 - Pequeno", "2 - Grande", "3 - Furgão"], width=220)
        self.op_tamanho.pack(pady=5)

        self.check_imprimir = ctk.CTkCheckBox(self.frame_menu, text="Imprimir Ticket?")
        self.check_imprimir.select()
        self.check_imprimir.pack(pady=15)

        self.btn_entrada = ctk.CTkButton(self.frame_menu, text="[F1] ENTRADA", fg_color="#27ae60", hover_color="#1e8449", height=50, font=("Arial", 16, "bold"), command=self.executar_entrada)
        self.btn_entrada.pack(pady=10, fill="x", padx=30)

        self.btn_saida = ctk.CTkButton(self.frame_menu, text="[F2] SAÍDA", fg_color="#e74c3c", hover_color="#c0392b", height=50, font=("Arial", 16, "bold"), command=self.executar_saida)
        self.btn_saida.pack(pady=10, fill="x", padx=30)

        self.frame_lista = ctk.CTkFrame(self)
        self.frame_lista.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.frame_busca = ctk.CTkFrame(self.frame_lista, fg_color="transparent")
        self.frame_busca.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(self.frame_busca, text="DATA DE CONSULTA:", font=("Arial", 12, "bold")).pack(side="left", padx=5)

        self.cal_data = DateEntry(self.frame_busca, width=12, background='darkblue',
                                 foreground='white', borderwidth=2, locale='pt_BR',
                                 date_pattern='dd/mm/yyyy')
        self.cal_data.pack(side="left", padx=5)
        self.cal_data.bind("<<DateEntrySelected>>", lambda e: self.buscar_historico())

        self.frame_busca = ctk.CTkFrame(self.frame_lista, fg_color="transparent")
        self.frame_busca.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(self.frame_busca, text="BUSCAR (ID/PLACA):", font=("Arial", 12, "bold")).pack(side="left", padx=(20, 5))
        self.entry_busca_rapida = ctk.CTkEntry(self.frame_busca, width=150, placeholder_text="Digite aqui...")
        self.entry_busca_rapida.pack(side="left", padx=5)
        self.entry_busca_rapida.bind("<KeyRelease>", lambda e: self.buscar_historico())
        
        self.frame_scroll_lista = ctk.CTkScrollableFrame(self.frame_lista, fg_color="transparent")
        self.frame_scroll_lista.pack(expand=True, fill="both", padx=10, pady=10)

        self.buscar_historico()

    def formatar_placa(self, event):
        if event.keysym == "BackSpace": return
        texto = self.entry_placa.get().upper().replace("-", "")
        if len(texto) >= 3:
            novo = texto[:3] + "-" + texto[3:7]
            if self.entry_placa.get() != novo:
                self.entry_placa.delete(0, "end")
                self.entry_placa.insert(0, novo)

    def buscar_sugestoes(self, event):
        if event.keysym in ("Up", "Down", "Return", "Escape"): return
        termo = self.entry_veiculo.get().upper()
        if len(termo) < 2:
            self.fechar_sugestoes()
            return
        try:
            conn = sqlite3.connect('modelos_veiculos.db')
            cursor = conn.cursor()
            cursor.execute("SELECT nome FROM modelos WHERE nome LIKE ? LIMIT 5", (f'%{termo}%',))
            modelos = cursor.fetchall()
            conn.close()
            if modelos: self.mostrar_sugestoes(modelos)
            else: self.fechar_sugestoes()
        except: pass

    def mostrar_sugestoes(self, modelos):
        for widget in self.frame_sugestoes.winfo_children(): widget.destroy()
        self.frame_sugestoes.configure(height=120)
        self.frame_sugestoes.pack(pady=0)
        for m in modelos:
            nome_m = m[0]
            btn = ctk.CTkButton(self.frame_sugestoes, text=nome_m, fg_color="transparent", text_color="black", hover_color="#eee", anchor="w", height=25, command=lambda n=nome_m: self.selecionar_modelo(n))
            btn.pack(fill="x")

    def selecionar_modelo(self, nome):
        self.entry_veiculo.delete(0, 'end')
        self.entry_veiculo.insert(0, nome)
        self.fechar_sugestoes()

    def fechar_sugestoes(self):
        self.frame_sugestoes.pack_forget()
        self.frame_sugestoes.configure(height=0)

    def popup_detalhe(self, dados):
        placa, veiculo, entrada, saida, valor, id_reg = dados
        self.popup = ctk.CTkToplevel(self)
        self.popup.title(f"Detalhes - {id_reg} - {placa}")
        self.popup.geometry("400x470")
        self.popup.attributes("-topmost", True)

        ctk.CTkLabel(self.popup, text="DETALHES DO VEÍCULO", font=("Arial", 18, "bold")).pack(pady=20)
        info_frame = ctk.CTkFrame(self.popup)
        info_frame.pack(padx=20, pady=10, fill="both", expand=True)

        detalhes = [f"PLACA: {placa}", f"MODELO: {veiculo}", f"ENTRADA: {entrada}", f"SAÍDA: {saida if saida else 'Ainda no Pátio'}", f"VALOR: R$ {valor:.2f}"]
        for info in detalhes:
            ctk.CTkLabel(info_frame, text=info, font=("Arial", 14)).pack(pady=5, anchor="w", padx=20)

        btn_print = ctk.CTkButton(self.popup, text="REIMPRIMIR TICKET", fg_color="#34495e", command=lambda: [self.reimprimir_especifico(dados), self.popup.destroy()])
        btn_print.pack(pady=10, padx=30, fill="x")

        if not saida:
            btn_sair = ctk.CTkButton(self.popup, text="DAR SAÍDA AGORA", fg_color="#e74c3c", command=lambda: [self.entry_placa.delete(0, 'end'), self.entry_placa.insert(0, placa), self.executar_saida(), self.popup.destroy()])
            btn_sair.pack(pady=10, padx=30, fill="x")

        btn_fechar = ctk.CTkButton(self.popup, text="FECHAR", fg_color="transparent", border_width=1, command=self.popup.destroy)
        btn_fechar.pack(pady=10)

    def abrir_mensalistas(self):
        janela = ctk.CTkToplevel(self)
        janela.title("Cadastro de Mensalistas")
        janela.geometry("650x550")
        janela.attributes("-topmost", True)
        janela.focus()
        frame_campos = ctk.CTkFrame(janela, fg_color="transparent")
        frame_campos.pack(padx=15, pady=15, fill="both", expand=True)
        campos = [("Nome", 0, 0), ("CPF", 0, 1), ("Telefone", 1, 0), ("Placa", 1, 1), ("Veículo", 2, 0), ("CEP", 2, 1), ("Endereço", 3, 0), ("Bairro", 3, 1), ("Cidade", 4, 0), ("UF", 4, 1), ("Data Vencimento", 5, 0), ("Valor da Mensalidade", 5, 1)]
        entries = {}
        for nome, r, c in campos:
            f = ctk.CTkFrame(frame_campos, fg_color="transparent")
            f.grid(row=r, column=c, padx=15, pady=10, sticky="w")
            ctk.CTkLabel(f, text=nome.upper(), font=("Arial", 11, "bold")).pack(anchor="w")
            en = ctk.CTkEntry(f, width=250)
            en.pack()
            entries[nome] = en
        def salvar():
            dados = {n: entries[n].get().upper().strip() for n, r, c in campos}
            if not dados["Placa"] or not dados["Nome"]: return
            funcoes.salvar_mensalista(dados)
            messagebox.showinfo("Sucesso", "Mensalista cadastrado!")
            janela.destroy()
        ctk.CTkButton(janela, text="SALVAR MENSALISTA", fg_color="#27ae60", height=40, command=salvar).pack(pady=20)

    def abrir_config_precos(self):
        janela = ctk.CTkToplevel(self)
        janela.title("Tabela de Preços")
        janela.geometry("850x420")
        janela.attributes("-topmost", True)
        header = ["TAMANHO", "15 MIN", "30 MIN", "45 MIN", "60 MIN", "75 MIN", "EXTRA 15m", "DIÁRIA",]
        for i, h in enumerate(header): ctk.CTkLabel(janela, text=h, font=("Arial", 11, "bold")).grid(row=0, column=i, padx=10, pady=15)
        entries = {}
        linhas = funcoes.obter_tabela_precos()
        nomes = {1: "1 - PEQUENO", 2: "2 - GRANDE", 3: "3 - FURGÃO"}
        for r_idx, row in enumerate(linhas):
            ctk.CTkLabel(janela, text=nomes[row[0]], font=("Arial", 10, "bold")).grid(row=r_idx+1, column=0, padx=10)
            for c_idx in range(1, 8):
                e = ctk.CTkEntry(janela, width=80, justify="center")
                e.insert(0, f"{row[c_idx]:.2f}")
                e.grid(row=r_idx+1, column=c_idx, padx=5, pady=8)
                entries[(row[0], c_idx)] = e
        def salvar():
            for t in [1, 2, 3]:
                vals = [float(entries[(t, c)].get().replace(',', '.')) for c in range(1, 8)]
                funcoes.atualizar_precos(t, vals)
            messagebox.showinfo("Sucesso", "Preços atualizados!")
            janela.destroy()
        ctk.CTkButton(janela, text="SALVAR TABELA", fg_color="#27ae60", command=salvar).grid(row=5, column=0, columnspan=8, pady=30)

    def buscar_historico(self):
        for widget in self.frame_scroll_lista.winfo_children(): widget.destroy()
    
        termo = self.entry_busca_rapida.get().strip()
        
        if termo:
            dados = funcoes.buscar_por_termo(termo)
        else:
            data_selecionada = self.cal_data.get()
            dados = funcoes.buscar_por_data(data_selecionada)
        for item in dados:
            id_banco, placa_val, veiculo_val, entrada_val, saida_val, valor_db, tamanho_val =item[0], item[1], item[2], (item[3] if item[3] else "---")[:15], item[4], item[5], item[6]
            if not saida_val:
                valor_exibir = funcoes.calcular_valor_estacionamento(entrada_val, tamanho_val, placa_val) if len(item) > 6 else 0
                status_txt = f"R$ {valor_exibir:.2f}"
                cor_txt_status = "#2980b9"
            else:
                valor_exibir = valor_db
                status_txt = f"SAÍDA: {saida_val} | R$ {valor_exibir:.2f}"
                cor_txt_status = "#7f8c8d"

            cor_card = "#ebf5fb" if not saida_val else "#f4f6f7"
            cor_borda = "#3498db" if not saida_val else "#bdc3c7"
            card = ctk.CTkFrame(self.frame_scroll_lista, fg_color=cor_card, border_color=cor_borda, border_width=1, height=30)
            card.pack(fill="x", pady=2, padx=2)
            card.pack_propagate(False)
            
            dados_popup = [item[1], item[2], item[3], item[4], (valor_exibir if not saida_val else valor_db), item[0]]
            abrir_detalhe = lambda e, d=dados_popup: self.popup_detalhe(d)
            card.bind("<Button-1>", abrir_detalhe)

            lbl_id = ctk.CTkLabel(card, text=f"#{id_banco}", font=("Arial", 10), width=30, text_color="gray")
            lbl_id.pack(side="left", padx=5)
            lbl_placa = ctk.CTkLabel(card, text=placa_val, font=("Arial", 14, "bold"), width=100, anchor="w")
            lbl_placa.pack(side="left", padx=15)
            lbl_veiculo = ctk.CTkLabel(card, text=veiculo_val, font=("Arial", 13), width=150, anchor="w")
            lbl_veiculo.pack(side="left", padx=10)
            lbl_entrada = ctk.CTkLabel(card, text=f"ENT: {entrada_val}", font=("Arial", 12), width=100, anchor="w")
            lbl_entrada.pack(side="left", padx=10)
            lbl_status = ctk.CTkLabel(card, text=status_txt, font=("Arial", 12, "bold"), text_color=cor_txt_status)
            lbl_status.pack(side="right", padx=15)
            for w in [lbl_placa, lbl_veiculo, lbl_entrada, lbl_status]: w.bind("<Button-1>", abrir_detalhe)

        no_patio = len([x for x in dados if not x[4]])
        sairam = len([x for x in dados if x[4]])
        self.lbl_ativos.configure(text=f"No Pátio: {no_patio}")
        self.lbl_finalizados.configure(text=f"Saíram Hoje: {sairam}")

    def executar_entrada(self):
        placa = self.entry_placa.get().upper().strip()
        veiculo = self.entry_veiculo.get().upper().strip() or "não informado"
        tamanho = self.op_tamanho.get()[0]
        if len(placa) >= 7:
            if funcoes.veiculo_no_patio(placa):
                messagebox.showwarning("Aviso", f"Veiculo {placa} já está no pátio")
                return 
            hora, id_gerado = funcoes.registrar_entrada(placa, veiculo, tamanho)
            if self.check_imprimir.get():
                ticket = funcoes.gerar_layout_ticket(placa, veiculo, hora, id_controle=id_gerado)
                self.imprimir_ticket(ticket)
            self.limpar_placa()
            self.buscar_historico()

    def executar_saida(self):
        placa = self.entry_placa.get().upper().strip()
        if placa:
            ent, sai, val, veiculo, id_reg = funcoes.dar_saida_banco(placa)
            if ent:
                ticket = funcoes.gerar_layout_ticket(placa, veiculo, ent, sai, val, id_controle=id_reg)
                self.imprimir_ticket(ticket)
                self.limpar_placa()
                self.buscar_historico()

    def reimprimir_especifico(self, dados):
        placa, veic, ent, sai, val = dados[:5]
        id_c = dados[5] if len(dados) > 5 else None
        
        ticket = funcoes.gerar_layout_ticket(
            placa=placa, 
            veiculo=veic, 
            ent=ent, 
            sai=sai, 
            valor=val, 
            id_controle=id_c
        )
        self.imprimir_ticket(ticket)

    def imprimir_ticket(self, texto):
        try:
            lista_p = [p[2] for p in win32print.EnumPrinters(2)]
            nome_impressora = next((p for p in lista_p if "ELGIN" in p.upper()), win32print.GetDefaultPrinter())
            hPrinter = win32print.OpenPrinter(nome_impressora)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Ticket Park", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, texto.encode('cp850'))
                win32print.WritePrinter(hPrinter, b"\x1d\x56\x01") 
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
            finally: win32print.ClosePrinter(hPrinter)
        except: pass

    def limpar_placa(self):
        self.entry_placa.delete(0, 'end')
        self.entry_veiculo.delete(0, 'end')
        self.fechar_sugestoes()
        self.entry_placa.focus()

if __name__ == "__main__":
    app = App()
    app.mainloop()