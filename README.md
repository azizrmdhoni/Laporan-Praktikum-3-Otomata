# Laporan-Praktikum-3-Otomata

 ## Kelompok 09
 ### Anggota Kelompok:
| Name | NRP | Class |
| ---- | --- | ----- |
| Naufal Daffa Alfa Zain | 5025241066 | A |
| Muhamad Aziz Romdhoni  | 5025241071 | A |
| Anak Agung Putu Arda Nareswara | 5025241073 | A |

## Simulator PDA (Pushdown Automaton)

### 1. Pendahuluan
Pushdown Automaton (PDA) adalah model automata yang menggunakan **stack** untuk memproses bahasa-bahasa yang lebih kompleks daripada regular language. Program ini dibuat sebagai simulator PDA berbasis **Python Tkinter** agar pengguna dapat menguji string, melihat hasil penerimaan atau penolakan, serta memahami langkah komputasi PDA secara lebih visual dan interaktif. Program ini juga menampilkan jejak langkah, definisi formal PDA, tabel transisi, dan visualisasi stack. 

### 2. Tujuan
Tujuan pembuatan program ini adalah:
1. Mensimulasikan kerja PDA secara langsung.
2. Membantu pengguna memahami proses push, pop, dan transisi epsilon.
3. Menyediakan beberapa contoh bahasa formal yang umum dipelajari.
4. Memberikan fasilitas pembuatan PDA kustom, import/export JSON, dan pengujian batch. 

### 3. Deskripsi Program
Program ini merupakan aplikasi desktop dengan judul **“Simulator PDA - Pushdown Automaton”**. Saat dijalankan, aplikasi menampilkan antarmuka utama dengan pilihan preset PDA, input string, hasil identifikasi, tabel transisi, visualisasi stack, dan tab khusus untuk membuat PDA kustom. Ukuran jendela aplikasi diatur pada **1320 x 840**. 

### 4. Fitur Program
Program ini memiliki beberapa fitur utama, yaitu:
1. **Pemilihan preset PDA**.
2. **Simulasi input string** untuk menentukan Accepted atau Rejected.
3. **Visualisasi langkah komputasi**.
4. **Visualisasi stack**.
5. **Batch testing** untuk banyak string sekaligus.
6. **PDA kustom**.
7. **Import dan export definisi PDA dalam format JSON**.
8. **Penyimpanan hasil pengujian** ke file TXT atau CSV. 

### 5. Preset PDA yang Disediakan
Program menyediakan lima PDA bawaan, yaitu:
1. Bahasa \(a^n b^n\), dengan syarat jumlah `a` sama dengan jumlah `b`.
2. Bahasa kurung seimbang.
3. Bahasa \(w#w^R\), yaitu string diikuti pembalikannya.
4. Bahasa dengan jumlah `a` sama dengan jumlah `b`.
5. Bahasa \(a^n b^m\) dengan syarat \(n \le m \le 2n\). 

### 6. Cara Kerja Program
Program bekerja dengan cara membaca input string, lalu menjalankan transisi PDA dari state awal hingga state akhir sesuai aturan yang tersedia. Setiap langkah akan dicatat sebagai konfigurasi PDA yang berisi state saat ini, sisa input, dan isi stack. Penerimaan string dilakukan berdasarkan **final state** atau **empty stack**, sesuai mode yang dipilih. 

Jika string diterima, program menampilkan pesan seperti:
**DITERIMA: String '...' diterima**.  
Jika string ditolak, program menampilkan pesan:
**DITOLAK: String '...' tidak diterima**. :contentReference[oaicite:6]{index=6}

### 7. Struktur Program
Program terdiri dari beberapa bagian utama:
- `TransisiPDA` untuk menyimpan aturan transisi.
- `KonfigurasiPDA` untuk menyimpan kondisi PDA saat proses berlangsung.
- `LangkahPDA` untuk mencatat jejak komputasi.
- `MesinPDA` sebagai inti logika simulasi.
- `AplikasiPDA` sebagai antarmuka GUI Tkinter. 

### 8. Fasilitas PDA Kustom
Pengguna dapat membuat PDA sendiri dengan mengisi:
- Nama PDA
- States
- Alfabet input
- Alfabet stack
- State awal
- Simbol stack awal
- State final
- Mode acceptance
- Transisi PDA per baris

Program juga menyediakan tombol **“Isi dari PDA Aktif”** agar definisi PDA yang sedang dipakai dapat disalin ke form kustom untuk diedit kembali. 

### 9. Impor dan Ekspor
Definisi PDA dapat disimpan dan dibaca kembali melalui file JSON. Hal ini memudahkan pengguna untuk menyimpan konfigurasi PDA dan membukanya lagi tanpa perlu menginput ulang seluruh transisi. 

### 10. Batch Testing dan Penyimpanan Hasil
Program mendukung pengujian banyak string sekaligus melalui fitur batch testing. Hasil tiap string akan ditampilkan dalam tabel, kemudian dapat disimpan ke file TXT atau CSV. 

### 11. Hasil Output
<img width="1918" height="1025" alt="Screenshot 2026-06-20 083259" src="https://github.com/user-attachments/assets/a808f45a-32b3-4aaa-8645-9019e632e4a3" />
<img width="1918" height="1020" alt="Screenshot 2026-06-20 083314" src="https://github.com/user-attachments/assets/3af08740-fc7e-4f46-9330-fed3ec719afc" />

### 12. Kesimpulan
Berdasarkan implementasinya, program ini merupakan simulator PDA yang cukup lengkap untuk pembelajaran teori automata. Selain menampilkan hasil akhir Accepted atau Rejected, program juga membantu pengguna memahami proses kerja PDA melalui jejak langkah, stack, tabel transisi, dan dukungan PDA kustom. 
