"""
DO_NI_KEP — ĐO NI KÉP 50 CON: MỌI GIẢI của MỌI ĐÀI quay hôm đó đều có bộ 50 con.
            3 họ logic mạnh nhất BỎ PHIẾU ra 50 con; hai cửa sổ kiểm là NHÃN ĐỘ TIN,
            không còn là cổng chặn.

═══════════════════════════════════════════════════════════════════════════════
QUY TẮC (người dùng yêu cầu: tất cả các giải của các đài đều có đề xuất)
    Với TỪNG giải của TỪNG đài quay hôm đó, lấy 150 kỳ gần nhất:
      ├── Kỳ 1–110   : mỗi họ chọn cấu hình tốt nhất, xếp hạng các họ theo thứ
      │                hạng. 3 HỌ ĐỨNG ĐẦU bỏ phiếu. Họ ĐỀU không bao giờ bỏ phiếu.
      ├── Kỳ 111–130 : CỬA SỔ 1 — bộ 3 họ bỏ phiếu ra 50 con, đếm số lần trúng
      └── Kỳ 131–150 : CỬA SỔ 2 — cùng bộ 3 họ, đếm số lần trúng
    Hôm nay: CÙNG bộ 3 họ bỏ phiếu ra 50 con -> LUÔN đề xuất.

    NHÃN ĐỘ TIN — chỉ để tham khảo, KHÔNG chặn bộ số nào:
      QUA 2 CỬA SỔ : cả hai cửa sổ >= 11/20 (55%, trên hoà vốn 52,63%)
      QUA 1 CỬA SỔ : chỉ một cửa sổ đạt
      KHÔNG QUA    : cả hai cửa sổ dưới 11/20
      ÍT DỮ LIỆU   : < 100 kỳ, không kiểm được 2 cửa sổ -> 50 con theo tần suất
      DỰ PHÒNG     : đài lỗi dữ liệu -> 50 con theo tần suất gộp cùng giải của các
                     đài khác hôm nay
    Trên giải ngẫu nhiên: ~17% "QUA 2 CỬA SỔ", ~48% "QUA 1", ~35% "KHÔNG QUA".

    CÁCH BỎ PHIẾU: mỗi họ đề cử 64 con. Xếp 100 con theo số phiếu (0–3); hoà phiếu
    thì TỔNG THỨ HẠNG trong 3 họ nhỏ hơn đứng trước. Lấy 50 con đầu.

VÌ SAO 50 CON: kỳ vọng không đổi (−5%) nhưng thắng/thua +45/−50 thay vì +31/−64.
VÌ SAO 3 HỌ (giải có logic thật, 50 con): bỏ phiếu đều 9 họ 70,7% · 3 họ mạnh
    nhất 76,3% · một họ tốt nhất 86,5%. Giải ngẫu nhiên: mọi cách ~50%.

SỔ TIẾN CỨU data/do_ni_kep_50.json — tách theo nhãn độ tin + NGẪU NHIÊN đối chứng.
    Nhãn bản ghi cũ tính lại từ số trúng 2 cửa sổ -> lịch sử liền mạch.
    Sau vài tuần: "QUA 2 CỬA SỔ" trúng nhiều hơn hẳn "KHÔNG QUA" thì nhãn có giá trị.
BẢNG XẾP HẠNG HỌ (chỉ theo dõi) + lịch sử bản 64 con (chỉ đọc).

BA MỐC: bốc bừa 50% · hoà vốn 52,63% · kỳ vọng −5% (tỷ lệ trả 95).
Máy quay công bằng thì MỌI bộ 50 con trúng 50%.
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
SO_CON       = 50     # số con cược
SO_DE_CU     = 64     # mỗi họ đề cử bao nhiêu con khi bỏ phiếu
SO_HO_BAU    = 3      # số họ mạnh nhất được bỏ phiếu
NGUONG_KY    = 11     # một cửa sổ "đạt" khi trúng >= 11/20 (55%, trên hoà vốn 52,63%)
T_BD         = 30     # khám phá bắt đầu dự báo từ kỳ thứ 31
N_MIN        = 100    # ít hơn -> "ÍT DỮ LIỆU", vẫn ra 50 con theo tần suất
TY_LE_TRA    = 95.0
HOA_VON      = SO_CON / TY_LE_TRA          # 52,63%
MOC          = SO_CON / 100.0              # 50%

CHAY_DB, CHAY_G1, CHAY_G8 = True, True, True
FILE_TT      = "data/do_ni_kep_50.json"
FILE_CU      = ["data/do_ni_kep.json", "data/do_ni_20.json"]   # sổ 64 con cũ — CHỈ ĐỌC
EMAIL_NHAN   = os.environ.get("MAIL_TO",   "Linh.tm.pg@gmail.com")
EMAIL_GUI    = os.environ.get("MAIL_USER", "Linh.tm.pg@gmail.com")
TEN_GIAI     = {"DB": "① Đặc Biệt", "G1": "② Giải Nhất", "G8": "③ Giải 8"}
THU_TU_GIAI  = {"DB": 0, "G1": 1, "G8": 2}
A_, B_ = np.arange(100) // 10, np.arange(100) % 10

HO = {"TẦN SUẤT": ["TẦN SUẤT"],
      "CỬA SỔ":   ["CỬA SỔ 10", "CỬA SỔ 20", "CỬA SỔ 30", "CỬA SỔ 50"],
      "GẦN ĐÂY":  ["GẦN ĐÂY 5", "GẦN ĐÂY 10", "GẦN ĐÂY 20"],
      "ĐỘC LẬP":  ["ĐỘC LẬP"], "MARKOV": ["MARKOV"], "TỔNG CS": ["TỔNG CS"],
      "GỘP GIẢI": ["GỘP GIẢI"], "LỊCH": ["LỊCH"], "GAN": ["GAN"], "ĐỀU": ["ĐỀU"]}
HO_KHONG_BAU = {"ĐỀU"}

MUC_2, MUC_1, MUC_0 = "QUA 2 CỬA SỔ", "QUA 1 CỬA SỔ", "KHÔNG QUA"
MUC_IT, MUC_DP = "ÍT DỮ LIỆU", "DỰ PHÒNG"
THU_TU_MUC = [MUC_2, MUC_1, MUC_0, MUC_IT, MUC_DP]
MAU = {MUC_2: "#2e7d32", MUC_1: "#ef6c00", MUC_0: "#78909c", MUC_IT: "#90a4ae", MUC_DP: "#c62828"}



# ==============================================================================
#  10 HỌ LOGIC — chép nguyên từ bản đã qua kiểm thử
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
#  CHỌN 3 HỌ + BỎ PHIẾU 50 CON — chép nguyên từ bản đã qua kiểm thử
# ==============================================================================

def chon_ho_bau(X, ds, t_kt):
    """Trên khám phá [T_BD, t_kt): mỗi họ lấy cấu hình tốt nhất của mình (theo thứ
       hạng), rồi xếp các họ. Trả (3 họ bỏ phiếu, cấu hình đại diện, điểm thứ hạng)."""
    hang = {c: _hang(c, X, T_BD, t_kt) for c in ds}
    dai = {}
    for ho, cs in HO.items():
        co = [c for c in cs if c in ds]
        if co and ho not in HO_KHONG_BAU:
            dai[ho] = min(co, key=lambda c: (hang[c], ds.index(c)))
    xep = sorted(dai, key=lambda h: (hang[dai[h]], list(HO).index(h)))
    return xep[:SO_HO_BAU], dai, hang


def bo_phieu(X, ba_ho, dai, t, thu_t):
    """Mỗi họ đề cử SO_DE_CU con. Xếp 100 con: nhiều phiếu trước; hoà phiếu thì
       tổng thứ hạng trong các họ nhỏ hơn đứng trước; cuối cùng theo số. Lấy SO_CON."""
    phieu = np.zeros(100); tong_hang = np.zeros(100)
    for h in ba_ho:
        o = _thu_tu(diem(dai[h], X, t, thu_t))
        phieu[o[:SO_DE_CU]] += 1
        pos = np.empty(100); pos[o] = np.arange(100); tong_hang += pos
    xep = sorted(range(100), key=lambda v: (-phieu[v], tong_hang[v], v))
    return sorted(xep[:SO_CON]), phieu


def _trung_bo(X, ba_ho, dai, t0, t1):
    mt, thu = X["mt"], X["thu"]
    return sum(1 for t in range(t0, t1) if mt[t] in set(bo_phieu(X, ba_ho, dai, t, thu[t])[0]))


# ==============================================================================
#  QUYẾT ĐỊNH 1 GIẢI — LUÔN ra 50 con
# ==============================================================================

def muc_tu_k(k1, k2):
    """Nhãn độ tin từ số trúng 2 cửa sổ."""
    return {2: MUC_2, 1: MUC_1, 0: MUC_0}[int(k1 >= NGUONG_KY) + int(k2 >= NGUONG_KY)]


def tan_suat_50(ds_so):
    c = np.bincount(np.asarray(ds_so, dtype=int), minlength=100) if len(ds_so) else np.zeros(100)
    return sorted(int(v) for v in _thu_tu(c)[:SO_CON])


def quyet_dinh(mt, pool, thu_list, thu_hn):
    """Không rò rỉ: 3 họ được chọn TRƯỚC cả hai cửa sổ; mỗi kỳ trong cửa sổ chỉ dùng
       dữ liệu trước nó; hôm nay dùng CHÍNH bộ 3 họ đó. Luôn trả về 50 con."""
    n = len(mt)
    if n < N_MIN:
        return {"muc": MUC_IT, "so": tan_suat_50(mt),
                "ly_do": f"chỉ {n} kỳ (cần {N_MIN} để kiểm 2 cửa sổ) — 50 con theo tần suất {n} kỳ"}
    X = _chuan_bi(mt, pool, thu_list)
    ds = cau_hinh(len(set(thu_list)) >= 2)
    t1, t2 = n - 2 * N_CUA_SO, n - N_CUA_SO
    ba_ho, dai, hang = chon_ho_bau(X, ds, t1)
    k1 = _trung_bo(X, ba_ho, dai, t1, t2)
    k2 = _trung_bo(X, ba_ho, dai, t2, n)
    so, phieu = bo_phieu(X, ba_ho, dai, n, thu_hn)
    return {"muc": muc_tu_k(k1, k2), "ba_ho": ba_ho, "cau_hinh": {h: dai[h] for h in ba_ho},
            "k1": k1, "k2": k2, "so": so, "phieu": phieu,
            "dong_thuan": {p: int(sum(1 for v in so if phieu[v] == p)) for p in range(SO_HO_BAU, -1, -1)},
            "rieng": {h: sorted(int(v) for v in _thu_tu(diem(dai[h], X, n, thu_hn))[:SO_CON]) for h in ba_ho}}


def ngau_nhien(ngay, stt, giai):
    rng = np.random.default_rng(zlib.crc32(f"{ngay}|{stt}|{giai}|50".encode()))
    return sorted(int(x) for x in rng.choice(100, SO_CON, replace=False))


# ==============================================================================
#  TIỆN ÍCH + SỔ — chép nguyên từ bản đã qua kiểm thử
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


def _tap(chuoi):
    return set(int(x) for x in chuoi.split(",")) if chuoi else set()


def wilson(t, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p, d = t / n, 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


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
        r["ket_qua"] = {"so_ve": y, "trung": y in _tap(r["so"]), "trung_ngau": y in _tap(r["ngau"])}
        moi.append(r)
    return moi


def muc_ban_ghi(r):
    """Bản ghi có số trúng 2 cửa sổ (kể cả bản ghi cũ) -> tính lại nhãn cho liền mạch."""
    if r.get("k1") is not None and r.get("k2") is not None:
        return muc_tu_k(r["k1"], r["k2"])
    return r.get("muc", MUC_DP)


def thanh_tich(tt):
    nhom = {"TẤT CẢ BỘ SỐ": [0, 0], **{m: [0, 0] for m in THU_TU_MUC}, "NGẪU NHIÊN": [0, 0]}
    for r in tt["so"]:
        kq = r.get("ket_qua")
        if not kq:
            continue
        t = int(kq["trung"])
        nhom["TẤT CẢ BỘ SỐ"][0] += t; nhom["TẤT CẢ BỘ SỐ"][1] += 1
        m = muc_ban_ghi(r); nhom[m][0] += t; nhom[m][1] += 1
        nhom["NGẪU NHIÊN"][0] += int(kq["trung_ngau"]); nhom["NGẪU NHIÊN"][1] += 1
    return nhom


def bang_ho(tt):
    """Bản 50 con: mỗi họ đã bỏ phiếu được chấm bằng 50 con RIÊNG của nó."""
    bh = {}
    for r in tt["so"]:
        kq = r.get("ket_qua")
        if not kq:
            continue
        for h, chuoi in r.get("rieng", {}).items():
            x = bh.setdefault(h, {"n": 0, "trung": 0, "ngau": 0})
            x["n"] += 1; x["trung"] += int(kq["so_ve"] in _tap(chuoi)); x["ngau"] += int(kq["trung_ngau"])
    return dict(sorted(bh.items(), key=lambda kv: -kv[1]["n"]))


def bang_ho_cu():
    """Lịch sử bản 64 con — CHỈ ĐỌC, khử trùng theo (ngày, đài, giải, họ)."""
    da, bh = set(), {}
    for f in FILE_CU:
        if not os.path.exists(f):
            continue
        try:
            ds = json.load(open(f, encoding="utf-8")).get("so", [])
        except Exception:
            continue
        for r in ds:
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



def lay_du_lieu_dai(stt):
    """Ba tầng, không bỏ phí dữ liệu đang có:
       1. Kho đủ SO_KY+30 kỳ -> dùng kho.
       2. Kho thiếu -> tải web.
       3. Web lỗi -> dùng MỌI kỳ đang có trong kho (dù ít hơn yêu cầu).
          Trước đây bước này không có: đài có 175 kỳ trong kho mà web lỗi đúng hôm đó
          bị coi như mất trắng dữ liệu và rơi xuống DỰ PHÒNG."""
    m = E.lay_tu_master(stt, SO_KY + 30)
    if m:
        return m[0], m[1]
    loi_web = None
    try:
        _, _, ng_all, tg_all, _ = E.lay_du_lieu(stt, SO_KY + 30)
        if tg_all:
            return tg_all, ng_all
    except Exception as e:
        loi_web = e
    kho = E.doc_master()
    co = len([k for k in kho["dai"].get(str(stt), {}).get("ky", []) if k.get("ngay")]) if kho else 0
    if co:
        m = E.lay_tu_master(stt, co)
        if m:
            return m[0], m[1]
    raise RuntimeError(f"không lấy được dữ liệu: {loi_web or 'kho và web đều trống'}")


# ==============================================================================
#  CHẠY 1 NGÀY — MỌI GIẢI CỦA MỌI ĐÀI ĐỀU CÓ 50 CON
# ==============================================================================

def chay(ngay=None, gui_mail=True):
    hom_nay = E.doc_ngay(ngay) if ngay else datetime.now(VN).date()
    thu = E.THU_VN[hom_nay.weekday()]
    hn = hom_nay.isoformat()
    tt = nap_tt()

    print("=" * 80)
    print(f"  ĐO NI KÉP 50 CON  |  {thu} {hom_nay:%d.%m.%Y}  |  mọi giải đều có đề xuất")
    print(f"  {SO_HO_BAU} họ bỏ phiếu · nhãn độ tin: >= {NGUONG_KY}/{N_CUA_SO} ở từng cửa sổ")
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
            tg_all, ng_all = lay_du_lieu_dai(s)
            tg, ng, _ = E.cat_truoc_ngay(tg_all, ng_all, hom_nay, SO_KY)
        except Exception as e:
            tg, ng = [], []
            d["loi"] = str(e)
        for giai, bat in (("DB", CHAY_DB), ("G1", CHAY_G1), ("G8", CHAY_G8)):
            if not bat:
                continue
            if not tg:
                if giai == "G8" and E.lay_dai(s)[1] == "xsmb":
                    continue
                o = {"muc": MUC_DP, "ly_do": d["loi"] or "không có dữ liệu", "_mt": []}
            else:
                vi = _vi_tri(tg, giai)
                if vi is None:
                    continue
                mt = [int(ky[vi][-2:]) for ky in tg]
                pool = [[int(x[-2:]) for j, x in enumerate(ky) if j != vi] for ky in tg]
                try:
                    o = quyet_dinh(mt, pool, [_thu(x) for x in ng], hom_nay.weekday())
                except Exception as e:
                    o = {"muc": MUC_DP, "ly_do": f"lỗi tính toán: {e}"}
                o["_mt"] = mt
            o.update(stt=s, dai=ten, giai=giai)
            d["o"].append(o); tat_ca.append(o)
        dai_list.append(d)

    # DỰ PHÒNG — giải nào chưa có số thì lấy tần suất gộp CÙNG GIẢI của các đài khác hôm nay
    for o in tat_ca:
        if "so" not in o:
            goc = [v for x in tat_ca if x is not o and x["giai"] == o["giai"] for v in x.get("_mt", [])]
            o["so"] = tan_suat_50(goc) if goc else list(range(SO_CON))
            o["ly_do"] = (o.get("ly_do", "") + " — " +
                          (f"50 con theo tần suất gộp {TEN_GIAI[o['giai']]} của các đài khác hôm nay ({len(goc)} kỳ)"
                           if goc else "không có dữ liệu nào để lập luận, tạm dùng 00–49"))
        o["ngau"] = ngau_nhien(hn, o["stt"], o["giai"])

    for d in dai_list:
        print(f"\n  {d['dai'].upper()}" + (f"   ⚠ {d['loi']}" if d["loi"] else ""))
        for o in d["o"]:
            chi = (f"{' + '.join(o['ba_ho'])} · cửa sổ 1: {o['k1']}/{N_CUA_SO} · cửa sổ 2: {o['k2']}/{N_CUA_SO}"
                   if "ba_ho" in o else o.get("ly_do", ""))
            print(f"     {TEN_GIAI[o['giai']]:<14} {o['muc']:<13} {chi}")

    da_co = {(r["ngay"], r["stt"], r["giai"]) for r in tt["so"]}
    for o in tat_ca:
        if (hn, o["stt"], o["giai"]) in da_co:
            continue
        r = {"ngay": hn, "stt": o["stt"], "dai": o["dai"], "giai": o["giai"], "muc": o["muc"],
             "so": _chuoi(o["so"]), "ngau": _chuoi(o["ngau"]), "ket_qua": None}
        if "ba_ho" in o:
            r.update(ba_ho=o["ba_ho"], k1=o["k1"], k2=o["k2"],
                     rieng={h: _chuoi(v) for h, v in o["rieng"].items()})
        tt["so"].append(r)
    luu_tt(tt)
    tk, bh, bh_cu = thanh_tich(tt), bang_ho(tt), bang_ho_cu()
    dem = {m: sum(1 for o in tat_ca if o["muc"] == m) for m in THU_TU_MUC}
    print(f"\n  {len(tat_ca)} bộ 50 con · " + " · ".join(f"{m} {v}" for m, v in dem.items() if v))
    for k, (a, b) in tk.items():
        if b:
            print(f"  Tiến cứu {k:<14} {a}/{b} = {a/b:.1%}")

    bc = {"ngay": hom_nay, "thu": thu, "dai": dai_list, "tat_ca": tat_ca, "tk": tk, "bh": bh,
          "bh_cu": bh_cu, "dem": dem, "n_o": len(tat_ca)}
    if gui_mail:
        print("\n  Đang gửi email...")
        gui_email(bc)
        print(f"  ✓ Đã gửi email tới {EMAIL_NHAN}")
    return bc


# ==============================================================================
#  EMAIL
# ==============================================================================

TD = 'style="padding:4px 9px;text-align:center"'


def _dong_ly_do(o):
    if "ba_ho" not in o:
        return html.escape(o.get("ly_do", ""))
    def c(k):
        ok = k >= NGUONG_KY
        return f'<span style="color:{"#2e7d32" if ok else "#c62828"}">{k}/{N_CUA_SO} {"✓" if ok else "✗"}</span>'
    ch = " + ".join(f'{html.escape(h)} ({html.escape(o["cau_hinh"][h])})' for h in o["ba_ho"])
    dt = " · ".join(f'{v} con {p}/{SO_HO_BAU} phiếu' for p, v in o["dong_thuan"].items() if v)
    return f'3 họ: {ch}<br>cửa sổ 1: {c(o["k1"])} · cửa sổ 2: {c(o["k2"])} · đồng thuận: {dt}'


def _bang_ho_html(bh, moc):
    if not bh:
        return '<p style="font-size:12px;color:#607d8b">Chưa có dữ liệu.</p>'
    h = ['<table style="font-size:12px;border-collapse:collapse">'
         '<tr style="background:#eceff1"><th style="padding:4px 9px;text-align:left">Họ logic</th>'
         f'<th {TD}>Số lượt</th><th {TD}>Trúng</th><th {TD}>Ngẫu nhiên cùng lượt</th>'
         f'<th {TD}>Chênh</th><th {TD}>KTC 95%</th></tr>']
    for ho, x in bh.items():
        lo, hi = wilson(x["trung"], x["n"]); ch = (x["trung"] - x["ngau"]) / x["n"]
        h.append(f'<tr><td style="padding:4px 9px">{html.escape(ho)}</td><td {TD}>{x["n"]}</td>'
                 f'<td {TD}><b>{x["trung"]/x["n"]:.1%}</b></td><td {TD}>{x["ngau"]/x["n"]:.1%}</td>'
                 f'<td {TD} style="color:{"#2e7d32" if ch > 0 else "#c62828"}">{ch:+.1%}</td>'
                 f'<td {TD}>[{lo:.0%}, {hi:.0%}]</td></tr>')
    h.append(f'</table><p style="font-size:11px;color:#90a4ae;margin:3px 0 0">Mốc bốc bừa ở bảng này: {moc}.</p>')
    return "".join(h)


def _html(bc):
    css = "font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;"
    ng, thu, tk = bc["ngay"], bc["thu"], bc["tk"]
    h = [f'<div style="{css}max-width:820px;color:#222">']
    h.append(f'<h2 style="margin:0 0 2px">Đo ni kép 50 con — {thu} {ng:%d.%m.%Y}</h2>')
    h.append(f'<p style="color:#666;margin:0 0 8px;font-size:13px">{len(bc["dai"])} đài · '
             f'<b>{bc["n_o"]} bộ 50 con</b> — mọi giải đều có đề xuất</p>')
    h.append('<div style="font-size:12px;margin:0 0 12px">' + " ".join(
        f'<span style="background:{MAU[m]};color:#fff;padding:2px 8px;border-radius:3px;margin-right:4px">'
        f'{m}: {v}</span>' for m, v in bc["dem"].items() if v) + '</div>')
    h.append(f'<div style="background:#fff8e1;border-left:4px solid #f9a825;padding:9px 12px;margin:0 0 16px;'
             f'font-size:12px;line-height:1.6"><b>Cách chọn:</b> kỳ 1–110 chọn {SO_HO_BAU} họ mạnh nhất → '
             f'3 họ bỏ phiếu ra {SO_CON} con. <b>Nhãn độ tin</b> (chỉ tham khảo): bộ phiếu đó trúng '
             f'≥ {NGUONG_KY}/{N_CUA_SO} ở cửa sổ kỳ 111–130 và/hoặc 131–150.<br><b>Ba mốc (50 con):</b> '
             f'bốc bừa 50% · hoà vốn {HOA_VON:.2%} · kỳ vọng −5% (tỷ lệ trả 95).</div>')

    h.append('<div style="font-size:15px;font-weight:700;margin:0 0 6px">THÀNH TÍCH TIẾN CỨU</div>')
    if not tk["TẤT CẢ BỘ SỐ"][1]:
        h.append('<p style="font-size:13px;color:#607d8b;margin:0 0 16px">Chưa có bộ số nào được chấm. '
                 'Sổ bắt đầu tích luỹ từ ngày mai.</p>')
    else:
        h.append('<table style="font-size:12px;border-collapse:collapse;margin:0 0 6px">'
                 '<tr style="background:#eceff1"><th style="padding:4px 9px;text-align:left">Nhóm</th>'
                 f'<th {TD}>Đúng/Tổng</th><th {TD}>Tỷ lệ</th><th {TD}>KTC 95%</th></tr>')
        for k, (a, b) in tk.items():
            if b:
                lo, hi = wilson(a, b)
                nhan = f'<b>{k}</b>' if k == "TẤT CẢ BỘ SỐ" else (k if k == "NGẪU NHIÊN" else f'&nbsp;&nbsp;└ {k}')
                h.append(f'<tr><td style="padding:4px 9px">{nhan}</td><td {TD}>{a}/{b}</td>'
                         f'<td {TD}><b>{a/b:.1%}</b></td><td {TD}>[{lo:.0%}, {hi:.0%}]</td></tr>')
        h.append('</table><p style="font-size:12px;color:#607d8b;margin:0 0 16px">"TẤT CẢ BỘ SỐ" phải trúng '
                 'nhiều hơn NGẪU NHIÊN qua nhiều tuần thì cách chọn có giá trị. Nếu "QUA 2 CỬA SỔ" trúng nhiều '
                 'hơn hẳn "KHÔNG QUA", nhãn độ tin đáng dùng để ưu tiên.</p>')

    for d in bc["dai"]:
        h.append(f'<div style="margin:14px 0 0;padding:8px 12px;background:#263238;color:#fff;'
                 f'border-radius:5px 5px 0 0"><b style="font-size:16px">{html.escape(d["dai"].upper())}</b>'
                 f'<span style="font-size:12px;opacity:.8"> &nbsp;|&nbsp; {html.escape(str(d["mien"]))}'
                 f' &nbsp;|&nbsp; {thu} {ng:%d.%m.%Y}</span></div>'
                 '<div style="border:1px solid #cfd8dc;border-top:0;border-radius:0 0 5px 5px;padding:4px 12px 12px">')
        for o in d["o"]:
            h.append(f'<div style="margin:10px 0 0"><b style="font-size:14px">{TEN_GIAI[o["giai"]]}</b> '
                     f'<span style="background:{MAU[o["muc"]]};color:#fff;padding:1px 7px;border-radius:3px;'
                     f'font-size:11px">{o["muc"]}</span>'
                     f'<div style="font-size:11px;color:#546e7a;margin-top:3px;line-height:1.5">{_dong_ly_do(o)}</div>'
                     f'<div style="font-family:ui-monospace,Menlo,Consolas,monospace;font-size:13px;'
                     f'background:#f1f8e9;border-left:4px solid {MAU[o["muc"]]};padding:8px 10px;margin-top:4px;'
                     f'word-break:break-all;line-height:1.85">{_chuoi(o["so"])}</div></div>')
        h.append('</div>')

    h.append('<div style="font-size:15px;font-weight:700;margin:18px 0 4px">BẢNG XẾP HẠNG HỌ LOGIC (50 con) — '
             'chỉ để theo dõi</div>')
    h.append(_bang_ho_html(bc["bh"], "50%"))
    if bc["bh_cu"]:
        h.append('<details style="margin:12px 0 0"><summary style="font-size:13px;color:#546e7a;cursor:pointer">'
                 'Lịch sử họ logic ở bản 64 con (chỉ đọc)</summary>' + _bang_ho_html(bc["bh_cu"], "64%")
                 + '</details>')
    h.append('<hr style="margin:20px 0 10px;border:0;border-top:1px solid #ddd">'
             '<p style="font-size:12px;color:#888;line-height:1.6">Mọi giải đều có 50 con. Nhãn độ tin cho biết '
             'bộ phiếu của giải đó đã đứng vững bao nhiêu cửa sổ gần nhất — không phải lời hứa trúng. Máy quay '
             'công bằng thì mọi bộ 50 con trúng 50%.</p></div>')
    return "".join(h)


def _text(bc):
    t = [f"ĐO NI KÉP 50 CON — {bc['thu']} {bc['ngay']:%d.%m.%Y}",
         f"{bc['n_o']} bộ 50 con — mọi giải đều có đề xuất", ""]
    for d in bc["dai"]:
        t.append(d["dai"].upper())
        for o in d["o"]:
            chi = (f" · {o['k1']}/{N_CUA_SO} + {o['k2']}/{N_CUA_SO}" if "ba_ho" in o else "")
            t.append(f"  {TEN_GIAI[o['giai']]} [{o['muc']}{chi}]")
            t.append("  " + _chuoi(o["so"]))
        t.append("")
    return "\n".join(t)


def gui_email(bc):
    mk = E._lay_mat_khau()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = (f"[ĐO NI KÉP 50] {bc['thu']} {bc['ngay']:%d.%m.%Y} — {bc['n_o']} bộ 50 con · "
                      f"{bc['dem'][MUC_2]} giải qua 2 cửa sổ")
    msg["From"] = formataddr(("XSMN Đo Ni Kép 50", EMAIL_GUI))
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
