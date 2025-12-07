import streamlit as st
import pandas as pd
import io
import xlsxwriter
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Finansal Yönetim Paneli V3", layout="wide", page_icon="🚀")

# --- CSS İLE GÖRÜNÜMÜ KÜÇÜLTME (COMPACT VIEW) ---
st.markdown("""
<style>
    /* Ana blok boşluğunu azalt */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1rem;
    }
    /* Metrik kutularını biraz küçült ve sıkılaştır */
    div[data-testid="stMetric"] {
        background-color: #f9f9f9;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #e0e0e0;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 14px !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 20px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- RENK PALETİ ---
COL_DARK_NAVY   = '#395168'
COL_INCOME_BLUE = '#659CE0'
COL_EXPENSE_RED = '#E74C3C'
COL_SUCCESS     = '#2ECC71'
COL_PENDING     = '#F1C40F'

# --- 1. VERİ ALTYAPISI (SESSION STATE) ---
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

# --- 2. SIDEBAR: İŞLEM EKLEME ---
st.sidebar.header("⚡ Hızlı Ekle")
with st.sidebar.form("add_form", clear_on_submit=True):
    new_desc = st.text_input("Açıklama", "Yeni İşlem")
    new_type = st.selectbox("Tür", ["ÖDEME", "TAHSİLAT"])
    new_amount = st.number_input("Tutar", min_value=0.0, step=100.0)
    new_status = st.selectbox("Durum", ["BEKLİYOR", "ÖDENDİ"])
    new_date = st.date_input("Tarih", datetime(2026, 1, 15))
    new_installments = st.number_input("Taksit", min_value=1, value=1, step=1)
    
    submit_btn = st.form_submit_button("Ekle")

    if submit_btn:
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
        st.success("Eklendi")
        st.rerun()

# --- 3. ANA DASHBOARD ---

# Üst Başlık ve Filtreler (Yan Yana Compact)
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

# KPI KARTLARI (KÜÇÜLTÜLMÜŞ & YAN YANA)
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Planlanan Gelir", f"{plan_gelir:,.0f} ₺", f"Kalan: {kalan_gelir:,.0f}")
kpi2.metric("Planlanan Gider", f"{plan_gider:,.0f} ₺", f"Kalan: {kalan_gider:,.0f}", delta_color="inverse")
kpi3.metric("Gerçekleşen (Giren)", f"{real_gelir:,.0f} ₺", delta_color="normal")
kpi4.metric("Gerçekleşen (Çıkan)", f"{real_gider:,.0f} ₺", delta_color="inverse")

st.markdown("---")

# --- GRAFİKLER (ANA EKRANDA YAN YANA) ---
col_chart1, col_chart2 = st.columns([1, 1])

with col_chart1:
    # 1. Grafik: Aylık Gelir Gider Dengesi (Basit Bar)
    st.markdown(f"**🗓️ {filtre_ay} Ayı Durumu**")
    
    # Progress Bar mantığını buraya grafik olarak gömelim (Gauge Chart daha şık olurdu ama basit bar yapalım)
    summary_data = pd.DataFrame({
        "Tip": ["Gelir (Tahsil)", "Gelir (Bekleyen)", "Gider (Ödenen)", "Gider (Bekleyen)"],
        "Tutar": [real_gelir, kalan_gelir, real_gider, kalan_gider],
        "Renk": ["#2ECC71", "#EAFAF1", "#E74C3C", "#FDEDEC"] # Koyu Yeşil, Açık Yeşil, Koyu Kırmızı, Açık Kırmızı
    })
    
    fig_summary = px.pie(summary_data, values='Tutar', names='Tip', hole=0.5, 
                         color='Tip', color_discrete_map={
                             "Gelir (Tahsil)": COL_SUCCESS, "Gelir (Bekleyen)": "#A9DFBF",
                             "Gider (Ödenen)": COL_EXPENSE_RED, "Gider (Bekleyen)": "#F5B7B1"
                         })
    fig_summary.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300)
    st.plotly_chart(fig_summary, use_container_width=True)

with col_chart2:
    # 2. Grafik: Yıllık Trend
    st.markdown(f"**📈 {filtre_yil} Yıllık Nakit Akışı**")
    trend_data = yearly_df.groupby(['AY', 'AY_NO', 'TÜR'])['TUTAR'].sum().reset_index().sort_values('AY_NO')
    fig_trend = px.line(trend_data, x="AY", y="TUTAR", color="TÜR", markers=True,
                        color_discrete_map={"TAHSİLAT": COL_INCOME_BLUE, "ÖDEME": COL_DARK_NAVY})
    fig_trend.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300, xaxis_title=None)
    st.plotly_chart(fig_trend, use_container_width=True)


# --- 4. VERİ LİSTESİ (SEKMELER) ---
tab_monthly, tab_yearly = st.tabs(["📝 Aylık Liste (Düzenle)", "📅 Yıllık Liste"])

with tab_monthly:
    # Düzenleme Modu
    col_edit1, col_edit2 = st.columns([3, 1])
    
    with col_edit1:
        st.info("Tablo üzerinde değişiklik yaptıktan sonra sağdaki **Kaydet** butonuna basınız.")
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
        st.write("") # Boşluk
        st.write("") 
        if st.button("💾 DEĞİŞİKLİKLERİ KAYDET", type="primary", use_container_width=True):
            try:
                main_df = st.session_state.df
                main_df.loc[edited_df.index] = edited_df
                st.session_state.df = main_df
                st.success("Güncellendi!")
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
