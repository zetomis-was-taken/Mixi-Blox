# Fixtures tính tay (#21)

Năm màn trong `tests/fixtures/` là bộ kiểm chứng nhỏ nhất của nhóm. Đáp án của chúng
được tính tay, không lấy từ solver — `docs/contracts.md` § Expected quy định
`expected.optimal_cost` "is never produced by running a solver".

Mỗi màn được gắn `group: L1` và không có ô dễ vỡ, nên mỗi nước đi có chi phí 1 và
`optimal_cost` bằng đúng số bước. Bốn solver (`ucs`, `astar`, `bfs`, `dfs`) đều được
assert trên cả năm màn; danh sách lấy từ `FIXTURE_IDS` trong `tests/search_helpers.py`,
suy ra từ thư mục nên thêm màn mới là tự động có mặt ở cả bốn.

Ký hiệu: `U` đứng (1 ô), `H` nằm ngang (2 ô), `V` nằm dọc (2 ô).

## FIX-01 — Straight line (`RRRRRR`, 6 bước)

```
............
.SooooooooG.
............
```

`S = (1,1)`, `G = (1,10)`. Hành lang thẳng 10 ô, cột 1 đến 10.

| # | Trạng thái | Nước đi |
|---|---|---|
| 0 | `U(1,1)` | `R` |
| 1 | `H(1,2)-(1,3)` | `R` |
| 2 | `U(1,4)` | `R` |
| 3 | `H(1,5)-(1,6)` | `R` |
| 4 | `U(1,7)` | `R` |
| 5 | `H(1,8)-(1,9)` | `R` |
| 6 | `U(1,10)` = đích | — |

Đồ thị đạt được có đúng 7 trạng thái và chuỗi trên đi qua cả 7, nên nó là đường ngắn
nhất: một đường ngắn hơn sẽ phải bỏ qua ít nhất một trạng thái, mà mỗi nước đi chỉ
sang được trạng thái kề. Các nước đi ngược (`L`) quay lại trạng thái trước đó hoặc
rơi ra ngoài hành lang nên không mở nhánh mới.

## FIX-02 — East then south (`RRDD`, 4 bước)

```
.......
.Sooo..
....o..
....o..
....G..
.......
```

`S = (1,1)`, `G = (4,4)`. Đi ngang 3 ô rồi xuống 3 ô.

| # | Trạng thái | Nước đi |
|---|---|---|
| 0 | `U(1,1)` | `R` |
| 1 | `H(1,2)-(1,3)` | `R` |
| 2 | `U(1,4)` | `D` |
| 3 | `V(2,4)-(3,4)` | `D` |
| 4 | `U(4,4)` = đích | — |

Năm trạng thái, chuỗi đi qua cả năm. Không có nhánh: từ `U(1,4)` chỉ `D` dẫn tới
trạng thái mới, còn `L` quay lại `H(1,2)-(1,3)`.

## FIX-03 — South then east (`DDRR`, 4 bước)

```
......
.S....
.o....
.o....
.oooG.
......
```

`S = (1,1)`, `G = (4,4)`. Ảnh gương của FIX-02: xuống 3 ô rồi sang 3 ô.

| # | Trạng thái | Nước đi |
|---|---|---|
| 0 | `U(1,1)` | `D` |
| 1 | `V(2,1)-(3,1)` | `D` |
| 2 | `U(4,1)` | `R` |
| 3 | `H(4,2)-(4,3)` | `R` |
| 4 | `U(4,4)` = đích | — |

Cùng lập luận: năm trạng thái, không nhánh.

## FIX-04 — Dead end above (`RRDD`, 4 bước)

```
....o....
....o....
....o....
....o....
.Sooo....
....o....
....o....
....G....
.........
```

`S = (4,1)`, `G = (7,4)`. Ngã ba ở `(4,4)`: một nhánh lên là ngõ cụt, một nhánh xuống tới đích.

| # | Trạng thái | Nước đi |
|---|---|---|
| 0 | `U(4,1)` | `R` |
| 1 | `H(4,2)-(4,3)` | `R` |
| 2 | `U(4,4)` | `D` |
| 3 | `V(5,4)-(6,4)` | `D` |
| 4 | `U(7,4)` = đích | — |

