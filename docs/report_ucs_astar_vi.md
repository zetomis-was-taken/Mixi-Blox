# Tìm kiếm chi phí đồng nhất và A* trong Bloxorz

Phần nội dung này phục vụ #7, #22, #23 và hạ tầng tìm kiếm chung #18. Đo hiệu năng, biểu đồ và
phân tích thực nghiệm toàn nhóm thuộc giai đoạn tích hợp sau, không nằm trong phần bàn giao này.

## 1. Hình thức hóa bài toán

Trạng thái `State(cubes, bridges)` chứa vị trí, hình dạng khối và trạng thái từng cầu. Hướng khối
được suy ra từ các ô bị chiếm. `State.key()` chứa cả hai trường nên các cấu hình cầu khác nhau
không bị gộp. Hai lập phương sau khi tách được sắp theo vị trí; đổi nhãn chúng không tạo thêm
trạng thái tìm kiếm.

Hành động `(cube_index, direction)` chọn lập phương trong **trạng thái nguồn** và hướng thuộc
`{U,D,L,R}`. Chỉ số có thể đổi khi trạng thái kế tiếp được chuẩn hóa. Chọn điều khiển không sinh
cạnh riêng và không tốn bước. `Board.successors` xử lý luật trò chơi, gồm ô dễ vỡ, cầu, công tắc,
dịch chuyển và hợp nhất. Bộ giải chỉ duyệt các cạnh hợp lệ được cung cấp.

Đích yêu cầu khối nguyên đứng trên ô đích; khối nằm qua đích hoặc một lập phương riêng lẻ không
thắng. Đường đi trả về được phát lại bằng mô hình trò chơi và tính lại tổng chi phí.

## 2. Hàm chi phí và chi phí nhỏ nhất (#7, #22)

Gọi `O(s)` là tập ô bị chiếm và `F` là tập ô dễ vỡ. Với cạnh hợp lệ:

\[
c(s,a,s')=1+|(O(s')\setminus O(s))\cap F|.
\]

Mỗi lần lăn có chi phí nền 1; mỗi ô dễ vỡ **mới tiếp xúc** cộng thêm 1. Trọng số thuộc `{1,2,3}`
vì khối chiếm nhiều nhất hai ô. Chính sách nằm trong `core.costs`; `Board.step_cost` chỉ gọi chính
sách này. Điều chỉnh trọng số không đòi hỏi sửa luật chuyển trạng thái hay vòng lặp tìm kiếm.

Phụ phí thể hiện ưu tiên hạn chế tiếp xúc bề mặt dễ vỡ, theo ví dụ §3.4 đề bài. Đây là mục tiêu
tối ưu được thiết kế, không phải xác suất rơi: trò chơi vẫn xác định. Hệ số 1 tạo đánh đổi dễ
giải thích: tránh một tiếp xúc tương đương giảm một lần lăn thường. Không chọn hệ số bằng cách
tối ưu kết quả thí nghiệm.

Lập phương đứng yên trên ô dễ vỡ không làm tăng chi phí mọi bước của lập phương còn lại. Đích
dịch chuyển được tính như tiếp xúc mới. Công tắc và cầu không có phụ phí riêng. Hợp đồng hiện
hành không có hành động đổi điều khiển riêng: chỉ số lập phương nằm trong hành động di chuyển,
nên không thêm cạnh chi phí 0 hoặc 1 để chọn điều khiển.

Mọi cạnh có `c_min=1>0`; bộ giải từ chối chi phí không hữu hạn hoặc nhỏ hơn 1. **Tổng chi phí**
là tổng trọng số cạnh; **độ dài** là `len(path)`. Hai đại lượng được xét riêng. Các màn L1 không
có ô dễ vỡ vẫn giữ đáp án tính tay ban đầu.

## 3. Thuật toán UCS (#22)

