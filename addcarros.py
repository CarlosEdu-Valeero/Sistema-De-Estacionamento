import customtkinter as ctk
from tkinter import messagebox
import sqlite3

BANCO_DADOS = 'modelos_veiculos.db'

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.inicializar_banco()

        self.title("ADICIONAR VEICULOS - CENTRAL PARK")
        self.geometry("400x600")
        ctk.set_appearance_mode("light")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.frame_topo = ctk.CTkFrame(self, corner_radius=10)
        self.frame_topo.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(self.frame_topo, text="NOME DO MODELO", font=("Arial", 12, "bold")).pack(pady=(15, 0))
        
        self.entry_modelo = ctk.CTkEntry(self.frame_topo, width=300, height=40, font=("Arial", 16))
        self.entry_modelo.pack(pady=10)
        self.entry_modelo.bind("<Return>", lambda e: self.salvar_modelo()) # Salva ao apertar Enter

        self.btn_salvar = ctk.CTkButton(self.frame_topo, text="ADICIONAR MODELO", fg_color="#27ae60", 
                                        hover_color="#1e8449", command=self.salvar_modelo)
        self.btn_salvar.pack(pady=15)

        self.frame_lista = ctk.CTkFrame(self, corner_radius=10)
        self.frame_lista.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

        ctk.CTkLabel(self.frame_lista, text="BUSCAR MODELO:", font=("Arial", 12)).pack(pady=(10, 0))
        self.entry_busca = ctk.CTkEntry(self.frame_lista, width=300, placeholder_text="Digite para filtrar...")
        self.entry_busca.pack(pady=5)
        self.entry_busca.bind("<KeyRelease>", lambda e: self.atualizar_lista())

        self.txt_lista = ctk.CTkTextbox(self.frame_lista, font=("Arial", 14), state="disabled")
        self.txt_lista.pack(expand=True, fill="both", padx=15, pady=15)

        self.atualizar_lista()

    def inicializar_banco(self):
        conn = sqlite3.connect(BANCO_DADOS)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS modelos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE
            )
        ''')
        conn.commit()
        conn.close()

    def salvar_modelo(self):
        nome = self.entry_modelo.get().upper().strip()
        if not nome:
            return

        try:
            conn = sqlite3.connect(BANCO_DADOS)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO modelos (nome) VALUES (?)", (nome,))
            conn.commit()
            conn.close()
            
            self.entry_modelo.delete(0, 'end')
            self.atualizar_lista()
        except sqlite3.IntegrityError:
            messagebox.showwarning("Aviso", "Este modelo já está cadastrado!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    def atualizar_lista(self):
        termo = self.entry_busca.get().upper()
        
        conn = sqlite3.connect(BANCO_DADOS)
        cursor = conn.cursor()
        if termo:
            cursor.execute("SELECT nome FROM modelos WHERE nome LIKE ? ORDER BY nome ASC", (f'%{termo}%',))
        else:
            cursor.execute("SELECT nome FROM modelos ORDER BY nome ASC")
        
        modelos = cursor.fetchall()
        conn.close()

        self.txt_lista.configure(state="normal")
        self.txt_lista.delete("1.0", "end")
        for m in modelos:
            self.txt_lista.insert("end", f"• {m[0]}\n")
        self.txt_lista.configure(state="disabled")

if __name__ == "__main__":
    app = App()
    app.mainloop()