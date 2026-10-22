# UCS theo hạ tầng base của nhóm (#22)

UCS gọi `base.search(stage, caps, frontier=CostFrontier())` từ PR #61, giữ nguyên
base và giao diện `solve(stage, caps) -> SearchResult`. Chính sách chi phí của #7
được dùng qua `Board.step_cost`; trọng số không nằm trong vòng lặp tìm kiếm.

`CostFrontier` sở hữu bảng chi phí tốt nhất theo khóa chuẩn hóa. Cải thiện nghiêm
ngặt thay thế nút đang chờ hoặc mở lại trạng thái đã lấy ra. Một bảng nút hiện
hành phân biệt bản ghi cũ trong heap. `len` và `bool` đếm nút hiện hành, theo
quyết định của người phụ trách #18. `generated` do base đếm mọi successor được
đề nghị, kể cả khi frontier từ chối; `frontier_peak` không tính bản ghi cũ.

Kết quả chứa tổng chi phí `cost` và đường đi `path`; số bước là `len(path)`.
Ví dụ L2-02: FIFO kiểm thử cho 46 bước/chi phí 64, UCS cho 49 bước/chi phí 58.
Điều này chứng minh hai mục tiêu khác nhau; không phải đo hiệu năng.

Kiểm thử đối chiếu chi phí với đồ thị đảo độc lập trên mười màn, phát lại đường
đi, màn nhỏ tính tay, giới hạn, trạng thái không có nghiệm, thay thế và mở lại
nút, cùng trường hợp heap chỉ còn bản ghi cũ. Giá trị không hữu hạn hoặc cạnh
có chi phí thấp hơn `c_min` bị từ chối trong frontier. Heap dùng thứ tự chèn để
phá hòa và không so sánh trạng thái.

Chạy tại gốc repository:

```powershell
python -m pytest -q
python -m ruff check .
python -m Source.main --stage Source/bloxorz/core/stages/L2-02_fragile_ring.json --solver ucs
```

Báo cáo: chèn `\input{sections/ucs}` thay mục UCS cũ. Tệp đó chèn tiếp
`sections/action_cost` từ #7; không chèn chi phí lần thứ hai. Cần `amsmath`
và `hyperref` trong preamble. Không sửa các mục của thành viên khác.

Codex hỗ trợ chuyển UCS sang frontier của PR #61, tách kiểm thử và biên soạn
nội dung. Các kết luận dựa trên phát lại và đối chiếu chi phí độc lập; chưa thêm
số đo thời gian, bộ nhớ hoặc tuyên bố cải thiện hiệu năng.
