import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime
from PIL import Image
import io

st.set_page_config(page_title="JDA PIÇARRAS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&family=Playfair+Display:wght@700;800;900&display=swap');
* { font-family: 'Montserrat', sans-serif; }
.stApp { background: #0A0A0A; color: #FFFFFF; }
.stTextInput > div > div > input,.stTextArea > div > div > textarea,.stSelectbox > div > div > select,.stNumberInput > div > div > input {
    background: #1A1A1A!important; border: 1px solid #333!important; border-radius: 0px!important; color: #FFFFFF!important;
    font-family: 'Montserrat'!important; font-weight: 500!important; padding: 12px 15px!important;
}
.stTextInput > div > div > input:focus,.stTextArea > div > div > textarea:focus,.stSelectbox > div > div > select:focus,.stNumberInput > div > div > input:focus {
    border: 1px solid #32FF7E!important; box-shadow: 0 0 15px rgba(50, 255, 126, 0.3)!important; outline: none!important;
}
.stTextInput label,.stTextArea label,.stSelectbox label,.stNumberInput label,.stRadio label,.stCheckbox label {
    color: #FFFFFF!important; font-family: 'Montserrat'!important; font-weight: 600!important; font-size: 12px!important;
    letter-spacing: 1.5px!important; text-transform: uppercase!important;
}
.stButton > button {
    background: #1A1A1A!important; border: 2px solid #32FF7E!important; border-radius: 0px!important; color: #FFFFFF!important;
    font-family: 'Montserrat'!important; font-weight: 700!important; font-size: 13px!important; letter-spacing: 2.5px!important;
    text-transform: uppercase!important; padding: 16px 32px!important; width: 100%!important; transition: all 0.3s ease!important;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #32FF7E 0%, #FFD700 100%)!important; color: #000!important;
    box-shadow: 0 0 30px rgba(50, 255, 126, 0.5)!important; border: 2px solid #32FF7E!important;
}
.stRadio > div { gap: 40px!important; justify-content: center!important; flex-direction: row!important; }
.stRadio > div > label {
    font-family: 'Montserrat'!important; font-weight: 600!important; font-size: 12px!important; letter-spacing: 2px!important;
    text-transform: uppercase!important; color: #CCCCCC!important; padding: 8px 0!important;
}
.stRadio > div > label[data-selected="true"] { color: #32FF7E!important; text-shadow: 0 0 10px rgba(50, 255, 126, 0.5)!important; }
.stRadio > div > label > div:first-child { border-color: #32FF7E!important; }
.neon-line { height: 3px; background: linear-gradient(90deg, transparent, #32FF7E, #FFD700, transparent); box-shadow: 0 0 15px #32FF7E; margin: 30px auto; }
.section-title { font-family: 'Playfair Display', serif!important; font-size: 48px!important; font-weight: 700!important; color: #FFFFFF!important;
    text-align: center!important; margin: 50px 0 30px 0!important; letter-spacing: 3px!important; }
</style>
""", unsafe_allow_html=True)

DB = 'jda.db'

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS alunos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, email TEXT UNIQUE NOT NULL, senha TEXT NOT NULL, telefone TEXT,
        data_cadastro TEXT, status TEXT DEFAULT 'pendente', graduacao TEXT DEFAULT 'Iniciante', paga_mensalidade INTEGER DEFAULT 0,
        taxa_cadastro_paga INTEGER DEFAULT 0, role TEXT DEFAULT 'aluno', foto_path BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS horarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT, dia TEXT NOT NULL, turma TEXT NOT NULL, horario TEXT NOT NULL, ordem INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, categoria TEXT NOT NULL, preco REAL NOT NULL, estoque INTEGER DEFAULT 0,
        descricao TEXT, imagem_url BLOB, ativo INTEGER DEFAULT 1, ordem INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, data_pedido TEXT, total REAL, status TEXT DEFAULT 'pendente',
        FOREIGN KEY(aluno_id) REFERENCES alunos(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT, pedido_id INTEGER, produto_id INTEGER, quantidade INTEGER, preco_unitario REAL,
        FOREIGN KEY(pedido_id) REFERENCES pedidos(id), FOREIGN KEY(produto_id) REFERENCES produtos(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS configuracoes (chave TEXT PRIMARY KEY, valor TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS progressao (
        id INTEGER PRIMARY KEY AUTOINCREMENT, graduacao TEXT, tipo TEXT, nome TEXT, ordem INTEGER DEFAULT 0)''')
    c.execute("INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES ('taxa_cadastro', '50.00')")
    c.execute("INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES ('chave_pix', 'jda.picaras@pix.com.br')")
    c.execute("SELECT * FROM alunos WHERE email = 'admin@jda.com'")
    if not c.fetchone():
        c.execute("INSERT INTO alunos (nome, email, senha, role, status, taxa_cadastro_paga) VALUES (?,?,?,?,?,?)",
                  ('Mestre JDA', 'admin@jda.com', hash_senha('admin123'), 'admin', 'ativo', 1))
    c.execute("SELECT COUNT(*) FROM horarios")
    if c.fetchone()[0] == 0:
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
        (1, 'Iniciante', '#FFFFFF'), (2, 'Crua', '#8B4513'), (3, 'Amarela', '#FFD700'), (4, 'Laranja', '#FF8C00'),
        (5, 'Azul', '#1E90FF'), (6, 'Verde', '#32CD32'), (7, 'Roxa', '#9370DB'), (8, 'Marrom', '#A0522D'),
        (9, 'Vermelha', '#DC143C'), (10, 'Mestre', '#FFD700')
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

if st.session_state.pagina == 'site':
    aba = st.radio("", ["HOME", "LOGIN", "REGISTRO"], horizontal=True)

    if aba == "HOME":
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(0,0,0,0.92) 0%, rgba(10,10,10,0.98) 100%),
                    url('https://images.unsplash.com/photo-1544552866-d3ed42536cfd?q=80&w=2070') center/cover;
                    padding: 100px 40px 120px 40px; margin: -2rem -1rem 0 -1rem; text-align: center;">
            <div style="font-family:'Playfair Display'; font-size:88px; font-weight:900; letter-spacing: 5px; margin-bottom: 15px;
                        background: linear-gradient(90deg, #32FF7E 0%, #FFD700 100%); -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent; background-clip: text; text-shadow: 0 0 40px rgba(50,255,126,0.3);">
                JDA PIÇARRAS
            </div>
            <div style="font-family:'Montserrat'; font-size:16px; color:#CCCCCC; letter-spacing: 6px; text-transform: uppercase; margin-bottom: 40px;">
                ACADEMIA DE CAPOEIRA
            </div>
            <div style="font-family:'Montserrat'; font-size:18px; color:#AAAAAA; max-width:750px; margin: 0 auto 50px auto; line-height: 1.9; letter-spacing: 0.5px;">
                Tradição, disciplina e cultura em cada movimento. Formando capoeiristas e cidadãos através da arte da roda.
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("SE INSCREVER", use_container_width=True, key="btn_inscrever"):
                    st.session_state.pagina = 'site'
                    st.rerun()
            with col_btn2:
                if st.button("PORTAL DO ALUNO", use_container_width=True, key="btn_portal"):
                    st.session_state.pagina = 'site'
                    st.rerun()

        st.markdown("""
        <div style="padding: 80px 40px; background: #0A0A0A;">
            <div style="font-family:'Playfair Display'; font-size:48px; color:#FFFFFF; font-weight:700; text-align: center;
                        margin-bottom: 15px; letter-spacing: 3px;">HORÁRIOS DE TREINO</div>
            <div class="neon-line" style="width:120px; margin: 0 auto 60px auto;"></div>
        </div>
        """, unsafe_allow_html=True)

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT * FROM horarios ORDER BY ordem ASC")
        horarios = c.fetchall()
        conn.close()

        dias = {}
        for h in horarios:
            if h[1] not in dias:
                dias[h[1]] = []
            dias[h[1]].append(h)

        cols = st.columns(3)
        col_index = 0
        for dia, aulas in dias.items():
            with cols[col_index % 3]:
                st.markdown(f"""
                <div style="background: linear-gradient(180deg, #1A1A1A 0%, #0F0F0F 100%); border: 2px solid #32FF7E; padding: 35px;
                            margin-bottom: 35px; box-shadow: 0 0 20px rgba(50,255,126,0.1);">
                    <div style="font-family:'Montserrat'; font-size:14px; background: linear-gradient(90deg, #32FF7E 0%, #FFD700 100%);
                                -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
                                letter-spacing: 3px; font-weight: 700; margin-bottom: 25px; text-align: center;">
                        {dia.upper()}
                    </div>
                """, unsafe_allow_html=True)
                for aula in aulas:
                    st.markdown(f"""
                    <div style="margin-bottom: 22px; text-align: center;">
                        <div style="font-family:'Playfair Display'; font-size:26px; color:#FFFFFF; font-weight:700; margin-bottom: 8px;">
                            {aula[2]}
                        </div>
                        <div style="font-family:'Montserrat'; font-size:16px; color:#CCCCCC; letter-spacing: 1px;">
                            {aula[3]}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            col_index += 1

        st.markdown("""
        <div style="background: #000; border-top: 3px solid #32FF7E; padding: 60px 40px 30px 40px; margin: 80px -1rem -2rem -1rem;">
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 40px; max-width: 1200px; margin: 0 auto;">
                <div style="flex: 1; min-width: 250px;">
                    <div style="font-family:'Playfair Display'; font-size:32px; font-weight:900;
                                background: linear-gradient(90deg, #32FF7E 0%, #FFD700 100%); -webkit-background-clip: text;
                                -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 15px;">JDA PIÇARRAS</div>
                    <div style="font-family:'Montserrat'; font-size:14px; color:#888; line-height: 1.8;">Capoeira é liberdade. Capoeira é vida.</div>
                </div>
                <div style="flex: 1; min-width: 250px;">
                    <div style="font-family:'Montserrat'; font-size:14px; color:#32FF7E; font-weight: 700; letter-spacing: 2px;
                                margin-bottom: 15px; text-transform: uppercase;">CONTATO</div>
                    <div style="font-family:'Montserrat'; font-size:14px; color:#888; line-height: 2;">
                        Piçarras - SC<br>WhatsApp: (47) 99999-9999<br>Instagram: @jdapicaras
                    </div>
                </div>
                <div style="flex: 1; min-width: 250px;">
                    <div style="font-family:'Montserrat'; font-size:14px; color:#32FF7E; font-weight: 700; letter-spacing: 2px;
                                margin-bottom: 15px; text-transform: uppercase;">HORÁRIOS</div>
                    <div style="font-family:'Montserrat'; font-size:14px; color:#888; line-height: 2;">
                        Seg / Qua / Sex<br>Infantil: 18h às 19h<br>Adulto: 19h às 20h30
                    </div>
                </div>
            </div>
            <div style="border-top: 1px solid #222; margin-top: 50px; padding-top: 30px; text-align: center;">
                <div style="font-family:'Montserrat'; font-size:12px; color:#555; letter-spacing: 1.5px;">
                    © 2026 JDA PIÇARRAS - TODOS OS DIREITOS RESERVADOS
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    elif aba == "LOGIN":
        st.markdown('<div class="section-title">LOGIN</div>', unsafe_allow_html=True)
        email = st.text_input("EMAIL")
        senha = st.text_input("SENHA", type="password")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("ENTRAR", use_container_width=True):
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("SELECT * FROM alunos WHERE email =?", (email,))
                usuario = c.fetchone()
                if usuario and usuario[3] == hash_senha(senha):
                    if usuario[6] == 'pendente':
                        st.error("SUA CONTA AINDA NÃO FOI APROVADA PELO MESTRE JDA!")
                    else:
                        if usuario[3] == hash_senha(f"{email.split('@')[0]}JDA{datetime.now().year}"):
                            st.session_state.forcar_troca_senha = True
                        st.session_state.usuario = usuario
                        st.session_state.pagina = 'admin' if usuario[11] == 'admin' else 'aluno'
                        st.rerun()
                else:
                    st.error("EMAIL OU SENHA INCORRETOS!")
                conn.close()
        with col2:
            if st.button("ESQUECI SENHA", use_container_width=True):
                st.session_state.pagina = 'esqueci_senha'
                st.rerun()

    elif aba == "REGISTRO":
        st.markdown('<div class="section-title">REGISTRO DE ALUNO</div>', unsafe_allow_html=True)
        nome = st.text_input("NOME COMPLETO")
        email = st.text_input("EMAIL")
        senha = st.text_input("SENHA", type="password")
        telefone = st.text_input("TELEFONE WHATSAPP")
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

elif st.session_state.pagina == 'esqueci_senha':
    st.markdown("""
    <div style="font-family:'Playfair Display'; font-size:64px; font-weight:900; letter-spacing: 5px; margin-bottom: 15px;
                text-align: center; background: linear-gradient(90deg, #32FF7E 0%, #FFD700 100%); -webkit-background-clip: text;
                -webkit-text-fill-color: transparent; background-clip: text;">JDA PIÇARRAS</div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="section-title">RECUPERAR SENHA</div>', unsafe_allow_html=True)
    email_recuperar = st.text_input("DIGITE SEU EMAIL CADASTRADO")
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
    if st.button("VOLTAR AO LOGIN"):
        st.session_state.pagina = 'site'
        st.rerun()
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
            if st.button("SALVAR", key=f"ps_{prod[0]}", use_container_width=True):
                c.execute("UPDATE produtos SET nome=?, preco=?, estoque=?, ativo=? WHERE id=?",
                          (nome_edit, preco_edit, estoque_edit, 1 if ativo_edit else 0, prod[0]))
                conn.commit()
                st.success("ATUALIZADO!")
                st.rerun()
            if st.button("EXCLUIR", key=f"pdel_{prod[0]}", use_container_width=True):
                c.execute("DELETE FROM produtos WHERE id =?", (prod[0],))
                conn.commit()
                st.rerun()

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
            if st.button("ATUALIZAR", key=f"stb_{pedido[0]}"):
                c.execute("UPDATE pedidos SET status =? WHERE id =?", (novo_status, pedido[0]))
                conn.commit()
                st.success("STATUS ATUALIZADO!")
                st.rerun()

    elif aba == "CONFIGURAÇÕES":
        st.markdown('<div class="section-title">CONFIGURAÇÕES DO SISTEMA</div>', unsafe_allow_html=True)
        taxa_atual = float(get_config('taxa_cadastro'))
        nova_taxa = st.number_input("VALOR DA TAXA DE CADASTRO (R$)", value=taxa_atual, min_value=0.0, step=5.0)
        chave_pix_atual = get_config('chave_pix')
        nova_chave_pix = st.text_input("CHAVE PIX", value=chave_pix_atual)
        if st.button("SALVAR CONFIGURAÇÕES"):
            set_config('taxa_cadastro', nova_taxa)
            set_config('chave_pix', nova_chave_pix)
            st.success("CONFIGURAÇÕES SALVAS!")

    if st.button("SAIR"):
        st.session_state.usuario = None
        st.session_state.pagina = 'site'
        st.rerun()
    conn.close()

elif st.session_state.pagina == 'aluno':
    usuario = st.session_state.usuario
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    if st.session_state.forcar_troca_senha:
        st.markdown('<div class="section-title">TROCAR SENHA TEMPORÁRIA</div>', unsafe_allow_html=True)
        nova_senha = st.text_input("NOVA SENHA", type="password")
        confirmar_senha = st.text_input("CONFIRMAR SENHA", type="password")
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
        conn.close()
        st.stop()

    st.markdown("""
    <div style="font-family:'Playfair Display'; font-size:64px; font-weight:900; letter-spacing: 5px; margin-bottom: 15px;
                text-align: center; background: linear-gradient(90deg, #32FF7E 0%, #FFD700 100%); -webkit-background-clip: text;
                -webkit-text-fill-color: transparent; background-clip: text;">JDA PIÇARRAS</div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="neon-line" style="width:80px;"></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-family:Montserrat; font-size:14px; color:#CCC; text-align:center; margin-bottom:40px; letter-spacing:4px; text-transform:uppercase;">BEM-VINDO, {usuario[1].upper()}</div>', unsafe_allow_html=True)

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
            if st.button("ADICIONAR AO CARRINHO", key=f"cart_{prod[0]}", use_container_width=True):
                st.session_state.carrinho.append({'id': prod[0], 'nome': prod[1], 'preco': prod[3]})
                st.success(f"{prod[1]} ADICIONADO AO CARRINHO!")
        if st.session_state.carrinho:
            st.markdown("### CARRINHO")
            total = sum(item['preco'] for item in st.session_state.carrinho)
            for item in st.session_state.carrinho:
                st.write(f"- {item['nome']} - R$ {item['preco']:.2f}")
            st.write(f"**TOTAL: R$ {total:.2f}**")
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

    if st.button("SAIR"):
        st.session_state.usuario = None
        st.session_state.pagina = 'site'
        st.rerun()
    conn.close()
