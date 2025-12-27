# Sửa Lỗi t() Function Key Parameter Conflict - 2025-01-27

## Vấn Đề

Lỗi khi gọi hàm `t()` với tham số `key`:
```
t() got multiple values for argument 'key'
```

Lỗi xảy ra khi gọi:
```python
t("view_info.device_id_details.vscode_id_item", key=key, value=value)
```

**Nguyên nhân:**
- Hàm `t()` có tham số đầu tiên tên là `key` (translation key)
- Khi gọi với `key=key` trong kwargs, Python thấy xung đột:
  - Tham số vị trí đầu tiên `"view_info.device_id_details.vscode_id_item"` → gán cho `key`
  - Keyword argument `key=key` → cũng cố gán cho `key` → **CONFLICT!**

## Giải Pháp

Đổi tên tham số từ `key` sang `translation_key` trong:
1. `Translator.get()` method
2. `Translator.__call__()` method  
3. `t()` helper function

### Files Đã Sửa

**utils/i18n.py:**
- Đổi `def get(self, key: str, ...)` → `def get(self, translation_key: str, ...)`
- Đổi `def __call__(self, key: str, ...)` → `def __call__(self, translation_key: str, ...)`
- Đổi `def t(key: str, ...)` → `def t(translation_key: str, ...)`
- Cập nhật tất cả references đến `key` trong method body thành `translation_key`

## Kết Quả

✅ Giờ đây có thể gọi `t("...", key=key, value=value)` mà không bị conflict
✅ `key=key` trong kwargs được dùng để format translation string `"{key}: {value}"`
✅ Tất cả các calls hiện tại vẫn hoạt động (vì dùng positional argument)
✅ Syntax check: Passed
✅ Linter: No errors

## Kiểm Tra

- ✅ Syntax check: Passed
- ✅ Linter: No errors  
- ✅ Code review: No critical issues
- ✅ Backward compatibility: Maintained (tất cả calls dùng positional args vẫn work)

## Ghi Chú

- Translation string `"vscode_id_item": "         • {key}: {value}"` cần `key` và `value` trong kwargs
- Giờ đây có thể truyền `key=key` mà không conflict với function parameter
- Tất cả các calls khác vẫn hoạt động bình thường vì dùng positional arguments

