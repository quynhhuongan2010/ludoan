from typing import Literal

# Bac truy cap dung chung cho posts / directives / documents
Classification = Literal["cong_khai", "noi_bo", "mat"]

CLASSIFICATION_LABELS = {
    "cong_khai": "Công khai",
    "noi_bo": "Nội bộ",
    "mat": "Mật",
}
