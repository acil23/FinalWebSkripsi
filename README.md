# Sistem Informasi Penjadwalan Mata Kuliah

Implementasi web untuk sistem penjadwalan mata kuliah berbasis **Memetic Algorithm**. Aplikasi ini dirancang untuk membantu Admin Program Studi dalam mengelola data masukan, menentukan konfigurasi pembukaan kelas, mengatur parameter algoritma, menjalankan optimasi penjadwalan, melihat hasil jadwal dan evaluasi, mengekspor hasil, serta menyimpan riwayat jadwal.

Sistem dikembangkan menggunakan **FastAPI**, **Jinja2 Templates**, **Pandas**, dan **SQLite**. Pemrosesan data dan engine algoritma berjalan secara in-memory, sedangkan SQLite digunakan untuk menyimpan riwayat jadwal dalam bentuk JSON snapshot.

## Fitur Utama

- Dashboard penjadwalan dengan alur proses sistem.
- Unggah data masukan dalam format CSV.
- Unduh template CSV untuk setiap jenis data masukan.
- Drag-and-drop file CSV pada halaman unggah data.
- Validasi struktur dan kelengkapan data masukan.
- Rekomendasi dan konfirmasi konfigurasi pembukaan kelas.
- Pengaturan parameter algoritma, termasuk ukuran populasi, jumlah generasi, crossover rate, mutation rate, peluang local search, elitism, dan seed.
- Eksekusi penjadwalan menggunakan engine Memetic Algorithm.
- Polling status eksekusi untuk menampilkan progres generasi, fitness, dan konflik.
- Tampilan hasil jadwal, evaluasi, beban dosen, dan grafik konvergensi.
- Ekspor hasil jadwal, evaluasi, beban dosen, log konvergensi, dan paket ZIP.
- Penyimpanan riwayat jadwal menggunakan SQLite.
- Tampilan daftar riwayat, detail riwayat, ekspor ulang, dan hapus riwayat.

## Struktur Folder

```text
app/
  algorithm/       Engine algoritma penjadwalan
  controllers/     Control layer untuk mengatur alur use case
  core/            Konfigurasi, path, dan state aplikasi
  entities/        Entity dan value object sistem
  repositories/    Repository untuk akses penyimpanan riwayat
  routers/         Boundary layer / route FastAPI
  schemas/         Metadata form dan validasi input
  services/        Service pendukung seperti data loader, ekspor, dan visualisasi
  static/          CSS dan aset gambar
  templates/       Template halaman web Jinja2

data/
  db/              Lokasi database SQLite riwayat jadwal
  export/          Lokasi file hasil ekspor
  input/           Direktori input pendukung
  output/          Direktori output engine algoritma
  uploaded/        Lokasi penyimpanan file CSV yang diunggah
```

## Kebutuhan Sistem

- Python 3.11 atau lebih baru.
- Browser web modern.
- Paket Python sesuai `requirements.txt`.

## Cara Menjalankan Aplikasi

1. Buat virtual environment.

```bash
python -m venv .venv
```

2. Aktifkan virtual environment.

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

3. Instal dependensi.

```bash
pip install -r requirements.txt
```

4. Jalankan server pengembangan.

```bash
uvicorn app.main:app --reload
```

5. Buka aplikasi melalui browser.

```text
http://127.0.0.1:8000
```

## Alur Penggunaan

1. Buka halaman **Dashboard**.
2. Masuk ke halaman **Unggah Data**.
3. Unduh template CSV apabila diperlukan.
4. Unggah seluruh data masukan yang dibutuhkan.
5. Buka halaman **Konfigurasi Kelas** dan hasilkan rekomendasi pembukaan kelas.
6. Tinjau atau ubah jumlah kelas final, lalu simpan konfigurasi.
7. Buka halaman **Parameter Algoritma** dan simpan parameter eksekusi.
8. Buka halaman **Eksekusi Penjadwalan** dan jalankan proses optimasi.
9. Buka halaman **Hasil Penjadwalan** untuk melihat jadwal, evaluasi, grafik, dan beban dosen.
10. Gunakan halaman **Ekspor Hasil** untuk mengunduh file hasil penjadwalan.
11. Gunakan fitur **Simpan Riwayat** untuk menyimpan hasil jadwal ke SQLite.
12. Buka halaman **Riwayat Jadwal** untuk melihat kembali hasil yang telah disimpan.

## Data Masukan

Aplikasi menerima beberapa data masukan utama dalam format CSV:

- Data mata kuliah wajib.
- Data mata kuliah pilihan.
- Data dosen pengampu.
- Data preferensi dosen.
- Data ruang kelas.
- Data slot waktu.
- Data jumlah mahasiswa.
- Data Pra-KRS mata kuliah pilihan.

Template CSV dapat diunduh langsung dari halaman **Unggah Data** melalui tombol **Unduh Template CSV** pada masing-masing kartu data.

## Penyimpanan Riwayat

Riwayat jadwal disimpan menggunakan SQLite pada direktori berikut:

```text
data/db/scheduling_history.sqlite3
```

Database dibuat otomatis saat aplikasi dijalankan. Setiap riwayat disimpan sebagai satu record utama pada tabel `riwayat_jadwal` dengan pendekatan JSON snapshot. Metadata ringkas disimpan pada kolom terpisah, sedangkan detail hasil jadwal, parameter algoritma, dan konfigurasi pembukaan kelas disimpan dalam kolom JSON.

## Catatan Implementasi

- Aplikasi dirancang untuk alur penggunaan satu Admin Program Studi.
- State aktif aplikasi masih disimpan secara in-memory selama server berjalan.
- Jika server dimatikan atau restart, data aktif yang belum disimpan sebagai riwayat perlu diproses ulang.
- Untuk pengembangan produksi, autentikasi pengguna, session per admin, job queue, dan penyimpanan state yang lebih persisten dapat ditambahkan.

## Status

Versi ini merupakan implementasi final sementara untuk kebutuhan penulisan dan pengujian skripsi. Seluruh use case utama UC-01 sampai UC-08 telah direalisasikan dalam bentuk halaman web, endpoint, service, dan repository yang sesuai dengan rancangan sistem.
