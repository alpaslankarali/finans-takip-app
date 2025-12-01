# build_exe.py
# Bu dosyayı finans_app.py ile aynı klasöre kaydedin

import subprocess
import sys
import os

print("🚀 Finans Uygulamasını EXE'ye Dönüştürme")
print("=" * 50)

# PyInstaller kurulu mu kontrol et
try:
    import PyInstaller
    print("✅ PyInstaller bulundu")
except ImportError:
    print("📦 PyInstaller kuruluyor...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    print("✅ PyInstaller kuruldu")

# Icon dosyası oluştur (basit bir icon)
icon_path = "app_icon.ico"
if not os.path.exists(icon_path):
    print(f"⚠️  Icon dosyası bulunamadı: {icon_path}")
    print("   İsterseniz kendi .ico dosyanızı ekleyebilirsiniz")
    icon_cmd = ""
else:
    icon_cmd = f"--icon={icon_path}"
    print(f"✅ Icon bulundu: {icon_path}")

print("\n🔨 EXE oluşturuluyor (5-10 dakika sürebilir)...")

# PyInstaller komutu
cmd = f"""
pyinstaller --name="FinansTakip" \
    --onefile \
    --windowed \
    --add-data "finans_app.py;." \
    {icon_cmd} \
    --hidden-import=streamlit \
    --hidden-import=pandas \
    --hidden-import=plotly \
    --hidden-import=openpyxl \
    finans_app.py
"""

# Windows için komutu düzenle
if sys.platform == "win32":
    cmd = cmd.replace("\\\n", " ").replace("    ", "").strip()
    cmd_list = cmd.split()
    
    try:
        subprocess.run(cmd_list, check=True)
        print("\n" + "=" * 50)
        print("✅ BAŞARILI! EXE dosyanız hazır!")
        print("📂 Konum: dist/FinansTakip.exe")
        print("💡 Bu dosyayı istediğiniz yere taşıyabilir,")
        print("   çift tıklayarak çalıştırabilirsiniz!")
        print("=" * 50)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ HATA: {e}")
        print("\n🔧 Alternatif Yöntem:")
        print("Terminal'de şunu çalıştırın:")
        print('pyinstaller --onefile --windowed --name="FinansTakip" finans_app.py')
else:
    os.system(cmd)