# DFS trên vòng lặp chung của nhóm (#20)

DFS gọi `base.search(stage, caps, frontier=StackFrontier())` từ PR #61 và giữ
nguyên base cùng giao diện `solve(stage, caps) -> SearchResult`. Biến thể được
chọn là DFS lặp với ngăn xếp tường minh, không đệ quy, nên không chạm giới hạn
độ sâu của Python trên màn lớn.

`StackFrontier` kế thừa `Frontier` và chỉ đổi `pop` sang lấy phần tử cuối.
`push` vẫn do base giữ: khóa đã gặp bị từ chối, kể cả khi nút còn đang chờ hoặc
đã mở rộng, nên tập đã gặp chặn chu trình. Trên đồ thị hữu hạn tìm kiếm luôn
kết thúc; nó đầy đủ nhưng không tối ưu số bước lẫn chi phí.

So với UCS, DFS trả nghiệm đầu tiên chạm đích theo thứ tự ngăn xếp. Trên L1-02,
DFS cho 50 bước với chi phí 50; UCS cho 22 bước với chi phí 22. Vì vậy DFS chỉ
dùng để kiểm chứng yêu cầu về duyệt sâu, không thay UCS hay A* khi cần tối ưu.

Nhóm chọn DFS thay vì IDS và ghi lại lựa chọn này. Trên mười màn chính thức DFS
trả tổng 701 bước, còn phép duyệt FIFO trong kiểm thử trả 328 bước (2,1 lần);
mức tệ nhất là L4-02 với 168 bước so với 24. Chênh lệch vẫn đọc được như đặc
điểm của duyệt sâu nên IDS không cần thiết cho so sánh ở mục thực nghiệm.

Kiểm thử phát lại mọi đường đi trên `Board` và so chi phí với chi phí tính lại.
Ba màn tính tay cho 6, 4 và 4 bước; vì DFS không bảo đảm tối ưu, kiểm thử chỉ
ràng buộc độ dài không nhỏ hơn `expected.optimal_cost`. Hai board tổng hợp khoá
phần đặc trưng: một chu trình không có đích phải trả `unsolvable` sau ba lần mở
rộng, và một board hai đường cho DFS 5 bước trong khi FIFO cho 2 bước.

DFS mở rộng ít nút hơn UCS ở 8/10 màn vì dừng sớm, nhưng đỉnh ngăn xếp lớn hơn
ở cả 10/10 màn. Đỉnh frontier không phải toàn bộ bộ nhớ: cả hai đều giữ tập đã
gặp `O(V)`. Đây là kiểm tra tính đúng, không phải đo thời gian hay bộ nhớ; hai
số đo đó thuộc công cụ chung của #24.

Chạy tại gốc repository:

```powershell
python -m pytest -q
python -m ruff check .
python -m Source.main --stage Source/bloxorz/core/stages/L1-02_two_flights.json --solver dfs
```

Báo cáo: `Report/main.tex` dùng `\input{sections/dfs}` thay mục DFS cũ (mục cũ
khẳng định nhóm đã cài IDS, không còn đúng), đặt trước `\input{sections/ucs}`.
`dfs.tex` không lặp lại ví dụ L2-02 mà trỏ về `sec:bloxorz-ucs`; không sửa nội
dung của thành viên khác.
