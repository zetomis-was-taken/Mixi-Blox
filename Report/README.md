# Hướng Dẫn Sử Dụng Khung Báo Cáo LaTeX (CSC14003 - Bloxorz)

Thư mục này chứa toàn bộ mẫu báo cáo LaTeX chuẩn cho đồ án 1 môn **Cơ sở Trí tuệ nhân tạo (CSC14003)**.

## 1. Cấu trúc thư mục

```text
Report/
├── main.tex              # File nguồn LaTeX chính (đã phân mục theo đúng barem 30 điểm)
├── figures/              # Hình ảnh và biểu đồ thực nghiệm
│   ├── logo_khtn.png
│   └── (benchmark_*.pdf do bench harness sinh ra)
├── tables/               # Bảng kết quả thực nghiệm
│   └── benchmark_results.tex
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

Số liệu do bench harness sinh ra, không nhập tay:

```bash
PYTHONPATH=Source python -m bloxorz.bench.run_all
```

Lệnh này chỉ chạy được sau khi `bloxorz.solvers` (#18-#23) có đủ bốn thuật toán; trước đó nó dừng
ngay và không ghi số liệu giả. Khi chạy xong, harness ghi:

1. `Report/data/benchmark_results.csv` và `.json` — dữ liệu thô;
2. `Report/tables/benchmark_results.tex` — bảng LaTeX (`export_records_latex`);
3. `Report/figures/benchmark_*.pdf` — biểu đồ thời gian, bộ nhớ, số node và độ dài lời giải
   (`plot_benchmark_charts`).

Biên dịch lại `main.tex` là báo cáo tự cập nhật bảng và đồ thị mới nhất.
