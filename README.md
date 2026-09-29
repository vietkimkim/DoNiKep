# Đo Ni Kép 50 con — ĐB · G1 · G8

Mỗi sáng 6h35 (giờ VN), workflow tự lấy kết quả mới, chạy bộ lọc hai cửa sổ cho mọi
giải của các đài quay hôm đó, rồi gửi email.

## Quy tắc
- Kỳ 1–110: xếp hạng 10 họ logic, 3 họ mạnh nhất được bỏ phiếu (họ ĐỀU không bỏ phiếu)
- Mỗi họ đề cử 64 con; lấy 50 con nhiều phiếu nhất (hoà phiếu: tổng thứ hạng nhỏ hơn đứng trước)
- Kỳ 111–130 và 131–150: CÙNG bộ 3 họ đó phải trúng >= 11/20 ở cả hai cửa sổ
- Qua cả hai -> ĐỀ XUẤT, xếp hạng theo bằng chứng (không giới hạn số đề xuất mỗi ngày)

## File
| File | Vai trò |
|---|---|
| `engine.py` | Hạ tầng: lấy dữ liệu, lịch quay, kho dữ liệu — KHÔNG xoá |
| `do_ni_kep.py` | Engine đo ni kép 50 con |
| `.github/workflows/do_ni_kep.yml` | Lịch chạy 6h35 + gửi email |
| `data/` | Code tự tạo: kho dữ liệu, sổ tiến cứu `do_ni_kep_50.json` — KHÔNG xoá |

## Secrets cần có (Settings → Secrets and variables → Actions)
`GMAIL_APP_PASSWORD` · `MAIL_USER` · `MAIL_TO`

Ba mốc (50 con): bốc bừa 50% · hoà vốn 52,63% · kỳ vọng −5% (tỷ lệ trả 95).