Nhánh cụt: từ `U(4,4)` đi `U` được `V(2,4)-(3,4)`, đi `U` nữa được `U(1,4)`, rồi hết
đường vì nước tiếp theo rơi ra ngoài bàn. Vào rồi ra mất 4 nước, nên đường vòng qua
đó dài 8 chứ không phải 4 — đây là màn đầu tiên buộc solver phải bỏ một nhánh.

Tính tay: từ `S` chỉ có `R` (ba hướng còn lại rơi ra ngoài); từ `H(4,2)-(4,3)` chỉ `R`
mở trạng thái mới (`L` quay lại `U(4,1)`); nên hai nước đầu bị buộc, và từ `U(4,4)` chỉ
`D` mới tiến được. Vậy 4 là nhỏ nhất. Đồ thị có 7 trạng thái và 6 cạnh — vẫn là cây,
nên mọi đường đơn đều dài 4.

## FIX-05 — Slide, then stand (`DRRU`, 4 bước)

```
.....
.SoG.
.ooo.
.ooo.
.....
```

Phòng 3×3, `S = (1,1)`, `G = (1,3)`. Đích nằm trên cùng hàng, cách chỗ xuất phát hai
cột, nhưng block không "bước" thẳng tới được: nó lăn theo hướng hiện tại, và khi đang nằm
thì lăn ngang chỉ trượt sang bên mà vẫn giữ tư thế nằm. Muốn đứng trên ô đích phải đi vòng.

| # | Trạng thái | Nước đi |
|---|---|---|
| 0 | `U(1,1)` | `D` |
| 1 | `V(2,1)-(3,1)` | `R` |
| 2 | `V(2,2)-(3,2)` | `R` |
| 3 | `V(2,3)-(3,3)` | `U` |
| 4 | `U(1,3)` = đích | — |

Block nằm dọc trượt ngang hai lần rồi dựng lên ở đích. Đếm tay theo tầng, mỗi tầng chỉ
liệt kê trạng thái mới:

| Tầng | Trạng thái |
|---|---|
| 1 | `(1,2)-(1,3)`, `(2,1)-(3,1)` |
| 2 | `(2,2)-(2,3)`, `(2,2)-(3,2)` |
| 3 | `(1,2)`, `(2,1)`, `(2,3)-(3,3)`, `(3,2)-(3,3)` |
| 4 | `(1,3)` = đích, `(3,1)` |

Tầng 1 và 2 toàn block nằm hai ô nên không thể là đích. Tiền thân duy nhất của đích là
`H(1,1)-(1,2)` và `V(2,3)-(3,3)`; cái sau chỉ xuất hiện ở tầng 3, cái trước không có ở
tầng 1–3. Vậy sớm nhất là 4, và `DRRU` đạt đúng 4.

Đây là màn **duy nhất** trong bộ có đồ thị trạng thái chứa chu trình: 20 trạng thái, 20
cạnh. Nó có hai đường đơn tới đích, dài **4** và **12**. Nhờ vậy `expected.optimal_cost`
lần đầu tiên có thể sai được: một solver trả về đường 12 vẫn hợp lệ nhưng vẫn bị bắt.

## Kiểm chứng

`tests/test_fixtures.py` so `expected.optimal_cost` với chi phí tối ưu tính bằng
`remaining_costs` (duyệt toàn bộ đồ thị rồi chạy Dijkstra ngược từ đích). Oracle đó
độc lập với solver nhưng vẫn dùng `Board.successors`; phép đếm tay ở trên là kiểm tra
duy nhất không dựa vào engine.

`tests/test_fixtures.py` cũng giữ một guard: ít nhất một màn phải có đồ thị trạng thái
chứa chu trình (`|E| ≥ |V|`). Không có guard đó, ai đấy có thể thay các màn có nhánh
bằng đường thẳng, `optimal_cost` sẽ không còn phân biệt được gì, mà bộ test vẫn xanh.

Các test solver giữ phần "đạt được": `ucs`/`astar`/`bfs` khẳng định chi phí trả về
bằng `expected.optimal_cost`, `bfs` khẳng định thêm số bước; `dfs` chỉ khẳng định
đường đi phát lại tới đích và không ngắn hơn đáp án tối ưu, vì DFS không tối ưu.

```powershell
python -m pytest -q tests/test_fixtures.py tests/test_ucs.py tests/test_astar.py tests/test_bfs.py tests/test_dfs.py
```
