"""
DO_NI_KEP — ĐO NI KÉP: cùng một họ logic phải thắng ở HAI cửa sổ liên tiếp,
            mỗi ngày tối đa 3 đề xuất có bằng chứng mạnh nhất.

═══════════════════════════════════════════════════════════════════════════════
QUY TẮC (ý tưởng 1 làm lõi + ý tưởng 3 — người dùng duyệt)
    Mỗi ngày, với từng giải của từng đài quay hôm đó, lấy 150 kỳ gần nhất:
      ├── Kỳ 1–110   : thử 10 họ logic, chọn họ phù hợp nhất (theo thứ hạng)
      ├── Kỳ 111–130 : CỬA SỔ 1 — họ đó phải trúng >= 14/20
      └── Kỳ 131–150 : CỬA SỔ 2 — CÙNG họ đó phải trúng >= 14/20
    Qua cả hai -> ứng viên. Mỗi ngày lấy tối đa 3 ứng viên mạnh nhất
    (tổng trúng 2 cửa sổ cao nhất) -> ĐỀ XUẤT. Ứng viên còn lại -> DỰ BỊ.
    Không qua -> ĐỂ TRỐNG, ghi rõ cửa sổ nào trượt.
    Hôm nay dùng CHÍNH họ đã được kiểm chứng (không chọn lại họ khác).

VÌ SAO HAI CỬA SỔ — đo trên 300 giải mỗi loại trước khi dựng
                                      Giải ngẫu nhiên    Giải có logic thật
                                      có đề xuất         có đề xuất · trúng
    1 cửa sổ 20 kỳ, > 64%                  52%              100% · 94%
    2 cửa sổ cùng họ, >= 14/20             15%              100% · 91%
    Một giải ngẫu nhiên vượt MỘT cửa sổ nhờ may khá dễ; vượt HAI cửa sổ độc lập
    với CÙNG một họ thì hiếm. Logic thật giữ được qua cả hai.
    -> Nhiễu lọt qua giảm ~3,5 lần, logic thật KHÔNG bị bỏ sót.
    Giả sử 1/20 giải có logic thật: tỷ lệ thắng cả ngày 66,7% -> 71,0%.
    Nếu không giải nào có logic thật: mọi bộ vẫn ~64%, nhưng số bộ phải đặt
    giảm ~3,5 lần -> tổng tiền mất mỗi ngày giảm theo.

BẢNG XẾP HẠNG HỌ LOGIC — CHỈ ĐỂ THEO DÕI (ý tưởng 2, chưa bật luật khoá)
    Gộp tiến cứu của từng họ trên MỌI giải, MỌI ngày — kể cả sổ cũ
    data/do_ni_20.json (chỉ đọc, không ghi). Sau 4–6 tuần, khi mỗi họ có vài
    trăm lượt, mới quyết định luật khoá. Khoá sớm chính là đuổi theo nhiễu.

SỔ TIẾN CỨU — 4 nhóm để dữ liệu tự trả lời
    ĐỀ XUẤT · DỰ BỊ · ĐỂ TRỐNG (bóng) · NGẪU NHIÊN (đối chứng tái lập được)

BA MỐC: bốc bừa 64% · hoà vốn 67,37% (tỷ lệ trả 95) · kỳ vọng -5%.
Máy quay công bằng thì mọi bộ 64 con trúng 64% — bộ lọc chỉ đổi được TỶ TRỌNG
bộ có logic thật trong số đề xuất, không làm bộ nhiễu trúng nhiều hơn.
═══════════════════════════════════════════════════════════════════════════════
"""
import os, sys, json, math, html, zlib, smtplib, traceback
from datetime import datetime, timedelta, timezone, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import numpy as np

import engine as E

VN = timezone(timedelta(hours=7))

# ==============================================================================
#  ┌──────────────────────────────────────────────────────────────────────┐
#  │  BẢNG ĐIỀU KHIỂN                                                     │
#  └──────────────────────────────────────────────────────────────────────┘
# ==============================================================================

