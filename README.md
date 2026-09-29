# Đo Ni Kép 50 con — ĐB · G1 · G8

Mỗi sáng 6h35 (giờ VN), workflow tự lấy kết quả mới, chạy bộ lọc hai cửa sổ cho mọi
giải của các đài quay hôm đó, rồi gửi email.

## Quy tắc
- MỌI giải của MỌI đài quay hôm đó đều có bộ 50 con
- Kỳ 1–110: xếp hạng 10 họ logic, 3 họ mạnh nhất bỏ phiếu (họ ĐỀU không bỏ phiếu)
- Mỗi họ đề cử 64 con; lấy 50 con nhiều phiếu nhất (hoà phiếu: tổng thứ hạng nhỏ hơn đứng trước)
- Nhãn độ tin (chỉ tham khảo, không chặn): bộ phiếu trúng >= 11/20 ở cửa sổ kỳ 111–130
  và/hoặc 131–150 -> QUA 2 CỬA SỔ / QUA 1 CỬA SỔ / KHÔNG QUA
- Đài ít dữ liệu -> 50 con theo tần suất; đài lỗi dữ liệu -> 50 con theo tần suất gộp cùng giải

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
