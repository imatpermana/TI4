#!/usr/bin/env python3
"""krs_sesudah_mutex.py : perbaikan race condition KRS dengan mutex (threading.Lock), TI-4A.

Mutex mengunci seluruh critical section: cek kursi, kurangi kursi, dan catat pendaftar.
Opsi --keliru mengunci hanya bagian pengurangan, untuk menunjukkan bahwa cakupan kunci
yang salah tetap menimbulkan race condition.

Contoh:
  python3 krs_sesudah_mutex.py --verbose
  python3 krs_sesudah_mutex.py --ulang 1000
  python3 krs_sesudah_mutex.py --ulang 1000 --keliru
"""
import argparse
import threading
import time

NAMA = ["Andi", "Budi", "Citra", "Dewi", "Eko", "Fani", "Gita", "Hadi"]


def satu_percobaan(mahasiswa, kursi, jeda, kejadian=None, keliru=False):
    sisa = [kursi]
    terdaftar = []
    kunci = threading.Lock()  # mutex pelindung critical section
    gerbang = threading.Barrier(mahasiswa)
    t0 = time.perf_counter()

    def catat(teks):
        if kejadian is not None:
            kejadian.append((time.perf_counter() - t0, teks))

    def daftar(nama):
        gerbang.wait()
        if keliru:
            # SALAH: pengecekan di luar kunci, hanya pengurangan yang dikunci
            if sisa[0] > 0:
                catat("%s cek kursi (tanpa kunci): sisa=%d, lolos" % (nama, sisa[0]))
                if jeda > 0:
                    time.sleep(jeda)
                with kunci:
                    sisa[0] -= 1
                    terdaftar.append(nama)
                    catat("%s kurangi kursi: sisa=%d" % (nama, sisa[0]))
            else:
                catat("%s cek kursi: sisa=%d, ditolak" % (nama, sisa[0]))
            return
        # BENAR: seluruh critical section berada di dalam kunci
        with kunci:
            if sisa[0] > 0:
                catat("%s masuk kunci, cek kursi: sisa=%d, lolos" % (nama, sisa[0]))
                if jeda > 0:
                    time.sleep(jeda)
                sisa[0] -= 1
                terdaftar.append(nama)
                catat("%s kurangi kursi: sisa=%d, keluar kunci" % (nama, sisa[0]))
            else:
                catat("%s masuk kunci, cek kursi: sisa=%d, ditolak" % (nama, sisa[0]))

    ths = []
    for i in range(mahasiswa):
        nama = NAMA[i] if i < len(NAMA) else "Mhs-%d" % (i + 1)
        ths.append(threading.Thread(target=daftar, args=(nama,)))
    for t in ths:
        t.start()
    for t in ths:
        t.join()
    return terdaftar, sisa[0]


def ulangi(ulang, mahasiswa, kursi, jeda, keliru=False):
    race = 0
    total_terdaftar = 0
    contoh = []
    mulai = time.perf_counter()
    for k in range(ulang):
        terdaftar, sisa = satu_percobaan(mahasiswa, kursi, jeda, keliru=keliru)
        total_terdaftar += len(terdaftar)
        if len(terdaftar) > kursi or sisa < 0:
            race += 1
            if len(contoh) < 3:
                contoh.append((k + 1, terdaftar, sisa))
    return {"ulang": ulang, "race": race, "rata_terdaftar": total_terdaftar / ulang,
            "durasi_s": time.perf_counter() - mulai, "contoh": contoh}


def main():
    ap = argparse.ArgumentParser(description="Rebutan kursi KRS dengan mutex")
    ap.add_argument("--mahasiswa", type=int, default=2)
    ap.add_argument("--kursi", type=int, default=1)
    ap.add_argument("--jeda", type=float, default=0.001)
    ap.add_argument("--ulang", type=int, default=1)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--keliru", action="store_true", help="kunci hanya di pengurangan (salah)")
    a = ap.parse_args()

    if a.verbose:
        kejadian = []
        terdaftar, sisa = satu_percobaan(a.mahasiswa, a.kursi, a.jeda, kejadian, a.keliru)
        for t, teks in sorted(kejadian):
            print("t+%6.3f ms  %s" % (t * 1000, teks))
        print("Terdaftar : %s (%d orang)" % (", ".join(terdaftar), len(terdaftar)))
        print("Kursi awal: %d, sisa akhir: %d" % (a.kursi, sisa))
        print("Hasil     : %s" % ("RACE CONDITION, kursi terjual lebih dari kapasitas"
                                   if len(terdaftar) > a.kursi or sisa < 0 else "aman, tidak ada kursi berlebih"))
        return

    r = ulangi(a.ulang, a.mahasiswa, a.kursi, a.jeda, a.keliru)
    print("Versi                : mutex %s" % ("(cakupan kunci keliru)" if a.keliru else "(cakupan kunci penuh)"))
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
