import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, get_app, _apps, storage
from datetime import datetime
import hashlib
import pandas as pd

st.set_page_config(layout="wide", page_title="JDA PIÇARRAS - Painel Mestre", initial_sidebar_state="expanded")

# Inicialização do Firebase
if not _apps:
    try:
        cred = credentials.Certificate(dict(st.secrets['firebase_credentials']))
        firebase_admin.initialize_app(cred, {'storageBucket': 'jda-picarras1.appspot.com'})
    except Exception as e:
        st.error(f"ERRO FIREBASE: {e}")
        st.stop()
else:
    app = get_app()

db = firestore.client()

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def obter_taxa_cadastro():
    doc = db.collection('config').document('taxa_cadastro').get()
    return doc.to_dict().get('valor', 50) if doc.exists else 50

def obter_chave_pix():
    doc = db.collection('config').document('chave_pix').get()
    return doc.to_dict().get('valor', 'jda@pix.com.br') if doc.exists else 'jda@pix.com.br'

def obter_horarios():
    doc = db.collection('config').document('horarios').get()
    return doc.to_dict().get('lista', [
        {"dia": "Segunda / Quarta / Sexta", "horario": "19:00 - 21:00"},
        {"dia": "Sábado", "horario": "14:00 - 17:00"},
        {"dia": "Roda Mensal", "horario": "Último Sábado - 16:00"}
    ]) if doc.exists else []

def salvar_horarios(lista_horarios):
    db.collection('config').document('horarios').set({'lista': lista_horarios})
    return True

def obter_produtos_loja():
    doc = db.collection('config').document('loja').get()
    return doc.to_dict().get('produtos', [
        {"nome": "Camiseta JDA", "preco": 45.00, "descricao": "Camiseta oficial JDA Piçarras"}
    ]) if doc.exists else []

def salvar_produtos_loja(lista_produtos):
    db.collection('config').document('loja').set({'produtos': lista_produtos})
    return True

def obter_golpes_por_graduacao(graduacao):
    doc = db.collection('golpes').document(graduacao).get()
    if doc.exists:
        return doc.to_dict().get('golpes', [])
    return [{"nome": f"Golpe {i+1}", "descricao": ""} for i in range(25)]

def salvar_golpes_por_graduacao(graduacao, lista_golpes):
    db.collection('golpes').document(graduacao).set({'golpes': lista_golpes})
    return True

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

def login_aluno(email, senha):
    hash_senha = hashlib.sha256(senha.encode()).hexdigest()
    doc = db.collection('alunos').document(email).get()

    if not doc.exists:
        st.error("Credenciais inválidas")
        return False

    dados = doc.to_dict()

    if dados.get('senha') == hash_senha and dados.get('status') == 'ativo':
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

# Estado da sessão
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

# CSS ESTILIZADO PARA TODO O APP
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

header, #MainMenu, footer {visibility: hidden!important;}

.stApp {
    background: #0a0a0a!important;
    font-family: 'Inter', sans-serif!important;
}

/* SIDEBAR ESTILIZADA */
[data-testid="stSidebar"] {
    background: #0f0f0f!important;
    border-right: 1px solid rgba(0, 255, 136, 0.3)!important;
    padding: 30px 20px!important;
}

[data-testid="stSidebar"].stTitle {
    font-family: 'Playfair Display', serif!important;
    color: #00ff88!important;
    font-size: 28px!important;
    letter-spacing: 2px!important;
    text-transform: uppercase!important;
    margin-bottom: 30px!important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    font-family: 'Inter', sans-serif!important;
    color: rgba(255, 255, 255, 0.8)!important;
    font-size: 14px!important;
    letter-spacing: 1.5px!important;
    text-transform: uppercase!important;
    padding: 12px 0!important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    color: #00ff88!important;
}

/* CARDS E TÍTULOS */
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
    padding: 15px 30px!important;
    border-radius: 4px!important;
    transition: all 0.3s ease!important;
}

