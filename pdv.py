import customtkinter as ctk
from tkinter import ttk, messagebox, Toplevel, scrolledtext, filedialog
import sqlite3
from datetime import datetime, timedelta
import hashlib # Para hash de senhas (melhor segurança)
import os # Para lidar com caminhos de arquivo
import shutil # Para operações de arquivo como cópia
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from PIL import Image, ImageTk # Importar para manipulação de imagens

# Configuração inicial do tema CustomTkinter
ctk.set_appearance_mode("Light")  # Tema inicial: Claro
ctk.set_default_color_theme("blue") # Base do tema de cores para usar CustomTkinter

class AuthApp:
    def __init__(self, master):
        """
        Inicializa a aplicação de autenticação (Login/Cadastro).

        Args:
            master: A janela principal do CustomTkinter (CTk).
        """
        self.master = master
        master.title("Organizer - Login / Cadastro")
        
        # Centraliza a janela de login
        window_width = 450
        window_height = 500
        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()
        x_cordinate = int((screen_width/2) - (window_width/2))
        y_cordinate = int((screen_height/2) - (window_height/2))
        master.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
        master.resizable(False, False) # Mantém não redimensionável para tela de login

        self.db_name = "pdv.db" # Usaremos o mesmo DB para usuários e PDV
        self._init_auth_db()

        self.login_frame = ctk.CTkFrame(master, corner_radius=15, fg_color=("gray90", "gray15")) # Fundo do frame de login
        self.login_frame.pack(pady=40, padx=40, fill="both", expand=True)
        self.login_frame.grid_columnconfigure(0, weight=1)
        self.login_frame.grid_rowconfigure((0,1,2,3,4,5,6,7,8,9,10), weight=1)

        self.create_login_widgets()

    def _init_auth_db(self):
        """
        Inicializa o banco de dados para autenticação, criando a tabela de usuários se não existir.
        Lida com a migração para remover a restrição UNIQUE da coluna 'establishment_name'
        se o banco de dados já existir com a estrutura antiga, e garante que a coluna 'role' exista.
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Verifica se a tabela 'users' existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        table_exists = cursor.fetchone()

        if table_exists:
            # Obtém a definição atual da tabela 'users'
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
            create_table_sql = cursor.fetchone()[0]
            
            # Verifica se o fragmento antigo (com UNIQUE em establishment_name) está presente
            old_fragment = "establishment_name TEXT NOT NULL UNIQUE"

            if old_fragment in create_table_sql:
                print("Migração necessária: a coluna 'establishment_name' possui restrição UNIQUE. Realizando migração.")
                cursor.execute("ALTER TABLE users RENAME TO old_users")

                cursor.execute("""
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        establishment_name TEXT NOT NULL,
                        username TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        role TEXT DEFAULT 'caixa' NOT NULL
                    )
                """)

                cursor.execute("""
                    INSERT INTO users (id, establishment_name, username, password_hash, role)
                    SELECT id, establishment_name, username, password_hash, role FROM old_users
                """)

                cursor.execute("DROP TABLE old_users")
                print("Migração concluída: restrição UNIQUE removida de 'establishment_name'.")
            
            # Garante que a coluna 'role' exista, para compatibilidade com DBs muito antigos
            cursor.execute("PRAGMA table_info(users)")
            current_columns = [col[1] for col in cursor.fetchall()]
            if 'role' not in current_columns:
                print("Adicionando coluna 'role'.")
                cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'caixa' NOT NULL")
        else:
            # A tabela 'users' não existe, então a cria com a estrutura correta (sem UNIQUE em establishment_name)
            cursor.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    establishment_name TEXT NOT NULL,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'caixa' NOT NULL
                )
            """)
        conn.commit()
        conn.close()

    def hash_password(self, password):
        """
        Gera o hash SHA256 de uma senha.
        """
        return hashlib.sha256(password.encode()).hexdigest()

    def create_login_widgets(self):
        """
        Cria os widgets para a tela de login.
        """
        for widget in self.login_frame.winfo_children():
            widget.destroy()

        self.login_frame.grid_rowconfigure((0,1,2,3,4,5,6,7,8,9), weight=1)
        self.login_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.login_frame, text="Bem-vindo ao Organizer", font=ctk.CTkFont(size=24, weight="bold"), text_color=("gray10", "gray90")).grid(row=1, column=0, pady=(20,10))
        ctk.CTkLabel(self.login_frame, text="Login de Estabelecimento", font=ctk.CTkFont(size=18)).grid(row=2, column=0, pady=5)

        ctk.CTkLabel(self.login_frame, text="Nome de Usuário:", text_color=("gray10", "gray90")).grid(row=3, column=0, pady=(10,0))
        self.username_entry = ctk.CTkEntry(self.login_frame, width=280, corner_radius=10, placeholder_text="Seu nome de usuário")
        self.username_entry.grid(row=4, column=0, pady=5)

        ctk.CTkLabel(self.login_frame, text="Senha:", text_color=("gray10", "gray90")).grid(row=5, column=0, pady=(10,0))
        self.password_entry = ctk.CTkEntry(self.login_frame, show="*", width=280, corner_radius=10, placeholder_text="Sua senha")
        self.password_entry.grid(row=6, column=0, pady=5)

        self.login_button = ctk.CTkButton(self.login_frame, text="Entrar", command=self.attempt_login,
                                            fg_color="#4CAF50", hover_color="#45a049", corner_radius=10,
                                            font=ctk.CTkFont(size=15, weight="bold"))
        self.login_button.grid(row=7, column=0, pady=25)

        ctk.CTkLabel(self.login_frame, text="Não tem uma conta?", text_color=("gray10", "gray90")).grid(row=8, column=0, pady=(10,0))
        self.register_button = ctk.CTkButton(self.login_frame, text="Cadastre-se", command=self.create_register_widgets,
                                                fg_color="#2196F3", hover_color="#1976D2", corner_radius=10,
                                                font=ctk.CTkFont(size=15))
        self.register_button.grid(row=9, column=0, pady=5)

    def create_register_widgets(self):
        """
        Cria os widgets para a tela de cadastro.
        """
        for widget in self.login_frame.winfo_children():
            widget.destroy()

        self.login_frame.grid_rowconfigure((0,1,2,3,4,5,6,7,8,9,10,11), weight=1)
        self.login_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.login_frame, text="Cadastre Seu Estabelecimento", font=ctk.CTkFont(size=22, weight="bold"), text_color=("gray10", "gray90")).grid(row=1, column=0, pady=(20,10))

        ctk.CTkLabel(self.login_frame, text="Nome do Estabelecimento:", text_color=("gray10", "gray90")).grid(row=2, column=0, pady=(10,0))
        self.establishment_name_entry = ctk.CTkEntry(self.login_frame, width=280, corner_radius=10, placeholder_text="Ex: Minha Loja")
        self.establishment_name_entry.grid(row=3, column=0, pady=5)

        ctk.CTkLabel(self.login_frame, text="Nome de Usuário (Admin):", text_color=("gray10", "gray90")).grid(row=4, column=0, pady=(10,0))
        self.reg_username_entry = ctk.CTkEntry(self.login_frame, width=280, corner_radius=10, placeholder_text="Ex: admin_principal")
        self.reg_username_entry.grid(row=5, column=0, pady=5)

        ctk.CTkLabel(self.login_frame, text="Senha:", text_color=("gray10", "gray90")).grid(row=6, column=0, pady=(10,0))
        self.reg_password_entry = ctk.CTkEntry(self.login_frame, show="*", width=280, corner_radius=10, placeholder_text="Sua senha")
        self.reg_password_entry.grid(row=7, column=0, pady=5)

        ctk.CTkLabel(self.login_frame, text="Confirmar Senha:", text_color=("gray10", "gray90")).grid(row=8, column=0, pady=(10,0))
        self.reg_confirm_password_entry = ctk.CTkEntry(self.login_frame, show="*", width=280, corner_radius=10, placeholder_text="Confirme sua senha")
        self.reg_confirm_password_entry.grid(row=9, column=0, pady=5)

        self.register_user_button = ctk.CTkButton(self.login_frame, text="Registrar Estabelecimento", command=self.register_user,
                                                    fg_color="#4CAF50", hover_color="#45a049", corner_radius=10,
                                                    font=ctk.CTkFont(size=15, weight="bold"))
        self.register_user_button.grid(row=10, column=0, pady=25)

        self.back_to_login_button = ctk.CTkButton(self.login_frame, text="Voltar ao Login", command=self.create_login_widgets,
                                                    fg_color="#F44336", hover_color="#D32F2F", corner_radius=10,
                                                    font=ctk.CTkFont(size=15))
        self.back_to_login_button.grid(row=11, column=0, pady=5)

    def attempt_login(self):
        """
        Tenta fazer login com as credenciais fornecidas.
        """
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        password_hash = self.hash_password(password)

        if not username or not password:
            messagebox.showerror("Erro de Login", "Por favor, preencha todos os campos.")
            return

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id, establishment_name, username, password_hash, role FROM users WHERE username=? AND password_hash=?", (username, password_hash))
        user = cursor.fetchone()
        conn.close()

        if user:
            messagebox.showinfo("Login Bem-sucedido", f"Bem-vindo, {user[2]} ({user[4]})!")
            self.master.destroy()
            root_pdv = ctk.CTk()
            root_pdv.state('zoomed')
            PdvApp(root_pdv, user_id=user[0], username=user[2], establishment_name=user[1], user_role=user[4])
            root_pdv.mainloop()
        else:
            messagebox.showerror("Erro de Login", "Nome de usuário ou senha incorretos.")

    def register_user(self):
        """
        Registra um novo usuário/estabelecimento no banco de dados.
        Define o primeiro usuário como 'admin' e os subsequentes como 'caixa'.
        """
        establishment_name = self.establishment_name_entry.get().strip()
        username = self.reg_username_entry.get().strip()
        password = self.reg_password_entry.get().strip()
        confirm_password = self.reg_confirm_password_entry.get().strip()

        if not establishment_name or not username or not password or not confirm_password:
            messagebox.showerror("Erro de Cadastro", "Por favor, preencha todos os campos.")
            return

        if password != confirm_password:
            messagebox.showerror("Erro de Cadastro", "As senhas não coincidem.")
            return

        password_hash = self.hash_password(password)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
            if cursor.fetchone()[0] > 0:
                messagebox.showerror("Erro de Cadastro", "Este nome de usuário já está em uso. Por favor, escolha outro.")
                return

            cursor.execute("SELECT COUNT(*) FROM users WHERE establishment_name = ?", (establishment_name,))
            if cursor.fetchone()[0] > 0:
                messagebox.showerror("Erro de Cadastro", "Este nome de estabelecimento já está em uso. Por favor, escolha outro.")
                return

            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            role_to_assign = 'admin' if user_count == 0 else 'caixa'

            cursor.execute("INSERT INTO users (establishment_name, username, password_hash, role) VALUES (?, ?, ?, ?)",
                           (establishment_name, username, password_hash, role_to_assign))
            conn.commit()
            messagebox.showinfo("Cadastro Bem-sucedido", f"Estabelecimento e usuário '{username}' ({role_to_assign}) cadastrados com sucesso! Faça login para continuar.")
            self.create_login_widgets()
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro no cadastro: {e}")
        finally:
            conn.close()


