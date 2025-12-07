import streamlit as st
import pandas as pd
import io
import xlsxwriter
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Finansal Yönetim Paneli V4", layout="wide", page_icon="🚀")

# --- CSS (GÖRSEL TASARIM & DARK MODE UYUMU) ---
st.markdown("""
<style>
    /* Ana kapsayıcı ayarı */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* KPI KARTLARI TASARIMI */
    .kpi-card {
        background-color: #262730; /* Koyu tema uyumlu arka plan */
        border-radius: 10px;
        padding: 15px;
        margin: 5px;
        border: 1px solid #444;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
        text-align: center;
        transition: transform 0.2s;
    }
    .kpi-card:hover {
        transform: scale(1.02);
        border-color: #666;
    }
    .kpi-title {
        font-size: 14px;
        color: #b0b0b0;
        margin-bottom: 5px;
        text-transform: uppercase;
        font-weight: 600;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: bold;
        color: #ffffff;
        margin: 0;
    }
    .kpi-sub {
        font-size: 12px;
        margin-top: 5px;
    }
    
    /* Renk Kodları */
    .text-green { color: #2ecc71; }
    .text-red { color: #e74c3c; }
    .text-blue { color: #3498db; }
    .text-orange { color: #f39c12; }
    
    .border-green { border-left: 5px solid #2ecc71 !important; }
    .border-red { border-left: 5px solid #e74c3c !important; }
    .border-blue { border-left: 5px solid #3498db !important; }
    .border-orange { border-left: 5px solid #f39c12 !important; }

</style>
""", unsafe_allow_html=True)

# --- RENK PALETİ ---
COL_DARK_NAVY   = '#395168'
COL_INCOME_BLUE = '#659CE0'
COL_EXPENSE_RED = '#E74C3C'
COL_SUCCESS     = '#2ECC71'
COL_PENDING     = '#F1C40F'

# --- 1. VERİ ALTYAPISI ---
if 'df' not in st.session_state:
    rows = []
    years = [2026, 2027]
    months = ["OCAK", "ŞUBAT", "MART", "NİSAN", "MAYIS", "HAZİRAN", 
              "TEMMUZ", "AĞUSTOS", "EYLÜL", "EKİM", "KASIM", "ARALIK"]

    standard_items = [
        {"AÇIKLAMA": "MAAŞ", "TÜR": "TAHSİLAT", "TUTAR": 115000, "GÜN": 5, "DURUM": "BEKLİYOR"},
        {"AÇIKLAMA": "TEKİRDAĞ KİRA", "TÜR": "TAHSİLAT", "TUTAR": 17500, "GÜN": 22, "DURUM": "BEKLİYOR"},
        {"AÇIKLAMA": "KONUT KREDİSİ", "TÜR": "ÖDEME", "TUTAR": 3611, "GÜN": 10, "DURUM": "BEKLİYOR"},
        {"AÇIKLAMA": "KREDİ KARTI", "TÜR": "ÖDEME", "TUTAR": 40000, "GÜN": 7, "DURUM": "BEKLİYOR"}
    ]

    for year in years:
        for i, month_name in enumerate(months, 1):
            current_items = standard_items.copy()
            if year == 2026 and i == 1:
                current_items.append({"AÇIKLAMA": "ZİRAAT KREDİ", "TÜR": "ÖDEME", "TUTAR": 9031, "GÜN": 6, "DURUM": "BEKLİYOR"})
            
            for item in current_items:
                date_obj = datetime(year, i, item["GÜN"])
                rows.append({
                    'TARİH': date_obj,
                    'YIL': year,
                    'AY': month_name,
                    'AY_NO': i,
                    'AÇIKLAMA': item['AÇIKLAMA'],
                    'TÜR': item['TÜR'],
                    'TUTAR': item['TUTAR'],
                    'DURUM': item['DURUM']
                })
    st.session_state.df = pd.DataFrame(rows)

df = st.session_state.df

# --- 2. SIDEBAR ---
st.sidebar.header("⚡ Hızlı İşlem Ekle")
with st.sidebar.form("add_form", clear_on_submit=True):
    new_desc = st.text_input("Açıklama", "Yeni İşlem")
    new_type = st.selectbox("Tür", ["ÖDEME", "TAHSİLAT"])
    new_amount = st.number_input("Tutar", min_value=0.0, step=100.0)
    new_status = st.selectbox("Durum", ["BEKLİYOR", "ÖDENDİ"])
    new_date = st.date_input("Tarih", datetime(2026, 1, 15))
    new_installments = st.number_input("Taksit", min_value=1, value=1, step=1)
    
    if st.form_submit_button("Kaydet"):
        new_rows = []
        months_list = ["OCAK", "ŞUBAT", "MART", "NİSAN", "MAYIS", "HAZİRAN", 
                        "TEMMUZ", "AĞUSTOS", "EYLÜL", "EKİM", "KASIM", "ARALIK"]
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
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_rows)], ignore_index=True)
        st.rerun()

# --- 3. ANA DASHBOARD ---

# Üst Başlık ve Filtreler
c_title, c_filt1, c_filt2 = st.columns([6, 1, 1])
with c_title: st.subheader("📊 Finansal Kontrol Merkezi")
with c_filt1: filtre_yil = st.selectbox("Yıl", sorted(df['YIL'].unique()), label_visibility="collapsed")
with c_filt2: filtre_ay = st.selectbox("Ay", df[df['YIL'] == filtre_yil]['AY'].unique(), label_visibility="collapsed")

# Veri Hazırlığı
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

