# Fixtures tính tay (#21)

Ba màn trong `tests/fixtures/` là bộ kiểm chứng nhỏ nhất của nhóm. Đáp án của chúng
được tính tay, không lấy từ solver — `docs/contracts.md` § Expected quy định
`expected.optimal_cost` "is never produced by running a solver".

Mỗi màn được gắn `group: L1` và không có ô dễ vỡ, nên mỗi nước đi có chi phí 1 và
`optimal_cost` bằng đúng số bước. Bốn solver (`ucs`, `astar`, `bfs`, `dfs`) đều được
assert trên cả ba màn; danh sách lấy từ `FIXTURE_IDS` trong `tests/search_helpers.py`,
suy ra từ thư mục nên thêm màn mới là tự động có mặt ở cả bốn.

Ký hiệu: `U` đứng (1 ô), `H` nằm ngang (2 ô), `V` nằm dọc (2 ô).

## FIX-01 — Straight line (`RRRRRR`, 6 bước)

```
............
.SoooooooG.
............
```

`S = (1,1)`, `G = (1,10)`. Hành lang thẳng 9 ô.

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

## Kiểm chứng

`tests/test_fixtures.py` so `expected.optimal_cost` với chi phí tối ưu tính bằng
`remaining_costs` (duyệt toàn bộ đồ thị rồi chạy Dijkstra ngược từ đích). Oracle đó
độc lập với solver nhưng vẫn dùng `Board.successors`; phép đếm tay ở trên là kiểm tra
duy nhất không dựa vào engine.

Các test solver giữ phần "đạt được": `ucs`/`astar`/`bfs` khẳng định chi phí trả về
bằng `expected.optimal_cost`, `bfs` khẳng định thêm số bước; `dfs` chỉ khẳng định
đường đi phát lại tới đích và không ngắn hơn đáp án tối ưu, vì DFS không tối ưu.

```powershell
python -m pytest -q tests/test_fixtures.py tests/test_ucs.py tests/test_astar.py tests/test_bfs.py tests/test_dfs.py
```
