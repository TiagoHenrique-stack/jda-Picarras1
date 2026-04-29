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
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&family=Playfair+Display:wght@700;800;900&display=swap');
* { font-family: 'Montserrat', sans-serif; }
.stApp { background: #0A0A0A; color: #FFFFFF; }
.stTextInput > div > div > input,.stTextArea > div > div > textarea,.stSelectbox > div > div > select,.stNumberInput > div > div > input {
    background: #1A1A1A!important; border: 1px solid #333!important; border-radius: 0px!important; color: #FFFFFF!important;
    font-family: 'Montserrat'!important; font-weight: 500!important; padding: 12px 15px!important;
}
.stTextInput > div > div > input:focus,.stTextArea > div > div > textarea:focus,.stSelectbox > div > div > select:focus,.stNumberInput > div > div > input:focus {
    border: 1px solid #32FF7E!important; box-shadow: 0 0 15px rgba(50, 255, 126, 0.3)!important; outline: none!important;
}
.stTextInput label,.stTextArea label,.stSelectbox label,.stNumberInput label,.stCheckbox label {
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
.neon-line { height: 3px; background: linear-gradient(90deg, transparent, #32FF7E, #FFD700, transparent); box-shadow: 0 0 15px #32FF7E; margin: 30px auto; }
.section-title { font-family: 'Playfair Display', serif!important; font-size: 48px!important; font-weight: 700!important; color: #FFFFFF!important;
    text-align: center!important; margin: 50px 0 30px 0!important; letter-spacing: 3px!important; }
.hero-title {
    font-family:'Playfair Display'; font-size:72px; font-weight:900; letter-spacing: 6px; margin-bottom: 25px;
    background: linear-gradient(90deg, #32FF7E 0%, #FFD700 100%); -webkit-background-clip: text;
    -webkit-text-fill-color: transparent; background-clip: text; text-shadow: 0 0 40px rgba(50,255,126,0.5);
    white-space: nowrap;
}
@media (max-width: 768px) {
.hero-title { font-size: 48px; white-space: normal; letter-spacing: 3px; }
}
.pix-box { background: #1A1A1A; border: 2px solid #32FF7E; padding: 30px; margin: 25px 0; box-shadow: 0 0 20px rgba(50,255,126,0.3); }
</style>
""", unsafe_allow_html=True)

DB = 'jda.db'

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def get_graduacoes():
    return [
        (1, 'Iniciante', '#FFFFFF'),
        (2, 'Verde', '#32CD32'),
        (3, 'Amarela', '#FFD700'),
        (4, 'Azul', '#1E90FF'),
        (5, 'Verde Amarela', '#ADFF2F'),
        (6, 'Verde Azul', '#20B2AA'),
        (7, 'Estagiário', '#FFA500'),
        (8, 'Formado', '#8B0000'),
        (9, 'Monitor', '#9932CC'),
        (10, 'Instrutor', '#DC143C'),
        (11, 'Contra Mestre', '#FFD700'),
        (12, 'Mestre', '#000')
    ]

def resize_image(uploaded_file):
    image = Image.open(uploaded_file)
    image = image.convert('RGB')
    image = image.resize((400, 400))
    buf = io.BytesIO()
    image.save(buf, format='JPEG', quality=85)
    return buf.getvalue()

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
        FOREIGN KEY(aluno_id) REFERENCES pedidos(id))''')
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
    c.execute("DELETE FROM progressao")
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

init_db()

if 'pagina' not in st.session_state:
    st.session_state.pagina = 'home'
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []
if 'forcar_troca_senha' not in st.session_state:
    st.session_state.forcar_troca_senha = False

if st.session_state.pagina == 'home':
    st.markdown("""
    <div style="background: #0A0A0A; padding: 160px 40px 180px 40px; margin: -2rem -1rem 0 -1rem; text-align: center; border-bottom: 3px solid #32FF7E;">
        <div class="hero-title">JDA PIÇARRAS</div>
        <div style="font-family:'Montserrat'; font-size:20px; color:#CCCCCC; letter-spacing: 10px; text-transform: uppercase; margin-bottom: 60px;">
            ACADEMIA PREMIUM DE CAPOEIRA
        </div>
        <div style="font-family:'Montserrat'; font-size:22px; color:#AAAAAA; max-width:850px; margin: 0 auto 70px auto;
                    line-height: 2.2; letter-spacing: 1px; font-weight: 400;">
            Tradição, disciplina e cultura em cada movimento. Formando capoeiristas e cidadãos através da arte da roda.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("SE INSCREVER", use_container_width=True, key="btn_inscrever"):
                st.session_state.pagina = 'registro'
                st.rerun()
        with col_btn2:
            if st.button("PORTAL DO ALUNO", use_container_width=True, key="btn_portal"):
                st.session_state.pagina = 'login'
                st.rerun()

    st.markdown("""
    <div style="padding: 120px 40px; background: #0A0A0A;">
        <div style="font-family:'Playfair Display'; font-size:60px; color:#FFFFFF; font-weight:700; text-align: center;
                    margin-bottom: 25px; letter-spacing: 5px;">HORÁRIOS DE TREINOS</div>
        <div class="neon-line" style="width:180px; margin: 0 auto 90px auto;"></div>
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
            <div style="background: linear-gradient(180deg, #1A1A1A 0%, #0F0F0F 100%); border: 2px solid #32FF7E; padding: 45px;
                        margin-bottom: 45px; box-shadow: 0 0 30px rgba(50,255,126,0.18);">
                <div style="font-family:'Montserrat'; font-size:16px; background: linear-gradient(90deg, #32FF7E 0%, #FFD700 100%);
                            -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
                            letter-spacing: 5px; font-weight: 800; margin-bottom: 35px; text-align: center;">
                    {dia.upper()}
                </div>
            """, unsafe_allow_html=True)
            for aula in aulas:
                st.markdown(f"""
                <div style="margin-bottom: 30px; text-align: center;">
                    <div style="font-family:'Playfair Display'; font-size:36px; color:#FFFFFF; font-weight:700; margin-bottom: 12px;">
                        {aula[2]}
                    </div>
                    <div style="font-family:'Montserrat'; font-size:18px; color:#CCCCCC; letter-spacing: 2px;">
                        {aula[3]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        col_index += 1

    st.markdown("""
    <div style="background: #000; border-top: 1px solid #222; padding: 40px; margin: 100px -1rem -2rem -1rem; text-align: center;">
        <div style="font-family:'Montserrat'; font-size:13px; color:#555; letter-spacing: 3px;">
            © 2026 JDA PIÇARRAS
        </div>
    </div>
    """, unsafe_allow_html=True)

elif st.session_state.pagina == 'login':
    st.markdown('<div class="section-title">LOGIN</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        email = st.text_input("EMAIL")
        senha = st.text_input("SENHA", type="password")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
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
                        st.session_state.pagina = 'admin' if usuario[10] == 'admin' else 'aluno'
                        st.rerun()
                else:
                    st.error("EMAIL OU SENHA INCORRETOS!")
                conn.close()
        with col_btn2:
            if st.button("VOLTAR", use_container_width=True):
                st.session_state.pagina = 'home'
                st.rerun()

elif st.session_state.pagina == 'registro':
    st.markdown('<div class="section-title">REGISTRO DE ALUNO</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        nome = st.text_input("NOME COMPLETO")
        email = st.text_input("EMAIL")
        senha = st.text_input("SENHA", type="password")
        telefone = st.text_input("TELEFONE WHATSAPP")

        taxa_cadastro = float(get_config('taxa_cadastro'))
        chave_pix = get_config('chave_pix')

        st.markdown(f"""
        <div class="pix-box">
            <div style="font-family:'Montserrat'; font-size:14px; color:#32FF7E; letter-spacing: 2px; font-weight: 700; margin-bottom: 15px;">
                TAXA DE CADASTRO: R$ {taxa_cadastro:.2f}
            </div>
            <div style="font-family:'Montserrat'; font-size:14px; color:#CCC; margin-bottom: 10px;">
                FAÇA O PAGAMENTO VIA PIX PARA LIBERAR SEU CADASTRO:
            </div>
            <div style="font-family:'Montserrat'; font-size:16px; color:#FFFFFF; font-weight: 700; background: #000; padding: 12px; border: 1px solid #333;">
                {chave_pix}
            </div>
            <div style="font-family:'Montserrat'; font-size:12px; color:#999; margin-top: 10px;">
                ENVIE O COMPROVANTE PARA O MESTRE JDA APÓS O REGISTRO
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("SOLICITAR CADASTRO", use_container_width=True):
            if nome and email and senha and telefone:
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO alunos (nome, email, senha, telefone, data_cadastro, taxa_cadastro_paga) VALUES (?,?,?,?,?,?)",
                              (nome, email, hash_senha(senha), telefone, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 0))
                    conn.commit()
                    st.success("CADASTRO REALIZADO! ENVIE O COMPROVANTE DO PIX PARA O MESTRE JDA APROVAR SEU ACESSO.")
                except sqlite3.IntegrityError:
                    st.error("EMAIL JÁ CADASTRADO!")
                conn.close()
            else:
                st.error("PREENCHA TODOS OS CAMPOS!")
        if st.button("VOLTAR PARA HOME", use_container_width=True):
            st.session_state.pagina = 'home'
            st.rerun()
elif st.session_state.pagina == 'esqueci_senha':
    st.markdown('<div class="section-title">RECUPERAR SENHA</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        email_recuperar = st.text_input("DIGITE SEU EMAIL CADASTRADO")
        if st.button("GERAR SENHA TEMPORÁRIA", use_container_width=True):
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
        if st.button("VOLTAR AO LOGIN", use_container_width=True):
            st.session_state.pagina = 'login'
            st.rerun()

elif st.session_state.pagina == 'admin':
    usuario = st.session_state.usuario
    if not usuario or usuario[10]!= 'admin':
        st.error("ACESSO NEGADO! VOCÊ NÃO É ADMINISTRADOR.")
        st.session_state.pagina = 'home'
        st.rerun()

    st.markdown('<div class="section-title">PAINEL MESTRE JDA</div>', unsafe_allow_html=True)

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    aba = st.radio("", ["ALUNOS PENDENTES", "ALUNOS ATIVOS", "GRADUAÇÃO", "GOLPES", "HORÁRIOS", "LOJA", "PEDIDOS", "CONFIGURAÇÕES"], horizontal=True)

    if aba == "ALUNOS PENDENTES":
        st.markdown('<div class="section-title">ALUNOS AGUARDANDO APROVAÇÃO</div>', unsafe_allow_html=True)
        c.execute("SELECT * FROM alunos WHERE status = 'pendente' ORDER BY data_cadastro DESC")
        pendentes = c.fetchall()
        if pendentes:
            for aluno in pendentes:
                st.markdown(f"""
                <div style="padding:30px 0; border-bottom:1px solid #333;">
                    <div style="font-family:'Playfair Display'; font-size:32px; color:#32FF7E; text-shadow: 0 0 10px #32FF7E;">{aluno[1]}</div>
                    <div style="font-family:'Montserrat'; color:#ccc; margin:12px 0;">{aluno[2]} | {aluno[4]}</div>
                    <div style="font-family:'Montserrat'; color:#FFD700;">TAXA CADASTRO: {'PAGA' if aluno[9] else 'PENDENTE'}</div>
                </div>
                """, unsafe_allow_html=True)
                taxa_paga = st.checkbox("CONFIRMAR PAGAMENTO TAXA", value=bool(aluno[9]), key=f"taxa_{aluno[0]}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"APROVAR ALUNO", key=f"aprov_{aluno[0]}", use_container_width=True):
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
                with col2:
                    if st.button(f"REJEITAR", key=f"rej_{aluno[0]}", use_container_width=True):
                        c.execute("DELETE FROM alunos WHERE id =?", (aluno[0],))
                        conn.commit()
                        st.warning("ALUNO REJEITADO!")
                        st.rerun()
        else:
            st.info("NENHUM ALUNO PENDENTE")

    elif aba == "ALUNOS ATIVOS":
        st.markdown('<div class="section-title">ALUNOS ATIVOS</div>', unsafe_allow_html=True)
        c.execute("SELECT * FROM alunos WHERE status = 'ativo' AND role = 'aluno' ORDER BY nome")
        ativos = c.fetchall()
        if ativos:
            for aluno in ativos:
                if aluno[11]:
                    st.image(aluno[11], width=80)
                else:
                    st.markdown('<div style="width:80px;height:80px;border-radius:50%;background:#222;border:2px solid #32FF7E;display:flex;align-items:center;justify-content:center;color:#32FF7E;">JDA</div>', unsafe_allow_html=True)
                st.markdown(f"""
                <div style="padding:30px 0; border-bottom:1px solid #333;">
                    <div style="font-family:'Playfair Display'; font-size:32px; color:#32FF7E; text-shadow: 0 0 10px #32FF7E;">{aluno[1]}</div>
                    <div style="font-family:'Montserrat'; color:#ccc;">Graduação: {aluno[7]} | Mensalidade: {'ATIVA' if aluno[8] else 'INATIVA'}</div>
                </div>
                """, unsafe_allow_html=True)
                paga_mensal = st.checkbox("PAGA MENSALIDADE", value=bool(aluno[8]), key=f"mens_{aluno[0]}")
                if st.button("SALVAR", key=f"save_mens_{aluno[0]}"):
                    c.execute("UPDATE alunos SET paga_mensalidade =? WHERE id =?", (1 if paga_mensal else 0, aluno[0]))
                    conn.commit()
                    st.success("ATUALIZADO!")
                    st.rerun()
        else:
            st.info("NENHUM ALUNO ATIVO")

    elif aba == "GOLPES":
        st.markdown('<div class="section-title">GESTÃO DE GOLPES POR GRADUAÇÃO</div>', unsafe_allow_html=True)
        graduacoes = get_graduacoes()
        GRADUACOES_NOMES = [g[1] for g in graduacoes]

        if 'grad_select' not in st.session_state:
            st.session_state.grad_select = GRADUACOES_NOMES[0]

        grad_selecionada = st.selectbox("SELECIONE A GRADUAÇÃO", GRADUACOES_NOMES, key="grad_select")

        st.markdown("### ADICIONAR GOLPE/MOVIMENTO")
        col1, col2, col3 = st.columns([2,2,1])

        with col1:
            tipo_item = st.selectbox("TIPO", ["MOVIMENTO", "BERIMBAU", "PANDEIRO", "ATRIBUTO"], key="tipo_select")
        with col2:
            nome_item = st.text_input("NOME DO GOLPE", placeholder="Ex: Meia-lua de frente", key="nome_golpe")
        with col3:
            st.write("")
            st.write("")
            if st.button("ADICIONAR", key="btn_add_golpe", use_container_width=True):
                if nome_item and nome_item.strip():
                    try:
                        # Abre conexão nova só pra este insert - funciona no Streamlit Cloud
                        conn_temp = sqlite3.connect(DB)
                        c_temp = conn_temp.cursor()
                        c_temp.execute("SELECT MAX(ordem) FROM progressao WHERE graduacao=?", (grad_selecionada,))
                        max_ordem = c_temp.fetchone()[0] or 0
                        c_temp.execute("INSERT INTO progressao (graduacao, tipo, nome, ordem) VALUES (?,?,?,?)",
                                  (grad_selecionada, tipo_item.lower(), nome_item.strip(), max_ordem + 1))
                        conn_temp.commit()
                        conn_temp.close()
                        st.success(f"GOLPE '{nome_item}' ADICIONADO EM {grad_selecionada}!")
                        st.session_state.nome_golpe = ""
                        st.rerun()
                    except Exception as e:
                        st.error(f"ERRO AO SALVAR: {e}")
                else:
                    st.error("DIGITE O NOME DO GOLPE!")

        # Lista os movimentos usando a conexão principal
        st.markdown(f"### GOLPES PARA {grad_selecionada.upper()}")
        tipos = ["MOVIMENTO", "BERIMBAU", "PANDEIRO", "ATRIBUTO"]
        for tipo in tipos:
            c.execute("SELECT * FROM progressao WHERE graduacao=? AND tipo=? ORDER BY ordem ASC", (grad_selecionada, tipo.lower()))
            itens = c.fetchall()
            if itens:
                st.markdown(f"#### {tipo} ({len(itens)}/25)")
                for item in itens:
                    col1, col2, col3 = st.columns([3,1,1])
                    col1.write(f"{item[3]}")
                    if col2.button("SUBIR", key=f"up_{item[0]}"):
                        if item[4] > 1:
                            c.execute("UPDATE progressao SET ordem = ordem - 1 WHERE id =?", (item[0],))
                            c.execute("UPDATE progressao SET ordem = ordem + 1 WHERE graduacao=? AND tipo=? AND ordem =? AND id!=?",
                                      (grad_selecionada, tipo.lower(), item[4] - 1, item[0]))
                            conn.commit()
                            st.rerun()
                    if col3.button("EXCLUIR", key=f"del_prog_{item[0]}"):
                        c.execute("DELETE FROM progressao WHERE id=?", (item[0],))
                        conn.commit()
                        st.success("GOLPE EXCLUÍDO!")
                        st.rerun()
            else:
                st.info(f"NENHUM {tipo} CADASTRADO PARA {grad_selecionada}")

    elif aba == "GRADUAÇÃO":
        st.markdown('<div class="section-title">APROVAR GRADUAÇÃO</div>', unsafe_allow_html=True)
        graduacoes = get_graduacoes()
        GRADUACOES_NOMES = [g[1] for g in graduacoes]
        c.execute("SELECT * FROM alunos WHERE status = 'ativo' AND role = 'aluno' ORDER BY nome")
        alunos = c.fetchall()
        if alunos:
            for aluno in alunos:
                grad_atual = aluno[7]
                if grad_atual in GRADUACOES_NOMES:
                    idx_atual = GRADUACOES_NOMES.index(grad_atual)
                    proxima_grad = GRADUACOES_NOMES[idx_atual + 1] if idx_atual + 1 < len(GRADUACOES_NOMES) else None
                else:
                    proxima_grad = GRADUACOES_NOMES[0]

                if proxima_grad:
                    st.markdown(f"""
                    <div style="padding:30px 0; border-bottom:1px solid #333;">
                        <div style="font-family:'Playfair Display'; font-size:32px; color:#32FF7E; text-shadow: 0 0 10px #32FF7E;">{aluno[1]}</div>
                        <div style="font-family:'Montserrat'; color:#ccc;">Graduação Atual: {grad_atual} → Próxima: {proxima_grad}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"PROMOVER PARA {proxima_grad.upper()}", key=f"prom_{aluno[0]}", use_container_width=True):
                        c.execute("UPDATE alunos SET graduacao =? WHERE id =?", (proxima_grad, aluno[0]))
                        conn.commit()
                        st.success(f"{aluno[1]} PROMOVIDO PARA {proxima_grad}!")
                        st.rerun()
                else:
                    st.markdown(f"""
                    <div style="padding:30px 0; border-bottom:1px solid #333;">
                        <div style="font-family:'Playfair Display'; font-size:32px; color:#32FF7E; text-shadow: 0 0 10px #32FF7E;">{aluno[1]}</div>
                        <div style="font-family:'Montserrat'; color:#FFD700;">GRADUAÇÃO: MESTRE - MÁXIMA</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("NENHUM ALUNO ATIVO PARA PROMOVER")

    elif aba == "HORÁRIOS":
        st.markdown('<div class="section-title">GESTÃO DE HORÁRIOS</div>', unsafe_allow_html=True)
        with st.expander("ADICIONAR HORÁRIO"):
            col1, col2, col3 = st.columns(3)
            novo_dia = col1.text_input("DIA DA SEMANA", key="novo_dia")
            nova_turma = col2.text_input("NOME DA TURMA", key="nova_turma")
            novo_horario = col3.text_input("HORÁRIO", key="novo_horario")
            if st.button("ADICIONAR", key="btn_add_horario"):
                if novo_dia and nova_turma and novo_horario:
                    c.execute("SELECT MAX(ordem) FROM horarios")
                    max_ordem = c.fetchone()[0] or 0
                    c.execute("INSERT INTO horarios (dia, turma, horario, ordem) VALUES (?,?,?,?)",
                              (novo_dia, nova_turma, novo_horario, max_ordem + 1))
                    conn.commit()
                    st.success("HORÁRIO ADICIONADO!")
                    st.rerun()

        c.execute("SELECT * FROM horarios ORDER BY ordem ASC")
        horarios = c.fetchall()
        if horarios:
            for h in horarios:
                st.markdown(f"""
                <div style="padding:25px 0; border-bottom:1px solid #333;">
                    <div style="font-family:'Montserrat'; font-size:13px; color:#32FF7E; text-shadow: 0 0 10px #32FF7E;">{h[1].upper()}</div>
                    <div style="font-family:'Playfair Display'; font-size:32px; color:#fff;">{h[2]}</div>
                    <div style="font-family:'Montserrat'; font-size:22px; color:#999;">{h[3]}</div>
                </div>
                """, unsafe_allow_html=True)
                col1, col2, col3 = st.columns([3,3,1])
                dia_edit = col1.text_input("DIA", value=h[1], key=f"dia_{h[0]}")
                turma_edit = col2.text_input("TURMA", value=h[2], key=f"turma_{h[0]}")
                horario_edit = col3.text_input("HORÁRIO", value=h[3], key=f"hor_{h[0]}")
                if st.button("SALVAR", key=f"save_{h[0]}", use_container_width=True):
                    c.execute("UPDATE horarios SET dia=?, turma=?, horario=? WHERE id=?", (dia_edit, turma_edit, horario_edit, h[0]))
                    conn.commit()
                    st.success("ATUALIZADO!")
                    st.rerun()
                if st.button("EXCLUIR", key=f"del_{h[0]}", use_container_width=True):
                    c.execute("DELETE FROM horarios WHERE id =?", (h[0],))
                    conn.commit()
                    st.success("HORÁRIO EXCLUÍDO!")
                    st.rerun()
        else:
            st.info("NENHUM HORÁRIO CADASTRADO")

    elif aba == "LOJA":
        st.markdown('<div class="section-title">GESTÃO DA LOJA</div>', unsafe_allow_html=True)
        with st.expander("ADICIONAR PRODUTO"):
            nome_prod = st.text_input("NOME DO PRODUTO", key="nome_prod")
            categoria_prod = st.selectbox("CATEGORIA", ["CAMISA", "INSTRUMENTO", "ACESSORIO", "OUTROS"], key="cat_prod")
            preco_prod = st.number_input("PREÇO", min_value=0.0, step=0.50, key="preco_prod")
            estoque_prod = st.number_input("ESTOQUE", min_value=0, step=1, key="estoque_prod")
            descricao_prod = st.text_area("DESCRIÇÃO", key="desc_prod")
            imagem_prod = st.file_uploader("IMAGEM", type=['jpg', 'jpeg', 'png'], key="img_prod")
            if st.button("ADICIONAR PRODUTO", key="btn_add_prod"):
                if nome_prod and preco_prod > 0:
                    imagem_bytes = resize_image(imagem_prod) if imagem_prod else None
                    c.execute("SELECT MAX(ordem) FROM produtos")
                    max_ordem = c.fetchone()[0] or 0
                    c.execute("INSERT INTO produtos (nome, categoria, preco, estoque, descricao, imagem_url, ativo, ordem) VALUES (?,?,?,?,?,?,?,?)",
                              (nome_prod, categoria_prod, preco_prod, estoque_prod, descricao_prod, imagem_bytes, 1, max_ordem + 1))
                    conn.commit()
                    st.success("PRODUTO ADICIONADO!")
                    st.rerun()
                else:
                    st.error("PREENCHA NOME E PREÇO!")

        c.execute("SELECT * FROM produtos ORDER BY ordem ASC")
        produtos = c.fetchall()
        if produtos:
            for prod in produtos:
                if prod[6]:
                    st.image(prod[6], width=200)
                st.markdown(f"""
                <div style="padding:30px 0; border-bottom:1px solid #333;">
                    <div style="font-family:'Playfair Display'; font-size:32px; color:#32FF7E; text-shadow: 0 0 10px #32FF7E;">{prod[1]}</div>
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
                    st.success("PRODUTO EXCLUÍDO!")
                    st.rerun()
        else:
            st.info("NENHUM PRODUTO CADASTRADO")

    elif aba == "PEDIDOS":
        st.markdown('<div class="section-title">PEDIDOS RECEBIDOS</div>', unsafe_allow_html=True)
        c.execute("""SELECT p.id, a.nome, p.data_pedido, p.total, p.status
                     FROM pedidos p JOIN alunos a ON p.aluno_id = a.id
                     ORDER BY p.data_pedido DESC""")
        pedidos = c.fetchall()
        if pedidos:
            for pedido in pedidos:
                st.markdown(f"""
                <div style="padding:30px 0; border-bottom:1px solid #333;">
                    <div style="font-family:'Playfair Display'; font-size:32px; color:#32FF7E; text-shadow: 0 0 10px #32FF7E;">PEDIDO #{pedido[0]} - {pedido[1]}</div>
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
                if st.button("ATUALIZAR STATUS", key=f"stb_{pedido[0]}"):
                    c.execute("UPDATE pedidos SET status =? WHERE id =?", (novo_status, pedido[0]))
                    conn.commit()
                    st.success("STATUS ATUALIZADO!")
                    st.rerun()
        else:
            st.info("NENHUM PEDIDO RECEBIDO")

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

    if st.button("SAIR", use_container_width=True):
        st.session_state.usuario = None
        st.session_state.pagina = 'home'
        st.rerun()
    conn.close()

elif st.session_state.pagina == 'aluno':
    usuario = st.session_state.usuario

    # BLOQUEIA ADMIN DE ENTRAR NO PAINEL DE ALUNO
    if usuario[10] == 'admin':
        st.session_state.pagina = 'admin'
        st.rerun()

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    if st.session_state.forcar_troca_senha:
        st.markdown('<div class="section-title">TROCAR SENHA TEMPORÁRIA</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            nova_senha = st.text_input("NOVA SENHA", type="password")
            confirmar_senha = st.text_input("CONFIRMAR SENHA", type="password")
            if st.button("SALVAR NOVA SENHA", use_container_width=True):
                if nova_senha and nova_senha == confirmar_senha:
                    c.execute("UPDATE alunos SET senha =? WHERE id =?", (hash_senha(nova_senha), usuario[0]))
                    conn.commit()
                    st.session_state.forcar_troca_senha = False
                    st.success("SENHA ALTERADA! FAÇA LOGIN NOVAMENTE.")
                    st.session_state.usuario = None
                    st.session_state.pagina = 'home'
                    st.rerun()
                else:
                    st.error("SENHAS NÃO CONFEREM!")
        conn.close()
        st.stop()

    st.markdown('<div class="section-title">PAINEL DO ALUNO</div>', unsafe_allow_html=True)
    aba = st.radio("", ["MEU PERFIL", "PROGRESSÃO", "LOJA", "MEUS PEDIDOS"], horizontal=True)

    if aba == "MEU PERFIL":
        st.markdown('<div class="section-title">MEU PERFIL</div>', unsafe_allow_html=True)
        col1, col2 = st.columns([1,3])
        with col1:
            if usuario[11]:
                st.image(usuario[11], width=150)
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
            <div style="padding:30px 0;">
                <div style="font-family:'Playfair Display'; font-size:40px; color:#32FF7E; text-shadow: 0 0 10px #32FF7E;">{usuario[1]}</div>
                <div style="font-family:'Montserrat'; color:#ccc; margin:15px 0;">{usuario[2]} | {usuario[4]}</div>
                <div style="font-family:'Montserrat'; color:#32FF7E; font-weight:700; font-size:16px;">GRADUAÇÃO: {usuario[7]}</div>
                <div style="font-family:'Montserrat'; color:#ccc; font-size:16px;">STATUS MENSALIDADE: {'ATIVA' if usuario[8] else 'INATIVA'}</div>
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
                    st.checkbox(item[3], key=f"prog_aluno_{item[0]}", disabled=True)
            else:
                st.info(f"NENHUM {tipo} CADASTRADO PARA {grad_atual}")

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
            <div style="padding:30px 0; border-bottom:1px solid #333;">
                <div style="font-family:'Playfair Display'; font-size:32px; color:#32FF7E; text-shadow: 0 0 10px #32FF7E;">{prod[1]}</div>
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
            if st.button("FINALIZAR PEDIDO", use_container_width=True):
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
            <div style="padding:30px 0; border-bottom:1px solid #333;">
                <div style="font-family:'Playfair Display'; font-size:32px; color:#32FF7E; text-shadow: 0 0 10px #32FF7E;">PEDIDO #{pedido[0]}</div>
                <div style="font-family:'Montserrat'; color:#ccc;">R$ {pedido[3]:.2f} | {pedido[4].upper()} | {pedido[2]}</div>
            </div>
            """, unsafe_allow_html=True)
            c.execute("""SELECT pr.nome, ip.quantidade, ip.preco_unitario
                         FROM itens_pedido ip JOIN produtos pr ON ip.produto_id = pr.id
                         WHERE ip.pedido_id =?""", (pedido[0],))
            for item in c.fetchall():
                st.write(f'- {item[1]}x {item[0]} - R$ {item[2]:.2f}')

    if st.button("SAIR", use_container_width=True):
        st.session_state.usuario = None
        st.session_state.pagina = 'home'
        st.rerun()
    conn.close()
