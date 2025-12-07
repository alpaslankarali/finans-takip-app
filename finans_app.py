import streamlit as st
import pandas as pd
import io
import xlsxwriter
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Finansal Yönetim Paneli V2.1", layout="wide", page_icon="🚀")

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

# Ana veriyi çek
df = st.session_state.df

# --- 2. SIDEBAR: İŞLEM EKLEME ---
st.sidebar.header("⚡ Yeni Kayıt / Makro")
with st.sidebar.form("add_form", clear_on_submit=True):
    new_desc = st.text_input("Açıklama", "Yeni İşlem")
    new_type = st.selectbox("İşlem Türü", ["ÖDEME", "TAHSİLAT"])
    new_amount = st.number_input("Tutar", min_value=0.0, step=100.0)
    new_status = st.selectbox("Durum", ["BEKLİYOR", "ÖDENDİ"])
    new_date = st.date_input("Başlangıç Tarihi", datetime(2026, 1, 15))
    new_installments = st.number_input("Taksit Sayısı (Ay)", min_value=1, value=1, step=1)
    
    submit_btn = st.form_submit_button("Listeye Ekle")

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
        st.success("Kayıtlar eklendi!")
        st.rerun()

# --- 3. ANA SAYFA VE KPI ---
st.title("📊 Finansal Kontrol Merkezi")

# Filtreler
col_f1, col_f2 = st.columns(2)
with col_f1: filtre_yil = st.selectbox("Yıl", sorted(df['YIL'].unique()))
with col_f2: filtre_ay = st.selectbox("Ay", df[df['YIL'] == filtre_yil]['AY'].unique())

# Filtrelenmiş Veri (Kopya değil, indexleri koruyarak filtreliyoruz)
# Bu kısım önemli: Ana verideki indexleri kaybetmemeliyiz ki güncelleyebilelim.
filtered_indices = df[(df['YIL'] == filtre_yil) & (df['AY'] == filtre_ay)].index
filtered_df = df.loc[filtered_indices].copy()

yearly_df = df[df['YIL'] == filtre_yil].copy()

# --- HESAPLAMALAR ---
# 1. Planlanan (Toplam)
plan_gelir = filtered_df[filtered_df['TÜR'] == 'TAHSİLAT']['TUTAR'].sum()
plan_gider = filtered_df[filtered_df['TÜR'] == 'ÖDEME']['TUTAR'].sum()

# 2. Gerçekleşen (Sadece 'ÖDENDİ' olanlar)
real_gelir = filtered_df[(filtered_df['TÜR'] == 'TAHSİLAT') & (filtered_df['DURUM'] == 'ÖDENDİ')]['TUTAR'].sum()
real_gider = filtered_df[(filtered_df['TÜR'] == 'ÖDEME') & (filtered_df['DURUM'] == 'ÖDENDİ')]['TUTAR'].sum()

# 3. Kalan
kalan_gelir = plan_gelir - real_gelir
kalan_gider = plan_gider - real_gider
net_nakit = real_gelir - real_gider

# KPI KARTLARI
c1, c2, c3, c4 = st.columns(4)
c1.metric("TOPLAM PLANLANAN GELİR", f"{plan_gelir:,.0f} ₺", delta=f"Bekleyen: {kalan_gelir:,.0f}")
c2.metric("TOPLAM PLANLANAN GİDER", f"{plan_gider:,.0f} ₺", delta=f"Bekleyen: {kalan_gider:,.0f}", delta_color="inverse")
c3.metric("CEBE GİREN (TAHSİL)", f"{real_gelir:,.0f} ₺", delta_color="normal")
c4.metric("CEPTEN ÇIKAN (ÖDENEN)", f"{real_gider:,.0f} ₺", delta_color="inverse")

# İLERLEME ÇUBUKLARI (Seçilen Ay İçin)
st.caption(f"{filtre_ay} {filtre_yil} - Bütçe Gerçekleşme Durumu")
col_p1, col_p2 = st.columns(2)
with col_p1:
    prog_gelir = (real_gelir / plan_gelir) if plan_gelir > 0 else 0
    st.progress(prog_gelir, text=f"Tahsilat Tamamlanma: %{prog_gelir*100:.1f} ({real_gelir:,.0f} / {plan_gelir:,.0f})")
with col_p2:
    prog_gider = (real_gider / plan_gider) if plan_gider > 0 else 0
    st.progress(prog_gider, text=f"Ödeme Tamamlanma: %{prog_gider*100:.1f} ({real_gider:,.0f} / {plan_gider:,.0f})")

st.markdown("---")

# --- 4. GRAFİKLER VE LİSTE ---
# Yeni sekme yapısı: Aylık Liste | Yıllık Liste | Grafikler
tab_list, tab_yearly, tab_charts = st.tabs(["📝 Aylık Liste (Düzenle)", "📅 Yıllık Liste", "📈 Grafikler"])

