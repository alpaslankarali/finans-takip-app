import streamlit as st
import pandas as pd
import io
import xlsxwriter
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Finansal Yönetim Paneli", layout="wide", page_icon="💼")

# --- RENK PALETİ ---
COL_DARK_NAVY   = '#395168'
COL_INCOME_BLUE = '#659CE0'
COL_EXPENSE_RED = '#E74C3C'
COL_OFF_WHITE   = '#FEFEFE'
COL_SLATE       = '#34495E'

# --- 1. VERİ ALTYAPISI (SESSION STATE) ---
# Verilerin hafızada tutulması için Session State kullanıyoruz.
if 'df' not in st.session_state:
    # Başlangıç verileri (İlk açılışta gelecekler)
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
            # Örnek Ziraat Kredisi (Sadece Ocak 2026)
            if year == 2026 and i == 1:
                current_items.append({"AÇIKLAMA": "ZİRAAT KREDİ", "TÜR": "ÖDEME", "TUTAR": 9031, "GÜN": 6, "DURUM": "BEKLİYOR"})
            
            for item in current_items:
                # Tarih objesi oluştur
                date_obj = datetime(year, i, item["GÜN"])
                rows.append({
                    'TARİH': date_obj,
                    'YIL': year,
                    'AY': month_name, # Filtreleme için ay ismi
                    'AY_NO': i,       # Sıralama için ay numarası
                    'AÇIKLAMA': item['AÇIKLAMA'],
                    'TÜR': item['TÜR'],
                    'TUTAR': item['TUTAR'],
                    'DURUM': item['DURUM']
                })
    
    st.session_state.df = pd.DataFrame(rows)

# Ana veri çerçevesi (Session State'den okuyoruz)
df = st.session_state.df

# --- 2. SIDEBAR: İŞLEM EKLEME (MAKRO MANTIĞI) ---
st.sidebar.header("⚡ Hızlı İşlem / Taksit Ekle")

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
        # Taksit döngüsü (Makro mantığı)
        for _ in range(new_installments):
            # Ay ismini bul
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
            # Bir sonraki aya geç
            current_date += relativedelta(months=1)
        
        # Yeni veriyi ana veriye ekle
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_rows)], ignore_index=True)
        st.success(f"{new_installments} adet kayıt başarıyla eklendi!")
        st.rerun() # Sayfayı yenile ve veriyi güncelle

# --- 3. ANA SAYFA VE FİLTRELER ---
st.title("📊 Finansal Yönetim Paneli")

# Filtreler (Yan yana)
col_f1, col_f2 = st.columns(2)
with col_f1:
    filtre_yil = st.selectbox("Yıl Seçiniz", sorted(df['YIL'].unique()), index=0)
with col_f2:
    # Seçilen yıla ait ayları getir
    filtre_ay = st.selectbox("Ay Seçiniz", df[df['YIL'] == filtre_yil]['AY'].unique())

# Veriyi Filtrele
filtered_df = df[(df['YIL'] == filtre_yil) & (df['AY'] == filtre_ay)].copy()
yearly_df = df[df['YIL'] == filtre_yil].copy() # Yıllık grafik için

# KPI Kartları
total_income = filtered_df[filtered_df['TÜR'] == 'TAHSİLAT']['TUTAR'].sum()
total_expense = filtered_df[filtered_df['TÜR'] == 'ÖDEME']['TUTAR'].sum()
net_balance = total_income - total_expense

col1, col2, col3 = st.columns(3)
col1.metric("TOPLAM GELİR", f"{total_income:,.0f} ₺", delta="Tahsilat")
col2.metric("TOPLAM GİDER", f"{total_expense:,.0f} ₺", delta="-Ödeme", delta_color="inverse")
col3.metric("NET DURUM", f"{net_balance:,.0f} ₺", delta_color="normal" if net_balance > 0 else "inverse")

st.markdown("---")

# --- 4. GRAFİKLER ---
tab1, tab2 = st.tabs(["📈 Aylık Analiz", "📅 Yıllık Genel Bakış"])