SO_KY        = 150    # số kỳ gần nhất
N_CUA_SO     = 20     # độ dài MỖI cửa sổ kiểm
NGUONG_KY    = 14     # phải trúng >= 14/20 (70%, trên hoà vốn 67,37%) ở CẢ HAI cửa sổ
T_BD         = 30     # khám phá bắt đầu dự báo từ kỳ thứ 31
N_MIN        = 100    # ít hơn -> "THIẾU" (khám phá cần >= 30 kỳ)
MAX_DE_XUAT  = 3      # mỗi ngày tối đa bao nhiêu đề xuất (ý tưởng 3)
SO_CON       = 64
TY_LE_TRA    = 95.0
HOA_VON      = SO_CON / TY_LE_TRA          # 67,37%

CHAY_DB, CHAY_G1, CHAY_G8 = True, True, True
FILE_TT      = "data/do_ni_kep.json"
FILE_SO_CU   = "data/do_ni_20.json"        # sổ cũ — CHỈ ĐỌC, gộp vào bảng xếp hạng họ
EMAIL_NHAN   = os.environ.get("MAIL_TO",   "Linh.tm.pg@gmail.com")
EMAIL_GUI    = os.environ.get("MAIL_USER", "Linh.tm.pg@gmail.com")
TEN_GIAI     = {"DB": "① Đặc Biệt", "G1": "② Giải Nhất", "G8": "③ Giải 8"}
THU_TU_GIAI  = {"DB": 0, "G1": 1, "G8": 2}
A_, B_ = np.arange(100) // 10, np.arange(100) % 10


# ==============================================================================
#  10 HỌ LOGIC — chép nguyên từ do_ni_20.py (đã qua bộ kiểm thử 11/11)
# ==============================================================================

def _thu(d):
    return d.weekday() if hasattr(d, "weekday") else date.fromisoformat(str(d)[:10]).weekday()


