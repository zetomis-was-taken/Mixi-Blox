# UCS và A* trong Bloxorz

Phần nội dung dành cho báo cáo chung CSC14003. [Bảng thực đo đầy đủ](informed_search_results_vi.md)
ghi kết quả bốn adapter dùng chung vòng lặp #18. Nhóm cần chạy lại harness chung trên phiên bản
cuối được nộp sau khi tích hợp các nhánh thành viên; số liệu này là bản bàn giao có thể tái lập.

## 1. Hình thức hóa bài toán

Trạng thái `State(cubes, bridges)` mô tả vị trí, hình dạng khối và trạng thái từng cầu. Hướng khối
được suy ra từ các ô bị chiếm, không lưu thêm góc quay có thể sai lệch. `State.key()` chứa cả hai
trường nên hai cấu hình cầu khác nhau không bị gộp. Hai lập phương sau khi tách được sắp theo vị
trí; việc đổi nhãn chúng không tạo thêm trạng thái tìm kiếm.

Hành động `(cube_index, direction)` chọn lập phương trong **trạng thái nguồn** và hướng thuộc
`{U,D,L,R}`. Chỉ số có thể đổi khi trạng thái đích được chuẩn hóa. Chọn điều khiển không sinh cạnh
riêng và không tốn bước. `Board.successors` xử lý mọi luật chuyển trạng thái, kể cả cầu, công tắc,
ô dễ vỡ, dịch chuyển và hợp nhất; solver không cài lại luật chơi. Đích yêu cầu khối nguyên đứng
trên ô đích. Mọi đường đi thực đo được phát lại bằng engine và kiểm tra lại tổng cost.

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

Một lập phương đứng yên trên ô dễ vỡ không làm tăng cost của mọi bước của lập phương còn lại.
Đích dịch chuyển được xét như tiếp xúc mới. Công tắc và cầu không có phụ phí riêng; đổi điều
khiển không tạo cạnh để cộng cost. Mọi cạnh có `c_min=1>0`; solver từ chối cost không hữu hạn hoặc
nhỏ hơn 1. **Tổng chi phí** là tổng trọng số cạnh; **độ dài** là `len(path)`. Các fixture L1 không
có ô dễ vỡ vẫn giữ đáp án tính tay ban đầu.

## 3. UCS

Tìm kiếm chi phí đồng nhất (Uniform-Cost Search, UCS) lấy nút có `g` nhỏ nhất từ hàng đợi ưu tiên.
`best_cost[state.key()]` lưu chi phí tốt nhất đã phát hiện. Tìm được đường rẻ hơn thì cập nhật và
push bản ghi mới, kể cả khi trạng thái đã từng được mở rộng. Vì `heapq` không có giảm khóa trực
tiếp, bản ghi cũ được bỏ qua lúc pop nếu `g` không còn bằng `best_cost`. Khóa `(g,g,serial)` dùng
bộ đếm tăng dần để phá hòa ổn định và tránh so sánh các đối tượng trạng thái. Liên kết cha và
hành động được dùng để khôi phục đường đi.

```text
push(gốc); best[gốc] = 0
trong khi frontier chưa rỗng:
    kiểm tra time cap
    pop nút có g nhỏ nhất; bỏ qua bản ghi cũ
    nếu đạt đích: khôi phục đường đi, trả solved
    nếu đủ số lần mở rộng cho phép: trả cap
    tăng expanded
    với mỗi cạnh hợp lệ đến t:
        g_mới = g + step_cost
        nếu chưa biết t hoặc g_mới < best[t]: cập nhật best[t], push nút mới
nếu frontier cạn: trả unsolvable
```

Mọi cạnh có chi phí dương, nên khi pop đích hợp lệ không còn đường rẻ hơn chưa được xét. UCS tối
ưu tổng chi phí, không nhất thiết ít bước nhất. Graph hữu hạn và không áp cap thì tìm kiếm kết
thúc bằng nghiệm hoặc kết luận không có nghiệm.

## 4. A* và chứng minh heuristic

