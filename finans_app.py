import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ... (Veri yükleme ve önceki fonksiyonlarınız burada kalacak) ...

# --- KENAR ÇUBUĞU (SIDEBAR) ---
st.sidebar.header("Ayarlar")

# REVİZE 1: Menü sırasını değiştirdik, Görsel Rapor başa geldi.
mod_secimi = st.sidebar.radio(
    "Görünüm Modu",
    ["🎨 Görsel Rapor (Renkli)", "✏️ Düzenleme Modu"]
)

# ... (Ay ve Yıl seçim kodlarınız burada aynı kalacak) ...

# --- ANA EKRAN ---

if mod_secimi == "🎨 Görsel Rapor (Renkli)":
    st.title(f"📊 {secilen_yil} {secilen_ay_ad} - Finansal Özet")
    
    # Verileri Hazırlama (Örnek mantık - kendi değişkenlerinizle eşleştirin)
    # REVİZE 2: İsimler güncellendi
    toplam_gelir = df_aylik[df_aylik['Tur'] == 'Gelir']['Tutar'].sum()
    toplam_gider = df_aylik[df_aylik['Tur'] == 'Gider']['Tutar'].sum()
    
    kalan = toplam_gelir - toplam_gider
    
    # Metrik Kartları (Renk uyumu korundu)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Gelir Rengi: Yeşil (success)
        st.markdown(f":green[**TAHSİL EDİLEN**]") 
        st.metric(label="", value=f"{toplam_gelir:,.2f} TL")
        
    with col2:
        # Gider Rengi: Kırmızı (error/danger)
        st.markdown(f":red[**ÖDENEN**]")
        st.metric(label="", value=f"{toplam_gider:,.2f} TL")
        
    with col3:
        st.markdown("**NET DURUM**")
        st.metric(label="", value=f"{kalan:,.2f} TL", delta_color="normal")

    st.divider()

    # --- GRAFİK KISMI (ORANSAL) ---
    # Pasta Grafiği (Donut Chart) ile oransal gösterim
    
    # Veri seti oluşturma
    labels = ['TAHSİL EDİLEN', 'ÖDENEN']
    values = [toplam_gelir, toplam_gider]
    
    # Renkleri metinlerle eşleştirme (Bir önceki talebinizdeki renk uyumu)
    # Gelir (Tahsil Edilen) -> Yeşil, Gider (Ödenen) -> Kırmızı
    colors = ['#28a745', '#dc3545'] 

    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.4, # Donut görünümü için
        marker=dict(colors=colors, line=dict(color='#000000', width=1))
    )])

    fig.update_layout(
        title_text="Gelir vs Gider Oranı",
        annotations=[dict(text='Nakit<br>Akışı', x=0.5, y=0.5, font_size=20, showarrow=False)]
    )

    st.plotly_chart(fig, use_container_width=True)

elif mod_secimi == "✏️ Düzenleme Modu":
    st.subheader("📝 Veri Girişi ve Düzenleme")
    # ... (Buradaki düzenleme tablosu (data_editor) kodlarınız aynı kalacak) ...
    # Sadece tablo başlıklarını değiştirmeniz gerekebilir eğer kolon ismi olarak kullanıyorsanız.