[data-testid="stButton"] > button:hover {
    background: #00ff88!important;
    color: #000!important;
    transform: translateY(-2px)!important;
    box-shadow: 0 8px 20px rgba(0, 255, 136, 0.3)!important;
}

/* INPUTS E FORMS */
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
.stNumberInput > div > div > input:focus,
.stSelectbox > div > div > select:focus {
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

/* DATAFRAME */
.stDataFrame {
    background: #1a1a1a!important;
    border: 1px solid rgba(0, 255, 136, 0.2)!important;
    border-radius: 4px!important;
}
</style>
""", unsafe_allow_html=True)# TELA INICIAL PÚBLICA
if not st.session_state.logged_in and not st.session_state.show_admin and not st.session_state.show_student_portal and not st.session_state.show_cadastro:

    st.markdown('<h1 class="title-cardinal">JDA PIÇARRAS</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle-cardinal">Tradição, disciplina e cultura em cada movimento</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("PORTAL DO ALUNO", key="btn_aluno", use_container_width=True):
            st.session_state.show_student_portal = True
            st.rerun()
    with col2:
        if st.button("SE INSCREVER", key="btn_cadastro", use_container_width=True):
            st.session_state.show_cadastro = True
            st.rerun()

    st.subheader("Horário de Treinos")
    horarios = obter_horarios()
    for h in horarios:
        st.write(f"**{h['dia']}** - {h['horario']}")

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

# PAINEL ADMIN LOGADO - ESTILIZADO
elif st.session_state.logged_in and not st.session_state.must_change_password and st.session_state.user_data.get('role') == 'admin':

    # SIDEBAR ESTILIZADA
    with st.sidebar:
        st.title("PAINEL MESTRE")
        st.session_state.admin_page = st.radio(
            "Navegação",
            ["Dashboard", "Horários", "Loja", "Golpes", "Alunos", "Configurações"]
        )
        st.divider()
        if st.button("SAIR", use_container_width=True):
            logout()

    # HEADER DO PAINEL
    st.markdown(f'<h1 class="admin-title">{st.session_state.admin_page}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="admin-subtitle">Bem-vindo, {st.session_state.user_data["nome"]}</p>', unsafe_allow_html=True)

    # DASHBOARD
    if st.session_state.admin_page == "Dashboard":
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

    # EDITAR HORÁRIOS
    elif st.session_state.admin_page == "Horários":
        st.markdown('<div class="admin-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-title">Editar Horários de Treino</h3>', unsafe_allow_html=True)

        horarios = obter_horarios()
        with st.form("form_horarios"):
            novos_horarios = []
            for i in range(3):
                dia_atual = horarios[i]["dia"] if i < len(horarios) else ""
                horario_atual = horarios[i]["horario"] if i < len(horarios) else ""
                col1, col2 = st.columns(2)
                dia = col1.text_input(f"Dia {i+1}", value=dia_atual)
                horario = col2.text_input(f"Horário {i+1}", value=horario_atual)
                novos_horarios.append({"dia": dia, "horario": horario})

            if st.form_submit_button("SALVAR HORÁRIOS", use_container_width=True):
                salvar_horarios(novos_horarios)
                st.success("Horários salvos com sucesso!")
        st.markdown("</div>", unsafe_allow_html=True)

    # EDITAR LOJA
    elif st.session_state.admin_page == "Loja":
        st.markdown('<div class="admin-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-title">Editar Produtos da Loja</h3>', unsafe_allow_html=True)

        produtos = obter_produtos_loja()
        with st.form("form_loja"):
            novos_produtos = []
            for i in range(4):
                nome_atual = produtos[i]["nome"] if i < len(produtos) else ""
                preco_atual = float(produtos[i]["preco"]) if i < len(produtos) else 0.0
                desc_atual = produtos[i]["descricao"] if i < len(produtos) else ""

                st.markdown(f"<h4 style='color:#ffffff;font-size:16px;margin:25px 0 15px 0;'>Produto {i+1}</h4>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                nome = col1.text_input(f"Nome", value=nome_atual, key=f"prod_nome_{i}")
                preco = col2.number_input(f"Preço R$", value=preco_atual, key=f"prod_preco_{i}")
                desc = col3.text_input(f"Descrição", value=desc_atual, key=f"prod_desc_{i}")
                novos_produtos.append({"nome": nome, "preco": preco, "descricao": desc})

            if st.form_submit_button("SALVAR PRODUTOS", use_container_width=True):
                salvar_produtos_loja(novos_produtos)
                st.success("Produtos salvos com sucesso!")
        st.markdown("</div>", unsafe_allow_html=True)

    # EDITAR GOLPES
    elif st.session_state.admin_page == "Golpes":
        st.markdown('<div class="admin-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-title">25 Golpes por Graduação</h3>', unsafe_allow_html=True)

        graduacao_selecionada = st.selectbox("Selecione a Graduação para Editar", GRADUACOES_CAPOEIRA)
        golpes = obter_golpes_por_graduacao(graduacao_selecionada)

        with st.form(f"form_golpes_{graduacao_selecionada}"):
            novos_golpes = []
            for i in range(25):
                nome_atual = golpes[i]["nome"] if i < len(golpes) else f"Golpe {i+1}"
                desc_atual = golpes[i]["descricao"] if i < len(golpes) else ""
                col1, col2 = st.columns([3,5])
                nome = col1.text_input(f"Golpe {i+1}", value=nome_atual, key=f"golpe_nome_{i}")
                desc = col2.text_input(f"Descrição", value=desc_atual, key=f"golpe_desc_{i}")
                novos_golpes.append({"nome": nome, "descricao": desc})

            if st.form_submit_button(f"SALVAR 25 GOLPES - {graduacao_selecionada}", use_container_width=True):
                salvar_golpes_por_graduacao(graduacao_selecionada, novos_golpes)
                st.success(f"Golpes salvos para {graduacao_selecionada}")
        st.markdown("</div>", unsafe_allow_html=True)

    # GERENCIAR ALUNOS
    elif st.session_state.admin_page == "Alunos":
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

            st.markdown('<h4 class="section-title" style="font-size:24px;margin:50px 0 20px 0;">Alunos Pendentes de Aprovação</h4>', unsafe_allow_html=True)
            pendentes = [a for a in alunos_lista if a['status'] == 'pendente']
            if pendentes:
                for aluno in pendentes:
                    col1, col2 = st.columns([5,1])
                    col1.markdown(f'<div class="admin-card" style="margin:15px 0;padding:25px;"><strong>{aluno["nome"]}</strong> — {aluno["graduacao"]}<br>{aluno["email"]}</div>', unsafe_allow_html=True)
                    if col2.button("APROVAR", key=f"aprov_{aluno['email']}"):
                        aprovar_aluno(aluno['email'])
                        st.success(f"{aluno['nome']} aprovado!")
                        st.rerun()
            else:
                st.info("Nenhum aluno pendente no momento")
        else:
            st.info("Nenhum capoeirista cadastrado")
        st.markdown("</div>", unsafe_allow_html=True)

    # CONFIGURAÇÕES
    elif st.session_state.admin_page == "Configurações":
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

# PORTAL DO ALUNO ESTILIZADO
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

# TROCA DE SENHA OBRIGATÓRIA ESTILIZADA
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
                    st.success("Senha alterada")
                    st.rerun()
                else:
                    st.error("Senha atual incorreta")
    st.markdown('</div>', unsafe_allow_html=True)

# CADASTRO ESTILIZADO
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
    st.markdown('</div>', unsafe_allow_html=True)

# LOGIN ALUNO ESTILIZADO
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
