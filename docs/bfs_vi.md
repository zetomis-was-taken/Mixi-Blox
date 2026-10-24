# BFS trên vòng lặp chung của nhóm (#19)

BFS gọi `base.search(stage, caps, frontier=Frontier())` từ PR #61 và giữ nguyên
base cùng giao diện `solve(stage, caps) -> SearchResult`. Toàn bộ cài đặt nằm ở
`Source/bloxorz/solvers/bfs.py`, mười một dòng; không có vòng lặp, tập đã gặp hay
bộ đếm riêng.

`Frontier` của base là hàng đợi FIFO: `push` từ chối khóa đã gặp và `pop` lấy
phần tử cũ nhất. Trạng thái được đánh dấu ngay khi sinh, nên mỗi trạng thái vào
frontier đúng một lần và vòng lặp dừng trên màn có chu trình. Kiểm tra đích diễn
ra khi lấy nút ra; các nút được lấy theo độ sâu không giảm, nên nút đích đầu tiên
có số bước nhỏ nhất.

BFS không đọc `step_cost`, vì vậy nó tối ưu số bước chứ không tối ưu chi phí.
Trên màn chỉ có ô thường, hai mục tiêu trùng nhau; trên màn có ô dễ vỡ, chi phí
theo #7 tách khỏi số bước. Hệ quả: BFS có thể trả đường ít bước hơn nhưng đắt hơn
UCS. Trên L2-02, BFS cho 46 bước với chi phí 64; UCS cho 49 bước với chi phí 58.

Kiểm thử đối chiếu số bước với một phép duyệt theo chiều rộng viết độc lập trong
`tests/test_bfs.py`, không đi qua `base.search`, trên cả mười màn chính thức. Ba
màn tính tay cho 6, 4 và 4 bước, khớp `expected.optimal_cost`; đường đi được phát
lại trên `Board`. Hai board tổng hợp khoá thứ tự FIFO và việc dừng trên chu trình.

So với UCS, `expanded`, `generated` và `frontier_peak` trùng nhau trên chín trong
mười màn; L2-02 là ngoại lệ với BFS 134/286/9 và UCS 135/288/10. Đây là kiểm tra
tính đúng, không phải đo thời gian hay bộ nhớ; hai số đo đó thuộc công cụ chung
của #24 và không được khẳng định trong mục này.

Chạy tại gốc repository:

```powershell
python -m pytest -q
python -m ruff check .
python -m Source.main --stage Source/bloxorz/core/stages/L2-02_fragile_ring.json --solver bfs
```

Báo cáo: `Report/main.tex` dùng `\input{sections/bfs}` thay mục BFS cũ, đặt trước
`\input{sections/ucs}`. `bfs.tex` tham chiếu `eq:bloxorz-action-cost` do `ucs.tex`
chèn qua `sections/action_cost`, nên không chèn chi phí lần thứ hai. Mục BFS không
lặp lại ví dụ L2-02 đã có ở UCS và A* mà trỏ về `sec:bloxorz-ucs`. Cần `amsmath`
và `hyperref` trong preamble; không sửa nội dung của thành viên khác.
