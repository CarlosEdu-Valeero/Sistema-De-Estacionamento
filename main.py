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

        self.btn_config = ctk.CTkButton(self.frame_menu, text="Configurar Preços", fg_color="transparent", 
                                       border_width=1, text_color="black", command=self.abrir_config_precos)
        self.btn_config.pack(pady=10, padx=30, fill="x")

        self.lbl_ativos = ctk.CTkLabel(self.frame_menu, text="No Pátio: 0", font=("Arial", 18, "bold"), text_color="#3498db")
        self.lbl_ativos.pack(pady=(20, 5))
        
        self.lbl_finalizados = ctk.CTkLabel(self.frame_menu, text="Saíram Hoje: 0", font=("Arial", 14))
        self.lbl_finalizados.pack(pady=5)

        ctk.CTkLabel(self.frame_menu, text="PLACA DO VEÍCULO", font=("Arial", 12)).pack(pady=(30, 0))
        self.entry_placa = ctk.CTkEntry(self.frame_menu, width=220, height=50, font=("Arial", 26, "bold"), justify="center")
        self.entry_placa.pack(pady=10)
        self.entry_placa.focus()

        ctk.CTkLabel(self.frame_menu, text="MODELO VEÍCULO", font=("Arial", 12)).pack(pady=(10, 0))
        self.entry_veiculo = ctk.CTkEntry(self.frame_menu, width=220, height=35, font=("Arial", 16))
        self.entry_veiculo.pack(pady=5)

        self.frame_sugestoes = ctk.CTkScrollableFrame(self.frame_menu, width=210, height=0) # Começa invisível
        self.entry_veiculo.bind('<KeyRelease>', self.buscar_sugestoes)
        
        self.entry_placa.bind('<KeyRelease>', self.formatar_placa)

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
        
        self.frame_scroll_lista = ctk.CTkScrollableFrame(self.frame_lista, fg_color="transparent")
        self.frame_scroll_lista.pack(expand=True, fill="both", padx=10, pady=10)

        self.buscar_historico()

    def selecionar_da_lista(self, dados=None):
        if hasattr(self, "popup") and self.popup and self.popup.winfo_exists():
            return
        
        try:
            linha_texto = self.txt_lista.get("insert linestart", "insert lineend")
        
            if "|" in linha_texto:
                placa = linha_texto.split("|")[0].strip()
                dados = funcoes.buscar_dados_placa(placa)
            if dados:
                self.popup_detalhe(dados)
        except Exception as e:
            print(f"Erro ao selecionar: {e}")

    def buscar_sugestoes(self, event):
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return

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

            if modelos:
                self.mostrar_sugestoes(modelos)
            else:
                self.fechar_sugestoes()
        except Exception as e:
            print(f"Erro ao buscar modelos: {e}")

    def mostrar_sugestoes(self, modelos):
        for widget in self.frame_sugestoes.winfo_children():
            widget.destroy()

        self.frame_sugestoes.configure(height=120) 
        self.frame_sugestoes.pack(pady=0)

        for m in modelos:
            nome_modelo = m[0]
            btn = ctk.CTkButton(
                self.frame_sugestoes, 
                text=nome_modelo, 
                fg_color="transparent", 
                text_color="black",
                hover_color="#eee",
                anchor="w",
                height=25,
                command=lambda n=nome_modelo: self.selecionar_modelo(n)
            )
            btn.pack(fill="x")

    def selecionar_modelo(self, nome):
        self.entry_veiculo.delete(0, 'end')
        self.entry_veiculo.insert(0, nome)
        self.fechar_sugestoes()

    def fechar_sugestoes(self):
        self.frame_sugestoes.pack_forget()
        self.frame_sugestoes.configure(height=0)

    def popup_detalhe(self, dados):
        placa, veiculo, entrada, saida, valor = dados

        if not saida and (valor == 0 or valor == 0.0):
            valor = funcoes.calcular_valor_atual(entrada)

        self.popup = ctk.CTkToplevel(self)
        self.popup.title(f"Detalhes - {placa}")
        self.popup.geometry("400x470")
        self.popup.attributes("-topmost", True)

        ctk.CTkLabel(self.popup, text="DETALHES DO VEÍCULO", font=("Arial", 18, "bold")).pack(pady=20)
    
        info_frame = ctk.CTkFrame(self.popup)
        info_frame.pack(padx=20, pady=10, fill="both", expand=True)

        detalhes = [
            f"PLACA: {placa}",
            f"MODELO: {veiculo}",
            f"ENTRADA: {entrada}",
            f"SAÍDA: {saida if saida else 'Ainda no Pátio'}",
            f"VALOR: R$ {valor:.2f}"
        ]

        for info in detalhes:
            ctk.CTkLabel(info_frame, text=info, font=("Arial", 14)).pack(pady=5, anchor="w", padx=20)

        dados_atualizados = (placa, veiculo, entrada, saida, valor)
        btn_print = ctk.CTkButton(self.popup, text="REIMPRIMIR TICKET", fg_color="#34495e", 
                               command=lambda: [self.reimprimir_especifico(dados_atualizados), self.popup.destroy()])
        btn_print.pack(pady=10, padx=30, fill="x")

        if not saida:
            btn_sair = ctk.CTkButton(self.popup, text="DAR SAÍDA AGORA", fg_color="#e74c3c", 
                                  command=lambda: [self.entry_placa.delete(0, 'end'), 
                                                 self.entry_placa.insert(0, placa), 
                                                 self.executar_saida(), 
                                                 self.popup.destroy()])
            btn_sair.pack(pady=10, padx=30, fill="x")

        btn_fechar = ctk.CTkButton(self.popup, text="FECHAR", fg_color="transparent", border_width=1, 
                                 command=self.popup.destroy)
        btn_fechar.pack(pady=10)

    def formatar_placa(self, event):
        if event.keysym == "BackSpace": return
        texto = self.entry_placa.get().upper().replace("-", "")
        if len(texto) >= 3:
            novo = texto[:3] + "-" + texto[3:7]
            if self.entry_placa.get() != novo:
                self.entry_placa.delete(0, "end")
                self.entry_placa.insert(0, novo)

    def limpar_placa(self):
        self.entry_placa.delete(0, 'end')
        self.entry_veiculo.delete(0, 'end')
        self.fechar_sugestoes()
        self.entry_placa.focus()

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
            finally:
                win32print.ClosePrinter(hPrinter)
        except Exception as e:
            print(f"Erro Impressora: {e}")

    def atualizar_contadores(self, dados):
        no_patio = len([x for x in dados if not x[4]])
        sairam = len([x for x in dados if x[4]])
        self.lbl_ativos.configure(text=f"No Pátio: {no_patio}")
        self.lbl_finalizados.configure(text=f"Saíram Hoje: {sairam}")

    def buscar_historico(self):
        for widget in self.frame_scroll_lista.winfo_children():
            widget.destroy()

        data = self.cal_data.get()
        dados = funcoes.buscar_por_data(data)
        
        for item in dados:
            placa_val = item[1]
            veiculo_val = (item[2] if item[2] else "---")[:15]
            entrada_val = item[3]
            saida_val = item[4]
            valor_db = item[5]
            
            if not saida_val:
                valor_exibir = funcoes.calcular_valor_atual(entrada_val)
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

            dados_popup = [item[1], item[2], item[3], item[4], (valor_exibir if not saida_val else valor_db)]
            abrir_detalhe = lambda e, d=dados_popup: self.popup_detalhe(d)

            card.bind("<Button-1>", abrir_detalhe)

            lbl_placa = ctk.CTkLabel(card, text=placa_val, font=("Arial", 14, "bold"), width=100, anchor="w")
            lbl_placa.pack(side="left", padx=15)

            lbl_veiculo = ctk.CTkLabel(card, text=veiculo_val, font=("Arial", 13), width=150, anchor="w")
            lbl_veiculo.pack(side="left", padx=10)

            lbl_entrada = ctk.CTkLabel(card, text=f"ENT: {entrada_val}", font=("Arial", 12), width=100, anchor="w")
            lbl_entrada.pack(side="left", padx=10)

            lbl_status = ctk.CTkLabel(card, text=status_txt, font=("Arial", 12, "bold"), text_color=cor_txt_status)
            lbl_status.pack(side="right", padx=15)

            for widget in [lbl_placa, lbl_veiculo, lbl_entrada, lbl_status]:
                widget.bind("<Button-1>", abrir_detalhe)

        self.atualizar_contadores(dados)

    def executar_entrada(self):
        placa = self.entry_placa.get().upper()
        veiculo = self.entry_veiculo.get().upper() or "não informado"
        if len(placa) >= 8:
            if funcoes.veiculo_no_patio(placa):
                messagebox.showwarning(f"Veiculo {placa} já está no pátio")
                return 
            hora = funcoes.registrar_entrada(placa, veiculo)
            if self.check_imprimir.get():
                ticket = funcoes.gerar_layout_ticket(placa, veiculo, hora)
                self.imprimir_ticket(ticket)
            self.entry_placa.delete(0, 'end')
            self.entry_veiculo.delete(0, 'end')
            self.entry_placa.focus()
            self.fechar_sugestoes()
            self.buscar_historico()

    def executar_saida(self):
        placa = self.entry_placa.get().upper()
        if placa:
            ent, sai, val, veiculo = funcoes.dar_saida_banco(placa)
            if ent:
                ticket = funcoes.gerar_layout_ticket(placa, veiculo, ent, sai, val)
                self.imprimir_ticket(ticket)
                self.entry_placa.delete(0, 'end')
                self.entry_veiculo.delete(0, 'end')
                self.fechar_sugestoes()
                self.buscar_historico()
            else:
                print("Placa não encontrada no pátio.")

    def reimprimir_especifico(self, dados):
        ticket = funcoes.gerar_layout_ticket(dados[0], dados[1], dados[2], dados[3], dados[4])
        self.imprimir_ticket(ticket)
    
    def abrir_config_precos(self):
        janela = ctk.CTkToplevel(self)
        janela.title("Configurar Tabela de Preços")
        janela.geometry("400x500")
        janela.grab_set()
        janela.attributes("-topmost", True)

        ctk.CTkLabel(janela, text="CONFIGURAR FAIXAS DE PREÇO", font=("Arial", 16, "bold")).pack(pady=10)
        ctk.CTkLabel(janela, text="Defina o tempo máximo (min) e o valor (R$)", font=("Arial", 10)).pack(pady=5)

        container = ctk.CTkScrollableFrame(janela, width=350, height=300)
        container.pack(pady=10, padx=10)

        rows = []
        
        def renderizar_linhas():
            for w in container.winfo_children(): w.destroy()
            rows.clear()
            
            conn = sqlite3.connect('estacionamento.db')
            cursor = conn.cursor()
            cursor.execute("SELECT minutos_limite, valor FROM precos_faixas ORDER BY minutos_limite ASC")
            dados = cursor.fetchall()
            conn.close()

            for lim, val in dados:
                f = ctk.CTkFrame(container, fg_color="transparent")
                f.pack(fill="x", pady=2)
                e_min = ctk.CTkEntry(f, width=100)
                e_min.insert(0, str(lim))
                e_min.pack(side="left", padx=5)
                
                e_val = ctk.CTkEntry(f, width=100)
                e_val.insert(0, f"{val:.2f}")
                e_val.pack(side="left", padx=5)
                
                rows.append((e_min, e_val))

        def salvar():
            try:
                novas_regras = []
                for e_m, e_v in rows:
                    m = int(e_m.get())
                    v = float(e_v.get().replace(',', '.'))
                    novas_regras.append((m, v))
                
                conn = sqlite3.connect('estacionamento.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM precos_faixas")
                cursor.executemany("INSERT INTO precos_faixas (minutos_limite, valor) VALUES (?, ?)", novas_regras)
                conn.commit()
                conn.close()
                messagebox.showinfo("Sucesso", "Preços atualizados!")
                janela.destroy()
            except:
                messagebox.showerror("Erro", "Valores inválidos!")

        def add_linha():
            f = ctk.CTkFrame(container, fg_color="transparent")
            f.pack(fill="x", pady=2)
            e_m = ctk.CTkEntry(f, width=100); e_m.pack(side="left", padx=5)
            e_v = ctk.CTkEntry(f, width=100); e_v.pack(side="left", padx=5)
            rows.append((e_m, e_v))

        renderizar_linhas()
        
        ctk.CTkButton(janela, text="+ Adicionar Faixa", fg_color="#34495e", command=add_linha).pack(pady=5)
        ctk.CTkButton(janela, text="SALVAR TUDO", fg_color="#27ae60", command=salvar).pack(pady=10, padx=20, fill="x")

if __name__ == "__main__":
    app = App()
    app.mainloop()