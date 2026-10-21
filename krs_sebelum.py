#!/usr/bin/env python3
"""krs_sebelum.py : race condition pada rebutan kursi terakhir saat KRS (TI-4A).

Kasus: beberapa mahasiswa (thread) mendaftar ke satu kelas yang kursinya hampir penuh.
Program ini TANPA sinkronisasi, jadi kursi bisa terjual lebih dari kapasitas.

Contoh:
  python3 krs_sebelum.py --verbose                 # satu percobaan dengan urutan kejadian
  python3 krs_sebelum.py --ulang 1000              # 1000 percobaan berulang
  python3 krs_sebelum.py --ulang 1000 --jeda 0     # tanpa jeda buatan
  python3 krs_sebelum.py --ulang 5000 --jeda 0 --switch-interval 0.000001
"""
import argparse
import sys
import threading
import time

NAMA = ["Andi", "Budi", "Citra", "Dewi", "Eko", "Fani", "Gita", "Hadi"]


def satu_percobaan(mahasiswa, kursi, jeda, kejadian=None):
    """Satu putaran rebutan kursi. Mengembalikan (daftar terdaftar, sisa kursi akhir)."""
    sisa = [kursi]
    terdaftar = []
    gerbang = threading.Barrier(mahasiswa)  # semua thread mulai bersamaan
    t0 = time.perf_counter()

    def catat(teks):
        if kejadian is not None:
            kejadian.append((time.perf_counter() - t0, teks))

    def daftar(nama):
        gerbang.wait()
        # ---- critical section dimulai: cek kursi, kurangi kursi, catat pendaftar ----
        if sisa[0] > 0:
            catat("%s cek kursi: sisa=%d, lolos" % (nama, sisa[0]))
            if jeda > 0:
                time.sleep(jeda)  # simulasi proses lain, misalnya validasi dan tulis ke basis data
            sisa[0] -= 1
            terdaftar.append(nama)
            catat("%s kurangi kursi: sisa=%d" % (nama, sisa[0]))
        else:
            catat("%s cek kursi: sisa=%d, ditolak" % (nama, sisa[0]))
        # ---- critical section selesai ----

    ths = []
    for i in range(mahasiswa):
        nama = NAMA[i] if i < len(NAMA) else "Mhs-%d" % (i + 1)
        ths.append(threading.Thread(target=daftar, args=(nama,)))
    for t in ths:
        t.start()
    for t in ths:
        t.join()
    return terdaftar, sisa[0]


def ulangi(ulang, mahasiswa, kursi, jeda):
    """Ulangi percobaan. Mengembalikan ringkasan hasil."""
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
    ap = argparse.ArgumentParser(description="Rebutan kursi KRS tanpa sinkronisasi")
    ap.add_argument("--mahasiswa", type=int, default=2, help="jumlah mahasiswa (thread)")
    ap.add_argument("--kursi", type=int, default=1, help="kursi tersisa")
    ap.add_argument("--jeda", type=float, default=0.001, help="jeda detik antara cek dan kurangi")
    ap.add_argument("--ulang", type=int, default=1, help="jumlah percobaan")
    ap.add_argument("--verbose", action="store_true", help="tampilkan urutan kejadian satu percobaan")
    ap.add_argument("--switch-interval", type=float, default=0,
                    help="atur sys.setswitchinterval (detik), contoh 0.000001")
    a = ap.parse_args()
    if a.switch_interval > 0:
        sys.setswitchinterval(a.switch_interval)

    if a.verbose:
        kejadian = []
        terdaftar, sisa = satu_percobaan(a.mahasiswa, a.kursi, a.jeda, kejadian)
        for t, teks in sorted(kejadian):
            print("t+%6.3f ms  %s" % (t * 1000, teks))
        print("Terdaftar : %s (%d orang)" % (", ".join(terdaftar), len(terdaftar)))
        print("Kursi awal: %d, sisa akhir: %d" % (a.kursi, sisa))
        print("Hasil     : %s" % ("RACE CONDITION, kursi terjual lebih dari kapasitas"
                                   if len(terdaftar) > a.kursi or sisa < 0 else "aman pada percobaan ini"))
        return

    r = ulangi(a.ulang, a.mahasiswa, a.kursi, a.jeda)
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
