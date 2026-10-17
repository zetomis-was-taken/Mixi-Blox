# Thư Viện Benchmark Cho Thuật Toán Tìm Kiếm Bloxorz

Thư viện hỗ trợ đo đạc chính xác 4 chỉ số hiệu năng theo quy định của đề bài:
1. **Search Time**: Thời gian thực thi thuật toán (đo bằng `time.perf_counter`, xuất ra mili-giây và giây).
2. **Peak Memory**: Bộ nhớ RAM tối đa chiếm dụng (sử dụng `tracemalloc`, xuất ra KB và MB).
3. **Expanded Nodes**: Tổng số nút đã mở rộng khỏi Frontier.
4. **Solution Length**: Số bước đi (hành động lăn) trong đường đi tìm được.

---

## 1. Cấu trúc thư viện

```text
benchmark/
├── __init__.py
├── metrics.py        # BenchmarkResult dataclass & hàm benchmark_search
├── runner.py         # BenchmarkRunner quản lý chạy hàng loạt, xuất CSV, JSON, Markdown, LaTeX
├── plotter.py        # plot_benchmark_results vẽ 4 biểu đồ so sánh (PNG & vector PDF)
└── README.md
```

---

## 2. Cách sử dụng

### Bước 1: Viết hàm giải (Solver)
Mỗi hàm giải chỉ cần nhận vào dữ liệu màn chơi và trả về:
* Tuple: `(solution_path, expanded_nodes)` (Ví dụ: `(['U', 'R', 'D'], 42)`).

```python
def solve_bfs(level_data):
    # Logic BFS của bạn...
    return path, expanded_nodes
```

### Bước 2: Khởi tạo Runner và đăng ký thuật toán & màn chơi

```python
from benchmark import BenchmarkRunner, plot_benchmark_results

runner = BenchmarkRunner()

# 1. Đăng ký các thuật toán
runner.register_algorithm("BFS", solve_bfs)
runner.register_algorithm("DFS", solve_dfs)
runner.register_algorithm("UCS", solve_ucs)
runner.register_algorithm("A*", solve_astar)

# 2. Đăng ký các màn chơi kiểm thử
runner.register_level("Level 01", level_1_data)
runner.register_level("Level 02", level_2_data)

# 3. Chạy toàn bộ thực nghiệm
results = runner.run_all()

# 4. Xuất dữ liệu
runner.export_csv("benchmark_results.csv")
runner.export_latex_table("report/tables/benchmark_table.tex")

# 5. Tự động vẽ và lưu biểu đồ vào thư mục báo cáo
plot_benchmark_results(results, output_dir="report/figures")
```
