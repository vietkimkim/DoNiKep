# Đo Ni Kép — 64 con cho ĐB · G1 · G8

M��i sáng 6h35 (giờ VN), workflow tự lấy kết quả mới, chạy bộ lọc hai cửa sổ cho mọi
giải của các đài quay hôm đó, rồi gửi email.

## Quy tắc
- Kỳ 1–110: chọn họ logic phù hợp nhất (10 họ, chọn theo thứ hạng)
- Kỳ 111–130 và 131–150: CÙNG họ đó phải trúng >= 14/20 ở cả hai cửa sổ
- Qua cả hai -> tối đa 3 giải mạnh nhất được ĐỀ XUẤT, còn lại là DỰ BỊ

## File
| File | Vai trò |
|---|---|
| `engine.py` | Hạ tầng: lấy dữ liệu, lịch quay, kho dữ liệu — KHÔNG xoá |
| `do_ni_kep.py` | Engine đo ni kép |
| `.github/workflows/do_ni_kep.yml` | Lịch chạy 6h35 + gửi email |
| `data/` | Code tự tạo: kho dữ liệu và sổ tiến cứu — KHÔNG xoá |

## Secrets cần có (Settings → Secrets and variables → Actions)
`GMAIL_APP_PASSWORD` · `MAIL_USER` · `MAIL_TO`

Ba mốc: bốc bừa 64% · hoà vốn 67,37% · kỳ vọng −5% (tỷ lệ trả 95).
