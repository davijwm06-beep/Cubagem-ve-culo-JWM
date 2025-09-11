import streamlit as st
import openpyxl
import pandas as pd
import unicodedata
from PIL import Image
from io import BytesIO

st.set_page_config(page_title="Cubagem de Veículos", layout="wide")

# ===== SIDEBAR =====
st.sidebar.title("Instruções")
st.sidebar.write("""
Preencha as dimensões do material e o peso unitário.  
Você pode filtrar veículos específicos ou deixar em branco para considerar todos.\n
* Pressionar Enter para aplicar os parâmetros
""")
st.sidebar.write("Site JWM Nossa Frota: [👉Clique aqui](https://jwmlogistica.com.br/frota/)")

# ===== Layout com título e logo =====
col1, col2 = st.columns([6, 1])
with col1:
    st.title("🚚 Cubagem de Veículos - JWM")
with col2:
    try:
        st.image("JWM.png", width=80)
    except Exception:
        st.warning("⚠️ Logo não carregada. Verifique se o arquivo 'JWM.png' está presente.")

# ===== Função de normalização =====
def normaliza(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', s)
        if not unicodedata.category(c).startswith('M')).lower().strip()

# ===== Base de veículos =====
lista_veiculos = [
    {"nome":"Fiorino", "largura": 1.00, "comprimento": 1.40, "altura": 1.00, "peso_max": 500},
    {"nome": "Van Utilitário", "largura": 1.00, "comprimento": 1.60, "altura": 1.00, "peso_max": 500},
    {"nome": "(HR)", "largura": 1.80, "comprimento": 3.00, "altura": 1.90, "peso_max": 1200},
    {"nome": "Veículo 3/4", "largura": 2.10, "comprimento": 5.00, "altura": 2.30, "peso_max": 3000},
    {"nome": "Veículo Toco", "largura": 2.20, "comprimento": 6.00, "altura": 2.70, "peso_max": 6000},
    {"nome": "Vuc", "largura": 1.80, "comprimento": 3.10, "altura": 2.00, "peso_max": 2500},
    {"nome": "Caminhão Truck", "largura": 2.40, "comprimento": 7.50, "altura": 2.70, "peso_max": 12000},
    {"nome": "Combinado (Caminhão+Bi-truck)", "largura": 2.40, "comprimento": 10.00, "altura": 2.70, "peso_max": 18000},
    {"nome": "Carreta Movida a GNV", "largura": 2.40, "comprimento": 12.00, "altura": 2.70, "peso_max": 24000},
    {"nome": "Carreta Slider", "largura": 2.40, "comprimento": 12.00, "altura": 2.70, "peso_max": 24000},
    {"nome": "Carreta Wanderleia", "largura": 2.40, "comprimento": 12.00, "altura": 2.70, "peso_max": 27000},
    {"nome": "Carreta Rodo Trem", "largura": 2.40, "comprimento": 12.00, "altura": 2.70, "peso_max": 74000},
    {"nome": "Bitruck Slider", "largura": 2.40, "comprimento": 10.00, "altura": 2.70, "peso_max": 18000},
    {"nome": "Carreta Grade Baixa", "largura": 2.40, "comprimento": 12.40, "altura": 2.70, "peso_max": 24000},
    {"nome": "Wanderleia Carga Seca", "largura": 2.40, "comprimento": 14.40, "altura": 2.70, "peso_max": 27000}
]

# ===== Entrada do usuário =====
st.subheader("📦 Dimensões do material (em metros)")
col1, col2, col3, col4 = st.columns(4)
with col1:
    comprimentomat = st.number_input("Comprimento (m):", min_value=0.01, format="%.2f")
with col2:
    larguramat = st.number_input("Largura (m):", min_value=0.01, format="%.2f")
with col3:
    alturamat = st.number_input("Altura (m):", min_value=0.01, format="%.2f")
with col4:
    pergpeso = st.number_input("Peso unitário (kg):", min_value=0.01, format="%.2f")

# Filtro de veículos
opcoes = sorted({v["nome"].strip() for v in lista_veiculos})
filtro = st.multiselect("Filtrar veículos específicos (opcional):", opcoes)

# Placeholder para resultados
resultado = st.empty()

# ===== Cálculo =====
if st.button("Calcular"):
    material_vol = comprimentomat * larguramat * alturamat
    st.info(f"Volume do material: **{material_vol:.2f} m³**")
    aproveitamento = 0.90

    veiculos_para_olhar = lista_veiculos if not filtro else [v for v in lista_veiculos if v["nome"] in filtro]

    # 🔎 Checagem se o material excede todos os veículos
    motivos_excesso = {}
    for veiculo in veiculos_para_olhar:
        motivos = []
        if comprimentomat > veiculo["comprimento"]:
            motivos.append(f"Comprimento excede ({comprimentomat}m > {veiculo['comprimento']}m)")
        if larguramat > veiculo["largura"]:
            motivos.append(f"Largura excede ({larguramat}m > {veiculo['largura']}m)")
        if alturamat > veiculo["altura"]:
            motivos.append(f"Altura excede ({alturamat}m > {veiculo['altura']}m)")
        if motivos:
            motivos_excesso[veiculo["nome"]] = motivos

    if len(motivos_excesso) == len(veiculos_para_olhar):
        st.error("🚫 O material excede as dimensões de todos os veículos da frota!")
        for veiculo, motivos in motivos_excesso.items():
            for motivo in motivos:
                st.write(f"• {veiculo}: {motivo}")
    else:
        veiculos_viaveis = []
        quantidade_total = 0

        for veiculo in veiculos_para_olhar:
            if veiculo["nome"] not in motivos_excesso:  # só os que comportam
                cubagem_veiculo = veiculo["comprimento"] * veiculo["largura"] * veiculo["altura"]

                cap_por_volume = int((cubagem_veiculo * aproveitamento) / material_vol)
                cap_por_peso = int(veiculo["peso_max"] / pergpeso)
                qtd = min(cap_por_volume, cap_por_peso)

                if qtd > 0:
                    peso_total = qtd * pergpeso
                    veiculos_viaveis.append({
                        "Veículo": veiculo["nome"],
                        "Cubagem (m³)": round(cubagem_veiculo, 2),
                        "Qtd Máxima (un)": int(qtd),
                        "Peso Total (kg)": round(peso_total, 2)
                    })
                    quantidade_total += int(qtd)

        if veiculos_viaveis:
            df = pd.DataFrame(veiculos_viaveis)
            df["Cubagem (m³)"] = pd.to_numeric(df["Cubagem (m³)"], errors="coerce")
            df["Peso Total (kg)"] = pd.to_numeric(df["Peso Total (kg)"], errors="coerce")
            df = df.drop_duplicates().sort_values(by="Veículo")

            st.success(f"Quantidade total possível: **{quantidade_total} unidades**")

            with resultado.container():
                st.dataframe(df)
                st.bar_chart(df.set_index("Veículo")["Qtd Máxima (un)"])

            def gerar_excel(df):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name="Veículos Viáveis")
                return output.getvalue()

            excel_bytes = gerar_excel(df)
            st.download_button(
                label="📥 Baixar Excel",
                data=excel_bytes,
                file_name="veiculos_viaveis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Nenhum veículo comporta a carga.")