class PdvApp:
    def __init__(self, master, user_id, username, establishment_name, user_role):
        """
        Inicializa o aplicativo PDV.
        """
        self.master = master
        master.title(f"Organizer - {establishment_name} ({username} - {user_role})")
        
        self.user_id = user_id
        self.username = username
        self.establishment_name = establishment_name
        self.user_role = user_role
        
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=3)
        self.master.grid_rowconfigure(0, weight=1)

        self.db_name = "pdv.db"
        self.MINIMUM_STOCK_THRESHOLD = 5
        self._init_db()

        self.current_cart = {}
        self.selected_product_for_sale_id = None
        self.editing_product_id = None
        self.selected_cart_item_id = None
        self.selected_user_id = None
        self.selected_return_sale_id = None
        self.selected_return_item_id = None
        self.selected_customer_id = None # Novo: ID do cliente selecionado

        self.current_discount_value = 0.0
        self.current_discount_type = "Porcentagem"
        self.current_product_image_path = None # Novo: Caminho da imagem do produto selecionado/em edição

        # Garante que o diretório de imagens de produtos existe
        self.product_images_dir = "product_images"
        os.makedirs(self.product_images_dir, exist_ok=True)

        self.create_widgets()
        self._apply_role_permissions()

    def _init_db(self):
        """
        Inicializa o banco de dados SQLite, criando as tabelas e índices se não existirem.
        Tabelas: products, sales, sale_items, returns, customers.
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Tabela de produtos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                price REAL NOT NULL,
                stock INTEGER NOT NULL,
                image_path TEXT DEFAULT NULL
            )
        """)
        # Adiciona a coluna 'image_path' se não existir
        cursor.execute("PRAGMA table_info(products)")
        product_columns = [col[1] for col in cursor.fetchall()]
        if 'image_path' not in product_columns:
            cursor.execute("ALTER TABLE products ADD COLUMN image_path TEXT DEFAULT NULL")

        # Adiciona índice para pesquisa rápida por nome de produto
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_name ON products (name);")

        # Tabela de clientes (NOVO)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT
            )
        """)
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_name_phone_email ON customers (name, phone, email);") # Índice para unicidade
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_name ON customers (name);")

        # Tabela de vendas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total REAL NOT NULL,
                customer_id INTEGER, -- Novo: ID do cliente vinculado
                customer_name TEXT, -- Mantido para compatibilidade e casos sem customer_id
                payment_method TEXT,
                discount_value REAL DEFAULT 0.0,
                discount_type TEXT DEFAULT 'Nenhum',
                received_amount REAL DEFAULT 0.0,
                change_amount REAL DEFAULT 0.0,
                FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE SET NULL
            )
        """)
        # Adiciona a coluna 'customer_id' e sua FK se não existir
        cursor.execute("PRAGMA table_info(sales)")
        sales_columns = [col[1] for col in cursor.fetchall()]
        if 'customer_id' not in sales_columns:
            cursor.execute("ALTER TABLE sales ADD COLUMN customer_id INTEGER")
            # Adiciona a restrição de chave estrangeira (requer que a tabela não esteja em uso)
            # Para adicionar a FK após a criação da coluna, é geralmente necessário recriar a tabela.
            # No SQLite, ALTER TABLE ADD COLUMN não suporta FOREIGN KEY.
            # Uma forma robusta seria:
            # 1. Renomear a tabela sales para old_sales
            # 2. Criar a nova tabela sales com a FK
            # 3. Copiar dados de old_sales para sales
            # 4. Excluir old_sales
            # Para simplificar agora, se a coluna não existe, apenas a adicionamos,
            # e a FK será efetivada em futuras criações de DB ou se a tabela for migrada.
            # O ON DELETE SET NULL é importante para não apagar vendas ao apagar cliente.

        if 'received_amount' not in sales_columns:
            cursor.execute("ALTER TABLE sales ADD COLUMN received_amount REAL DEFAULT 0.0")
        if 'change_amount' not in sales_columns:
            cursor.execute("ALTER TABLE sales ADD COLUMN change_amount REAL DEFAULT 0.0")

        # Adiciona índices para pesquisa rápida no histórico de vendas
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_timestamp ON sales (timestamp);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_customer_name ON sales (customer_name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_customer_id ON sales (customer_id);") # Novo índice

        # Tabela de itens de venda
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales (id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """)
        # Adiciona índices para pesquisa rápida de itens de venda
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sale_items_sale_id ON sale_items (sale_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sale_items_product_id ON sale_items (product_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sale_items_product_name ON sale_items (product_name);")


        # Tabela para registrar devoluções
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                return_timestamp TEXT NOT NULL,
                reason TEXT,
                processed_by_user_id INTEGER NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales (id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (processed_by_user_id) REFERENCES users (id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_returns_sale_id ON returns (sale_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_returns_timestamp ON returns (return_timestamp);")


        # Adiciona as colunas customer_name e payment_method se não existirem
        cursor.execute("PRAGMA table_info(sales)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'customer_name' not in columns:
            cursor.execute("ALTER TABLE sales ADD COLUMN customer_name TEXT")
        if 'payment_method' not in columns:
            cursor.execute("ALTER TABLE sales ADD COLUMN payment_method TEXT")
        if 'discount_value' not in columns:
            cursor.execute("ALTER TABLE sales ADD COLUMN discount_value REAL DEFAULT 0.0")
        if 'discount_type' not in columns:
            cursor.execute("ALTER TABLE sales ADD COLUMN discount_type TEXT DEFAULT 'Nenhum'")

        conn.commit()
        conn.close()

    def create_widgets(self):
        """
        Cria todos os widgets da interface do usuário (UI) do aplicativo.
        """
        self.primary_green = "#4CAF50"
        self.secondary_green = "#8BC34A"
        self.text_color_light = "white" # Usado em cabeçalhos de Treeview (fundo verde)

        self.sidebar_frame = ctk.CTkFrame(self.master, width=200, corner_radius=0, fg_color=("gray90", "gray15"))
        self.sidebar_frame.grid(row=0, column=0, rowspan=7, sticky="nsew") 
        self.sidebar_frame.grid_rowconfigure(8, weight=1) # Ajuste para acomodar o botão de clientes

        ctk.CTkLabel(self.sidebar_frame, text="🛒 Organizer", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.primary_green).grid(row=0, column=0, padx=20, pady=20)

        self.product_btn = ctk.CTkButton(self.sidebar_frame, text="Gestão de Produtos", command=lambda: self.show_frame("products"),
                                        fg_color=self.primary_green, hover_color=self.secondary_green, corner_radius=10,
                                        font=ctk.CTkFont(size=14, weight="bold"))
        self.product_btn.grid(row=1, column=0, padx=20, pady=10)

        self.sales_btn = ctk.CTkButton(self.sidebar_frame, text="Vendas", command=lambda: self.show_frame("sales"),
                                      fg_color=self.primary_green, hover_color=self.secondary_green, corner_radius=10,
                                      font=ctk.CTkFont(size=14, weight="bold"))
        self.sales_btn.grid(row=2, column=0, padx=20, pady=10)

        self.history_btn = ctk.CTkButton(self.sidebar_frame, text="Histórico de Vendas", command=lambda: self.show_frame("history"),
                                        fg_color=self.primary_green, hover_color=self.secondary_green, corner_radius=10,
                                        font=ctk.CTkFont(size=14, weight="bold"))
        self.history_btn.grid(row=3, column=0, padx=20, pady=10)

        self.returns_btn = ctk.CTkButton(self.sidebar_frame, text="Devoluções/Trocas", command=lambda: self.show_frame("returns"),
                                        fg_color=self.primary_green, hover_color=self.secondary_green, corner_radius=10,
                                        font=ctk.CTkFont(size=14, weight="bold"))
        self.returns_btn.grid(row=4, column=0, padx=20, pady=10)

        self.reports_btn = ctk.CTkButton(self.sidebar_frame, text="Relatórios", command=lambda: self.show_frame("reports"),
                                        fg_color=self.primary_green, hover_color=self.secondary_green, corner_radius=10,
                                        font=ctk.CTkFont(size=14, weight="bold"))
        self.reports_btn.grid(row=5, column=0, padx=20, pady=10)
        
        # NOVO: Botão de Gerenciamento de Clientes
        self.customer_management_btn = ctk.CTkButton(self.sidebar_frame, text="Gestão de Clientes", command=lambda: self.show_frame("customers"),
                                                fg_color=self.primary_green, hover_color=self.secondary_green, corner_radius=10,
                                                font=ctk.CTkFont(size=14, weight="bold"))
        self.customer_management_btn.grid(row=6, column=0, padx=20, pady=10)

        self.user_management_btn = ctk.CTkButton(self.sidebar_frame, text="Gerenciar Usuários", command=lambda: self.show_frame("user_management"),
                                                    fg_color=self.primary_green, hover_color=self.secondary_green, corner_radius=10,
                                                    font=ctk.CTkFont(size=14, weight="bold"))
        self.user_management_btn.grid(row=7, column=0, padx=20, pady=10)


        self.theme_switch_var = ctk.StringVar(value="light")
        self.theme_switch = ctk.CTkSwitch(self.sidebar_frame, text="Tema Escuro", command=self.change_theme,
                                           variable=self.theme_switch_var, onvalue="dark", offvalue="light",
                                           button_color=self.primary_green, progress_color=self.secondary_green,
                                           font=ctk.CTkFont(size=12))
        self.theme_switch.grid(row=8, column=0, padx=20, pady=10, sticky="s") # Ajustei a linha

        self.logout_btn = ctk.CTkButton(self.sidebar_frame, text="Sair", command=self.logout,
                                        fg_color="#F44336", hover_color="#D32F2F", corner_radius=10,
                                        font=ctk.CTkFont(size=14, weight="bold"))
        self.logout_btn.grid(row=9, column=0, padx=20, pady=(10,20), sticky="s") # Ajustei a linha


        self.main_content_frame = ctk.CTkFrame(self.master, fg_color=("white", "gray10"), corner_radius=15)
        self.main_content_frame.grid(row=0, column=1, rowspan=7, sticky="nsew", padx=20, pady=20) 
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)

        self.products_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        self.sales_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        self.history_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        self.returns_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        self.reports_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        self.user_management_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent") 
        self.customers_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent") # NOVO FRAME DE CLIENTES

        # Grid all frames initially to allow show_frame to work by grid_remove/grid
        self.products_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.sales_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.history_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.returns_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.reports_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.user_management_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10) 
        self.customers_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10) # NOVO

        # Immediately hide all frames except the initial one (products_frame)
        self.sales_frame.grid_remove()
        self.history_frame.grid_remove()
        self.returns_frame.grid_remove()
        self.reports_frame.grid_remove()
        self.user_management_frame.grid_remove()
        self.customers_frame.grid_remove() # NOVO

        self.products_frame.grid_columnconfigure(1, weight=1)
        self.products_frame.grid_rowconfigure(9, weight=1)

        self.sales_frame.grid_columnconfigure(0, weight=1)
        self.sales_frame.grid_columnconfigure(1, weight=1)
        
        self.history_frame.grid_columnconfigure(0, weight=1)
        self.history_frame.grid_columnconfigure(1, weight=1)
        self.history_frame.grid_rowconfigure(3, weight=1)

        self.returns_frame.grid_columnconfigure(0, weight=1)
        self.returns_frame.grid_columnconfigure(1, weight=1)
        self.returns_frame.grid_rowconfigure(3, weight=1)
        self.returns_frame.grid_rowconfigure(7, weight=1)

        self.reports_frame.grid_columnconfigure(0, weight=1)
        self.reports_frame.grid_rowconfigure(7, weight=1) 

        self.user_management_frame.grid_columnconfigure(0, weight=1) 
        self.user_management_frame.grid_columnconfigure(1, weight=1)
        self.user_management_frame.grid_rowconfigure(7, weight=1) 

        self.customers_frame.grid_columnconfigure(1, weight=1) # NOVO
        self.customers_frame.grid_rowconfigure(7, weight=1) # NOVO


        # --- Frame de Gerenciamento de Produtos ---
        ctk.CTkLabel(self.products_frame, text="Gerenciar Produtos", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.primary_green).grid(row=0, column=0, columnspan=3, pady=15)

        ctk.CTkLabel(self.products_frame, text="Buscar Produto (ID/Nome):").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.product_search_entry = ctk.CTkEntry(self.products_frame, width=300, corner_radius=10, placeholder_text="Buscar por ID ou Nome")
        self.product_search_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        self.product_search_entry.bind("<KeyRelease>", self.filter_products_management)

        self.search_product_management_btn = ctk.CTkButton(self.products_frame, text="Buscar", command=self.filter_products_management,
                                                            fg_color=self.primary_green, hover_color=self.secondary_green, corner_radius=10)
        self.search_product_management_btn.grid(row=1, column=2, padx=10, pady=5)

        ctk.CTkLabel(self.products_frame, text="Nome:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.product_name_entry = ctk.CTkEntry(self.products_frame, width=300, corner_radius=10, placeholder_text="Nome do produto")
        self.product_name_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(self.products_frame, text="Preço:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.product_price_entry = ctk.CTkEntry(self.products_frame, width=300, corner_radius=10, placeholder_text="Preço unitário (R$)")
        self.product_price_entry.grid(row=3, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(self.products_frame, text="Estoque:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.product_stock_entry = ctk.CTkEntry(self.products_frame, width=300, corner_radius=10, placeholder_text="Quantidade em estoque")
        self.product_stock_entry.grid(row=4, column=1, sticky="ew", padx=10, pady=5)
        
        # Novo: Campo para imagem do produto
        ctk.CTkLabel(self.products_frame, text="Imagem do Produto:").grid(row=2, column=2, sticky="nw", padx=10, pady=5)
        self.product_image_label = ctk.CTkLabel(self.products_frame, text="Nenhuma imagem", width=120, height=120, 
                                                fg_color=("gray80", "gray25"), corner_radius=10) # Set initial text
        self.product_image_label.grid(row=3, column=2, rowspan=2, padx=10, pady=5, sticky="n")
        
        self.select_image_btn = ctk.CTkButton(self.products_frame, text="Selecionar Imagem", command=self.select_product_image,
                                             fg_color="#2196F3", hover_color="#1976D2", corner_radius=10,
                                             font=ctk.CTkFont(size=12))
        self.select_image_btn.grid(row=5, column=2, padx=10, pady=5, sticky="n")


        self.add_product_btn = ctk.CTkButton(self.products_frame, text="Adicionar/Atualizar Produto", command=self.add_or_update_product,
                                            fg_color=self.primary_green, hover_color=self.secondary_green, corner_radius=10,
                                            font=ctk.CTkFont(size=14, weight="bold"))
        self.add_product_btn.grid(row=5, column=0, columnspan=2, pady=15) # Ajustei a linha para acomodar a imagem

        self.delete_product_btn = ctk.CTkButton(self.products_frame, text="Excluir Produto Selecionado", command=self.delete_product,
                                                fg_color="#F44336", hover_color="#D32F2F", corner_radius=10,
                                                font=ctk.CTkFont(size=14, weight="bold"))
        self.delete_product_btn.grid(row=6, column=0, columnspan=2, padx=10, pady=15) # Ajustei a linha

        self.low_stock_alert_label = ctk.CTkLabel(self.products_frame, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color="#FF4500")
        self.low_stock_alert_label.grid(row=7, column=0, columnspan=2, sticky="w", padx=10, pady=5) # Ajustei a linha

        self.show_low_stock_btn = ctk.CTkButton(self.products_frame, text="Ver Estoque Baixo", command=self.filter_low_stock_products,
                                                fg_color="#FF4500", hover_color="#CD3700", corner_radius=10)
        self.show_low_stock_btn.grid(row=7, column=2, padx=10, pady=5) # Ajustei a linha

        product_style = ttk.Style()
        product_style.theme_use("clam")
        product_style.configure("Treeview.Heading", font=("Roboto", 11, "bold"), 
                                background=self.primary_green,
                                foreground=self.text_color_light, borderwidth=1, 
                                bordercolor=self.primary_green)
        product_style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        self.product_tree = ttk.Treeview(self.products_frame, columns=("ID", "Nome", "Preço", "Estoque"), show="headings", style="Treeview")
        self.product_tree.heading("ID", text="ID")
        self.product_tree.heading("Nome", text="Nome")
        self.product_tree.heading("Preço", text="Preço")
        self.product_tree.heading("Estoque", text="Estoque")
        self.product_tree.column("ID", width=50, anchor="center")
        self.product_tree.column("Nome", width=250)
        self.product_tree.column("Preço", width=100, anchor="e")
        self.product_tree.column("Estoque", width=100, anchor="e")
        self.product_tree.grid(row=9, column=0, columnspan=3, sticky="nsew", padx=10, pady=10)
        self.product_tree.bind("<<TreeviewSelect>>", self.on_product_select_for_management)


        # --- Frame de Vendas ---
        self.sales_product_list_frame = ctk.CTkFrame(self.sales_frame, fg_color="transparent")
        self.sales_product_list_frame.grid(row=0, column=0, rowspan=10, sticky="nsew", padx=5, pady=5)
        self.sales_product_list_frame.grid_columnconfigure(0, weight=1)
        self.sales_product_list_frame.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self.sales_product_list_frame, text="Produtos Disponíveis", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.primary_green).grid(row=0, column=0, pady=(15, 10))

        self.sales_product_search_entry_list = ctk.CTkEntry(self.sales_product_list_frame, placeholder_text="Buscar produto por nome ou ID (Enter para adicionar)", corner_radius=10)
        self.sales_product_search_entry_list.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        # Modificado para lidar com Enter (barcode) e KeyRelease (filtragem)
        self.sales_product_search_entry_list.bind("<Return>", self.handle_sales_product_search_entry)
        self.sales_product_search_entry_list.bind("<KeyRelease>", self.handle_sales_product_search_entry)

        self.product_selection_tree = ttk.Treeview(self.sales_product_list_frame, columns=("ID", "Nome", "Preço", "Estoque"), show="headings", style="Treeview")
        self.product_selection_tree.heading("ID", text="ID")
        self.product_selection_tree.heading("Nome", text="Nome")
        self.product_selection_tree.heading("Preço", text="Preço")
        self.product_selection_tree.heading("Estoque", text="Estoque")
        self.product_selection_tree.column("ID", width=40, anchor="center")
        self.product_selection_tree.column("Nome", width=150)
        self.product_selection_tree.column("Preço", width=70, anchor="e")
        self.product_selection_tree.column("Estoque", width=60, anchor="e")
        self.product_selection_tree.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.product_selection_tree.bind("<<TreeviewSelect>>", self.on_product_select_for_sale)

        ctk.CTkLabel(self.sales_product_list_frame, text="Produto Selecionado:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.selected_product_display = ctk.CTkLabel(self.sales_product_list_frame, text="", font=ctk.CTkFont(weight="bold"), text_color=self.primary_green)
        self.selected_product_display.grid(row=4, column=0, sticky="w", padx=10, pady=5)

        ctk.CTkLabel(self.sales_product_list_frame, text="Quantidade:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.sales_quantity_entry = ctk.CTkEntry(self.sales_product_list_frame, width=100, corner_radius=10, placeholder_text="Qtde")
        self.sales_quantity_entry.grid(row=6, column=0, sticky="w", padx=10, pady=5)

        self.add_to_cart_btn = ctk.CTkButton(self.sales_product_list_frame, text="Adicionar ao Carrinho", command=self.add_product_to_cart,
                                            fg_color=self.primary_green, hover_color=self.secondary_green, corner_radius=10,
                                            font=ctk.CTkFont(size=14, weight="bold"))
        self.add_to_cart_btn.grid(row=7, column=0, pady=10)


        self.sales_cart_details_frame = ctk.CTkFrame(self.sales_frame, fg_color="transparent")
        self.sales_cart_details_frame.grid(row=0, column=1, rowspan=10, sticky="nsew", padx=5, pady=5)
        self.sales_cart_details_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.sales_cart_details_frame, text="Carrinho de Compras", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.primary_green).grid(row=0, column=0, pady=(15, 10))
        
        self.cart_tree = ttk.Treeview(self.sales_cart_details_frame, columns=("ID", "Nome", "Preço Unit.", "Qtde", "Subtotal"), show="headings", style="Treeview")
        self.cart_tree.heading("ID", text="ID")
        self.cart_tree.heading("Nome", text="Nome")
        self.cart_tree.heading("Preço Unit.", text="Preço Unit.")
        self.cart_tree.heading("Qtde", text="Qtde")
        self.cart_tree.heading("Subtotal", text="Subtotal")
        self.cart_tree.column("ID", width=50, anchor="center")
        self.cart_tree.column("Nome", width=150)
        self.cart_tree.column("Preço Unit.", width=70, anchor="e")
        self.cart_tree.column("Qtde", width=60, anchor="e")
        self.cart_tree.column("Subtotal", width=90, anchor="e")
        self.cart_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.cart_tree.bind("<<TreeviewSelect>>", self.on_cart_item_select)

        self.cart_actions_frame = ctk.CTkFrame(self.sales_cart_details_frame, fg_color="transparent")
        self.cart_actions_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        self.cart_actions_frame.grid_columnconfigure(0, weight=1)
        self.cart_actions_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.cart_actions_frame, text="Qtde no Carrinho:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.cart_quantity_entry = ctk.CTkEntry(self.cart_actions_frame, width=80, corner_radius=10, placeholder_text="Nova Qtde")
        self.cart_quantity_entry.grid(row=0, column=1, sticky="w", padx=5, pady=2)

        self.update_cart_quantity_btn = ctk.CTkButton(self.cart_actions_frame, text="Atualizar Qtde", command=self.update_cart_item_quantity,
                                                    fg_color=self.primary_green, hover_color=self.secondary_green, corner_radius=10)
        self.update_cart_quantity_btn.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        self.remove_from_cart_btn = ctk.CTkButton(self.cart_actions_frame, text="Remover Item", command=self.remove_item_from_cart,
                                                    fg_color="#F44336", hover_color="#D32F2F", corner_radius=10)
        self.remove_from_cart_btn.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(self.sales_cart_details_frame, text="Desconto:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.discount_entry = ctk.CTkEntry(self.sales_cart_details_frame, width=100, corner_radius=10, placeholder_text="Valor")
        self.discount_entry.grid(row=3, column=0, sticky="e", padx=(10, 120), pady=5)

        self.discount_type_combobox = ctk.CTkComboBox(self.sales_cart_details_frame, values=["Porcentagem", "Valor Fixo"],
                                                      state="readonly", width=120, corner_radius=10)
        self.discount_type_combobox.set("Porcentagem")
        self.discount_type_combobox.grid(row=3, column=0, sticky="e", padx=10, pady=5)

        self.apply_discount_btn = ctk.CTkButton(self.sales_cart_details_frame, text="Aplicar Desconto", command=self.apply_discount,
                                                fg_color=self.primary_green, hover_color=self.secondary_green, corner_radius=10)
        self.apply_discount_btn.grid(row=4, column=0, pady=5)

        self.total_label = ctk.CTkLabel(self.sales_cart_details_frame, text="Total: R$ 0.00", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.primary_green)
        self.total_label.grid(row=5, column=0, pady=20, sticky="e", padx=10)

        # Campos para pagamento em dinheiro e troco
        self.cash_payment_frame = ctk.CTkFrame(self.sales_cart_details_frame, fg_color="transparent")
        self.cash_payment_frame.grid_columnconfigure((0,1), weight=1)

        ctk.CTkLabel(self.cash_payment_frame, text="Valor Recebido (R$):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.received_amount_entry = ctk.CTkEntry(self.cash_payment_frame, width=120, corner_radius=10, placeholder_text="0.00")
        self.received_amount_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.received_amount_entry.bind("<KeyRelease>", self.calculate_change)

        ctk.CTkLabel(self.cash_payment_frame, text="Troco (R$):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.change_label = ctk.CTkLabel(self.cash_payment_frame, text="R$ 0.00", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.primary_green)
        self.change_label.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        # NOVO: Seleção de Cliente na tela de Vendas
        ctk.CTkLabel(self.sales_cart_details_frame, text="Cliente:").grid(row=6, column=0, sticky="w", padx=10, pady=5)
        self.customer_sales_combobox = ctk.CTkComboBox(self.sales_cart_details_frame, values=["-- Selecione um Cliente (Opcional) --"],
                                                       state="readonly", width=250, corner_radius=10,
                                                       command=self.on_customer_select_in_sales)
        self.customer_sales_combobox.set("-- Selecione um Cliente (Opcional) --")
        self.customer_sales_combobox.grid(row=7, column=0, sticky="ew", padx=10, pady=5)
        
        # Mantive o entry antigo, agora para nomes avulsos sem vínculo a cadastro
        ctk.CTkLabel(self.sales_cart_details_frame, text="Nome Avulso (opcional):").grid(row=8, column=0, sticky="w", padx=10, pady=5)
        self.customer_name_entry = ctk.CTkEntry(self.sales_cart_details_frame, width=250, corner_radius=10, placeholder_text="Nome do cliente avulso")
        self.customer_name_entry.grid(row=9, column=0, sticky="ew", padx=10, pady=5)


        ctk.CTkLabel(self.sales_cart_details_frame, text="Forma de Pagamento:").grid(row=10, column=0, sticky="w", padx=10, pady=5)
        self.payment_methods = ["Dinheiro", "Cartão de Crédito", "Cartão de Débito", "Pix", "Outro"]
        self.payment_method_combobox = ctk.CTkComboBox(self.sales_cart_details_frame, values=self.payment_methods,
                                                    state="readonly", width=200, corner_radius=10,
                                                    command=self.update_payment_fields) # Adicionado command
        self.payment_method_combobox.set("Dinheiro")
        self.payment_method_combobox.grid(row=11, column=0, sticky="w", padx=10, pady=5)


        self.finalize_sale_btn = ctk.CTkButton(self.sales_cart_details_frame, text="Finalizar Venda", command=self.finalize_sale,
                                                fg_color=self.primary_green, hover_color="#3CB371", corner_radius=10,
                                                font=ctk.CTkFont(size=16, weight="bold"))
        self.finalize_sale_btn.grid(row=12, column=0, pady=15)
        
        self.cancel_sale_btn = ctk.CTkButton(self.sales_cart_details_frame, text="Cancelar Venda", command=self.cancel_sale,
                                            fg_color="#F44336", hover_color="#D32F2F", corner_radius=10,
                                            font=ctk.CTkFont(size=14))
        self.cancel_sale_btn.grid(row=13, column=0, pady=5)


        # --- Frame de Histórico de Vendas ---
        ctk.CTkLabel(self.history_frame, text="Histórico de Vendas", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.primary_green).grid(row=0, column=0, columnspan=2, pady=15)

        filter_frame = ctk.CTkFrame(self.history_frame, fg_color="transparent")
        filter_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        filter_frame.grid_columnconfigure((0,1,2,3), weight=1)

        ctk.CTkLabel(filter_frame, text="Cliente:").grid(row=0, column=0, sticky="w", padx=5)
        self.history_customer_search_entry = ctk.CTkEntry(filter_frame, placeholder_text="Nome do Cliente", corner_radius=10)
        self.history_customer_search_entry.grid(row=0, column=1, sticky="ew", padx=5)

        ctk.CTkLabel(filter_frame, text="Produto:").grid(row=0, column=2, sticky="w", padx=5)
        self.history_product_search_entry = ctk.CTkEntry(filter_frame, placeholder_text="Nome do Produto", corner_radius=10)
        self.history_product_search_entry.grid(row=0, column=3, sticky="ew", padx=5)

        ctk.CTkLabel(filter_frame, text="Período:").grid(row=1, column=0, sticky="w", padx=5, pady=(5,0))
        self.history_period_combobox = ctk.CTkComboBox(filter_frame, values=["Todos os Tempos", "Hoje", "Últimos 7 dias", "Mês Atual"],
                                                       state="readonly", width=180, corner_radius=10)
        self.history_period_combobox.set("Todos os Tempos")
        self.history_period_combobox.grid(row=1, column=1, sticky="ew", padx=5, pady=(5,0))

        self.apply_history_filters_btn = ctk.CTkButton(filter_frame, text="Aplicar Filtros", command=self.load_sales_history,
                                                       fg_color=self.primary_green, hover_color=self.secondary_green, corner_radius=10)
        self.apply_history_filters_btn.grid(row=1, column=3, pady=(5,0))


        self.history_tree = ttk.Treeview(self.history_frame, columns=("ID Venda", "Data/Hora", "Total", "Desconto", "Cliente", "Pagamento", "Recebido", "Troco"), show="headings", style="Treeview") # Adicionadas colunas
        self.history_tree.heading("ID Venda", text="ID Venda")
        self.history_tree.heading("Data/Hora", text="Data/Hora")
        self.history_tree.heading("Total", text="Total")
        self.history_tree.heading("Desconto", text="Desconto")
        self.history_tree.heading("Cliente", text="Cliente")
        self.history_tree.heading("Pagamento", text="Pagamento")
        self.history_tree.heading("Recebido", text="Recebido") # Nova coluna
        self.history_tree.heading("Troco", text="Troco")     # Nova coluna
        self.history_tree.column("ID Venda", width=80, anchor="center")
        self.history_tree.column("Data/Hora", width=150)
        self.history_tree.column("Total", width=100, anchor="e")
        self.history_tree.column("Desconto", width=80, anchor="e")
        self.history_tree.column("Cliente", width=150)
        self.history_tree.column("Pagamento", width=100)
        self.history_tree.column("Recebido", width=80, anchor="e") # Coluna de recebido
        self.history_tree.column("Troco", width=80, anchor="e")    # Coluna de troco
        self.history_tree.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)


        # --- Frame de Devoluções/Trocas ---
        ctk.CTkLabel(self.returns_frame, text="Módulo de Devoluções/Trocas", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.primary_green).grid(row=0, column=0, columnspan=2, pady=15)

        search_return_frame = ctk.CTkFrame(self.returns_frame, fg_color="transparent")
        search_return_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        search_return_frame.grid_columnconfigure((0,1), weight=1)

        ctk.CTkLabel(search_return_frame, text="Buscar Venda (ID/Cliente):").grid(row=0, column=0, sticky="w", padx=5)
        self.return_sale_search_entry = ctk.CTkEntry(search_return_frame, placeholder_text="ID da Venda ou Nome do Cliente", corner_radius=10)
        self.return_sale_search_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.return_sale_search_entry.bind("<KeyRelease>", self.load_sales_for_returns)

        ctk.CTkButton(search_return_frame, text="Buscar", command=self.load_sales_for_returns,
                      fg_color=self.primary_green, hover_color=self.secondary_green, corner_radius=10).grid(row=0, column=2, padx=5)

        self.return_sales_tree = ttk.Treeview(self.returns_frame, columns=("ID Venda", "Data/Hora", "Total", "Cliente", "Pagamento"), show="headings", style="Treeview") # Adicionei Pagamento
        self.return_sales_tree.heading("ID Venda", text="ID Venda")
        self.return_sales_tree.heading("Data/Hora", text="Data/Hora")
        self.return_sales_tree.heading("Total", text="Total")
        self.return_sales_tree.heading("Cliente", text="Cliente")
        self.return_sales_tree.heading("Pagamento", text="Pagamento") # Novo
        self.return_sales_tree.column("ID Venda", width=80, anchor="center")
        self.return_sales_tree.column("Data/Hora", width=150)
        self.return_sales_tree.column("Total", width=100, anchor="e")
        self.return_sales_tree.column("Cliente", width=150)
        self.return_sales_tree.column("Pagamento", width=100) # Novo
        self.return_sales_tree.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        self.return_sales_tree.bind("<<TreeviewSelect>>", self.on_return_sale_select)


        ctk.CTkLabel(self.returns_frame, text="Itens da Venda Selecionada:", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.primary_green).grid(row=4, column=0, columnspan=2, pady=(15, 5))
        self.return_sale_details_label = ctk.CTkLabel(self.returns_frame, text="Nenhuma venda selecionada.", wraplength=500)
        self.return_sale_details_label.grid(row=5, column=0, columnspan=2, sticky="w", padx=10, pady=5)

        self.return_items_tree = ttk.Treeview(self.returns_frame, columns=("ID Produto", "Nome", "Qtde Vendida", "Qtde Devolvida", "Qtde Disponível", "Preço Unit."), show="headings", style="Treeview") # Adicionei mais colunas
        self.return_items_tree.heading("ID Produto", text="ID Prod.")
        self.return_items_tree.heading("Nome", text="Nome")
        self.return_items_tree.heading("Qtde Vendida", text="Qtde Vend.")
        self.return_items_tree.heading("Qtde Devolvida", text="Qtde Devolv.") # Nova
        self.return_items_tree.heading("Qtde Disponível", text="Qtde Disp.") # Nova
        self.return_items_tree.heading("Preço Unit.", text="Preço Unit.")
        self.return_items_tree.column("ID Produto", width=60, anchor="center")
        self.return_items_tree.column("Nome", width=150)
        self.return_items_tree.column("Qtde Vendida", width=80, anchor="center")
        self.return_items_tree.column("Qtde Devolvida", width=80, anchor="center") # Nova
        self.return_items_tree.column("Qtde Disponível", width=80, anchor="center") # Nova
        self.return_items_tree.column("Preço Unit.", width=90, anchor="e")
        self.return_items_tree.grid(row=6, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        self.return_items_tree.bind("<<TreeviewSelect>>", self.on_return_item_select)

        ctk.CTkLabel(self.returns_frame, text="Quantidade a Devolver:").grid(row=7, column=0, sticky="w", padx=10, pady=5)
        self.return_quantity_entry = ctk.CTkEntry(self.returns_frame, width=100, corner_radius=10, placeholder_text="Qtde")
        self.return_quantity_entry.grid(row=7, column=0, sticky="e", padx=(10,0), pady=5)

        ctk.CTkLabel(self.returns_frame, text="Motivo da Devolução:").grid(row=8, column=0, sticky="w", padx=10, pady=5)
        self.return_reason_entry = ctk.CTkEntry(self.returns_frame, width=250, corner_radius=10, placeholder_text="Ex: Defeito, Tamanho Errado")
        self.return_reason_entry.grid(row=8, column=1, sticky="ew", padx=10, pady=5)

        self.process_return_btn = ctk.CTkButton(self.returns_frame, text="Processar Devolução", command=self.process_return,
                                                fg_color="#F44336", hover_color="#D32F2F", corner_radius=10,
                                                font=ctk.CTkFont(size=14, weight="bold"))
        self.process_return_btn.grid(row=9, column=0, columnspan=2, pady=15)
        self.process_return_btn.configure(state="disabled")


        # --- Frame de Relatórios e Análises ---
        ctk.CTkLabel(self.reports_frame, text="Relatórios e Análises", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.primary_green).grid(row=0, column=0, columnspan=2, pady=15)

        ctk.CTkLabel(self.reports_frame, text="Filtrar por Período:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.report_period_combobox = ctk.CTkComboBox(self.reports_frame, values=["Hoje", "Últimos 7 dias", "Mês Atual", "Todos os Tempos"],
                                                      state="readonly", width=180, corner_radius=10, command=self.load_reports)
        self.report_period_combobox.set("Todos os Tempos")
        self.report_period_combobox.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        self.generate_reports_btn = ctk.CTkButton(self.reports_frame, text="Gerar Relatórios", command=self.load_reports,
                                                fg_color=self.primary_green, hover_color=self.secondary_green, corner_radius=10)
        self.generate_reports_btn.grid(row=2, column=0, columnspan=2, pady=10)

        ctk.CTkLabel(self.reports_frame, text="Resumo de Fluxo de Caixa (Vendas)", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.primary_green).grid(row=3, column=0, columnspan=2, pady=(20,10))
        self.cash_flow_total_label = ctk.CTkLabel(self.reports_frame, text="Total de Vendas no Período: R$ 0.00", font=ctk.CTkFont(size=16, weight="bold"))
        self.cash_flow_total_label.grid(row=4, column=0, columnspan=2, pady=5)
        ctk.CTkLabel(self.reports_frame, text="*Este resumo inclui apenas receitas de vendas. Despesas não são rastreadas.", font=ctk.CTkFont(size=10), text_color="gray").grid(row=4, column=0, columnspan=2, sticky="s", pady=(0, 5))


        ctk.CTkLabel(self.reports_frame, text="Vendas por Produto", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.primary_green).grid(row=5, column=0, sticky="w", padx=10, pady=(20,10))
        self.sales_by_product_tree = ttk.Treeview(self.reports_frame, columns=("Produto", "Quantidade Vendida", "Faturamento Total"), show="headings", style="Treeview")
        self.sales_by_product_tree.heading("Produto", text="Produto")
        self.sales_by_product_tree.heading("Quantidade Vendida", text="Quantidade Vendida")
        self.sales_by_product_tree.heading("Faturamento Total", text="Faturamento Total")
        self.sales_by_product_tree.column("Produto", width=200)
        self.sales_by_product_tree.column("Quantidade Vendida", width=120, anchor="e")
        self.sales_by_product_tree.column("Faturamento Total", width=120, anchor="e")
        self.sales_by_product_tree.grid(row=6, column=0, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(self.reports_frame, text="Vendas por Forma de Pagamento", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.primary_green).grid(row=5, column=1, sticky="w", padx=10, pady=(20,10))
        self.sales_by_payment_tree = ttk.Treeview(self.reports_frame, columns=("Forma de Pagamento", "Faturamento Total"), show="headings", style="Treeview")
        self.sales_by_payment_tree.heading("Forma de Pagamento", text="Forma de Pagamento")
        self.sales_by_payment_tree.heading("Faturamento Total", text="Faturamento Total")
        self.sales_by_payment_tree.column("Forma de Pagamento", width=150)
        self.sales_by_payment_tree.column("Faturamento Total", width=120, anchor="e")
        self.sales_by_payment_tree.grid(row=6, column=1, sticky="nsew", padx=10, pady=10)

        self.backup_db_btn = ctk.CTkButton(self.reports_frame, text="Fazer Backup do Banco de Dados", command=self.backup_database,
                                            fg_color="#FF9800", hover_color="#FB8C00", corner_radius=10,
                                            font=ctk.CTkFont(size=14, weight="bold"))
        self.backup_db_btn.grid(row=7, column=0, padx=10, pady=20, sticky="ew") 
        
        self.restore_db_btn = ctk.CTkButton(self.reports_frame, text="Restaurar Banco de Dados", command=self.restore_database,
                                            fg_color="#F44336", hover_color="#D32F2F", corner_radius=10,
                                            font=ctk.CTkFont(size=14, weight="bold"))
        self.restore_db_btn.grid(row=7, column=1, padx=10, pady=20, sticky="ew") 


        # --- Frame de Gerenciamento de Usuários ---
        ctk.CTkLabel(self.user_management_frame, text="Gerenciar Usuários", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.primary_green).grid(row=0, column=0, columnspan=2, pady=15)

        ctk.CTkLabel(self.user_management_frame, text="Nome de Usuário:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.user_username_entry = ctk.CTkEntry(self.user_management_frame, width=250, corner_radius=10, placeholder_text="Nome de usuário")
        self.user_username_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(self.user_management_frame, text="Senha (Nova):").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.user_password_entry = ctk.CTkEntry(self.user_management_frame, show="*", width=250, corner_radius=10)
        self.user_password_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(self.user_management_frame, text="Confirmar Senha:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.user_confirm_password_entry = ctk.CTkEntry(self.user_management_frame, show="*", width=250, corner_radius=10)
        self.user_confirm_password_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(self.user_management_frame, text="Função:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.user_role_combobox = ctk.CTkComboBox(self.user_management_frame, values=["admin", "caixa"], state="readonly", width=150, corner_radius=10)
        self.user_role_combobox.set("caixa")
        self.user_role_combobox.grid(row=4, column=1, sticky="w", padx=10, pady=5)

        self.add_user_btn = ctk.CTkButton(self.user_management_frame, text="Adicionar Novo Usuário", command=self.add_new_user,
                                            fg_color=self.primary_green, hover_color=self.secondary_green, corner_radius=10,
                                            font=ctk.CTkFont(size=14, weight="bold"))
        self.add_user_btn.grid(row=5, column=0, pady=10)

        self.update_user_btn = ctk.CTkButton(self.user_management_frame, text="Atualizar Usuário Selecionado", command=self.update_selected_user,
                                            fg_color=self.primary_green, hover_color=self.secondary_green, corner_radius=10,
                                            font=ctk.CTkFont(size=14, weight="bold"))
        self.update_user_btn.grid(row=5, column=1, pady=10)

        self.delete_user_btn = ctk.CTkButton(self.user_management_frame, text="Excluir Usuário Selecionado", command=self.delete_selected_user,
                                            fg_color="#F44336", hover_color="#D32F2F", corner_radius=10,
                                            font=ctk.CTkFont(size=14, weight="bold"))
        self.delete_user_btn.grid(row=6, column=0, pady=10)

        self.change_my_password_btn = ctk.CTkButton(self.user_management_frame, text="Alterar Minha Senha", command=self.open_change_password_window,
                                                    fg_color="#FF9800", hover_color="#FB8C00", corner_radius=10,
                                                    font=ctk.CTkFont(size=14, weight="bold"))
        self.change_my_password_btn.grid(row=6, column=1, pady=10)

        user_style = ttk.Style()
        user_style.theme_use("clam")
        user_style.configure("UserTreeview.Heading", font=("Roboto", 11, "bold"), 
                              background=self.primary_green,
                              foreground=self.text_color_light, borderwidth=1, 
                              bordercolor=self.primary_green)
        user_style.layout("UserTreeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        self.user_tree = ttk.Treeview(self.user_management_frame, columns=("ID", "Estabelecimento", "Usuário", "Função"), show="headings", style="UserTreeview")
        self.user_tree.heading("ID", text="ID")
        self.user_tree.heading("Estabelecimento", text="Estabelecimento")
        self.user_tree.heading("Usuário", text="Usuário")
        self.user_tree.heading("Função", text="Função")
        self.user_tree.column("ID", width=50, anchor="center")
        self.user_tree.column("Estabelecimento", width=200)
        self.user_tree.column("Usuário", width=150)
        self.user_tree.column("Função", width=100, anchor="center")
        self.user_tree.grid(row=7, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        self.user_tree.bind("<<TreeviewSelect>>", self.on_user_select)
        

        # --- Frame de Gerenciamento de Clientes (NOVO) ---
        ctk.CTkLabel(self.customers_frame, text="Gerenciar Clientes", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.primary_green).grid(row=0, column=0, columnspan=3, pady=15)

        ctk.CTkLabel(self.customers_frame, text="Buscar Cliente (ID/Nome/Telefone):").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.customer_search_entry = ctk.CTkEntry(self.customers_frame, width=300, corner_radius=10, placeholder_text="Buscar por ID, Nome ou Telefone")
        self.customer_search_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        self.customer_search_entry.bind("<KeyRelease>", self.filter_customers_management)

        self.search_customer_btn = ctk.CTkButton(self.customers_frame, text="Buscar", command=self.filter_customers_management,
                                                fg_color=self.primary_green, hover_color=self.secondary_green, corner_radius=10)
        self.search_customer_btn.grid(row=1, column=2, padx=10, pady=5)

        ctk.CTkLabel(self.customers_frame, text="Nome Completo:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.customer_name_entry_mgmt = ctk.CTkEntry(self.customers_frame, width=300, corner_radius=10, placeholder_text="Nome do cliente")
        self.customer_name_entry_mgmt.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(self.customers_frame, text="Telefone:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.customer_phone_entry_mgmt = ctk.CTkEntry(self.customers_frame, width=300, corner_radius=10, placeholder_text="Telefone (opcional)")
        self.customer_phone_entry_mgmt.grid(row=3, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(self.customers_frame, text="Email:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.customer_email_entry_mgmt = ctk.CTkEntry(self.customers_frame, width=300, corner_radius=10, placeholder_text="Email (opcional)")
        self.customer_email_entry_mgmt.grid(row=4, column=1, sticky="ew", padx=10, pady=5)

        self.add_customer_btn = ctk.CTkButton(self.customers_frame, text="Adicionar/Atualizar Cliente", command=self.add_or_update_customer,
                                            fg_color=self.primary_green, hover_color=self.secondary_green, corner_radius=10,
                                            font=ctk.CTkFont(size=14, weight="bold"))
        self.add_customer_btn.grid(row=5, column=0, columnspan=2, pady=15)

        self.delete_customer_btn = ctk.CTkButton(self.customers_frame, text="Excluir Cliente Selecionado", command=self.delete_customer,
                                                fg_color="#F44336", hover_color="#D32F2F", corner_radius=10,
                                                font=ctk.CTkFont(size=14, weight="bold"))
        self.delete_customer_btn.grid(row=6, column=0, columnspan=2, padx=10, pady=15)

        self.view_customer_history_btn = ctk.CTkButton(self.customers_frame, text="Ver Histórico de Compras", command=self.show_customer_purchase_history,
                                                        fg_color="#2196F3", hover_color="#1976D2", corner_radius=10,
                                                        font=ctk.CTkFont(size=14, weight="bold"))
        self.view_customer_history_btn.grid(row=5, column=2, padx=10, pady=15)

        customer_style = ttk.Style()
        customer_style.theme_use("clam")
        customer_style.configure("CustomerTreeview.Heading", font=("Roboto", 11, "bold"), 
                                background=self.primary_green,
                                foreground=self.text_color_light, borderwidth=1, 
                                bordercolor=self.primary_green)
        customer_style.layout("CustomerTreeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        self.customer_tree = ttk.Treeview(self.customers_frame, columns=("ID", "Nome", "Telefone", "Email"), show="headings", style="CustomerTreeview")
        self.customer_tree.heading("ID", text="ID")
        self.customer_tree.heading("Nome", text="Nome")
        self.customer_tree.heading("Telefone", text="Telefone")
        self.customer_tree.heading("Email", text="Email")
        self.customer_tree.column("ID", width=50, anchor="center")
        self.customer_tree.column("Nome", width=200)
        self.customer_tree.column("Telefone", width=150)
        self.customer_tree.column("Email", width=200)
        self.customer_tree.grid(row=7, column=0, columnspan=3, sticky="nsew", padx=10, pady=10)
        self.customer_tree.bind("<<TreeviewSelect>>", self.on_customer_select)


        # Initial loading functions
        self.load_products_to_treeview()
        self.check_low_stock_status()
        self.update_treeview_styles() 
        self.update_payment_fields() # Garante que os campos de pagamento em dinheiro estejam corretos ao iniciar
        self.update_customer_dropdown_in_sales() # Popula o combobox de clientes na tela de vendas

    def change_theme(self):
        """
        Alterna entre o tema claro e escuro do aplicativo.
        """
        if self.theme_switch_var.get() == "dark":
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")
        
        # Update the treeview styles and then the product image label background
        self.update_treeview_styles()
        
        current_appearance_mode = ctk.get_appearance_mode()
        # Determine the index based on the current mode string
        appearance_mode_index = 0 if current_appearance_mode == "Light" else 1 
        
        # Update the background color of the product image label manually
        # This uses the theme manager to get the correct background color for CTkFrame.
        text_bg_color = ctk.ThemeManager.theme["CTkFrame"]["fg_color"][appearance_mode_index]
        self.product_image_label.configure(fg_color=text_bg_color)


    def update_treeview_styles(self):
        """
        Atualiza as cores dos Treeviews após uma mudança de tema.
        """
        current_appearance_mode = ctk.get_appearance_mode()
        appearance_mode_index = 0 if current_appearance_mode == "Light" else 1 # 0 for Light, 1 for Dark

        current_fg_color = ctk.ThemeManager.theme["CTkFrame"]["fg_color"][appearance_mode_index]
        current_text_color = ctk.ThemeManager.theme["CTkLabel"]["text_color"][appearance_mode_index]
        current_border_color = ctk.ThemeManager.theme["CTkFrame"]["border_color"][appearance_mode_index]

        style = ttk.Style()
        style.configure("Treeview", background=current_fg_color, 
                        foreground=current_text_color,
                        fieldbackground=current_fg_color, 
                        borderwidth=1, bordercolor=current_border_color)
        style.map("Treeview", 
                  background=[('selected', self.secondary_green)],
                  foreground=[('selected', "white")])

        style.configure("UserTreeview", background=current_fg_color, 
                        foreground=current_text_color,
                        fieldbackground=current_fg_color, 
                        borderwidth=1, bordercolor=current_border_color)
        style.map("UserTreeview", 
                  background=[('selected', self.secondary_green)],
                  foreground=[('selected', "white")])
        
        # NOVO: Estilo para Treeview de Clientes
        style.configure("CustomerTreeview", background=current_fg_color, 
                        foreground=current_text_color,
                        fieldbackground=current_fg_color, 
                        borderwidth=1, bordercolor=current_border_color)
        style.map("CustomerTreeview", 
                  background=[('selected', self.secondary_green)],
                  foreground=[('selected', "white")])
        

    def _apply_role_permissions(self):
        """
        Aplica as permissões baseadas na função do usuário logado.
        """
        is_admin = (self.user_role == 'admin')

        # Gestão de Produtos
        self.product_name_entry.configure(state="normal" if is_admin else "disabled")
        self.product_price_entry.configure(state="normal" if is_admin else "disabled")
        self.product_stock_entry.configure(state="normal" if is_admin else "disabled")
        self.add_product_btn.configure(state="normal" if is_admin else "disabled")
        self.delete_product_btn.configure(state="normal" if is_admin else "disabled")
        self.show_low_stock_btn.configure(state="normal" if is_admin else "disabled")
        self.select_image_btn.configure(state="normal" if is_admin else "disabled")

        # Devoluções/Trocas e Relatórios - desabilita botões da sidebar para não-admins
        self.returns_btn.configure(state="normal" if is_admin else "disabled")
        self.reports_btn.configure(state="normal" if is_admin else "disabled")
        self.user_management_btn.configure(state="normal" if is_admin else "disabled")
        self.customer_management_btn.configure(state="normal" if is_admin else "disabled") # NOVO

        # Gerenciamento de usuários
        self.backup_db_btn.configure(state="normal" if is_admin else "disabled")
        self.restore_db_btn.configure(state="normal" if is_admin else "disabled")

        # Gerenciamento de Clientes (NOVO)
        self.customer_name_entry_mgmt.configure(state="normal" if is_admin else "disabled")
        self.customer_phone_entry_mgmt.configure(state="normal" if is_admin else "disabled")
        self.customer_email_entry_mgmt.configure(state="normal" if is_admin else "disabled")
        self.add_customer_btn.configure(state="normal" if is_admin else "disabled")
        self.delete_customer_btn.configure(state="normal" if is_admin else "disabled")
        self.view_customer_history_btn.configure(state="normal" if is_admin else "disabled")


    def show_frame(self, frame_name):
        """
        Esconde todos os frames de conteúdo e exibe apenas o frame selecionado.
        """
        self.products_frame.grid_remove()
        self.sales_frame.grid_remove()
        self.history_frame.grid_remove()
        self.returns_frame.grid_remove()
        self.reports_frame.grid_remove()
        self.user_management_frame.grid_remove() 
        self.customers_frame.grid_remove() # NOVO

        if frame_name == "products":
            self.products_frame.grid()
            self.load_products_to_treeview()
            self.product_name_entry.delete(0, ctk.END)
            self.product_price_entry.delete(0, ctk.END)
            self.product_stock_entry.delete(0, ctk.END)
            self.editing_product_id = None
            self.product_search_entry.delete(0, ctk.END)
            self.check_low_stock_status()
            self.display_product_image_on_load(None) # Clear image display
        elif frame_name == "sales":
            self.sales_frame.grid()
            self.load_products_for_sale()
            self.update_cart_display()
            self.selected_product_for_sale = None 
            self.selected_product_display.configure(text="")
            self.sales_quantity_entry.delete(0, ctk.END)
            self.sales_quantity_entry.insert(0, "1") # Preenche com 1 para agilizar o barcode
            self.customer_sales_combobox.set("-- Selecione um Cliente (Opcional) --") # NOVO
            self.customer_name_entry.delete(0, ctk.END) # Este é o nome avulso agora
            self.payment_method_combobox.set("Dinheiro")
            self.sales_product_search_entry_list.delete(0, ctk.END)
            self.cart_quantity_entry.delete(0, ctk.END)
            self.selected_cart_item_id = None
            self.discount_entry.delete(0, ctk.END)
            self.discount_type_combobox.set("Porcentagem")
            self.current_discount_value = 0.0
            self.current_discount_type = "Porcentagem"
            self.received_amount_entry.delete(0, ctk.END)
            self.change_label.configure(text="R$ 0.00")
            self.update_payment_fields() # Ensure cash payment fields are visible if 'Dinheiro' is selected
            self.update_customer_dropdown_in_sales() # NOVO: Recarrega clientes
            self.selected_customer_id = None # Reseta o cliente selecionado para venda
        elif frame_name == "history":
            self.history_frame.grid()
            self.load_sales_history() # Chama sem filtros inicialmente
        elif frame_name == "returns":
            if self.user_role == 'admin':
                self.returns_frame.grid()
                self.load_sales_for_returns()
                self.return_sale_details_label.configure(text="Nenhuma venda selecionada.")
                for item in self.return_items_tree.get_children():
                    self.return_items_tree.delete(item)
                self.return_quantity_entry.delete(0, ctk.END)
                self.return_reason_entry.delete(0, ctk.END)
                self.process_return_btn.configure(state="disabled")
                self.selected_return_sale_id = None
                self.selected_return_item_id = None
            else:
                messagebox.showwarning("Acesso Negado", "Você não tem permissão para acessar o módulo de Devoluções/Trocas.")
                self.show_frame("sales")
        elif frame_name == "reports":
            if self.user_role == 'admin':
                self.reports_frame.grid()
                self.load_reports()
                self.backup_db_btn.configure(state="normal" if self.user_role == 'admin' else "disabled")
                self.restore_db_btn.configure(state="normal" if self.user_role == 'admin' else "disabled")
            else:
                messagebox.showwarning("Acesso Negado", "Você não tem permissão para visualizar relatórios.")
                self.show_frame("sales")
        elif frame_name == "user_management":
            if self.user_role == 'admin':
                self.user_management_frame.grid()
                self.load_users_to_treeview()
                self.user_username_entry.delete(0, ctk.END)
                self.user_password_entry.delete(0, ctk.END)
                self.user_confirm_password_entry.delete(0, ctk.END)
                self.user_role_combobox.set("caixa")
                self.selected_user_id = None
                self.update_user_btn.configure(state="disabled")
                self.delete_user_btn.configure(state="disabled")
            else:
                messagebox.showwarning("Acesso Negado", "Você não tem permissão para acessar o gerenciamento de usuários.")
                self.show_frame("sales")
        elif frame_name == "customers": # NOVO: exibir frame de clientes
            if self.user_role == 'admin':
                self.customers_frame.grid()
                self.load_customers_to_treeview()
                self.customer_name_entry_mgmt.delete(0, ctk.END)
                self.customer_phone_entry_mgmt.delete(0, ctk.END)
                self.customer_email_entry_mgmt.delete(0, ctk.END)
                self.selected_customer_id = None # Reseta o ID do cliente selecionado para gestão
                self.customer_search_entry.delete(0, ctk.END)
                self.view_customer_history_btn.configure(state="disabled")
            else:
                messagebox.showwarning("Acesso Negado", "Você não tem permissão para acessar o gerenciamento de clientes.")
                self.show_frame("sales")


    def select_product_image(self):
        """
        Permite ao usuário selecionar um arquivo de imagem e exibe uma prévia.
        A imagem é copiada para o diretório de imagens do produto.
        """
        file_path = filedialog.askopenfilename(
            title="Selecionar Imagem do Produto",
            filetypes=[("Arquivos de Imagem", "*.png;*.jpg;*.jpeg;*.gif"), ("Todos os arquivos", "*.*")]
        )
        if file_path:
            try:
                # Gerar um nome de arquivo único para evitar colisões
                file_extension = os.path.splitext(file_path)[1]
                new_file_name = f"product_{datetime.now().strftime('%Y%m%d%H%M%S%f')}{file_extension}"
                destination_path = os.path.join(self.product_images_dir, new_file_name)

                shutil.copyfile(file_path, destination_path)
                self.current_product_image_path = destination_path # Armazena o caminho relativo

                # Exibir prévia da imagem
                original_image = Image.open(file_path)
                resized_image = original_image.resize((120, 120), Image.Resampling.LANCZOS)
                self.product_photo_image = ImageTk.PhotoImage(resized_image)
                self.product_image_label.configure(image=self.product_photo_image, text="")
                messagebox.showinfo("Sucesso", "Imagem selecionada e copiada com sucesso!")

            except Exception as e:
                messagebox.showerror("Erro de Imagem", f"Não foi possível carregar ou copiar a imagem: {e}")
                self.current_product_image_path = None
                self.product_image_label.configure(image=None, text="Erro ao carregar imagem")
                print(f"Erro detalhado ao selecionar imagem: {e}")
        else:
            self.current_product_image_path = None
            self.product_image_label.configure(image=None, text="Nenhuma imagem selecionada")

    def display_product_image_on_load(self, image_path):
        """
        Carrega e exibe a imagem do produto no label de prévia.
        """
        if image_path and os.path.exists(image_path):
            try:
                original_image = Image.open(image_path)
                resized_image = original_image.resize((120, 120), Image.Resampling.LANCZOS)
                self.product_photo_image = ImageTk.PhotoImage(resized_image)
                self.product_image_label.configure(image=self.product_photo_image, text="")
            except Exception as e:
                self.product_image_label.configure(image=None, text="Erro ao carregar imagem")
                print(f"Erro ao exibir imagem do produto: {e}")
        else:
            self.product_image_label.configure(image=None, text="Nenhuma imagem")
        self.current_product_image_path = image_path # Mantém o caminho atual para salvar

    def add_or_update_product(self):
        """
        Adiciona um novo produto ao banco de dados ou atualiza um produto existente.
        Verifica a validade dos dados de entrada.
        """
        if self.user_role != 'admin':
            messagebox.showwarning("Permissão Negada", "Você não tem permissão para adicionar/atualizar produtos.")
            return

        name = self.product_name_entry.get().strip()
        price_str = self.product_price_entry.get().strip()
        stock_str = self.product_stock_entry.get().strip()
        image_path_to_save = self.current_product_image_path # Pega o caminho da imagem

        if not name or not price_str or not stock_str:
            messagebox.showerror("Erro", "Todos os campos devem ser preenchidos.")
            return

        try:
            price = float(price_str.replace(',', '.'))
            stock = int(stock_str)
            if price <= 0 or stock < 0:
                raise ValueError("Preço deve ser positivo e estoque não negativo.")
        except ValueError:
            messagebox.showerror("Erro", "Preço e Estoque devem ser números válidos.")
            return

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        try:
            if self.editing_product_id:
                product_id = self.editing_product_id
                cursor.execute("UPDATE products SET name=?, price=?, stock=?, image_path=? WHERE id=?", (name, price, stock, image_path_to_save, product_id))
                messagebox.showinfo("Sucesso", f"Produto '{name}' atualizado com sucesso!")
                self.editing_product_id = None
            else:
                cursor.execute("INSERT INTO products (name, price, stock, image_path) VALUES (?, ?, ?, ?)", (name, price, stock, image_path_to_save))
                messagebox.showinfo("Sucesso", f"Produto '{name}' adicionado com sucesso!")
            
            conn.commit()
            self.load_products_to_treeview()
            self.check_low_stock_status()
            # Limpa os campos de entrada e a imagem
            self.product_name_entry.delete(0, ctk.END)
            self.product_price_entry.delete(0, ctk.END)
            self.product_stock_entry.delete(0, ctk.END)
            self.product_tree.selection_remove(self.product_tree.focus())
            self.display_product_image_on_load(None) # Limpa a prévia da imagem
            self.current_product_image_path = None

        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Um produto com este nome já existe.")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}")
            print(f"Erro detalhado ao adicionar/atualizar produto: {e}")
        finally:
            conn.close()

    def delete_product(self):
        """
        Exclui o produto selecionado do banco de dados.
        """
        if self.user_role != 'admin':
            messagebox.showwarning("Permissão Negada", "Você não tem permissão para excluir produtos.")
            return

        selected_item = self.product_tree.focus()
        if not selected_item:
            messagebox.showwarning("Aviso", "Por favor, selecione um produto para excluir.")
            return
        
        product_id = self.product_tree.item(selected_item, 'values')[0]
        product_name = self.product_tree.item(selected_item, 'values')[1]
        
        # Pega o caminho da imagem para excluí-la se o produto for removido
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT image_path FROM products WHERE id=?", (product_id,))
        image_path_to_delete = cursor.fetchone()[0]
        conn.close()

        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o produto '{product_name}' (ID: {product_id})? Esta ação é irreversível."):
            conn = sqlite3.connect(self.db_name)
            cursor = conn.executescript("PRAGMA foreign_keys = ON;") # Garante que FKs estejam ativas para ON DELETE CASCADE
            try:
                cursor.execute("SELECT COUNT(*) FROM sale_items WHERE product_id=?", (product_id,))
                sales_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM returns WHERE product_id=?", (product_id,))
                returns_count = cursor.fetchone()[0]

                if sales_count > 0 or returns_count > 0:
                    messagebox.showerror("Erro", "Não é possível excluir este produto. Ele está associado a vendas ou devoluções existentes.")
                    return

                cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
                conn.commit()
                
                # Tenta excluir o arquivo de imagem associado
                if image_path_to_delete and os.path.exists(image_path_to_delete):
                    try:
                        os.remove(image_path_to_delete)
                        print(f"Imagem {image_path_to_delete} excluída.")
                    except Exception as img_e:
                        print(f"Aviso: Não foi possível excluir o arquivo de imagem {image_path_to_delete}: {img_e}")


                messagebox.showinfo("Sucesso", f"Produto '{product_name}' excluído com sucesso!")
                self.load_products_to_treeview()
                self.check_low_stock_status()
                self.product_name_entry.delete(0, ctk.END)
                self.product_price_entry.delete(0, ctk.END)
                self.product_stock_entry.delete(0, ctk.END)
                self.editing_product_id = None
                self.display_product_image_on_load(None) # Limpa a prévia da imagem
                self.current_product_image_path = None

            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao excluir o produto: {e}")
                print(f"Erro detalhado ao excluir produto: {e}")
            finally:
                conn.close()

    def on_product_select_for_management(self, event):
        """
        Popula os campos de entrada com os detalhes do produto selecionado no Treeview
        da aba de Gerenciamento de Produtos, para que possa ser editado, incluindo a imagem.
        """
        selected_item = self.product_tree.focus()
        if selected_item:
            values = self.product_tree.item(selected_item, 'values')
            self.editing_product_id = int(values[0])
            self.product_name_entry.delete(0, ctk.END)
            self.product_name_entry.insert(0, values[1])
            self.product_price_entry.delete(0, ctk.END)
            self.product_price_entry.insert(0, values[2].replace('R$ ', '').replace('.', ','))
            self.product_stock_entry.delete(0, ctk.END)
            self.product_stock_entry.insert(0, values[3])

            # Carrega o caminho da imagem e exibe
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT image_path FROM products WHERE id=?", (self.editing_product_id,))
            image_path = cursor.fetchone()[0]
            conn.close()
            self.display_product_image_on_load(image_path)

        else:
            self.editing_product_id = None
            self.product_name_entry.delete(0, ctk.END)
            self.product_price_entry.delete(0, ctk.END)
            self.product_stock_entry.delete(0, ctk.END)
            self.display_product_image_on_load(None) # Limpa a prévia da imagem
            self.current_product_image_path = None


    def filter_products_management(self, event=None):
        """
        Filtra os produtos na Treeview de gerenciamento com base no termo de busca.
        """
        search_term = self.product_search_entry.get().strip().lower()
        
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        # A query agora seleciona image_path também, mas não é exibido no Treeview diretamente
        if search_term:
            cursor.execute("SELECT id, name, price, stock, image_path FROM products WHERE LOWER(name) LIKE ? OR CAST(id AS TEXT) LIKE ? ORDER BY name",
                           (f"%{search_term}%", f"%{search_term}%"))
        else:
            cursor.execute("SELECT id, name, price, stock, image_path FROM products ORDER BY name")
        products = cursor.fetchall()
        conn.close()

        for product in products:
            # Não exibe a imagem no treeview, mas o image_path está disponível se precisar
            self.product_tree.insert("", ctk.END, values=(product[0], product[1], f"R$ {product[2]:.2f}", product[3]))
        
        self.check_low_stock_status()

    def filter_low_stock_products(self):
        """
        Filtra a lista de produtos para mostrar apenas aqueles com estoque baixo.
        """
        if self.user_role != 'admin':
            messagebox.showwarning("Permissão Negada", "Você não tem permissão para visualizar produtos com estoque baixo.")
            return

        for item in self.product_tree.get_children():
            self.product_tree.delete(item)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, stock, image_path FROM products WHERE stock <= ? ORDER BY name", (self.MINIMUM_STOCK_THRESHOLD,))
        low_stock_products = cursor.fetchall()
        conn.close()

        if not low_stock_products:
            messagebox.showinfo("Estoque Baixo", "Nenhum produto com estoque abaixo do limite definido.")
            self.load_products_to_treeview()
            return

        for product in low_stock_products:
            self.product_tree.insert("", ctk.END, values=(product[0], product[1], f"R$ {product[2]:.2f}", product[3]))
        
        self.low_stock_alert_label.configure(text=f"ATENÇÃO: {len(low_stock_products)} produto(s) com estoque baixo!", text_color="#FF4500")


    def check_low_stock_status(self):
        """
        Verifica o estoque e atualiza a label de alerta na aba de produtos.
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products WHERE stock <= ?", (self.MINIMUM_STOCK_THRESHOLD,))
        low_stock_count = cursor.fetchone()[0]
        conn.close()

        if low_stock_count > 0:
            self.low_stock_alert_label.configure(text=f"ATENÇÃO: {low_stock_count} produto(s) com estoque baixo!", text_color="#FF4500")
            self.show_low_stock_btn.configure(state="normal" if self.user_role == 'admin' else "disabled")
        else:
            self.low_stock_alert_label.configure(text="Todos os produtos com estoque OK.", text_color=self.primary_green)
            self.show_low_stock_btn.configure(state="disabled")

    def load_products_to_treeview(self):
        """
        Carrega todos os produtos do banco de dados e os exibe no Treeview de produtos na aba de Gestão.
        """
        self.filter_products_management()

    def load_products_for_sale(self):
        """
        Carrega todos os produtos do banco de dados e os exibe no Treeview de seleção de produtos na aba de Vendas.
        """
        self.filter_products_for_sale()

    def filter_products_for_sale(self, event=None):
        """
        Filtra os produtos na Treeview de vendas com base no termo de busca.
        """
        search_term = self.sales_product_search_entry_list.get().strip().lower()
        
        for item in self.product_selection_tree.get_children():
            self.product_selection_tree.delete(item)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        if search_term:
            cursor.execute("SELECT id, name, price, stock FROM products WHERE LOWER(name) LIKE ? OR CAST(id AS TEXT) LIKE ? ORDER BY name",
                           (f"%{search_term}%", f"%{search_term}%"))
        else:
            cursor.execute("SELECT id, name, price, stock FROM products ORDER BY name")
        products = cursor.fetchall()
        conn.close()

        for product in products:
            self.product_selection_tree.insert("", ctk.END, values=(product[0], product[1], f"R$ {product[2]:.2f}", product[3]))

    def handle_sales_product_search_entry(self, event=None):
        """
        Gerencia a entrada no campo de busca de vendas.
        Se Enter for pressionado e o texto for um ID numérico, tenta adicionar o produto ao carrinho.
        Caso contrário (ou KeyRelease), filtra a lista de produtos.
        """
        entry_text = self.sales_product_search_entry_list.get().strip()

        if event and event.keysym == "Return":
            try:
                product_id = int(entry_text)
                quantity = int(self.sales_quantity_entry.get().strip() or "1") # Usa 1 se o campo de quantidade estiver vazio
                self.add_product_to_cart(product_id=product_id, quantity_to_add=quantity)
                self.sales_product_search_entry_list.delete(0, ctk.END) # Limpa o campo após adicionar
                self.sales_quantity_entry.delete(0, ctk.END)
                self.sales_quantity_entry.insert(0, "1") # Reseta para 1
            except ValueError:
                messagebox.showwarning("Formato Inválido", "Por favor, insira um ID de produto numérico válido para adicionar rapidamente, ou use o botão 'Adicionar ao Carrinho'.")
            finally:
                self.filter_products_for_sale() # Sempre filtra para manter a lista atualizada
        else:
            self.filter_products_for_sale()


    def on_product_select_for_sale(self, event):
        """
        Captura o evento de seleção de um produto no Treeview da tela de vendas (lista de produtos).
        Popula o display do produto selecionado e limpa o campo de quantidade.
        """
        selected_item = self.product_selection_tree.focus()
        if selected_item:
            values = self.product_selection_tree.item(selected_item, 'values')
            product_id = int(values[0])
            product_name = values[1]
            product_price_str = values[2].replace('R$ ', '').replace(',', '.')
            product_price = float(product_price_str)
            product_stock = int(values[3])

            self.selected_product_for_sale = {
                'id': product_id,
                'name': product_name,
                'price': product_price,
                'stock': product_stock
            }
            self.selected_product_display.configure(text=f"{product_name} (Estoque: {product_stock})")
            self.sales_quantity_entry.delete(0, ctk.END)
            self.sales_quantity_entry.insert(0, "1") # Preenche com 1 para agilizar

        else:
            self.selected_product_for_sale = None
            self.selected_product_display.configure(text="")
            self.sales_quantity_entry.delete(0, ctk.END)
            self.sales_quantity_entry.insert(0, "1") # Preenche com 1 para agilizar

        self.cart_tree.selection_remove(self.cart_tree.focus())
        self.selected_cart_item_id = None
        self.cart_quantity_entry.delete(0, ctk.END)


    def on_cart_item_select(self, event):
        """
        Captura o evento de seleção de um item no Treeview do carrinho.
        Popula o campo de quantidade para edição e armazena o ID do item.
        """
        selected_item = self.cart_tree.focus()
        if selected_item:
            values = self.cart_tree.item(selected_item, 'values')
            product_id = int(values[0])
            quantity_in_cart = int(values[3])

            self.selected_cart_item_id = product_id
            self.cart_quantity_entry.delete(0, ctk.END)
            self.cart_quantity_entry.insert(0, str(quantity_in_cart))
            
            self.product_selection_tree.selection_remove(self.product_selection_tree.focus())
            self.selected_product_for_sale = None
            self.selected_product_display.configure(text="")
            self.sales_quantity_entry.delete(0, ctk.END)
            self.sales_quantity_entry.insert(0, "1") # Preenche com 1 para agilizar

        else:
            self.selected_cart_item_id = None
            self.cart_quantity_entry.delete(0, ctk.END)

    def update_cart_item_quantity(self):
        """
        Atualiza a quantidade de um item selecionado no carrinho.
        """
        if self.selected_cart_item_id is None:
            messagebox.showwarning("Aviso", "Por favor, selecione um item no carrinho para atualizar a quantidade.")
            return

        try:
            new_quantity = int(self.cart_quantity_entry.get().strip())
            if new_quantity <= 0:
                messagebox.showerror("Erro", "A quantidade deve ser um número positivo.")
                return
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira uma quantidade válida para o carrinho.")
            return

        product_id = self.selected_cart_item_id
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT stock, name FROM products WHERE id=?", (product_id,))
        product_info = cursor.fetchone()
        conn.close()

        if not product_info:
            messagebox.showerror("Erro", "Produto não encontrado no estoque.")
            return

        available_stock = product_info[0]
        product_name = product_info[1]

        current_quantity_in_cart = self.current_cart[product_id]['quantity']
        effective_stock = available_stock + current_quantity_in_cart

        if new_quantity > effective_stock:
            messagebox.showwarning("Estoque Insuficiente", f"Não há estoque suficiente para a nova quantidade de '{product_name}' ({new_quantity}). Estoque disponível: {available_stock}. Você já tem {current_quantity_in_cart} no carrinho.") 
            return

        self.current_cart[product_id]['quantity'] = new_quantity
        self.update_cart_display()
        messagebox.showinfo("Sucesso", f"Quantidade de '{product_name}' atualizada para {new_quantity} no carrinho.")
        self.cart_quantity_entry.delete(0, ctk.END)
        self.cart_tree.selection_remove(self.cart_tree.focus())
        self.selected_cart_item_id = None
        self.calculate_change() # Recalcula o troco se o carrinho mudar

    def remove_item_from_cart(self): # Adicionada esta função que estava faltando
        """
        Remove um item selecionado do carrinho de compras.
        """
        if self.selected_cart_item_id is None:
            messagebox.showwarning("Aviso", "Por favor, selecione um item no carrinho para remover.")
            return

        product_id = self.selected_cart_item_id
        product_name = self.current_cart[product_id]['name']

        if messagebox.askyesno("Remover Item", f"Tem certeza que deseja remover '{product_name}' do carrinho?"):
            del self.current_cart[product_id]
            self.update_cart_display()
            messagebox.showinfo("Sucesso", f"'{product_name}' removido do carrinho.")
            self.cart_quantity_entry.delete(0, ctk.END)
            self.cart_tree.selection_remove(self.cart_tree.focus())
            self.selected_cart_item_id = None
            self.calculate_change() # Recalcula o troco se o carrinho mudar


    def add_product_to_cart(self, product_id=None, quantity_to_add=None):
        """
        Adiciona o produto ao carrinho de compras, seja por seleção na Treeview
        ou por ID direto (como de um leitor de código de barras).
        Verifica a quantidade disponível em estoque.
        """
        if product_id is None: # Chamada do botão "Adicionar ao Carrinho"
            if not hasattr(self, 'selected_product_for_sale') or not self.selected_product_for_sale:
                messagebox.showerror("Erro", "Nenhum produto selecionado para adicionar ao carrinho. Por favor, selecione um produto na lista.")
                return
            product_id = self.selected_product_for_sale['id']
            try:
                quantity_to_add = int(self.sales_quantity_entry.get().strip())
                if quantity_to_add <= 0:
                    raise ValueError("Quantidade deve ser um número positivo.")
            except ValueError:
                messagebox.showerror("Erro", "Por favor, insira uma quantidade válida.")
                return
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT name, price, stock FROM products WHERE id=?", (product_id,))
        product_info = cursor.fetchone()
        conn.close()

        if not product_info:
            messagebox.showerror("Erro", f"Produto com ID {product_id} não encontrado.")
            return

        product_name, product_price, available_stock = product_info

        if product_id in self.current_cart:
            current_cart_quantity = self.current_cart[product_id]['quantity']
            if (current_cart_quantity + quantity_to_add) > available_stock:
                messagebox.showwarning("Estoque Insuficiente", f"Não há estoque suficiente para adicionar mais {quantity_to_add} unidades de '{product_name}'. Disponível em estoque: {available_stock}. Já no carrinho: {current_cart_quantity}")
                return
            self.current_cart[product_id]['quantity'] += quantity_to_add
        else:
            if quantity_to_add > available_stock:
                messagebox.showwarning("Estoque Insuficiente", f"Não há estoque suficiente para adicionar {quantity_to_add} unidades de '{product_name}'. Disponível: {available_stock}")
                return
            self.current_cart[product_id] = {
                'name': product_name,
                'price': product_price,
                'quantity': quantity_to_add
            }
        
        self.update_cart_display()
        self.sales_quantity_entry.delete(0, ctk.END) 
        self.sales_quantity_entry.insert(0, "1") # Reseta para 1 após adicionar

        # Feedback visual de sucesso (botão pisca)
        self.flash_button(self.add_to_cart_btn, self.primary_green, "#32CD32", self.secondary_green, "#3CB371")

        self.selected_product_for_sale = None
        self.selected_product_display.configure(text="")
        self.product_selection_tree.selection_remove(self.product_selection_tree.focus())
        self.load_products_for_sale()
        self.calculate_change() # Recalcula o troco se o carrinho mudar

    def flash_button(self, button_widget, original_fg, flash_fg, original_hover, flash_hover, duration_ms=200):
        """
        Faz um botão piscar momentaneamente para indicar uma ação bem-sucedida.
        """
        button_widget.configure(fg_color=flash_fg, hover_color=flash_hover)
        self.master.after(duration_ms, lambda: button_widget.configure(fg_color=original_fg, hover_color=original_hover))


    def apply_discount(self):
        """
        Aplica o desconto inserido no total da venda.
        """
        discount_str = self.discount_entry.get().strip()
        discount_type = self.discount_type_combobox.get()

        if not discount_str:
            self.current_discount_value = 0.0
            self.current_discount_type = "Nenhum"
            self.update_cart_display()
            self.calculate_change() # Recalcula o troco
            messagebox.showinfo("Desconto Removido", "Desconto removido do total da venda.")
            return

        try:
            discount_val = float(discount_str.replace(',', '.'))
            if discount_val < 0:
                raise ValueError("O valor do desconto não pode ser negativo.")
        except ValueError:
            messagebox.showerror("Erro de Desconto", "Por favor, insira um valor de desconto numérico válido.")
            return

        if discount_type == "Porcentagem" and discount_val > 100:
            messagebox.showwarning("Aviso", "Desconto em porcentagem não pode ser maior que 100%. Será aplicado 100% no máximo.")
            discount_val = 100.0
        
        self.current_discount_value = discount_val
        self.current_discount_type = discount_type
        self.update_cart_display()
        self.calculate_change() # Recalcula o troco
        messagebox.showinfo("Desconto Aplicado", f"Desconto de {discount_str} {discount_type} aplicado ao total.")

    def calculate_change(self, event=None):
        """
        Calcula e exibe o troco, se a forma de pagamento for "Dinheiro".
        """
        if self.payment_method_combobox.get() == "Dinheiro":
            try:
                total_str = self.total_label.cget("text").replace("Total: R$ ", "").replace(",", ".")
                total = float(total_str)
            except ValueError:
                total = 0.0

            try:
                received_amount = float(self.received_amount_entry.get().replace(',', '.'))
            except ValueError:
                received_amount = 0.0
            
            change = received_amount - total
            if change < 0:
                self.change_label.configure(text="R$ 0.00", text_color="#F44336") # Vermelho para troco insuficiente
            else:
                self.change_label.configure(text=f"R$ {change:.2f}", text_color=self.primary_green)
        else:
            self.received_amount_entry.delete(0, ctk.END)
            self.change_label.configure(text="R$ 0.00")


    def update_payment_fields(self, choice=None):
        """
        Mostra ou esconde os campos de valor recebido e troco com base na forma de pagamento selecionada.
        """
        if self.payment_method_combobox.get() == "Dinheiro":
            # Reposicionar cash_payment_frame
            self.cash_payment_frame.grid(row=5, column=0, sticky="ew", padx=10, pady=5)
            self.sales_cart_details_frame.grid_rowconfigure(5, weight=0) # Total label is row 5, not a problem
            self.sales_cart_details_frame.grid_rowconfigure(6, weight=0) # Now cash_payment_frame is row 6
            self.sales_cart_details_frame.grid_rowconfigure(7, weight=0) # Customer combobox
            self.sales_cart_details_frame.grid_rowconfigure(8, weight=0) # customer name label
            self.sales_cart_details_frame.grid_rowconfigure(9, weight=0) # customer name entry
            self.sales_cart_details_frame.grid_rowconfigure(10, weight=0) # payment method label
            self.sales_cart_details_frame.grid_rowconfigure(11, weight=0) # payment method combobox
            self.sales_cart_details_frame.grid_rowconfigure(12, weight=1) # Finalize button

            self.received_amount_entry.configure(state="normal")
            self.received_amount_entry.bind("<KeyRelease>", self.calculate_change)
            self.calculate_change() # Calcula troco ao mudar para dinheiro
        else:
            self.cash_payment_frame.grid_remove()
            self.received_amount_entry.configure(state="disabled")
            self.received_amount_entry.unbind("<KeyRelease>")
            self.received_amount_entry.delete(0, ctk.END)
            self.change_label.configure(text="R$ 0.00")
            # Reset row weights to ensure layout adjusts
            self.sales_cart_details_frame.grid_rowconfigure(5, weight=0) # Total label
            self.sales_cart_details_frame.grid_rowconfigure(6, weight=0) # Customer combobox label
            self.sales_cart_details_frame.grid_rowconfigure(7, weight=0) # Customer combobox
            self.sales_cart_details_frame.grid_rowconfigure(8, weight=0) # Customer name label
            self.sales_cart_details_frame.grid_rowconfigure(9, weight=0) # Customer name entry
            self.sales_cart_details_frame.grid_rowconfigure(10, weight=0) # Payment method label
            self.sales_cart_details_frame.grid_rowconfigure(11, weight=0) # Payment method combobox
            self.sales_cart_details_frame.grid_rowconfigure(12, weight=1) # Finalize button

    def update_cart_display(self):
        """
        Atualiza a exibição do Treeview do carrinho de compras e o total da venda, aplicando o desconto.
        """
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)

        subtotal_before_discount = 0.0
        for product_id, item_data in self.current_cart.items():
            subtotal = item_data['quantity'] * item_data['price']
            subtotal_before_discount += subtotal
            self.cart_tree.insert("", ctk.END, values=(
                product_id,
                item_data['name'],
                f"R$ {item_data['price']:.2f}",
                item_data['quantity'],
                f"R$ {subtotal:.2f}"
            ))
        
        final_total = subtotal_before_discount
        if self.current_discount_type == "Porcentagem":
            final_total = subtotal_before_discount * (1 - (self.current_discount_value / 100))
        elif self.current_discount_type == "Valor Fixo":
            final_total = subtotal_before_discount - self.current_discount_value
            if final_total < 0:
                final_total = 0.0

        self.total_label.configure(text=f"Total: R$ {final_total:.2f}")
        self.calculate_change() # Recalcula o troco com o novo total

    def on_customer_select_in_sales(self, choice):
        """
        Lida com a seleção de um cliente no combobox da tela de vendas.
        Atualiza self.selected_customer_id e preenche customer_name_entry_temp.
        """
        if choice == "-- Selecione um Cliente (Opcional) --":
            self.selected_customer_id = None
            self.customer_name_entry.delete(0, ctk.END) # Limpa o nome avulso se um cliente foi desselecionado
        else:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            # Precisamos encontrar o ID do cliente baseado no nome (e assumindo unicidade, ou ajustando se houver homônimos)
            cursor.execute("SELECT id FROM customers WHERE name=?", (choice,))
            result = cursor.fetchone()
            conn.close()
            if result:
                self.selected_customer_id = result[0]
                self.customer_name_entry.delete(0, ctk.END) # Limpa o nome avulso se um cliente selecionado
                self.customer_name_entry.insert(0, choice) # Preenche com o nome do cliente selecionado (apenas para exibição)
            else:
                self.selected_customer_id = None
                self.customer_name_entry.delete(0, ctk.END)
                messagebox.showerror("Erro", "Cliente selecionado não encontrado. Por favor, recarregue a lista de clientes.")
        
    def update_customer_dropdown_in_sales(self):
        """
        Popula o combobox de seleção de clientes na tela de vendas.
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM customers ORDER BY name")
        customer_names = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Adiciona a opção padrão no início
        dropdown_values = ["-- Selecione um Cliente (Opcional) --"] + customer_names
        self.customer_sales_combobox.configure(values=dropdown_values)
        self.customer_sales_combobox.set("-- Selecione um Cliente (Opcional) --") # Reseta a seleção

    def finalize_sale(self):
        """
        Finaliza a venda atual, registrando-a no banco de dados
        e atualizando o estoque dos produtos.
        """
        if not self.current_cart:
            messagebox.showwarning("Venda Vazia", "O carrinho está vazio. Adicione produtos para finalizar a venda.")
            return

        customer_name_manual = self.customer_name_entry.get().strip() # Nome digitado avulso
        payment_method = self.payment_method_combobox.get()
        final_total = float(self.total_label.cget("text").replace("Total: R$ ", "").replace(",", "."))
        
        received_amount = 0.0
        change_amount = 0.0

        if payment_method == "Dinheiro":
            try:
                received_amount = float(self.received_amount_entry.get().replace(',', '.'))
                if received_amount < final_total:
                    messagebox.showerror("Erro de Pagamento", "O valor recebido é menor que o total da venda.")
                    return
                change_amount = received_amount - final_total
            except ValueError:
                messagebox.showerror("Erro de Pagamento", "Por favor, insira um valor numérico válido para 'Valor Recebido'.")
                return

        # Determinar o nome do cliente a ser salvo
        customer_name_to_save = customer_name_manual
        customer_id_to_save = self.selected_customer_id # Já vem do combobox se selecionado

        if not messagebox.askyesno("Confirmar Finalização de Venda", 
                                    f"Deseja realmente finalizar esta venda no valor total de R$ {final_total:.2f}?\n"
                                    f"Cliente: {customer_name_to_save if customer_name_to_save else 'Não informado'}\n"
                                    f"Pagamento: {payment_method}" + 
                                    (f"\nRecebido: R$ {received_amount:.2f}\nTroco: R$ {change_amount:.2f}" if payment_method == "Dinheiro" else "")
                                    ):
            return

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            for product_id, item_data in self.current_cart.items():
                cursor.execute("SELECT stock FROM products WHERE id=?", (product_id,))
                result = cursor.fetchone()
                if not result:
                    raise Exception(f"Produto com ID {product_id} não encontrado no estoque.")
                
                current_stock = result[0]
                if item_data['quantity'] > current_stock:
                    messagebox.showerror("Erro de Estoque", f"Estoque insuficiente para '{item_data['name']}'. Disponível: {current_stock}")
                    conn.rollback()
                    return

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Atualiza a inserção na tabela 'sales' com as novas colunas
            cursor.execute("INSERT INTO sales (timestamp, total, customer_id, customer_name, payment_method, discount_value, discount_type, received_amount, change_amount) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (timestamp, final_total, customer_id_to_save, customer_name_to_save, payment_method, self.current_discount_value, self.current_discount_type, received_amount, change_amount))
            sale_id = cursor.lastrowid

            for product_id, item_data in self.current_cart.items():
                cursor.execute(
                    "INSERT INTO sale_items (sale_id, product_id, product_name, quantity, price) VALUES (?, ?, ?, ?, ?)",
                    (sale_id, product_id, item_data['name'], item_data['quantity'], item_data['price'])
                )
                cursor.execute("UPDATE products SET stock = stock - ? WHERE id=?", (item_data['quantity'], product_id))
            
            conn.commit()
            
            cart_items_for_receipt = list(self.current_cart.values())

            # Passa as novas informações para o recibo
            self.display_receipt(sale_id, timestamp, final_total, customer_name_to_save, payment_method, self.current_discount_value, self.current_discount_type, received_amount, change_amount, cart_items_for_receipt)

            messagebox.showinfo("Venda Finalizada", f"Venda {sale_id} finalizada com sucesso!")
            
            # Reseta a interface de vendas
            self.current_cart = {}
            self.update_cart_display()
            self.load_products_to_treeview()
            self.load_products_for_sale()
            self.load_sales_history()
            self.customer_sales_combobox.set("-- Selecione um Cliente (Opcional) --") # NOVO
            self.customer_name_entry.delete(0, ctk.END)
            self.selected_customer_id = None # Reseta o ID do cliente selecionado
            self.payment_method_combobox.set("Dinheiro")
            self.discount_entry.delete(0, ctk.END)
            self.discount_type_combobox.set("Porcentagem")
            self.current_discount_value = 0.0
            self.current_discount_type = "Porcentagem"
            self.received_amount_entry.delete(0, ctk.END) # Limpa valor recebido
            self.change_label.configure(text="R$ 0.00") # Limpa troco
            self.check_low_stock_status()
            self.update_payment_fields() # Garante que campos de pagamento estejam corretos após finalizar a venda
            self.update_customer_dropdown_in_sales() # NOVO: Recarrega clientes

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Erro na Venda", f"Ocorreu um erro ao finalizar a venda: {e}")
            print(f"Erro detalhado ao finalizar venda: {e}")
        finally:
            conn.close()

    def display_receipt(self, sale_id, timestamp, total, customer_name, payment_method, discount_value, discount_type, received_amount, change_amount, cart_items):
        """
        Exibe um recibo visual em uma nova janela.
        Adiciona botão para gerar PDF.
        """
        receipt_window = ctk.CTkToplevel(self.master)
        receipt_window.title(f"Recibo da Venda {sale_id}")
        receipt_window.geometry("400x550") 
        receipt_window.transient(self.master) 
        receipt_window.grab_set() 

        self.master.update_idletasks() 
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (receipt_window.winfo_width() // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (receipt_window.winfo_height() // 2)
        receipt_window.geometry(f"+{x}+{y}")

        text_bg_color = ctk.ThemeManager.theme["CTkFrame"]["fg_color"][ctk.get_appearance_mode_index()]
        text_fg_color = ctk.ThemeManager.theme["CTkLabel"]["text_color"][ctk.get_appearance_mode_index()]

        receipt_text = scrolledtext.ScrolledText(receipt_window, wrap=ctk.WORD, font=("Consolas", 10))
        receipt_text.pack(expand=True, fill="both", padx=10, pady=10)
        receipt_text.configure(state="normal", bg=text_bg_color, fg=text_fg_color)

        receipt_content = f"""
=====================================
          ORGANIZER - RECIBO
=====================================
Estabelecimento: {self.establishment_name}
Data/Hora: {timestamp}
Venda ID: {sale_id}
-------------------------------------
Itens:
"""
        for item_data in cart_items: 
            subtotal = item_data['quantity'] * item_data['price']
            receipt_content += f"{item_data['name']} (x{item_data['quantity']}) - R$ {item_data['price']:.2f} = R$ {subtotal:.2f}\n"

        subtotal_before_discount = sum(item['quantity'] * item['price'] for item in cart_items)
        discount_display = f"{discount_value:.2f}%" if discount_type == 'Porcentagem' else f"R$ {discount_value:.2f}"
        if discount_type == "Nenhum" or discount_value == 0.0:
            discount_display = "Nenhum"

        receipt_content += f"""
-------------------------------------
Subtotal: R$ {subtotal_before_discount:.2f}
Desconto ({discount_type}): {discount_display}
Total Final: R$ {total:.2f}
-------------------------------------
Cliente: {customer_name if customer_name else 'Não informado'}
Pagamento: {payment_method}
"""
        if payment_method == "Dinheiro":
            receipt_content += f"""Valor Recebido: R$ {received_amount:.2f}
Troco: R$ {change_amount:.2f}
"""
        receipt_content += f"""=====================================
    Obrigado pela preferência!
=====================================
"""
        receipt_text.insert(ctk.END, receipt_content)
        receipt_text.configure(state="disabled") 

        generate_pdf_btn = ctk.CTkButton(receipt_window, text="Gerar PDF para Impressão", command=lambda: self.generate_pdf_receipt(
            sale_id, timestamp, total, customer_name, payment_method, discount_value, discount_type, received_amount, change_amount, cart_items), corner_radius=10,
            fg_color="#4CAF50", hover_color="#45a049", font=ctk.CTkFont(size=13, weight="bold")
        )
        generate_pdf_btn.pack(pady=(5, 5))

        close_btn = ctk.CTkButton(receipt_window, text="Fechar Recibo", command=receipt_window.destroy, corner_radius=10,
                                fg_color=self.primary_green, hover_color=self.secondary_green, font=ctk.CTkFont(size=13, weight="bold"))
        close_btn.pack(pady=5)

    def generate_pdf_receipt(self, sale_id, timestamp, total, customer_name, payment_method, discount_value, discount_type, received_amount, change_amount, cart_items):
        """
        Gera um recibo em formato PDF.
        """
        file_name = f"recibo_venda_{sale_id}.pdf"
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
            initialfile=file_name,
            title="Salvar Recibo PDF Como"
        )

        if not filepath: 
            messagebox.showinfo("Cancelado", "Geração de PDF cancelada.")
            return

        try:
            c = canvas.Canvas(filepath, pagesize=letter)
            width, height = letter 

            left_margin = inch
            # right_margin = width - inch # Não utilizado diretamente, mas bom para referência
            top_margin = height - inch
            # bottom_margin = inch # Não utilizado diretamente

            y_position = top_margin
            line_height = 14 

            c.setFont("Helvetica-Bold", 16)
            c.drawString(left_margin, y_position, "ORGANIZER - RECIBO")
            y_position -= line_height * 2

            c.setFont("Helvetica", 10)
            c.drawString(left_margin, y_position, f"Estabelecimento: {self.establishment_name}")
            y_position -= line_height
            c.drawString(left_margin, y_position, f"Data/Hora: {timestamp}")
            y_position -= line_height
            c.drawString(left_margin, y_position, f"Venda ID: {sale_id}")
            y_position -= line_height * 2

            c.setFont("Helvetica-Bold", 12)
            c.drawString(left_margin, y_position, "Itens:")
            y_position -= line_height

            c.setFont("Helvetica", 10)
            for item_data in cart_items:
                subtotal = item_data['quantity'] * item_data['price']
                item_line = f"{item_data['name']} (x{item_data['quantity']}) - R$ {item_data['price']:.2f} = R$ {subtotal:.2f}"
                c.drawString(left_margin, y_position, item_line)
                y_position -= line_height

            y_position -= line_height

            subtotal_before_discount = sum(item['quantity'] * item['price'] for item in cart_items)
            discount_display = f"{discount_value:.2f}%" if discount_type == 'Porcentagem' else f"R$ {discount_value:.2f}"
            if discount_type == "Nenhum" or discount_value == 0.0:
                discount_display = "Nenhum"

            c.setFont("Helvetica-Bold", 10)
            c.drawString(left_margin, y_position, f"Subtotal: R$ {subtotal_before_discount:.2f}")
            y_position -= line_height
            c.drawString(left_margin, y_position, f"Desconto ({discount_type}): {discount_display}")
            y_position -= line_height * 2

            c.setFont("Helvetica-Bold", 14)
            c.drawString(left_margin, y_position, f"Total Final: R$ {total:.2f}")
            y_position -= line_height * 2

            c.setFont("Helvetica", 10)
            c.drawString(left_margin, y_position, f"Cliente: {customer_name if customer_name else 'Não informado'}")
            y_position -= line_height
            c.drawString(left_margin, y_position, f"Forma de Pagamento: {payment_method}")
            y_position -= line_height

            if payment_method == "Dinheiro":
                c.drawString(left_margin, y_position, f"Valor Recebido: R$ {received_amount:.2f}")
                y_position -= line_height
                c.drawString(left_margin, y_position, f"Troco: R$ {change_amount:.2f}")
                y_position -= line_height

            y_position -= line_height * 2

            c.setFont("Helvetica-Oblique", 10)
            c.drawCentredString(width / 2.0, y_position, "Obrigado pela preferência!")

            c.save() 

            messagebox.showinfo("PDF Gerado", f"Recibo gerado com sucesso!\nO arquivo foi salvo em:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Erro na Geração de PDF", f"Não foi possível gerar o PDF: {e}")
            print(f"Erro detalhado na geração de PDF: {e}") 


    def cancel_sale(self):
        """
        Cancela a venda atual, esvaziando o carrinho de compras.
        Pede confirmação ao usuário.
        """
        if messagebox.askyesno("Confirmar Cancelamento", "Tem certeza que deseja cancelar a venda atual? Todo o conteúdo do carrinho será esvaziado e a operação não poderá ser desfeita."):
            self.current_cart = {}
            self.update_cart_display()
            self.sales_quantity_entry.delete(0, ctk.END) 
            self.sales_quantity_entry.insert(0, "1") # Reseta para 1
            self.selected_product_for_sale = None 
            self.selected_product_display.configure(text="") 
            self.customer_sales_combobox.set("-- Selecione um Cliente (Opcional) --") # NOVO
            self.customer_name_entry.delete(0, ctk.END) 
            self.selected_customer_id = None # Reseta o ID do cliente selecionado
            self.payment_method_combobox.set("Dinheiro") 
            self.cart_quantity_entry.delete(0, ctk.END) 
            self.selected_cart_item_id = None 
            self.discount_entry.delete(0, ctk.END) 
            self.discount_type_combobox.set("Porcentagem") 
            self.current_discount_value = 0.0 
            self.current_discount_type = "Porcentagem" 
            self.received_amount_entry.delete(0, ctk.END) # Limpa valor recebido
            self.change_label.configure(text="R$ 0.00") # Limpa troco
            self.update_payment_fields() # Garante que campos de pagamento estejam corretos após cancelar a venda
            self.update_customer_dropdown_in_sales() # NOVO: Recarrega clientes
            messagebox.showinfo("Venda Cancelada", "A venda atual foi cancelada com sucesso.")

    def load_sales_history(self):
        """
        Carrega o histórico de vendas do banco de dados e o exibe no Treeview de histórico,
        aplicando filtros de busca e período.
        """
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        customer_search_term = self.history_customer_search_entry.get().strip().lower()
        product_search_term = self.history_product_search_entry.get().strip().lower()
        period_selection = self.history_period_combobox.get()

        start_date = None
        end_date = datetime.now()

        if period_selection == "Hoje":
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        elif period_selection == "Últimos 7 dias":
            start_date = datetime.now() - timedelta(days=7)
        elif period_selection == "Mês Atual":
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        query = """
            SELECT DISTINCT s.id, s.timestamp, s.total, 
                            COALESCE(c.name, s.customer_name) AS customer_display_name, -- Preferir nome do cliente cadastrado
                            s.payment_method, s.discount_value, s.discount_type, s.received_amount, s.change_amount
            FROM sales s
            LEFT JOIN sale_items si ON s.id = si.sale_id
            LEFT JOIN customers c ON s.customer_id = c.id -- NOVO JOIN com a tabela de clientes
            WHERE 1=1
        """
        params = []

        if customer_search_term:
            query += " AND (LOWER(COALESCE(c.name, s.customer_name)) LIKE ?)"
            params.append(f"%{customer_search_term}%")
        
        if product_search_term:
            query += " AND LOWER(si.product_name) LIKE ?"
            params.append(f"%{product_search_term}%")

        if start_date:
            query += " AND s.timestamp >= ? AND s.timestamp <= ?"
            params.append(start_date.strftime("%Y-%m-%d %H:%M:%S"))
            params.append(end_date.strftime("%Y-%m-%d %H:%M:%S"))
        
        query += " ORDER BY s.timestamp DESC"

        cursor.execute(query, tuple(params))
        sales = cursor.fetchall()
        conn.close()

        for sale in sales:
            discount_display = f"{sale[5]:.2f}%" if sale[6] == "Porcentagem" else f"R$ {sale[5]:.2f}"
            if sale[6] == "Nenhum" or sale[5] == 0.0:
                discount_display = "Nenhum"
            
            # Formata os valores recebido e troco
            received_display = f"R$ {sale[7]:.2f}" if sale[7] is not None else "N/A"
            change_display = f"R$ {sale[8]:.2f}" if sale[8] is not None else "N/A"

            self.history_tree.insert("", ctk.END, values=(sale[0], sale[1], f"R$ {sale[2]:.2f}", discount_display, 
                                                        sale[3] if sale[3] else "Não informado", sale[4] if sale[4] else "N/A",
                                                        received_display, change_display))

    def load_sales_for_returns(self, event=None):
        """
        Carrega as vendas para o módulo de devoluções, com opção de filtro.
        """
        for item in self.return_sales_tree.get_children():
            self.return_sales_tree.delete(item)
        
        search_term = self.return_sale_search_entry.get().strip().lower()

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        query = """
            SELECT s.id, s.timestamp, s.total, COALESCE(c.name, s.customer_name) AS customer_display_name, s.payment_method
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
            WHERE 1=1
        """
        params = []

        if search_term:
            query += " AND (CAST(s.id AS TEXT) LIKE ? OR LOWER(COALESCE(c.name, s.customer_name)) LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        query += " ORDER BY s.timestamp DESC"

        cursor.execute(query, tuple(params))
        sales = cursor.fetchall()
        conn.close()

        for sale in sales:
            self.return_sales_tree.insert("", ctk.END, values=(sale[0], sale[1], f"R$ {sale[2]:.2f}", sale[3] if sale[3] else "Não informado", sale[4] if sale[4] else "N/A"))
        
        self.return_sale_details_label.configure(text="Nenhuma venda selecionada.")
        for item in self.return_items_tree.get_children():
            self.return_items_tree.delete(item)
        self.process_return_btn.configure(state="disabled")
        self.selected_return_sale_id = None
        self.selected_return_item_id = None
        self.return_quantity_entry.delete(0, ctk.END)
        self.return_reason_entry.delete(0, ctk.END)

    def on_return_sale_select(self, event):
        """
        Carrega os itens da venda selecionada no Treeview de devoluções.
        """
        selected_item = self.return_sales_tree.focus()
        if selected_item:
            values = self.return_sales_tree.item(selected_item, 'values')
            self.selected_return_sale_id = int(values[0])
            sale_timestamp = values[1]
            sale_total = values[2]
            sale_customer = values[3]
            sale_payment = values[4]
            
            self.return_sale_details_label.configure(text=f"Venda ID: {self.selected_return_sale_id} | Data: {sale_timestamp} | Total: {sale_total} | Cliente: {sale_customer} | Pagamento: {sale_payment}")

            for item in self.return_items_tree.get_children():
                self.return_items_tree.delete(item)

            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT product_id, product_name, quantity, price FROM sale_items WHERE sale_id=?", (self.selected_return_sale_id,))
            items = cursor.fetchall()
            conn.close()

            for item_data in items:
                # Verificar quantidade já devolvida para este item nesta venda
                conn = sqlite3.connect(self.db_name)
                cursor = conn.cursor()
                cursor.execute("SELECT SUM(quantity) FROM returns WHERE sale_id=? AND product_id=?", (self.selected_return_sale_id, item_data[0]))
                returned_qty = cursor.fetchone()[0] or 0
                conn.close()

                remaining_qty_to_return = item_data[2] - returned_qty
                
                self.return_items_tree.insert("", ctk.END, values=(item_data[0], item_data[1], item_data[2], returned_qty, remaining_qty_to_return, f"R$ {item_data[3]:.2f}"))
            
            self.process_return_btn.configure(state="disabled")
            self.selected_return_item_id = None
            self.return_quantity_entry.delete(0, ctk.END)
            self.return_reason_entry.delete(0, ctk.END)
        else:
            self.selected_return_sale_id = None
            self.return_sale_details_label.configure(text="Nenhuma venda selecionada.")
            for item in self.return_items_tree.get_children():
                self.return_items_tree.delete(item)
            self.process_return_btn.configure(state="disabled")
            self.selected_return_item_id = None
            self.return_quantity_entry.delete(0, ctk.END)
            self.return_reason_entry.delete(0, ctk.END)

    def on_return_item_select(self, event):
        """
        Habilita o botão de processar devolução e popula a quantidade máxima para devolver.
        """
        selected_item = self.return_items_tree.focus()
        if selected_item and self.selected_return_sale_id is not None:
            values = self.return_items_tree.item(selected_item, 'values')
            self.selected_return_item_id = int(values[0]) # Product ID
            quantity_available_to_return = int(values[4]) # Qtde Disponível para devolver

            self.return_quantity_entry.delete(0, ctk.END)
            self.return_quantity_entry.insert(0, str(quantity_available_to_return))
            self.process_return_btn.configure(state="normal")
        else:
            self.process_return_btn.configure(state="disabled")
            self.selected_return_item_id = None
            self.return_quantity_entry.delete(0, ctk.END)
            self.return_reason_entry.delete(0, ctk.END)

    def process_return(self):
        """
        Processa a devolução de um item da venda selecionada.
        Atualiza o estoque e registra a devolução.
        """
        if self.user_role != 'admin':
            messagebox.showwarning("Permissão Negada", "Você não tem permissão para processar devoluções.")
            return

        if self.selected_return_sale_id is None or self.selected_return_item_id is None:
            messagebox.showwarning("Aviso", "Por favor, selecione uma venda e um item para devolução.")
            return
        
        try:
            return_quantity = int(self.return_quantity_entry.get().strip())
            if return_quantity <= 0:
                raise ValueError("A quantidade a devolver deve ser um número positivo.")
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira uma quantidade válida para devolução.")
            return
        
        return_reason = self.return_reason_entry.get().strip()
        if not return_reason:
            messagebox.showwarning("Aviso", "Por favor, insira o motivo da devolução.")
            return

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Obter a quantidade original vendida para este item nesta venda
        cursor.execute("SELECT quantity, product_name FROM sale_items WHERE sale_id=? AND product_id=?", (self.selected_return_sale_id, self.selected_return_item_id))
        sale_item_info = cursor.fetchone()
        
        if not sale_item_info:
            conn.close()
            messagebox.showerror("Erro", "Item da venda não encontrado.")
            return

        original_sold_quantity = sale_item_info[0]
        product_name = sale_item_info[1]

        # Verificar quantidade já devolvida para este item nesta venda
        cursor.execute("SELECT SUM(quantity) FROM returns WHERE sale_id=? AND product_id=?", (self.selected_return_sale_id, self.selected_return_item_id))
        returned_qty_so_far = cursor.fetchone()[0] or 0
        conn.close()

        if (returned_qty_so_far + return_quantity) > original_sold_quantity:
            messagebox.showwarning("Quantidade Inválida", f"A quantidade total devolvida para '{product_name}' não pode exceder a quantidade vendida ({original_sold_quantity}). Já foram devolvidas {returned_qty_so_far} unidades.")
            return
        
        if not messagebox.askyesno("Confirmar Devolução", f"Confirmar devolução de {return_quantity} unidades de '{product_name}' da Venda ID {self.selected_return_sale_id}?"):
            return

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            # 1. Atualizar estoque do produto
            cursor.execute("UPDATE products SET stock = stock + ? WHERE id=?", (return_quantity, self.selected_return_item_id))
            
            # 2. Registrar a devolução
            return_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO returns (sale_id, product_id, product_name, quantity, return_timestamp, reason, processed_by_user_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (self.selected_return_sale_id, self.selected_return_item_id, product_name, return_quantity, return_timestamp, return_reason, self.user_id))
            
            conn.commit()
            messagebox.showinfo("Sucesso", f"Devolução de {return_quantity} unidades de '{product_name}' processada com sucesso!")
            
            # Atualiza displays
            self.load_products_to_treeview()
            self.load_products_for_sale()
            self.load_sales_for_returns() # Recarrega a lista de vendas para devolução
            self.on_return_sale_select(None) # Limpa detalhes da venda selecionada
            self.check_low_stock_status()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Erro na Devolução", f"Ocorreu um erro ao processar a devolução: {e}")
            print(f"Erro detalhado ao processar devolução: {e}")
        finally:
            conn.close()


    def load_reports(self, event=None):
        """
        Carrega os relatórios de vendas e fluxo de caixa com base no período selecionado.
        """
        if self.user_role != 'admin':
            messagebox.showwarning("Permissão Negada", "Você não tem permissão para visualizar relatórios.")
            return

        period_selection = self.report_period_combobox.get()
        start_date = None
        end_date = datetime.now()

        if period_selection == "Hoje":
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        elif period_selection == "Últimos 7 dias":
            start_date = datetime.now() - timedelta(days=7)
        elif period_selection == "Mês Atual":
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # --- Relatório de Vendas por Produto ---
        for item in self.sales_by_product_tree.get_children():
            self.sales_by_product_tree.delete(item)
        
        query_sales_by_product = """
            SELECT si.product_name, SUM(si.quantity) as total_quantity, SUM(si.quantity * si.price) as total_revenue
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
        """
        params_by_product = []
        if start_date:
            query_sales_by_product += " WHERE s.timestamp >= ? AND s.timestamp <= ?"
            params_by_product.append(start_date.strftime("%Y-%m-%d %H:%M:%S"))
            params_by_product.append(end_date.strftime("%Y-%m-%d %H:%M:%S"))
        query_sales_by_product += " GROUP BY si.product_name ORDER BY total_revenue DESC"
        
        cursor.execute(query_sales_by_product, tuple(params_by_product))
        sales_by_product = cursor.fetchall()

        for item in sales_by_product:
            self.sales_by_product_tree.insert("", ctk.END, values=(item[0], item[1], f"R$ {item[2]:.2f}"))

        # --- Relatório de Vendas por Forma de Pagamento ---
        for item in self.sales_by_payment_tree.get_children():
            self.sales_by_payment_tree.delete(item)

        query_sales_by_payment = """
            SELECT payment_method, SUM(total) as total_revenue
            FROM sales
        """
        params_by_payment = []
        if start_date:
            query_sales_by_payment += " WHERE timestamp >= ? AND timestamp <= ?"
            params_by_payment.append(start_date.strftime("%Y-%m-%d %H:%M:%S"))
            params_by_payment.append(end_date.strftime("%Y-%m-%d %H:%M:%S"))
        query_sales_by_payment += " GROUP BY payment_method ORDER BY total_revenue DESC"

        cursor.execute(query_sales_by_payment, tuple(params_by_payment))
        sales_by_payment = cursor.fetchall()

        for item in sales_by_payment:
            self.sales_by_payment_tree.insert("", ctk.END, values=(item[0], f"R$ {item[1]:.2f}"))

        # --- Fluxo de Caixa (Resumo de Vendas) ---
        query_cash_flow = "SELECT SUM(total) FROM sales"
        params_cash_flow = []
        if start_date:
            query_cash_flow += " WHERE timestamp >= ? AND timestamp <= ?"
            params_cash_flow.append(start_date.strftime("%Y-%m-%d %H:%M:%S"))
            params_cash_flow.append(end_date.strftime("%Y-%m-%d %H:%M:%S"))
        
        cursor.execute(query_cash_flow, tuple(params_cash_flow))
        total_sales_for_period = cursor.fetchone()[0]
        if total_sales_for_period is None:
            total_sales_for_period = 0.0

        self.cash_flow_total_label.configure(text=f"Total de Vendas no Período: R$ {total_sales_for_period:.2f}")

        conn.close()

    def backup_database(self):
        """
        Cria um backup do arquivo do banco de dados (pdv.db).
        """
        if self.user_role != 'admin':
            messagebox.showwarning("Permissão Negada", "Você não tem permissão para fazer backup do banco de dados.")
            return

        default_filename = f"pdv_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("Arquivos de Banco de Dados SQLite", "*.db"), ("Todos os arquivos", "*.*")],
            initialfile=default_filename,
            title="Salvar Backup do Banco de Dados Como"
        )
        
        if not filepath:
            messagebox.showinfo("Backup Cancelado", "A operação de backup foi cancelada.")
            return

        try:
            if not os.path.exists(self.db_name):
                messagebox.showerror("Erro de Backup", f"O arquivo do banco de dados '{self.db_name}' não foi encontrado.")
                return

            shutil.copyfile(self.db_name, filepath)
            messagebox.showinfo("Backup Concluído", f"Backup do banco de dados salvo com sucesso em:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Erro de Backup", f"Ocorreu um erro ao fazer o backup: {e}\nVerifique se o aplicativo está acessando o banco de dados e tente novamente.")
            print(f"Erro detalhado no backup: {e}") 
            try:
                self.master.destroy() 
                root_auth = ctk.CTk()
                AuthApp(root_auth)
                root_auth.mainloop()
            except Exception as re_e:
                print(f"Erro ao tentar reabrir AuthApp após erro de backup: {re_e}")


    def restore_database(self):
        """
        Restaura o banco de dados a partir de um arquivo de backup selecionado.
        Esta é uma operação CRÍTICA e exige confirmação.
        """
        if self.user_role != 'admin':
            messagebox.showwarning("Permissão Negada", "Você não tem permissão para restaurar o banco de dados.")
            return

        if not messagebox.askyesno("Confirmar Restauração", 
                                   "ATENÇÃO: Restaurar o banco de dados irá apagar todos os dados atuais e substituí-los pelo conteúdo do arquivo de backup selecionado.\n"
                                   "Esta ação é irreversível. Tem certeza que deseja continuar?"):
            messagebox.showinfo("Restauração Cancelada", "A operação de restauração foi cancelada.")
            return

        filepath = filedialog.askopenfilename(
            defaultextension=".db",
            filetypes=[("Arquivos de Banco de Dados SQLite", "*.db"), ("Todos os arquivos", "*.*")],
            title="Selecionar Arquivo de Backup para Restaurar"
        )
        
        if not filepath:
            messagebox.showinfo("Restauração Cancelada", "Nenhum arquivo de backup selecionado. Operação cancelada.")
            return

        try:
            self.master.destroy() 
            
            shutil.copyfile(filepath, self.db_name)
            messagebox.showinfo("Restauração Concluída", "Banco de dados restaurado com sucesso! O aplicativo será reiniciado para carregar os novos dados.")
        except Exception as e:
            messagebox.showerror("Erro de Restauração", f"Ocorreu um erro ao restaurar o banco de dados: {e}\nCertifique-se de que o arquivo de backup é válido e que o aplicativo tem permissão para gravar no diretório.")
            print(f"Erro detalhado na restauração: {e}") 
        finally:
            root_auth = ctk.CTk()
            AuthApp(root_auth)
            root_auth.mainloop()


    def load_users_to_treeview(self):
        """
        Carrega todos os usuários do banco de dados e os exibe no Treeview de gerenciamento de usuários.
        """
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id, establishment_name, username, role FROM users ORDER BY username")
        users = cursor.fetchall()
        conn.close()

        for user in users:
            self.user_tree.insert("", ctk.END, values=(user[0], user[1], user[2], user[3]))

    def on_user_select(self, event):
        """
        Popula os campos de entrada com os detalhes do usuário selecionado no Treeview
        da aba de Gerenciamento de Usuários, para que possa ser editado.
        """
        selected_item = self.user_tree.focus()
        if selected_item:
            values = self.user_tree.item(selected_item, 'values')
            self.selected_user_id = int(values[0])
            self.user_username_entry.delete(0, ctk.END)
            self.user_username_entry.insert(0, values[2])
            self.user_role_combobox.set(values[3])

            self.user_password_entry.delete(0, ctk.END)
            self.user_confirm_password_entry.delete(0, ctk.END)

            self.update_user_btn.configure(state="normal" if self.user_role == 'admin' else "disabled")
            self.delete_user_btn.configure(state="normal" if self.user_role == 'admin' else "disabled")
            if self.selected_user_id == self.user_id:
                 self.delete_user_btn.configure(state="disabled")
        else:
            self.selected_user_id = None
            self.user_username_entry.delete(0, ctk.END)
            self.user_password_entry.delete(0, ctk.END)
            self.user_confirm_password_entry.delete(0, ctk.END)
            self.user_role_combobox.set("caixa")
            self.update_user_btn.configure(state="disabled")
            self.delete_user_btn.configure(state="disabled")

    def add_new_user(self):
        """
        Adiciona um novo usuário ao banco de dados. (Apenas para administradores)
        """
        if self.user_role != 'admin':
            messagebox.showwarning("Permissão Negada", "Você não tem permissão para adicionar novos usuários.")
            return

        username = self.user_username_entry.get().strip()
        password = self.user_password_entry.get().strip()
        confirm_password = self.user_confirm_password_entry.get().strip()
        role = self.user_role_combobox.get()
        establishment_name = self.establishment_name

        if not username or not password or not confirm_password or not role:
            messagebox.showerror("Erro", "Todos os campos devem ser preenchidos.")
            return

        if password != confirm_password:
            messagebox.showerror("Erro", "As senhas não coincidem.")
            return
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
            if cursor.fetchone()[0] > 0:
                messagebox.showerror("Erro", "Este nome de usuário já está em uso por outro usuário. Por favor, escolha outro nome de usuário.")
                return

            cursor.execute("INSERT INTO users (establishment_name, username, password_hash, role) VALUES (?, ?, ?, ?)",
                           (establishment_name, username, password_hash, role))
            conn.commit()
            messagebox.showinfo("Sucesso", f"Usuário '{username}' ({role}) adicionado com sucesso!")
            self.load_users_to_treeview()
            self.user_username_entry.delete(0, ctk.END)
            self.user_password_entry.delete(0, ctk.END)
            self.user_confirm_password_entry.delete(0, ctk.END)
            self.user_role_combobox.set("caixa")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}")
            print(f"Erro detalhado ao adicionar novo usuário: {e}") 
        finally:
            conn.close()

    def update_selected_user(self):
        """
        Atualiza as informações (username, role, e opcionalmente senha) do usuário selecionado. (Apenas para administradores)
        """
        if self.user_role != 'admin':
            messagebox.showwarning("Permissão Negada", "Você não tem permissão para atualizar usuários.")
            return

        if self.selected_user_id is None:
            messagebox.showwarning("Aviso", "Por favor, selecione um usuário para atualizar.")
            return

        username = self.user_username_entry.get().strip()
        password = self.user_password_entry.get().strip()
        confirm_password = self.user_confirm_password_entry.get().strip()
        role = self.user_role_combobox.get()

        if not username or not role:
            messagebox.showerror("Erro", "Nome de usuário e Função não podem estar vazios.")
            return
        
        if password and password != confirm_password:
            messagebox.showerror("Erro", "As novas senhas não coincidem.")
            return
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", (username, self.selected_user_id))
            if cursor.fetchone():
                messagebox.showerror("Erro", "Este nome de usuário já está em uso por outro usuário.")
                return

            if password:
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                cursor.execute("UPDATE users SET username=?, password_hash=?, role=? WHERE id=?", (username, password_hash, role, self.selected_user_id))
            else:
                cursor.execute("UPDATE users SET username=?, role=? WHERE id=?", (username, role, self.selected_user_id))
            
            conn.commit()
            messagebox.showinfo("Sucesso", f"Usuário '{username}' atualizado com sucesso!")
            self.load_users_to_treeview()
            self.on_user_select(None)

            if self.selected_user_id == self.user_id:
                if self.user_role != role or self.username != username:
                    messagebox.showinfo("Informação", "Suas permissões/nome de usuário foram alterados. Será necessário fazer login novamente para que as alterações entrem em vigor.")
                    self.logout()

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao atualizar o usuário: {e}")
            print(f"Erro detalhado ao atualizar usuário: {e}") 
        finally:
            conn.close()

    def delete_selected_user(self):
        """
        Exclui o usuário selecionado do banco de dados. (Apenas para administradores)
        """
        if self.user_role != 'admin':
            messagebox.showwarning("Permissão Negada", "Você não tem permissão para excluir usuários.")
            return

        if self.selected_user_id is None:
            messagebox.showwarning("Aviso", "Por favor, selecione um usuário para excluir.")
            return
        
        if self.selected_user_id == self.user_id:
            messagebox.showerror("Erro", "Você não pode excluir seu próprio usuário.")
            return

        username_to_delete = self.user_tree.item(self.user_tree.focus(), 'values')[2]

        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o usuário '{username_to_delete}'? Esta ação é irreversível."):
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM users WHERE id=?", (self.selected_user_id,))
                conn.commit()
                messagebox.showinfo("Sucesso", f"Usuário '{username_to_delete}' excluído com sucesso!")
                self.load_users_to_treeview()
                self.on_user_select(None)
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao excluir o usuário: {e}")
                print(f"Erro detalhado ao excluir usuário: {e}") 
            finally:
                conn.close()

    def open_change_password_window(self):
        """
        Abre uma nova janela para o usuário logado alterar sua senha.
        """
        change_password_window = ctk.CTkToplevel(self.master)
        change_password_window.title("Alterar Senha")
        change_password_window.geometry("380x280")
        change_password_window.transient(self.master)
        change_password_window.grab_set()

        self.master.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (change_password_window.winfo_width() // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (change_password_window.winfo_height() // 2)
        change_password_window.geometry(f"+{x}+{y}")

        change_password_frame = ctk.CTkFrame(change_password_window, fg_color=("gray90", "gray15"), corner_radius=15)
        change_password_frame.pack(pady=20, padx=20, fill="both", expand=True)
        change_password_frame.grid_columnconfigure(0, weight=1)
        change_password_frame.grid_columnconfigure(1, weight=2)

        ctk.CTkLabel(change_password_frame, text="Alterar Senha", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.primary_green).grid(row=0, column=0, columnspan=2, pady=15)

        ctk.CTkLabel(change_password_frame, text="Senha Antiga:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        old_password_entry = ctk.CTkEntry(change_password_frame, show="*", width=250, corner_radius=10)
        old_password_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(change_password_frame, text="Nova Senha:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        new_password_entry = ctk.CTkEntry(change_password_frame, show="*", width=250, corner_radius=10)
        new_password_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(change_password_frame, text="Confirmar Nova Senha:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        confirm_new_password_entry = ctk.CTkEntry(change_password_frame, show="*", width=250, corner_radius=10)
        confirm_new_password_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        def perform_password_change():
            old_pass = old_password_entry.get().strip()
            new_pass = new_password_entry.get().strip()
            confirm_new_pass = confirm_new_password_entry.get().strip()

            if not old_pass or not new_pass or not confirm_new_pass:
                messagebox.showerror("Erro", "Todos os campos devem ser preenchidos.")
                return
            
            if new_pass != confirm_new_pass:
                messagebox.showerror("Erro", "As novas senhas não coincidem.")
                return
            
            if new_pass == old_pass:
                messagebox.showwarning("Aviso", "A nova senha não pode ser igual à antiga.")
                return

            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            hashed_old_pass = hashlib.sha256(old_pass.encode()).hexdigest()
            hashed_new_pass = hashlib.sha256(new_pass.encode()).hexdigest()

            cursor.execute("SELECT id FROM users WHERE id=? AND password_hash=?", (self.user_id, hashed_old_pass))
            if cursor.fetchone():
                cursor.execute("UPDATE users SET password_hash=? WHERE id=?", (hashed_new_pass, self.user_id))
                conn.commit()
                messagebox.showinfo("Sucesso", "Senha alterada com sucesso! Você será desconectado.")
                change_password_window.destroy()
                self.logout()
            else:
                messagebox.showerror("Erro", "Senha antiga incorreta.")
            conn.close()

        change_btn = ctk.CTkButton(change_password_frame, text="Alterar Senha", command=perform_password_change,
                                    fg_color=self.primary_green, hover_color=self.secondary_green, corner_radius=10,
                                    font=ctk.CTkFont(size=14, weight="bold"))
        change_btn.grid(row=4, column=0, columnspan=2, pady=15)


    def load_customers_to_treeview(self):
        """
        Carrega todos os clientes do banco de dados e os exibe no Treeview de clientes.
        """
        self.filter_customers_management()

    def filter_customers_management(self, event=None):
        """
        Filtra os clientes na Treeview de gerenciamento com base no termo de busca.
        """
        search_term = self.customer_search_entry.get().strip().lower()
        
        for item in self.customer_tree.get_children():
            self.customer_tree.delete(item)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        if search_term:
            cursor.execute("SELECT id, name, phone, email FROM customers WHERE LOWER(name) LIKE ? OR LOWER(phone) LIKE ? OR LOWER(email) LIKE ? OR CAST(id AS TEXT) LIKE ? ORDER BY name",
                           (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        else:
            cursor.execute("SELECT id, name, phone, email FROM customers ORDER BY name")
        customers = cursor.fetchall()
        conn.close()

        for customer in customers:
            self.customer_tree.insert("", ctk.END, values=(customer[0], customer[1], customer[2] if customer[2] else "N/A", customer[3] if customer[3] else "N/A"))
        
        # Reseta os campos e desabilita botões se nada estiver selecionado
        self.on_customer_select(None) 

    def on_customer_select(self, event):
        """
        Popula os campos de entrada com os detalhes do cliente selecionado no Treeview
        da aba de Gerenciamento de Clientes.
        """
        selected_item = self.customer_tree.focus()
        if selected_item:
            values = self.customer_tree.item(selected_item, 'values')
            self.selected_customer_id = int(values[0])
            self.customer_name_entry_mgmt.delete(0, ctk.END)
            self.customer_name_entry_mgmt.insert(0, values[1])
            self.customer_phone_entry_mgmt.delete(0, ctk.END)
            self.customer_phone_entry_mgmt.insert(0, values[2] if values[2] != "N/A" else "")
            self.customer_email_entry_mgmt.delete(0, ctk.END)
            self.customer_email_entry_mgmt.insert(0, values[3] if values[3] != "N/A" else "")

            # Habilita botões
            self.add_customer_btn.configure(text="Atualizar Cliente" if self.user_role == 'admin' else "Adicionar/Atualizar Cliente", 
                                            state="normal" if self.user_role == 'admin' else "disabled")
            self.delete_customer_btn.configure(state="normal" if self.user_role == 'admin' else "disabled")
            self.view_customer_history_btn.configure(state="normal" if self.user_role == 'admin' else "disabled")

        else:
            self.selected_customer_id = None
            self.customer_name_entry_mgmt.delete(0, ctk.END)
            self.customer_phone_entry_mgmt.delete(0, ctk.END)
            self.customer_email_entry_mgmt.delete(0, ctk.END)
            # Desabilita botões
            self.add_customer_btn.configure(text="Adicionar/Atualizar Cliente", 
                                            state="normal" if self.user_role == 'admin' else "disabled")
            self.delete_customer_btn.configure(state="disabled")
            self.view_customer_history_btn.configure(state="disabled")

    def add_or_update_customer(self):
        """
        Adiciona um novo cliente ao banco de dados ou atualiza um cliente existente.
        """
        if self.user_role != 'admin':
            messagebox.showwarning("Permissão Negada", "Você não tem permissão para adicionar/atualizar clientes.")
            return

        name = self.customer_name_entry_mgmt.get().strip()
        phone = self.customer_phone_entry_mgmt.get().strip()
        email = self.customer_email_entry_mgmt.get().strip()

        if not name:
            messagebox.showerror("Erro", "O nome do cliente é obrigatório.")
            return

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        try:
            if self.selected_customer_id:
                # Atualizar cliente existente
                cursor.execute("UPDATE customers SET name=?, phone=?, email=? WHERE id=?", (name, phone, email, self.selected_customer_id))
                messagebox.showinfo("Sucesso", f"Cliente '{name}' atualizado com sucesso!")
            else:
                # Adicionar novo cliente
                cursor.execute("INSERT INTO customers (name, phone, email) VALUES (?, ?, ?)", (name, phone, email))
                messagebox.showinfo("Sucesso", f"Cliente '{name}' adicionado com sucesso!")
            
            conn.commit()
            self.load_customers_to_treeview()
            self.update_customer_dropdown_in_sales() # Atualiza o combobox de vendas
            self.on_customer_select(None) # Limpa os campos após a operação

        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Um cliente com a mesma combinação de Nome/Telefone/Email já existe.")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}")
            print(f"Erro detalhado ao adicionar/atualizar cliente: {e}")
        finally:
            conn.close()

    def delete_customer(self):
        """
        Exclui o cliente selecionado do banco de dados.
        """
        if self.user_role != 'admin':
            messagebox.showwarning("Permissão Negada", "Você não tem permissão para excluir clientes.")
            return

        selected_item = self.customer_tree.focus()
        if not selected_item:
            messagebox.showwarning("Aviso", "Por favor, selecione um cliente para excluir.")
            return
        
        customer_id = self.customer_tree.item(selected_item, 'values')[0]
        customer_name = self.customer_tree.item(selected_item, 'values')[1]

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;") # Garante que FKs estejam ativas

        try:
            # Verificar se o cliente tem vendas associadas
            cursor.execute("SELECT COUNT(*) FROM sales WHERE customer_id=?", (customer_id,))
            sales_count = cursor.fetchone()[0]

            if sales_count > 0:
                if not messagebox.askyesno("Atenção!", 
                                           f"O cliente '{customer_name}' está associado a {sales_count} vendas.\n"
                                           "Excluí-lo fará com que essas vendas não tenham mais um cliente vinculado, mas não serão apagadas.\n"
                                           "Deseja realmente continuar?"):
                    return
            else:
                if not messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o cliente '{customer_name}' (ID: {customer_id})? Esta ação é irreversível."):
                    return

            cursor.execute("DELETE FROM customers WHERE id=?", (customer_id,))
            conn.commit()
            messagebox.showinfo("Sucesso", f"Cliente '{customer_name}' excluído com sucesso!")
            self.load_customers_to_treeview()
            self.update_customer_dropdown_in_sales() # Atualiza o combobox de vendas
            self.on_customer_select(None) # Limpa os campos após a operação
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Erro", f"Ocorreu um erro ao excluir o cliente: {e}")
            print(f"Erro detalhado ao excluir cliente: {e}")
        finally:
            conn.close()

    def show_customer_purchase_history(self):
        """
        Exibe o histórico de compras do cliente selecionado em uma nova janela.
        """
        if self.user_role != 'admin':
            messagebox.showwarning("Permissão Negada", "Você não tem permissão para ver o histórico de clientes.")
            return

        if self.selected_customer_id is None:
            messagebox.showwarning("Aviso", "Por favor, selecione um cliente para ver o histórico de compras.")
            return
        
        customer_name = self.customer_name_entry_mgmt.get().strip()

        history_window = ctk.CTkToplevel(self.master)
        history_window.title(f"Histórico de Compras - {customer_name}")
        history_window.geometry("800x600")
        history_window.transient(self.master)
        history_window.grab_set()

        self.master.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (history_window.winfo_width() // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (history_window.winfo_height() // 2)
        history_window.geometry(f"+{x}+{y}")

        ctk.CTkLabel(history_window, text=f"Histórico de Compras de {customer_name}", 
                     font=ctk.CTkFont(size=18, weight="bold"), text_color=self.primary_green).pack(pady=10)

        history_tree = ttk.Treeview(history_window, columns=("ID Venda", "Data/Hora", "Total", "Desconto", "Pagamento"), show="headings", style="Treeview")
        history_tree.heading("ID Venda", text="ID Venda")
        history_tree.heading("Data/Hora", text="Data/Hora")
        history_tree.heading("Total", text="Total")
        history_tree.heading("Desconto", text="Desconto")
        history_tree.heading("Pagamento", text="Pagamento")
        history_tree.column("ID Venda", width=80, anchor="center")
        history_tree.column("Data/Hora", width=150)
        history_tree.column("Total", width=100, anchor="e")
        history_tree.column("Desconto", width=80, anchor="e")
        history_tree.column("Pagamento", width=100)
        history_tree.pack(expand=True, fill="both", padx=10, pady=10)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, timestamp, total, discount_value, discount_type, payment_method
            FROM sales
            WHERE customer_id = ?
            ORDER BY timestamp DESC
        """, (self.selected_customer_id,))
        sales = cursor.fetchall()
        conn.close()

        if not sales:
            ctk.CTkLabel(history_window, text="Nenhuma compra registrada para este cliente.", text_color="gray").pack(pady=10)

        for sale in sales:
            discount_display = f"{sale[3]:.2f}%" if sale[4] == "Porcentagem" else f"R$ {sale[3]:.2f}"
            if sale[4] == "Nenhum" or sale[3] == 0.0:
                discount_display = "Nenhum"
            history_tree.insert("", ctk.END, values=(sale[0], sale[1], f"R$ {sale[2]:.2f}", discount_display, sale[5] if sale[5] else "N/A"))

        close_btn = ctk.CTkButton(history_window, text="Fechar", command=history_window.destroy, corner_radius=10,
                                fg_color=self.primary_green, hover_color=self.secondary_green)
        close_btn.pack(pady=10)


    def logout(self):
        """
        Realiza o logout do usuário, fechando a janela do PDV e reabrindo a tela de login.
        """
        if messagebox.askyesno("Sair", "Tem certeza que deseja sair?"):
            self.master.destroy()
            root_auth = ctk.CTk()
            AuthApp(root_auth)
            root_auth.mainloop()


if __name__ == "__main__":
    root_auth = ctk.CTk()
    AuthApp(root_auth)
    root_auth.mainloop()
