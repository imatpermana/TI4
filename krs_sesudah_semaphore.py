#!/usr/bin/env python3
"""krs_sesudah_semaphore.py : perbaikan race condition KRS dengan semaphore, TI-4A.

Semaphore dibuat dengan nilai awal sama dengan jumlah kursi. Setiap mahasiswa mencoba
acquire tanpa menunggu. Jika nilai semaphore sudah 0, acquire gagal dan pendaftaran ditolak.
Karena operasi acquire bersifat atomik, tidak mungkin ada lebih banyak pendaftar daripada kursi.

Contoh:
  python3 krs_sesudah_semaphore.py --verbose
  python3 krs_sesudah_semaphore.py --ulang 1000
"""
import argparse
import threading
import time

NAMA = ["Andi", "Budi", "Citra", "Dewi", "Eko", "Fani", "Gita", "Hadi"]


def satu_percobaan(mahasiswa, kursi, jeda, kejadian=None):
    sem = threading.Semaphore(kursi)  # nilai semaphore = kursi yang tersisa
    daftar_kunci = threading.Lock()   # hanya untuk menambah ke daftar hasil
    terdaftar = []
    gerbang = threading.Barrier(mahasiswa)
    t0 = time.perf_counter()

    def catat(teks):
        if kejadian is not None:
            kejadian.append((time.perf_counter() - t0, teks))

    def daftar(nama):
        gerbang.wait()
        if sem.acquire(blocking=False):  # atomik: ambil satu kursi atau gagal
            catat("%s berhasil acquire semaphore (kursi diambil)" % nama)
            if jeda > 0:
                time.sleep(jeda)  # simulasi proses lain setelah kursi pasti milik sendiri
            with daftar_kunci:
                terdaftar.append(nama)
            catat("%s tercatat sebagai pendaftar" % nama)
        else:
            catat("%s gagal acquire semaphore, kursi sudah habis" % nama)

    ths = []
    for i in range(mahasiswa):
        nama = NAMA[i] if i < len(NAMA) else "Mhs-%d" % (i + 1)
        ths.append(threading.Thread(target=daftar, args=(nama,)))
    for t in ths:
        t.start()
    for t in ths:
        t.join()
    return terdaftar, kursi - len(terdaftar)


def ulangi(ulang, mahasiswa, kursi, jeda):
    race = 0
    total_terdaftar = 0
    contoh = []
    mulai = time.perf_counter()
    for k in range(ulang):
        terdaftar, sisa = satu_percobaan(mahasiswa, kursi, jeda)
        total_terdaftar += len(terdaftar)
        if len(terdaftar) > kursi or sisa < 0:
            race += 1
            if len(contoh) < 3:
                contoh.append((k + 1, terdaftar, sisa))
    return {"ulang": ulang, "race": race, "rata_terdaftar": total_terdaftar / ulang,
            "durasi_s": time.perf_counter() - mulai, "contoh": contoh}


def main():
    ap = argparse.ArgumentParser(description="Rebutan kursi KRS dengan semaphore")
    ap.add_argument("--mahasiswa", type=int, default=2)
    ap.add_argument("--kursi", type=int, default=1)
    ap.add_argument("--jeda", type=float, default=0.001)
    ap.add_argument("--ulang", type=int, default=1)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    if a.verbose:
        kejadian = []
        terdaftar, sisa = satu_percobaan(a.mahasiswa, a.kursi, a.jeda, kejadian)
        for t, teks in sorted(kejadian):
            print("t+%6.3f ms  %s" % (t * 1000, teks))
        print("Terdaftar : %s (%d orang)" % (", ".join(terdaftar), len(terdaftar)))
        print("Kursi awal: %d, sisa akhir: %d" % (a.kursi, sisa))
        print("Hasil     : %s" % ("RACE CONDITION, kursi terjual lebih dari kapasitas"
                                   if len(terdaftar) > a.kursi or sisa < 0 else "aman, tidak ada kursi berlebih"))
        return

    r = ulangi(a.ulang, a.mahasiswa, a.kursi, a.jeda)
    print("Versi                : semaphore")
    print("Mahasiswa (thread)   : %d" % a.mahasiswa)
    print("Kursi awal           : %d" % a.kursi)
    print("Jeda cek-kurangi     : %.1f ms" % (a.jeda * 1000))
    print("Jumlah percobaan     : %d" % r["ulang"])
    print("Percobaan kena race  : %d (%.2f%%)" % (r["race"], 100.0 * r["race"] / r["ulang"]))
    print("Rata-rata terdaftar  : %.2f orang per percobaan" % r["rata_terdaftar"])
    print("Durasi total         : %.2f detik" % r["durasi_s"])
    for k, terdaftar, sisa in r["contoh"]:
        print("  contoh percobaan ke-%d: terdaftar=%s, sisa kursi=%d" % (k, ",".join(terdaftar), sisa))


if __name__ == "__main__":
    main()
