# Panduan Install Mythos di Komputer Lain

## Cara Cepat (Windows)

### 1. Install Python (jika belum ada)

Download dan install Python 3.9+ dari: https://www.python.org/downloads/

**PENTING**: Centang "Add Python to PATH" saat install!

### 2. Clone Repository

Buka CMD atau PowerShell, lalu jalankan:

```bash
git clone https://github.com/mythos-ai/mythos.git
cd mythos
```

### 3. Run Installer

```bash
python install.py
```

Installer akan:
- ✅ Cek Python version
- ✅ Install dependencies otomatis
- ✅ Buat virtual environment
- ✅ Jalankan self-test
- ✅ Tawarkan tambah ke PATH

### 4. Launch Mythos

```bash
python mythos.py
```

Atau jika sudah ditambah ke PATH:

```bash
Mythos
```

---

## Install Global (Recommended)

Agar bisa dipanggil dari mana saja:

```bash
python install_global.py
```

Setelah install, buka terminal baru dan ketik:

```bash
Mythos
```

---

## Manual Install

Jika ingin install manual:

```bash
# Clone
git clone https://github.com/mythos-ai/mythos.git
cd mythos

# Install dependencies
pip install -r requirements.txt

# Jalankan
python mythos.py
```

---

## Struktur Folder

```
mythos/
├── mythos.py           # Entry point utama
├── install.py          # Installer
├── install_global.py   # Global installer (tambah ke PATH)
├── config.json         # Konfigurasi API keys
├── requirements.txt    # Python dependencies
├── core/               # Core modules
│   ├── agent.py        # Main agent
│   ├── api_client.py   # API integration
│   ├── memory.py       # Memory system
│   └── ...
├── tests/              # Test files
├── assets/             # Static assets
└── .mimocode/          # Skills and hooks
    └── skills/         # 17 skills
```

---

## Troubleshooting

### "Python not found"
- Pastikan Python terinstall dan ada di PATH
- Coba: `python --version` atau `py --version`

### "Module not found"
- Jalankan: `pip install -r requirements.txt`
- Atau: `python install.py`

### "API key error"
- Edit `config.json`
- Masukkan API key yang valid

### Permission error
- Jalankan terminal sebagai Administrator
- Atau gunakan `--user` flag: `pip install --user -r requirements.txt`

---

## API Keys

Mythos menggunakan API keys dari:
- **OpenRouter**: https://openrouter.ai/
- **Shannon AI**: https://shannon-ai.com/

Edit `config.json` untuk menambah/mengganti keys.

---

## Update

```bash
# Pull latest changes
git pull

# Reinstall dependencies
pip install -r requirements.txt

# Atau jalankan installer lagi
python install.py
```

---

## Uninstall

```bash
# Hapus dari PATH
python install_global.py --remove

# Hapus folder
rm -rf mythos/
```

---

## Bantuan

Jika ada masalah, buka issue di:
https://github.com/mythos-ai/mythos/issues
