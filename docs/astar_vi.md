# A* và hàm ước lượng theo chi phí thực tế (#23)

A* dùng `base.search` từ PR #61 và kế thừa `CostFrontier` của UCS. Phần thay đổi
thứ tự nằm trong `AStarFrontier.priority`: `f = g + h`. Không có vòng lặp, bảng
trạng thái lặp hoặc bộ đếm thứ hai.

Trên màn không có công tắc tách:

```text
d(s) = min Manhattan(p, goal), với p thuộc các ô bị chiếm
h(s) = c_min * d(s) / 2
```

Một lần lăn giảm `d` tối đa hai, nên cần ít nhất `d/2` lần lăn. Mỗi cạnh tốn ít
nhất `c_min`; vì vậy hàm ước lượng không đánh giá quá cao. Với từng cạnh,
`d(s) <= d(s') + 2`, suy ra `h(s) <= c_min + h(s') <= c(s,a,s') + h(s')`.
Tại đích, `h=0`; do đó hàm nhất quán theo chính trọng số không đồng nhất của #7.

Màn có công tắc tách dùng `h=0` trên mọi trạng thái, kể cả trước khi tách, vì
cạnh kích hoạt có thể dịch chuyển xa. A* khi đó trùng chiến lược UCS; không
khẳng định cải thiện hiệu năng. Dữ liệu tĩnh được kiểm tra một lần mỗi lần giải.

Không cộng thêm một đơn vị cho khối nằm: trên FIX-01, trạng thái sau năm lần
đi phải chỉ cần một bước chi phí 1 để thắng. Giá trị đang dùng là 0,5; cộng
một thành 1,5 sẽ vượt chi phí thật. Hạng phạt hướng là tùy chọn và chưa được
sử dụng nếu chưa có chứng minh đúng.

Kiểm thử đối chiếu mọi chi phí còn lại hữu hạn trên ba màn tính tay; trên mười
màn chính thức, duyệt 2.946 trạng thái, kiểm tra cận và tính nhất quán trên từng
cạnh, phát lại đường đi và so sánh chi phí UCS. Một đồ thị riêng kiểm tra mở lại
trạng thái dưới hàm ước lượng không đánh giá quá cao nhưng không nhất quán.

Chạy tại gốc repository:

```powershell
python -m pytest -q
python -m ruff check .
python -m Source.main --stage Source/bloxorz/core/stages/L2-02_fragile_ring.json --solver astar
```

`Report/main.tex` đã ghép hai mục UCS/A* bằng các dòng sau, theo thứ tự:

```tex
\input{sections/ucs}
\input{sections/astar}
```

`ucs.tex` đã chèn `action_cost.tex`; không chèn chi phí lần nữa. Phụ lục công bố
AI đã chèn `\input{sections/informed_search_ai_usage}`. Cần `amsmath` và
`hyperref` như mẫu nhóm. Các đoạn mới thay nội dung cũ để tránh hai bộ trọng số
và hai heuristic khác nhau. Người phụ trách báo cáo cần rà soát phần mô hình,
nhận xét hiệu năng và GUI xung quanh; phần này không sửa nội dung của đồng đội.

Trạng thái tích hợp và lỗi có sẵn ngoài phạm vi các mục được giao nằm ở
[ghi chú tích hợp báo cáo](report_integration_status.md).
