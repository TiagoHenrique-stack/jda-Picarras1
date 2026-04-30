import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, get_app, _apps, storage
from datetime import datetime
import hashlib
import pandas as pd
import base64
import os

st.set_page_config(layout="wide", page_title="JDA PIÇARRAS - Capoeira", initial_sidebar_state="expanded")

# Inicialização do Firebase
if not _apps:
    try:
        if 'firebase_credentials' in st.secrets:
            cred = credentials.Certificate(dict(st.secrets['firebase_credentials']))
        else:
            cred = credentials.Certificate("firebase_key.json")
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

# CSS APENAS PARA PÁGINA PÚBLICA
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

header, #MainMenu, footer {visibility: hidden!important;}

.stApp {
    background: #0a0a0a!important;
    padding: 60px 20px 40px 20px!important;
}

.title-cardinal {
    font-family: 'Playfair Display', serif!important;
    font-size: 72px!important;
    font-weight: 800!important;
    background: linear-gradient(135deg, #00ff88 0%, #ffff00 100%)!important;
    -webkit-background-clip: text!important;
    -webkit-text-fill-color: transparent!important;
    background-clip: text!important;
    text-align: center!important;
    letter-spacing: -2px!important;
    margin: 0 0 24px 0!important;
}

.subtitle-cardinal {
    font-family: 'Inter', sans-serif!important;
    font-size: 16px!important;
    color: rgba(255, 255, 255, 0.8)!important;
    text-align: center!important;
    letter-spacing: 1.5px!important;
    margin: 0 auto 80px auto!important;
}

[data-testid="stButton"] > button {
    background: #000!important;
    border: 2px solid #00ff88!important;
    color: #00ff88!important;
    font-family: 'Inter', sans-serif!important;
    font-size: 14px!important;
    font-weight: 600!important;
    letter-spacing: 3px!important;
    text-transform: uppercase!important;
    padding: 35px 50px!important;
    width: 100%!important;
    border-radius: 0px!important;
}

[data-testid="stButton"] > button:hover {
    background: #00ff88!important;
    color: #000!important;
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
    st.title("Painel do Mestre - Login")
    with st.form("admin_login_form"):
        email = st.text_input("Email Admin")
        senha = st.text_input("Senha Admin", type="password")
        submitted = st.form_submit_button("ENTRAR")
        if submitted:
            login_aluno(email, senha)

    if st.button("VOLTAR"):
        st.session_state.show_admin = False
        st.rerun()

# PAINEL ADMIN LOGADO - SIDEBAR NATIVA
elif st.session_state.logged_in and not st.session_state.must_change_password and st.session_state.user_data.get('role') == 'admin':

    # SIDEBAR NATIVA DO STREAMLIT
    with st.sidebar:
        st.title("Painel Mestre")
        st.session_state.admin_page = st.radio(
            "Menu",
            ["Dashboard", "Horários", "Loja", "Golpes", "Alunos", "Configurações"]
        )
        st.divider()
        if st.button("Sair"):
            logout()

    # CONTEÚDO PRINCIPAL DO ADMIN
    st.header(f"{st.session_state.admin_page}")

    # DASHBOARD
    if st.session_state.admin_page == "Dashboard":
        alunos = list(db.collection('alunos').stream())
        total_alunos = len([a for a in alunos if a.to_dict().get('role') == 'aluno'])
        alunos_ativos = len([a for a in alunos if a.to_dict().get('status') == 'ativo'])
        alunos_pendentes = len([a for a in alunos if a.to_dict().get('status') == 'pendente'])

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Capoeiristas", total_alunos)
        col2.metric("Ativos", alunos_ativos)
        col3.metric("Pendentes", alunos_pendentes)

    # EDITAR HORÁRIOS
    elif st.session_state.admin_page == "Horários":
        st.subheader("Editar Horários de Treino")
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

            if st.form_submit_button("SALVAR HORÁRIOS"):
                salvar_horarios(novos_horarios)
                st.success("Horários salvos!")

    # EDITAR LOJA
    elif st.session_state.admin_page == "Loja":
        st.subheader("Editar Produtos da Loja")
        produtos = obter_produtos_loja()

        with st.form("form_loja"):
            novos_produtos = []
            for i in range(3):
                nome_atual = produtos[i]["nome"] if i < len(produtos) else ""
                preco_atual = float(produtos[i]["preco"]) if i < len(produtos) else 0.0
                desc_atual = produtos[i]["descricao"] if i < len(produtos) else ""

                st.write(f"Produto {i+1}")
                col1, col2, col3 = st.columns(3)
                nome = col1.text_input(f"Nome {i+1}", value=nome_atual)
                preco = col2.number_input(f"Preço {i+1}", value=preco_atual)
                desc = col3.text_input(f"Descrição {i+1}", value=desc_atual)
                novos_produtos.append({"nome": nome, "preco": preco, "descricao": desc})

            if st.form_submit_button("SALVAR PRODUTOS"):
                salvar_produtos_loja(novos_produtos)
                st.success("Produtos salvos!")

    # EDITAR GOLPES
    elif st.session_state.admin_page == "Golpes":
        st.subheader("Editar 25 Golpes por Graduação")
        graduacao_selecionada = st.selectbox("Selecione a Graduação", GRADUACOES_CAPOEIRA)
        golpes = obter_golpes_por_graduacao(graduacao_selecionada)

        with st.form(f"form_golpes_{graduacao_selecionada}"):
            novos_golpes = []
            for i in range(25):
                nome_atual = golpes[i]["nome"] if i < len(golpes) else f"Golpe {i+1}"
                desc_atual = golpes[i]["descricao"] if i < len(golpes) else ""
                col1, col2 = st.columns(2)
                nome = col1.text_input(f"Golpe {i+1}", value=nome_atual, key=f"golpe_nome_{i}")
                desc = col2.text_input(f"Descrição {i+1}", value=desc_atual, key=f"golpe_desc_{i}")
                novos_golpes.append({"nome": nome, "descricao": desc})

            if st.form_submit_button("SALVAR 25 GOLPES"):
                salvar_golpes_por_graduacao(graduacao_selecionada, novos_golpes)
                st.success(f"Golpes salvos para {graduacao_selecionada}")

    # GERENCIAR ALUNOS
    elif st.session_state.admin_page == "Alunos":
        st.subheader("Gerenciar Alunos")
        alunos = list(db.collection('alunos').stream())
        alunos_lista = []
        for aluno in alunos:
            dados = aluno.to_dict()
            dados['id'] = aluno.id
            if dados.get('role') == 'aluno':
                alunos_lista.append(dados)

        if alunos_lista:
            df = pd.DataFrame(alunos_lista)
            st.dataframe(df[['nome', 'email', 'graduacao', 'status']])

            st.subheader("Alunos Pendentes")
            pendentes = [a for a in alunos_lista if a['status'] == 'pendente']
            for aluno in pendentes:
                col1, col2 = st.columns([4,1])
                col1.write(f"{aluno['nome']} - {aluno['graduacao']}")
                if col2.button("APROVAR", key=f"aprov_{aluno['email']}"):
                    aprovar_aluno(aluno['email'])
                    st.rerun()
        else:
            st.info("Nenhum aluno cadastrado")

    # CONFIGURAÇÕES
    elif st.session_state.admin_page == "Configurações":
        st.subheader("Configurações Gerais")
        with st.form("config_form"):
            nova_taxa = st.number_input("Taxa de Cadastro R$", value=float(obter_taxa_cadastro()))
            nova_chave_pix = st.text_input("Chave PIX", value=obter_chave_pix())
            if st.form_submit_button("SALVAR CONFIGURAÇÕES"):
                db.collection('config').document('taxa_cadastro').set({'valor': nova_taxa})
                db.collection('config').document('chave_pix').set({'valor': nova_chave_pix})
                st.success("Configurações salvas!")

# PORTAL DO ALUNO
elif st.session_state.logged_in and not st.session_state.must_change_password and st.session_state.user_data.get('role') == 'aluno':
    st.header(f"Portal do Capoeirista - {st.session_state.user_data['nome']}")
    st.write(f"Graduação: {st.session_state.user_data['graduacao']}")

    st.subheader("Meus Golpes")
    golpes = obter_golpes_por_graduacao(st.session_state.user_data["graduacao"])
    progresso = st.session_state.user_data.get('progresso_golpes', {}).get(st.session_state.user_data["graduacao"], [False] * 25)

    with st.form("form_progresso"):
        for i, golpe in enumerate(golpes):
            checked = st.checkbox(f"{golpe['nome']} - {golpe['descricao']}", value=progresso[i] if i < len(progresso) else False)
            if i < len(progresso):
                progresso[i] = checked

        if st.form_submit_button("SALVAR PROGRESSO"):
            db.collection('alunos').document(st.session_state.user_data['email']).update({
                f'progresso_golpes.{st.session_state.user_data["graduacao"]}': progresso
            })
            st.success("Progresso salvo!")
            st.rerun()

    if st.button("SAIR"):
        logout()

# TROCA DE SENHA OBRIGATÓRIA
elif st.session_state.must_change_password:
    st.title("Primeiro Acesso - Trocar Senha")
    with st.form("trocar_senha_form"):
        senha_atual = st.text_input("Senha Atual", type="password")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar_senha = st.text_input("Confirmar Nova Senha", type="password")
        submitted = st.form_submit_button("CONFIRMAR")

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

# CADASTRO
elif st.session_state.show_cadastro:
    st.title("Inscrição JDA Piçarras")
    with st.form("cadastro_form"):
        nome = st.text_input("Nome Completo")
        email = st.text_input("Email")
        telefone = st.text_input("Telefone")
        graduacao = st.selectbox("Graduação Atual", GRADUACOES_CAPOEIRA)

        st.write(f"**Taxa de Cadastro: R$ {obter_taxa_cadastro():.2f}**")
        st.write(f"**Chave PIX: {obter_chave_pix()}**")

        taxa_paga = st.checkbox("Taxa paga via PIX")
        mensalidade_paga = st.checkbox("Mensalidade paga")

        submitted = st.form_submit_button("FINALIZAR INSCRIÇÃO")
        if submitted:
            if nome and email and telefone:
                cadastrar_aluno(nome, email, graduacao, telefone, 1 if mensalidade_paga else 0, 1 if taxa_paga else 0)
                st.success("Inscrição realizada! Aguarde aprovação do mestre.")
                st.session_state.show_cadastro = False
                st.rerun()
            else:
                st.error("Preencha todos os campos")

    if st.button("VOLTAR"):
        st.session_state.show_cadastro = False
        st.rerun()

# LOGIN ALUNO
elif st.session_state.show_student_portal and not st.session_state.logged_in:
    st.title("Portal do Capoeirista")
    with st.form("login_form_aluno"):
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("ENTRAR")
        if submitted:
            login_aluno(email, senha)

    if st.button("VOLTAR"):
        st.session_state.show_student_portal = False
        st.rerun()
