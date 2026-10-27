# Chính sách chi phí và cận dưới của mỗi hành động (#7)

Với cạnh hợp lệ `(s, a, s')`, đặt `O(s)` là tập ô bị chiếm và `F` là tập ô dễ vỡ:

```text
c(s, a, s') = 1 + |(O(s') \ O(s)) ∩ F|
c_min = 1
```

Một lần di chuyển tốn một đơn vị, mỗi ô dễ vỡ mới tiếp xúc cộng thêm một đơn vị.
Khối chiếm nhiều nhất hai ô nên chi phí thuộc `{1, 2, 3}`. Phụ phí thể hiện ưu tiên
giảm tiếp xúc bề mặt dễ vỡ theo ví dụ của đề, không phải xác suất rơi. Hệ số một
cho phép giải thích trực tiếp đánh đổi giữa một lần tiếp xúc và một lần lăn thường.

Chính sách nằm duy nhất tại `Source/bloxorz/core/costs.py`; `Board.step_cost` gọi
chính sách này. Các luật chuyển trạng thái, kiểu dữ liệu và giao diện đóng băng
được giữ nguyên. Không tính lại phí cho lập phương đứng yên hoặc ô vẫn bị chiếm.
Đích dịch chuyển được xét như tiếp xúc mới; cầu và công tắc không có phụ phí riêng.
Hàm nhận cạnh hợp lệ từ engine, với các ô bị chiếm nằm trong bàn; đây không phải
giao diện định giá tọa độ tùy ý do bên gọi cung cấp.

Theo hợp đồng hiện hành, chọn lập phương đã nằm trong `(cube_index, direction)`.
Không có cạnh đổi điều khiển riêng để gán chi phí. Mọi cạnh di chuyển thực sự
đều có giá ít nhất `c_min`; không thêm cạnh miễn phí vào đồ thị tìm kiếm.

Với một cận số bước còn lại `L`, cận chi phí là `c_min * L`. Trên màn không dịch
chuyển, khoảng cách Manhattan từ ô bị chiếm gần đích nhất giảm tối đa hai mỗi
lần lăn, nên `c_min * d / 2` là cận dưới. Khi có dịch chuyển, phải dùng cận khác
đã chứng minh hoặc dùng không. Phần cài đặt và kiểm chứng A* nằm ở PR #23 riêng.
Nhân với `c_min` là phép đổi từ đơn vị bước sang chi phí; chia cho `c_min` không
cho lập luận tổng quát đúng khi thay đổi trọng số.

Trong mười màn chính thức hiện tại, phụ phí chỉ xuất hiện trên L2-01 và L2-02.
Tám màn còn lại có mọi cạnh giá 1, nên UCS có cùng thứ tự tìm kiếm với FIFO khi
dùng cách phá hòa hiện tại. Chính sách không bảo đảm UCS tìm đường rẻ hơn FIFO
trên mọi màn; tính không đồng nhất và đánh đổi số bước/chi phí phải được xét
theo từng màn. Đây là giới hạn của bộ dữ liệu, không phải kết luận về hiệu năng.

Kiểm thử gồm tiếp xúc mới, tiếp tục chiếm ô, lập phương đứng yên, đích dịch chuyển
và mọi cạnh đạt được trên mười màn chính thức. PR này không thêm thuật toán,
frontier ưu tiên, công cụ đo hay số liệu hiệu năng.

Đoạn báo cáo LaTeX: [action_cost.tex](../Report/sections/action_cost.tex), đã được
chèn trong mục UCS của `Report/main.tex` thay cho bảng trọng số cũ. Đoạn này dùng
`amsmath` và `hyperref` như mẫu nhóm. Khi mục UCS đầy đủ được ghép ở PR #63,
`ucs.tex` sẽ chèn chi phí này; không chèn thêm lần thứ hai.

Codex hỗ trợ tách phần triển khai, rà soát lập luận và kiểm thử. Nội dung được
đối chiếu với mã thực tế; người nộp cần hiểu và giải thích được trọng số đã chọn.
