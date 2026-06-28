# Autonomous Operation Extensions

Peningkatan otonomi untuk MiMoCode CLI Tool.

## Komponen yang Dibuat

### Hooks (`.mimocode/hooks/`)

| File | Fungsi |
|------|--------|
| `auto-continue.ts` | Otomatis melanjutkan kerja setelah task selesai |
| `auto-task-chain.ts` | Menghubungkan task secara otomatis |
| `smart-continuation.ts` | Keputusan kapan harus melanjutkan vs berhenti |
| `enforce-autonomy.ts` | Memaksa perilaku otonom |
| `error-recovery.ts` | Penanganan error otomatis |
| `auto-logger.ts` | Logging aksi penting |
| `memory-learner.ts` | Pembelajaran dari error |

### Tools (`.mimocode/tools/`)

| File | Fungsi |
|------|--------|
| `workflow-state.ts` | Tracking state workflow |
| `autonomous-tracker.ts` | Logging dan tracking progress |

### Skills (`.mimocode/skills/`)

| File | Fungsi |
|------|--------|
| `autonomous/SKILL.md` | Skill dasar otonomi |
| `autonomous-operation/SKILL.md` | Framework operasi otonom lengkap |
| `error-recovery/SKILL.md` | Pola recovery dari error |
| `continuous-work/SKILL.md` | Kerja tanpa interupsi |

## Cara Kerja

### Alur Otonom
```
task list → task start → kerja → task done → task list → repeat
```

### Keputusan: Tanya vs Kerja

| Situasi | Tindakan |
|---------|----------|
| Kebutuhan jelas | Kerja langsung |
| Ambiguitas kecil | Asumsi wajar, dokumentasi |
| Multi pendekatan | Pilih terbaik, jelaskan |
| Aksi destruktif | Tanya dulu |
| Info kritis hilang | Tanya spesifik |

### Error Handling
1. Error pertama → baca, coba fix obvious
2. Error kedua → search memory, coba alternatif
3. Error ketiga → document, lanjut task lain
4. Jangan retry lebih dari 3x

## Fitur Utama

1. **Auto-Task Chaining** - Task selesai → langsung mulai task berikutnya
2. **Error Recovery** - Penanganan error otomatis tanpa berhenti
3. **Smart Blocking** - Hanya berhenti saat benar-benar perlu
4. **Memory Learning** - Belajar dari error masa lalu
5. **Progress Tracking** - Log otomatis setiap aksi signifikan

## Monitoring

### Cek Status
```bash
task list status=open
```

### Progress Report
Setiap 5 task selesai atau ganti kategori kerja.

## Anti-Patterns yang Dicegah

- ❌ "Apa yang harus saya lakukan selanjutnya?" saat task masih ada
- ❌ Menunggu konfirmasi untuk operasi rutin
- ❌ Retry command yang sama tanpa ubah apapun
- ❌ Menjelaskan aksi yang obvious