# --- KPI KARTLARI (HTML/CSS İLE ÖZEL TASARIM) ---
# Burada st.metric yerine kendi HTML kartlarımızı oluşturuyoruz.
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    st.markdown(f"""
    <div class="kpi-card border-blue">
        <div class="kpi-title">📋 Planlanan Gelir</div>
        <div class="kpi-value">{plan_gelir:,.0f} ₺</div>
        <div class="kpi-sub text-blue">Bekleyen: {kalan_gelir:,.0f} ₺</div>
    </div>
    """, unsafe_allow_html=True)

with col_kpi2:
    st.markdown(f"""
    <div class="kpi-card border-red">
        <div class="kpi-title">📉 Planlanan Gider</div>
        <div class="kpi-value">{plan_gider:,.0f} ₺</div>
        <div class="kpi-sub text-red">Bekleyen: {kalan_gider:,.0f} ₺</div>
    </div>
    """, unsafe_allow_html=True)

with col_kpi3:
    st.markdown(f"""
    <div class="kpi-card border-green">
        <div class="kpi-title">💰 Kasaya Giren</div>
        <div class="kpi-value text-green">{real_gelir:,.0f} ₺</div>
        <div class="kpi-sub">Gerçekleşen Tahsilat</div>
    </div>
    """, unsafe_allow_html=True)

with col_kpi4:
    st.markdown(f"""
    <div class="kpi-card border-orange">
        <div class="kpi-title">💸 Kasadan Çıkan</div>
        <div class="kpi-value text-orange">{real_gider:,.0f} ₺</div>
        <div class="kpi-sub">Gerçekleşen Ödeme</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- GRAFİKLER ---
col_chart1, col_chart2 = st.columns([1, 1])

with col_chart1:
    st.markdown(f"**🗓️ {filtre_ay} Ayı Özeti**")
    summary_data = pd.DataFrame({
        "Tip": ["Kasa (Giriş)", "Bekleyen (Gelir)", "Kasa (Çıkış)", "Bekleyen (Gider)"],
        "Tutar": [real_gelir, kalan_gelir, real_gider, kalan_gider],
        "Renk": ["#2ECC71", "#145A32", "#E74C3C", "#641E16"] 
    })
    
    # Donut Chart - Daha modern renkler
    fig_summary = px.pie(summary_data, values='Tutar', names='Tip', hole=0.6, 
                         color='Tip', color_discrete_map={
                             "Kasa (Giriş)": "#2ECC71",    # Parlak Yeşil
                             "Bekleyen (Gelir)": "#1D8348", # Koyu Yeşil
                             "Kasa (Çıkış)": "#E74C3C",    # Parlak Kırmızı
                             "Bekleyen (Gider)": "#922B21"  # Koyu Kırmızı
                         })
    fig_summary.update_layout(showlegend=True, margin=dict(t=20, b=20, l=20, r=20), height=320, 
                              legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
    st.plotly_chart(fig_summary, use_container_width=True)

with col_chart2:
    st.markdown(f"**📈 {filtre_yil} Yıllık Nakit Akışı**")
    trend_data = yearly_df.groupby(['AY', 'AY_NO', 'TÜR'])['TUTAR'].sum().reset_index().sort_values('AY_NO')
    fig_trend = px.line(trend_data, x="AY", y="TUTAR", color="TÜR", markers=True,
                        color_discrete_map={"TAHSİLAT": COL_INCOME_BLUE, "ÖDEME": COL_EXPENSE_RED})
    fig_trend.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=320, xaxis_title=None,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_trend, use_container_width=True)

# --- 4. VERİ LİSTESİ ---
tab_monthly, tab_yearly = st.tabs(["📝 Aylık Liste (Düzenle)", "📅 Yıllık Liste"])

with tab_monthly:
    col_edit1, col_edit2 = st.columns([3, 1])
    
    with col_edit1:
        st.info("💡 İpucu: Durum sütunundan 'ÖDENDİ' seçerseniz yukarıdaki grafikler anında güncellenir (Kaydet butonuna basınca).")
        edited_df = st.data_editor(
            filtered_df,
            column_config={
                "TARİH": st.column_config.DateColumn("Tarih", format="DD.MM.YYYY"),
                "TUTAR": st.column_config.NumberColumn("Tutar", format="%d ₺"),
                "TÜR": st.column_config.SelectboxColumn("Tür", options=["TAHSİLAT", "ÖDEME"]),
                "DURUM": st.column_config.SelectboxColumn("Durum", options=["BEKLİYOR", "ÖDENDİ"]),
            },
            use_container_width=True,
            num_rows="dynamic",
            key="editor_monthly",
            hide_index=True,
            height=400
        )
    
    with col_edit2:
        st.write("") 
        st.write("") 
        if st.button("💾 DEĞİŞİKLİKLERİ KAYDET", type="primary", use_container_width=True):
            try:
                main_df = st.session_state.df
                main_df.loc[edited_df.index] = edited_df
                st.session_state.df = main_df
                st.success("✅ Tablo Güncellendi!")
                st.rerun()
            except Exception as e:
                st.error(f"Hata: {e}")
        
        st.divider()
        
        # Excel İndir
        def generate_excel():
            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            st.session_state.df.to_excel(writer, sheet_name='TÜM_VERİLER', index=False)
            writer.close()
            return output.getvalue()

        st.download_button(
            label="📥 Excel İndir",
            data=generate_excel(),
            file_name="Finans_Raporu.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

with tab_yearly:
    st.dataframe(
        yearly_df.sort_values(by="TARİH"),
        column_config={
                "TARİH": st.column_config.DateColumn("Tarih", format="DD.MM.YYYY"),
                "TUTAR": st.column_config.NumberColumn("Tutar", format="%d ₺"),
            },
        use_container_width=True,
        hide_index=True
    )
