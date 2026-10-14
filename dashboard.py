import streamlit as st
import serial
import time
from PIL import Image

# Configuração da página
st.set_page_config(page_title="Projeto de Aquapônia", layout="wide")

# --- MEMÓRIA DE ESTADO (Para os botões Iniciar/Parar e últimos valores) ---
if "monitorando" not in st.session_state:
    st.session_state.monitorando = True  

if "ultimos_dados" not in st.session_state:
    st.session_state.ultimos_dados = {
        "temp_agua": 26.1,
        "temp_ar": 28.5,
        "umid_ar": 65.0,
        "distancia_tanque": 16.0 
    }

# --- ESTILO CSS MODERNO ---
st.markdown("""
<style>
.stApp { background: linear-gradient(180deg, #101C33 0%, #1A2C4C 100%) !important; }
header[data-testid="stHeader"] { background: transparent !important; }

.header-box { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 16px; padding: 18px 25px; margin-bottom: 15px; }
.sensor-card { background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 18px; padding: 24px 20px; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.35); text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: space-between; height: 450px; box-sizing: border-box; }
.topo-card { width: 100%; }
.titulo-sensor { font-size: 16px; font-weight: 700; color: #E2E8F0; letter-spacing: 1.2px; text-transform: uppercase; min-height: 44px; display: flex; align-items: center; justify-content: center; margin-bottom: 4px; }
.valor-destaque { font-size: 34px; font-weight: 800; color: #FFFFFF; margin-bottom: 10px; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
.bloco-medidor { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; }
.linha-tanque { display: flex; flex-direction: row; align-items: center; justify-content: center; width: 270px; margin: 0 auto 16px auto; }
.escala { width: 45px; height: 220px; display: flex; flex-direction: column; justify-content: space-between; color: #94A3B8; font-size: 12px; font-weight: 600; text-align: right; padding: 4px 10px 4px 0; box-sizing: border-box; }
.compensacao-direita { width: 45px; height: 220px; }
.visor-tanque { background-color: #D3D8DE; border-radius: 12px; width: 180px; height: 220px; position: relative; overflow: hidden; box-shadow: inset 0 4px 10px rgba(0,0,0,0.25); border: 3px solid #CBD5E1; box-sizing: border-box; }
.visor-tanque::after { content: ""; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(to bottom, transparent 24%, rgba(0,0,0,0.06) 25%, transparent 26%, transparent 49%, rgba(0,0,0,0.06) 50%, transparent 51%, transparent 74%, rgba(0,0,0,0.06) 75%, transparent 76%); pointer-events: none; }
.torre-verde { background: linear-gradient(180deg, #10B981 0%, #0A893D 100%); width: 66%; position: absolute; bottom: 0; left: 17%; border-radius: 8px 8px 0 0; box-shadow: 0 -2px 10px rgba(16, 185, 129, 0.5); transition: height 0.2s ease-out; }
.torre-alerta { background: linear-gradient(180deg, #EF4444 0%, #B91C1C 100%) !important; box-shadow: 0 -2px 10px rgba(239, 68, 68, 0.5) !important; }

/* Botões */
div.stButton > button { width: 100%; height: 46px; background-color: #FFFFFF !important; color: #101C33 !important; border-radius: 10px !important; border: 2px solid #FFFFFF !important; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important; transition: all 0.2s ease-in-out !important; }
div.stButton > button p { color: #101C33 !important; font-weight: 800 !important; font-size: 15px !important; letter-spacing: 0.5px !important; }
div.stButton > button:hover:not(:disabled) { background-color: #F8FAFC !important; border-color: #10B981 !important; transform: translateY(-2px); box-shadow: 0 6px 16px rgba(16, 185, 129, 0.35) !important; }
div.stButton > button:disabled { background-color: rgba(255, 255, 255, 0.2) !important; border: 1px solid rgba(255, 255, 255, 0.25) !important; box-shadow: none !important; cursor: not-allowed !important; }
div.stButton > button:disabled p { color: rgba(255, 255, 255, 0.55) !important; }

/* Rodapé Acadêmico Atualizado (Mesmo cinza dos gráficos e letra escura) */
.rodape-academico {
    background-color: #D3D8DE;
    border: 3px solid #CBD5E1;
    border-radius: 12px;
    padding: 20px;
    margin-top: 40px;
    margin-bottom: 20px;
    text-align: center;
    box-shadow: inset 0 4px 10px rgba(0,0,0,0.1);
}
.rodape-texto {
    color: #101C33;
    font-size: 16px;
    font-weight: 600;
    margin: 0;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

# --- CABEÇALHO INSTITUCIONAL E BARRA DE CONTROLE ---
col_esq, col_centro, col_dir = st.columns([1.2, 4.6, 1.2], vertical_alignment="center")

with col_esq:
    try:
        st.image(Image.open("logo ufrpe.png"), use_container_width=True)
    except FileNotFoundError: pass

cor_subtitulo = "#34D399" if st.session_state.monitorando else "#FBBF24"
texto_subtitulo = "● MONITORAMENTO EM TEMPO REAL — ATIVO" if st.session_state.monitorando else "⏸ MONITORAMENTO PAUSADO — DADOS CONGELADOS"

with col_centro:
    st.markdown(f"""
<div class="header-box">
<h1 style='text-align: center; color: #FFFFFF; font-size: 36px; margin: 0; letter-spacing: 1.5px;'>
PROJETO DE AQUAPÔNIA
</h1>
<p style='text-align: center; color: {cor_subtitulo}; font-size: 15px; font-weight: 600; margin: 5px 0 0 0; letter-spacing: 3px;'>
{texto_subtitulo}
</p>
</div>
""", unsafe_allow_html=True)
    
    espaco_esq, btn_col1, btn_col2, espaco_dir = st.columns([0.8, 2, 2, 0.8], gap="medium")
    with btn_col1:
        if st.button("▶️ Iniciar / Retomar", disabled=st.session_state.monitorando, use_container_width=True):
            st.session_state.monitorando = True
            st.rerun()
    with btn_col2:
        if st.button("⏹️ Pausar Leitura", disabled=not st.session_state.monitorando, use_container_width=True):
            st.session_state.monitorando = False
            st.rerun()

with col_dir:
    try:
        st.image(Image.open("logo codai.avif"), use_container_width=True)
    except FileNotFoundError: pass

st.markdown("<br>", unsafe_allow_html=True)

# --- ESPAÇOS E FUNÇÕES DE RENDERIZAÇÃO ---
placeholder_alerta = st.empty()

def renderizar_card(titulo, valor_texto, porcentagem, escala_max, escala_meio, escala_min, status, em_alerta=False):
    cor_texto = "#EF4444" if em_alerta else "#34D399"
    cor_bg = "rgba(239, 68, 68, 0.2)" if em_alerta else "rgba(16, 185, 129, 0.2)"
    cor_borda = "rgba(239, 68, 68, 0.4)" if em_alerta else "rgba(16, 185, 129, 0.4)"
    classe_torre = "torre-verde torre-alerta" if em_alerta else "torre-verde"
    
    return f"""
<div class="sensor-card">
<div class="topo-card">
<div class="titulo-sensor">{titulo}</div>
<div class="valor-destaque">{valor_texto}</div>
</div>
<div class="bloco-medidor">
<div class="linha-tanque">
<div class="escala">
<span>{escala_max}</span>
<span>{escala_meio}</span>
<span>{escala_min}</span>
</div>
<div class="visor-tanque">
<div class="{classe_torre}" style="height: {porcentagem}%;"></div>
</div>
<div class="compensacao-direita"></div>
</div>
<div style="display: flex; align-items: center; justify-content: center; width: 180px; margin: 0 auto; padding: 7px 0; border-radius: 20px; font-size: 13px; font-weight: 700; background: {cor_bg}; color: {cor_texto}; border: 1px solid {cor_borda}; letter-spacing: 0.5px; box-sizing: border-box;">
{status}
</div>
</div>
</div>
"""

def atualizar_tela(placeholder_alerta, placeholder_agua, placeholder_clima, placeholder_tanque, dados):
    temp_agua = dados["temp_agua"]
    temp_ar = dados["temp_ar"]
    umid_ar = dados["umid_ar"]
    distancia = dados["distancia_tanque"]

    if distancia < 10:
        placeholder_alerta.markdown("""
        <div style="background-color: rgba(239, 68, 68, 0.15); border: 2px solid #EF4444; border-radius: 12px; padding: 15px; margin-bottom: 25px; text-align: center; box-shadow: 0 4px 15px rgba(239,68,68,0.2);">
            <h3 style="color: #EF4444; margin: 0; font-size: 22px; letter-spacing: 1px;">🚨 ALERTA CRÍTICO: BOMBA DESLIGADA AUTOMATICAMENTE</h3>
            <p style="color: #FCA5A5; margin: 5px 0 0 0; font-weight: 600; font-size: 15px;">O nível do tanque caiu para a zona de perigo (< 50%). O relé cortou a energia da bomba por segurança.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        placeholder_alerta.markdown("""
        <div style="background-color: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 12px; margin-bottom: 25px; text-align: center;">
            <p style="color: #34D399; margin: 0; font-weight: 700; font-size: 15px; letter-spacing: 1px;">⚙️ SISTEMA DE BOMBEAMENTO ATIVO E OPERACIONAL</p>
        </div>
        """, unsafe_allow_html=True)

    porcentagem_agua = min(max((temp_agua / 50.0) * 100, 0), 100)
    alerta_agua = temp_agua < 20 or temp_agua > 30
    placeholder_agua.markdown(renderizar_card("🌡️ Temperatura da Água", f"{temp_agua:.1f} °C", porcentagem_agua, "50°C", "25°C", "0°C", "⚠️ ATENÇÃO" if alerta_agua else "● FAIXA IDEAL", alerta_agua), unsafe_allow_html=True)

    placeholder_clima.markdown(renderizar_card("💨 Temp. e Umidade do Ar", f"{temp_ar:.1f}°C | {umid_ar:.0f}%", umid_ar, "100%", "50%", "0%", "● CLIMA ESTÁVEL"), unsafe_allow_html=True)

    porcentagem_tanque = min(max((distancia / 20.0) * 100, 0), 100)
    alerta_tanque = distancia < 10
    placeholder_tanque.markdown(renderizar_card("💧 Nível do Tanque", f"{porcentagem_tanque:.0f} %", porcentagem_tanque, "100%", "50%", "0%", "⚠️ NÍVEL PERIGOSO" if alerta_tanque else "● NÍVEL NORMAL", alerta_tanque), unsafe_allow_html=True)

# --- COLUNAS DOS SENSORES ---
col1, col2, col3 = st.columns(3, gap="large")
placeholder_agua = col1.empty()
placeholder_clima = col2.empty()
placeholder_tanque = col3.empty()

# Desenha o estado inicial
atualizar_tela(placeholder_alerta, placeholder_agua, placeholder_clima, placeholder_tanque, st.session_state.ultimos_dados)

# --- RODAPÉ ACADÊMICO ---
st.markdown("""
<div class="rodape-academico">
    <p class="rodape-texto">
        O projeto foi realizado pelos estudantes do curso Técnico em Agronomia do CODAI (UFRPE) e os discentes do curso de Computação da (UFRPE), supervisionado pelo professor: <strong>Marcílio Ferreira de Souza Júnior CODAI (UFRPE)</strong>.
    </p>
</div>
""", unsafe_allow_html=True)

# --- LÓGICA DE EXECUÇÃO EM TEMPO REAL ---
PORTA_SERIAL = 'COM9' 
BAUD_RATE = 9600

@st.cache_resource
def iniciar_serial():
    try:
        return serial.Serial(PORTA_SERIAL, BAUD_RATE, timeout=1)
    except Exception:
        return None

arduino = iniciar_serial()

if arduino:
    if st.session_state.monitorando:
        arduino.reset_input_buffer()
        
        while st.session_state.monitorando:
            if arduino.in_waiting > 0:
                atualizou_dado = False
                
                while arduino.in_waiting > 0:
                    linha = arduino.readline().decode('utf-8', errors='ignore').strip()
                    try:
                        if "Temperatura da agua:" in linha:
                            st.session_state.ultimos_dados["temp_agua"] = float(linha.split(":")[1])
                            atualizou_dado = True
                        elif "Temperatura do ar:" in linha:
                            st.session_state.ultimos_dados["temp_ar"] = float(linha.split(":")[1])
                            atualizou_dado = True
                        elif "Umidade do ar:" in linha:
                            st.session_state.ultimos_dados["umid_ar"] = float(linha.split(":")[1])
                            atualizou_dado = True
                        elif "Distancia do tanque:" in linha:
                            st.session_state.ultimos_dados["distancia_tanque"] = float(linha.split(":")[1])
                            atualizou_dado = True
                    except ValueError:
                        pass
                
                if atualizou_dado:
                    atualizar_tela(placeholder_alerta, placeholder_agua, placeholder_clima, placeholder_tanque, st.session_state.ultimos_dados)
                    
            time.sleep(0.05)
    else:
        st.info("⏸️ Leitura pausada. Clique em **'▶️ Iniciar / Retomar'**.")
else:
    st.warning(f"⚠️ Modo de Demonstração (Arduino desconectado da porta {PORTA_SERIAL}).")