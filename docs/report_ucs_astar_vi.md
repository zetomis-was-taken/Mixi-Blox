# Tìm kiếm chi phí đồng nhất và A* trong Bloxorz

Phần nội dung dành cho báo cáo chung CSC14003. [Bảng thực đo đầy đủ](informed_search_results_vi.md)
ghi kết quả bốn thuật toán dùng chung vòng lặp #18. Nhóm cần chạy lại bộ công cụ đo đạc trên phiên bản
cuối được nộp sau khi tích hợp các nhánh thành viên; số liệu này là bản bàn giao có thể tái lập.

## 1. Hình thức hóa bài toán

Trạng thái `State(cubes, bridges)` mô tả vị trí, hình dạng khối và trạng thái từng cầu. Hướng khối
được suy ra từ các ô bị chiếm, không lưu thêm góc quay có thể sai lệch. `State.key()` chứa cả hai
trường nên hai cấu hình cầu khác nhau không bị gộp. Hai lập phương sau khi tách được sắp theo vị
trí; việc đổi nhãn chúng không tạo thêm trạng thái tìm kiếm.

Hành động `(cube_index, direction)` chọn lập phương trong **trạng thái nguồn** và hướng thuộc
`{U,D,L,R}`. Chỉ số có thể đổi khi trạng thái đích được chuẩn hóa. Chọn điều khiển không sinh cạnh
riêng và không tốn bước. `Board.successors` xử lý mọi luật chuyển trạng thái, kể cả cầu, công tắc,
ô dễ vỡ, dịch chuyển và hợp nhất; bộ giải không cài lại luật chơi. Đích yêu cầu khối nguyên đứng
trên ô đích. Mọi đường đi thực đo được phát lại bằng mô hình trò chơi và kiểm tra lại tổng chi phí.

## 2. Hàm chi phí không đồng nhất

Gọi `O(s)` là tập ô bị chiếm và `F` là tập ô dễ vỡ. Với cạnh hợp lệ:

\[
c(s,a,s')=1+|(O(s')\setminus O(s))\cap F|.
\]

Mỗi lần lăn có chi phí nền 1; mỗi ô dễ vỡ **mới tiếp xúc** cộng thêm 1. Chi phí thuộc `{1,2,3}`,
do khối chiếm nhiều nhất hai ô. Trọng số nằm trong `core.costs`; `Board.step_cost` chỉ gọi chính
sách này, nên chỉnh trọng số không đòi hỏi sửa luật chuyển trạng thái hay thuật toán tìm kiếm.

Phụ phí thể hiện ưu tiên hạn chế tiếp xúc bề mặt dễ vỡ, theo ví dụ §3.4 đề bài. Đây là mục tiêu
tối ưu do nhóm thiết kế, không phải xác suất rơi: trò chơi vẫn xác định và bước hợp lệ không tự
nhiên trở thành bước có xác suất thất bại. Hệ số 1 tạo đánh đổi dễ giải thích: tránh một tiếp xúc
tương đương giảm một lần lăn thường. Không chọn hệ số bằng cách tối ưu kết quả thí nghiệm.

Một lập phương đứng yên trên ô dễ vỡ không làm tăng chi phí của mọi bước của lập phương còn lại.
Đích dịch chuyển được xét như tiếp xúc mới. Công tắc và cầu không có phụ phí riêng; đổi điều
khiển không tạo cạnh để cộng chi phí. Mọi cạnh có `c_min=1>0`; bộ giải từ chối chi phí không hữu hạn
hoặc nhỏ hơn 1. **Tổng chi phí** là tổng trọng số cạnh; **độ dài** là `len(path)`. Các màn kiểm thử
L1 không có ô dễ vỡ vẫn giữ đáp án tính tay ban đầu.

## 3. UCS

Tìm kiếm chi phí đồng nhất (Uniform-Cost Search, UCS) lấy nút có `g` nhỏ nhất từ hàng đợi ưu tiên.
`best_cost[state.key()]` lưu chi phí tốt nhất đã phát hiện. Tìm được đường rẻ hơn thì cập nhật và
đưa bản ghi mới vào hàng đợi, kể cả khi trạng thái đã từng được mở rộng. Vì `heapq` không có giảm
khóa trực tiếp, bản ghi cũ được bỏ qua lúc lấy ra nếu `g` không còn bằng `best_cost`. Khóa `(g,g,serial)` dùng
bộ đếm tăng dần để phá hòa ổn định và tránh so sánh các đối tượng trạng thái. Liên kết cha và
hành động được dùng để khôi phục đường đi.

```text
đưa gốc vào hàng đợi; chi_phí_tốt_nhất[gốc] = 0
trong khi hàng đợi chưa rỗng:
    kiểm tra giới hạn thời gian
    lấy nút có g nhỏ nhất; bỏ qua bản ghi cũ
    nếu đạt đích: khôi phục đường đi, trả kết quả giải được
    nếu đủ số lần mở rộng cho phép: trả kết quả đạt giới hạn
    tăng bộ đếm nút mở rộng
    với mỗi cạnh hợp lệ đến t:
        g_mới = g + chi_phí_cạnh
        nếu chưa biết t hoặc g_mới < chi_phí_tốt_nhất[t]:
            cập nhật chi_phí_tốt_nhất[t], đưa nút mới vào hàng đợi
nếu hàng đợi cạn: trả kết quả không có nghiệm
```

