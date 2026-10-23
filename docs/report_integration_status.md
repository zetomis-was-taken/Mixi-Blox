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

## Lỗi có sẵn cần người phụ trách báo cáo xử lý

Lần kiểm tra toàn bộ `Report/main.tex` dừng ở dòng 103, trước các mục thuật toán:

```text
Missing number, treated as zero.
l.103 [Tên Giảng Viên Thực Hành]
```

Dòng này đứng ngay sau `\\`, khiến dấu `[` bị hiểu là tham số giãn dòng cần
một độ dài. Lỗi tồn tại nguyên trạng ở main `af67ba4`, không phát sinh từ việc
ghép các mục UCS/A*. Nội dung/trang bìa thuộc phần phối hợp #29 nên được giữ
nguyên. Người phụ trách có thể bao placeholder bằng ngoặc nhọn và biên dịch lại
để tìm lỗi tiếp theo; chưa khẳng định đó là lỗi duy nhất của mẫu.

Các mục còn lại cũng cần người sở hữu nghiệm thu trước khi xuất bản nộp: phần
mô hình hóa vẫn mô tả SwitchControl/khóa ba thành phần; phần nhận xét còn chứa
con số 40–70% chưa có phép đo và câu A* tối ưu số bước; phần GUI/video còn là
mẫu. Những đoạn đó nằm ngoài các mục được phân công, chưa được thay đổi ở đây.

Các PR này chỉ hoàn thành nội dung chi phí/UCS/A* và công bố AI tương ứng.
Không đóng thay toàn bộ #29, không tạo số đo hiệu năng, và không xác nhận PDF
cuối của toàn nhóm đã sẵn sàng nộp.
