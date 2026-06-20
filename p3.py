import json
import csv
import copy
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional

@dataclass
class TransisiPDA:
    """Merepresentasikan satu aturan transisi PDA."""
    state_asal: str
    simbol_input: str
    simbol_pop: str  
    state_tujuan: str
    simbol_push: List[str] 

    def __str__(self):
        inp = self.simbol_input if self.simbol_input else 'ε'
        pop = self.simbol_pop if self.simbol_pop else 'ε'
        push = ''.join(self.simbol_push) if self.simbol_push else 'ε'
        return f"δ({self.state_asal}, {inp}, {pop}) → ({self.state_tujuan}, {push})"


@dataclass
class KonfigurasiPDA:
    state: str
    sisa_input: str
    stack: List[str]

    def stack_str(self):
        return ''.join(self.stack) if self.stack else '∅'

    def __str__(self):
        inp = self.sisa_input if self.sisa_input else 'ε'
        return f"({self.state}, {inp}, {self.stack_str()})"


@dataclass
class LangkahPDA:
    nomor: int
    konfigurasi_awal: str
    transisi_digunakan: str
    konfigurasi_akhir: str
    keterangan: str

class MesinPDA:
    def __init__(self):
        self.states: Set[str] = set()
        self.alfabet_input: Set[str] = set()
        self.alfabet_stack: Set[str] = set()
        self.transisi: List[TransisiPDA] = []
        self.state_awal: str = ''
        self.simbol_stack_awal: str = ''
        self.state_final: Set[str] = set()
        self.mode_acceptance: str = 'final_state'
        self.nama: str = 'PDA Kustom'
        self.deskripsi: str = ''
        self.batas_langkah: int = 500

    def _get_transisi(self, state: str, simbol_input: str, top_stack: str) -> List[TransisiPDA]:
        hasil = []
        for t in self.transisi:
            if t.state_asal != state:
                continue
            if t.simbol_input != '' and t.simbol_input != simbol_input:
                continue
            if t.simbol_pop != '' and t.simbol_pop != top_stack:
                continue
            hasil.append(t)
        return hasil

    def proses(self, input_string: str) -> Tuple[bool, List[LangkahPDA], str]:
        stack_awal = [self.simbol_stack_awal] if self.simbol_stack_awal else []
        konfigurasi_awal = KonfigurasiPDA(self.state_awal, input_string, list(stack_awal))

        antrian = [(konfigurasi_awal, [])]
        visited = set()
        total_langkah = 0
        jalur_terbaik = []

        while antrian:
            if total_langkah > self.batas_langkah:
                pesan = (f"DITOLAK: Batas komputasi ({self.batas_langkah} langkah) tercapai. "
                         f"Kemungkinan loop atau string terlalu panjang.")
                return False, jalur_terbaik, pesan

            konfig, langkah_list = antrian.pop(0)
            total_langkah += 1

            if self._cek_diterima(konfig):
                pesan = self._buat_pesan_diterima(konfig, input_string)
                return True, langkah_list, pesan
            if len(langkah_list) > len(jalur_terbaik):
                jalur_terbaik = langkah_list

            state_key = (konfig.state, konfig.sisa_input, tuple(konfig.stack))
            if state_key in visited:
                continue
            visited.add(state_key)

            top_stack = konfig.stack[-1] if konfig.stack else ''
            simbol_input_sekarang = konfig.sisa_input[0] if konfig.sisa_input else ''

            if simbol_input_sekarang:
                transisi_cocok = self._get_transisi(konfig.state, simbol_input_sekarang, top_stack)
                transisi_cocok = [t for t in transisi_cocok if t.simbol_input != '']
                for t in transisi_cocok:
                    konfig_baru = self._terapkan_transisi(konfig, t, konsumsi_input=True)
                    if konfig_baru is not None:
                        nomor = len(langkah_list) + 1
                        langkah_baru = LangkahPDA(
                            nomor=nomor,
                            konfigurasi_awal=str(konfig),
                            transisi_digunakan=str(t),
                            konfigurasi_akhir=str(konfig_baru),
                            keterangan=self._buat_keterangan(t, konfig_baru)
                        )
                        antrian.append((konfig_baru, langkah_list + [langkah_baru]))

            transisi_epsilon = self._get_transisi(konfig.state, '', top_stack)
            transisi_epsilon = [t for t in transisi_epsilon if t.simbol_input == '']
            for t in transisi_epsilon:
                konfig_baru = self._terapkan_transisi(konfig, t, konsumsi_input=False)
                if konfig_baru is not None:
                    nomor = len(langkah_list) + 1
                    langkah_baru = LangkahPDA(
                        nomor=nomor,
                        konfigurasi_awal=str(konfig),
                        transisi_digunakan=str(t),
                        konfigurasi_akhir=str(konfig_baru),
                        keterangan=self._buat_keterangan(t, konfig_baru)
                    )
                    antrian.append((konfig_baru, langkah_list + [langkah_baru]))

        pesan = self._buat_pesan_ditolak(input_string, jalur_terbaik)
        return False, jalur_terbaik, pesan

    def _cek_diterima(self, konfig: KonfigurasiPDA) -> bool:
        if konfig.sisa_input:  # masih ada input yang belum dibaca
            return False
        if self.mode_acceptance == 'final_state':
            return konfig.state in self.state_final
        elif self.mode_acceptance == 'empty_stack':
            return len(konfig.stack) == 0
        else:  # both
            return konfig.state in self.state_final or len(konfig.stack) == 0

    def _terapkan_transisi(self, konfig: KonfigurasiPDA, t: TransisiPDA,
                           konsumsi_input: bool) -> Optional[KonfigurasiPDA]:
        """Menerapkan transisi dan menghasilkan konfigurasi baru."""
        stack_baru = list(konfig.stack)

        if t.simbol_pop:
            if not stack_baru or stack_baru[-1] != t.simbol_pop:
                return None
            stack_baru.pop()

        for simbol in reversed(t.simbol_push):
            stack_baru.append(simbol)

        sisa = konfig.sisa_input[1:] if konsumsi_input else konfig.sisa_input

        return KonfigurasiPDA(t.state_tujuan, sisa, stack_baru)

    def _buat_keterangan(self, t: TransisiPDA, konfig_baru: KonfigurasiPDA) -> str:
        parts = []
        if t.simbol_input:
            parts.append(f"Baca '{t.simbol_input}'")
        else:
            parts.append("Transisi ε (tanpa baca input)")

        if t.simbol_pop:
            parts.append(f"pop '{t.simbol_pop}'")
        else:
            parts.append("tidak pop")

        if t.simbol_push:
            parts.append(f"push '{''.join(t.simbol_push)}'")
        else:
            parts.append("tidak push")

        parts.append(f"→ state {konfig_baru.state}")
        return "; ".join(parts)

    def _buat_pesan_diterima(self, konfig: KonfigurasiPDA, input_string: str) -> str:
        w = input_string if input_string else 'ε'
        if self.mode_acceptance == 'final_state':
            return (f"DITERIMA: String '{w}' diterima. "
                    f"Berakhir di state final '{konfig.state}' "
                    f"dengan stack = {konfig.stack_str()}.")
        elif self.mode_acceptance == 'empty_stack':
            return (f"DITERIMA: String '{w}' diterima. "
                    f"Stack kosong di state '{konfig.state}'.")
        else:
            return f"DITERIMA: String '{w}' diterima oleh PDA."

    def _buat_pesan_ditolak(self, input_string: str, jalur: List[LangkahPDA]) -> str:
        w = input_string if input_string else 'ε'
        if self.mode_acceptance == 'final_state':
            return (f"DITOLAK: String '{w}' tidak diterima. "
                    f"Tidak ada jalur komputasi yang berakhir di state final "
                    f"dengan input habis terbaca.")
        elif self.mode_acceptance == 'empty_stack':
            return (f"DITOLAK: String '{w}' tidak diterima. "
                    f"Tidak ada jalur komputasi yang menghasilkan stack kosong "
                    f"dengan input habis terbaca.")
        else:
            return (f"DITOLAK: String '{w}' tidak diterima oleh PDA.")

    def validasi_string(self, teks: str) -> Tuple[bool, str]:
        if not self.alfabet_input:
            return True, "Alfabet input tidak didefinisikan, semua simbol dianggap valid."
        karakter_salah = sorted(set(ch for ch in teks if ch not in self.alfabet_input))
        if karakter_salah:
            return False, (f"Karakter tidak valid: {', '.join(repr(c) for c in karakter_salah)}. "
                           f"Alfabet input: {{{', '.join(sorted(self.alfabet_input))}}}.")
        return True, "String valid."

    def to_dict(self) -> dict:
        return {
            'nama': self.nama,
            'deskripsi': self.deskripsi,
            'states': sorted(self.states),
            'alfabet_input': sorted(self.alfabet_input),
            'alfabet_stack': sorted(self.alfabet_stack),
            'state_awal': self.state_awal,
            'simbol_stack_awal': self.simbol_stack_awal,
            'state_final': sorted(self.state_final),
            'mode_acceptance': self.mode_acceptance,
            'transisi': [
                {
                    'state_asal': t.state_asal,
                    'simbol_input': t.simbol_input,
                    'simbol_pop': t.simbol_pop,
                    'state_tujuan': t.state_tujuan,
                    'simbol_push': t.simbol_push,
                }
                for t in self.transisi
            ]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'MesinPDA':
        mesin = cls()
        mesin.nama = data.get('nama', 'PDA Impor')
        mesin.deskripsi = data.get('deskripsi', '')
        mesin.states = set(data.get('states', []))
        mesin.alfabet_input = set(data.get('alfabet_input', []))
        mesin.alfabet_stack = set(data.get('alfabet_stack', []))
        mesin.state_awal = data.get('state_awal', '')
        mesin.simbol_stack_awal = data.get('simbol_stack_awal', '')
        mesin.state_final = set(data.get('state_final', []))
        mesin.mode_acceptance = data.get('mode_acceptance', 'final_state')
        for td in data.get('transisi', []):
            mesin.transisi.append(TransisiPDA(
                state_asal=td['state_asal'],
                simbol_input=td.get('simbol_input', ''),
                simbol_pop=td.get('simbol_pop', ''),
                state_tujuan=td['state_tujuan'],
                simbol_push=td.get('simbol_push', []),
            ))
        return mesin

def buat_pda_anbn() -> MesinPDA:
    pda = MesinPDA()
    pda.nama = "PDA untuk L = { aⁿbⁿ | n ≥ 1 }"
    pda.deskripsi = (
        "Menerima string yang terdiri dari sejumlah 'a' diikuti sejumlah 'b' "
        "yang sama banyak. Contoh: ab, aabb, aaabbb.\n"
        "Mode acceptance: Final State."
    )
    pda.states = {'q0', 'q1', 'q2', 'q3'}
    pda.alfabet_input = {'a', 'b'}
    pda.alfabet_stack = {'Z', 'A'}
    pda.state_awal = 'q0'
    pda.simbol_stack_awal = 'Z'
    pda.state_final = {'q3'}
    pda.mode_acceptance = 'final_state'

    pda.transisi = [
        TransisiPDA('q0', 'a', 'Z', 'q1', ['A', 'Z']),
        TransisiPDA('q1', 'a', 'A', 'q1', ['A', 'A']),
        TransisiPDA('q1', 'b', 'A', 'q2', []),
        TransisiPDA('q2', 'b', 'A', 'q2', []),
        TransisiPDA('q2', '', 'Z', 'q3', []),
    ]
    return pda


def buat_pda_balanced_parentheses() -> MesinPDA:
    pda = MesinPDA()
    pda.nama = "PDA untuk Kurung Seimbang"
    pda.deskripsi = (
        "Menerima string kurung buka '(' dan kurung tutup ')' yang seimbang.\n"
        "Contoh: (), (()), (())(), ((()))\n"
        "Mode acceptance: Final State."
    )
    pda.states = {'q0', 'q1'}
    pda.alfabet_input = {'(', ')'}
    pda.alfabet_stack = {'Z', 'X'}
    pda.state_awal = 'q0'
    pda.simbol_stack_awal = 'Z'
    pda.state_final = {'q1'}
    pda.mode_acceptance = 'final_state'

    pda.transisi = [
        TransisiPDA('q0', '(', 'Z', 'q0', ['X', 'Z']),
        TransisiPDA('q0', '(', 'X', 'q0', ['X', 'X']),
        TransisiPDA('q0', ')', 'X', 'q0', []),
        TransisiPDA('q0', '', 'Z', 'q1', []),
    ]
    return pda


def buat_pda_wcwr() -> MesinPDA:
    pda = MesinPDA()
    pda.nama = "PDA untuk L = { w#wᴿ | w ∈ {a,b}* }"
    pda.deskripsi = (
        "Menerima string berbentuk w#w^R, yaitu string w diikuti '#' "
        "lalu diikuti pembalikan w.\n"
        "Contoh: #, a#a, ab#ba, aab#baa, abb#bba\n"
        "Mode acceptance: Final State."
    )
    pda.states = {'q0', 'q1', 'q2'}
    pda.alfabet_input = {'a', 'b', '#'}
    pda.alfabet_stack = {'Z', 'A', 'B'}
    pda.state_awal = 'q0'
    pda.simbol_stack_awal = 'Z'
    pda.state_final = {'q2'}
    pda.mode_acceptance = 'final_state'

    pda.transisi = [
        TransisiPDA('q0', 'a', 'Z', 'q0', ['A', 'Z']),
        TransisiPDA('q0', 'a', 'A', 'q0', ['A', 'A']),
        TransisiPDA('q0', 'a', 'B', 'q0', ['A', 'B']),
        TransisiPDA('q0', 'b', 'Z', 'q0', ['B', 'Z']),
        TransisiPDA('q0', 'b', 'A', 'q0', ['B', 'A']),
        TransisiPDA('q0', 'b', 'B', 'q0', ['B', 'B']),
        TransisiPDA('q0', '#', 'Z', 'q1', ['Z']),
        TransisiPDA('q0', '#', 'A', 'q1', ['A']),
        TransisiPDA('q0', '#', 'B', 'q1', ['B']),
        TransisiPDA('q1', 'a', 'A', 'q1', []),
        TransisiPDA('q1', 'b', 'B', 'q1', []),
        TransisiPDA('q1', '', 'Z', 'q2', []),
    ]
    return pda


def buat_pda_equal_ab() -> MesinPDA:
    pda = MesinPDA()
    pda.nama = "PDA untuk L = { w | #a = #b }"
    pda.deskripsi = (
        "Menerima string yang mengandung jumlah 'a' sama dengan jumlah 'b' "
        "dalam urutan apa pun.\n"
        "Contoh: ab, ba, aabb, abba, baba, abab, ε (string kosong)\n"
        "Mode acceptance: Final State."
    )
    pda.states = {'q0', 'q1'}
    pda.alfabet_input = {'a', 'b'}
    pda.alfabet_stack = {'Z', 'A', 'B'}
    pda.state_awal = 'q0'
    pda.simbol_stack_awal = 'Z'
    pda.state_final = {'q1'}
    pda.mode_acceptance = 'final_state'

    pda.transisi = [
        TransisiPDA('q0', 'a', 'Z', 'q0', ['A', 'Z']),
        TransisiPDA('q0', 'a', 'A', 'q0', ['A', 'A']),
        TransisiPDA('q0', 'a', 'B', 'q0', []),
        TransisiPDA('q0', 'b', 'Z', 'q0', ['B', 'Z']),
        TransisiPDA('q0', 'b', 'B', 'q0', ['B', 'B']),
        TransisiPDA('q0', 'b', 'A', 'q0', []),
        TransisiPDA('q0', '', 'Z', 'q1', []),
    ]
    return pda


def buat_pda_anbncn_approx() -> MesinPDA:
    pda = MesinPDA()
    pda.nama = "PDA untuk L = { aⁿbᵐ | n ≤ m ≤ 2n }"
    pda.deskripsi = (
        "Menerima string yang terdiri dari sejumlah 'a' diikuti sejumlah 'b', "
        "dengan jumlah b antara n hingga 2n.\n"
        "Contoh: ab, abb, aabb, aabbb, aabbbb, aaabbb\n"
        "Mode acceptance: Final State."
    )
    pda.states = {'q0', 'q1', 'q2', 'q3'}
    pda.alfabet_input = {'a', 'b'}
    pda.alfabet_stack = {'Z', 'A'}
    pda.state_awal = 'q0'
    pda.simbol_stack_awal = 'Z'
    pda.state_final = {'q3'}
    pda.mode_acceptance = 'final_state'

    pda.transisi = [
        TransisiPDA('q0', 'a', 'Z', 'q1', ['A', 'Z']),  
        TransisiPDA('q0', 'a', 'Z', 'q1', ['A', 'A', 'Z']),
        TransisiPDA('q1', 'b', 'A', 'q2', []),
        TransisiPDA('q2', 'b', 'A', 'q2', []),
        TransisiPDA('q2', '', 'Z', 'q3', []),
    ]
    return pda


PRESET_PDA = {
    "aⁿbⁿ (n ≥ 1)": buat_pda_anbn,
    "Kurung Seimbang": buat_pda_balanced_parentheses,
    "w#wᴿ (palindrome)": buat_pda_wcwr,
    "Jumlah a = Jumlah b": buat_pda_equal_ab,
    "aⁿbᵐ (n ≤ m ≤ 2n)": buat_pda_anbncn_approx,
}

class AplikasiPDA(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulator PDA - Pushdown Automaton")
        self.geometry("1320x840")
        self.minsize(1100, 700)

        self.mesin: Optional[MesinPDA] = None
        self.langkah_terakhir: List[LangkahPDA] = []
        self.hasil_terakhir: str = ""
        self.batch_results: List[Tuple[str, bool, str]] = []

        self._atur_style()
        self._bangun_ui()
        self._muat_preset_default()

    def _atur_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Judul.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Subjudul.TLabel", font=("Segoe UI", 10))
        style.configure("Hasil.TLabel", font=("Segoe UI", 13, "bold"))
        style.configure("Diterima.TLabel", font=("Segoe UI", 14, "bold"), foreground="#1a7f37")
        style.configure("Ditolak.TLabel", font=("Segoe UI", 14, "bold"), foreground="#cf222e")
        style.configure("TButton", padding=5)
        style.configure("Accent.TButton", padding=5, font=("Segoe UI", 10, "bold"))
        style.configure("TNotebook.Tab", padding=(12, 6), font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.configure("Treeview", rowheight=24, font=("Segoe UI", 9))

    def _bangun_ui(self):
        # Frame utama
        utama = ttk.Frame(self, padding=10)
        utama.pack(fill="both", expand=True)
        utama.columnconfigure(1, weight=1)
        utama.rowconfigure(1, weight=1)

        header = ttk.Frame(utama)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        header.columnconfigure(1, weight=1)

        ttk.Label(header, text="⚙ Simulator PDA", style="Judul.TLabel").grid(
            row=0, column=0, sticky="w"
        )

        self.deskripsi_var = tk.StringVar(value="Pilih atau definisikan PDA untuk memulai simulasi.")
        ttk.Label(header, textvariable=self.deskripsi_var, style="Subjudul.TLabel",
                  wraplength=900).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))

        panel_kiri = ttk.Frame(utama, width=380)
        panel_kiri.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        panel_kiri.columnconfigure(0, weight=1)

        pilih_frame = ttk.LabelFrame(panel_kiri, text="Pilih / Muat PDA", padding=8)
        pilih_frame.grid(row=0, column=0, sticky="ew")
        pilih_frame.columnconfigure(0, weight=1)

        ttk.Label(pilih_frame, text="Preset PDA:").grid(row=0, column=0, sticky="w")
        self.preset_var = tk.StringVar()
        preset_names = list(PRESET_PDA.keys())
        self.preset_combo = ttk.Combobox(
            pilih_frame, textvariable=self.preset_var,
            values=preset_names, state="readonly", width=30
        )
        self.preset_combo.grid(row=1, column=0, sticky="ew", pady=(2, 6))
        self.preset_combo.bind("<<ComboboxSelected>>", lambda e: self._muat_preset())
        if preset_names:
            self.preset_combo.current(0)

        btn_frame_pda = ttk.Frame(pilih_frame)
        btn_frame_pda.grid(row=2, column=0, sticky="ew")
        btn_frame_pda.columnconfigure(0, weight=1)
        btn_frame_pda.columnconfigure(1, weight=1)
        btn_frame_pda.columnconfigure(2, weight=1)

        ttk.Button(btn_frame_pda, text="Muat Preset", command=self._muat_preset).grid(
            row=0, column=0, padx=2, sticky="ew")
        ttk.Button(btn_frame_pda, text="Impor JSON", command=self._impor_pda).grid(
            row=0, column=1, padx=2, sticky="ew")
        ttk.Button(btn_frame_pda, text="Ekspor JSON", command=self._ekspor_pda).grid(
            row=0, column=2, padx=2, sticky="ew")

        input_frame = ttk.LabelFrame(panel_kiri, text="Input String", padding=8)
        input_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        input_frame.columnconfigure(0, weight=1)

        self.input_var = tk.StringVar()
        self.input_var.trace_add("write", lambda *args: self._validasi_input_langsung())

        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_var,
                                     font=("Consolas", 15))
        self.input_entry.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self.input_entry.focus()

        self.validasi_var = tk.StringVar(value="")
        ttk.Label(input_frame, textvariable=self.validasi_var,
                  wraplength=340, font=("Segoe UI", 8)).grid(
            row=1, column=0, sticky="w", pady=(0, 4))

        ttk.Label(input_frame, text="Ketik ε atau biarkan kosong untuk string kosong (epsilon).",
                  font=("Segoe UI", 8), foreground="gray").grid(
            row=2, column=0, sticky="w", pady=(0, 6))

        btn_frame_input = ttk.Frame(input_frame)
        btn_frame_input.grid(row=3, column=0, sticky="ew")
        btn_frame_input.columnconfigure(0, weight=1)
        btn_frame_input.columnconfigure(1, weight=1)

        ttk.Button(btn_frame_input, text="▶  Proses PDA", style="Accent.TButton",
                   command=self._proses_input).grid(row=0, column=0, padx=2, sticky="ew")
        ttk.Button(btn_frame_input, text="Bersihkan", command=self._bersihkan).grid(
            row=0, column=1, padx=2, sticky="ew")

        contoh_frame = ttk.LabelFrame(panel_kiri, text="Contoh Cepat", padding=8)
        contoh_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        contoh_frame.columnconfigure(0, weight=1)
        contoh_frame.columnconfigure(1, weight=1)

        ttk.Label(contoh_frame, text="Diterima:", font=("Segoe UI", 9, "bold"),
                  foreground="#1a7f37").grid(row=0, column=0, sticky="w")
        ttk.Label(contoh_frame, text="Ditolak:", font=("Segoe UI", 9, "bold"),
                  foreground="#cf222e").grid(row=0, column=1, sticky="w")

        self.list_ok = tk.Listbox(contoh_frame, height=5, exportselection=False,
                                  font=("Consolas", 10), selectbackground="#d4edda")
        self.list_no = tk.Listbox(contoh_frame, height=5, exportselection=False,
                                  font=("Consolas", 10), selectbackground="#f8d7da")
        self.list_ok.grid(row=1, column=0, sticky="ew", padx=(0, 4))
        self.list_no.grid(row=1, column=1, sticky="ew", padx=(4, 0))

        self.list_ok.bind("<<ListboxSelect>>", lambda e: self._pilih_contoh(self.list_ok))
        self.list_no.bind("<<ListboxSelect>>", lambda e: self._pilih_contoh(self.list_no))

        batch_frame = ttk.LabelFrame(panel_kiri, text="Pengujian Batch (Multi-String)", padding=8)
        batch_frame.grid(row=3, column=0, sticky="nsew", pady=(8, 0))
        batch_frame.columnconfigure(0, weight=1)
        panel_kiri.rowconfigure(3, weight=1)

        ttk.Label(batch_frame, text="Masukkan satu string per baris:",
                  font=("Segoe UI", 8)).grid(row=0, column=0, sticky="w")

        self.batch_text = ScrolledText(batch_frame, height=5, wrap="word",
                                       font=("Consolas", 10))
        self.batch_text.grid(row=1, column=0, sticky="nsew", pady=(2, 4))
        batch_frame.rowconfigure(1, weight=1)

        btn_batch = ttk.Frame(batch_frame)
        btn_batch.grid(row=2, column=0, sticky="ew")
        btn_batch.columnconfigure(0, weight=1)
        btn_batch.columnconfigure(1, weight=1)

        ttk.Button(btn_batch, text="Proses Batch", command=self._proses_batch).grid(
            row=0, column=0, padx=2, sticky="ew")
        ttk.Button(btn_batch, text="Simpan Hasil", command=self._simpan_hasil).grid(
            row=0, column=1, padx=2, sticky="ew")

        panel_kanan = ttk.Frame(utama)
        panel_kanan.grid(row=1, column=1, sticky="nsew")
        panel_kanan.columnconfigure(0, weight=1)
        panel_kanan.rowconfigure(1, weight=1)

        hasil_frame = ttk.LabelFrame(panel_kanan, text="Hasil Identifikasi", padding=8)
        hasil_frame.grid(row=0, column=0, sticky="ew")
        hasil_frame.columnconfigure(0, weight=1)

        self.hasil_var = tk.StringVar(value="Masukkan string, lalu klik Proses PDA.")
        self.hasil_label = ttk.Label(hasil_frame, textvariable=self.hasil_var,
                                     style="Hasil.TLabel")
        self.hasil_label.grid(row=0, column=0, sticky="w")

        self.detail_var = tk.StringVar(value="-")
        ttk.Label(hasil_frame, textvariable=self.detail_var, wraplength=700,
                  font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.notebook = ttk.Notebook(panel_kanan)
        self.notebook.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        tab_jejak = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab_jejak, text="Jejak Langkah")
        tab_jejak.columnconfigure(0, weight=1)
        tab_jejak.rowconfigure(0, weight=1)

        kolom_jejak = ("No", "Konfigurasi Awal", "Transisi", "Konfigurasi Akhir", "Keterangan")
        self.tabel_jejak = ttk.Treeview(tab_jejak, columns=kolom_jejak, show="headings")
        ukuran_jejak = {"No": 40, "Konfigurasi Awal": 180, "Transisi": 230,
                        "Konfigurasi Akhir": 180, "Keterangan": 280}
        for k in kolom_jejak:
            self.tabel_jejak.heading(k, text=k)
            self.tabel_jejak.column(k, width=ukuran_jejak[k], anchor="w")

        yscroll_jejak = ttk.Scrollbar(tab_jejak, orient="vertical",
                                      command=self.tabel_jejak.yview)
        xscroll_jejak = ttk.Scrollbar(tab_jejak, orient="horizontal",
                                      command=self.tabel_jejak.xview)
        self.tabel_jejak.configure(yscrollcommand=yscroll_jejak.set,
                                   xscrollcommand=xscroll_jejak.set)
        self.tabel_jejak.grid(row=0, column=0, sticky="nsew")
        yscroll_jejak.grid(row=0, column=1, sticky="ns")
        xscroll_jejak.grid(row=1, column=0, sticky="ew")

        tab_definisi = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab_definisi, text="Definisi PDA")
        tab_definisi.columnconfigure(0, weight=1)
        tab_definisi.rowconfigure(0, weight=1)

        self.definisi_text = ScrolledText(tab_definisi, wrap="word", font=("Consolas", 10))
        self.definisi_text.pack(fill="both", expand=True)

        tab_transisi = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab_transisi, text="Tabel Transisi")
        tab_transisi.columnconfigure(0, weight=1)
        tab_transisi.rowconfigure(0, weight=1)

        kolom_trans = ("No", "State Asal", "Input", "Pop", "State Tujuan", "Push")
        self.tabel_transisi = ttk.Treeview(tab_transisi, columns=kolom_trans, show="headings")
        ukuran_trans = {"No": 40, "State Asal": 100, "Input": 80, "Pop": 80,
                        "State Tujuan": 100, "Push": 100}
        for k in kolom_trans:
            self.tabel_transisi.heading(k, text=k)
            self.tabel_transisi.column(k, width=ukuran_trans[k], anchor="w")

        yscroll_trans = ttk.Scrollbar(tab_transisi, orient="vertical",
                                      command=self.tabel_transisi.yview)
        self.tabel_transisi.configure(yscrollcommand=yscroll_trans.set)
        self.tabel_transisi.grid(row=0, column=0, sticky="nsew")
        yscroll_trans.grid(row=0, column=1, sticky="ns")

        tab_stack = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab_stack, text="Visualisasi Stack")
        tab_stack.columnconfigure(0, weight=1)
        tab_stack.rowconfigure(0, weight=1)

        self.stack_text = ScrolledText(tab_stack, wrap="word", font=("Consolas", 10))
        self.stack_text.pack(fill="both", expand=True)

        tab_batch = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab_batch, text="Hasil Batch")
        tab_batch.columnconfigure(0, weight=1)
        tab_batch.rowconfigure(0, weight=1)

        kolom_batch = ("No", "String", "Hasil", "Keterangan")
        self.tabel_batch = ttk.Treeview(tab_batch, columns=kolom_batch, show="headings")
        ukuran_batch = {"No": 40, "String": 200, "Hasil": 100, "Keterangan": 500}
        for k in kolom_batch:
            self.tabel_batch.heading(k, text=k)
            self.tabel_batch.column(k, width=ukuran_batch[k], anchor="w")

        self.tabel_batch.tag_configure("acc", foreground="#1a7f37")
        self.tabel_batch.tag_configure("rej", foreground="#cf222e")

        yscroll_batch = ttk.Scrollbar(tab_batch, orient="vertical",
                                      command=self.tabel_batch.yview)
        self.tabel_batch.configure(yscrollcommand=yscroll_batch.set)
        self.tabel_batch.grid(row=0, column=0, sticky="nsew")
        yscroll_batch.grid(row=0, column=1, sticky="ns")

        tab_kustom = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab_kustom, text="Buat PDA Kustom")
        self._bangun_tab_kustom(tab_kustom)

        self.status_var = tk.StringVar(value="Siap.")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w",
                               padding=(6, 3))
        status_bar.pack(fill="x", side="bottom")
        self.bind("<Return>", lambda e: self._proses_input())

    def _bangun_tab_kustom(self, parent):
        """Membangun tab untuk mendefinisikan PDA kustom."""
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

        kiri = ttk.Frame(parent)
        kiri.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        kiri.columnconfigure(1, weight=1)

        fields = [
            ("Nama PDA:", "kustom_nama"),
            ("States (pisah koma):", "kustom_states"),
            ("Alfabet Input (pisah koma):", "kustom_alfabet"),
            ("Alfabet Stack (pisah koma):", "kustom_stack_alf"),
            ("State Awal:", "kustom_state_awal"),
            ("Simbol Stack Awal:", "kustom_stack_awal_simbol"),
            ("State Final (pisah koma):", "kustom_state_final"),
        ]

        self.kustom_vars = {}
        for i, (label_text, var_name) in enumerate(fields):
            ttk.Label(kiri, text=label_text, font=("Segoe UI", 9)).grid(
                row=i, column=0, sticky="w", pady=2)
            var = tk.StringVar()
            self.kustom_vars[var_name] = var
            ttk.Entry(kiri, textvariable=var, font=("Consolas", 10)).grid(
                row=i, column=1, sticky="ew", pady=2, padx=(4, 0))

        ttk.Label(kiri, text="Mode Acceptance:", font=("Segoe UI", 9)).grid(
            row=len(fields), column=0, sticky="w", pady=2)
        self.kustom_mode_var = tk.StringVar(value="final_state")
        mode_frame = ttk.Frame(kiri)
        mode_frame.grid(row=len(fields), column=1, sticky="w", pady=2)
        ttk.Radiobutton(mode_frame, text="Final State", variable=self.kustom_mode_var,
                        value="final_state").pack(side="left", padx=(0, 8))
        ttk.Radiobutton(mode_frame, text="Empty Stack", variable=self.kustom_mode_var,
                        value="empty_stack").pack(side="left")

        kanan = ttk.Frame(parent)
        kanan.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        kanan.columnconfigure(0, weight=1)
        kanan.rowconfigure(1, weight=1)

        ttk.Label(kanan, text="Transisi (satu per baris, format: state_asal,input,pop,state_tujuan,push)",
                  font=("Segoe UI", 8), wraplength=400).grid(row=0, column=0, sticky="w")
        ttk.Label(kanan, text="Gunakan 'e' atau kosong untuk epsilon. Push bisa multi-karakter (misal: AZ).",
                  font=("Segoe UI", 8), foreground="gray").grid(row=0, column=0, sticky="w", pady=(16, 0))

        self.kustom_transisi_text = ScrolledText(kanan, height=10, wrap="word",
                                                  font=("Consolas", 10))
        self.kustom_transisi_text.grid(row=1, column=0, sticky="nsew", pady=(4, 4))

        ttk.Label(kanan, text="Contoh transisi:\nq0,a,Z,q1,AZ\nq1,b,A,q1,e\nq1,e,Z,q2,e",
                  font=("Consolas", 9), foreground="gray").grid(row=2, column=0, sticky="w")

        btn_kustom = ttk.Frame(parent)
        btn_kustom.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        btn_kustom.columnconfigure(0, weight=1)
        btn_kustom.columnconfigure(1, weight=1)

        ttk.Button(btn_kustom, text="Terapkan PDA Kustom", style="Accent.TButton",
                   command=self._terapkan_kustom).grid(row=0, column=0, padx=2, sticky="ew")
        ttk.Button(btn_kustom, text="Isi dari PDA Aktif", command=self._isi_dari_aktif).grid(
            row=0, column=1, padx=2, sticky="ew")

    def _muat_preset_default(self):
        self._muat_preset()

    def _muat_preset(self):
        nama = self.preset_var.get()
        if nama not in PRESET_PDA:
            messagebox.showwarning("Pilih Preset", "Silakan pilih preset PDA terlebih dahulu.")
            return
        self.mesin = PRESET_PDA[nama]()
        self._perbarui_tampilan_pda()
        self._perbarui_contoh_cepat()
        self._bersihkan_hasil()
        self.status_var.set(f"PDA dimuat: {self.mesin.nama}")

    def _perbarui_tampilan_pda(self):
        if not self.mesin:
            return

        self.deskripsi_var.set(f"{self.mesin.nama} — {self.mesin.deskripsi[:120]}")

        # Tab Definisi PDA
        lines = []
        lines.append(f"Nama         : {self.mesin.nama}")
        lines.append(f"Deskripsi    : {self.mesin.deskripsi}")
        lines.append("")
        lines.append(f"States (Q)         : {{ {', '.join(sorted(self.mesin.states))} }}")
        lines.append(f"Alfabet Input (Σ)  : {{ {', '.join(sorted(self.mesin.alfabet_input))} }}")
        lines.append(f"Alfabet Stack (Γ)  : {{ {', '.join(sorted(self.mesin.alfabet_stack))} }}")
        lines.append(f"State Awal (q₀)    : {self.mesin.state_awal}")
        lines.append(f"Simbol Stack (Z₀)  : {self.mesin.simbol_stack_awal if self.mesin.simbol_stack_awal else 'ε'}")
        lines.append(f"State Final (F)    : {{ {', '.join(sorted(self.mesin.state_final))} }}")
        lines.append(f"Mode Acceptance    : {self.mesin.mode_acceptance}")
        lines.append("")
        lines.append("Definisi Formal:")
        lines.append(f"  PDA M = (Q, Σ, Γ, δ, q₀, Z₀, F)")
        lines.append("")
        lines.append("Fungsi Transisi (δ):")
        lines.append("─" * 60)
        for i, t in enumerate(self.mesin.transisi, 1):
            lines.append(f"  {i:2d}. {t}")
        lines.append("─" * 60)

        self.definisi_text.config(state="normal")
        self.definisi_text.delete("1.0", tk.END)
        self.definisi_text.insert("1.0", "\n".join(lines))
        self.definisi_text.config(state="disabled")

        # Tab Tabel Transisi
        for item in self.tabel_transisi.get_children():
            self.tabel_transisi.delete(item)
        for i, t in enumerate(self.mesin.transisi, 1):
            inp = t.simbol_input if t.simbol_input else 'ε'
            pop = t.simbol_pop if t.simbol_pop else 'ε'
            push = ''.join(t.simbol_push) if t.simbol_push else 'ε'
            self.tabel_transisi.insert("", "end", values=(i, t.state_asal, inp, pop,
                                                          t.state_tujuan, push))

    def _perbarui_contoh_cepat(self):
        self.list_ok.delete(0, tk.END)
        self.list_no.delete(0, tk.END)

        if not self.mesin:
            return

        contoh = self._generate_contoh()
        for s in contoh['diterima']:
            self.list_ok.insert(tk.END, s if s else "ε")
        for s in contoh['ditolak']:
            self.list_no.insert(tk.END, s if s else "ε")

    def _generate_contoh(self) -> dict:
        nama = self.mesin.nama if self.mesin else ""
        if "aⁿbⁿ" in nama and "n ≥ 1" in nama:
            return {
                'diterima': ["ab", "aabb", "aaabbb", "aaaabbbb", "aaaaabbbbb"],
                'ditolak': ["", "a", "b", "ba", "aab", "abb", "abab", "abc"]
            }
        elif "Kurung" in nama:
            return {
                'diterima': ["()", "(())", "()()", "((()))", "(()())"],
                'ditolak': ["", "(", ")", "(()", "())", ")(", "(()(", "abc"]
            }
        elif "w#wᴿ" in nama or "w#w" in nama:
            return {
                'diterima': ["#", "a#a", "b#b", "ab#ba", "aab#baa", "abb#bba"],
                'ditolak': ["", "a#b", "ab#ab", "aa#a", "ab", "#a", "abc"]
            }
        elif "#a = #b" in nama:
            return {
                'diterima': ["", "ab", "ba", "aabb", "abba", "abab", "baba", "bbaa"],
                'ditolak': ["a", "b", "aab", "bba", "aaab", "bbb", "aaa"]
            }
        elif "n ≤ m ≤ 2n" in nama:
            return {
                'diterima': ["ab", "abb", "aabb", "aabbb", "aabbbb", "aaabbb"],
                'ditolak': ["", "a", "b", "ba", "abbb", "aab", "aabbbbb"]
            }
        else:
            return {'diterima': [], 'ditolak': []}

    def _proses_input(self):
        if not self.mesin:
            messagebox.showwarning("PDA Belum Dimuat",
                                   "Muat PDA terlebih dahulu (pilih preset atau definisikan kustom).")
            return

        teks = self.input_var.get().strip()
        if teks in ('ε', 'epsilon', 'eps'):
            teks = ''

        if teks:
            valid, pesan_validasi = self.mesin.validasi_string(teks)
            if not valid:
                self.hasil_var.set("INPUT TIDAK VALID")
                self.hasil_label.configure(style="Ditolak.TLabel")
                self.detail_var.set(pesan_validasi)
                self.status_var.set(pesan_validasi)
                return

        diterima, langkah_list, pesan = self.mesin.proses(teks)
        self.langkah_terakhir = langkah_list

        if diterima:
            self.hasil_var.set("✓  DITERIMA (ACCEPTED)")
            self.hasil_label.configure(style="Diterima.TLabel")
        else:
            self.hasil_var.set("✗  DITOLAK (REJECTED)")
            self.hasil_label.configure(style="Ditolak.TLabel")

        self.detail_var.set(pesan)

        self._kosongkan_tabel(self.tabel_jejak)
        for step in langkah_list:
            self.tabel_jejak.insert("", "end", values=(
                step.nomor, step.konfigurasi_awal, step.transisi_digunakan,
                step.konfigurasi_akhir, step.keterangan
            ))

        self._visualisasi_stack(teks, langkah_list, diterima)

        self._simpan_hasil_terakhir(teks, diterima, pesan, langkah_list)

        self.notebook.select(0)

        self.status_var.set(pesan)

    def _visualisasi_stack(self, teks: str, langkah_list: List[LangkahPDA], diterima: bool):
        lines = []
        lines.append("═" * 55)
        lines.append(f"  VISUALISASI STACK - String: '{teks if teks else 'ε'}'")
        lines.append("═" * 55)
        lines.append("")

        if not langkah_list:
            lines.append("  Tidak ada langkah komputasi.")
            if not teks:
                lines.append("  Input: ε (string kosong)")
                lines.append(f"  State awal: {self.mesin.state_awal}")
                stack_awal = self.mesin.simbol_stack_awal if self.mesin.simbol_stack_awal else '∅'
                lines.append(f"  Stack awal: [{stack_awal}]")

                if diterima:
                    lines.append("\n  → String kosong DITERIMA oleh PDA.")
                else:
                    lines.append("\n  → String kosong DITOLAK oleh PDA.")
        else:
            stack_init = [self.mesin.simbol_stack_awal] if self.mesin.simbol_stack_awal else []
            lines.append(f"  Konfigurasi Awal:")
            lines.append(f"  State: {self.mesin.state_awal}")
            lines.append(f"  Input: {teks if teks else 'ε'}")
            lines.append(f"  Stack: {self._gambar_stack(stack_init)}")
            lines.append("")
            lines.append("─" * 55)

            for step in langkah_list:
                lines.append(f"\n  Langkah {step.nomor}:")
                lines.append(f"  {step.transisi_digunakan}")
                lines.append(f"  {step.keterangan}")
                lines.append(f"  Konfigurasi: {step.konfigurasi_akhir}")

                stack_visual = self._parse_stack_dari_konfigurasi(step.konfigurasi_akhir)
                lines.append(f"  Stack: {stack_visual}")
                lines.append("  " + "─" * 50)

        lines.append("")
        lines.append("═" * 55)
        status = "DITERIMA ✓" if diterima else "DITOLAK ✗"
        lines.append(f"  Hasil akhir: {status}")
        lines.append("═" * 55)

        self.stack_text.config(state="normal")
        self.stack_text.delete("1.0", tk.END)
        self.stack_text.insert("1.0", "\n".join(lines))
        self.stack_text.config(state="disabled")

    def _gambar_stack(self, stack: List[str]) -> str:
        if not stack:
            return "[ ∅ ] (kosong)"
        # Top of stack di kanan
        visual = " | ".join(reversed(stack))
        top = stack[-1]
        return f"[ {visual} ]  ← top: {top}"

    def _parse_stack_dari_konfigurasi(self, konfig_str: str) -> str:
        try:
            inner = konfig_str.strip("()")
            parts = inner.rsplit(", ", 2)
            if len(parts) >= 3:
                stack_part = parts[2]
                if stack_part == '∅':
                    return "[ ∅ ] (kosong)"
                stack_list = list(stack_part)
                return self._gambar_stack(stack_list)
        except Exception:
            pass
        return konfig_str

    def _simpan_hasil_terakhir(self, teks, diterima, pesan, langkah_list):
        lines = []
        lines.append(f"String input    : {teks if teks else 'ε'}")
        lines.append(f"Panjang string  : {len(teks)}")
        lines.append(f"PDA             : {self.mesin.nama}")
        lines.append(f"Mode Acceptance : {self.mesin.mode_acceptance}")
        lines.append(f"Hasil           : {'DITERIMA' if diterima else 'DITOLAK'}")
        lines.append(f"Penjelasan      : {pesan}")
        lines.append("")
        lines.append("Jejak Langkah:")
        lines.append("-" * 80)
        for step in langkah_list:
            lines.append(f"  {step.nomor}. {step.konfigurasi_awal}")
            lines.append(f"     {step.transisi_digunakan}")
            lines.append(f"     → {step.konfigurasi_akhir}")
            lines.append(f"     Ket: {step.keterangan}")
            lines.append("")
        self.hasil_terakhir = "\n".join(lines)

    def _validasi_input_langsung(self):
        if not self.mesin:
            self.validasi_var.set("")
            return
        teks = self.input_var.get().strip()
        if teks in ('ε', 'epsilon', 'eps', ''):
            self.validasi_var.set("String kosong (ε) — siap diproses.")
            return
        valid, pesan = self.mesin.validasi_string(teks)
        self.validasi_var.set(pesan)

    def _pilih_contoh(self, listbox):
        pilihan = listbox.curselection()
        if not pilihan:
            return
        nilai = listbox.get(pilihan[0])
        if nilai == "ε":
            nilai = ""
        self.input_var.set(nilai)
        self.after(50, self._proses_input)

    def _proses_batch(self):
        if not self.mesin:
            messagebox.showwarning("PDA Belum Dimuat",
                                   "Muat PDA terlebih dahulu sebelum pengujian batch.")
            return

        teks = self.batch_text.get("1.0", tk.END).strip()
        if not teks:
            messagebox.showwarning("Input Kosong", "Masukkan setidaknya satu string untuk batch testing.")
            return

        baris = teks.splitlines()
        self._kosongkan_tabel(self.tabel_batch)
        self.batch_results = []

        total_acc = 0
        total_rej = 0

        for i, raw in enumerate(baris, 1):
            s = raw.strip()
            if s in ('ε', 'epsilon', 'eps'):
                s = ''

            diterima, langkah, pesan = self.mesin.proses(s)
            status = "DITERIMA" if diterima else "DITOLAK"
            tag = "acc" if diterima else "rej"
            display_s = s if s else "ε"

            self.tabel_batch.insert("", "end", values=(i, display_s, status, pesan), tags=(tag,))
            self.batch_results.append((display_s, diterima, pesan))

            if diterima:
                total_acc += 1
            else:
                total_rej += 1

        self.notebook.select(4)
        self.status_var.set(
            f"Batch selesai: {len(baris)} string diuji | "
            f"Diterima: {total_acc} | Ditolak: {total_rej}"
        )

    def _terapkan_kustom(self):
        try:
            pda = MesinPDA()

            pda.nama = self.kustom_vars['kustom_nama'].get().strip() or "PDA Kustom"

            states_raw = self.kustom_vars['kustom_states'].get().strip()
            if not states_raw:
                messagebox.showerror("Error", "States tidak boleh kosong.")
                return
            pda.states = set(s.strip() for s in states_raw.split(',') if s.strip())

            alf_raw = self.kustom_vars['kustom_alfabet'].get().strip()
            pda.alfabet_input = set(s.strip() for s in alf_raw.split(',') if s.strip())

            stack_alf_raw = self.kustom_vars['kustom_stack_alf'].get().strip()
            pda.alfabet_stack = set(s.strip() for s in stack_alf_raw.split(',') if s.strip())

            pda.state_awal = self.kustom_vars['kustom_state_awal'].get().strip()
            if pda.state_awal not in pda.states:
                messagebox.showerror("Error",
                                     f"State awal '{pda.state_awal}' tidak terdapat dalam states.")
                return

            pda.simbol_stack_awal = self.kustom_vars['kustom_stack_awal_simbol'].get().strip()

            final_raw = self.kustom_vars['kustom_state_final'].get().strip()
            pda.state_final = set(s.strip() for s in final_raw.split(',') if s.strip())

            pda.mode_acceptance = self.kustom_mode_var.get()

            transisi_raw = self.kustom_transisi_text.get("1.0", tk.END).strip()
            if not transisi_raw:
                messagebox.showerror("Error", "Transisi tidak boleh kosong.")
                return

            pda.transisi = []
            for nomor, line in enumerate(transisi_raw.splitlines(), 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(',')
                if len(parts) != 5:
                    messagebox.showerror("Error",
                                         f"Baris transisi {nomor} format salah: '{line}'\n"
                                         f"Format: state_asal,input,pop,state_tujuan,push")
                    return

                state_asal = parts[0].strip()
                simbol_input = parts[1].strip()
                simbol_pop = parts[2].strip()
                state_tujuan = parts[3].strip()
                simbol_push_raw = parts[4].strip()

                if simbol_input.lower() in ('e', 'ε', 'eps', 'epsilon', ''):
                    simbol_input = ''
                if simbol_pop.lower() in ('e', 'ε', 'eps', 'epsilon', ''):
                    simbol_pop = ''
                if simbol_push_raw.lower() in ('e', 'ε', 'eps', 'epsilon', ''):
                    simbol_push = []
                else:
                    simbol_push = list(simbol_push_raw)

                pda.transisi.append(TransisiPDA(state_asal, simbol_input, simbol_pop,
                                                state_tujuan, simbol_push))

            for t in pda.transisi:
                if t.state_asal not in pda.states:
                    messagebox.showerror("Error",
                                         f"State asal '{t.state_asal}' dalam transisi tidak ada di states.")
                    return
                if t.state_tujuan not in pda.states:
                    messagebox.showerror("Error",
                                         f"State tujuan '{t.state_tujuan}' dalam transisi tidak ada di states.")
                    return

            self.mesin = pda
            self._perbarui_tampilan_pda()
            self._perbarui_contoh_cepat()
            self._bersihkan_hasil()

            messagebox.showinfo("Berhasil",
                                f"PDA Kustom '{pda.nama}' berhasil diterapkan!\n"
                                f"States: {len(pda.states)} | "
                                f"Transisi: {len(pda.transisi)}")
            self.status_var.set(f"PDA Kustom '{pda.nama}' berhasil diterapkan.")

        except Exception as e:
            messagebox.showerror("Error", f"Gagal membuat PDA Kustom:\n{e}")

    def _isi_dari_aktif(self):
        if not self.mesin:
            messagebox.showwarning("Tidak Ada PDA", "Belum ada PDA yang aktif.")
            return

        self.kustom_vars['kustom_nama'].set(self.mesin.nama)
        self.kustom_vars['kustom_states'].set(', '.join(sorted(self.mesin.states)))
        self.kustom_vars['kustom_alfabet'].set(', '.join(sorted(self.mesin.alfabet_input)))
        self.kustom_vars['kustom_stack_alf'].set(', '.join(sorted(self.mesin.alfabet_stack)))
        self.kustom_vars['kustom_state_awal'].set(self.mesin.state_awal)
        self.kustom_vars['kustom_stack_awal_simbol'].set(self.mesin.simbol_stack_awal)
        self.kustom_vars['kustom_state_final'].set(', '.join(sorted(self.mesin.state_final)))
        self.kustom_mode_var.set(self.mesin.mode_acceptance)

        lines = []
        for t in self.mesin.transisi:
            inp = t.simbol_input if t.simbol_input else 'e'
            pop = t.simbol_pop if t.simbol_pop else 'e'
            push = ''.join(t.simbol_push) if t.simbol_push else 'e'
            lines.append(f"{t.state_asal},{inp},{pop},{t.state_tujuan},{push}")

        self.kustom_transisi_text.delete("1.0", tk.END)
        self.kustom_transisi_text.insert("1.0", "\n".join(lines))

        self.notebook.select(5)
        self.status_var.set("Form PDA Kustom diisi dari PDA aktif. Edit sesuai kebutuhan.")

    def _impor_pda(self):
        path = filedialog.askopenfilename(
            title="Impor Definisi PDA (JSON)",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.mesin = MesinPDA.from_dict(data)
            self._perbarui_tampilan_pda()
            self._perbarui_contoh_cepat()
            self._bersihkan_hasil()
            messagebox.showinfo("Berhasil", f"PDA berhasil diimpor dari:\n{path}")
            self.status_var.set(f"PDA diimpor: {self.mesin.nama}")
        except Exception as e:
            messagebox.showerror("Gagal Impor", f"Error membaca file:\n{e}")

    def _ekspor_pda(self):
        if not self.mesin:
            messagebox.showwarning("Tidak Ada PDA", "Belum ada PDA yang aktif untuk diekspor.")
            return
        path = filedialog.asksaveasfilename(
            title="Ekspor Definisi PDA (JSON)",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.mesin.to_dict(), f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Berhasil", f"PDA berhasil diekspor ke:\n{path}")
            self.status_var.set(f"PDA diekspor: {path}")
        except Exception as e:
            messagebox.showerror("Gagal Ekspor", f"Error menyimpan file:\n{e}")

    def _simpan_hasil(self):
        if not self.hasil_terakhir and not self.batch_results:
            messagebox.showwarning("Belum Ada Hasil",
                                   "Proses string terlebih dahulu sebelum menyimpan.")
            return

        path = filedialog.asksaveasfilename(
            title="Simpan Hasil Pengujian PDA",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            if path.endswith('.csv') and self.batch_results:
                with open(path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["No", "String", "Hasil", "Keterangan"])
                    for i, (s, acc, pesan) in enumerate(self.batch_results, 1):
                        writer.writerow([i, s, "DITERIMA" if acc else "DITOLAK", pesan])
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(f"Simulator PDA - Hasil Pengujian\n")
                    f.write(f"PDA: {self.mesin.nama if self.mesin else 'N/A'}\n")
                    f.write(f"{'=' * 60}\n\n")

                    if self.batch_results:
                        f.write("HASIL BATCH TESTING:\n")
                        f.write("-" * 60 + "\n")
                        for i, (s, acc, pesan) in enumerate(self.batch_results, 1):
                            status = "DITERIMA" if acc else "DITOLAK"
                            f.write(f"  {i:3d}. '{s}' → {status}\n")
                            f.write(f"       {pesan}\n\n")
                    elif self.hasil_terakhir:
                        f.write(self.hasil_terakhir)

            messagebox.showinfo("Berhasil", f"Hasil disimpan ke:\n{path}")
            self.status_var.set(f"Hasil disimpan: {path}")
        except Exception as e:
            messagebox.showerror("Gagal Menyimpan", str(e))

    def _kosongkan_tabel(self, tabel: ttk.Treeview):
        for item in tabel.get_children():
            tabel.delete(item)

    def _bersihkan(self):
        self.input_var.set("")
        self._bersihkan_hasil()
        self.input_entry.focus()
        self.status_var.set("Input dibersihkan.")

    def _bersihkan_hasil(self):
        self._kosongkan_tabel(self.tabel_jejak)
        self._kosongkan_tabel(self.tabel_batch)
        self.hasil_var.set("Masukkan string, lalu klik Proses PDA.")
        self.hasil_label.configure(style="Hasil.TLabel")
        self.detail_var.set("-")
        self.langkah_terakhir = []
        self.hasil_terakhir = ""

        self.stack_text.config(state="normal")
        self.stack_text.delete("1.0", tk.END)
        self.stack_text.config(state="disabled")

if __name__ == "__main__":
    app = AplikasiPDA()
    app.mainloop()