def _chuan_bi(mt, pool, thu_list):
    n = len(mt); mt = np.asarray(mt)
    X = {"mt": mt, "thu": thu_list}
    one = np.zeros((n, 100)); one[np.arange(n), mt] = 1
    X["c"] = np.vstack([np.zeros(100), np.cumsum(one, 0)])
    pk = np.zeros((n, 100))
    for t, ky in enumerate(pool):
        np.add.at(pk[t], ky, 1)
    X["pool"] = np.vstack([np.zeros(100), np.cumsum(pk, 0)])
    for ten, v in (("d1", mt // 10), ("d2", mt % 10), ("tong", (mt // 10 + mt % 10) % 10)):
        m = np.zeros((n, 10)); m[np.arange(n), v] = 1
        X[ten] = np.vstack([np.zeros(10), np.cumsum(m, 0)])
    for H in (5, 10, 20):
        R = np.zeros((n + 1, 100)); dec = 0.5 ** (1.0 / H)
        for t in range(1, n + 1):
            R[t] = R[t - 1] * dec; R[t, mt[t - 1]] += 1
        X[f"gd{H}"] = R
    T1 = np.zeros((n + 1, 10, 10)); T2 = np.zeros((n + 1, 10, 10))
    L = np.full((n + 1, 100), -1.0); W = np.zeros((n + 1, 7, 100))
    for t in range(1, n + 1):
        T1[t] = T1[t - 1]; T2[t] = T2[t - 1]; L[t] = L[t - 1]; W[t] = W[t - 1]
        if t >= 2:
            T1[t, mt[t - 2] // 10, mt[t - 1] // 10] += 1
            T2[t, mt[t - 2] % 10, mt[t - 1] % 10] += 1
        L[t, mt[t - 1]] = t - 1
        W[t, thu_list[t - 1], mt[t - 1]] += 1
    X.update(T1=T1, T2=T2, last=L, wd=W)
    return X


def cau_hinh(co_lich):
    ds = ["TẦN SUẤT", "CỬA SỔ 10", "CỬA SỔ 20", "CỬA SỔ 30", "CỬA SỔ 50",
          "GẦN ĐÂY 5", "GẦN ĐÂY 10", "GẦN ĐÂY 20", "ĐỘC LẬP", "MARKOV",
          "TỔNG CS", "GỘP GIẢI", "GAN", "ĐỀU"]
    if co_lich:
        ds.insert(12, "LỊCH")
    return ds


def diem(cfg, X, t, thu_t):
    mt = X["mt"]
    if cfg == "TẦN SUẤT":
        return X["c"][t]
    if cfg.startswith("CỬA SỔ"):
        w = int(cfg.split()[-1]); return X["c"][t] - X["c"][max(0, t - w)]
    if cfg.startswith("GẦN ĐÂY"):
        return X[f"gd{int(cfg.split()[-1])}"][t]
    if cfg == "ĐỘC LẬP":
        return np.log(X["d1"][t] + 1)[A_] + np.log(X["d2"][t] + 1)[B_]
    if cfg == "MARKOV":
        if t < 2:
            return np.zeros(100)
        a, b = mt[t - 1] // 10, mt[t - 1] % 10
        return np.log(X["T1"][t, a] + 1)[A_] + np.log(X["T2"][t, b] + 1)[B_]
    if cfg == "TỔNG CS":
        return X["tong"][t][(A_ + B_) % 10]
    if cfg == "GỘP GIẢI":
        return X["pool"][t] + X["c"][t]
    if cfg == "LỊCH":
        return X["wd"][t, thu_t]
    if cfg == "GAN":
        return t - X["last"][t]
    return np.zeros(100)                                   # ĐỀU


def _thu_tu(s):
    return np.argsort(-np.asarray(s, float), kind="stable")


def top64(s):
    return sorted(int(i) for i in _thu_tu(s)[:SO_CON])


def _trung(cfg, X, t0, t1):
    mt, thu = X["mt"], X["thu"]
    return sum(1 for t in range(t0, t1) if mt[t] in set(_thu_tu(diem(cfg, X, t, thu[t]))[:SO_CON].tolist()))


def _hang(cfg, X, t0, t1):
    mt, thu = X["mt"], X["thu"]
    r = []
    for t in range(t0, t1):
        pos = np.empty(100); pos[_thu_tu(diem(cfg, X, t, thu[t]))] = np.arange(100)
        r.append(pos[mt[t]])
    return float(np.mean(r)) if r else 99.0


# ==============================================================================
#  QUYẾT ĐỊNH 1 GIẢI — hai cửa sổ, cùng họ
# ==============================================================================

def quyet_dinh(mt, pool, thu_list, thu_hn):
    """Chọn họ trên khám phá, kiểm CÙNG họ trên 2 cửa sổ rời nhau. Không rò rỉ:
       họ được chọn TRƯỚC cả hai cửa sổ; mỗi kỳ trong cửa sổ chỉ dùng dữ liệu trước nó."""
    n = len(mt)
    if n < N_MIN:
        return {"trang_thai": "THIẾU", "ly_do": f"chỉ {n} kỳ, cần >= {N_MIN}"}
    X = _chuan_bi(mt, pool, thu_list)
    ds = cau_hinh(len(set(thu_list)) >= 2)
    t1, t2 = n - 2 * N_CUA_SO, n - N_CUA_SO
    hang = {c: _hang(c, X, T_BD, t1) for c in ds}
    ho = min(ds, key=lambda c: (hang[c], ds.index(c)))
    k1 = _trung(ho, X, t1, t2)
    k2 = _trung(ho, X, t2, n)
    return {"trang_thai": "ỨNG VIÊN" if (k1 >= NGUONG_KY and k2 >= NGUONG_KY) else "ĐỂ TRỐNG",
            "ho": ho, "k1": k1, "k2": k2, "hang": hang[ho],
            "so": top64(diem(ho, X, n, thu_hn))}


def ap_gioi_han(tat_ca):
    """Ý tưởng 3: mỗi ngày tối đa MAX_DE_XUAT. Xếp theo bằng chứng mạnh nhất:
       tổng trúng 2 cửa sổ, rồi cửa sổ gần hơn, rồi thứ hạng khám phá."""
    uv = [o for o in tat_ca if o["trang_thai"] == "ỨNG VIÊN"]
    uv.sort(key=lambda o: (-(o["k1"] + o["k2"]), -o["k2"], o["hang"], o["stt"], THU_TU_GIAI[o["giai"]]))
    for i, o in enumerate(uv):
        o["thu_hang"] = i + 1
        o["trang_thai"] = "ĐỀ XUẤT" if i < MAX_DE_XUAT else "DỰ BỊ"


def ngau_nhien_64(ngay, stt, giai):
    rng = np.random.default_rng(zlib.crc32(f"{ngay}|{stt}|{giai}".encode()))
    return sorted(int(x) for x in rng.choice(100, SO_CON, replace=False))


# ==============================================================================
#  TIỆN ÍCH
# ==============================================================================

def _vi_tri(tg, giai):
    if giai == "DB":
        return 0
    if giai == "G1":
        return 1
    if giai == "G8" and len(tg[0]) == 18 and len(tg[0][-1]) == 2:
        return len(tg[0]) - 1
    return None


def _chuoi(so):
    return ",".join(f"{v:02d}" for v in so)


def wilson(t, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p, d = t / n, 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


# ==============================================================================
#  SỔ TIẾN CỨU + BẢNG XẾP HẠNG HỌ
# ==============================================================================

def nap_tt():
    if os.path.exists(FILE_TT):
        try:
            tt = json.load(open(FILE_TT, encoding="utf-8")); tt.setdefault("so", [])
            return tt
        except Exception:
            pass
    return {"so": [], "cap_nhat": None}


def luu_tt(tt):
    os.makedirs(os.path.dirname(FILE_TT) or ".", exist_ok=True)
    tt["cap_nhat"] = datetime.now(VN).isoformat(timespec="seconds")
    json.dump(tt, open(FILE_TT, "w", encoding="utf-8"), ensure_ascii=False)


def cham_cu(tt, hom_nay):
    cache = {}

    def tra(stt, giai, ngay):
        if stt not in cache:
            m = E.lay_tu_master(stt, 60)
            cache[stt] = {str(d)[:10]: ky for ky, d in zip(m[0], m[1])} if m else {}
        ky = cache[stt].get(ngay)
        vi = _vi_tri([ky], giai) if ky else None
        return None if vi is None else int(ky[vi][-2:])

    moi = []
    for r in tt["so"]:
        if r.get("ket_qua") is not None or r["ngay"] >= hom_nay.isoformat():
            continue
        y = tra(r["stt"], r["giai"], r["ngay"])
        if y is None:
            continue
        r["ket_qua"] = {"so_ve": y,
                        "trung": y in set(int(x) for x in r["so"].split(",")),
                        "trung_ngau": y in set(int(x) for x in r["ngau"].split(","))}
        moi.append(r)
    return moi


def thanh_tich(tt):
    nhom = {"ĐỀ XUẤT": [0, 0], "DỰ BỊ": [0, 0], "ĐỂ TRỐNG (bóng)": [0, 0], "NGẪU NHIÊN": [0, 0]}
    for r in tt["so"]:
        if not r.get("ket_qua"):
            continue
        k = "ĐỂ TRỐNG (bóng)" if r["trang_thai"] == "ĐỂ TRỐNG" else r["trang_thai"]
        nhom[k][0] += int(r["ket_qua"]["trung"]); nhom[k][1] += 1
        nhom["NGẪU NHIÊN"][0] += int(r["ket_qua"]["trung_ngau"]); nhom["NGẪU NHIÊN"][1] += 1
    return nhom


def bang_ho(tt):
    """Gộp tiến cứu theo HỌ LOGIC trên mọi giải, mọi ngày — kể cả sổ cũ (chỉ đọc).
       Khử trùng theo (ngày, đài, giải, họ): cùng họ cùng ngày là cùng một dự báo."""
    ban_ghi = list(tt["so"])
    if os.path.exists(FILE_SO_CU):
        try:
            ban_ghi += json.load(open(FILE_SO_CU, encoding="utf-8")).get("so", [])
        except Exception:
            pass
    da, bh = set(), {}
    for r in ban_ghi:
        kq = r.get("ket_qua")
        if not kq or not r.get("ho"):
            continue
        khoa = (r["ngay"], r["stt"], r["giai"], r["ho"])
        if khoa in da:
            continue
        da.add(khoa)
        x = bh.setdefault(r["ho"], {"n": 0, "trung": 0, "ngau": 0})
        x["n"] += 1; x["trung"] += int(kq["trung"]); x["ngau"] += int(kq.get("trung_ngau", 0))
    return dict(sorted(bh.items(), key=lambda kv: -kv[1]["n"]))


# ==============================================================================
#  CHẠY 1 NGÀY
# ==============================================================================

def chay(ngay=None, gui_mail=True):
    hom_nay = E.doc_ngay(ngay) if ngay else datetime.now(VN).date()
    thu = E.THU_VN[hom_nay.weekday()]
    hn = hom_nay.isoformat()
    tt = nap_tt()

    print("=" * 80)
    print(f"  ĐO NI KÉP  |  {thu} {hom_nay:%d.%m.%Y}")
    print(f"  Cùng họ >= {NGUONG_KY}/{N_CUA_SO} ở CẢ 2 cửa sổ · tối đa {MAX_DE_XUAT} đề xuất/ngày")
    print("=" * 80)

    moi_cham = cham_cu(tt, hom_nay)
    if moi_cham:
        print(f"\n[CHẤM HÔM TRƯỚC] {len(moi_cham)} bộ vừa có kết quả")

    dsach = E.dai_theo_ngay(hom_nay)
    lich = E.xay_lich()
    dai_list, tat_ca = [], []
    for s in dsach:
        ten = lich.get(str(s), {}).get("ten", E.lay_dai(s)[0])
        mien = lich.get(str(s), {}).get("mien", E.lay_dai(s)[2])
        d = {"stt": s, "dai": ten, "mien": mien, "o": [], "loi": ""}
        try:
            m = E.lay_tu_master(s, SO_KY + 30)
            if m:
                tg_all, ng_all, _ = m
            else:
                _, _, ng_all, tg_all, _ = E.lay_du_lieu(s, SO_KY + 30)
            tg, ng, _ = E.cat_truoc_ngay(tg_all, ng_all, hom_nay, SO_KY)
        except Exception as e:
            tg, ng = [], []
            d["loi"] = f"không lấy được dữ liệu: {e}"
        for giai, bat in (("DB", CHAY_DB), ("G1", CHAY_G1), ("G8", CHAY_G8)):
            if not bat:
                continue
            if not tg:
                if giai == "G8" and E.lay_dai(s)[1] == "xsmb":
                    continue
                o = {"trang_thai": "LỖI", "ly_do": d["loi"] or "không có dữ liệu"}
            else:
                vi = _vi_tri(tg, giai)
                if vi is None:
                    continue
                mt = [int(ky[vi][-2:]) for ky in tg]
                pool = [[int(x[-2:]) for j, x in enumerate(ky) if j != vi] for ky in tg]
                try:
                    o = quyet_dinh(mt, pool, [_thu(x) for x in ng], hom_nay.weekday())
                except Exception as e:
                    o = {"trang_thai": "LỖI", "ly_do": f"lỗi tính toán: {e}"}
            o.update(stt=s, dai=ten, giai=giai)
            if "so" in o:
                o["ngau"] = ngau_nhien_64(hn, s, giai)
            d["o"].append(o); tat_ca.append(o)
        dai_list.append(d)

    ap_gioi_han(tat_ca)

    for d in dai_list:
        print(f"\n  {d['dai'].upper()}" + (f"   ⚠ {d['loi']}" if d["loi"] else ""))
        for o in d["o"]:
            chi = (f"{o['ho']:<11} cửa sổ 1: {o['k1']}/{N_CUA_SO} · cửa sổ 2: {o['k2']}/{N_CUA_SO}"
                   if "ho" in o else o.get("ly_do", ""))
            print(f"     {TEN_GIAI[o['giai']]:<14} {o['trang_thai']:<9} {chi}")

    da_co = {(r["ngay"], r["stt"], r["giai"]) for r in tt["so"]}
    for o in tat_ca:
        if "so" in o and (hn, o["stt"], o["giai"]) not in da_co:
            tt["so"].append({"ngay": hn, "stt": o["stt"], "dai": o["dai"], "giai": o["giai"],
                             "trang_thai": o["trang_thai"], "ho": o["ho"], "k1": o["k1"], "k2": o["k2"],
                             "so": _chuoi(o["so"]), "ngau": _chuoi(o["ngau"]), "ket_qua": None})
    luu_tt(tt)
    tk, bh = thanh_tich(tt), bang_ho(tt)
    n_dx = sum(1 for o in tat_ca if o["trang_thai"] == "ĐỀ XUẤT")
    n_db = sum(1 for o in tat_ca if o["trang_thai"] == "DỰ BỊ")
    print(f"\n  {n_dx} đề xuất · {n_db} dự bị · {len(tat_ca)} giải")
    for k, (a, b) in tk.items():
        if b:
            print(f"  Tiến cứu {k:<16} {a}/{b} = {a/b:.1%}")

    bc = {"ngay": hom_nay, "thu": thu, "dai": dai_list, "tat_ca": tat_ca, "tk": tk, "bh": bh,
          "n_dx": n_dx, "n_db": n_db, "n_o": len(tat_ca)}
    if gui_mail:
        print("\n  Đang gửi email...")
        gui_email(bc)
        print(f"  ✓ Đã gửi email tới {EMAIL_NHAN}")
    return bc


# ==============================================================================
#  EMAIL
# ==============================================================================

MAU = {"ĐỀ XUẤT": "#2e7d32", "DỰ BỊ": "#ef6c00", "ĐỂ TRỐNG": "#90a4ae", "THIẾU": "#b0bec5", "LỖI": "#c62828"}


def _o_cua_so(o):
    if "ho" not in o:
        return html.escape(o.get("ly_do", ""))
    def c(k):
        ok = k >= NGUONG_KY
        return f'<span style="color:{"#2e7d32" if ok else "#c62828"}">{k}/{N_CUA_SO} {"✓" if ok else "✗"}</span>'
    return f'{html.escape(o["ho"])} · cửa sổ 1: {c(o["k1"])} · cửa sổ 2: {c(o["k2"])}'


def _html(bc):
    css = "font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;"
    ng, thu, tk, bh = bc["ngay"], bc["thu"], bc["tk"], bc["bh"]
    td = 'style="padding:4px 9px;text-align:center"'
    h = [f'<div style="{css}max-width:820px;color:#222">']
    h.append(f'<h2 style="margin:0 0 2px">Đo ni kép — {thu} {ng:%d.%m.%Y}</h2>')
    h.append(f'<p style="color:#666;margin:0 0 10px;font-size:13px">{len(bc["dai"])} đài · '
             f'{bc["n_o"]} giải · <b>{bc["n_dx"]} đề xuất</b> · {bc["n_db"]} dự bị</p>')
    h.append(f'<div style="background:#fff8e1;border-left:4px solid #f9a825;padding:9px 12px;'
             f'margin:0 0 16px;font-size:12px;line-height:1.6"><b>Quy tắc:</b> kỳ 1–110 chọn họ logic → '
             f'CÙNG họ đó phải trúng ≥ {NGUONG_KY}/{N_CUA_SO} ở cả cửa sổ kỳ 111–130 lẫn kỳ 131–150 → '
             f'tối đa {MAX_DE_XUAT} giải mạnh nhất được đề xuất.<br><b>Ba mốc:</b> bốc bừa 64% · hoà vốn '
             f'{HOA_VON:.2%} · kỳ vọng −5% (tỷ lệ trả 95).</div>')

    # ---- Tiến cứu ----
    h.append('<div style="font-size:15px;font-weight:700;margin:0 0 6px">THÀNH TÍCH TIẾN CỨU</div>')
    if not any(b for _, b in tk.values()):
        h.append('<p style="font-size:13px;color:#607d8b;margin:0 0 16px">Chưa có bộ số nào được chấm. '
                 'Sổ bắt đầu tích luỹ từ ngày mai.</p>')
    else:
        h.append('<table style="font-size:12px;border-collapse:collapse;margin:0 0 6px">'
                 '<tr style="background:#eceff1"><th style="padding:4px 9px;text-align:left">Nhóm</th>'
                 f'<th {td}>Đúng/Tổng</th><th {td}>Tỷ lệ</th><th {td}>KTC 95%</th></tr>')
        for k, (a, b) in tk.items():
            if b:
                lo, hi = wilson(a, b)
                h.append(f'<tr><td style="padding:4px 9px">{k}</td><td {td}>{a}/{b}</td>'
                         f'<td {td}><b>{a/b:.1%}</b></td><td {td}>[{lo:.0%}, {hi:.0%}]</td></tr>')
        h.append('</table><p style="font-size:12px;color:#607d8b;margin:0 0 16px">Nhóm ĐỀ XUẤT phải trúng '
                 'nhiều hơn cả ĐỂ TRỐNG lẫn NGẪU NHIÊN qua nhiều tuần thì bộ lọc hai cửa sổ mới có giá trị.</p>')

    # ---- Đề xuất ----
    dx = [o for o in bc["tat_ca"] if o["trang_thai"] == "ĐỀ XUẤT"]
    h.append('<div style="font-size:15px;font-weight:700;margin:6px 0 6px">ĐỀ XUẤT HÔM NAY</div>')
    if not dx:
        h.append('<div style="border-left:4px solid #90a4ae;background:#fafafa;padding:11px 13px;'
                 'margin:0 0 16px;font-size:13px"><b>Không giải nào qua được cả hai cửa sổ hôm nay.</b> '
                 'Không đề xuất.</div>')
    for o in dx:
        h.append(f'<div style="margin:0 0 14px;border:1px solid #cfd8dc;border-radius:5px">'
                 f'<div style="padding:8px 12px;background:#263238;color:#fff"><b>#{o["thu_hang"]} · '
                 f'{html.escape(o["dai"].upper())} — {TEN_GIAI[o["giai"]]}</b></div>'
                 f'<div style="padding:9px 12px"><div style="font-size:12px;color:#455a64;margin-bottom:5px">'
                 f'Họ logic <b>{html.escape(o["ho"])}</b> · cửa sổ 1: <b>{o["k1"]}/{N_CUA_SO}</b> · '
                 f'cửa sổ 2: <b>{o["k2"]}/{N_CUA_SO}</b> · tổng {o["k1"]+o["k2"]}/{2*N_CUA_SO}</div>'
                 f'<div style="font-family:ui-monospace,Menlo,Consolas,monospace;font-size:14px;'
                 f'background:#e8f5e9;border-left:4px solid #2e7d32;padding:9px 11px;'
                 f'word-break:break-all;line-height:1.85">{_chuoi(o["so"])}</div></div></div>')

    db = [o for o in bc["tat_ca"] if o["trang_thai"] == "DỰ BỊ"]
    if db:
        h.append(f'<div style="font-size:13px;margin:0 0 14px;color:#ef6c00"><b>DỰ BỊ</b> — qua cả hai cửa '
                 f'sổ nhưng ngoài top {MAX_DE_XUAT} hôm nay: '
                 + "; ".join(f'{html.escape(o["dai"])} {TEN_GIAI[o["giai"]]} ({o["k1"]}+{o["k2"]})' for o in db)
                 + '</div>')

    # ---- Mọi giải ----
    h.append('<div style="font-size:15px;font-weight:700;margin:6px 0 6px">MỌI GIẢI HÔM NAY</div>'
             '<table style="font-size:12px;border-collapse:collapse;margin:0 0 16px">')
    for d in bc["dai"]:
        for i, o in enumerate(d["o"]):
            h.append(f'<tr><td style="padding:3px 8px">{html.escape(d["dai"]) if i == 0 else ""}</td>'
                     f'<td style="padding:3px 8px">{TEN_GIAI[o["giai"]]}</td>'
                     f'<td style="padding:3px 8px"><span style="background:{MAU.get(o["trang_thai"], "#999")};'
                     f'color:#fff;padding:1px 6px;border-radius:3px;font-size:11px">{o["trang_thai"]}</span></td>'
                     f'<td style="padding:3px 8px;color:#546e7a">{_o_cua_so(o)}</td></tr>')
    h.append('</table>')

    # ---- Bảng xếp hạng họ ----
    h.append('<div style="font-size:15px;font-weight:700;margin:6px 0 4px">BẢNG XẾP HẠNG HỌ LOGIC — '
             'chỉ để theo dõi</div>')
    if not bh:
        h.append('<p style="font-size:12px;color:#607d8b">Chưa có dữ liệu tiến cứu theo họ.</p>')
    else:
        h.append('<table style="font-size:12px;border-collapse:collapse">'
                 '<tr style="background:#eceff1"><th style="padding:4px 9px;text-align:left">Họ logic</th>'
                 f'<th {td}>Số lượt</th><th {td}>Trúng</th><th {td}>Ngẫu nhiên cùng lượt</th>'
                 f'<th {td}>Chênh</th><th {td}>KTC 95%</th></tr>')
        for ho, x in bh.items():
            lo, hi = wilson(x["trung"], x["n"])
            ch = (x["trung"] - x["ngau"]) / x["n"]
            h.append(f'<tr><td style="padding:4px 9px">{html.escape(ho)}</td><td {td}>{x["n"]}</td>'
                     f'<td {td}><b>{x["trung"]/x["n"]:.1%}</b></td><td {td}>{x["ngau"]/x["n"]:.1%}</td>'
                     f'<td {td} style="color:{"#2e7d32" if ch > 0 else "#c62828"}">{ch:+.1%}</td>'
                     f'<td {td}>[{lo:.0%}, {hi:.0%}]</td></tr>')
        h.append('</table>')
    h.append('<p style="font-size:12px;color:#607d8b;margin:4px 0 0">Gộp mọi giải, mọi ngày, kể cả sổ cũ của '
             'engine Đo ni 20. Chưa dùng để quyết định: sau 4–6 tuần, khi mỗi họ có vài trăm lượt, mới xem '
             'xét luật khoá họ kém. Khoá sớm chính là đuổi theo nhiễu.</p>')

    h.append('<hr style="margin:20px 0 10px;border:0;border-top:1px solid #ddd">'
             '<p style="font-size:12px;color:#888;line-height:1.6">Bộ lọc hai cửa sổ giảm nhiễu lọt qua từ '
             '~52% xuống ~15% mà không bỏ sót logic thật. Nó không làm bộ nhiễu trúng nhiều hơn — nó làm '
             'ít bộ nhiễu vào danh sách hơn. Máy quay công bằng thì mọi bộ 64 con trúng 64%.</p></div>')
    return "".join(h)


def _text(bc):
    t = [f"ĐO NI KÉP — {bc['thu']} {bc['ngay']:%d.%m.%Y}",
         f"{bc['n_dx']} đề xuất · {bc['n_db']} dự bị · {bc['n_o']} giải", ""]
    for o in bc["tat_ca"]:
        if o["trang_thai"] == "ĐỀ XUẤT":
            t.append(f"#{o['thu_hang']} {o['dai'].upper()} {TEN_GIAI[o['giai']]} "
                     f"[ĐỀ XUẤT · {o['ho']} · {o['k1']}/{N_CUA_SO} + {o['k2']}/{N_CUA_SO}]")
            t.append("  " + _chuoi(o["so"]))
    t.append("")
    for o in bc["tat_ca"]:
        if o["trang_thai"] != "ĐỀ XUẤT":
            chi = (f"{o['ho']} · {o['k1']}/{N_CUA_SO} + {o['k2']}/{N_CUA_SO}" if "ho" in o
                   else o.get("ly_do", ""))
            t.append(f"{o['dai']} {TEN_GIAI[o['giai']]} [{o['trang_thai']} · {chi}]")
    return "\n".join(t)


def gui_email(bc):
    mk = E._lay_mat_khau()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = (f"[ĐO NI KÉP] {bc['thu']} {bc['ngay']:%d.%m.%Y} — "
                      + (f"{bc['n_dx']} đề xuất" if bc["n_dx"] else "không có đề xuất"))
    msg["From"] = formataddr(("XSMN Đo Ni Kép", EMAIL_GUI))
    msg["To"] = EMAIL_NHAN
    msg.attach(MIMEText(_text(bc), "plain", "utf-8"))
    msg.attach(MIMEText(_html(bc), "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as sv:
        sv.login(EMAIL_GUI, mk)
        sv.send_message(msg)


if __name__ == "__main__":
    ngay = next((a for a in sys.argv[1:] if "." in a), None)
    try:
        E._lay_mat_khau()
        print("  Mật khẩu ứng dụng: OK")
        kho = E.doc_master()
        if kho is None:
            print("  Chưa có kho — quét lần đầu..."); E.tao_master(so_ky=200)
        else:
            print(f"  Kho: {len(kho['dai'])} đài, cập nhật {kho['tao_luc'][:16]}")
            E.cap_nhat_master(so_ky_moi=20)
        chay(ngay)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