Tìm kiếm chi phí đồng nhất (Uniform-Cost Search, UCS) lấy nút có `g` nhỏ nhất từ hàng đợi ưu tiên.
`best_cost[state.key()]` lưu chi phí tốt nhất đã biết. Tìm được đường rẻ hơn thì cập nhật và đưa
bản ghi mới vào, kể cả khi trạng thái từng được mở rộng. Vì `heapq` không có giảm khóa trực tiếp,
bản ghi cũ bị bỏ qua khi lấy ra nếu `g` không còn bằng `best_cost`. Bộ đếm thứ tự tăng dần phá
hòa ổn định và tránh so sánh đối tượng trạng thái. Liên kết cha giúp khôi phục đường đi.

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

Mọi cạnh có chi phí dương, nên khi lấy đích hợp lệ ra không còn đường rẻ hơn chưa được xét. UCS
tối ưu chi phí, không nhất thiết ít bước nhất. Đồ thị hữu hạn và không áp giới hạn thì thuật
toán kết thúc bằng nghiệm hoặc kết luận không có nghiệm.

Ví dụ trên L2-02: phép duyệt đối chiếu **chỉ nằm trong kiểm thử** tìm đường ít bước nhất dài 46
bước, chi phí 64. UCS/A* chọn đường dài 49 bước nhưng chi phí chỉ 58. Ví dụ này kiểm tra ý nghĩa
của trọng số; nó không phải bảng đánh giá hiệu năng các thuật toán.

## 4. A* và chứng minh hàm ước lượng (#23)

A* ưu tiên `f=g+h`, với `h` là hàm ước lượng (heuristic), giữ cơ chế cập nhật và mở lại trạng
thái như UCS. Trên màn không có công tắc tách:

\[
d(s)=\min_{(r,c)\in O(s)}(|r-r_G|+|c-c_G|),\qquad h(s)=c_{min}d(s)/2.
\]

**Không đánh giá quá cao (admissibility):** mỗi lần lăn giảm `d` nhiều nhất hai ô. Bỏ qua vật cản,
hướng khối, cầu và ô dễ vỡ chỉ làm bài toán dễ hơn. Cần ít nhất `d/2` bước và mỗi bước tốn ít nhất
`c_min`, nên `h` không vượt chi phí tối ưu còn lại.

**Nhất quán (consistency):** trên cạnh không dịch chuyển, `d(s) <= d(s')+2`, suy ra
`h(s) <= h(s')+c_min <= h(s')+c(s,a,s')`. Tại đích `h=0`. Lập luận áp dụng trực tiếp cho chi phí
không đồng nhất đang dùng vì phụ phí không âm.

Công tắc tách dịch chuyển xa tùy ý, làm mất giới hạn hai ô. Vì vậy dùng `h=0` trên **mọi trạng
thái của màn có công tắc tách**. Phương án này không đánh giá quá cao và nhất quán, làm A* trở
thành UCS. Chỉ tắt hàm ước lượng sau khi đã tách là không đủ: cạnh kích hoạt dịch chuyển cũng có
thể phá cận. Không cộng hình phạt hướng tùy ý vì có thể vượt cận dưới. Dữ liệu tĩnh được kiểm tra
một lần để tạo hàm ước lượng, không quét lưới trên từng nút.

## 5. Vòng lặp chung, giới hạn và bộ đếm (#18)

`solvers/base.py` có một vòng lặp với ba cách sắp thứ tự: vào trước ra trước (FIFO), vào sau ra
trước (LIFO), hoặc theo độ ưu tiên chi phí. Hai cách đầu đánh dấu trạng thái ngay khi đưa vào;
cách ưu tiên cho phép cập nhật đường rẻ hơn. FIFO/LIFO là các điểm mở rộng cho thành viên phụ
trách BFS/DFS tích hợp sau; nhánh này không chứa các mô-đun BFS/DFS riêng.

`generated` đếm gốc và mỗi lần thực sự đưa nút vào; `expanded` chỉ tăng trước `successors`, sau
kiểm tra đích và giới hạn nút; `frontier_peak` gồm cả bản ghi cũ còn trong hàng đợi. Bỏ qua bản
ghi cũ không tăng số nút mở rộng. `Counts` được trả cho kết quả giải được, đạt giới hạn và không
có nghiệm. Thời gian và bộ nhớ thực nghiệm do bộ công cụ đo đạc của nhóm phụ trách.

