import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import os
from PIL import Image
import io

DB = 'jda.db'

# ===== CONFIGURAÇÃO VISUAL NEON VERDE =====
st.set_page_config(page_title="JDA PIÇARRAS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;800&family=Playfair+Display:wght@700;900&display=swap');

.stApp {
        background: #000;
        color: #ffffff;
        margin-top: -80px;
    }

.block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

.stMarkdown,.stText, div[data-testid="stVerticalBlock"],.stColumn {
        border: none!important;
    }

.hero-container {
        position: relative;
        padding: 40px 40px 20px 40px;
        margin-bottom: 40px;
        text-align: center;
    }

.neon-line {
        width: 120px;
        height: 3px;
        background: #32FF7E;
        margin: 15px auto 0 auto;
        box-shadow: 0 0 20px #32FF7E, 0 0 40px #32FF7E;
    }

.logo-header {
        font-family: 'Playfair Display', serif;
        font-size: 96px;
        font-weight: 900;
        letter-spacing: 8px;
        margin: 0;
        text-transform: uppercase;
        line-height: 1;
        text-align: center;
    }

.logo-jda {
        background: linear-gradient(90deg, #32FF7E 0%, #FFD700 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-fill-color: transparent;
        filter: drop-shadow(0 0 15px rgba(50, 255, 126, 0.4));
    }

.logo-picaras {
        color: #ffffff;
    }

.sub-header {
        font-family: 'Montserrat', sans-serif;
        font-size: 18px;
        font-weight: 300;
        color: #cccccc;
        margin-top: 15px;
        letter-spacing: 6px;
        text-transform: uppercase;
    }

.section-title {
        font-family: 'Playfair Display', serif;
        font-size: 42px;
        font-weight: 700;
        color: #32FF7E;
        margin: 40px 0 25px 0;
        letter-spacing: 3px;
        text-align: center;
        text-shadow: 0 0 10px rgba(50, 255, 126, 0.5);
    }

.stButton>button {
        background: transparent;
        color: #32FF7E;
        border: 2px solid #32FF7E;
        border-radius: 0px;
        padding: 15px 30px;
        font-family: 'Montserrat', sans-serif;
        font-weight: 600;
        font-size: 14px;
        letter-spacing: 3px;
        text-transform: uppercase;
        transition: all 0.3s ease;
        margin: 0 5px;
    }

.stButton>button:hover {
        background: #32FF7E;
        color: #000;
        box-shadow: 0 0 25px #32FF7E;
        transform: translateY(-2px);
    }

.button-equal {
        width: 280px!important;
        margin: 0 auto;
    }

.button-equal > button {
        width: 280px!important;
        min-width: 280px!important;
    }

.stTextInput>div>div>input,.stSelectbox>div>div>select,.stTextArea>div>div>textarea {
        background: #111;
        border: 1px solid #333;
        border-radius: 0px;
        color: #fff;
        font-family: 'Montserrat', sans-serif;
    }

.stTextInput>div>div>input:focus {
        border: 1px solid #32FF7E!important;
        box-shadow: 0 0 10px rgba(50, 255, 126, 0.3)!important;
    }

.stRadio>div>label {
        color: #fff!important;
        font-family: 'Montserrat', sans-serif;
        font-weight: 400;
        font-size: 16px;
        letter-spacing: 2px;
    }

.stCheckbox>label {
        color: #fff!important;
        font-family: 'Montserrat', sans-serif;
        font-size: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ===== FUNÇÕES DO SISTEMA =====
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS alunos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT UNIQUE,
        senha TEXT,
        telefone TEXT,
        role TEXT DEFAULT 'aluno',
        status TEXT DEFAULT 'pendente',
        graduacao TEXT DEFAULT 'Iniciante',
        graduacao_solicitada TEXT DEFAULT 'Iniciante',
        data_cadastro TEXT,
        paga_mensalidade INTEGER DEFAULT 0,
        taxa_cadastro_paga INTEGER DEFAULT 0,
        foto_path TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS graduacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE,
        cor TEXT DEFAULT '#32FF7E',
        ordem INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS horarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dia TEXT,
        turma TEXT,
        horario TEXT,
        ordem INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        categoria TEXT,
        preco REAL,
        estoque INTEGER,
        descricao TEXT,
        imagem_url TEXT,
        ativo INTEGER DEFAULT 1,
        ordem INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER,
        data_pedido TEXT,
        status TEXT DEFAULT 'pendente',
        total REAL,
        FOREIGN KEY(aluno_id) REFERENCES alunos(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        preco_unitario REAL,
        FOREIGN KEY(pedido_id) REFERENCES pedidos(id),
        FOREIGN KEY(produto_id) REFERENCES produtos(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS configuracoes (
        chave TEXT PRIMARY KEY,
        valor TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS progressao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        graduacao TEXT,
        tipo TEXT,
        nome TEXT,
        ordem INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS progresso_aluno (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER,
        progressao_id INTEGER,
        concluido INTEGER DEFAULT 0,
        FOREIGN KEY(aluno_id) REFERENCES alunos(id),
        FOREIGN KEY(progressao_id) REFERENCES progressao(id),
        UNIQUE(aluno_id, progressao_id)
    )''')

    c.execute("INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES ('taxa_cadastro', '100.00')")
    c.execute("INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES ('chave_pix', 'jda.picaras@pix.com.br')")

    # SISTEMA DE 12 GRADUAÇÕES
    graduacoes_padrao = [
        ('Iniciante', '#888', 0),
        ('Verde', '#00FF00', 1),
        ('Amarela', '#FFD700', 2),
        ('Azul', '#0000FF', 3),
        ('Verde e Amarelo', '#32FF7E', 4),
        ('Verde e Azul', '#00FFFF', 5),
        ('Estagiário', '#FFFFFF', 6),
        ('Formado', '#FFFFFF', 7),
        ('Monitor', '#FFFFFF', 8),
        ('Instrutor', '#FFFFFF', 9),
        ('Contra Mestre', '#800080', 10),
        ('Mestre', '#000', 11)
    ]
    for grad in graduacoes_padrao:
        c.execute("INSERT OR IGNORE INTO graduacoes (nome, cor, ordem) VALUES (?,?,?)", grad)

    admin_senha = hash_senha('admin123')
    c.execute("INSERT OR IGNORE INTO alunos (nome, email, senha, role, status, taxa_cadastro_paga, graduacao) VALUES ('Admin JDA', 'admin@jda.com',?, 'admin', 'ativo', 1, 'Mestre')", (admin_senha,))
    conn.commit()
    conn.close()

def get_graduacoes():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM graduacoes ORDER BY ordem ASC")
    graduacoes = c.fetchall()
    conn.close()
    return graduacoes

def get_config(chave):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT valor FROM configuracoes WHERE chave =?", (chave,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else ""

def set_config(chave, valor):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?,?)", (chave, str(valor)))
    conn.commit()
    conn.close()

def resize_image(uploaded_file):
    image = Image.open(uploaded_file)
    image = image.convert('RGB')
    image = image.resize((400, 400))
    buf = io.BytesIO()
    image.save(buf, format='JPEG', quality=85)
    filename = f"img_{datetime.now().timestamp()}.jpg"
    filepath = os.path.join("static", filename)
    os.makedirs("static", exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(buf.getvalue())
    return filepath

init_db()

if 'pagina' not in st.session_state:
    st.session_state.pagina = 'site'
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []
if 'forcar_troca_senha' not in st.session_state:
    st.session_state.forcar_troca_senha = False

# ===== SITE PÚBLICO NEON =====
if st.session_state.pagina == 'site':
    st.markdown('<div class="hero-container">', unsafe_allow_html=True)
    st.markdown('<div class="logo-header"><span class="logo-jda">JDA</span> <span class="logo-picaras">PIÇARRAS</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="neon-line"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Capoeira • Disciplina • Respeito • Tradição</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            st.markdown('<div class="button-equal">', unsafe_allow_html=True)
            if st.button("INSCREVER-SE AGORA", use_container_width=True):
                st.session_state.pagina = 'cadastro'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with btn_col2:
            st.markdown('<div class="button-equal">', unsafe_allow_html=True)
            if st.button("ÁREA DO ALUNO", use_container_width=True):
                st.session_state.pagina = 'login'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">A ARTE DA CAPOEIRA</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,3,1])
    with col2:
        st.markdown("""
        <div style="text-align:center; font-family:'Montserrat'; font-size:16px; line-height:1.8; color:#cccccc; font-weight:300;">
        A JDA Piçarras transcende o conceito de academia. Somos guardiões de uma tradição secular brasileira,
        onde cada movimento carrega história, cada roda celebra a cultura e cada aluno constrói sua força interior.
        <br><br>
        <span style="color:#32FF7E; font-weight:600;">Mestre CACHORRO</span> - 19 anos dedicados à arte da Capoeira em Santa Catarina
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">HORÁRIOS</div>', unsafe_allow_html=True)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM horarios ORDER BY ordem ASC")
    horarios = c.fetchall()
    if horarios:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            for h in horarios:
                st.markdown(f"""
                <div style="text-align:center; padding:20px 0; border-bottom:1px solid #222;">
                    <div style="font-family:'Montserrat'; font-size:12px; color:#32FF7E; letter-spacing:4px; margin-bottom:8px; text-shadow: 0 0 8px #32FF7E;">{h[1].upper()}</div>
                    <div style="font-family:'Playfair Display'; font-size:28px; color:#fff; font-weight:700; margin-bottom:5px;">{h[2]}</div>
                    <div style="font-family:'Montserrat'; font-size:20px; color:#999; font-weight:300;">{h[3]}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align:center; color:#666;'>Horários em breve</div>", unsafe_allow_html=True)
    conn.close()

    st.write("")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("""
        <div style="text-align:center; padding:50px 0; border-top:1px solid #333;">
            <div style="font-family:'Playfair Display'; font-size:32px; color:#32FF7E; margin-bottom:15px; text-shadow: 0 0 10px rgba(50, 255, 126, 0.5);">PRIMEIRA AULA GRATUITA</div>
            <div style="font-family:'Montserrat'; font-size:14px; color:#999; margin-bottom:25px; letter-spacing:2px;">VENHA CONHECER O NOSSA GRUPO</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="button-equal">', unsafe_allow_html=True)
        if st.button("QUERO FAZER PARTE", use_container_width=True):
            st.session_state.pagina = 'cadastro'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='text-align:center; color:#444; font-family:Montserrat; font-size:12px; letter-spacing:3px; padding:30px 0;'>JDA PIÇARRAS 2026 • PIÇARRAS SC</div>", unsafe_allow_html=True)

# ===== SOBRE NÓS =====
elif st.session_state.pagina == 'sobre':
    st.markdown('<div class="logo-header" style="font-size:64px;"><span class="logo-jda">JDA</span> <span class="logo-picaras">PIÇARRAS</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="neon-line" style="width:80px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">NOSSOS HORÁRIOS</div>', unsafe_allow_html=True)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM horarios ORDER BY ordem ASC")
    horarios = c.fetchall()
    for h in horarios:
        st.markdown(f"""
        <div style="text-align:center; padding:20px 0; border-bottom:1px solid #222;">
            <div style="font-family:'Montserrat'; font-size:12px; color:#32FF7E; letter-spacing:4px; margin-bottom:8px; text-shadow: 0 0 8px #32FF7E;">{h[1].upper()}</div>
            <div style="font-family:'Playfair Display'; font-size:28px; color:#fff; font-weight:700; margin-bottom:5px;">{h[2]}</div>
            <div style="font-family:'Montserrat'; font-size:20px; color:#999; font-weight:300;">{h[3]}</div>
        </div>
        """, unsafe_allow_html=True)
    conn.close()

    st.markdown('<div class="button-equal">', unsafe_allow_html=True)
    if st.button("← VOLTAR AO SITE"):
        st.session_state.pagina = 'site'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ===== CADASTRO =====
elif st.session_state.pagina == 'cadastro':
    st.markdown('<div class="logo-header" style="font-size:64px;"><span class="logo-jda">JDA</span> <span class="logo-picaras">PIÇARRAS</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="neon-line" style="width:80px;"></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        nome = st.text_input("NOME COMPLETO")
        email = st.text_input("EMAIL")
        telefone = st.text_input("TELEFONE", placeholder="47999999")
        graduacao_solicitada = st.selectbox("GRADUAÇÃO SOLICITADA", [g[1] for g in get_graduacoes()])

        taxa_cadastro = float(get_config('taxa_cadastro'))
        chave_pix = get_config('chave_pix')

        st.markdown(f"<div style='color:#32FF7E; font-family:Montserrat; font-weight:600; margin:20px 0; text-shadow: 0 0 8px #32FF7E;'>TAXA DE CADASTRO: R$ {taxa_cadastro:.2f}</div>", unsafe_allow_html=True)
        st.code(f"PIX: {chave_pix}")
        st.info("APÓS PAGAR O PIX, AGUARDE O MESTRE CONFIRMAR O PAGAMENTO")

        st.markdown('<div class="button-equal">', unsafe_allow_html=True)
        if st.button("FINALIZAR CADASTRO", use_container_width=True):
            if nome and email and telefone:
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                try:
                    senha_temp = hash_senha(email.split('@')[0] + 'JDA')
                    c.execute("INSERT INTO alunos (nome, email, senha, telefone, graduacao_solicitada, data_cadastro, taxa_cadastro_paga, graduacao) VALUES (?,?,?,?,?,?,?,?)",
                              (nome, email, senha_temp, telefone, graduacao_solicitada, datetime.now().strftime('%Y-%m-%d'), 0, graduacao_solicitada))
                    conn.commit()
                    st.success("CADASTRO REALIZADO! AGUARDE APROVAÇÃO DO MESTRE JDA.")
                except sqlite3.IntegrityError:
                    st.error("EMAIL JÁ CADASTRADO")
                finally:
                    conn.close()
            else:
                st.error("PREENCHA TODOS OS CAMPOS")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="button-equal">', unsafe_allow_html=True)
    if st.button("← VOLTAR AO SITE"):
        st.session_state.pagina = 'site'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ===== RESET DE SENHA =====
elif st.session_state.pagina == 'reset_senha':
    st.markdown('<div class="logo-header" style="font-size:64px;"><span class="logo-jda">JDA</span> <span class="logo-picaras">PIÇARRAS</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="neon-line" style="width:80px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">RESETAR SENHA</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        email_reset = st.text_input("DIGITE SEU EMAIL CADASTRADO")

        st.markdown('<div class="button-equal">', unsafe_allow_html=True)
        if st.button("GERAR SENHA TEMPORÁRIA", use_container_width=True):
            if email_reset:
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("SELECT id, nome, telefone, role FROM alunos WHERE email =?", (email_reset,))
                usuario = c.fetchone()

                if usuario:
                    senha_temp = email_reset.split('@')[0] + 'JDA' + str(datetime.now().year)
                    senha_hash = hash_senha(senha_temp)
                    c.execute("UPDATE alunos SET senha =? WHERE id =?", (senha_hash, usuario[0]))
                    conn.commit()

                    st.success(f"SENHA TEMPORÁRIA GERADA: {senha_temp}")
                    st.info("ALUNO DEVE TROCAR A SENHA NO PRIMEIRO LOGIN")

                    if usuario[2]:
                        numero_limpo = str(usuario[2]).replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "")
                        if not numero_limpo.startswith("55"):
                            numero_limpo = "55" + numero_limpo
                        mensagem = f"JDA PIÇARRAS - RESET DE SENHA\nOlá {usuario[1]}, sua nova senha temporária é: {senha_temp}\nTroque assim que fizer login. OSS!"
                        link_whatsapp = f"https://wa.me/{numero_limpo}?text={mensagem.replace('\n', '%0A')}"
                        st.markdown(f'[ENVIAR VIA WHATSAPP]({link_whatsapp})', unsafe_allow_html=True)
                else:
                    st.error("EMAIL NÃO ENCONTRADO")
                conn.close()
            else:
                st.error("DIGITE O EMAIL")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="button-equal">', unsafe_allow_html=True)
    if st.button("← VOLTAR AO LOGIN"):
        st.session_state.pagina = 'login'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ===== LOGIN =====
elif st.session_state.pagina == 'login':
    st.markdown('<div class="logo-header" style="font-size:64px;"><span class="logo-jda">JDA</span> <span class="logo-picaras">PIÇARRAS</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="neon-line" style="width:80px;"></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        email = st.text_input("EMAIL")
        senha = st.text_input("SENHA", type="password")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.markdown('<div class="button-equal">', unsafe_allow_html=True)
            if st.button("ENTRAR", use_container_width=True):
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("SELECT * FROM alunos WHERE email =? AND senha =?", (email, hash_senha(senha)))
                usuario = c.fetchone()
                conn.close()
                if usuario:
                    if usuario[6] == 'pendente':
                        st.warning("CADASTRO AINDA PENDENTE DE APROVAÇÃO")
                    else:
                        st.session_state.usuario = usuario
                        if senha == email.split('@')[0] + 'JDA' + str(datetime.now().year):
                            st.session_state.forcar_troca_senha = True
                        st.session_state.pagina = 'admin' if usuario[5] == 'admin' else 'aluno'
                        st.rerun()
                else:
                    st.error("EMAIL OU SENHA INCORRETOS")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_btn2:
            st.markdown('<div class="button-equal">', unsafe_allow_html=True)
            if st.button("ESQUECI SENHA", use_container_width=True):
                st.session_state.pagina = 'reset_senha'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="button-equal">', unsafe_allow_html=True)
    if st.button("← VOLTAR AO SITE"):
        st.session_state.pagina = 'site'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)# ===== PAINEL DO ADMIN =====
elif st.session_state.pagina == 'admin':
    usuario = st.session_state.usuario
    st.markdown(f'<div class="logo-header" style="font-size:64px;"><span class="logo-jda">JDA</span> <span class="logo-picaras">PIÇARRAS</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="neon-line" style="width:80px;"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">BEM-VINDO, MESTRE {usuario[1].upper()}</div>', unsafe_allow_html=True)

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS progressao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        graduacao TEXT,
        tipo TEXT,
        nome TEXT,
        ordem INTEGER DEFAULT 0
    )''')

    aba = st.radio("", ["ALUNOS PENDENTES", "ALUNOS ATIVOS", "GRADUAÇÃO", "PROGRESSÃO", "HORÁRIOS", "LOJA", "PEDIDOS", "CONFIGURAÇÕES"], horizontal=True)

    if aba == "ALUNOS PENDENTES":
        st.markdown('<div class="section-title">ALUNOS AGUARDANDO APROVAÇÃO</div>', unsafe_allow_html=True)
        c.execute("SELECT * FROM alunos WHERE status = 'pendente' ORDER BY data_cadastro DESC")
        pendentes = c.fetchall()
        if pendentes:
            for aluno in pendentes:
                st.markdown(f"""
                <div style="padding:25px 0; border-bottom:1px solid #333;">
                    <div style="font-family:'Playfair Display'; font-size:28px; color:#32FF7E; text-shadow: 0 0 8px #32FF7E;">{aluno[1]}</div>
                    <div style="font-family:'Montserrat'; color:#ccc; margin:10px 0;">{aluno[2]} | {aluno[4]}</div>
                    <div style="font-family:'Montserrat'; color:#999;">Graduação: {aluno[8]} | Taxa: {'PAGA' if aluno[11] else 'PENDENTE'}</div>
                </div>
                """, unsafe_allow_html=True)

                taxa_paga = st.checkbox("TAXA PAGA", value=bool(aluno[11]), key=f"taxa_{aluno[0]}")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<div class="button-equal">', unsafe_allow_html=True)
                    if st.button(f"APROVAR", key=f"aprov_{aluno[0]}", use_container_width=True):
                        c.execute("UPDATE alunos SET status = 'ativo', taxa_cadastro_paga =? WHERE id =?", (1 if taxa_paga else 0, aluno[0]))
                        conn.commit()
                        mensagem = f"🔥 BEM-VINDO À JDA PIÇARRAS 🔥\nE aí {aluno[1]}, seu acesso foi LIBERADO!\n\nEmail: {aluno[2]}\nSenha: {aluno[2].split('@')[0]}JDA{datetime.now().year}\nOSS!"
                        if aluno[4]:
                            numero_limpo = str(aluno[4]).replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "")
                            if not numero_limpo.startswith("55"):
                                numero_limpo = "55" + numero_limpo
                            link_whatsapp = f"https://wa.me/{numero_limpo}?text={mensagem.replace('\n', '%0A')}"
                            st.markdown(f'[ENVIAR WHATSAPP]({link_whatsapp})', unsafe_allow_html=True)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with col2:
                    st.markdown('<div class="button-equal">', unsafe_allow_html=True)
                    if st.button(f"REJEITAR", key=f"rej_{aluno[0]}", use_container_width=True):
                        c.execute("DELETE FROM alunos WHERE id =?", (aluno[0],))
                        conn.commit()
                        st.warning("ALUNO REJEITADO!")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("NENHUM ALUNO PENDENTE")

    elif aba == "ALUNOS ATIVOS":
        st.markdown('<div class="section-title">ALUNOS ATIVOS</div>', unsafe_allow_html=True)
        c.execute("SELECT * FROM alunos WHERE status = 'ativo' AND role = 'aluno' ORDER BY nome")
        ativos = c.fetchall()
        for aluno in ativos:
            foto_path = aluno[12] if len(aluno) > 12 else ""
            foto_html = f'<img src="{foto_path}" style="width:80px;height:80px;border-radius:50%;object-fit:cover;border:2px solid #32FF7E;box-shadow:0 0 15px #32FF7E;">' if foto_path and os.path.exists(foto_path) else '<div style="width:80px;height:80px;border-radius:50%;background:#222;border:2px solid #32FF7E;display:flex;align-items:center;justify-content:center;color:#32FF7E;">JDA</div>'
            st.markdown(f"""
            <div style="padding:25px 0; border-bottom:1px solid #333; display:flex; gap:20px; align-items:center;">
                {foto_html}
                <div>
                    <div style="font-family:'Playfair Display'; font-size:28px; color:#32FF7E; text-shadow: 0 0 8px #32FF7E;">{aluno[1]}</div>
                    <div style="font-family:'Montserrat'; color:#ccc;">Graduação: {aluno[7]} | Mensalidade: {'ATIVA' if aluno[10] else 'INATIVA'}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            paga_mensal = st.checkbox("PAGA MENSALIDADE", value=bool(aluno[10]), key=f"mens_{aluno[0]}")
            st.markdown('<div class="button-equal">', unsafe_allow_html=True)
            if st.button("SALVAR", key=f"save_mens_{aluno[0]}"):
                c.execute("UPDATE alunos SET paga_mensalidade =? WHERE id =?", (1 if paga_mensal else 0, aluno[0]))
                conn.commit()
                st.success("ATUALIZADO!")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    elif aba == "PROGRESSÃO":
        st.markdown('<div class="section-title">CONFIGURAR PROGRESSÃO POR GRADUAÇÃO</div>', unsafe_allow_html=True)
        graduacoes = get_graduacoes()
        GRADUACOES_NOMES = [g[1] for g in graduacoes]

        grad_selecionada = st.selectbox("SELECIONE A GRADUAÇÃO", GRADUACOES_NOMES)

        st.markdown("### ADICIONAR ITEM DE PROGRESSÃO")
        col1, col2, col3 = st.columns([2,2,1])
        tipo_item = col1.selectbox("TIPO", ["MOVIMENTO", "BERIMBAU", "PANDEIRO", "ATRIBUTO"])
        nome_item = col2.text_input("NOME DO ITEM", placeholder="Ex: Meia-lua de frente")
        st.markdown('<div class="button-equal">', unsafe_allow_html=True)
        if col3.button("ADICIONAR"):
            if nome_item:
                c.execute("SELECT MAX(ordem) FROM progressao WHERE graduacao=?", (grad_selecionada,))
                max_ordem = c.fetchone()[0] or 0
                c.execute("INSERT INTO progressao (graduacao, tipo, nome, ordem) VALUES (?,?,?,?)",
                          (grad_selecionada, tipo_item.lower(), nome_item, max_ordem + 1))
                conn.commit()
                st.success("ITEM ADICIONADO!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(f"### ITENS PARA {grad_selecionada.upper()}")
        tipos = ["MOVIMENTO", "BERIMBAU", "PANDEIRO", "ATRIBUTO"]
        for tipo in tipos:
            c.execute("SELECT * FROM progressao WHERE graduacao=? AND tipo=? ORDER BY ordem ASC", (grad_selecionada, tipo.lower()))
            itens = c.fetchall()
            if itens:
                st.markdown(f"#### {tipo} ({len(itens)}/25)")
                for item in itens:
                    col1, col2 = st.columns([4,1])
                    col1.write(f"{item[4]}. {item[3]}")
                    if col2.button("EXCLUIR", key=f"del_prog_{item[0]}"):
                        c.execute("DELETE FROM progressao WHERE id=?", (item[0],))
                        conn.commit()
                        st.rerun()

    elif aba == "GRADUAÇÃO":
        st.markdown('<div class="section-title">APROVAR GRADUAÇÃO</div>', unsafe_allow_html=True)
        graduacoes = get_graduacoes()
        GRADUACOES_NOMES = [g[1] for g in graduacoes]
        c.execute("SELECT * FROM alunos WHERE status = 'ativo' AND role = 'aluno' ORDER BY nome")
        alunos = c.fetchall()
        for aluno in alunos:
            grad_atual = aluno[7]
            idx_atual = GRADUACOES_NOMES.index(grad_atual) if grad_atual in GRADUACOES_NOMES else 0
            proxima_grad = GRADUACOES_NOMES[idx_atual + 1] if idx_atual + 1 < len(GRADUACOES_NOMES) else None

            if proxima_grad:
                st.markdown(f"""
                <div style="padding:25px 0; border-bottom:1px solid #333;">
                    <div style="font-family:'Playfair Display'; font-size:28px; color:#32FF7E; text-shadow: 0 0 8px #32FF7E;">{aluno[1]}</div>
                    <div style="font-family:'Montserrat'; color:#ccc;">Graduação Atual: {grad_atual} → Próxima: {proxima_grad}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown('<div class="button-equal">', unsafe_allow_html=True)
                if st.button(f"PROMOVER PARA {proxima_grad.upper()}", key=f"prom_{aluno[0]}", use_container_width=True):
                    c.execute("UPDATE alunos SET graduacao =? WHERE id =?", (proxima_grad, aluno[0]))
                    conn.commit()
                    st.success(f"{aluno[1]} PROMOVIDO PARA {proxima_grad}!")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="padding:25px 0; border-bottom:1px solid #333;">
                    <div style="font-family:'Playfair Display'; font-size:28px; color:#32FF7E; text-shadow: 0 0 8px #32FF7E;">{aluno[1]}</div>
                    <div style="font-family:'Montserrat'; color:#FFD700;">GRADUAÇÃO: MESTRE</div>
                </div>
                """, unsafe_allow_html=True)

    elif aba == "HORÁRIOS":
        st.markdown('<div class="section-title">GESTÃO DE HORÁRIOS</div>', unsafe_allow_html=True)
        with st.expander("ADICIONAR HORÁRIO"):
            col1, col2, col3 = st.columns(3)
            novo_dia = col1.text_input("DIA")
            nova_turma = col2.text_input("TURMA")
            novo_horario = col3.text_input("HORÁRIO")
            st.markdown('<div class="button-equal">', unsafe_allow_html=True)
            if st.button("ADICIONAR"):
                if novo_dia and nova_turma and novo_horario:
                    c.execute("SELECT MAX(ordem) FROM horarios")
                    max_ordem = c.fetchone()[0] or 0
                    c.execute("INSERT INTO horarios (dia, turma, horario, ordem) VALUES (?,?,?,?)",
                              (novo_dia, nova_turma, novo_horario, max_ordem + 1))
                    conn.commit()
                    st.success("HORÁRIO ADICIONADO!")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        c.execute("SELECT * FROM horarios ORDER BY ordem ASC")
        horarios = c.fetchall()
        for h in horarios:
            st.markdown(f"""
            <div style="padding:20px 0; border-bottom:1px solid #333;">
                <div style="font-family:'Montserrat'; font-size:12px; color:#32FF7E; text-shadow: 0 0 8px #32FF7E;">{h[1].upper()}</div>
                <div style="font-family:'Playfair Display'; font-size:28px; color:#fff;">{h[2]}</div>
                <div style="font-family:'Montserrat'; font-size:20px; color:#999;">{h[3]}</div>
            </div>
            """, unsafe_allow_html=True)
            col1, col2, col3 = st.columns([3,3,1])
            dia_edit = col1.text_input("DIA", value=h[1], key=f"dia_{h[0]}")
            turma_edit = col2.text_input("TURMA", value=h[2], key=f"turma_{h[0]}")
            horario_edit = col3.text_input("HORÁRIO", value=h[3], key=f"hor_{h[0]}")
            st.markdown('<div class="button-equal">', unsafe_allow_html=True)
            if st.button("SALVAR", key=f"save_{h[0]}", use_container_width=True):
                c.execute("UPDATE horarios SET dia=?, turma=?, horario=? WHERE id=?", (dia_edit, turma_edit, horario_edit, h[0]))
                conn.commit()
                st.success("ATUALIZADO!")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="button-equal">', unsafe_allow_html=True)
            if st.button("EXCLUIR", key=f"del_{h[0]}", use_container_width=True):
                c.execute("DELETE FROM horarios WHERE id =?", (h[0],))
                conn.commit()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    elif aba == "LOJA":
        st.markdown('<div class="section-title">GESTÃO DA LOJA</div>', unsafe_allow_html=True)
        with st.expander("ADICIONAR PRODUTO"):
            nome_prod = st.text_input("NOME")
            categoria_prod = st.selectbox("CATEGORIA", ["CAMISA", "INSTRUMENTO", "ACESSORIO", "OUTROS"])
            preco_prod = st.number_input("PREÇO", min_value=0.0, step=0.50)
            estoque_prod = st.number_input("ESTOQUE", min_value=0, step=1)
            descricao_prod = st.text_area("DESCRIÇÃO")
            imagem_prod = st.file_uploader("IMAGEM", type=['jpg', 'jpeg', 'png'])
            st.markdown('<div class="button-equal">', unsafe_allow_html=True)
            if st.button("ADICIONAR PRODUTO"):
                imagem_path = resize_image(imagem_prod) if imagem_prod else ""
                c.execute("SELECT MAX(ordem) FROM produtos")
                max_ordem = c.fetchone()[0] or 0
                c.execute("INSERT INTO produtos (nome, categoria, preco, estoque, descricao, imagem_url, ativo, ordem) VALUES (?,?,?,?,?,?,?,?)",
                          (nome_prod, categoria_prod, preco_prod, estoque_prod, descricao_prod, imagem_path, 1, max_ordem + 1))
                conn.commit()
                st.success("PRODUTO ADICIONADO!")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        c.execute("SELECT * FROM produtos ORDER BY ordem ASC")
        produtos = c.fetchall()
        for prod in produtos:
            st.markdown(f"""
            <div style="padding:25px 0; border-bottom:1px solid #333;">
                <div style="font-family:'Playfair Display'; font-size:28px; color:#32FF7E; text-shadow: 0 0 8px #32FF7E;">{prod[1]}</div>
                <div style="font-family:'Montserrat'; color:#ccc;">R$ {prod[3]:.2f} | Estoque: {prod[4]}</div>
                <div style="font-family:'Montserrat'; color:#999;">{prod[5]}</div>
            </div>
            """, unsafe_allow_html=True)
            col1, col2 = st.columns([2,1])
            nome_edit = col1.text_input("NOME", value=prod[1], key=f"pn_{prod[0]}")
            preco_edit = col2.number_input("PREÇO", value=float(prod[3]), key=f"pp_{prod[0]}")
            estoque_edit = col1.number_input("ESTOQUE", value=int(prod[4]), key=f"pe_{prod[0]}")
            ativo_edit = col2.checkbox("ATIVO", value=bool(prod[7]), key=f"pa_{prod[0]}")
            st.markdown('<div class="button-equal">', unsafe_allow_html=True)
            if st.button("SALVAR", key=f"ps_{prod[0]}", use_container_width=True):
                c.execute("UPDATE produtos SET nome=?, preco=?, estoque=?, ativo=? WHERE id=?",
                          (nome_edit, preco_edit, estoque_edit, 1 if ativo_edit else 0, prod[0]))
                conn.commit()
                st.success("ATUALIZADO!")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="button-equal">', unsafe_allow_html=True)
            if st.button("EXCLUIR", key=f"pdel_{prod[0]}", use_container_width=True):
                c.execute("DELETE FROM produtos WHERE id =?", (prod[0],))
                conn.commit()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    elif aba == "PEDIDOS":
        st.markdown('<div class="section-title">PEDIDOS RECEBIDOS</div>', unsafe_allow_html=True)
        c.execute("""SELECT p.id, a.nome, p.data_pedido, p.total, p.status
                     FROM pedidos p JOIN alunos a ON p.aluno_id = a.id
                     ORDER BY p.data_pedido DESC""")
        pedidos = c.fetchall()
        for pedido in pedidos:
            st.markdown(f"""
            <div style="padding:25px 0; border-bottom:1px solid #333;">
                <div style="font-family:'Playfair Display'; font-size:28px; color:#32FF7E; text-shadow: 0 0 8px #32FF7E;">PEDIDO #{pedido[0]} - {pedido[1]}</div>
                <div style="font-family:'Montserrat'; color:#ccc;">R$ {pedido[3]:.2f} | {pedido[4].upper()} | {pedido[2]}</div>
            </div>
            """, unsafe_allow_html=True)
            c.execute("""SELECT pr.nome, ip.quantidade, ip.preco_unitario
                         FROM itens_pedido ip JOIN produtos pr ON ip.produto_id = pr.id
                         WHERE ip.pedido_id =?""", (pedido[0],))
            for item in c.fetchall():
                st.write(f'- {item[1]}x {item[0]} - R$ {item[2]:.2f}')
            novo_status = st.selectbox("STATUS", ["pendente", "pago", "enviado", "entregue"],
                                       index=["pendente", "pago", "enviado", "entregue"].index(pedido[4]), key=f"st_{pedido[0]}")
            st.markdown('<div class="button-equal">', unsafe_allow_html=True)
            if st.button("ATUALIZAR", key=f"stb_{pedido[0]}", use_container_width=True):
                c.execute("UPDATE pedidos SET status=? WHERE id=?", (novo_status, pedido[0]))
                conn.commit()
                st.success("STATUS ATUALIZADO!")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    elif aba == "CONFIGURAÇÕES":
        st.markdown('<div class="section-title">CONFIGURAÇÕES</div>', unsafe_allow_html=True)

        # ALTERAR SENHA DO ADMIN
        st.markdown("### ALTERAR SENHA DO ADMIN")
        senha_atual_admin = st.text_input("SENHA ATUAL", type="password", key="senha_atual_admin")
        nova_senha_admin = st.text_input("NOVA SENHA", type="password", key="nova_senha_admin")
        confirmar_senha_admin = st.text_input("CONFIRMAR NOVA SENHA", type="password", key="conf_senha_admin")
        st.markdown('<div class="button-equal">', unsafe_allow_html=True)
        if st.button("ALTERAR SENHA ADMIN"):
            if senha_atual_admin and nova_senha_admin and confirmar_senha_admin:
                if hash_senha(senha_atual_admin)!= usuario[3]:
                    st.error("SENHA ATUAL INCORRETA")
                elif nova_senha_admin!= confirmar_senha_admin:
                    st.error("SENHAS NÃO COINCIDEM")
                elif len(nova_senha_admin) < 6:
                    st.error("SENHA DEVE TER NO MÍNIMO 6 CARACTERES")
                else:
                    c.execute("UPDATE alunos SET senha =? WHERE id =?", (hash_senha(nova_senha_admin), usuario[0]))
                    conn.commit()
                    st.success("SENHA DO ADMIN ALTERADA COM SUCESSO!")
            else:
                st.error("PREENCHA TODOS OS CAMPOS")
        st.markdown('</div>', unsafe_allow_html=True)

        taxa_atual = float(get_config('taxa_cadastro'))
        nova_taxa = st.number_input("TAXA DE CADASTRO R$", value=taxa_atual, step=5.0)
        st.markdown('<div class="button-equal">', unsafe_allow_html=True)
        if st.button("SALVAR TAXA"):
            set_config('taxa_cadastro', nova_taxa)
            st.success("TAXA ATUALIZADA!")
        st.markdown('</div>', unsafe_allow_html=True)

        chave_atual = get_config('chave_pix')
        nova_chave = st.text_input("CHAVE PIX", value=chave_atual)
        st.markdown('<div class="button-equal">', unsafe_allow_html=True)
        if st.button("SALVAR PIX"):
            set_config('chave_pix', nova_chave)
            st.success("PIX ATUALIZADO!")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="button-equal">', unsafe_allow_html=True)
    if st.button("LOGOUT", use_container_width=True):
        st.session_state.pagina = 'site'
        st.session_state.usuario = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ===== PAINEL DO ALUNO =====
elif st.session_state.pagina == 'aluno':
    usuario = st.session_state.usuario
    st.markdown(f'<div class="logo-header" style="font-size:64px;"><span class="logo-jda">JDA</span> <span class="logo-picaras">PIÇARRAS</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="neon-line" style="width:80px;"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">BEM-VINDO, {usuario[1].upper()}</div>', unsafe_allow_html=True)

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS progresso_aluno (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER,
        progressao_id INTEGER,
        concluido INTEGER DEFAULT 0,
        FOREIGN KEY(aluno_id) REFERENCES alunos(id),
        FOREIGN KEY(progressao_id) REFERENCES progressao(id),
        UNIQUE(aluno_id, progressao_id)
    )''')

    aba_aluno = st.radio("", ["MEU PERFIL", "MINHA PROGRESSÃO", "LOJA"], horizontal=True)

    if aba_aluno == "MEU PERFIL":
        # FORÇA TROCA DE SENHA TEMPORÁRIA
        if st.session_state.get('forcar_troca_senha', False):
            st.warning("VOCÊ ESTÁ USANDO SENHA TEMPORÁRIA. TROQUE SUA SENHA AGORA.")
            nova_senha = st.text_input("NOVA SENHA", type="password")
            confirmar_senha = st.text_input("CONFIRMAR NOVA SENHA", type="password")
            st.markdown('<div class="button-equal">', unsafe_allow_html=True)
            if st.button("SALVAR NOVA SENHA"):
                if nova_senha and nova_senha == confirmar_senha:
                    if len(nova_senha) < 6:
                        st.error("SENHA DEVE TER NO MÍNIMO 6 CARACTERES")
                    else:
                        c.execute("UPDATE alunos SET senha =? WHERE id =?", (hash_senha(nova_senha), usuario[0]))
                        conn.commit()
                        st.session_state.forcar_troca_senha = False
                        st.success("SENHA ALTERADA COM SUCESSO!")
                        st.rerun()
                else:
                    st.error("SENHAS NÃO COINCIDEM")
            st.markdown('</div>', unsafe_allow_html=True)
            st.stop()

        foto_path = usuario[12] if len(usuario) > 12 else ""
        foto_html = f'<img src="{foto_path}" style="width:120px;height:120px;border-radius:50%;object-fit:cover;border:3px solid #32FF7E;box-shadow:0 0 25px #32FF7E;">' if foto_path and os.path.exists(foto_path) else '<div style="width:120px;height:120px;border-radius:50%;background:#222;border:3px solid #32FF7E;display:flex;align-items:center;justify-content:center;color:#32FF7E;font-size:32px;font-family:Playfair Display;">JDA</div>'

        col1, col2 = st.columns([1,3])
        with col1:
            st.markdown(foto_html, unsafe_allow_html=True)
            foto_upload = st.file_uploader("ALTERAR FOTO", type=['jpg','jpeg','png'])
            if foto_upload:
                foto_path = resize_image(foto_upload)
                c.execute("ALTER TABLE alunos ADD COLUMN IF NOT EXISTS foto_path TEXT")
                c.execute("UPDATE alunos SET foto_path =? WHERE id =?", (foto_path, usuario[0]))
                conn.commit()
                st.success("FOTO ATUALIZADA!")
                st.rerun()

        with col2:
            st.markdown(f"""
            <div style="padding:25px 0;">
                <div style="font-family:'Playfair Display'; font-size:28px; color:#32FF7E; text-shadow: 0 0 8px #32FF7E;">MEUS DADOS</div>
                <div style="font-family:'Montserrat'; color:#ccc; line-height:2;">
                    Nome: {usuario[1]}<br>
                    Email: {usuario[2]}<br>
                    Graduação Atual: {usuario[7]}<br>
                    Mensalidade: {'ATIVA' if usuario[10] else 'INATIVA'}<br>
                    Status: {usuario[6].upper()}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # TROCA DE SENHA VOLUNTÁRIA
        st.markdown("### ALTERAR MINHA SENHA")
        senha_atual = st.text_input("SENHA ATUAL", type="password", key="senha_atual")
        nova_senha_aluno = st.text_input("NOVA SENHA", type="password", key="nova_senha_aluno")
        confirmar_nova_aluno = st.text_input("CONFIRMAR NOVA SENHA", type="password", key="conf_nova_aluno")
        st.markdown('<div class="button-equal">', unsafe_allow_html=True)
        if st.button("ALTERAR SENHA"):
            if senha_atual and nova_senha_aluno and confirmar_nova_aluno:
                if hash_senha(senha_atual)!= usuario[3]:
                    st.error("SENHA ATUAL INCORRETA")
                elif nova_senha_aluno!= confirmar_nova_aluno:
                    st.error("SENHAS NÃO COINCIDEM")
                elif len(nova_senha_aluno) < 6:
                    st.error("SENHA DEVE TER NO MÍNIMO 6 CARACTERES")
                else:
                    c.execute("UPDATE alunos SET senha =? WHERE id =?", (hash_senha(nova_senha_aluno), usuario[0]))
                    conn.commit()
                    st.success("SENHA ALTERADA COM SUCESSO!")
            else:
                st.error("PREENCHA TODOS OS CAMPOS")
        st.markdown('</div>', unsafe_allow_html=True)

    elif aba_aluno == "MINHA PROGRESSÃO":
        st.markdown('<div class="section-title">MINHA PROGRESSÃO</div>', unsafe_allow_html=True)
        graduacao_atual = usuario[7]

        graduacoes = get_graduacoes()
        GRADUACOES_NOMES = [g[1] for g in graduacoes]
        idx_atual = GRADUACOES_NOMES.index(graduacao_atual) if graduacao_atual in GRADUACOES_NOMES else 0
        proxima_grad = GRADUACOES_NOMES[idx_atual + 1] if idx_atual + 1 < len(GRADUACOES_NOMES) else "MESTRE"

        if proxima_grad == "MESTRE" and graduacao_atual == "Mestre":
            st.success("VOCÊ JÁ É MESTRE! OSS!")
        else:
            st.markdown(f"<div style='text-align:center; color:#FFD700; font-family:Montserrat; font-size:16px; letter-spacing:3px; margin-bottom:30px;'>PRÓXIMA GRADUAÇÃO: {proxima_grad.upper()}</div>", unsafe_allow_html=True)

            tipos = ["MOVIMENTO", "BERIMBAU", "PANDEIRO", "ATRIBUTO"]
            for tipo in tipos:
                c.execute("SELECT * FROM progressao WHERE graduacao=? AND tipo=? ORDER BY ordem ASC", (proxima_grad, tipo.lower()))
                itens = c.fetchall()
                if itens:
                    st.markdown(f"#### {tipo} ({len(itens)})")
                    for item in itens:
                        c.execute("SELECT concluido FROM progresso_aluno WHERE aluno_id=? AND progressao_id=?", (usuario[0], item[0]))
                        status = c.fetchone()
                        concluido = bool(status[0]) if status else False
                        novo_status = st.checkbox(item[3], value=concluido, key=f"prog_{item[0]}")
                        if novo_status!= concluido:
                            c.execute("INSERT OR REPLACE INTO progresso_aluno (aluno_id, progressao_id, concluido) VALUES (?,?,?)",
                                      (usuario[0], item[0], 1 if novo_status else 0))
                            conn.commit()

                    concluidos = sum(1 for item in itens if st.session_state.get(f"prog_{item[0]}", False))
                    progresso = (concluidos / len(itens)) * 100 if itens else 0
                    st.progress(progresso / 100)
                    st.markdown(f"<div style='color:#32FF7E; font-family:Montserrat; text-align:right;'>{concluidos}/{len(itens)} CONCLUÍDOS</div>", unsafe_allow_html=True)
                    st.write("")

    elif aba_aluno == "LOJA":
        st.markdown('<div class="section-title">LOJA JDA</div>', unsafe_allow_html=True)
        c.execute("SELECT * FROM produtos WHERE ativo = 1 ORDER BY ordem ASC")
        produtos = c.fetchall()
        if produtos:
            cols = st.columns(3)
            for idx, prod in enumerate(produtos):
                with cols[idx % 3]:
                    if prod[6] and os.path.exists(prod[6]):
                        st.image(prod[6], use_container_width=True)
                    st.markdown(f"""
                    <div style="padding:20px 0; text-align:center;">
                        <div style="font-family:'Playfair Display'; font-size:24px; color:#32FF7E; text-shadow: 0 0 8px #32FF7E;">{prod[1]}</div>
                        <div style="font-family:'Montserrat'; font-size:20px; color:#fff; margin:10px 0;">R$ {prod[3]:.2f}</div>
                        <div style="font-family:'Montserrat'; color:#999; margin-bottom:15px;">Estoque: {prod[4]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    qtd = st.number_input("QTD", min_value=1, max_value=int(prod[4]), value=1, key=f"qtd_{prod[0]}")
                    st.markdown('<div class="button-equal">', unsafe_allow_html=True)
                    if st.button("ADICIONAR AO CARRINHO", key=f"add_{prod[0]}", use_container_width=True):
                        st.session_state.carrinho.append({
                            'id': prod[0],
                            'nome': prod[1],
                            'preco': prod[3],
                            'qtd': qtd
                        })
                        st.success("ADICIONADO AO CARRINHO!")
                    st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.carrinho:
            st.markdown('<div class="section-title">CARRINHO</div>', unsafe_allow_html=True)
            total = 0
            for item in st.session_state.carrinho:
                st.write(f"{item['qtd']}x {item['nome']} - R$ {item['preco'] * item['qtd']:.2f}")
                total += item['preco'] * item['qtd']
            st.markdown(f"<div style='color:#32FF7E; font-size:24px; font-family:Playfair Display; font-weight:700; text-shadow: 0 0 10px rgba(50, 255, 126, 0.5);'>TOTAL: R$ {total:.2f}</div>", unsafe_allow_html=True)
            st.code(f"PIX: {get_config('chave_pix')}")

            st.markdown('<div class="button-equal">', unsafe_allow_html=True)
            if st.button("FINALIZAR PEDIDO", use_container_width=True):
                try:
                    c.execute("INSERT INTO pedidos (aluno_id, data_pedido, total, status) VALUES (?,?,?,?)",
                              (usuario[0], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), total, 'pendente'))
                    pedido_id = c.lastrowid
                    for item in st.session_state.carrinho:
                        c.execute("INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?,?,?,?)",
                                  (pedido_id, item['id'], item['qtd'], item['preco']))
                        c.execute("UPDATE produtos SET estoque = estoque -? WHERE id =?", (item['qtd'], item['id']))
                    conn.commit()
                    st.session_state.carrinho = []
                    st.success("PEDIDO REALIZADO COM SUCESSO! O MESTRE JDA VAI ENTRAR EM CONTATO.")
                    st.rerun()
                except Exception as e:
                    st.error(f"ERRO AO FINALIZAR PEDIDO: {e}")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("SEU CARRINHO ESTÁ VAZIO")

    st.markdown('<div class="button-equal">', unsafe_allow_html=True)
    if st.button("LOGOUT", use_container_width=True):
        st.session_state.pagina = 'site'
        st.session_state.usuario = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    conn.close()