A* ưu tiên `f=g+h`, giữ cùng cơ chế cập nhật/mở lại trạng thái. Trên màn không có công tắc tách:

\[
d(s)=\min_{(r,c)\in O(s)}(|r-r_G|+|c-c_G|),\qquad h(s)=c_{min}d(s)/2.
\]

**Không đánh giá quá cao (admissibility):** một lần lăn giảm `d` nhiều nhất hai ô. Bỏ qua vật cản,
hướng khối, cầu và ô dễ vỡ chỉ làm bài toán dễ hơn. Cần ít nhất `d/2` bước và mỗi bước tốn ít nhất
`c_min`, nên `h` không vượt chi phí tối ưu còn lại.

**Nhất quán (consistency):** trên mỗi cạnh không dịch chuyển, `d(s) <= d(s')+2`, suy ra
`h(s) <= h(s')+c_min <= h(s')+c(s,a,s')`. Tại đích `h=0`. Lập luận áp dụng cho cost không đồng nhất
thực tế vì phụ phí không âm.

Công tắc tách có thể dịch chuyển xa tùy ý, làm mất giới hạn hai ô. Vì vậy dùng `h=0` trên **mọi
trạng thái của một màn có công tắc tách**. Cách này admissible và consistent, làm A* trở thành UCS.
Chỉ tắt heuristic khi khối đã tách là không đủ: chính cạnh kích hoạt dịch chuyển cũng phá cận.
Không cộng hình phạt hướng tùy ý vì có thể vượt cận dưới. Kiểm tra dữ liệu tĩnh của màn chỉ làm
một lần để tạo hàm heuristic, không quét grid trên từng nút.

## 5. Vòng lặp chung và độ phức tạp

`solvers/base.py` chứa một vòng lặp cho cả bốn adapter. BFS dùng FIFO, DFS dùng LIFO và đánh dấu
ngay khi push. UCS/A* dùng heap và cập nhật đường rẻ hơn. BFS tối ưu số bước nhưng vẫn báo cost có
trọng số của đường tìm được; DFS không bảo đảm tối ưu bước hoặc cost.

`generated` đếm gốc và mỗi lần push thực sự; `expanded` chỉ tăng ngay trước `successors`, sau
goal test và node cap; `frontier_peak` gồm cả entry cũ còn trong frontier. Entry cũ bị bỏ qua không
tăng expanded. Mọi trạng thái kết quả đều có bộ đếm, kể cả `cap` và `unsolvable`.

Theo pseudocode hợp đồng, time cap kiểm tra **trước pop**, nên có thể chặn đích đang chờ. Node cap
kiểm tra **sau goal test**, nên tìm được đích đúng số expansion tối đa vẫn trả `solved`. Phần diễn
giải hợp đồng đã phân biệt hai cap để khớp pseudocode; không thay đổi API.

Với heuristic consistent đang dùng, mỗi trạng thái được mở rộng nhiều nhất một lần hợp lệ. Gọi
`V,E` là số trạng thái/cạnh đạt được: UCS/A* dùng heap có thời gian `O((V+E)log(V+E))`, bộ nhớ
`O(V+E)` kể cả entry thay thế. BFS/DFS dùng `O(V+E)` thời gian và `O(V)` bộ nhớ. DFS có visited toàn
cục nên không được mô tả là chỉ tốn bộ nhớ theo độ sâu.

## 6. Kiểm thử và thực nghiệm

Test bao gồm ba fixture tính tay, replay, không giải được, cap, graph có trọng số, entry cũ và
mở lại nút đã expanded dưới heuristic admissible nhưng inconsistent. Cost được kiểm tra trên
board thật cho tiếp xúc ô dễ vỡ, lập phương đứng yên và đích dịch chuyển. CLI được kiểm tra qua
subprocess như khi chạy từ checkout sạch.

Với từng màn chính thức, kiểm thử duyệt toàn bộ trạng thái đạt được, tạo graph cạnh ngược và
tính chi phí còn lại bằng một phép tìm đường ngắn độc lập từ các trạng thái đích. Giá trị này
được so với nghiệm UCS/A* và heuristic trên mọi trạng thái có đường tới đích; mọi cạnh đều được
kiểm tra consistency. Tổng cộng **2.946 trạng thái**, bao gồm cầu và tách/hợp nhất.

