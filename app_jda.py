import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, get_app, _apps, storage
from datetime import datetime
import hashlib
import pandas as pd

st.set_page_config(layout="wide", page_title="JDA PIÇARRAS - Painel Mestre", initial_sidebar_state="expanded")

# === INICIALIZAÇÃO DO FIREBASE COM ARQUIVO JSON ===
@st.cache_resource
def init_firebase():
    try:
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred, {
            'storageBucket': 'jda-picarras1.appspot.com'
        })
        return firestore.client()
    except Exception as e:
        st.error(f"ERRO FIREBASE DETALHADO: {e}")
        st.stop()

db = init_firebase()

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def obter_horarios():
    doc = db.collection('config').document('horarios').get()
    return doc.to_dict().get('lista', []) if doc.exists else []

def salvar_horarios(lista_horarios):
    db.collection('config').document('horarios').set({'lista': lista_horarios})
    return True

def deletar_horario(index):
    horarios = obter_horarios()
    if 0 <= index < len(horarios):
        horarios.pop(index)
        salvar_horarios(horarios)
    return True

def obter_produtos_loja():
    doc = db.collection('config').document('loja').get()
    return doc.to_dict().get('produtos', []) if doc.exists else []

def salvar_produtos_loja(lista_produtos):
    db.collection('config').document('loja').set({'produtos': lista_produtos})
    return True

def deletar_produto(index):
    produtos = obter_produtos_loja()
    if 0 <= index < len(produtos):
        produtos.pop(index)
        salvar_produtos_loja(produtos)
    return True

def obter_golpes_por_graduacao(graduacao):
    doc = db.collection('golpes').document(graduacao).get()
    if doc.exists:
        return doc.to_dict().get('golpes', [])
    return []

def salvar_golpes_por_graduacao(graduacao, lista_golpes):
    db.collection('golpes').document(graduacao).set({'golpes': lista_golpes})
    return True

def deletar_golpe(graduacao, index):
    golpes = obter_golpes_por_graduacao(graduacao)
    if 0 <= index < len(golpes):
        golpes.pop(index)
        salvar_golpes_por_graduacao(graduacao, golpes)
    return True

def obter_taxa_cadastro():
    doc = db.collection('config').document('taxa_cadastro').get()
    return doc.to_dict().get('valor', 50) if doc.exists else 50

def obter_chave_pix():
    doc = db.collection('config').document('chave_pix').get()
    return doc.to_dict().get('valor', 'jda@pix.com.br') if doc.exists else 'jda@pix.com.br'

def cadastrar_aluno(nome, email, graduacao, telefone, paga_mensalidade, taxa_cadastro_paga):
    senha_temp = hash_senha("123456")
    aluno_data = {
        'nome': nome,
        'email': email,
        'senha': senha_temp,
        'graduacao': graduacao,
        'telefone': telefone,
        'paga_mensalidade': paga_mensalidade,
        'taxa_cadastro_paga': taxa_cadastro_paga,
        'role': 'aluno',
        'status': 'pendente',
        'primeiro_acesso': True,
        'data_cadastro': datetime.now(),
        'progresso_golpes': {}
    }
    db.collection('alunos').document(email).set(aluno_data)
    return True

def aprovar_aluno(email):
    db.collection('alunos').document(email).update({'status': 'ativo'})
    return True

def deletar_aluno(email):
    db.collection('alunos').document(email).delete()
    return True

def login_aluno(email, senha):
    hash_senha_calc = hashlib.sha256(senha.encode()).hexdigest()
    doc = db.collection('alunos').document(email).get()

    if not doc.exists:
        st.error("Credenciais inválidas")
        return False

    dados = doc.to_dict()

    if dados.get('senha') == hash_senha_calc and dados.get('status') == 'ativo':
        st.session_state.logged_in = True
        st.session_state.user_data = dados
        if dados.get('primeiro_acesso', False):
            st.session_state.must_change_password = True
        st.rerun()
        return True
    else:
        st.error("Credenciais inválidas ou usuário inativo")
        return False

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 12 GRADUAÇÕES DE CAPOEIRA
GRADUACOES_CAPOEIRA = [
    "Crua", "Crua 1º Cordão", "Crua 2º Cordão",
    "Amarela", "Amarela 1º Cordão", "Amarela 2º Cordão",
    "Laranja", "Laranja 1º Cordão", "Laranja 2º Cordão",
    "Azul", "Azul 1º Cordão", "Azul 2º Cordão",
    "Verde", "Verde 1º Cordão", "Verde 2º Cordão",
    "Roxa", "Roxa 1º Cordão", "Roxa 2º Cordão",
    "Marrom", "Marrom 1º Cordão", "Marrom 2º Cordão",
    "Preta", "Preta 1º Cordão", "Preta 2º Cordão",
    "Preta 3º Cordão", "Preta 4º Cordão", "Mestre"
]

