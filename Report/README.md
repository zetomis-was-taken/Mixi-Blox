# Hướng Dẫn Sử Dụng Khung Báo Cáo LaTeX (CSC14003 - Bloxorz)

Thư mục này chứa toàn bộ mẫu báo cáo LaTeX chuẩn cho đồ án 1 môn **Cơ sở Trí tuệ nhân tạo (CSC14003)**.

## 1. Cấu trúc thư mục

```text
report/
├── main.tex              # File nguồn LaTeX chính (đã phân mục theo đúng barem 30 điểm)
├── figures/              # Chứa toàn bộ hình ảnh và biểu đồ thực nghiệm
│   ├── logo_khtn.png
│   ├── benchmark_search_time.pdf
│   ├── benchmark_peak_memory.pdf
│   ├── benchmark_expanded_nodes.pdf
│   └── benchmark_solution_length.pdf
└── README.md             # Tài liệu hướng dẫn này
```

## 2. Cách biên dịch file LaTeX

### Cách 1: Sử dụng Overleaf (Khuyên dùng)
1. Nén toàn bộ thư mục `report/` thành file `.zip`.
2. Truy cập [Overleaf](https://www.overleaf.com), bấm **New Project** -> **Upload Project**.
3. Chọn file `.zip` vừa nén để tải lên.
4. Chọn compiler là **pdfLaTeX** hoặc **XeLaTeX** và bấm **Recompile**.

### Cách 2: Biên dịch cục bộ (Local máy tính)
Nếu máy bạn đã cài MiKTeX hoặc TeX Live:
```bash
pdflatex main.tex
```

## 3. Cách cập nhật số liệu thực nghiệm tự động

Khi nhóm chạy thử nghiệm các thuật toán thông qua thư viện `benchmark`, chỉ cần:
1. Chạy hàm `runner.to_latex_table()` hoặc `runner.export_latex_table("report/tables/benchmark_table.tex")` để xuất bảng mã LaTeX.
2. Chạy `plot_benchmark_results(results, output_dir="report/figures")` để tự động làm mới các file đồ thị vector PDF trong thư mục `report/figures/`.
3. Biên dịch lại file LaTeX là báo cáo sẽ tự động cập nhật bảng biểu và đồ thị mới nhất!