Theo mã giả hợp đồng, giới hạn thời gian kiểm tra **trước khi lấy nút ra**, nên có thể chặn đích
đang chờ. Giới hạn nút kiểm tra **sau kiểm tra đích**, nên đích được tìm đúng số lần mở rộng tối
đa vẫn trả `solved`. Đồng hồ trong bộ giải chỉ thực thi giới hạn, không xuất số đo hiệu năng.
Phần diễn giải hợp đồng đã phân biệt hai giới hạn để khớp mã giả.

Với hàm ước lượng nhất quán đang dùng, mỗi trạng thái được mở rộng nhiều nhất một lần hợp lệ.
Gọi `V,E` là số trạng thái/cạnh đạt được: UCS/A* dùng hàng đợi ưu tiên có thời gian
`O((V+E)log(V+E))`, bộ nhớ `O(V+E)` kể cả các bản ghi thay thế.

## 6. Bằng chứng kiểm thử

Kiểm thử đối chiếu ba màn có đáp án tính tay, phát lại đường đi, không có nghiệm, các giới hạn,
đồ thị có trọng số, bản ghi cũ và mở lại nút đã mở rộng dưới hàm ước lượng không đánh giá quá cao
nhưng không nhất quán. Chi phí được kiểm tra trên màn thật cho tiếp xúc ô dễ vỡ, lập phương đứng
yên và đích dịch chuyển. Giao diện dòng lệnh chỉ chạy UCS/A*.

Với từng màn trong mười màn chính thức, kiểm thử duyệt toàn bộ trạng thái đạt được, tạo đồ thị
cạnh ngược và tính chi phí còn lại độc lập từ các trạng thái đích. Giá trị đó được so với nghiệm
UCS/A* và hàm ước lượng trên mọi trạng thái có đường tới đích; mọi cạnh được kiểm tra tính nhất
quán. Tổng cộng **2.946 trạng thái**, gồm cầu và tách/hợp nhất. Kiểm tra trên ba màn nhỏ đáp ứng
trực tiếp #23; mười màn cung cấp thêm bằng chứng với các luật nâng cao.

Nguồn mười màn nằm trong [tài liệu trích dẫn màn chơi](../CREDITS.md). Việc dùng ba màn kiểm thử
sẵn có không thay thế nhiệm vụ xây dựng tập màn chung #21 của thành viên khác.

## 7. Phân công và hỗ trợ của trí tuệ nhân tạo

Phần bàn giao gồm hàm chi phí (#7), UCS (#22), A* (#23), vòng lặp chung (#18), tài liệu và kiểm
thử tương ứng. Nhiệm vụ #18 cần người phụ trách aFlyingSeal xem xét tích hợp. BFS/DFS, đo hiệu
năng, biểu đồ, giao diện đồ họa và bản ghi trình diễn thuộc các luồng công việc khác.

Đã sử dụng Codex để rà soát, hỗ trợ cài đặt, tạo kiểm thử và biên soạn. Yêu cầu chính là hoàn
thiện bốn nhiệm vụ trên và giới hạn phạm vi bàn giao. Kết quả được kiểm chứng bằng kiểm thử,
phép tính đối chiếu độc lập và phát lại lời giải. Người nộp cần hiểu và giải thích được thuật
toán, trọng số và các giới hạn khi vấn đáp.

## Tài liệu tham khảo

1. Đề bài CSC14003, Project 1: Bloxorz Solver, §3.2–3.6, PDF do học phần cung cấp.
2. [Hợp đồng nhóm](contracts.md), các nhiệm vụ #7, #18, #22 và #23.
3. [Nguồn màn chơi và dữ liệu đối chiếu](../CREDITS.md).
4. [Tài liệu Python về heapq](https://docs.python.org/3/library/heapq.html).