Mọi cạnh có chi phí dương, nên khi lấy đích hợp lệ ra không còn đường rẻ hơn chưa được xét. UCS tối
ưu tổng chi phí, không nhất thiết ít bước nhất. Đồ thị hữu hạn và không áp giới hạn thì tìm kiếm kết
thúc bằng nghiệm hoặc kết luận không có nghiệm.

## 4. A* và chứng minh hàm ước lượng

A* ưu tiên `f=g+h`, trong đó `h` là hàm ước lượng (heuristic), giữ cùng cơ chế cập nhật/mở lại trạng
thái. Trên màn không có công tắc tách:

\[
d(s)=\min_{(r,c)\in O(s)}(|r-r_G|+|c-c_G|),\qquad h(s)=c_{min}d(s)/2.
\]

**Không đánh giá quá cao (admissibility):** một lần lăn giảm `d` nhiều nhất hai ô. Bỏ qua vật cản,
hướng khối, cầu và ô dễ vỡ chỉ làm bài toán dễ hơn. Cần ít nhất `d/2` bước và mỗi bước tốn ít nhất
`c_min`, nên `h` không vượt chi phí tối ưu còn lại.

**Nhất quán (consistency):** trên mỗi cạnh không dịch chuyển, `d(s) <= d(s')+2`, suy ra
`h(s) <= h(s')+c_min <= h(s')+c(s,a,s')`. Tại đích `h=0`. Lập luận áp dụng cho chi phí không đồng nhất
thực tế vì phụ phí không âm.

Công tắc tách có thể dịch chuyển xa tùy ý, làm mất giới hạn hai ô. Vì vậy dùng `h=0` trên **mọi
trạng thái của một màn có công tắc tách**. Cách này không đánh giá quá cao và nhất quán, làm A* trở
thành UCS. Chỉ tắt hàm ước lượng khi khối đã tách là không đủ: chính cạnh kích hoạt dịch chuyển cũng phá cận.
Không cộng hình phạt hướng tùy ý vì có thể vượt cận dưới. Kiểm tra dữ liệu tĩnh của màn chỉ làm
một lần để tạo hàm ước lượng, không quét lưới trên từng nút.

## 5. Vòng lặp chung và độ phức tạp

`solvers/base.py` chứa một vòng lặp cho cả bốn thuật toán. BFS dùng hàng đợi vào trước ra trước
(FIFO), DFS dùng ngăn xếp vào sau ra trước (LIFO) và đánh dấu ngay khi đưa nút vào. UCS/A* dùng
hàng đợi ưu tiên cài bằng cây nhị phân dạng đống (heap) và cập nhật đường rẻ hơn. BFS tối ưu số
bước nhưng vẫn báo chi phí có trọng số của đường tìm được; DFS không bảo đảm tối ưu bước hoặc chi phí.

`generated` đếm gốc và mỗi lần thực sự đưa nút vào; `expanded` chỉ tăng ngay trước `successors`, sau
kiểm tra đích và giới hạn nút; `frontier_peak` gồm cả bản ghi cũ còn trong hàng đợi. Bản ghi cũ bị bỏ qua không
tăng expanded. Mọi trạng thái kết quả đều có bộ đếm, kể cả `cap` và `unsolvable`.

Theo mã giả trong hợp đồng, giới hạn thời gian được kiểm tra **trước khi lấy nút ra**, nên có thể
chặn đích đang chờ. Giới hạn nút được kiểm tra **sau kiểm tra đích**, nên tìm được đích đúng số lần
mở rộng tối đa vẫn trả `solved`. Phần diễn giải hợp đồng đã phân biệt hai giới hạn để khớp mã giả;
không thay đổi giao diện lập trình.

Với hàm ước lượng nhất quán đang dùng, mỗi trạng thái được mở rộng nhiều nhất một lần hợp lệ. Gọi
`V,E` là số trạng thái/cạnh đạt được: UCS/A* dùng hàng đợi ưu tiên có thời gian `O((V+E)log(V+E))`, bộ nhớ
`O(V+E)` kể cả bản ghi thay thế. BFS/DFS dùng `O(V+E)` thời gian và `O(V)` bộ nhớ. DFS có tập đã thăm toàn
cục nên không được mô tả là chỉ tốn bộ nhớ theo độ sâu.

## 6. Kiểm thử và thực nghiệm

Kiểm thử bao gồm ba màn tính tay, phát lại đường đi, không giải được, giới hạn tìm kiếm, đồ thị có
trọng số, bản ghi cũ và mở lại nút đã mở rộng dưới hàm ước lượng không đánh giá quá cao nhưng không
nhất quán. Chi phí được kiểm tra trên màn thật cho tiếp xúc ô dễ vỡ, lập phương đứng yên và đích
dịch chuyển. Giao diện dòng lệnh được kiểm tra qua tiến trình con như khi chạy từ bản sao mã nguồn sạch.

