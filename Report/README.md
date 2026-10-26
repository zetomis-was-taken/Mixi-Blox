# Báo Cáo Đồ Án 1 - Bloxorz Solver (CSC14003)

Báo cáo LaTeX của nhóm. File nguồn chính là `report.tex`, toàn bộ nội dung nằm trong `sections/`.

## 1. Cấu trúc thư mục

```text
Report/
├── report.tex              # File nguồn chính
├── reportDoCS2025.cls      # Class của bộ môn
├── biblio.tex              # Tài liệu tham khảo
├── sections/               # Nội dung báo cáo
│   ├── credits.tex         # Bảng phân công & lộ trình thực hiện
│   ├── part1.tex           # Mô hình hóa bài toán
│   ├── part2.tex           # Cài đặt các thuật toán tìm kiếm
│   │   ├── bfs.tex, dfs.tex, ucs.tex, action_cost.tex, astar.tex
│   ├── part3.tex           # Thiết kế kịch bản thực nghiệm
│   ├── part4.tex           # Kết quả thực nghiệm & phân tích
│   ├── part5.tex           # Giao diện & video demo
│   ├── conclusion.tex      # Kết luận & phụ lục GenAI
│   └── informed_search_ai_usage.tex
├── tables/                 # Bảng sinh tự động bởi bench
├── figures/                # Biểu đồ sinh tự động bởi bench + figures/logos/
└── data/                   # Số liệu thô CSV/JSON sinh bởi bench
```

## 2. Biên dịch

Báo cáo được biên dịch **trực tuyến trên Prism**, không biên dịch cục bộ trong repo.

- File chính: `report.tex`
- Compiler: **XeLaTeX** (class dùng `fontspec` + `polyglossia` cho tiếng Việt)
- Không cần `--shell-escape`: báo cáo không dùng `minted` hay `lstlisting`

Sau khi tải PDF về, lưu thành `Report/Report.pdf` để `tools/package.py` và
`tools/verify_submission.py` tìm thấy (các file PDF/aux đã được `.gitignore` bỏ qua).

## 3. Cập nhật số liệu thực nghiệm

```bash
python -m bloxorz.bench.run_all
```

(hoặc `python Source/bloxorz/bench/run_all.py` từ thư mục gốc repo) sẽ ghi lại:

- `Report/data/benchmark_results.csv` và `Report/data/benchmark_results.json`
- `Report/tables/benchmark_results.tex` (bảng được `\input` từ `part4.tex`)
- `Report/figures/benchmark_*.pdf` (biểu đồ so sánh)

Sau đó biên dịch lại trên Prism để bảng và biểu đồ mới nhất xuất hiện trong báo cáo.