# ESTADO DA SESSÃO - SIDEBAR ABERTA NO PC, FECHADA NO MOBILE
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'show_admin' not in st.session_state:
    st.session_state.show_admin = False
if 'show_student_portal' not in st.session_state:
    st.session_state.show_student_portal = False
if 'must_change_password' not in st.session_state:
    st.session_state.must_change_password = False
if 'show_cadastro' not in st.session_state:
    st.session_state.show_cadastro = False
if 'admin_page' not in st.session_state:
    st.session_state.admin_page = "Dashboard"
if 'edit_index' not in st.session_state:
    st.session_state.edit_index = None
if 'edit_type' not in st.session_state:
    st.session_state.edit_type = None
if 'sidebar_visible' not in st.session_state:
    st.session_state.sidebar_visible = True

# CSS ESTILIZADO
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

header, #MainMenu, footer {visibility: hidden!important;}
.stApp {background: #0a0a0a!important; font-family: 'Inter', sans-serif!important;}

/* BOTÃO TOGGLE SIDEBAR */
.sidebar-toggle {
    position: fixed;
    top: 20px;
    left: 20px;
    z-index: 9999;
    background: #000!important;
    border: 2px solid #00ff88!important;
    color: #00ff88!important;
    padding: 8px 15px!important;
    border-radius: 4px!important;
    font-weight: 600!important;
    letter-spacing: 1px!important;
    cursor: pointer!important;
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: #0f0f0f!important;
    border-right: 1px solid rgba(0, 255, 136, 0.3)!important;
    padding: 30px 20px!important;
}

/* PÁGINA INICIAL */
.title-cardinal {
    font-family: 'Playfair Display', serif!important;
    font-size: 72px!important;
    font-weight: 800!important;
    text-align: center!important;
    background: linear-gradient(135deg, #00ff88 0%, #00cc6a 50%, #00ff88 100%)!important;
    -webkit-background-clip: text!important;
    -webkit-text-fill-color: transparent!important;
    background-clip: text!important;
    letter-spacing: 4px!important;
    text-transform: uppercase!important;
    margin: 100px 0 20px 0!important;
    text-shadow: 0 0 40px rgba(0, 255, 136, 0.3)!important;
}

.subtitle-cardinal {
    font-family: 'Inter', sans-serif!important;
    font-size: 16px!important;
    color: rgba(255, 255, 255, 0.7)!important;
    text-align: center!important;
    letter-spacing: 3px!important;
    text-transform: uppercase!important;
    margin: 0 0 60px 0!important;
}

.horario-titulo {
    font-family: 'Playfair Display', serif!important;
    font-size: 36px!important;
    color: #00ff88!important;
    text-align: center!important;
    letter-spacing: 2px!important;
    text-transform: uppercase!important;
    margin: 80px 0 30px 0!important;
    text-shadow: 0 0 20px rgba(0, 255, 136, 0.4)!important;
}

.horario-item {
    font-family: 'Inter', sans-serif!important;
    font-size: 18px!important;
    color: #00ff88!important;
    text-align: center!important;
    letter-spacing: 1.5px!important;
    margin: 15px 0!important;
    text-shadow: 0 0 10px rgba(0, 255, 136, 0.3)!important;
}

/* CARDS */
.admin-card {
    background: rgba(0, 255, 136, 0.03)!important;
    border: 1px solid rgba(0, 255, 136, 0.2)!important;
    padding: 40px 35px!important;
    margin: 30px 0!important;
    border-radius: 8px!important;
}

.admin-title {
    font-family: 'Playfair Display', serif!important;
    font-size: 42px!important;
    font-weight: 700!important;
    color: #00ff88!important;
    letter-spacing: 2px!important;
    text-transform: uppercase!important;
    margin: 0 0 15px 0!important;
}

.admin-subtitle {
    font-family: 'Inter', sans-serif!important;
    font-size: 14px!important;
    color: rgba(255, 255, 255, 0.6)!important;
    letter-spacing: 1.5px!important;
    margin: 0 0 40px 0!important;
}

.section-title {
    font-family: 'Playfair Display', serif!important;
    font-size: 28px!important;
    color: #00ff88!important;
    letter-spacing: 2px!important;
    text-transform: uppercase!important;
    margin: 0 0 25px 0!important;
}

/* BOTÕES */
[data-testid="stButton"] > button {
    background: #000!important;
    border: 2px solid #00ff88!important;
    color: #00ff88!important;
    font-family: 'Inter', sans-serif!important;
    font-size: 13px!important;
    font-weight: 600!important;
    letter-spacing: 2px!important;
    text-transform: uppercase!important;
    padding: 12px 25px!important;
    border-radius: 4px!important;
    transition: all 0.3s ease!important;
}

[data-testid="stButton"] > button:hover {
    background: #00ff88!important;
    color: #000!important;
    transform: translateY(-2px)!important;
    box-shadow: 0 8px 20px rgba(0, 255, 136, 0.3)!important;
}

/* INPUTS */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div > select,
.stTextArea > div > div > textarea {
    background: #1a1a1a!important;
    border: 1px solid rgba(0, 255, 136, 0.3)!important;
    color: #ffffff!important;
    border-radius: 4px!important;
    font-family: 'Inter', sans-serif!important;
}

.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border: 1px solid #00ff88!important;
    box-shadow: 0 0 0 2px rgba(0, 255, 136, 0.2)!important;
}

/* MÉTRICAS */
[data-testid="stMetricValue"] {
    font-family: 'Playfair Display', serif!important;
    font-size: 48px!important;
    color: #00ff88!important;
}

[data-testid="stMetricLabel"] {
    font-family: 'Inter', sans-serif!important;
    font-size: 12px!important;
    color: rgba(255, 255, 255, 0.5)!important;
    letter-spacing: 2px!important;
    text-transform: uppercase!important;
}

/* ITEM LIST */
.item-list {
    background: #1a1a1a!important;
    border: 1px solid rgba(0, 255, 136, 0.15)!important;
    padding: 20px 25px!important;
    margin: 12px 0!important;
    border-radius: 4px!important;
}

/* RESPONSIVO MOBILE */
@media (max-width: 768px) {
.title-cardinal {font-size: 48px!important; margin: 60px 0 15px 0!important;}
.horario-titulo {font-size: 28px!important; margin: 50px 0 20px 0!important;}
.horario-item {font-size: 16px!important;}
.sidebar-toggle {
    position: fixed!important;
    top: 15px!important;
    left: 15px!important;
    z-index: 9999!important;
}
</style>
""", unsafe_allow_html=True)# BOTÃO TOGGLE SIDEBAR - VISÍVEL SEMPRE NO ADMIN
if st.session_state.logged_in and st.session_state.user_data.get('role') == 'admin':
    if st.button("☰ MENU", key="sidebar_toggle", help="Abrir/Fechar menu"):
        st.session_state.sidebar_visible = not st.session_state.sidebar_visible

# TELA INICIAL PÚBLICA
if not st.session_state.logged_in and not st.session_state.show_admin and not st.session_state.show_student_portal and not st.session_state.show_cadastro:

    # CONTAINER CENTRALIZADO
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<h1 class="title-cardinal">JDA PIÇARRAS</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle-cardinal">Tradição, disciplina e cultura em cada movimento</p>', unsafe_allow_html=True)

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("PORTAL DO ALUNO", key="btn_aluno", use_container_width=True):
                st.session_state.show_student_portal = True
                st.rerun()
        with col_btn2:
            if st.button("SE INSCREVER", key="btn_cadastro", use_container_width=True):
                st.session_state.show_cadastro = True
                st.rerun()

        # HORÁRIO DE TREINOS CENTRALIZADO E VERDE NEON
        st.markdown('<h2 class="horario-titulo">Horário de Treinos</h2>', unsafe_allow_html=True)
        horarios = obter_horarios()
        if horarios:
            for h in horarios:
                st.markdown(f'<p class="horario-item"><strong>{h["dia"]}</strong> — {h["horario"]}</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="horario-item">Nenhum horário cadastrado</p>', unsafe_allow_html=True)

# LOGIN ADMIN
elif st.session_state.show_admin and not st.session_state.logged_in:
    st.markdown('<div style="max-width:500px;margin:100px auto;padding:60px 50px;">', unsafe_allow_html=True)
    st.markdown('<h1 class="admin-title">Painel do Mestre</h1>', unsafe_allow_html=True)
    st.markdown('<p class="admin-subtitle">Acesso Restrito</p>', unsafe_allow_html=True)

    with st.form("admin_login_form"):
        email = st.text_input("Email Admin")
        senha = st.text_input("Senha Admin", type="password")
        submitted = st.form_submit_button("ENTRAR", use_container_width=True)
        if submitted:
            login_aluno(email, senha)

    if st.button("VOLTAR", use_container_width=True):
        st.session_state.show_admin = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# PAINEL ADMIN LOGADO
elif st.session_state.logged_in and not st.session_state.must_change_password and st.session_state.user_data.get('role') == 'admin':

    # SIDEBAR CONDICIONAL - ABERTA NO PC, FECHADA NO MOBILE
    if st.session_state.sidebar_visible:
        with st.sidebar:
            st.title("PAINEL MESTRE")
            menu_opcoes = [
                "📊 Dashboard",
                "⏰ Horários",
                "🛍️ Loja",
                "🥋 Golpes",
                "👥 Alunos",
                "⚙️ Configurações"
            ]
            st.session_state.admin_page = st.radio("Navegação", menu_opcoes, index=0)
            st.divider()
            if st.button("🚪 SAIR", use_container_width=True):
                logout()
    else:
        # Sidebar fechada - espaço vazio
        pass

    # HEADER DO PAINEL
    pagina_atual = st.session_state.admin_page.split(' ', 1)[1] if ' in st.session_state.admin_page' else st.session_state.admin_page
    st.markdown(f'<h1 class="admin-title">{pagina_atual}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="admin-subtitle">Bem-vindo, {st.session_state.user_data["nome"]}</p>', unsafe_allow_html=True)

    # DASHBOARD
    if st.session_state.admin_page == "📊 Dashboard":
        alunos = list(db.collection('alunos').stream())
        total_alunos = len([a for a in alunos if a.to_dict().get('role') == 'aluno'])
        alunos_ativos = len([a for a in alunos if a.to_dict().get('status') == 'ativo'])
        alunos_pendentes = len([a for a in alunos if a.to_dict().get('status') == 'pendente'])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="admin-card" style="text-align:center;">', unsafe_allow_html=True)
            st.metric("Total Capoeiristas", total_alunos)
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="admin-card" style="text-align:center;">', unsafe_allow_html=True)
            st.metric("Alunos Ativos", alunos_ativos)
            st.markdown('</div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="admin-card" style="text-align:center;">', unsafe_allow_html=True)
            st.metric("Pendentes", alunos_pendentes)
            st.markdown('</div>', unsafe_allow_html=True)

    # HORÁRIOS - ADICIONAR + LISTA + EDITAR + EXCLUIR
    elif st.session_state.admin_page == "⏰ Horários":
        st.markdown('<div class="admin-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-title">Gerenciar Horários</h3>', unsafe_allow_html=True)

        # FORM ADICIONAR/EDITAR
        if st.session_state.edit_type == "horario" and st.session_state.edit_index is not None:
            horarios = obter_horarios()
            horario_edit = horarios[st.session_state.edit_index]
            with st.form("form_edit_horario"):
                st.write("**Editando Horário**")
                dia = st.text_input("Dia", value=horario_edit["dia"])
                horario = st.text_input("Horário", value=horario_edit["horario"])
                col1, col2 = st.columns(2)
                if col1.form_submit_button("ATUALIZAR", use_container_width=True):
                    horarios[st.session_state.edit_index] = {"dia": dia, "horario": horario}
                    salvar_horarios(horarios)
                    st.session_state.edit_index = None
                    st.session_state.edit_type = None
                    st.success("Horário atualizado!")
                    st.rerun()
                if col2.form_submit_button("CANCELAR", use_container_width=True):
                    st.session_state.edit_index = None
                    st.session_state.edit_type = None
                    st.rerun()
        else:
            with st.form("form_add_horario"):
                st.write("**Adicionar Novo Horário**")
                col1, col2 = st.columns(2)
                dia = col1.text_input("Dia da Semana", placeholder="Ex: Segunda / Quarta / Sexta")
                horario = col2.text_input("Horário", placeholder="Ex: 19:00 - 21:00")
                if st.form_submit_button("ADICIONAR HORÁRIO", use_container_width=True):
                    if dia and horario:
                        horarios = obter_horarios()
                        horarios.append({"dia": dia, "horario": horario})
                        salvar_horarios(horarios)
                        st.success("Horário adicionado!")
                        st.rerun()
                    else:
                        st.error("Preencha todos os campos")

        # LISTA DE HORÁRIOS
        st.markdown('<h3 class="section-title" style="font-size:24px;margin:50px 0 20px 0;">Horários Cadastrados</h3>', unsafe_allow_html=True)
        horarios = obter_horarios()
        if horarios:
            for i, h in enumerate(horarios):
                st.markdown(f'<div class="item-list">', unsafe_allow_html=True)
                col1, col2, col3 = st.columns([4,1,1])
                col1.markdown(f"**{h['dia']}** — {h['horario']}")
                if col2.button("EDITAR", key=f"edit_hor_{i}"):
                    st.session_state.edit_index = i
                    st.session_state.edit_type = "horario"
                    st.rerun()
                if col3.button("EXCLUIR", key=f"del_hor_{i}"):
                    deletar_horario(i)
                    st.success("Horário excluído!")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Nenhum horário cadastrado")
        st.markdown("</div>", unsafe_allow_html=True)

    # LOJA - ADICIONAR + LISTA + EDITAR + EXCLUIR
    elif st.session_state.admin_page == "🛍️ Loja":
        st.markdown('<div class="admin-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-title">Gerenciar Produtos</h3>', unsafe_allow_html=True)

        # FORM ADICIONAR/EDITAR
        if st.session_state.edit_type == "produto" and st.session_state.edit_index is not None:
            produtos = obter_produtos_loja()
            produto_edit = produtos[st.session_state.edit_index]
            with st.form("form_edit_produto"):
                st.write("**Editando Produto**")
                nome = st.text_input("Nome do Produto", value=produto_edit["nome"])
                preco = st.number_input("Preço R$", value=float(produto_edit["preco"]))
                desc = st.text_input("Descrição", value=produto_edit["descricao"])
                col1, col2 = st.columns(2)
                if col1.form_submit_button("ATUALIZAR", use_container_width=True):
                    produtos[st.session_state.edit_index] = {"nome": nome, "preco": preco, "descricao": desc}
                    salvar_produtos_loja(produtos)
                    st.session_state.edit_index = None
                    st.session_state.edit_type = None
                    st.success("Produto atualizado!")
                    st.rerun()
                if col2.form_submit_button("CANCELAR", use_container_width=True):
                    st.session_state.edit_index = None
                    st.session_state.edit_type = None
                    st.rerun()
        else:
            with st.form("form_add_produto"):
                st.write("**Adicionar Novo Produto**")
                col1, col2, col3 = st.columns(3)
                nome = col1.text_input("Nome do Produto", placeholder="Ex: Camiseta JDA")
                preco = col2.number_input("Preço R$", min_value=0.0, step=5.0)
                desc = col3.text_input("Descrição", placeholder="Ex: Camiseta oficial")
                if st.form_submit_button("ADICIONAR PRODUTO", use_container_width=True):
                    if nome and preco > 0:
                        produtos = obter_produtos_loja()
                        produtos.append({"nome": nome, "preco": preco, "descricao": desc})
                        salvar_produtos_loja(produtos)
                        st.success("Produto adicionado!")
                        st.rerun()
                    else:
                        st.error("Preencha nome e preço")

        # LISTA DE PRODUTOS
        st.markdown('<h3 class="section-title" style="font-size:24px;margin:50px 0 20px 0;">Produtos Cadastrados</h3>', unsafe_allow_html=True)
        produtos = obter_produtos_loja()
        if produtos:
            for i, p in enumerate(produtos):
                st.markdown(f'<div class="item-list">', unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns([3,2,3,2])
                col1.markdown(f"**{p['nome']}**")
                col2.markdown(f"R$ {p['preco']:.2f}")
                col3.markdown(f"{p['descricao']}")
                if col4.button("EDITAR", key=f"edit_prod_{i}"):
                    st.session_state.edit_index = i
                    st.session_state.edit_type = "produto"
                    st.rerun()
                if col4.button("EXCLUIR", key=f"del_prod_{i}"):
                    deletar_produto(i)
                    st.success("Produto excluído!")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Nenhum produto cadastrado")
        st.markdown("</div>", unsafe_allow_html=True)

    # GOLPES - ADICIONAR + LISTA + EDITAR + EXCLUIR
    elif st.session_state.admin_page == "🥋 Golpes":
        st.markdown('<div class="admin-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-title">Gerenciar Golpes por Graduação</h3>', unsafe_allow_html=True)

        graduacao_selecionada = st.selectbox("Selecione a Graduação", GRADUACOES_CAPOEIRA, key="select_grad_golpes")

        # FORM ADICIONAR/EDITAR GOLPE
        if st.session_state.edit_type == "golpe" and st.session_state.edit_index is not None:
            golpes = obter_golpes_por_graduacao(graduacao_selecionada)
            golpe_edit = golpes[st.session_state.edit_index]
            with st.form("form_edit_golpe"):
                st.write(f"**Editando Golpe {st.session_state.edit_index + 1} - {graduacao_selecionada}**")
                nome = st.text_input("Nome do Golpe", value=golpe_edit["nome"])
                desc = st.text_input("Descrição", value=golpe_edit["descricao"])
                col1, col2 = st.columns(2)
                if col1.form_submit_button("ATUALIZAR", use_container_width=True):
                    golpes[st.session_state.edit_index] = {"nome": nome, "descricao": desc}
                    salvar_golpes_por_graduacao(graduacao_selecionada, golpes)
                    st.session_state.edit_index = None
                    st.session_state.edit_type = None
                    st.success("Golpe atualizado!")
                    st.rerun()
                if col2.form_submit_button("CANCELAR", use_container_width=True):
                    st.session_state.edit_index = None
                    st.session_state.edit_type = None
                    st.rerun()
        else:
            with st.form("form_add_golpe"):
                st.write(f"**Adicionar Novo Golpe - {graduacao_selecionada}**")
                col1, col2 = st.columns(2)
                nome = col1.text_input("Nome do Golpe", placeholder="Ex: Meia Lua de Compasso")
                desc = col2.text_input("Descrição", placeholder="Ex: Golpe circular de perna")
                if st.form_submit_button("ADICIONAR GOLPE", use_container_width=True):
                    if nome:
                        golpes = obter_golpes_por_graduacao(graduacao_selecionada)
                        golpes.append({"nome": nome, "descricao": desc})
                        salvar_golpes_por_graduacao(graduacao_selecionada, golpes)
                        st.success("Golpe adicionado!")
                        st.rerun()
                    else:
                        st.error("Preencha o nome do golpe")

        # LISTA DE GOLPES
        st.markdown(f'<h3 class="section-title" style="font-size:24px;margin:50px 0 20px 0;">Golpes - {graduacao_selecionada}</h3>', unsafe_allow_html=True)
        golpes = obter_golpes_por_graduacao(graduacao_selecionada)
        if golpes:
            for i, g in enumerate(golpes):
                st.markdown(f'<div class="item-list">', unsafe_allow_html=True)
                col1, col2, col3 = st.columns([5,1,1])
                col1.markdown(f"**{i+1}. {g['nome']}** — {g['descricao']}")
                if col2.button("EDITAR", key=f"edit_golpe_{i}"):
                    st.session_state.edit_index = i
                    st.session_state.edit_type = "golpe"
                    st.rerun()
                if col3.button("EXCLUIR", key=f"del_golpe_{i}"):
                    deletar_golpe(graduacao_selecionada, i)
                    st.success("Golpe excluído!")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Nenhum golpe cadastrado para esta graduação")
        st.markdown("</div>", unsafe_allow_html=True)

    # ALUNOS - LISTA + APROVAR + EXCLUIR
    elif st.session_state.admin_page == "👥 Alunos":
        st.markdown('<div class="admin-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-title">Gerenciar Alunos</h3>', unsafe_allow_html=True)

        alunos = list(db.collection('alunos').stream())
        alunos_lista = []
        for aluno in alunos:
            dados = aluno.to_dict()
            dados['id'] = aluno.id
            if dados.get('role') == 'aluno':
                alunos_lista.append(dados)

        if alunos_lista:
            df = pd.DataFrame(alunos_lista)
            st.dataframe(df[['nome', 'email', 'graduacao', 'status', 'telefone']], use_container_width=True)

            st.markdown('<h3 class="section-title" style="font-size:24px;margin:50px 0 20px 0;">Alunos Pendentes</h3>', unsafe_allow_html=True)
            pendentes = [a for a in alunos_lista if a['status'] == 'pendente']
            if pendentes:
                for aluno in pendentes:
                    st.markdown(f'<div class="item-list">', unsafe_allow_html=True)
                    col1, col2, col3 = st.columns([4,1,1])
                    col1.markdown(f"**{aluno['nome']}** — {aluno['graduacao']}<br>{aluno['email']}")
                    if col2.button("APROVAR", key=f"aprov_{aluno['email']}"):
                        aprovar_aluno(aluno['email'])
                        st.success(f"{aluno['nome']} aprovado!")
                        st.rerun()
                    if col3.button("EXCLUIR", key=f"del_aluno_{aluno['email']}"):
                        deletar_aluno(aluno['email'])
                        st.success(f"{aluno['nome']} excluído!")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("Nenhum aluno pendente")
        else:
            st.info("Nenhum capoeirista cadastrado")
        st.markdown("</div>", unsafe_allow_html=True)

    # CONFIGURAÇÕES
    elif st.session_state.admin_page == "⚙️ Configurações":
        st.markdown('<div class="admin-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-title">Configurações Gerais</h3>', unsafe_allow_html=True)

        with st.form("config_form"):
            nova_taxa = st.number_input("Taxa de Cadastro R$", value=float(obter_taxa_cadastro()))
            nova_chave_pix = st.text_input("Chave PIX", value=obter_chave_pix())
            if st.form_submit_button("SALVAR CONFIGURAÇÕES", use_container_width=True):
                db.collection('config').document('taxa_cadastro').set({'valor': nova_taxa})
                db.collection('config').document('chave_pix').set({'valor': nova_chave_pix})
                st.success("Configurações salvas com sucesso!")
        st.markdown("</div>", unsafe_allow_html=True)

# PORTAL DO ALUNO
elif st.session_state.logged_in and not st.session_state.must_change_password and st.session_state.user_data.get('role') == 'aluno':
    st.markdown(f'<h1 class="admin-title">{st.session_state.user_data["nome"]}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="admin-subtitle">Graduação: {st.session_state.user_data["graduacao"]}</p>', unsafe_allow_html=True)

    st.markdown('<div class="admin-card">', unsafe_allow_html=True)
    st.markdown('<h3 class="section-title">Meus Golpes - Marcar Progresso</h3>', unsafe_allow_html=True)

    golpes = obter_golpes_por_graduacao(st.session_state.user_data["graduacao"])
    progresso = st.session_state.user_data.get('progresso_golpes', {}).get(st.session_state.user_data["graduacao"], [False] * 25)

    with st.form("form_progresso"):
        for i, golpe in enumerate(golpes):
            checked = st.checkbox(f"{golpe['nome']} - {golpe['descricao']}", value=progresso[i] if i < len(progresso) else False, key=f"prog_{i}")
            if i < len(progresso):
                progresso[i] = checked

        if st.form_submit_button("SALVAR PROGRESSO", use_container_width=True):
            db.collection('alunos').document(st.session_state.user_data['email']).update({
                f'progresso_golpes.{st.session_state.user_data["graduacao"]}': progresso
            })
            st.success("Progresso salvo!")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("SAIR", use_container_width=True):
        logout()

# TROCA DE SENHA OBRIGATÓRIA
elif st.session_state.must_change_password:
    st.markdown('<div style="max-width:600px;margin:100px auto;padding:60px 50px;">', unsafe_allow_html=True)
    st.markdown('<h1 class="admin-title">Primeiro Acesso</h1>', unsafe_allow_html=True)
    st.markdown('<p class="admin-subtitle">Defina sua senha de segurança</p>', unsafe_allow_html=True)

    with st.form("trocar_senha_form"):
        senha_atual = st.text_input("Senha Atual", type="password")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar_senha = st.text_input("Confirmar Nova Senha", type="password")
        submitted = st.form_submit_button("CONFIRMAR", use_container_width=True)

        if submitted:
            if nova_senha!= confirmar_senha:
                st.error("As senhas não coincidem")
            elif len(nova_senha) < 6:
                st.error("Mínimo 6 caracteres")
            else:
                hash_atual = hashlib.sha256(senha_atual.encode()).hexdigest()
                doc = db.collection('alunos').document(st.session_state.user_data['email']).get()
                if doc.exists and doc.to_dict().get('senha') == hash_atual:
                    novo_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
                    db.collection('alunos').document(st.session_state.user_data['email']).update({
                        'senha': novo_hash,
                        'primeiro_acesso': False
                    })
                    st.session_state.must_change_password = False
                    st.success("Senha alterada com sucesso!")
                    st.rerun()
                else:
                    st.error("Senha atual incorreta")
    st.markdown('</div>', unsafe_allow_html=True)

# CADASTRO PÚBLICO
elif st.session_state.show_cadastro:
    st.markdown('<div style="max-width:700px;margin:80px auto;padding:60px 50px;">', unsafe_allow_html=True)
    st.markdown('<h1 class="admin-title">Inscrição JDA Piçarras</h1>', unsafe_allow_html=True)
    st.markdown('<p class="admin-subtitle">Junte-se à roda da JDA Piçarras</p>', unsafe_allow_html=True)

    with st.form("cadastro_form"):
        nome = st.text_input("Nome Completo")
        email = st.text_input("Email")
        telefone = st.text_input("Telefone")
        graduacao = st.selectbox("Graduação Atual", GRADUACOES_CAPOEIRA)

        st.markdown('<div class="admin-card">', unsafe_allow_html=True)
        st.markdown(f'<h4 style="color:#00ff88;font-family:Playfair Display;font-size:32px;text-align:center;margin:0;">R$ {obter_taxa_cadastro():.2f}</h4>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:rgba(255,255,255,0.6);text-align:center;font-size:12px;letter-spacing:2px;">TAXA DE CADASTRO • PIX: {obter_chave_pix()}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        taxa_paga = st.checkbox("Taxa de cadastro paga via PIX")
        mensalidade_paga = st.checkbox("Mensalidade paga")

        submitted = st.form_submit_button("FINALIZAR INSCRIÇÃO", use_container_width=True)
        if submitted:
            if nome and email and telefone:
                cadastrar_aluno(nome, email, graduacao, telefone, 1 if mensalidade_paga else 0, 1 if taxa_paga else 0)
                st.success("Inscrição realizada! Axé! Aguarde aprovação do mestre.")
                st.session_state.show_cadastro = False
                st.rerun()
            else:
                st.error("Preencha todos os campos")

    if st.button("VOLTAR", use_container_width=True):
        st.session_state.show_cadastro = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# LOGIN ALUNO
elif st.session_state.show_student_portal and not st.session_state.logged_in:
    st.markdown('<div style="max-width:500px;margin:100px auto;padding:60px 50px;">', unsafe_allow_html=True)
    st.markdown('<h1 class="admin-title">Portal do Capoeirista</h1>', unsafe_allow_html=True)
    st.markdown('<p class="admin-subtitle">Área do Aluno</p>', unsafe_allow_html=True)

    with st.form("login_form_aluno"):
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("ENTRAR", use_container_width=True)
        if submitted:
            login_aluno(email, senha)

    if st.button("VOLTAR", use_container_width=True):
        st.session_state.show_student_portal = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
