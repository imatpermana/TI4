#!/usr/bin/env python3
"""bandingkan.py : membandingkan versi sebelum dan sesudah perbaikan (TI-4A).

Menjalankan empat versi pada skenario yang sama lalu mencetak satu tabel perbandingan.
Letakkan di folder yang sama dengan krs_sebelum.py, krs_sesudah_mutex.py,
dan krs_sesudah_semaphore.py.

Contoh:
  python3 bandingkan.py                          # 2 mahasiswa, 1 kursi, 1000 percobaan
  python3 bandingkan.py --mahasiswa 20 --kursi 5 --ulang 500
  python3 bandingkan.py --jeda 0                 # tanpa jeda buatan
  python3 bandingkan.py --jeda 0 --ulang 5000 --switch-interval 0.000001
"""
import argparse
import sys

import krs_sebelum
import krs_sesudah_mutex
import krs_sesudah_semaphore


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mahasiswa", type=int, default=2)
    ap.add_argument("--kursi", type=int, default=1)
    ap.add_argument("--jeda", type=float, default=0.001)
    ap.add_argument("--ulang", type=int, default=1000)
    ap.add_argument("--switch-interval", type=float, default=0,
                    help="atur sys.setswitchinterval (detik), contoh 0.000001")
    a = ap.parse_args()
    if a.switch_interval > 0:
        sys.setswitchinterval(a.switch_interval)

    versi = [
        ("Sebelum (tanpa sinkronisasi)", lambda: krs_sebelum.ulangi(a.ulang, a.mahasiswa, a.kursi, a.jeda)),
        ("Mutex, kunci hanya di pengurangan (keliru)",
         lambda: krs_sesudah_mutex.ulangi(a.ulang, a.mahasiswa, a.kursi, a.jeda, keliru=True)),
        ("Sesudah: mutex, kunci seluruh critical section",
         lambda: krs_sesudah_mutex.ulangi(a.ulang, a.mahasiswa, a.kursi, a.jeda)),
        ("Sesudah: semaphore", lambda: krs_sesudah_semaphore.ulangi(a.ulang, a.mahasiswa, a.kursi, a.jeda)),
    ]
    print("Skenario: %d mahasiswa berebut %d kursi, jeda %.1f ms, %d percobaan per versi\n"
          % (a.mahasiswa, a.kursi, a.jeda * 1000, a.ulang))
    print("%-48s %8s %9s %14s %10s" % ("Versi", "Race", "Race (%)", "Rata terdaftar", "Durasi (s)"))
    print("-" * 94)
    for nama, fungsi in versi:
        r = fungsi()
        print("%-48s %8d %8.2f%% %14.2f %10.2f"
              % (nama, r["race"], 100.0 * r["race"] / r["ulang"], r["rata_terdaftar"], r["durasi_s"]))
    print("-" * 94)
    print("Kapasitas kursi = %d. Rata terdaftar di atas %d berarti ada kursi yang terjual berlebih."
          % (a.kursi, a.kursi))


if __name__ == "__main__":
    main()
