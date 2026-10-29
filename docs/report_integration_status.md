# Trạng thái ghép các mục chi phí, UCS và A* (#29)

Đã xử lý góp ý của aFlyingSeal tại
[review #62](https://github.com/zetomis-was-taken/Mixi-Blox/pull/62#pullrequestreview-5628743970)
trong các PR tương ứng:

- #62 thay bảng trọng số cũ trong `Report/main.tex` bằng `sections/action_cost`.
  Điều khoản chi phí #7 nêu đúng giá `{1, 2, 3}` và `c_min = 1`; tài liệu giới
  hạn tác động không đồng nhất ở hai màn fragile trong bộ dữ liệu hiện tại.
- #63 thay mục UCS cũ bằng `sections/ucs`, trong đó đã chèn `action_cost` một lần.
- #64 thay mục A* cũ bằng `sections/astar`, bỏ khẳng định hạng phạt hướng cộng 1
  luôn đúng và dùng chứng minh/giới hạn dịch chuyển khớp cài đặt. Phụ lục chèn
  công bố sinh mã và kiểm thử bằng Codex cho phần UCS/A*. Câu tự cài đặt có sẵn
  được thu hẹp để không bao gồm phần đóng góp có trợ giúp sinh mã này.

Như vậy, tại đầu nhánh #64, đường chèn nội dung là:

```text
Report/main.tex -> sections/ucs.tex -> sections/action_cost.tex
                -> sections/astar.tex
                -> sections/informed_search_ai_usage.tex
```

Các mục cũ được thay thế, không nối thêm một bộ trọng số hoặc heuristic thứ hai.
Những đoạn được phân công đã biên dịch trong bản xem trước riêng với các gói
cần thiết. Điều này xác nhận các đoạn đó, không xác nhận toàn bộ báo cáo nhóm.

## Trạng thái xử lý các mục cần nghiệm thu (#24, #29, PR #77)

- **Lỗi cú pháp dòng 103 (`Missing number`)**: Đã được xử lý dứt điểm; trang bìa đã cập nhật danh sách giảng viên chính thức (ThS. Bùi Duy Đăng, ThS. Nguyễn Ngọc Đức, ThS. Nguyễn Thanh Tình) và bổ sung đầy đủ MSSV cho 5 thành viên nhóm.
- **Số liệu đo đạc thực nghiệm & nhận xét**: Đã chạy đo lường toàn diện 10 màn chơi qua `python -m bloxorz.bench.run_all`. File `Report/tables/benchmark_results.tex` và 4 biểu đồ vector `Report/figures/benchmark_*.pdf` được cập nhật đồng bộ. Các nhận xét ước lượng cũ đã được thay thế bằng phân tích chi tiết đối chiếu khớp 100% với dữ liệu đo đạc thực tế.
- **Mô tả giao diện & Kết luận**: Đã cập nhật công nghệ GUI là Ursina (Panda3D) theo ADR-002 và bổ sung chương Kết luận (`Conclusion`) tổng kết đồ án.
- **Biên dịch PDF**: Báo cáo đã được kiểm tra biên dịch thành công ra file PDF trên Prism, layout các bảng biểu và hình ảnh hiển thị trọn vẹn, không còn lỗi biên dịch. Mục video YouTube sẽ được điền link sau khi hoàn tất khâu quay video demo.
