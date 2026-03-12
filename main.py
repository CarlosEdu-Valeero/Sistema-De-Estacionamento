import customtkinter as ctk
from tkinter import messagebox 
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
        
        self.entry_data = ctk.CTkEntry(self.frame_busca, width=120)
        self.entry_data.insert(0, datetime.now().strftime('%d/%m/%Y'))
        self.entry_data.pack(side="left", padx=5)
        
        ctk.CTkButton(self.frame_busca, text="Buscar Data", width=100, command=self.buscar_historico).pack(side="left", padx=5)

        self.txt_lista = ctk.CTkTextbox(self.frame_lista, font=("Courier New", 14))
        self.txt_lista.bind("<ButtonRelease-1>", self.selecionar_da_lista)
        self.txt_lista.pack(expand=True, fill="both", padx=10, pady=10)

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

    def popup_detalhe(self,dados):
        placa,veiculo,entrada,saida,valor=dados

        self.popup = ctk.CTkToplevel(self)
        self.popup.title(f"Detalhes - {placa}")
        self.popup.geometry("400x450")
        self.popup.grab_set()
        self.popup.attributes("-topmost", True)

        ctk.CTkLabel(self.popup, text="DETALHES DO VEÍCULO", font=("Arial", 18, "bold")).pack(pady=20)
    
        info_frame = ctk.CTkFrame(self.popup)
        info_frame.pack(padx=20, pady=10, fill="both", expand=True)
        detalhes = [
        f"PLACA: {placa}",
        f"MODELO: {veiculo}",
        f"ENTRADA: {entrada}",
        f"SAÍDA: {saida if saida else 'Ainda no Pátio'}",
        f"VALOR: R$ {valor if valor else 0.0:.2f}"
        ]

        for info in detalhes:
            ctk.CTkLabel(info_frame, text=info, font=("Arial", 14)).pack(pady=5, anchor="w", padx=20)
        btn_print = ctk.CTkButton(self.popup, text="REIMPRIMIR TICKET", fg_color="#34495e", 
                               command=lambda: [self.reimprimir_especifico(dados), self.popup.destroy()])
        btn_print.pack(pady=10, padx=30, fill="x")

        if not saida:
            btn_sair = ctk.CTkButton(self.popup, text="DAR SAÍDA AGORA", fg_color="#e74c3c", 
                                  command=lambda: [self.entry_placa.insert(0, placa), self.executar_saida(), self.popup.destroy()])
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
        data = self.entry_data.get()
        dados = funcoes.buscar_por_data(data)
        self.txt_lista.delete("1.0", "end")
        for item in dados:
            placa = item[1]
            veiculo = item[2] if item[2] else "---"
            entrada = item[3]
            saida = item[4]
            status = " [PÁTIO]" if not saida else f" [SAIU {saida}]"
            linha = f"{placa} | {veiculo} | Ent: {entrada}{status}\n"
            self.txt_lista.insert("end", linha)
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
                if self.check_imprimir.get():
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

if __name__ == "__main__":
    app = App()
    app.mainloop()