import streamlit as st
from firebase_admin import credentials, firestore, initialize_app
import hashlib
import base64
from datetime import datetime
from PIL import Image
import io

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="JDA PIÇARRAS - ACADEMIA DE CAPOEIRA",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS PREMIUM PRETO + VERDE + DOURADO
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Montserrat:wght@300;400;600;700;800&display=swap');

* {
    font-family: 'Montserrat', sans-serif;
}

.stApp {
    background: #0A0A0A;
    color: #FFFFFF;
}

.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 120px;
    font-weight: 900;
    background: linear-gradient(90deg, #32FF7E 0%, #FFD700 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-shadow: 0 0 40px rgba(50, 255, 126, 0.4);
    letter-spacing: 12px;
    line-height: 1.1;
    margin-bottom: 20px;
}

.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 64px;
    font-weight: 700;
    color: #FFFFFF;
    text-align: center;
    margin: 100px 0 60px 0;
    letter-spacing: 6px;
}

.neon-line {
    width: 120px;
    height: 4px;
    background: linear-gradient(90deg, #32FF7E 0%, #FFD700 100%);
    box-shadow: 0 0 20px #32FF7E;
    margin: 0 auto 80px auto;
}

.stButton > button {
    background: transparent;
    border: 2px solid #32FF7E;
    color: #32FF7E;
    font-family: 'Montserrat';
    font-weight: 700;
    font-size: 14px;
    letter-spacing: 3px;
    padding: 18px 40px;
    text-transform: uppercase;
    transition: all 0.3s ease;
    border-radius: 0px;
    box-shadow: 0 0 15px rgba(50, 255, 126, 0.2);
}

.stButton > button:hover {
    background: #32FF7E;
    color: #0A0A0A;
    box-shadow: 0 0 30px rgba(50, 255, 126, 0.8);
    transform: translateY(-2px);
}

.stTextInput > div > div > input {
    background: #1A1A1A;
    border: 1px solid #333;
    color: #FFFFFF;
    font-family: 'Montserrat';
    font-size: 16px;
    padding: 15px;
    border-radius: 0px;
}

.stTextInput > div > div > input:focus {
    border: 1px solid #32FF7E;
    box-shadow: 0 0 10px rgba(50, 255, 126, 0.5);
}

.stSelectbox > div > div > select {
    background: #1A1A1A;
    border: 1px solid #333;
    color: #FFFFFF;
    font-family: 'Montserrat';
    border-radius: 0px;
}

.stRadio > div {
    flex-direction: row;
    gap: 30px;
    justify-content: center;
    margin-bottom: 60px;
}

.stRadio > div > label {
    font-family: 'Montserrat';
    font-weight: 600;
    letter-spacing: 2px;
    font-size: 13px;
    color: #666;
}

.stRadio > div > label[data-checked="true"] {
    color: #32FF7E;
    text-shadow: 0 0 10px #32FF7E;
}

.pix-box {
    background: #1A1A1A;
    border: 2px solid #32FF7E;
    padding: 30px;
    margin: 30px 0;
    box-shadow: 0 0 25px rgba(50,255,126,0.2);
}

div[data-testid="stExpander"] {
    background: #1A1A1A;
    border: 1px solid #333;
    border-radius: 0px;
}

div[data-testid="stExpander"] > div > div > p {
    font-family: 'Montserrat';
    font-weight: 600;
    letter-spacing: 2px;
    color: #32FF7E;
}

</style>
""", unsafe_allow_html=True)

# FIREBASE INIT
from firebase_admin import get_app, _apps

if not _apps:
    try:
        if 'firebase_credentials' in st.secrets:
            cred = credentials.Certificate(dict(st.session_state.firebase_credentials)) if 'firebase_credentials' in st.session_state else credentials.Certificate(dict(st.secrets['firebase_credentials']))
        else:
            cred = credentials.Certificate("firebase_key.json")
        initialize_app(cred)
    except Exception as e:
        st.error(f"ERRO FIREBASE: {e}")
        st.stop()
else:
    app = get_app()

db = firestore.client()
col_alunos = db.collection('alunos')
col_horarios = db.collection('horarios')
col_produtos = db.collection('produtos')
col_pedidos = db.collection('pedidos')
col_itens_pedido = db.collection('itens_pedido')
col_config = db.collection('config')
col_progressao = db.collection('progressao')

# CONSTANTES GRADUAÇÃO
GRADUACOES = [
    (0, "Iniciante"),
    (1, "Cinza"),
    (2, "Cinza e Amarela"),
    (3, "Amarela"),
    (4, "Amarela e Laranja"),
    (5, "Laranja"),
    (6, "Laranja e Azul"),
    (7, "Azul"),
    (8, "Azul e Verde"),
    (9, "Verde"),
    (10, "Verde e Roxa"),
    (11, "Roxa"),
    (12, "Roxa e Marrom"),
    (13, "Marrom"),
    (14, "Marrom e Vermelha"),
    (15, "Vermelha"),
    (16, "Mestre")
]

def get_graduacoes():
    return GRADUACOES

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def resize_image(uploaded_file, max_size=(400, 400)):
    img = Image.open(uploaded_file)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode()

def get_config(chave):
    doc = col_config.document(chave).get()
    return doc.to_dict()['valor'] if doc.exists else ""

def set_config(chave, valor):
    col_config.document(chave).set({'valor': valor})

# SESSION STATE
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'home'
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []
if 'forcar_troca_senha' not in st.session_state:
    st.session_state.forcar_troca_senha = False

# ===== HOME =====
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

    horarios = sorted([doc.to_dict() for doc in col_horarios.stream()], key=lambda x: x.get('ordem', 0))
    dias = {}
    for h in horarios:
        if h['dia'] not in dias:
            dias[h['dia']] = []
        dias[h['dia']].append(h)

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
                        {aula['horario']}
                    </div>
                    <div style="font-family:'Montserrat'; font-size:18px; color:#CCCCCC; letter-spacing: 2px;">
                        {aula['turma']}
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

# ===== LOGIN =====
elif st.session_state.pagina == 'login':
    st.markdown('<div class="section-title">LOGIN</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        email = st.text_input("EMAIL")
        senha = st.text_input("SENHA", type="password")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("ENTRAR", use_container_width=True):
                usuario_doc = col_alunos.document(email).get()
                if usuario_doc.exists:
                    usuario = usuario_doc.to_dict()
                    if usuario['senha'] == hash_senha(senha):
                        if usuario.get('status') == 'pendente':
                            st.error("SUA CONTA AINDA NÃO FOI APROVADA PELO MESTRE JDA!")
                        else:
                            if usuario['senha'] == hash_senha(f"{email.split('@')[0]}JDA{datetime.now().year}"):
                                st.session_state.forcar_troca_senha = True
                            usuario['id'] = email
                            st.session_state.usuario = usuario
                            st.session_state.pagina = 'admin' if usuario.get('role') == 'admin' else 'aluno'
                            st.rerun()
                    else:
                        st.error("EMAIL OU SENHA INCORRETOS!")
                else:
                    st.error("EMAIL OU SENHA INCORRETOS!")
        with col_btn2:
            if st.button("VOLTAR", use_container_width=True):
                st.session_state.pagina = 'home'
                st.rerun()

# ===== REGISTRO =====
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
                if col_alunos.document(email).get().exists:
                    st.error("EMAIL JÁ CADASTRADO!")
                else:
                    col_alunos.document(email).set({
                        'nome': nome, 'email': email, 'senha': hash_senha(senha), 'telefone': telefone,
                        'data_cadastro': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'status': 'pendente', 'graduacao': 'Iniciante', 'paga_mensalidade': 0,
                        'taxa_cadastro_paga': 0, 'role': 'aluno'
                    })
                    st.success("CADASTRO REALIZADO! ENVIE O COMPROVANTE DO PIX PARA O MESTRE JDA APROVAR SEU ACESSO.")
            else:
                st.error("PREENCHA TODOS OS CAMPOS!")
        if st.button("VOLTAR PARA HOME", use_container_width=True):
            st.session_state.pagina = 'home'
            st.rerun()

# ===== RECUPERAR SENHA =====
elif st.session_state.pagina == 'esqueci_senha':
    st.markdown('<div class="section-title">RECUPERAR SENHA</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        email_recuperar = st.text_input("DIGITE SEU EMAIL CADASTRADO")
        if st.button("GERAR SENHA TEMPORÁRIA", use_container_width=True):
            if email_recuperar:
                usuario_doc = col_alunos.document(email_recuperar).get()
                if usuario_doc.exists:
                    nova_senha_temp = f"{email_recuperar.split('@')[0]}JDA{datetime.now().year}"
                    col_alunos.document(email_recuperar).update({'senha': hash_senha(nova_senha_temp)})
                    st.success(f"SENHA TEMPORÁRIA GERADA: {nova_senha_temp}")
                    st.info("USE ESSA SENHA NO LOGIN. VOCÊ SERÁ OBRIGADO A TROCAR NA PRIMEIRA ENTRADA.")
                else:
                    st.error("EMAIL NÃO ENCONTRADO!")
            else:
                st.error("DIGITE SEU EMAIL!")
        if st.button("VOLTAR AO LOGIN", use_container_width=True):
            st.session_state.pagina = 'login'
            st.rerun()
            # ===== PAINEL ADMIN =====
elif st.session_state.pagina == 'admin':
    usuario = st.session_state.usuario
    if not usuario or usuario.get('role')!= 'admin':
        st.error("ACESSO NEGADO! VOCÊ NÃO É ADMINISTRADOR.")
        st.session_state.pagina = 'home'
        st.rerun()

    st.markdown('<div class="section-title">PAINEL MESTRE JDA</div>', unsafe_allow_html=True)
    aba = st.radio("", ["ALUNOS PENDENTES", "ALUNOS ATIVOS", "GRADUAÇÃO", "GOLPES", "HORÁRIOS", "LOJA", "PEDIDOS", "CONFIGURAÇÕES"], horizontal=True)

    if aba == "ALUNOS PENDENTES":
        st.markdown('<div class="section-title">ALUNOS AGUARDANDO APROVAÇÃO</div>', unsafe_allow_html=True)
        pendentes = [doc for doc in col_alunos.where('status', '==', 'pendente').stream()]
        if pendentes:
            for aluno in pendentes:
                a = aluno.to_dict()
                st.markdown(f"""
                <div style="padding:30px 0; border-bottom:1px solid #333;">
                    <div style="font-family:'Playfair Display'; font-size:32px; color:#32FF7E; text-shadow: 0 0 10px #32FF7E;">{a['nome']}</div>
                    <div style="font-family:'Montserrat'; color:#ccc; margin:12px 0;">{a['email']} | {a.get('telefone','')}</div>
                    <div style="font-family:'Montserrat'; color:#FFD700;">TAXA CADASTRO: {'PAGA' if a.get('taxa_cadastro_paga') else 'PENDENTE'}</div>
                </div>
                """, unsafe_allow_html=True)
                taxa_paga = st.checkbox("CONFIRMAR PAGAMENTO TAXA", value=bool(a.get('taxa_cadastro_paga')), key=f"taxa_{aluno.id}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"APROVAR ALUNO", key=f"aprov_{aluno.id}", use_container_width=True):
                        col_alunos.document(aluno.id).update({'status': 'ativo', 'taxa_cadastro_paga': 1 if taxa_paga else 0})
                        st.rerun()
                with col2:
                    if st.button(f"REJEITAR", key=f"rej_{aluno.id}", use_container_width=True):
                        col_alunos.document(aluno.id).delete()
                        st.warning("ALUNO REJEITADO!")
                        st.rerun()
        else:
            st.info("NENHUM ALUNO PENDENTE")

    elif aba == "ALUNOS ATIVOS":
        st.markdown('<div class="section-title">ALUNOS ATIVOS</div>', unsafe_allow_html=True)
        ativos = [doc for doc in col_alunos.where('status', '==', 'ativo').where('role', '==', 'aluno').stream()]
        if ativos:
            for aluno in ativos:
                a = aluno.to_dict()
                if a.get('foto_path'):
                    st.image(base64.b64decode(a['foto_path']), width=80)
                else:
                    st.markdown('<div style="width:80px;height:80px;border-radius:50%;background:#222;border:2px solid #32FF7E;display:flex;align-items:center;justify-content:center;color:#32FF7E;">JDA</div>', unsafe_allow_html=True)
                st.markdown(f"""
                <div style="padding:30px 0; border-bottom:1px solid #333;">
                    <div style="font-family:'Playfair Display'; font-size:32px; color:#32FF7E; text-shadow: 0 0 10px #32FF7E;">{a['nome']}</div>
                    <div style="font-family:'Montserrat'; color:#ccc;">Graduação: {a.get('graduacao','Iniciante')} | Mensalidade: {'ATIVA' if a.get('paga_mensalidade') else 'INATIVA'}</div>
                </div>
                """, unsafe_allow_html=True)
                paga_mensal = st.checkbox("PAGA MENSALIDADE", value=bool(a.get('paga_mensalidade')), key=f"mens_{aluno.id}")
                if st.button("SALVAR", key=f"save_mens_{aluno.id}"):
                    col_alunos.document(aluno.id).update({'paga_mensalidade': 1 if paga_mensal else 0})
                    st.success("ATUALIZADO!")
                    st.rerun()
        else:
            st.info("NENHUM ALUNO ATIVO")

    elif aba == "GOLPES":
        st.markdown('<div class="section-title">GESTÃO DE GOLPES POR GRADUAÇÃO</div>', unsafe_allow_html=True)
        graduacoes = get_graduacoes()
        GRADUACOES_NOMES = [g[1] for g in graduacoes]

        with st.container():
            grad_selecionada = st.selectbox("SELECIONE A GRADUAÇÃO", GRADUACOES_NOMES, key="grad_select_golpes")

            with st.form(key="form_add_golpe", clear_on_submit=True):
                st.markdown("### ADICIONAR GOLPE/MOVIMENTO")
                col1, col2, col3 = st.columns([2,2,1])
                with col1:
                    tipo_item = st.selectbox("TIPO", ["MOVIMENTO", "BERIMBAU", "PANDEIRO", "ATRIBUTO"], key="tipo_select_form")
                with col2:
                    nome_item = st.text_input("NOME DO GOLPE", placeholder="Ex: Meia-lua de frente", key="nome_golpe_form")
                with col3:
                    st.write("")
                    st.write("")
                    submit_btn = st.form_submit_button("ADICIONAR", use_container_width=True)

            if submit_btn and nome_item and nome_item.strip():
                golpes_grad = [g for g in col_progressao.where('graduacao','==',grad_selecionada).stream()]
                max_ordem = max([g.to_dict().get('ordem',0) for g in golpes_grad], default=0)
                col_progressao.add({
                    'graduacao': grad_selecionada, 'tipo': tipo_item.lower(),
                    'nome': nome_item.strip(), 'ordem': max_ordem + 1
                })
                st.success(f"GOLPE '{nome_item}' ADICIONADO EM {grad_selecionada}!")
                st.rerun()

            st.markdown(f"### GOLPES PARA {grad_selecionada.upper()}")
            tipos = ["MOVIMENTO", "BERIMBAU", "PANDEIRO", "ATRIBUTO"]
            for tipo in tipos:
                itens = sorted([g for g in col_progressao.where('graduacao','==',grad_selecionada).where('tipo','==',tipo.lower()).stream()],
                               key=lambda x: x.to_dict().get('ordem',0))
                if itens:
                    st.markdown(f"#### {tipo} ({len(itens)}/25)")
                    for item in itens:
                        i = item.to_dict()
                        col1, col2 = st.columns([4,1])
                        col1.write(f"{i['nome']}")
                        if col2.button("EXCLUIR", key=f"del_prog_{item.id}"):
                            col_progressao.document(item.id).delete()
                            st.success("GOLPE EXCLUÍDO!")
                            st.rerun()
                else:
                    st.info(f"NENHUM {tipo} CADASTRADO PARA {grad_selecionada}")

    elif aba == "GRADUAÇÃO":
        st.markdown('<div class="section-title">APROVAR GRADUAÇÃO</div>', unsafe_allow_html=True)
        graduacoes = get_graduacoes()
        GRADUACOES_NOMES = [g[1] for g in graduacoes]
        alunos = [doc for doc in col_alunos.where('status', '==', 'ativo').where('role', '==', 'aluno').stream()]
        if alunos:
            for aluno in alunos:
                a = aluno.to_dict()
                grad_atual = a.get('graduacao','Iniciante')
                idx_atual = GRADUACOES_NOMES.index(grad_atual) if grad_atual in GRADUACOES_NOMES else 0
                proxima_grad = GRADUACOES_NOMES[idx_atual + 1] if idx_atual + 1 < len(GRADUACOES_NOMES) else None

                if proxima_grad:
                    st.markdown(f"""
                    <div style="padding:30px 0; border-bottom:1px solid #333;">
                        <div style="font-family:'Playfair Display'; font-size:32px; color:#32FF7E; text-shadow: 0 0 10px #32FF7E;">{a['nome']}</div>
                        <div style="font-family:'Montserrat'; color:#ccc;">Graduação Atual: {grad_atual} → Próxima: {proxima_grad}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"PROMOVER PARA {proxima_grad.upper()}", key=f"prom_{aluno.id}", use_container_width=True):
                        col_alunos.document(aluno.id).update({'graduacao': proxima_grad})
                        st.success(f"{a['nome']} PROMOVIDO PARA {proxima_grad}!")
                        st.rerun()
                else:
                    st.markdown(f"""
                    <div style="padding:30px 0; border-bottom:1px solid #333;">
                        <div style="font-family:'Playfair Display'; font-size:32px; color:#32FF7E; text-shadow: 0 0 10px #32FF7E;">{a['nome']}</div>
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
                    horarios = list(col_horarios.stream())
                    max_ordem = max([h.to_dict().get('ordem',0) for h in horarios], default=0)
                    col_horarios.add({'dia': novo_dia, 'turma': nova_turma, 'horario': novo_horario, 'ordem': max_ordem + 1})
                    st.success("HORÁRIO ADICIONADO!")
                    st.rerun()

        horarios = sorted([doc for doc in col_horarios.stream()], key=lambda x: x.to_dict().get('ordem',0))
        for h in horarios:
            h_data = h.to_dict()
            st.markdown(f"""
            <div style="padding:25px 0; border-bottom:1px solid #333;">
                <div style="font-family:'Montserrat'; font-size:13px; color:#32FF7E; text-shadow: 0 0 10px #32FF7E;">{h_data['dia'].upper()}</div>
                <div style="font-family:'Playfair Display'; font-size:32px; color:#fff;">{h_data['turma']}</div>
                <div style="font-family:'Montserrat'; font-size:22px; color:#999;">{h_data['horario']}</div>
            </div>
            """, unsafe_allow_html=True)
            col1, col2, col3 = st.columns([3,3,1])
            dia_edit = col1.text_input("DIA", value=h_data['dia'], key=f"dia_{h.id}")
            turma_edit = col2.text_input("TURMA", value=h_data['turma'], key=f"turma_{h.id}")
            horario_edit = col3.text_input("HORÁRIO", value=h_data['horario'], key=f"hor_{h.id}")
            if st.button("SALVAR", key=f"save_{h.id}", use_container_width=True):
                col_horarios.document(h.id).update({'dia': dia_edit, 'turma': turma_edit, 'horario': horario_edit})
                st.success("ATUALIZADO!")
                st.rerun()
            if st.button("EXCLUIR", key=f"del_{h.id}", use_container_width=True):
                col_horarios.document(h.id).delete()
                st.success("HORÁRIO EXCLUÍDO!")
                st.rerun()

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
                    produtos = list(col_produtos.stream())
                    max_ordem = max([p.to_dict().get('ordem',0) for p in produtos], default=0)
                    col_produtos.add({
                        'nome': nome_prod, 'categoria': categoria_prod, 'preco': preco_prod,
                        'estoque': estoque_prod, 'descricao': descricao_prod, 'imagem_url': imagem_bytes,
                        'ativo': 1, 'ordem': max_ordem + 1
                    })
                    st.success("PRODUTO ADICIONADO!")
                    st.rerun()

        produtos = sorted([doc for doc in col_produtos.stream()], key=lambda x: x.to_dict().get('ordem',0))
        for prod in produtos:
            p = prod.to_dict()
            if p.get('imagem_url'):
                st.image(base64.b64decode(p['imagem_url']), width=200)
            st.markdown(f"""
            <div style="padding:30px 0; border-bottom:1px solid #333;">
                <div style="font-family:'Playfair Display'; font-size:32px; color:#32FF7E; text-shadow: 0 0 10px #32FF7E;">{p['nome']}</div>
                <div style="font-family:'Montserrat'; color:#ccc;">R$ {p['preco']:.2f} | Estoque: {p['estoque']}</div>
                <div style="font-family:'Montserrat'; color:#999;">{p['descricao']}</div>
            </div>
            """, unsafe_allow_html=True)
            col1, col2 = st.columns([2,1])
            nome_edit = col1.text_input("NOME", value=p['nome'], key=f"pn_{prod.id}")
            preco_edit = col2.number_input("PREÇO", value=float(p['preco']), key=f"pp_{prod.id}")
            estoque_edit = col1.number_input("ESTOQUE", value=int(p['estoque']), key=f"pe_{prod.id}")
            ativo_edit = col2.checkbox("ATIVO", value=bool(p['ativo']), key=f"pa_{prod.id}")
            if st.button("SALVAR", key=f"ps_{prod.id}", use_container_width=True):
                col_produtos.document(prod.id).update({
                    'nome': nome_edit, 'preco': preco_edit, 'estoque': estoque_edit, 'ativo': 1 if ativo_edit else 0
                })
                st.success("ATUALIZADO!")
                st.rerun()
            if st.button("EXCLUIR", key=f"pdel_{prod.id}", use_container_width=True):
                col_produtos.document(prod.id).delete()
                st.success("PRODUTO EXCLUÍDO!")
                st.rerun()

    elif aba == "PEDIDOS":
        st.markdown('<div class="section-title">PEDIDOS RECEBIDOS</div>', unsafe_allow_html=True)
        pedidos = sorted([doc for doc in col_pedidos.stream()], key=lambda x: x.to_dict().get('data_pedido',''), reverse=True)
        if pedidos:
            for pedido in pedidos:
                p = pedido.to_dict()
                aluno_doc = col_alunos.document(p['aluno_id']).get()
                aluno_nome = aluno_doc.to_dict()['nome'] if aluno_doc.exists else "ALUNO REMOVIDO"
                st.markdown(f"""
                <div style="padding:30px 0; border-bottom:1px solid #333;">
                    <div style="font-family:'Playfair Display'; font-size:32px; color:#32FF7E; text-shadow: 0 0 10px #32FF7E;">PEDIDO #{pedido.id} - {aluno_nome}</div>
                    <div style="font-family:'Montserrat'; color:#ccc;">R$ {p['total']:.2f} | {p['status'].upper()} | {p['data_pedido']}</div>
                </div>
                """, unsafe_allow_html=True)
                itens = [doc.to_dict() for doc in col_itens_pedido.where('pedido_id', '==', pedido.id).stream()]
                for item in itens:
                    prod_doc = col_produtos.document(item['produto_id']).get()
                    prod_nome = prod_doc.to_dict()['nome'] if prod_doc.exists else "PRODUTO REMOVIDO"
                    st.write(f"- {item['quantidade']}x {prod_nome} - R$ {item['preco_unitario']:.2f}")
                novo_status = st.selectbox("STATUS", ["pendente", "pago", "enviado", "entregue"],
                                           index=["pendente", "pago", "enviado", "entregue"].index(p['status']), key=f"st_{pedido.id}")
                if st.button("ATUALIZAR STATUS", key=f"stb_{pedido.id}"):
                    col_pedidos.document(pedido.id).update({'status': novo_status})
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

# ===== PAINEL ALUNO =====
elif st.session_state.pagina == 'aluno':
    usuario = st.session_state.usuario

    # BLOQUEIA ADMIN DE ENTRAR NO PAINEL DE ALUNO
    if usuario.get('role') == 'admin':
        st.session_state.pagina = 'admin'
        st.rerun()

    if st.session_state.forcar_troca_senha:
        st.markdown('<div class="section-title">TROCAR SENHA TEMPORÁRIA</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            nova_senha = st.text_input("NOVA SENHA", type="password")
            confirmar_senha = st.text_input("CONFIRMAR SENHA", type="password")
            if st.button("SALVAR NOVA SENHA", use_container_width=True):
                if nova_senha and nova_senha == confirmar_senha:
                    col_alunos.document(usuario['id']).update({'senha': hash_senha(nova_senha)})
                    st.session_state.forcar_troca_senha = False
                    st.success("SENHA ALTERADA! FAÇA LOGIN NOVAMENTE.")
                    st.session_state.usuario = None
                    st.session_state.pagina = 'home'
                    st.rerun()
                else:
                    st.error("SENHAS NÃO CONFEREM!")
        st.stop()

    st.markdown('<div class="section-title">PAINEL DO ALUNO</div>', unsafe_allow_html=True)
    aba = st.radio("", ["MEU PERFIL", "PROGRESSÃO", "LOJA", "MEUS PEDIDOS"], horizontal=True)

    if aba == "MEU PERFIL":
        st.markdown('<div class="section-title">MEU PERFIL</div>', unsafe_allow_html=True)
        col1, col2 = st.columns([1,3])
        with col1:
            if usuario.get('foto_path'):
                st.image(base64.b64decode(usuario['foto_path']), width=150)
            else:
                st.markdown('<div style="width:150px;height:150px;border-radius:50%;background:#222;border:3px solid #32FF7E;display:flex;align-items:center;justify-content:center;color:#32FF7E;font-size:48px;font-family:Playfair Display;">JDA</div>', unsafe_allow_html=True)
            foto_upload = st.file_uploader("ENVIAR FOTO", type=['jpg', 'jpeg', 'png'], key="foto_perfil")
            if foto_upload:
                foto_bytes = resize_image(foto_upload)
                col_alunos.document(usuario['id']).update({'foto_path': foto_bytes})
                st.success("FOTO ATUALIZADA!")
                st.rerun()
        with col2:
            st.markdown(f"""
            <div style="padding:30px 0;">
                <div style="font-family:'Playfair Display'; font-size:40px; color:#32FF7E; text-shadow: 0 0 10px #32FF7E;">{usuario['nome']}</div>
                <div style="font-family:'Montserrat'; color:#ccc; margin:15px 0;">{usuario['email']} | {usuario.get('telefone','')}</div>
                <div style="font-family:'Montserrat'; color:#32FF7E; font-weight:700; font-size:16px;">GRADUAÇÃO: {usuario.get('graduacao','Iniciante')}</div>
                <div style="font-family:'Montserrat'; color:#ccc; font-size:16px;">STATUS MENSALIDADE: {'ATIVA' if usuario.get('paga_mensalidade') else 'INATIVA'}</div>
            </div>
            """, unsafe_allow_html=True)

    elif aba == "PROGRESSÃO":
        st.markdown('<div class="section-title">MINHA PROGRESSÃO</div>', unsafe_allow_html=True)
        grad_atual = usuario.get('graduacao','Iniciante')
        tipos = ["MOVIMENTO", "BERIMBAU", "PANDEIRO", "ATRIBUTO"]
        for tipo in tipos:
            itens = sorted([g.to_dict() for g in col_progressao.where('graduacao','==',grad_atual).where('tipo','==',tipo.lower()).stream()],
                           key=lambda x: x.get('ordem',0))
            if itens:
                st.markdown(f"### {tipo} ({len(itens)}/25)")
                for item in itens:
                    st.checkbox(item['nome'], key=f"prog_aluno_{item['nome']}", disabled=True)
            else:
                st.info(f"NENHUM {tipo} CADASTRADO PARA {grad_atual}")

    elif aba == "LOJA":
        st.markdown('<div class="section-title">LOJA JDA</div>', unsafe_allow_html=True)
        chave_pix = get_config('chave_pix')
        st.info(f"PIX PARA PAGAMENTO: {chave_pix}")

        # CARRINHO
        if st.session_state.carrinho:
            st.markdown("### SEU CARRINHO")
            total_carrinho = 0
            for i, item in enumerate(st.session_state.carrinho):
                col1, col2 = st.columns([4,1])
                col1.write(f"{item['nome']} - R$ {item['preco']:.2f}")
                if col2.button("REMOVER", key=f"rem_{i}"):
                    st.session_state.carrinho.pop(i)
                    st.rerun()
                total_carrinho += item['preco']
            st.markdown(f"**TOTAL: R$ {total_carrinho:.2f}**")
            if st.button("FINALIZAR PEDIDO", use_container_width=True):
                pedido_ref = col_pedidos.add({
                    'aluno_id': usuario['id'],
                    'total': total_carrinho,
                    'status': 'pendente',
                    'data_pedido': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })[1]
                for item in st.session_state.carrinho:
                    col_itens_pedido.add({
                        'pedido_id': pedido_ref.id,
                        'produto_id': item['id'],
                        'quantidade': 1,
                        'preco_unitario': item['preco']
                    })
                    # DIMINUIR ESTOQUE
                    prod_doc = col_produtos.document(item['id']).get()
                    if prod_doc.exists:
                        estoque_atual = prod_doc.to_dict().get('estoque', 0)
                        col_produtos.document(item['id']).update({'estoque': max(0, estoque_atual - 1)})
                st.session_state.carrinho = []
                st.success("PEDIDO REALIZADO COM SUCESSO!")
                st.rerun()

        # LISTA PRODUTOS
        st.markdown("### PRODUTOS DISPONÍVEIS")
        produtos = sorted([doc for doc in col_produtos.where('ativo', '==', 1).stream()], key=lambda x: x.to_dict().get('ordem',0))
        for prod in produtos:
            p = prod.to_dict()
            if p.get('imagem_url'):
                st.image(base64.b64decode(p['imagem_url']), width=200)
            st.markdown(f"""
            <div style="padding:30px 0; border-bottom:1px solid #333;">
                <div style="font-family:'Playfair Display'; font-size:32px; color:#32FF7E; text-shadow: 0 0 10px #32FF7E;">{p['nome']}</div>
                <div style="font-family:'Montserrat'; color:#ccc;">R$ {p['preco']:.2f} | Estoque: {p['estoque']}</div>
                <div style="font-family:'Montserrat'; color:#999;">{p['descricao']}</div>
            </div>
            """, unsafe_allow_html=True)
            if p['estoque'] > 0:
                if st.button("ADICIONAR AO CARRINHO", key=f"cart_{prod.id}", use_container_width=True):
                    st.session_state.carrinho.append({'id': prod.id, 'nome': p['nome'], 'preco': p['preco']})
                    st.success(f"{p['nome']} ADICIONADO AO CARRINHO!")
                    st.rerun()
            else:
                st.warning("PRODUTO ESGOTADO")

    elif aba == "MEUS PEDIDOS":
        st.markdown('<div class="section-title">MEUS PEDIDOS</div>', unsafe_allow_html=True)
        meus_pedidos = sorted([doc for doc in col_pedidos.where('aluno_id', '==', usuario['id']).stream()],
                              key=lambda x: x.to_dict().get('data_pedido',''), reverse=True)
        if meus_pedidos:
            for pedido in meus_pedidos:
                p = pedido.to_dict()
                st.markdown(f"""
                <div style="padding:30px 0; border-bottom:1px solid #333;">
                    <div style="font-family:'Playfair Display'; font-size:32px; color:#32FF7E; text-shadow: 0 0 10px #32FF7E;">PEDIDO #{pedido.id}</div>
                    <div style="font-family:'Montserrat'; color:#ccc;">R$ {p['total']:.2f} | {p['status'].upper()} | {p['data_pedido']}</div>
                </div>
                """, unsafe_allow_html=True)
                itens = [doc.to_dict() for doc in col_itens_pedido.where('pedido_id', '==', pedido.id).stream()]
                for item in itens:
                    prod_doc = col_produtos.document(item['produto_id']).get()
                    prod_nome = prod_doc.to_dict()['nome'] if prod_doc.exists else "PRODUTO REMOVIDO"
                    st.write(f"- {item['quantidade']}x {prod_nome} - R$ {item['preco_unitario']:.2f}")
        else:
            st.info("VOCÊ AINDA NÃO FEZ NENHUM PEDIDO")

    if st.button("SAIR", use_container_width=True):
        st.session_state.usuario = None
        st.session_state.pagina = 'home'
        st.session_state.carrinho = []
        st.rerun()
