import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime
from PIL import Image
import io

st.set_page_config(page_title="JDA PIÇARRAS", layout="wide", initial_sidebar_state="collapsed")

# CSS NEON VERDE PRETO COM BOTÕES IGUAIS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&family=Playfair+Display:wght@700;800;900&display=swap');

* { font-family: 'Montserrat', sans-serif; }

.stApp {
    background: #0A0A0A;
    color: #FFFFFF;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > select,
.stNumberInput > div > div > input {
    background: #1A1A1A!important;
    border: 1px solid #333!important;
    border-radius: 0px!important;
    color: #FFFFFF!important;
    font-family: 'Montserrat'!important;
    font-weight: 500!important;
    padding: 12px 15px!important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div > select:focus,
.stNumberInput > div > div > input:focus {
    border: 1px solid #32FF7E!important;
    box-shadow: 0 0 15px rgba(50, 255, 126, 0.3)!important;
}

.stTextInput label,.stTextArea label,.stSelectbox label,.stNumberInput label,.stRadio label,.stCheckbox label {
    color: #FFFFFF!important;
    font-family: 'Montserrat'!important;
    font-weight: 600!important;
    font-size: 12px!important;
    letter-spacing: 1.5px!important;
    text-transform: uppercase!important;
}

/* BOTÕES IGUAIS */
.button-equal.stButton > button {
    background: #1A1A1A!important;
    border: 1px solid #32FF7E!important;
    border-radius: 0px!important;
    color: #FFFFFF!important;
    font-family: 'Montserrat'!important;
    font-weight: 600!important;
    font-size: 12px!important;
    letter-spacing: 2px!important;
    text-transform: uppercase!important;
    padding: 15px 30px!important;
    width: 100%!important;
    transition: all 0.3s ease!important;
}

.button-equal.stButton > button:hover {
    background: #32FF7E!important;
    color: #000!important;
    box-shadow: 0 0 25px rgba(50, 255, 126, 0.5)!important;
}

.logo-header {
    font-family: 'Playfair Display', serif!important;
    font-weight: 900!important;
    font-size: 72px!important;
    letter-spacing: 4px!important;
    text-align: center!important;
    margin-bottom: 10px!important;
}

.logo-jda { color: #32FF7E; text-shadow: 0 0 20px rgba(50, 255, 126, 0.6); }
.logo-picaras { color: #FFFFFF; }

.neon-line {
    height: 3px;
    background: linear-gradient(90deg, transparent, #32FF7E, transparent);
    box-shadow: 0 0 15px #32FF7E;
    margin: 30px auto;
}

.section-title {
    font-family: 'Playfair Display', serif!important;
    font-size: 42px!important;
    font-weight: 700!important;
    color: #FFFFFF!important;
    text-align: center!important;
    margin: 50px 0 30px 0!important;
    letter-spacing: 3px!important;
}

.sub-header {
    font-family: 'Montserrat'!important;
    font-size: 14px!important;
    font-weight: 500!important;
    letter-spacing: 4px!important;
    color: #CCCCCC!important;
    text-align: center!important;
    margin-bottom: 40px!important;
    text-transform: uppercase!important;
}

.stRadio > div { gap: 40px!important; justify-content: center!important; }
.stRadio > div > label {
    font-family: 'Montserrat'!important;
    font-weight: 600!important;
    font-size: 12px!important;
    letter-spacing: 2px!important;
    text-transform: uppercase!important;
    color: #CCCCCC!important;
}
.stRadio > div > label[data-selected="true"] {
    color: #32FF7E!important;
    text-shadow: 0 0 10px rgba(50, 255, 126, 0.5)!important;
}
</style>
""", unsafe_allow_html=True)

DB = 'jda.db'

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS alunos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        telefone TEXT,
        data_cadastro TEXT,
        status TEXT DEFAULT 'pendente',
        graduacao TEXT DEFAULT 'Iniciante',
        paga_mensalidade INTEGER DEFAULT 0,
        taxa_cadastro_paga INTEGER DEFAULT 0,
        role TEXT DEFAULT 'aluno',
        foto_path BLOB
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS horarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dia TEXT NOT NULL,
        turma TEXT NOT NULL,
        horario TEXT NOT NULL,
        ordem INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        categoria TEXT NOT NULL,
        preco REAL NOT NULL,
        estoque INTEGER DEFAULT 0,
        descricao TEXT,
        imagem_url BLOB,
        ativo INTEGER DEFAULT 1,
        ordem INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER,
        data_pedido TEXT,
        total REAL,
        status TEXT DEFAULT 'pendente',
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
    c.execute("INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES ('taxa_cadastro', '50.00')")
    c.execute("INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES ('chave_pix', 'jda.picaras@pix.com.br')")

    c.execute("SELECT * FROM alunos WHERE email = 'admin@jda.com'")
    if not c.fetchone():
        c.execute("INSERT INTO alunos (nome, email, senha, role, status, taxa_cadastro_paga) VALUES (?,?,?,?,?,?)",
                  ('Mestre JDA', 'admin@jda.com', hash_senha('admin123'), 'admin', 'ativo', 1))

    if not c.fetchone():
        horarios_iniciais = [
            ('SEGUNDA', 'INFANTIL', '18:00 - 19:00', 1), ('SEGUNDA', 'ADULTO', '19:00 - 20:30', 2),
            ('QUARTA', 'INFANTIL', '18:00 - 19:00', 3), ('QUARTA', 'ADULTO', '19:00 - 20:30', 4),
            ('SEXTA', 'RODA LIVRE', '19:00 - 21:00', 5)
        ]
        c.executemany("INSERT INTO horarios (dia, turma, horario, ordem) VALUES (?,?,?,?)", horarios_iniciais)
    conn.commit()
    conn.close()

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

def get_graduacoes():
    return [
        (1, 'Iniciante', '#FFFFFF'), (2, 'Crua', '#8B4513'), (3, 'Amarela', '#FFD700'),
        (4, 'Laranja', '#FF8C00'), (5, 'Azul', '#1E90FF'), (6, 'Verde', '#32CD32'),
        (7, 'Roxa', '#9370DB'), (8, 'Marrom', '#A0522D'), (9, 'Vermelha', '#DC143C'),
        (10, 'Mestre', '#FFD700')
    ]

def resize_image(uploaded_file):
    image = Image.open(uploaded_file)
    image = image.convert('RGB')
    image = image.resize((400, 400))
    buf = io.BytesIO()
    image.save(buf, format='JPEG', quality=85)
    return buf.getvalue()

init_db()

if 'pagina' not in st.session_state:
    st.session_state.pagina = 'site'
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []
if 'forcar_troca_senha' not in st.session_state:
    st.session_state.forcar_troca_senha = False

# ===== SITE PRINCIPAL =====
if st.session_state.pagina == 'site':
    st.markdown('<div class="logo-header"><span class="logo-jda">JDA</span> <span class="logo-picaras">PIÇARRAS</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="neon-line" style="width:100px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">ACADEMIA DE CAPOEIRA</div>', unsafe_allow_html=True)

    aba = st.radio("", ["HOME", "LOGIN", "REGISTRO"], horizontal=True)

    if aba == "HOME":
        st.markdown('<div class="section-title">HORÁRIOS DAS AULAS</div>', unsafe_allow_html=True)
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT * FROM horarios ORDER BY ordem ASC")
        horarios = c.fetchall()
        for h in horarios:
            st.markdown(f"""
            <div style="padding:25px 0; border-bottom:1px solid #333;">
                <div style="font-family:'Montserrat'; font-size:12px; color:#32FF7E; text-shadow: 0 0 8px #32FF7E; letter-spacing:2px;">{h[1].upper()}</div>
                <div style="font-family:'Playfair Display'; font-size:32px; color:#FFFFFF; font-weight:700; margin:8px 0;">{h[2]}</div>
                <div style="font-family:'Montserrat'; font-size:20px; color:#CCCCCC; font-weight:400;">{h[3]}</div>
            </div>
            """, unsafe_allow_html=True)
        conn.close()

    elif aba == "LOGIN":
        st.markdown('<div class="section-title">LOGIN</div>', unsafe_allow_html=True)
        email = st.text_input("EMAIL")
        senha = st.text_input("SENHA", type="password")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="button-equal">', unsafe_allow_html=True)
            if st.button("ENTRAR", use_container_width=True):
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("SELECT * FROM alunos WHERE email =?", (email,))
                usuario = c.fetchone()
                if usuario and usuario[3] == hash_senha(senha):
                    if usuario[6] == 'pendente':
                        st.error("SUA CONTA AINDA NÃO FOI APROVADA PELO MESTRE JDA!")
                    else:
                        st.session_state.usuario = usuario
                        st.session_state.pagina = 'admin' if usuario[11] == 'admin' else 'aluno'
                        st.rerun()
                else:
                    st.error("EMAIL OU SENHA INCORRETOS!")
                conn.close()
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="button-equal">', unsafe_allow_html=True)
            if st.button("ESQUECI SENHA", use_container_width=True):
                st.session_state.pagina = 'esqueci_senha'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    elif aba == "REGISTRO":
        st.markdown('<div class="section-title">REGISTRO DE ALUNO</div>', unsafe_allow_html=True)
        nome = st.text_input("NOME COMPLETO")
        email = st.text_input("EMAIL")
        senha = st.text_input("SENHA", type="password")
        telefone = st.text_input("TELEFONE WHATSAPP")

        st.markdown('<div class="button-equal">', unsafe_allow_html=True)
        if st.button("SOLICITAR CADASTRO", use_container_width=True):
            if nome and email and senha and telefone:
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO alunos (nome, email, senha, telefone, data_cadastro) VALUES (?,?,?,?,?)",
                              (nome, email, hash_senha(senha), telefone, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    conn.commit()
                    st.success("CADASTRO REALIZADO! AGUARDE APROVAÇÃO DO MESTRE JDA.")
                except sqlite3.IntegrityError:
                    st.error("EMAIL JÁ CADASTRADO!")
                conn.close()
            else:
                st.error("PREENCHA TODOS OS CAMPOS!")
        st.markdown('</div>', unsafe_allow_html=True)

# ===== ESQUECI SENHA =====
elif st.session_state.pagina == 'esqueci_senha':
    st.markdown('<div class="logo-header" style="font-size:64px;"><span class="logo-jda">JDA</span> <span class="logo-picaras">PIÇARRAS</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">RECUPERAR SENHA</div>', unsafe_allow_html=True)

    email_recuperar = st.text_input("DIGITE SEU EMAIL CADASTRADO")
    st.markdown('<div class="button-equal">', unsafe_allow_html=True)
    if st.button("GERAR SENHA TEMPORÁRIA"):
        if email_recuperar:
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute("SELECT * FROM alunos WHERE email =?", (email_recuperar,))
            usuario = c.fetchone()
            if usuario:
                nova_senha_temp = f"{email_recuperar.split('@')[0]}JDA{datetime.now().year}"
                c.execute("UPDATE alunos SET senha =? WHERE email =?", (hash_senha(nova_senha_temp), email_recuperar))
                conn.commit()
                st.success(f"SENHA TEMPORÁRIA GERADA: {nova_senha_temp}")
                st.info("USE ESSA SENHA NO LOGIN. VOCÊ SERÁ OBRIGADO A TROCAR NA PRIMEIRA ENTRADA.")
            else:
                st.error("EMAIL NÃO ENCONTRADO!")
            conn.close()
        else:
            st.error("DIGITE SEU EMAIL!")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="button-equal">', unsafe_allow_html=True)
    if st.button("VOLTAR AO LOGIN"):
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
                    <div style="font-family:'Montserrat'; color:#999;">Graduação: {aluno[7]} | Taxa: {'PAGA' if aluno[10] else 'PENDENTE'}</div>
                </div>
                """, unsafe_allow_html=True)

                taxa_paga = st.checkbox("TAXA PAGA", value=bool(aluno[10]), key=f"taxa_{aluno[0]}")

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
            if aluno[12]:
                st.image(aluno[12], width=80)
            else:
                st.markdown('<div style="width:80px;height:80px;border-radius:50%;background:#222;border:2px solid #32FF7E;display:flex;align-items:center;justify-content:center;color:#32FF7E;">JDA</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div style="padding:25px 0; border-bottom:1px solid #333;">
                <div style="font-family:'Playfair Display'; font-size:28px; color:#32FF7E; text-shadow: 0 0 8px #32FF7E;">{aluno[1]}</div>
                <div style="font-family:'Montserrat'; color:#ccc;">Graduação: {aluno[7]} | Mensalidade: {'ATIVA' if aluno[9] else 'INATIVA'}</div>
            </div>
            """, unsafe_allow_html=True)
            paga_mensal = st.checkbox("PAGA MENSALIDADE", value=bool(aluno[9]), key=f"mens_{aluno[0]}")
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
                imagem_bytes = resize_image(imagem_prod) if imagem_prod else None
                c.execute("SELECT MAX(ordem) FROM produtos")
                max_ordem = c.fetchone()[0] or 0
                c.execute("INSERT INTO produtos (nome, categoria, preco, estoque, descricao, imagem_url, ativo, ordem) VALUES (?,?,?,?,?,?,?,?)",
                          (nome_prod, categoria_prod, preco_prod, estoque_prod, descricao_prod, imagem_bytes, 1, max_ordem + 1))
                conn.commit()
                st.success("PRODUTO ADICIONADO!")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        c.execute("SELECT * FROM produtos ORDER BY ordem ASC")
        produtos = c.fetchall()
        for prod in produtos:
            if prod[6]:
                st.image(prod[6], width=200)
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
            if st.button("ATUALIZAR", key=f"stb_{pedido[0]}"):
                c.execute("UPDATE pedidos SET status =? WHERE id =?", (novo_status, pedido[0]))
                conn.commit()
                st.success("STATUS ATUALIZADO!")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    elif aba == "CONFIGURAÇÕES":
        st.markdown('<div class="section-title">CONFIGURAÇÕES DO SISTEMA</div>', unsafe_allow_html=True)
        taxa_atual = float(get_config('taxa_cadastro'))
        nova_taxa = st.number_input("VALOR DA TAXA DE CADASTRO (R$)", value=taxa_atual, min_value=0.0, step=5.0)
        chave_pix_atual = get_config('chave_pix')
        nova_chave_pix = st.text_input("CHAVE PIX", value=chave_pix_atual)
        st.markdown('<div class="button-equal">', unsafe_allow_html=True)
        if st.button("SALVAR CONFIGURAÇÕES"):
            set_config('taxa_cadastro', nova_taxa)
            set_config('chave_pix', nova_chave_pix)
            st.success("CONFIGURAÇÕES SALVAS!")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="button-equal">', unsafe_allow_html=True)
    if st.button("SAIR"):
        st.session_state.usuario = None
        st.session_state.pagina = 'site'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    conn.close()

# ===== PAINEL DO ALUNO =====
elif st.session_state.pagina == 'aluno':
    usuario = st.session_state.usuario
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    if st.session_state.forcar_troca_senha:
        st.markdown('<div class="section-title">TROCAR SENHA TEMPORÁRIA</div>', unsafe_allow_html=True)
        nova_senha = st.text_input("NOVA SENHA", type="password")
        confirmar_senha = st.text_input("CONFIRMAR SENHA", type="password")
        st.markdown('<div class="button-equal">', unsafe_allow_html=True)
        if st.button("SALVAR NOVA SENHA"):
            if nova_senha and nova_senha == confirmar_senha:
                c.execute("UPDATE alunos SET senha =? WHERE id =?", (hash_senha(nova_senha), usuario[0]))
                conn.commit()
                st.session_state.forcar_troca_senha = False
                st.success("SENHA ALTERADA! FAÇA LOGIN NOVAMENTE.")
                st.session_state.usuario = None
                st.session_state.pagina = 'site'
                st.rerun()
            else:
                st.error("SENHAS NÃO CONFEREM!")
        st.markdown('</div>', unsafe_allow_html=True)
        conn.close()
        st.stop()

    st.markdown(f'<div class="logo-header" style="font-size:64px;"><span class="logo-jda">JDA</span> <span class="logo-picaras">PIÇARRAS</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="neon-line" style="width:80px;"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">BEM-VINDO, {usuario[1].upper()}</div>', unsafe_allow_html=True)

    aba = st.radio("", ["MEU PERFIL", "PROGRESSÃO", "LOJA", "MEUS PEDIDOS"], horizontal=True)

    if aba == "MEU PERFIL":
        st.markdown('<div class="section-title">MEU PERFIL</div>', unsafe_allow_html=True)
        col1, col2 = st.columns([1,3])
        with col1:
            if usuario[12]:
                st.image(usuario[12], width=150)
            else:
                st.markdown('<div style="width:150px;height:150px;border-radius:50%;background:#222;border:3px solid #32FF7E;display:flex;align-items:center;justify-content:center;color:#32FF7E;font-size:48px;font-family:Playfair Display;">JDA</div>', unsafe_allow_html=True)
            foto_upload = st.file_uploader("ENVIAR FOTO", type=['jpg', 'jpeg', 'png'], key="foto_perfil")
            if foto_upload:
                foto_bytes = resize_image(foto_upload)
                c.execute("UPDATE alunos SET foto_path =? WHERE id =?", (foto_bytes, usuario[0]))
                conn.commit()
                st.success("FOTO ATUALIZADA!")
                st.rerun()

        with col2:
            st.markdown(f"""
            <div style="padding:25px 0;">
                <div style="font-family:'Playfair Display'; font-size:36px; color:#32FF7E; text-shadow: 0 0 8px #32FF7E;">{usuario[1]}</div>
                <div style="font-family:'Montserrat'; color:#ccc; margin:10px 0;">{usuario[2]} | {usuario[4]}</div>
                <div style="font-family:'Montserrat'; color:#32FF7E; font-weight:600;">GRADUAÇÃO: {usuario[7]}</div>
                <div style="font-family:'Montserrat'; color:#ccc;">STATUS MENSALIDADE: {'ATIVA' if usuario[9] else 'INATIVA'}</div>
            </div>
            """, unsafe_allow_html=True)

    elif aba == "PROGRESSÃO":
        st.markdown('<div class="section-title">MINHA PROGRESSÃO</div>', unsafe_allow_html=True)
        grad_atual = usuario[7]
        tipos = ["MOVIMENTO", "BERIMBAU", "PANDEIRO", "ATRIBUTO"]
        for tipo in tipos:
            c.execute("SELECT * FROM progressao WHERE graduacao=? AND tipo=? ORDER BY ordem ASC", (grad_atual, tipo.lower()))
            itens = c.fetchall()
            if itens:
                st.markdown(f"### {tipo} ({len(itens)}/25)")
                for item in itens:
                    st.checkbox(item[3], key=f"prog_{item[0]}", disabled=True)

    elif aba == "LOJA":
        st.markdown('<div class="section-title">LOJA JDA</div>', unsafe_allow_html=True)
        chave_pix = get_config('chave_pix')
        st.info(f"PIX PARA PAGAMENTO: {chave_pix}")
        c.execute("SELECT * FROM produtos WHERE ativo = 1 ORDER BY ordem ASC")
        produtos = c.fetchall()
        for prod in produtos:
            if prod[6]:
                st.image(prod[6], width=200)
            st.markdown(f"""
            <div style="padding:25px 0; border-bottom:1px solid #333;">
                <div style="font-family:'Playfair Display'; font-size:28px; color:#32FF7E; text-shadow: 0 0 8px #32FF7E;">{prod[1]}</div>
                <div style="font-family:'Montserrat'; color:#ccc;">R$ {prod[3]:.2f} | Estoque: {prod[4]}</div>
                <div style="font-family:'Montserrat'; color:#999;">{prod[5]}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('<div class="button-equal">', unsafe_allow_html=True)
            if st.button("ADICIONAR AO CARRINHO", key=f"cart_{prod[0]}", use_container_width=True):
                st.session_state.carrinho.append({'id': prod[0], 'nome': prod[1], 'preco': prod[3]})
                st.success(f"{prod[1]} ADICIONADO AO CARRINHO!")
            st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.carrinho:
            st.markdown("### CARRINHO")
            total = sum(item['preco'] for item in st.session_state.carrinho)
            for item in st.session_state.carrinho:
                st.write(f"- {item['nome']} - R$ {item['preco']:.2f}")
            st.write(f"**TOTAL: R$ {total:.2f}**")
            st.markdown('<div class="button-equal">', unsafe_allow_html=True)
            if st.button("FINALIZAR PEDIDO"):
                data_pedido = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                c.execute("INSERT INTO pedidos (aluno_id, data_pedido, total, status) VALUES (?,?,?,?)",
                          (usuario[0], data_pedido, total, 'pendente'))
                pedido_id = c.lastrowid
                for item in st.session_state.carrinho:
                    c.execute("INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?,?,?,?)",
                              (pedido_id, item['id'], 1, item['preco']))
                conn.commit()
                st.session_state.carrinho = []
                st.success("PEDIDO REALIZADO! ENVIE O COMPROVANTE DO PIX PARA O MESTRE JDA.")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    elif aba == "MEUS PEDIDOS":
        st.markdown('<div class="section-title">MEUS PEDIDOS</div>', unsafe_allow_html=True)
        c.execute("SELECT * FROM pedidos WHERE aluno_id =? ORDER BY data_pedido DESC", (usuario[0],))
        pedidos = c.fetchall()
        for pedido in pedidos:
            st.markdown(f"""
            <div style="padding:25px 0; border-bottom:1px solid #333;">
                <div style="font-family:'Playfair Display'; font-size:28px; color:#32FF7E; text-shadow: 0 0 8px #32FF7E;">PEDIDO #{pedido[0]}</div>
                <div style="font-family:'Montserrat'; color:#ccc;">R$ {pedido[3]:.2f} | {pedido[4].upper()} | {pedido[2]}</div>
            </div>
            """, unsafe_allow_html=True)
            c.execute("""SELECT pr.nome, ip.quantidade, ip.preco_unitario
                         FROM itens_pedido ip JOIN produtos pr ON ip.produto_id = pr.id
                         WHERE ip.pedido_id =?""", (pedido[0],))
            for item in c.fetchall():
                st.write(f'- {item[1]}x {item[0]} - R$ {item[2]:.2f}')

    st.markdown('<div class="button-equal">', unsafe_allow_html=True)
    if st.button("SAIR"):
        st.session_state.usuario = None
        st.session_state.pagina = 'site'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    conn.close()