with tab_list:
    # İki alt sekme: Biri düzenleme için, biri görsel rapor için
    sub_tab1, sub_tab2 = st.tabs(["✏️ Düzenleme Modu", "🎨 Görsel Rapor"])
    
    with sub_tab1:
        st.info("Tablodaki verileri (Tutar, Durum vb.) değiştirdikten sonra aşağıdaki **'Değişiklikleri Kaydet'** butonuna basınız.")
        
        # Data Editor - Indexleri gizlemiyoruz çünkü güncelleme için referans alabiliriz, 
        # ama görsel temizlik için hide_index=True yapıp arkada index tutacağız.
        edited_df = st.data_editor(
            filtered_df, # Sadece filtrelenmiş veriyi göster
            column_config={
                "TARİH": st.column_config.DateColumn("Tarih", format="DD.MM.YYYY"),
                "TUTAR": st.column_config.NumberColumn("Tutar", format="%d ₺"),
                "TÜR": st.column_config.SelectboxColumn("Tür", options=["TAHSİLAT", "ÖDEME"]),
                "DURUM": st.column_config.SelectboxColumn("Durum", options=["BEKLİYOR", "ÖDENDİ"]),
            },
            use_container_width=True,
            num_rows="dynamic",
            key="editor_monthly",
            hide_index=True
        )
        
        # --- KAYDET BUTONU ---
        if st.button("💾 Değişiklikleri Kaydet", type="primary"):
            try:
                # 1. Session state'teki ana veriyi al
                main_df = st.session_state.df
                
                # 2. Editörden gelen verinin indexlerini kullanarak ana veriyi güncelle
                # edited_df zaten filtered_df'den geldiği için orijinal indexlere sahip.
                main_df.loc[edited_df.index] = edited_df
                
                # 3. Güncellenmiş veriyi tekrar session state'e yaz
                st.session_state.df = main_df
                
                st.success("Tablo başarıyla güncellendi! Hesaplamalar yenileniyor...")
                st.rerun() # Sayfayı yenile ki KPI'lar ve Grafikler güncellensin
            except Exception as e:
                st.error(f"Hata oluştu: {e}")
        
    with sub_tab2:
        st.markdown(f"**{filtre_ay} Ayı Durum Raporu**")
        
        def highlight_status(row):
            styles = [''] * len(row)
            if row['DURUM'] == 'ÖDENDİ':
                return ['background-color: #D1F2EB; color: #145A32; font-weight: bold'] * len(row)
            elif row['DURUM'] == 'BEKLİYOR':
                return ['background-color: #FCF3CF; color: #7D6608'] * len(row)
            return styles

        st.dataframe(
            filtered_df[['TARİH', 'AÇIKLAMA', 'TÜR', 'TUTAR', 'DURUM']].style.apply(highlight_status, axis=1).format({"TUTAR": "{:,.0f} ₺", "TARİH": lambda t: t.strftime("%d.%m.%Y")}),
            use_container_width=True
        )

with tab_yearly:
    st.subheader(f"📅 {filtre_yil} Yılı Tüm İşlemler")
    st.dataframe(
        yearly_df.sort_values(by="TARİH"),
        column_config={
                "TARİH": st.column_config.DateColumn("Tarih", format="DD.MM.YYYY"),
                "TUTAR": st.column_config.NumberColumn("Tutar", format="%d ₺"),
            },
        use_container_width=True,
        hide_index=True
    )

with tab_charts:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📅 Yıllık Genel Durum")
        yearly_summary = st.session_state.df.groupby(['YIL', 'TÜR'])['TUTAR'].sum().reset_index()
        fig_year = px.bar(yearly_summary, x="YIL", y="TUTAR", color="TÜR", barmode="group",
                          color_discrete_map={"TAHSİLAT": COL_INCOME_BLUE, "ÖDEME": COL_DARK_NAVY}, text_auto='.2s')
        st.plotly_chart(fig_year, use_container_width=True)
        
    with c2:
        st.subheader(f"📊 {filtre_yil} Aylık Trend")
        trend_data = yearly_df.groupby(['AY', 'AY_NO', 'TÜR'])['TUTAR'].sum().reset_index().sort_values('AY_NO')
        fig_trend = px.line(trend_data, x="AY", y="TUTAR", color="TÜR", markers=True,
                            color_discrete_map={"TAHSİLAT": COL_INCOME_BLUE, "ÖDEME": COL_EXPENSE_RED})
        st.plotly_chart(fig_trend, use_container_width=True)

# --- EXCEL İNDİRME ---
st.markdown("---")
def generate_excel():
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    st.session_state.df.to_excel(writer, sheet_name='TÜM_VERİLER', index=False)
    
    workbook = writer.book
    worksheet = writer.sheets['TÜM_VERİLER']
    header_fmt = workbook.add_format({'bold': True, 'bg_color': COL_DARK_NAVY, 'font_color': 'white'})
    money_fmt = workbook.add_format({'num_format': '#,##0 "₺"'})
    date_fmt = workbook.add_format({'num_format': 'dd.mm.yyyy'})
    
    for col_num, value in enumerate(st.session_state.df.columns.values):
        worksheet.write(0, col_num, value, header_fmt)
        
    worksheet.set_column('A:A', 15, date_fmt)
    worksheet.set_column('G:G', 15, money_fmt)
        
    writer.close()
    return output.getvalue()

st.download_button(
    label="💾 Güncel Tabloyu Excel Olarak İndir",
    data=generate_excel(),
    file_name="Finans_Takip_Raporu.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
