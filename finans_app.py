import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta
from streamlit_gsheets import GSheetsConnection

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Finansal Takip (Bulut)", layout="wide", page_icon="☁️")

# --- CSS TASARIM ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    .kpi-card { background-color: #262730; border-radius: 8px; padding: 15px; border: 1px solid #444; text-align: center; }
    .kpi-title { font-size: 13px; color: #aaa; margin-bottom: 5px; text-transform: uppercase; }
    .kpi-value { font-size: 22px; font-weight: 700; color: #fff; }
    .kpi-sub { font-size: 11px; margin-top: 4px; opacity: 0.8; }
    .text-green { color: #2ecc71 !important; }
    .text-red { color: #e74c3c !important; }
    .filter-container { background-color: #1E1E1E; padding: 10px 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #333; display: flex; align-items: center; }
</style>
""", unsafe_allow_html=True)

# --- RENK PALETİ ---
COL_INCOME = '#659CE0'
COL_EXPENSE = '#E74C3C'

# --- 1. VERİ ALTYAPISI (GOOGLE SHEETS) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    """Veriyi Google Sheets'ten çeker."""
    try:
        df = conn.read(ttl=0) # ttl=0: Her seferinde taze veri çek
        if df.empty:
            return create_default_data()
        df['TARİH'] = pd.to_datetime(df['TARİH'])
        return df
    except Exception:
        # Bağlantı henüz yoksa veya dosya boşsa örnek veri döndür
        return create_default_data()

def create_default_data():
    """İlk açılış için örnek veriler."""
    return pd.DataFrame([
        {"TARİH": datetime(2026, 1, 5), "YIL": 2026, "AY": "OCAK", "AY_NO": 1, 
         "AÇIKLAMA": "ÖRNEK MAAŞ", "TÜR": "TAHSİLAT", "TUTAR": 115000, "DURUM": "BEKLİYOR"}
    ])

def save_data(df_to_save):
    """Veriyi Google Sheets'e kaydeder."""
    try:
        save_df = df_to_save.copy()
        # Tarihleri Excel/Sheets formatına uygun string yap
        save_df['TARİH'] = save_df['TARİH'].dt.strftime('%Y-%m-%d')
        conn.update(data=save_df)
        st.success("✅ Veriler Google E-Tablolar'a kaydedildi!")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Kayıt hatası: {e}")

# Veriyi Yükle
df = load_data()

# --- 2. SOL MENÜ (KAYIT EKLEME) ---
st.sidebar.header("⚡ Hızlı İşlem Ekle")
with st.sidebar.form("add_form", clear_on_submit=True):
    new_desc = st.text_input("Açıklama", "Yeni İşlem")
    new_type = st.selectbox("Tür", ["ÖDEME", "TAHSİLAT"])
    new_amount = st.number_input("Tutar", min_value=0.0, step=100.0)
    new_status = st.selectbox("Durum", ["BEKLİYOR", "ÖDENDİ"])
    new_date = st.date_input("Tarih", datetime(2026, 1, 15))
    new_installments = st.number_input("Tekrar (Ay)", min_value=1, value=1, step=1)
    
    if st.form_submit_button("Listeye Ekle", use_container_width=True):
        new_rows = []
        months_list = ["OCAK", "ŞUBAT", "MART", "NİSAN", "MAYIS", "HAZİRAN", "TEMMUZ", "AĞUSTOS", "EYLÜL", "EKİM", "KASIM", "ARALIK"]
        current_date = new_date
        for _ in range(new_installments):
            month_name = months_list[current_date.month - 1]
            new_rows.append({
                'TARİH': pd.Timestamp(current_date),
                'YIL': current_date.year,
                'AY': month_name,
                'AY_NO': current_date.month,
                'AÇIKLAMA': new_desc,
                'TÜR': new_type,
                'TUTAR': new_amount,
                'DURUM': new_status
            })
            current_date += relativedelta(months=1)
        
        updated_df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
        save_data(updated_df)

# --- 3. ANA EKRAN ---
st.title("☁️ Finansal Kontrol (Google Sheets)")

# Filtre Alanı
with st.container():
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 4])
    if not df.empty and 'YIL' in df.columns:
        filtre_yil = c1.selectbox("📅 Yıl", sorted(df['YIL'].unique()))
        filtre_ay = c2.selectbox("🗓️ Ay", df[df['YIL'] == filtre_yil]['AY'].unique())
    else:
        st.warning("Veri tablosu boş veya formatı hatalı. Lütfen sol menüden yeni kayıt ekleyin.")
        st.stop()
    st.markdown('</div>', unsafe_allow_html=True)

# Filtreleme
filtered_indices = df[(df['YIL'] == filtre_yil) & (df['AY'] == filtre_ay)].index
filtered_df = df.loc[filtered_indices].copy()
yearly_df = df[df['YIL'] == filtre_yil].copy()

# Hesaplamalar
plan_gelir = filtered_df[filtered_df['TÜR'] == 'TAHSİLAT']['TUTAR'].sum()
plan_gider = filtered_df[filtered_df['TÜR'] == 'ÖDEME']['TUTAR'].sum()
real_gelir = filtered_df[(filtered_df['TÜR'] == 'TAHSİLAT') & (filtered_df['DURUM'] == 'ÖDENDİ')]['TUTAR'].sum()
real_gider = filtered_df[(filtered_df['TÜR'] == 'ÖDEME') & (filtered_df['DURUM'] == 'ÖDENDİ')]['TUTAR'].sum()
kalan_gelir = plan_gelir - real_gelir
kalan_gider = plan_gider - real_gider

# KPI Kartları
k1, k2, k3, k4 = st.columns(4)
k1.markdown(f'<div class="kpi-card"><div class="kpi-title">Planlanan Gelir</div><div class="kpi-value">{plan_gelir:,.0f} ₺</div><div class="kpi-sub" style="color:#659CE0">Bekleyen: {kalan_gelir:,.0f}</div></div>', unsafe_allow_html=True)
k2.markdown(f'<div class="kpi-card"><div class="kpi-title">Planlanan Gider</div><div class="kpi-value">{plan_gider:,.0f} ₺</div><div class="kpi-sub" style="color:#E74C3C">Bekleyen: {kalan_gider:,.0f}</div></div>', unsafe_allow_html=True)
k3.markdown(f'<div class="kpi-card"><div class="kpi-title">Kasa Giriş</div><div class="kpi-value text-green">{real_gelir:,.0f} ₺</div><div class="kpi-sub">Tahsil Edilen</div></div>', unsafe_allow_html=True)
k4.markdown(f'<div class="kpi-card"><div class="kpi-title">Kasa Çıkış</div><div class="kpi-value text-red">{real_gider:,.0f} ₺</div><div class="kpi-sub">Ödenen</div></div>', unsafe_allow_html=True)

st.markdown("---")

# Grafikler
g1, g2 = st.columns(2)
with g1:
    summary_data = pd.DataFrame({
        "Durum": ["Tahsil Edilen", "Bekleyen Alacak", "Ödenen", "Bekleyen Borç"],
        "Tutar": [real_gelir, kalan_gelir, real_gider, kalan_gider],
        "Renk": ["#2ECC71", "#1D8348", "#E74C3C", "#922B21"]
    })
    fig = px.pie(summary_data, values='Tutar', names='Durum', hole=0.6, color='Durum', color_discrete_map={k:v for k,v in zip(summary_data.Durum, summary_data.Renk)})
    fig.update_layout(height=300, margin=dict(t=20, b=20), showlegend=True, legend=dict(orientation="h", y=-0.1))
    st.plotly_chart(fig, use_container_width=True)

with g2:
    trend = yearly_df.groupby(['AY', 'AY_NO', 'TÜR'])['TUTAR'].sum().reset_index().sort_values('AY_NO')
    fig2 = px.line(trend, x='AY', y='TUTAR', color='TÜR', markers=True, color_discrete_map={"TAHSİLAT": COL_INCOME, "ÖDEME": COL_EXPENSE})
    fig2.update_layout(height=300, margin=dict(t=20, b=20), xaxis_title=None)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# --- LİSTE VE DÜZENLEME ---
tab_monthly, tab_yearly = st.tabs(["📝 Aylık Liste (Düzenle)", "📅 Yıllık Liste"])

with tab_monthly:
    col_save, col_space = st.columns([1, 6])
    with col_save:
        save_clicked = st.button("💾 Google Sheets'e Kaydet", type="primary")

    edited_df = st.data_editor(
        filtered_df,
        column_config={
            "TARİH": st.column_config.DateColumn("Tarih", format="DD.MM.YYYY", width="medium"),
            "AÇIKLAMA": st.column_config.TextColumn("Açıklama", width="large"),
            "TÜR": st.column_config.SelectboxColumn("İşlem Türü", options=["TAHSİLAT", "ÖDEME"], width="medium"),
            "TUTAR": st.column_config.ProgressColumn("Tutar", format="%d ₺", min_value=0, max_value=150000, width="medium"),
            "DURUM": st.column_config.SelectboxColumn("Durum", options=["BEKLİYOR", "ÖDENDİ"], width="small", required=True),
        },
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        key="editor_main"
    )

    if save_clicked:
        # Değişiklikleri ana DF'e yansıt
        df.loc[edited_df.index] = edited_df
        # Google Sheets'e gönder
        save_data(df)

with tab_yearly:
    st.subheader(f"📅 {filtre_yil} Yılı Genel Bakış")
    st.dataframe(yearly_df.sort_values("TARİH"), hide_index=True, use_container_width=True)
