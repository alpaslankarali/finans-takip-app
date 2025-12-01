import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. VERİ YÜKLEME VE HAZIRLIK
# -----------------------------------------------------------------------------

# NOT: Kendi projenizde aşağıdaki "ÖRNEK VERİ OLUŞTURMA" kısmını silip, 
# yerine kendi Excel okuma kodunuzu (pd.read_excel) yazmalısınız.

# --- SİZİN KODUNUZ BURAYA GELECEK ---
# dosya_yolu = "finans_takip.xlsx"  # Kendi dosya yolunuz
# df = pd.read_excel(dosya_yolu)
# ------------------------------------

# --- (Test İçin) ÖRNEK VERİ OLUŞTURMA BAŞLANGICI ---
data = {
    'Yil': [2025, 2025, 2025, 2025],
    'Ay': ['Ocak', 'Ocak', 'Şubat', 'Şubat'],
    'Tur': ['Gelir', 'Gider', 'Gelir', 'Gider'],
    'Aciklama': ['Maaş', 'Kira', 'Freelance', 'Fatura'],
    'Tutar': [50000, 20000, 15000, 3000]
}
df = pd.DataFrame(data)
# --- ÖRNEK VERİ BİTİŞİ ---

# -----------------------------------------------------------------------------
# 2. SIDEBAR (KENAR ÇUBUĞU) VE AYARLAR
# -----------------------------------------------------------------------------
st.sidebar.header("Ayarlar")

# İSTEK 1: Menü sırası değişti, Görsel Rapor varsayılan oldu.
mod_secimi = st.sidebar.radio(
    "Görünüm Modu",
    ["🎨 Görsel Rapor (Renkli)", "✏️ Düzenleme Modu"]
)

st.sidebar.divider()

# İSTEK 2: Tarih Seçimi (Hatayı önlemek için EN ÜSTTE tanımlıyoruz)
# Veri setindeki mevcut yıl ve ayları alalım
mevcut_yillar = sorted(df['Yil'].unique().tolist())
mevcut_aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

# Seçim Kutuları
secilen_yil = st.sidebar.selectbox("Yıl Seçiniz", mevcut_yillar)
secilen_ay_ad = st.sidebar.selectbox("Ay Seçiniz", mevcut_aylar)

# Veriyi Filtreleme
df_aylik = df[(df['Yil'] == secilen_yil) & (df['Ay'] == secilen_ay_ad)]

# -----------------------------------------------------------------------------
# 3. ANA EKRAN
# -----------------------------------------------------------------------------

if mod_secimi == "🎨 Görsel Rapor (Renkli)":
    # Başlık (Değişkenler yukarıda tanımlandığı için artık hata vermez)
    st.title(f"📊 {secilen_yil} {secilen_ay_ad} - Finansal Özet")
    
    # Hesaplamalar
    toplam_gelir = df_aylik[df_aylik['Tur'] == 'Gelir']['Tutar'].sum()
    toplam_gider = df_aylik[df_aylik['Tur'] == 'Gider']['Tutar'].sum()
    kalan = toplam_gelir - toplam_gider
    
    # --- METRİK KARTLARI ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # İSTEK 3: İsim "TAHSİL EDİLEN" oldu, Rengi Yeşil
        st.markdown(f":green[**TAHSİL EDİLEN**]") 
        st.metric(label="", value=f"{toplam_gelir:,.2f} TL")
        
    with col2:
        # İSTEK 4: İsim "ÖDENEN" oldu, Rengi Kırmızı
        st.markdown(f":red[**ÖDENEN**]")
        st.metric(label="", value=f"{toplam_gider:,.2f} TL")
        
    with col3:
        st.markdown("**NET DURUM**")
        st.metric(label="", value=f"{kalan:,.2f} TL", delta_color="normal")

    st.divider()

    # --- GRAFİK KISMI (ORANSAL / PASTA GRAFİĞİ) ---
    if toplam_gelir > 0 or toplam_gider > 0:
        # İSTEK 5: Oransal gösterim (Donut Chart)
        labels = ['TAHSİL EDİLEN', 'ÖDENEN']
        values = [toplam_gelir, toplam_gider]
        
        # İSTEK 6: Renkler metriklerle (yazılarla) aynı -> Yeşil ve Kırmızı
        colors = ['#28a745', '#dc3545'] 

        fig = go.Figure(data=[go.Pie(
            labels=labels, 
            values=values, 
            hole=.4, # Donut görünümü (ortası delik)
            marker=dict(colors=colors, line=dict(color='#000000', width=1))
        )])

        fig.update_layout(
            title_text="Gelir vs Gider Oranı",
            annotations=[dict(text='Nakit<br>Akışı', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Bu ay için görüntülenecek veri bulunamadı.")

elif mod_secimi == "✏️ Düzenleme Modu":
    st.subheader("📝 Veri Girişi ve Düzenleme")
    
    # Data Editor (Tablo düzenleme)
    edited_df = st.data_editor(
        df_aylik, 
        num_rows="dynamic",
        key="editor"
    )
    
    # Kaydetme Butonu (Örnek mantık)
    if st.button("Değişiklikleri Kaydet"):
        st.success("Veriler (simülasyon olarak) güncellendi!")
        # Burada gerçek kaydetme işlemini (to_excel) yapmalısınız.
