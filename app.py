import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw
import numpy as np
from datetime import datetime
import os

st.set_page_config(page_title="Simulador de Titulação - Fenolftaleína", layout="centered")

st.title("🧪 Simulador de Titulação Ácido-Base")
st.write("Determine a concentração da sua amostra individualizada realizando a titulação manualmente.")

# --- 1. IDENTIFICAÇÃO E VALOR INDIVIDUALIZADO ---
st.sidebar.header("Identificação")
nome = st.sidebar.text_input("Nome Completo:")
matricula_input = st.sidebar.text_input("Matrícula (somente números):")

if not nome or not matricula_input or not matricula_input.isdigit():
    st.warning("⚠️ Insira seu nome e matrícula na barra lateral para carregar sua amostra específica.")
    st.stop()

matricula = int(matricula_input)
ultimos_2 = matricula % 100

# Volume exato de equivalência individual (ex: entre 12.0 mL e 21.9 mL)
v_equivalencia_exato = round(12.0 + (ultimos_2 * 0.1), 2)
conc_titulante_NaOH = 0.100  # mol/L
v_aliquota_analito = 25.0    # mL de HCl na Erlenmeyer

st.sidebar.markdown("---")
st.sidebar.subheader("Dados do Ensaio")
st.sidebar.write(f"• **Alíquota de HCl ($V_A$):** {v_aliquota_analito} mL")
st.sidebar.write(f"• **Concentração de NaOH ($C_B$):** {conc_titulante_NaOH} mol/L")
st.sidebar.write("• **Indicador:** Fenolftaleína")

# --- 2. ESTADO DA BURETA (SESSION STATE) ---
if 'v_adicionado' not in st.session_state:
    st.session_state.v_adicionado = 0.0

# --- CONTROLES DE ADIÇÃO DE TITULANTE ---
st.header("1. Operação da Bureta")

col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
with col_btn1:
    if st.button("➕ Adicionar 0.1 mL"):
        st.session_state.v_adicionado = round(st.session_state.v_adicionado + 0.1, 2)
with col_btn2:
    if st.button("➕ Adicionar 0.5 mL"):
        st.session_state.v_adicionado = round(st.session_state.v_adicionado + 0.5, 2)
with col_btn3:
    if st.button("➕ Adicionar 2.0 mL"):
        st.session_state.v_adicionado = round(st.session_state.v_adicionado + 2.0, 2)
with col_btn4:
    if st.button("🔄 Zerar Bureta"):
        st.session_state.v_adicionado = 0.0

v_atual = st.session_state.v_adicionado
st.subheader(f"Volume de NaOH adicionado: **{v_atual:.2f} mL**")

# --- 3. LÓGICA DA COR DA FENOLFTALEÍNA ---
# Diferença entre o volume adicionado e o ponto de viragem
delta_v = v_atual - v_equivalencia_exato

if delta_v < -0.2:
    # Antes do ponto: Incolor
    cor_solucao = (240, 240, 250, 255)
    estado_texto = "⚪ Solução Incolor (Meio Ácido)"
elif -0.2 <= delta_v <= 0.2:
    # Ponto de Equivalência (Viragem): Rosa Leve/Pálido
    cor_solucao = (255, 182, 193, 255)
    estado_texto = "🌸 Solução Rosa Pálido Persistente (Ponto de Viragem Alcançado!)"
else:
    # Após o ponto: Rosa Choque / Violeta (Excesso de base)
    cor_solucao = (238, 13, 130, 255)
    estado_texto = "🌺 Solução Rosa Intenso / Violeta (Supertitulada / Excesso de NaOH)"

st.info(f"**Estado da Solução:** {estado_texto}")

# --- 4. DESENHO DINÂMICO DA BURETA E ERLENMEYER (PIL) ---
def desenhar_titulacao(v_adicionado, cor_rgb):
    img = Image.new("RGBA", (300, 350), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Desenhando a Bureta (Tubo superior)
    draw.rectangle([135, 20, 165, 180], outline="black", width=2)
    # Menisco/Líquido na Bureta (diminui conforme v_adicionado aumenta)
    altura_liquido = max(30, 170 - int(v_adicionado * 5))
    draw.rectangle([137, altura_liquido, 163, 178], fill=(173, 216, 230, 180))
    
    # Torneira da Bureta
    draw.rectangle([130, 180, 170, 188], fill="gray")
    draw.line([150, 188, 150, 210], fill="black", width=2)

    # Gota caindo se estiver adicionando
    if v_adicionado > 0:
        draw.ellipse([147, 215, 153, 223], fill=(173, 216, 230, 255))

    # Desenhando o Erlenmeyer (Frasco inferior)
    pontos_erlenmeyer = [(150, 230), (110, 260), (70, 320), (230, 320), (190, 260)]
    draw.polygon(pontos_erlenmeyer, outline="black", fill=cor_rgb, width=2)

    return img

imagem_simulacao = desenhar_titulacao(v_atual, cor_solucao)
st.image(imagem_simulacao, caption="Montagem Experimental da Titulação", width=300)

st.divider()

# --- 5. TAREFA E TRANSCRIÇÃO DOS CÁLCULOS ---
st.header("2. Registro dos Resultados e Cálculos")
st.write("Com base no volume final de titulação observado acima, realize os cálculos no seu caderno e insira os dados abaixo:")

with st.form("form_titulacao"):
    v_final_aluno = st.number_input("Volume de NaOH no ponto de viragem (mL):", step=0.01)
    n_mols_naoh = st.number_input("Número de mols de NaOH consumidos ($n_{NaOH}$):", format="%.5f")
    conc_hcl_aluno = st.number_input("Concentração molar calculada do HCl ($mol/L$):", format="%.4f")
    
    file_manuscrito = st.file_uploader("Upload do manuscrito demonstrando as equações e cálculos:", type=["jpg", "jpeg", "png"])
    
    submeter = st.form_submit_button("🚀 Enviar Resultados da Titulação")

if submeter:
    if not file_manuscrito:
        st.error("Por favor, anexe a foto da resolução manuscrita.")
    else:
        # Registro dos dados
        registro = {
            "Nome": nome.strip().title(),
            "Matricula": matricula,
            "DataEnvio": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "V_Equivalencia_Gabarito": v_equivalencia_exato,
            "V_Encontrado_Aluno": v_final_aluno,
            "Mols_NaOH_Aluno": n_mols_naoh,
            "Conc_HCl_Aluno": conc_hcl_aluno
        }
        
        csv_file = "titulacoes_alunos.csv"
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
            df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)
        else:
            df = pd.DataFrame([registro])
            
        df.sort_values(by="Nome", ascending=True).to_csv(csv_file, index=False)
        st.success("✅ Titulação registrada e submetida com sucesso!")