Với từng màn chính thức, kiểm thử duyệt toàn bộ trạng thái đạt được, tạo đồ thị cạnh ngược và
tính chi phí còn lại bằng một phép tìm đường ngắn độc lập từ các trạng thái đích. Giá trị này
được so với nghiệm UCS/A* và hàm ước lượng trên mọi trạng thái có đường tới đích; mọi cạnh đều được
kiểm tra tính nhất quán. Tổng cộng **2.946 trạng thái**, bao gồm cầu và tách/hợp nhất.

[Bảng thực đo](informed_search_results_vi.md) chứa từng cặp thuật toán–màn. Mỗi cặp chạy ba lần
độc lập; trạng thái kết quả, đường đi, chi phí và ba bộ đếm phải trùng nhau, còn thời gian và bộ nhớ
cấp phát đỉnh lấy trung vị riêng. `gc.collect()` chạy trước mỗi lần; `tracemalloc` được khởi động,
đặt lại và luôn dừng trong `finally`. Cửa sổ đo chỉ gồm `solve(stage,caps)`: không gồm nạp dữ liệu,
kiểm tra hợp lệ, biên dịch chỉ mục, phát lại lời giải hay đọc/ghi. Bộ nhớ cấp phát đỉnh của Python
không phải RAM toàn tiến trình. Kết quả đạt giới hạn hoặc không có nghiệm giữ số liệu công việc đã
làm và ghi `-` cho độ dài/chi phí; ngoại lệ được ghi riêng với chỉ số thiếu, không tạo hàng số 0 giả.

Mười màn lấy từ tập đã đối chiếu trong [tài liệu nguồn gốc màn chơi](../CREDITS.md): ba L1 cơ bản, hai L2 dễ vỡ,
ba L3 công tắc/cầu, hai L4 tách. Ba màn kiểm thử tính tay không được tính thêm vào mười màn thực nghiệm.

| Ví dụ L2-02 | Số bước | Tổng chi phí | Số nút mở rộng |
| --- | ---: | ---: | ---: |
| BFS | 46 | 64 | 134 |
| UCS | 49 | 58 | 135 |
| A* | 49 | 58 | 130 |

UCS/A* chọn thêm ba bước để giảm sáu đơn vị chi phí, tức 9,38% so với đường BFS. Trên L1-01, A* giảm
số nút mở rộng từ 64 xuống 27; trên L3-02 cả hai cùng mở rộng 186 nút. Trên hai L4, các bộ đếm UCS/A*
trùng nhau vì `h=0`. Không kết luận A* luôn nhanh hơn: chi phí tính hàm ước lượng và độ chặt của cận
đều ảnh hưởng thời gian thực đo. DFS có thể mở rộng ít nút hơn nhưng trả đường dài, ví dụ 168 bước
trên L4-02 so với 24.

Công cụ sinh năm biểu đồ: thời gian, bộ nhớ cấp phát đỉnh, số nút mở rộng, độ dài và tổng chi phí tại
`Report/figures/informed_search/`. Dữ liệu gốc CSV/JSON, ba mẫu mỗi chỉ số, phiên bản Python, nền tảng,
mã phiên bản nền và SHA-256 mã/màn nằm trong `Report/data/informed_search/`. Thời gian phụ thuộc máy và
tải nền; phải chạy lại trên phiên bản nộp chung thay vì ghép số từ các máy khác nhau.

## 7. Phân công và hỗ trợ của trí tuệ nhân tạo

Phần bàn giao này gồm hàm chi phí (#7/#22), UCS (#22), A* (#23), hạ tầng chung (#18), kiểm thử và nội
dung báo cáo tương ứng. BFS/DFS là các phiên bản đối chứng của vòng lặp chung; không nhận thay phân
công hay tự đóng nhiệm vụ #19/#20 của thành viên khác. Giao diện đồ họa, bản ghi trình diễn và báo
cáo tổng hợp thuộc phần việc của nhóm.

Đã sử dụng Codex để rà soát, hỗ trợ cài đặt, tạo kiểm thử, đo đạc và biên soạn. Yêu cầu chính là hoàn
thiện UCS/A*, chi phí không đồng nhất, xác minh hàm ước lượng và chuẩn bị bàn giao. Kết quả được kiểm
chứng bằng kiểm thử, phép tính đối chiếu độc lập và phát lại lời giải. Người nộp cần hiểu và giải thích được thuật toán,
trọng số, số liệu và các giới hạn khi vấn đáp.

## Tài liệu tham khảo

1. Đề bài CSC14003, Project 1: Bloxorz Solver, §3.2–3.6, PDF do học phần cung cấp.
2. [Hợp đồng nhóm](contracts.md), các nhiệm vụ #7, #18, #22 và #23.
3. [Nguồn màn chơi và dữ liệu đối chiếu](../CREDITS.md).
4. [Tài liệu Python về heapq](https://docs.python.org/3/library/heapq.html).
5. [Tài liệu Python về tracemalloc](https://docs.python.org/3/library/tracemalloc.html).
