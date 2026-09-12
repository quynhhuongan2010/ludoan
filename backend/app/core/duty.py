"""Tien ich dung chung cho module Lich truc - Kip truc (bang truc tuan theo don vi)."""

from datetime import date, timedelta

# Trang thai phe duyet bang truc tuan (giong luong duyet posts).
DRAFT = "nhap"
PENDING = "cho_duyet"
APPROVED = "da_duyet"
RETURNED = "tra_lai"

_WEEKDAY_LABELS = (
    "Thứ Hai",
    "Thứ Ba",
    "Thứ Tư",
    "Thứ Năm",
    "Thứ Sáu",
    "Thứ Bảy",
    "Chủ Nhật",
)


def monday_of(day: date) -> date:
    """Chuan hoa ve Thu Hai (ISO) cua tuan chua `day`."""
    return day - timedelta(days=day.weekday())


def sunday_of(day: date) -> date:
    return monday_of(day) + timedelta(days=6)


def week_days(monday: date) -> list[date]:
    return [monday + timedelta(days=i) for i in range(7)]


def weekday_label(day: date) -> str:
    return _WEEKDAY_LABELS[day.weekday()]


def week_label(monday: date) -> str:
    iso = monday.isocalendar()
    return f"Tuần {iso.week:02d}/{iso.year}"