[Bảng thực đo](informed_search_results_vi.md) chứa từng cặp thuật toán–màn. Mỗi cặp chạy ba lần
độc lập; status, path, cost và ba bộ đếm phải trùng nhau, còn time/peak heap lấy trung vị riêng.
`gc.collect()` chạy trước mỗi lần; `tracemalloc` được start/reset và luôn stop trong `finally`.
Cửa sổ đo chỉ gồm `solve(stage,caps)`: không gồm load, validation, biên dịch chỉ mục, replay hay
I/O. Peak heap Python không phải RAM toàn tiến trình. Cap/unsolvable giữ số liệu công việc đã
làm và ghi `-` cho độ dài/cost; exception được ghi riêng với metric thiếu, không tạo hàng số 0 giả.

Mười màn lấy từ tập đã đối chiếu trong [CREDITS](../CREDITS.md): ba L1 cơ bản, hai L2 dễ vỡ,
ba L3 công tắc/cầu, hai L4 tách. Ba fixture không được tính thêm vào mười màn thực nghiệm.

| Ví dụ L2-02 | Số bước | Tổng cost | Expanded |
| --- | ---: | ---: | ---: |
| BFS | 46 | 64 | 134 |
| UCS | 49 | 58 | 135 |
| A* | 49 | 58 | 130 |

UCS/A* chọn thêm ba bước để giảm sáu cost, tức 9,38% so với đường BFS. Trên L1-01, A* giảm expanded
từ 64 xuống 27; trên L3-02 cả hai cùng expanded 186. Trên hai L4, các bộ đếm UCS/A* trùng nhau vì
`h=0`. Không kết luận A* luôn nhanh hơn: overhead heuristic và độ chặt của cận đều ảnh hưởng thời
gian thực đo. DFS có thể expanded ít hơn nhưng trả đường dài, ví dụ 168 bước trên L4-02 so với 24.

Công cụ sinh năm biểu đồ: thời gian, peak heap, expanded, độ dài và tổng cost tại
`Report/figures/informed_search/`. Raw CSV/JSON, ba mẫu mỗi metric, phiên bản Python, nền tảng,
commit nền và SHA-256 mã/màn nằm trong `Report/data/informed_search/`. Thời gian phụ thuộc máy và
tải nền; phải chạy lại trên phiên bản nộp chung thay vì ghép số từ các máy khác nhau.

## 7. Phân công và hỗ trợ AI

Phần bàn giao này gồm cost (#7/#22), UCS (#22), A* (#23), hạ tầng chung (#18), kiểm thử và nội dung
báo cáo tương ứng. BFS/DFS là adapter đối chứng của vòng lặp chung; không nhận thay phân công hay
tự đóng issue #19/#20 của thành viên khác. GUI, video và báo cáo tổng hợp thuộc luồng nhóm.

Đã sử dụng Codex để rà soát, hỗ trợ cài đặt, tạo test, đo đạc và biên soạn. Yêu cầu chính là hoàn
thiện UCS/A*, cost không đồng nhất, xác minh heuristic và chuẩn bị bàn giao. Kết quả được kiểm
chứng bằng test, oracle độc lập và replay. Người nộp cần hiểu và giải thích được thuật toán,
trọng số, số liệu và các giới hạn khi vấn đáp.

## Tài liệu tham khảo

1. Đề bài CSC14003, Project 1: Bloxorz Solver, §3.2–3.6, PDF do học phần cung cấp.
2. [Hợp đồng nhóm](contracts.md), các issue #7, #18, #22 và #23.
3. [Nguồn màn chơi và dữ liệu đối chiếu](../CREDITS.md).
4. [Tài liệu Python về heapq](https://docs.python.org/3/library/heapq.html).
5. [Tài liệu Python về tracemalloc](https://docs.python.org/3/library/tracemalloc.html).