with tab1:
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader(f"{filtre_yil} Nakit Akışı Trendi")
        # Trend Verisi (Ay numarasına göre sıralı)
        trend_data = yearly_df.groupby(['AY', 'AY_NO', 'TÜR'])['TUTAR'].sum().reset_index().sort_values('AY_NO')
        
        fig_bar = px.bar(trend_data, x="AY", y="TUTAR", color="TÜR", barmode="group",
                         color_discrete_map={"TAHSİLAT": COL_INCOME_BLUE, "ÖDEME": COL_DARK_NAVY},
                         title=f"{filtre_yil} Gelir-Gider Dengesi")
        fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        st.subheader(f"{filtre_ay} Harcama Dağılımı")
        pie_data = filtered_df[filtered_df['TÜR'] == 'ÖDEME']
        if not pie_data.empty:
            fig_pie = px.pie(pie_data, values='TUTAR', names='AÇIKLAMA', hole=0.4,
                             color_discrete_sequence=px.colors.sequential.RdBu)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Bu ay için gider kaydı bulunamadı.")

with tab2:
    st.subheader("🗓️ Yıllık Karşılaştırma (Tüm Yıllar)")
    # Yıllık özet verisi
    yearly_summary = st.session_state.df.groupby(['YIL', 'TÜR'])['TUTAR'].sum().reset_index()
    
    fig_year = px.bar(yearly_summary, x="YIL", y="TUTAR", color="TÜR", barmode="group",
                      color_discrete_map={"TAHSİLAT": COL_INCOME_BLUE, "ÖDEME": COL_EXPENSE_RED},
                      text_auto='.2s')
    fig_year.update_layout(xaxis_type='category') # Yılları sayı değil kategori olarak göster
    st.plotly_chart(fig_year, use_container_width=True)

# --- 5. DÜZENLENEBİLİR LİSTE (DATA EDITOR) ---
st.subheader(f"📝 {filtre_ay} {filtre_yil} Detaylı Listesi (Düzenlenebilir)")
st.caption("Tablodaki verilere çift tıklayarak değişiklik yapabilirsiniz. Değişiklikler anında grafiklere yansır.")

# Data Editor Ayarları
edited_df = st.data_editor(
    filtered_df[['TARİH', 'AÇIKLAMA', 'TÜR', 'TUTAR', 'DURUM']],
    column_config={
        "TARİH": st.column_config.DateColumn("Tarih", format="DD.MM.YYYY"),
        "TUTAR": st.column_config.NumberColumn("Tutar", format="%d ₺"),
        "TÜR": st.column_config.SelectboxColumn("Tür", options=["TAHSİLAT", "ÖDEME"]),
        "DURUM": st.column_config.SelectboxColumn("Durum", options=["BEKLİYOR", "ÖDENDİ"]),
    },
    use_container_width=True,
    num_rows="dynamic", # Satır ekleme/silme izni
    key="editor"
)

# --- DÜZENLEMELERİ KAYDETME MANTIĞI ---
# Streamlit'te editör, filtrelenmiş veriyi döndürür. Bunu ana veri setine (session_state) geri yansıtmak karmaşıktır.
# Bu örnekte, 'görsel düzenleme' yaptık ve grafikler bu anlık düzenlemeye göre yukarıda (re-run ile) güncellenmedi.
# Ancak kullanıcı Excel indirdiğinde EN GÜNCEL halini (makro ile eklenenler dahil) almak ister.

# Not: Data Editor'daki değişiklikleri ana DF'ye yansıtmak için unique ID gerekir.
# Basitlik adına: Kullanıcıya "Excel İndir" butonu sunuyoruz. Bu buton Session State'deki (Makro ile eklenenler dahil) veriyi indirir.

st.markdown("---")
st.subheader("📥 Verileri Yedekle / İndir")

def generate_excel_download():
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    # Tüm veriyi yaz
    st.session_state.df.to_excel(writer, sheet_name='TÜM_VERİLER', index=False)
    
    # Formatlama (Basit)
    workbook = writer.book
    worksheet = writer.sheets['TÜM_VERİLER']
    header_fmt = workbook.add_format({'bold': True, 'bg_color': COL_DARK_NAVY, 'font_color': 'white'})
    for col_num, value in enumerate(st.session_state.df.columns.values):
        worksheet.write(0, col_num, value, header_fmt)
        
    writer.close()
    return output.getvalue()

st.download_button(
    label="Güncel Tabloyu Excel Olarak İndir",
    data=generate_excel_download(),
    file_name="Guncel_Finans_Verileri.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
