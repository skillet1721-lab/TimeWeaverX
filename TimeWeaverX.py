import os
import sys
import sqlite3
import winreg
import ctypes
import hashlib
import random
import tempfile
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from openai import OpenAI
from PyQt5.QtWidgets import QApplication
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque
import csv
import json

# --- Safe imports ---
PSUTIL_OK = True
WIN32_OK = True
OPENAI_OK = True
REQUESTS_OK = True

try:
    import psutil
except Exception:
    PSUTIL_OK = False
    psutil = None

try:
    import win32gui
    import win32process
    import win32api
    import win32con
except Exception:
    WIN32_OK = False
    win32gui = None
    win32process = None
    win32api = None
    win32con = None

try:
    from openai import OpenAI
except Exception:
    OPENAI_OK = False
    OpenAI = None

try:
    import requests
except Exception:
    REQUESTS_OK = False
    requests = None

from PyQt5.QtCore import (
    Qt, QTimer, QSettings, QDate,
    QThread, pyqtSignal,
    QSize, QRect, QPoint
)
from PyQt5.QtGui import (
    QBrush, QPen, QLinearGradient,
    QColor, QFont, QPainter,
    QPixmap, QIcon, QKeySequence
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame, QListWidget, QListWidgetItem,
    QLineEdit, QFormLayout, QSpinBox, QCheckBox, QMessageBox, QToolBar, QAction,
    QStatusBar, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QSystemTrayIcon, QMenu, QProgressBar, QScrollArea, QGridLayout, QDialog, 
    QDoubleSpinBox, QGroupBox, QSlider, QTabWidget, QTextEdit, QSizePolicy
)
import pyqtgraph as pg

CATEGORY_COLORS = {
    "Work": QColor("#4CAF50"),          # зелений
    "Study": QColor("#2196F3"),         # синій
    "Entertainment": QColor("#F44336"), # червоний
    "Social": QColor("#FF9800"),        # оранжевий
    "Neutral": QColor("#000000"),       # сірий
    "Other": QColor("#607D8B"),         # синьо-сірий
}


# =========================
# Constants
# =========================
DB_NAME = "timeweaver.db"
APP_VERSION = "1.0"

# Window size presets
WINDOW_PRESETS = {
    "compact": (900, 600),
    "standard": (1100, 700),
    "large": (1400, 900),
    "extra_large": (1600, 1000),
    "fullscreen": None,
}

# =========================
# =========================
TRANSLATIONS = {
    "uk": {
        "lang_name": "Українська",
        "app_title": "TimeWeaver Pro",
        "dashboard": "Головна",
        "activity": "Активність",
        "system": "Система",
        "reports": "Звіти",
        "insights": "Поради",
        "settings": "Налаштування",
        "start": "Запустити",
        "stop": "Зупинити",
        "status_ready": "Готово",
        "status_monitoring": "Моніторинг активний",
        "status_stopped": "Моніторинг зупинено",
        "today": "Сьогодні",
        "yesterday": "Вчора",
        "days_ago_2": "2 дні тому",
        "week": "Тиждень",
        "month": "Місяць",
        "total_time": "Загальний час",
        "top_app": "Топ програма",
        "distractions": "Відволікання",
        "score": "Оцінка",
        "current_activity": "Поточна активність",
        "generate_advice": "Згенерувати пораду",
        "last_7_days": "Останні 7 днів",
        "last_3_days": "Останні 3 дні",
        "last_30_days": "Останні 30 днів",
        "export_csv": "Експорт CSV",
        "category": "Категорія",
        "time": "Час",
        "percent": "Відсоток",
        "app": "Програма",
        "title": "Заголовок",
        "duration": "Тривалість",
        "cpu": "Процесор",
        "ram": "Пам'ять",
        "disk": "Диск",
        "network": "Мережа",
        "process": "Процес",
        "pid": "PID",
        "status": "Статус",
        "usage_history": "Історія (останні 60 сек)",
        "top_processes": "Топ процеси",
        "general": "Загальні",
        "appearance": "Вигляд",
        "ai_settings": "ШІ",
        "data": "Дані",
        "username": "Ім'я користувача",
        "poll_interval": "Інтервал опитування (мс)",
        "idle_timeout": "Таймаут простою (сек)",
        "break_reminder": "Нагадування про перерву (хв)",
        "distraction_threshold": "Поріг відволікань (%)",
        "autostart_monitoring": "Автозапуск моніторингу",
        "autostart_windows": "Автозапуск з Windows",
        "theme": "Тема",
        "dark_theme": "Темна",
        "light_theme": "Світла",
        "language": "Мова",
        "window_size": "Розмір вікна",
        "compact": "Компактний (900x600)",
        "standard": "Стандартний (1100x700)",
        "large": "Великий (1400x900)",
        "extra_large": "Дуже великий (1600x1000)",
        "fullscreen": "На весь екран",
        "remember_window": "Запам'ятати розмір/позицію вікна",
        "minimize_to_tray": "Згортати в трей замість закриття",
        "tray_notifications": "Показувати сповіщення в треї",
        "api_key": "API ключ OpenAI",
        "api_key_hint": "sk-... (опціонально, для покращених порад)",
        "api_key_info": "API ключ опціональний. Без нього поради генеруються локальними алгоритмами.",
        "test_api": "Тестувати API",
        "export_all": "Експортувати всі дані",
        "clear_all": "Очистити всі дані",
        "save": "Зберегти",
        "reset": "Скинути",
        "about": "Про програму",
        "about_text": "Трекер активності та аналізатор продуктивності для Windows.",
        "no_data": "Недостатньо даних для аналізу",
        "generating": "Генерація порад...",
        "error": "Помилка",
        "success": "Успіх",
        "warning": "Попередження",
        "confirm_clear": "Це видалить ВСІ дані активності!\n\nПродовжити?",
        "confirm_reset": "Скинути всі налаштування до значень за замовчуванням?",
        "settings_saved": "Налаштування збережено",
        "settings_reset": "Налаштування скинуто",
        "data_exported": "Дані експортовано до",
        "no_export_data": "Немає даних для експорту",
        "api_valid": "API ключ дійсний!",
        "api_invalid": "Недійсний API ключ",
        "api_rate_limit": "Перевищено ліміт запитів. Використовую локальну генерацію.",
        "enter_api_first": "Спочатку введіть API ключ",
        "openai_not_installed": "Бібліотека OpenAI не встановлена. Виконайте: pip install openai",
        "testing": "Тестування...",
        "break_reminder_msg": "Ви працюєте вже {0} хвилин. Зробіть перерву на 5-10 хвилин.",
        "minimized_to_tray": "Програма згорнута в трей. Двічі клацніть для відновлення.",
        "monitoring_started": "Моніторинг запущено",
        "monitoring_stopped": "Моніторинг зупинено",
        "work": "Робота",
        "study": "Навчання", 
        "entertainment": "Розваги",
        "social": "Соцмережі",
        "neutral": "Нейтральне",
        "other": "Інше",
        "previous_advice": "Попередні поради",
        "period": "Період",
        "created": "Створено",
        "preview": "Перегляд",
        "advice_placeholder": "Натисніть 'Згенерувати пораду' для отримання персоналізованих рекомендацій на основі ваших даних активності...",
        "by_category": "За категоріями",
        "events": "Подій",
        "total": "Загалом",
        "unproductive": "Непродуктивний час",
        "productive": "Продуктивний час",
        "start_col": "Початок",
        "end_col": "Кінець",
    },
    "en": {
        "lang_name": "English",
        "app_title": "TimeWeaver Pro",
        "dashboard": "Dashboard",
        "activity": "Activity",
        "system": "System",
        "reports": "Reports",
        "insights": "Insights",
        "settings": "Settings",
        "start": "Start",
        "stop": "Stop",
        "status_ready": "Ready",
        "status_monitoring": "Monitoring active",
        "status_stopped": "Monitoring stopped",
        "today": "Today",
        "yesterday": "Yesterday",
        "days_ago_2": "2 days ago",
        "week": "Week",
        "month": "Month",
        "total_time": "Total time",
        "top_app": "Top app",
        "distractions": "Distractions",
        "score": "Score",
        "current_activity": "Current activity",
        "generate_advice": "Generate advice",
        "last_7_days": "Last 7 days",
        "last_3_days": "Last 3 days",
        "last_30_days": "Last 30 days",
        "export_csv": "Export CSV",
        "category": "Category",
        "time": "Time",
        "percent": "Percent",
        "app": "App",
        "title": "Title",
        "duration": "Duration",
        "cpu": "CPU",
        "ram": "RAM",
        "disk": "Disk",
        "network": "Network",
        "process": "Process",
        "pid": "PID",
        "status": "Status",
        "usage_history": "Usage history (last 60 sec)",
        "top_processes": "Top processes",
        "general": "General",
        "appearance": "Appearance",
        "ai_settings": "AI",
        "data": "Data",
        "username": "Username",
        "poll_interval": "Poll interval (ms)",
        "idle_timeout": "Idle timeout (sec)",
        "break_reminder": "Break reminder (min)",
        "distraction_threshold": "Distraction threshold (%)",
        "autostart_monitoring": "Auto-start monitoring",
        "autostart_windows": "Auto-start with Windows",
        "theme": "Theme",
        "dark_theme": "Dark",
        "light_theme": "Light",
        "language": "Language",
        "window_size": "Window size",
        "compact": "Compact (900x600)",
        "standard": "Standard (1100x700)",
        "large": "Large (1400x900)",
        "extra_large": "Extra Large (1600x1000)",
        "fullscreen": "Fullscreen",
        "remember_window": "Remember window size/position",
        "minimize_to_tray": "Minimize to tray instead of close",
        "tray_notifications": "Show tray notifications",
        "api_key": "OpenAI API Key",
        "api_key_hint": "sk-... (optional, for enhanced advice)",
        "api_key_info": "API key is optional. Without it, advice is generated by local algorithms.",
        "test_api": "Test API",
        "export_all": "Export all data",
        "clear_all": "Clear all data",
        "save": "Save",
        "reset": "Reset",
        "about": "About",
        "about_text": "Activity tracker and productivity analyzer for Windows.",
        "no_data": "Not enough data for analysis",
        "generating": "Generating advice...",
        "error": "Error",
        "success": "Success",
        "warning": "Warning",
        "confirm_clear": "This will delete ALL activity data!\n\nContinue?",
        "confirm_reset": "Reset all settings to defaults?",
        "settings_saved": "Settings saved",
        "settings_reset": "Settings reset",
        "data_exported": "Data exported to",
        "no_export_data": "No data to export",
        "api_valid": "API key is valid!",
        "api_invalid": "Invalid API key",
        "api_rate_limit": "Rate limit exceeded. Using local generation.",
        "enter_api_first": "Enter API key first",
        "openai_not_installed": "OpenAI library not installed. Run: pip install openai",
        "testing": "Testing...",
        "break_reminder_msg": "You've been working for {0} minutes. Take a 5-10 min break.",
        "minimized_to_tray": "App minimized to tray. Double-click to restore.",
        "monitoring_started": "Monitoring started",
        "monitoring_stopped": "Monitoring stopped",
        "work": "Work",
        "study": "Study",
        "entertainment": "Entertainment",
        "social": "Social",
        "neutral": "Neutral",
        "other": "Other",
        "previous_advice": "Previous advice",
        "period": "Period",
        "created": "Created",
        "preview": "Preview",
        "advice_placeholder": "Click 'Generate advice' for personalized recommendations based on your activity data...",
        "by_category": "By category",
        "events": "Events",
        "total": "Total",
        "unproductive": "Unproductive",
        "productive": "Productive",
        "start_col": "Start",
        "end_col": "End",
    },
    "ru": {
        "lang_name": "Русский",
        "app_title": "TimeWeaver Pro",
        "dashboard": "Главная",
        "activity": "Активность",
        "system": "Система",
        "reports": "Отчёты",
        "insights": "Советы",
        "settings": "Настройки",
        "start": "Запустить",
        "stop": "Остановить",
        "status_ready": "Готово",
        "status_monitoring": "Мониторинг активен",
        "status_stopped": "Мониторинг остановлен",
        "today": "Сегодня",
        "yesterday": "Вчера",
        "days_ago_2": "2 дня назад",
        "week": "Неделя",
        "month": "Месяц",
        "total_time": "Общее время",
        "top_app": "Топ программа",
        "distractions": "Отвлечения",
        "score": "Оценка",
        "current_activity": "Текущая активность",
        "generate_advice": "Сгенерировать совет",
        "last_7_days": "Последние 7 дней",
        "last_3_days": "Последние 3 дня",
        "last_30_days": "Последние 30 дней",
        "export_csv": "Экспорт CSV",
        "category": "Категория",
        "time": "Время",
        "percent": "Процент",
        "app": "Программа",
        "title": "Заголовок",
        "duration": "Длительность",
        "cpu": "Процессор",
        "ram": "Память",
        "disk": "Диск",
        "network": "Сеть",
        "process": "Процесс",
        "pid": "PID",
        "status": "Статус",
        "usage_history": "История (последние 60 сек)",
        "top_processes": "Топ процессы",
        "general": "Общие",
        "appearance": "Внешний вид",
        "ai_settings": "ИИ",
        "data": "Данные",
        "username": "Имя пользователя",
        "poll_interval": "Интервал опроса (мс)",
        "idle_timeout": "Таймаут простоя (сек)",
        "break_reminder": "Напоминание о перерыве (мин)",
        "distraction_threshold": "Порог отвлечений (%)",
        "autostart_monitoring": "Автозапуск мониторинга",
        "autostart_windows": "Автозапуск с Windows",
        "theme": "Тема",
        "dark_theme": "Тёмная",
        "light_theme": "Светлая",
        "language": "Язык",
        "window_size": "Размер окна",
        "compact": "Компактный (900x600)",
        "standard": "Стандартный (1100x700)",
        "large": "Большой (1400x900)",
        "extra_large": "Очень большой (1600x1000)",
        "fullscreen": "Во весь экран",
        "remember_window": "Запомнить размер/позицию окна",
        "minimize_to_tray": "Сворачивать в трей вместо закрытия",
        "tray_notifications": "Показывать уведомления в трее",
        "api_key": "API ключ OpenAI",
        "api_key_hint": "sk-... (опционально, для улучшенных советов)",
        "api_key_info": "API ключ опционален. Без него советы генерируются локальными алгоритмами.",
        "test_api": "Тестировать API",
        "export_all": "Экспортировать все данные",
        "clear_all": "Очистить все данные",
        "save": "Сохранить",
        "reset": "Сбросить",
        "about": "О программе",
        "about_text": "Трекер активности и анализатор продуктивности для Windows.",
        "no_data": "Недостаточно данных для анализа",
        "generating": "Генерация советов...",
        "error": "Ошибка",
        "success": "Успех",
        "warning": "Предупреждение",
        "confirm_clear": "Это удалит ВСЕ данные активности!\n\nПродолжить?",
        "confirm_reset": "Сбросить все настройки к значениям по умолчанию?",
        "settings_saved": "Настройки сохранены",
        "settings_reset": "Настройки сброшены",
        "data_exported": "Данные экспортированы в",
        "no_export_data": "Нет данных для экспорта",
        "api_valid": "API ключ действителен!",
        "api_invalid": "Недействительный API ключ",
        "api_rate_limit": "Превышен лимит запросов. Использую локальную генерацию.",
        "enter_api_first": "Сначала введите API ключ",
        "openai_not_installed": "Библиотека OpenAI не установлена. Выполните: pip install openai",
        "testing": "Тестирование...",
        "break_reminder_msg": "Вы работаете уже {0} минут. Сделайте перерыв на 5-10 минут.",
        "minimized_to_tray": "Программа свёрнута в трей. Дважды щёлкните для восстановления.",
        "monitoring_started": "Мониторинг запущен",
        "monitoring_stopped": "Мониторинг остановлен",
        "work": "Работа",
        "study": "Учёба",
        "entertainment": "Развлечения",
        "social": "Соцсети",
        "neutral": "Нейтральное",
        "other": "Другое",
        "previous_advice": "Предыдущие советы",
        "period": "Период",
        "created": "Создано",
        "preview": "Просмотр",
        "advice_placeholder": "Нажмите 'Сгенерировать совет' для получения персонализированных рекомендаций...",
        "by_category": "По категориям",
        "events": "Событий",
        "total": "Всего",
        "unproductive": "Непродуктивное",
        "productive": "Продуктивное",
        "start_col": "Начало",
        "end_col": "Конец",
    },
    "pl": {
        "lang_name": "Polski",
        "app_title": "TimeWeaver Pro",
        "dashboard": "Panel",
        "activity": "Aktywnosc",
        "system": "System",
        "reports": "Raporty",
        "insights": "Porady",
        "settings": "Ustawienia",
        "start": "Start",
        "stop": "Stop",
        "status_ready": "Gotowy",
        "status_monitoring": "Monitorowanie aktywne",
        "status_stopped": "Monitorowanie zatrzymane",
        "today": "Dzisiaj",
        "yesterday": "Wczoraj",
        "days_ago_2": "2 dni temu",
        "week": "Tydzien",
        "month": "Miesiac",
        "total_time": "Calkowity czas",
        "top_app": "Top aplikacja",
        "distractions": "Rozproszenia",
        "score": "Wynik",
        "current_activity": "Biezaca aktywnosc",
        "generate_advice": "Generuj porade",
        "last_7_days": "Ostatnie 7 dni",
        "last_3_days": "Ostatnie 3 dni",
        "last_30_days": "Ostatnie 30 dni",
        "export_csv": "Eksport CSV",
        "category": "Kategoria",
        "time": "Czas",
        "percent": "Procent",
        "app": "Aplikacja",
        "title": "Tytul",
        "duration": "Czas trwania",
        "cpu": "CPU",
        "ram": "RAM",
        "disk": "Dysk",
        "network": "Siec",
        "process": "Proces",
        "pid": "PID",
        "status": "Status",
        "usage_history": "Historia (ostatnie 60 sek)",
        "top_processes": "Top procesy",
        "general": "Ogolne",
        "appearance": "Wyglad",
        "ai_settings": "AI",
        "data": "Dane",
        "username": "Nazwa uzytkownika",
        "poll_interval": "Interwal odpytywania (ms)",
        "idle_timeout": "Timeout bezczynnosci (sek)",
        "break_reminder": "Przypomnienie o przerwie (min)",
        "distraction_threshold": "Prog rozproszen (%)",
        "autostart_monitoring": "Autostart monitorowania",
        "autostart_windows": "Autostart z Windows",
        "theme": "Motyw",
        "dark_theme": "Ciemny",
        "light_theme": "Jasny",
        "language": "Jezyk",
        "window_size": "Rozmiar okna",
        "compact": "Kompaktowy (900x600)",
        "standard": "Standardowy (1100x700)",
        "large": "Duzy (1400x900)",
        "extra_large": "Bardzo duzy (1600x1000)",
        "fullscreen": "Pelny ekran",
        "remember_window": "Zapamietaj rozmiar/pozycje okna",
        "minimize_to_tray": "Minimalizuj do zasobnika zamiast zamykac",
        "tray_notifications": "Pokazuj powiadomienia w zasobniku",
        "api_key": "Klucz API OpenAI",
        "api_key_hint": "sk-... (opcjonalnie)",
        "api_key_info": "Klucz API jest opcjonalny.",
        "test_api": "Testuj API",
        "export_all": "Eksportuj wszystkie dane",
        "clear_all": "Wyczysc wszystkie dane",
        "save": "Zapisz",
        "reset": "Resetuj",
        "about": "O programie",
        "about_text": "Tracker aktywnosci i analizator produktywnosci dla Windows.",
        "no_data": "Za malo danych do analizy",
        "generating": "Generowanie porad...",
        "error": "Blad",
        "success": "Sukces",
        "warning": "Ostrzezenie",
        "confirm_clear": "To usunie WSZYSTKIE dane!\n\nKontynuowac?",
        "confirm_reset": "Zresetowac wszystkie ustawienia?",
        "settings_saved": "Ustawienia zapisane",
        "settings_reset": "Ustawienia zresetowane",
        "data_exported": "Dane wyeksportowane do",
        "no_export_data": "Brak danych do eksportu",
        "api_valid": "Klucz API jest prawidlowy!",
        "api_invalid": "Nieprawidlowy klucz API",
        "api_rate_limit": "Przekroczono limit. Uzywam lokalnej generacji.",
        "enter_api_first": "Najpierw wprowadz klucz API",
        "openai_not_installed": "Biblioteka OpenAI nie zainstalowana.",
        "testing": "Testowanie...",
        "break_reminder_msg": "Pracujesz juz {0} minut. Zrob przerwe.",
        "minimized_to_tray": "Aplikacja zminimalizowana. Kliknij dwukrotnie aby przywrocic.",
        "monitoring_started": "Monitorowanie uruchomione",
        "monitoring_stopped": "Monitorowanie zatrzymane",
        "work": "Praca",
        "study": "Nauka",
        "entertainment": "Rozrywka",
        "social": "Spolecznosci",
        "neutral": "Neutralne",
        "other": "Inne",
        "previous_advice": "Poprzednie porady",
        "period": "Okres",
        "created": "Utworzono",
        "preview": "Podglad",
        "advice_placeholder": "Kliknij 'Generuj porade' aby uzyskac rekomendacje...",
        "by_category": "Wg kategorii",
        "events": "Wydarzen",
        "total": "Razem",
        "unproductive": "Nieproduktywne",
        "productive": "Produktywne",
        "start_col": "Poczatek",
        "end_col": "Koniec",
    },
    "de": {
        "lang_name": "Deutsch",
        "app_title": "TimeWeaver Pro",
        "dashboard": "Dashboard",
        "activity": "Aktivitat",
        "system": "System",
        "reports": "Berichte",
        "insights": "Tipps",
        "settings": "Einstellungen",
        "start": "Starten",
        "stop": "Stoppen",
        "status_ready": "Bereit",
        "status_monitoring": "Uberwachung aktiv",
        "status_stopped": "Uberwachung gestoppt",
        "today": "Heute",
        "yesterday": "Gestern",
        "days_ago_2": "Vor 2 Tagen",
        "week": "Woche",
        "month": "Monat",
        "total_time": "Gesamtzeit",
        "top_app": "Top App",
        "distractions": "Ablenkungen",
        "score": "Punktzahl",
        "current_activity": "Aktuelle Aktivitat",
        "generate_advice": "Tipp generieren",
        "last_7_days": "Letzte 7 Tage",
        "last_3_days": "Letzte 3 Tage",
        "last_30_days": "Letzte 30 Tage",
        "export_csv": "CSV Export",
        "category": "Kategorie",
        "time": "Zeit",
        "percent": "Prozent",
        "app": "App",
        "title": "Titel",
        "duration": "Dauer",
        "cpu": "CPU",
        "ram": "RAM",
        "disk": "Festplatte",
        "network": "Netzwerk",
        "process": "Prozess",
        "pid": "PID",
        "status": "Status",
        "usage_history": "Verlauf (letzte 60 Sek)",
        "top_processes": "Top Prozesse",
        "general": "Allgemein",
        "appearance": "Aussehen",
        "ai_settings": "KI",
        "data": "Daten",
        "username": "Benutzername",
        "poll_interval": "Abfrageintervall (ms)",
        "idle_timeout": "Leerlauf-Timeout (Sek)",
        "break_reminder": "Pausenerinnerung (Min)",
        "distraction_threshold": "Ablenkungsschwelle (%)",
        "autostart_monitoring": "Autostart Uberwachung",
        "autostart_windows": "Autostart mit Windows",
        "theme": "Thema",
        "dark_theme": "Dunkel",
        "light_theme": "Hell",
        "language": "Sprache",
        "window_size": "Fenstergrosse",
        "compact": "Kompakt (900x600)",
        "standard": "Standard (1100x700)",
        "large": "Gross (1400x900)",
        "extra_large": "Sehr gross (1600x1000)",
        "fullscreen": "Vollbild",
        "remember_window": "Fenstergrosse/-position merken",
        "minimize_to_tray": "In Taskleiste minimieren",
        "tray_notifications": "Taskleisten-Benachrichtigungen",
        "api_key": "OpenAI API-Schlussel",
        "api_key_hint": "sk-... (optional)",
        "api_key_info": "API-Schlussel ist optional.",
        "test_api": "API testen",
        "export_all": "Alle Daten exportieren",
        "clear_all": "Alle Daten loschen",
        "save": "Speichern",
        "reset": "Zurucksetzen",
        "about": "Uber",
        "about_text": "Aktivitatstracker und Produktivitatsanalysator fur Windows.",
        "no_data": "Nicht genug Daten fur Analyse",
        "generating": "Generiere Tipps...",
        "error": "Fehler",
        "success": "Erfolg",
        "warning": "Warnung",
        "confirm_clear": "Dies loscht ALLE Daten!\n\nFortfahren?",
        "confirm_reset": "Alle Einstellungen zurucksetzen?",
        "settings_saved": "Einstellungen gespeichert",
        "settings_reset": "Einstellungen zuruckgesetzt",
        "data_exported": "Daten exportiert nach",
        "no_export_data": "Keine Daten zum Exportieren",
        "api_valid": "API-Schlussel gultig!",
        "api_invalid": "Ungultiger API-Schlussel",
        "api_rate_limit": "Limit uberschritten. Verwende lokale Generierung.",
        "enter_api_first": "Zuerst API-Schlussel eingeben",
        "openai_not_installed": "OpenAI Bibliothek nicht installiert.",
        "testing": "Teste...",
        "break_reminder_msg": "Sie arbeiten seit {0} Minuten. Machen Sie eine Pause.",
        "minimized_to_tray": "App minimiert. Doppelklick zum Wiederherstellen.",
        "monitoring_started": "Uberwachung gestartet",
        "monitoring_stopped": "Uberwachung gestoppt",
        "work": "Arbeit",
        "study": "Lernen",
        "entertainment": "Unterhaltung",
        "social": "Soziales",
        "neutral": "Neutral",
        "other": "Andere",
        "previous_advice": "Fruhere Tipps",
        "period": "Zeitraum",
        "created": "Erstellt",
        "preview": "Vorschau",
        "advice_placeholder": "Klicken Sie 'Tipp generieren' fur Empfehlungen...",
        "by_category": "Nach Kategorie",
        "events": "Ereignisse",
        "total": "Gesamt",
        "unproductive": "Unproduktiv",
        "productive": "Produktiv",
        "start_col": "Start",
        "end_col": "Ende",
    },
}

ICONS = {
    "home": "\u2302",        # ⌂
    "activity": "\u23F1",    # ⏱
    "system": "\u2699",      # ⚙
    "reports": "\u2637",     # ☷
    "insights": "\u2728",    # ✨ (will show as box on some fonts, fallback to *)
    "settings": "\u2630",    # ☰
    "start": "\u25B6",       # ▶
    "stop": "\u25A0",        # ■
    "time": "\u23F0",        # ⏰
    "app": "\u2610",         # ☐
    "warning": "\u26A0",     # ⚠
    "success": "\u2713",     # ✓
    "error": "\u2717",       # ✗
    "cpu": "\u2338",         # ⌸
    "ram": "\u2630",         # ☰
    "disk": "\u2B58",        # ⭘
    "network": "\u2301",     # ⌁
    "export": "\u21E9",      # ⇩
    "delete": "\u2716",      # ✖
    "save": "\u2714",        # ✔
    "reset": "\u21BA",       # ↺
    "test": "\u2192",        # →
    "fullscreen": "\u26F6",  # ⛶
    "work": "\u2692",        # ⚒
    "study": "\u2710",       # ✐
    "entertainment": "\u263A", # ☺
    "social": "\u2709",      # ✉
    "neutral": "\u25CF",     # ●
    "other": "\u2022",       # •
    "on": "\u25CF",          # ●
    "off": "\u25CB",         # ○
    "info": "\u2139",        # ℹ
    "ai": "\u2605",          # ★
}

# Global language manager
class LanguageManager:
    _instance = None
    _current_lang = "uk"
    
    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def set_language(self, lang_code: str):
        if lang_code in TRANSLATIONS:
            self._current_lang = lang_code
    
    def get_language(self) -> str:
        return self._current_lang
    
    def t(self, key: str) -> str:
        """Get translation for key"""
        lang_dict = TRANSLATIONS.get(self._current_lang, TRANSLATIONS["uk"])
        return lang_dict.get(key, TRANSLATIONS["uk"].get(key, key))
    
    def get_available_languages(self) -> list:
        return [(code, data["lang_name"]) for code, data in TRANSLATIONS.items()]

def t(key: str) -> str:
    """Shortcut for translation"""
    return LanguageManager.instance().t(key)

def icon(name: str) -> str:
    """Get icon for name"""
    return ICONS.get(name, "*")

# =========================
# Data + DB
# =========================
def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def parse_ts(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

def ensure_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_ts TEXT NOT NULL,
        end_ts TEXT NOT NULL,
        duration_sec INTEGER NOT NULL,
        app TEXT NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        score REAL NOT NULL
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS app_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        app TEXT NOT NULL,
        title_contains TEXT NOT NULL,
        category TEXT NOT NULL,
        score REAL NOT NULL
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ai_advice (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_start TEXT NOT NULL,
        period_end TEXT NOT NULL,
        advice_text TEXT NOT NULL,
        created_ts TEXT NOT NULL,
        advice_hash TEXT DEFAULT ''
    )
    """)
    
    try:
        cur.execute("ALTER TABLE ai_advice ADD COLUMN advice_hash TEXT DEFAULT ''")
    except:
        pass
    
    conn.commit()
    
    cur.execute("SELECT COUNT(*) FROM app_rules")
    count = cur.fetchone()[0]
    if count == 0:
        defaults = [
            ("chrome.exe", "YouTube", "Entertainment", -1.0),
            ("chrome.exe", "Twitch", "Entertainment", -1.0),
            ("chrome.exe", "TikTok", "Entertainment", -1.0),
            ("chrome.exe", "Instagram", "Social", -0.5),
            ("chrome.exe", "Telegram", "Social", -0.5),
            ("chrome.exe", "ChatGPT", "Study", +1.0),
            ("chrome.exe", "GitHub", "Work", +1.0),
            ("chrome.exe", "Stack Overflow", "Study", +0.8),
            ("chrome.exe", "Google Docs", "Work", +0.8),
            ("msedge.exe", "YouTube", "Entertainment", -1.0),
            ("msedge.exe", "GitHub", "Work", +1.0),
            ("firefox.exe", "YouTube", "Entertainment", -1.0),
            ("code.exe", "", "Work", +1.0),
            ("devenv.exe", "", "Work", +1.0),
            ("pycharm64.exe", "", "Work", +1.0),
            ("idea64.exe", "", "Work", +1.0),
            ("notepad.exe", "", "Work", +0.6),
            ("notepad++.exe", "", "Work", +0.8),
            ("WINWORD.EXE", "", "Work", +0.8),
            ("EXCEL.EXE", "", "Work", +0.8),
            ("POWERPNT.EXE", "", "Work", +0.7),
            ("discord.exe", "", "Social", -0.8),
            ("steam.exe", "", "Entertainment", -1.0),
            ("Spotify.exe", "", "Entertainment", -0.3),
            ("slack.exe", "", "Work", +0.5),
            ("zoom.exe", "", "Work", +0.6),
            ("teams.exe", "", "Work", +0.6),
        ]
        cur.executemany(
            "INSERT INTO app_rules(app,title_contains,category,score) VALUES (?,?,?,?)",
            defaults
        )
        conn.commit()
    conn.close()

def db_connect(db_path: str):
    return sqlite3.connect(db_path)

@dataclass
class ActiveWindow:
    app: str
    title: str

class Categorizer:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def classify(self, app: str, title: str) -> tuple:
        try:
            cur = self.conn.cursor()
            cur.execute("""
                SELECT category, score, title_contains
                FROM app_rules
                WHERE LOWER(app)=LOWER(?)
                ORDER BY LENGTH(title_contains) DESC
            """, (app,))
            rules = cur.fetchall()

            a = (app or "").lower()
            t = (title or "").lower()
            
            # ===== 1️⃣ DATABASE RULES (HIGHEST PRIORITY) =====
            for category, score, contains in rules:
                contains = (contains or "").strip()
                if contains == "":
                    return category, float(score)
                if contains.lower() in t:
                    return category, float(score)

            # ===== 2️⃣ GAMES =====
            game_keywords = [
                "osu",
                "steam",
                "valorant",
                "csgo",
                "dota",
                "league",
                "minecraft",
                "fortnite"
            ]

            if any(k in a or k in t for k in game_keywords):
                return "Entertainment", -1.0

            # ===== 3️⃣ DEVELOPMENT TOOLS =====
            if a in ("code.exe", "devenv.exe", "pycharm64.exe", "idea64.exe"):
                return "Work", +1.0

            # ===== 4️⃣ BROWSERS (SMART DETECTION) =====
            if "chrome" in a or "msedge" in a or "firefox" in a:
                if any(x in t for x in ["tiktok", "youtube", "instagram", "facebook"]):
                    return "Entertainment", -0.8
                if any(x in t for x in ["docs", "github", "jira", "chatgpt", "gmail"]):
                    return "Work", +0.8
                return "Neutral", +0.2

            # ===== 5️⃣ FALLBACK =====
            return "Other", 0.0

        except Exception:
            return "Other", 0.0

# =========================
# Windows active window tracker
# =========================
def get_active_window() -> ActiveWindow:
    if not (PSUTIL_OK and WIN32_OK):
        return ActiveWindow(app="missing_modules.exe", title="Install psutil + pywin32")
    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd) or ""
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        p = psutil.Process(pid)
        app = p.name() or "unknown.exe"
        return ActiveWindow(app=app, title=title)
    except Exception:
        return ActiveWindow(app="unknown.exe", title="")

# =========================
# Sleep/Idle Detection
# =========================
class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint),
    ]

class SystemStateDetector:
    def __init__(self, idle_timeout_sec: int = 180):
        self.idle_timeout_sec = idle_timeout_sec
        self.last_check_time = datetime.now()
        self.last_tick_count = self._get_tick_count()
        self.was_sleeping = False
        
    def _get_tick_count(self) -> int:
        try:
            return ctypes.windll.kernel32.GetTickCount64()
        except:
            return ctypes.windll.kernel32.GetTickCount()
    
    def _get_last_input_time(self) -> int:
        try:
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(lii)
            ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
            current_tick = self._get_tick_count()
            return current_tick - lii.dwTime
        except Exception:
            return 0
    
    def _is_screen_locked(self) -> bool:
        try:
            if PSUTIL_OK:
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'] and proc.info['name'].lower() == 'logonui.exe':
                        return True
            return False
        except Exception:
            return False
    
    def check_state(self) -> dict:
        now = datetime.now()
        current_tick = self._get_tick_count()
        
        time_since_last_check = (now - self.last_check_time).total_seconds()
        expected_tick_diff = time_since_last_check * 1000
        actual_tick_diff = current_tick - self.last_tick_count
        
        time_gap_detected = False
        if time_since_last_check > 5:
            if actual_tick_diff < expected_tick_diff * 0.5:
                time_gap_detected = True
        
        if time_since_last_check > 30:
            time_gap_detected = True
        
        idle_ms = self._get_last_input_time()
        idle_seconds = idle_ms / 1000
        
        is_idle = idle_seconds > self.idle_timeout_sec
        is_locked = self._is_screen_locked()
        is_sleeping = time_gap_detected or is_locked or is_idle
        
        self.last_check_time = now
        self.last_tick_count = current_tick
        self.was_sleeping = is_sleeping
        
        return {
            "is_idle": is_idle,
            "is_sleeping": is_sleeping,
            "is_locked": is_locked,
            "idle_seconds": int(idle_seconds),
            "time_gap_detected": time_gap_detected,
            "time_since_last_check": int(time_since_last_check),
        }

# =========================
# Autostart
# =========================
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE_NAME = "TimeWeaverX"

def set_autostart(enabled: bool, exe_path: str):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
    except FileNotFoundError:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY)
    if enabled:
        winreg.SetValueEx(key, RUN_VALUE_NAME, 0, winreg.REG_SZ, f"\"{exe_path}\"")
    else:
        try:
            winreg.DeleteValue(key, RUN_VALUE_NAME)
        except FileNotFoundError:
            pass
    winreg.CloseKey(key)

def get_autostart_enabled() -> bool:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ)
        _ = winreg.QueryValueEx(key, RUN_VALUE_NAME)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

# =========================
# Analytics
# =========================
def dt_range_for(day: QDate) -> tuple:
    start = datetime(day.year(), day.month(), day.day(), 0, 0, 0)
    end = start + timedelta(days=1)
    return start, end

def sum_by_app(conn: sqlite3.Connection, start: datetime, end: datetime, limit: int = 10):
    cur = conn.cursor()
    cur.execute("""
        SELECT
            app,
            SUM(duration_sec) AS total_sec,
            category
        FROM activities
        WHERE start_ts >= ? AND start_ts < ?
        GROUP BY app, category
        ORDER BY total_sec DESC
        LIMIT ?
    """, (
        start.strftime("%Y-%m-%d %H:%M:%S"),
        end.strftime("%Y-%m-%d %H:%M:%S"),
        limit
    ))
    return cur.fetchall()

def sum_by_category(conn: sqlite3.Connection, start: datetime, end: datetime):
    cur = conn.cursor()
    cur.execute("""
        SELECT category, SUM(duration_sec) AS s, SUM(score * duration_sec) AS score_sum
        FROM activities
        WHERE start_ts >= ? AND start_ts < ?
        GROUP BY category
        ORDER BY s DESC
    """, (start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S")))
    return cur.fetchall()

def sum_by_category_and_app(conn, start, end):
    cur = conn.cursor()
    cur.execute("""
        SELECT
            category,
            app,
            SUM(duration_sec) as sec
        FROM activities
        WHERE start_ts >= ? AND start_ts < ?
        GROUP BY category, app
        ORDER BY category, sec DESC
    """, (start, end))
    return cur.fetchall()

def last_events(conn: sqlite3.Connection, start: datetime, end: datetime, limit: int = 200):
    cur = conn.cursor()
    cur.execute("""
        SELECT start_ts, end_ts, duration_sec, app, title, category, score
        FROM activities
        WHERE start_ts >= ? AND start_ts < ?
        ORDER BY start_ts DESC
        LIMIT ?
    """, (start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S"), limit))
    return cur.fetchall()

def compute_productivity(conn: sqlite3.Connection, start: datetime, end: datetime) -> dict:
    cats = sum_by_category(conn, start, end)
    total_sec = sum(s for _, s, _ in cats) if cats else 0
    score_sum = sum(score_sum for _, _, score_sum in cats) if cats else 0.0
    unprod_sec = sum(s for c, s, _ in cats if c in ("Entertainment", "Social"))
    prod_ratio = 0.0 if total_sec == 0 else (score_sum / total_sec)
    unprod_ratio = 0.0 if total_sec == 0 else (unprod_sec / total_sec)
    return {
        "total_sec": total_sec,
        "score_sum": score_sum,
        "prod_ratio": prod_ratio,
        "unprod_ratio": unprod_ratio,
    }

def compute_distraction_percent(conn, start_ts, end_ts):
        cur = conn.cursor()
        cur.execute("""
            SELECT
                SUM(duration_sec) AS total_time,
                SUM(
                    CASE
                        WHEN category IN ('Entertainment','Social')
                        THEN duration_sec ELSE 0
                    END
                ) AS distract_time
            FROM activities
            WHERE start_ts >= ? AND start_ts < ?
        """, (start_ts, end_ts))

        row = cur.fetchone()
        if not row or not row[0]:
            return 0.0

        total, distract = row
        return (distract / total) * 100.0

def get_hourly_distribution(conn: sqlite3.Connection, start: datetime, end: datetime):
    cur = conn.cursor()
    cur.execute("""
        SELECT strftime('%H', start_ts) as hour, SUM(duration_sec) as total
        FROM activities
        WHERE start_ts >= ? AND start_ts < ?
        GROUP BY hour
        ORDER BY hour
    """, (start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S")))
    return cur.fetchall()

def get_daily_trends(conn: sqlite3.Connection, days: int = 7):
    cur = conn.cursor()
    end = datetime.now()
    start = end - timedelta(days=days)
    cur.execute("""
        SELECT date(start_ts) as day, 
               SUM(duration_sec) as total,
               SUM(CASE WHEN category IN ('Work', 'Study') THEN duration_sec ELSE 0 END) as productive,
               SUM(CASE WHEN category IN ('Entertainment', 'Social') THEN duration_sec ELSE 0 END) as unproductive
        FROM activities
        WHERE start_ts >= ? AND start_ts < ?
        GROUP BY day
        ORDER BY day
    """, (start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S")))
    return cur.fetchall()

# =========================
# =========================
class AIAdviceGenerator(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, data: dict, api_key: str = "", lang: str = "uk"):
        super().__init__()
        self.data = data
        self.api_key = api_key.strip()
        self.lang = lang
    
    def run(self):
        try:
            advice = self._generate_advice()
            self.finished.emit(advice)
        except Exception as e:
            self.error.emit(str(e))
    
    def _generate_advice(self) -> str:
        context = self._build_context()
        
        if self.api_key and OPENAI_OK and OpenAI is not None:
            try:
                return self._generate_with_openai(context)
            except Exception as e:
                error_str = str(e).lower()
                if "429" in str(e) or "rate" in error_str or "limit" in error_str or "quota" in error_str:
                    print(f"[AI] Rate limit hit, falling back to local: {e}")
                    # Return local advice with rate limit note
                    return self._generate_smart_advice(context, rate_limited=True)
                print(f"[AI] OpenAI error: {e}")
        
        return self._generate_smart_advice(context)
    
    def _build_context(self) -> dict:
        data = self.data
        total_hours = data.get("total_sec", 0) / 3600
        prod_ratio = data.get("prod_ratio", 0)
        unprod_ratio = data.get("unprod_ratio", 0)
        
        categories = {}
        for cat, sec, _ in data.get("categories", []):
            categories[cat] = {
                "hours": sec / 3600,
                "percentage": (sec / data["total_sec"] * 100) if data["total_sec"] > 0 else 0
            }
        
        top_apps = []
        for app, sec in data.get("apps", [])[:5]:
            top_apps.append({
                "name": app,
                "hours": sec / 3600,
                "percentage": (sec / data["total_sec"] * 100) if data["total_sec"] > 0 else 0
            })
        
        return {
            "total_hours": total_hours,
            "prod_ratio": prod_ratio,
            "unprod_ratio": unprod_ratio,
            "prod_percentage": prod_ratio * 100,
            "unprod_percentage": unprod_ratio * 100,
            "categories": categories,
            "top_apps": top_apps,
            "period_start": data.get("period_start", ""),
            "period_end": data.get("period_end", ""),
            "timestamp": datetime.now().isoformat(),
        }
    
    def _generate_with_openai(self, context: dict) -> str:
        client = OpenAI(api_key=self.api_key)

        lang_instructions = {
            "uk": "Write in Ukrainian language.",
            "en": "Write in English language.",
            "ru": "Write in Russian language.",
            "pl": "Write in Polish language.",
            "de": "Write in German language.",
        }

        lang_instruction = lang_instructions.get(self.lang, "Write in Ukrainian language.")

        prompt = f"""
You are a productivity expert.
Generate UNIQUE, personalized advice based on real activity data.

DATA:
- Total PC time: {context['total_hours']:.1f} hours
- Productivity: {context['prod_percentage']:.1f}%
- Distractions: {context['unprod_percentage']:.1f}%
- Categories: {json.dumps(context['categories'], ensure_ascii=False)}
- Top apps: {json.dumps(context['top_apps'], ensure_ascii=False)}
- Period: {context['period_start']} to {context['period_end']}
- Current time: {datetime.now().strftime('%A, %d %B %Y, %H:%M')}

REQUIREMENTS:
1. Advice must be NEW every time
2. Use exact numbers from data
3. Avoid generic tips
4. Give actionable steps
5. {lang_instruction}
6. Structure:
   - Short summary
   - Analysis
   - 3–5 concrete recommendations

Generate 300–500 words.
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",   # ✅ стабільна модель
            messages=[
                {"role": "system", "content": "You are an expert in productivity and time management."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=900,
        )

        return response.choices[0].message.content
    
    def _generate_smart_advice(self, context: dict, rate_limited: bool = False) -> str:
        """Generate smart advice with randomization - multilingual"""
        random.seed(int(datetime.now().timestamp()) % 10000)
        
        parts = []
        
        if rate_limited:
            rate_limit_msgs = {
                "uk": f"{icon('warning')} API ліміт перевищено. Використовую локальну генерацію.\n",
                "en": f"{icon('warning')} API rate limit exceeded. Using local generation.\n",
                "ru": f"{icon('warning')} Лимит API превышен. Использую локальную генерацию.\n",
                "pl": f"{icon('warning')} Limit API przekroczony. Uzywam lokalnej generacji.\n",
                "de": f"{icon('warning')} API-Limit uberschritten. Verwende lokale Generierung.\n",
            }
            parts.append(rate_limit_msgs.get(self.lang, rate_limit_msgs["uk"]))
        
        # Titles based on language
        titles = {
            "uk": {
                "analysis": "АНАЛІЗ ПРОДУКТИВНОСТІ",
                "period": "Період",
                "generated": "Згенеровано",
                "insufficient": "Недостатньо даних для повного аналізу.",
                "continue": "Продовжуйте використовувати програму.",
                "total_time": "Загальний час за ПК",
                "productivity": "Оцінка продуктивності",
                "distractions": "Час на відволікання",
                "top_apps": "ТОП-5 ПРОГРАМ",
                "categories": "КАТЕГОРІЇ",
                "tips": "ПЕРСОНАЛІЗОВАНІ ПОРАДИ",
                "hours": "год",
                "remember": "Пам'ятайте: маленькі кроки ведуть до великих змін!",
            },
            "en": {
                "analysis": "PRODUCTIVITY ANALYSIS",
                "period": "Period",
                "generated": "Generated",
                "insufficient": "Not enough data for full analysis.",
                "continue": "Continue using the app.",
                "total_time": "Total PC time",
                "productivity": "Productivity score",
                "distractions": "Distraction time",
                "top_apps": "TOP-5 APPS",
                "categories": "CATEGORIES",
                "tips": "PERSONALIZED TIPS",
                "hours": "h",
                "remember": "Remember: small steps lead to big changes!",
            },
            "ru": {
                "analysis": "АНАЛИЗ ПРОДУКТИВНОСТИ",
                "period": "Период",
                "generated": "Сгенерировано",
                "insufficient": "Недостаточно данных для полного анализа.",
                "continue": "Продолжайте использовать программу.",
                "total_time": "Общее время за ПК",
                "productivity": "Оценка продуктивности",
                "distractions": "Время на отвлечения",
                "top_apps": "ТОП-5 ПРОГРАММ",
                "categories": "КАТЕГОРИИ",
                "tips": "ПЕРСОНАЛИЗИРОВАННЫЕ СОВЕТЫ",
                "hours": "ч",
                "remember": "Помните: маленькие шаги ведут к большим изменениям!",
            },
            "pl": {
                "analysis": "ANALIZA PRODUKTYWNOSCI",
                "period": "Okres",
                "generated": "Wygenerowano",
                "insufficient": "Za malo danych do pelnej analizy.",
                "continue": "Kontynuuj uzywanie aplikacji.",
                "total_time": "Calkowity czas przy PC",
                "productivity": "Ocena produktywnosci",
                "distractions": "Czas na rozproszenia",
                "top_apps": "TOP-5 APLIKACJI",
                "categories": "KATEGORIE",
                "tips": "SPERSONALIZOWANE PORADY",
                "hours": "godz",
                "remember": "Pamietaj: male kroki prowadza do wielkich zmian!",
            },
            "de": {
                "analysis": "PRODUKTIVITATSANALYSE",
                "period": "Zeitraum",
                "generated": "Generiert",
                "insufficient": "Nicht genug Daten fur vollstandige Analyse.",
                "continue": "Nutzen Sie die App weiter.",
                "total_time": "Gesamte PC-Zeit",
                "productivity": "Produktivitatswert",
                "distractions": "Ablenkungszeit",
                "top_apps": "TOP-5 APPS",
                "categories": "KATEGORIEN",
                "tips": "PERSONALISIERTE TIPPS",
                "hours": "Std",
                "remember": "Denken Sie daran: Kleine Schritte fuhren zu grossen Veranderungen!",
            },
        }
        
        txt = titles.get(self.lang, titles["uk"])
        
        parts.append(f"=== {txt['analysis']} ===")
        parts.append(f"{txt['period']}: {context.get('period_start', 'N/A')} - {context.get('period_end', 'N/A')}")
        parts.append(f"{txt['generated']}: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
        
        total_h = context["total_hours"]
        if total_h < 0.5:
            parts.append(f"{icon('warning')} {txt['insufficient']}")
            parts.append(f"{txt['continue']}\n")
            return "\n".join(parts)
        
        parts.append("=" * 40)
        parts.append(f"{icon('time')} {txt['total_time']}: {total_h:.1f} {txt['hours']}")
        parts.append(f"{icon('success')} {txt['productivity']}: {context['prod_percentage']:.0f}%")
        parts.append(f"{icon('warning')} {txt['distractions']}: {context['unprod_percentage']:.0f}%")
        parts.append("=" * 40 + "\n")
        
        if context["top_apps"]:
            parts.append(f"{icon('app')} {txt['top_apps']}")
            medals = ["1.", "2.", "3.", "4.", "5."]
            for i, app in enumerate(context["top_apps"]):
                medal = medals[i] if i < 5 else f"{i+1}."
                parts.append(f"   {medal} {app['name']}: {app['hours']:.1f} {txt['hours']} ({app['percentage']:.0f}%)")
            parts.append("")
        
        if context["categories"]:
            parts.append(f"{icon('reports')} {txt['categories']}")
            cat_icons = {
                "Work": icon("work"), "Study": icon("study"), 
                "Entertainment": icon("entertainment"), "Social": icon("social"),
                "Neutral": icon("neutral"), "Other": icon("other")
            }
            for cat, data in context["categories"].items():
                cat_icon = cat_icons.get(cat, icon("other"))
                parts.append(f"   {cat_icon} {cat}: {data['hours']:.1f} {txt['hours']} ({data['percentage']:.0f}%)")
            parts.append("")
        
        parts.append(f"{icon('ai')} {txt['tips']}\n")
        
        prod_pct = context["prod_percentage"]
        unprod_pct = context["unprod_percentage"]
        
        # Tips based on language
        tips_data = {
            "uk": {
                "high_prod": [
                    f"{icon('success')} Відмінна робота! Ваша продуктивність на високому рівні.",
                    f"{icon('success')} Вражаюча концентрація! Продовжуйте в тому ж дусі.",
                    f"{icon('success')} Ви демонструєте чудову самодисципліну!",
                ],
                "med_prod": [
                    f"{icon('info')} Гарний баланс! Спробуйте техніку Помодоро (25 хв робота / 5 хв перерва).",
                    f"{icon('info')} Непоганий результат! Визначте свої 'золоті години' продуктивності.",
                    f"{icon('info')} Є потенціал для росту! Плануйте три головні задачі на початок дня.",
                ],
                "low_prod": [
                    f"{icon('warning')} Час для змін! Почніть з малого - виділіть 1 годину 'глибокої роботи'.",
                    f"{icon('warning')} Поставте конкретну мету на завтра. Один маленький крок веде до великих змін!",
                    f"{icon('warning')} Спробуйте 'цифровий детокс' - вимкніть сповіщення під час важливих задач.",
                ],
                "high_distract": [
                    f"{icon('error')} Багато часу йде на відволікання. Встановіть 'заборонені години' для соцмереж.",
                    f"{icon('error')} Розгляньте використання блокувальників сайтів під час роботи.",
                ],
                "med_distract": [
                    f"{icon('info')} Виділіть конкретний час для розваг (напр. 30 хв післяобіду).",
                    f"{icon('info')} Відстежуйте свої тригери відволікань.",
                ],
                "morning": f"{icon('time')} РАНОК: Найкращий час для складних задач!",
                "afternoon": f"{icon('time')} ДЕНЬ: Післяобід може бути спад енергії. Ідеально для рутини.",
                "evening": f"{icon('time')} ВЕЧІР: Час для рефлексії. Підведіть підсумки дня.",
                "weekly": [
                    f"{icon('ai')} Спробуйте 'правило 3-х' - визначте три головні досягнення на тиждень.",
                    f"{icon('ai')} Заведіть 'журнал перемог' - записуйте свої досягнення.",
                    f"{icon('ai')} Практикуйте 'ранішні сторінки' - 10 хв вільного письма на початку дня.",
                    f"{icon('ai')} Використовуйте 'метод Айзенхауера' для пріоритезації.",
                ],
            },
            "en": {
                "high_prod": [
                    f"{icon('success')} Excellent work! Your productivity is at a high level.",
                    f"{icon('success')} Impressive focus! Keep up the great work.",
                    f"{icon('success')} You're showing great self-discipline!",
                ],
                "med_prod": [
                    f"{icon('info')} Good balance! Try the Pomodoro technique (25 min work / 5 min break).",
                    f"{icon('info')} Not bad! Identify your 'golden hours' of productivity.",
                    f"{icon('info')} Room for growth! Plan three main tasks at the start of each day.",
                ],
                "low_prod": [
                    f"{icon('warning')} Time for change! Start small - dedicate 1 hour to 'deep work'.",
                    f"{icon('warning')} Set a specific goal for tomorrow. Small steps lead to big changes!",
                    f"{icon('warning')} Try a 'digital detox' - disable notifications during important tasks.",
                ],
                "high_distract": [
                    f"{icon('error')} Too much time on distractions. Set 'forbidden hours' for social media.",
                    f"{icon('error')} Consider using website blockers during work hours.",
                ],
                "med_distract": [
                    f"{icon('info')} Set specific time for entertainment (e.g., 30 min after lunch).",
                    f"{icon('info')} Track your distraction triggers.",
                ],
                "morning": f"{icon('time')} MORNING: Best time for complex tasks!",
                "afternoon": f"{icon('time')} AFTERNOON: Energy may dip. Good for routine work.",
                "evening": f"{icon('time')} EVENING: Time for reflection. Review your day.",
                "weekly": [
                    f"{icon('ai')} Try the 'rule of 3' - identify three main achievements for the week.",
                    f"{icon('ai')} Keep a 'wins journal' - record your achievements.",
                    f"{icon('ai')} Practice 'morning pages' - 10 min of free writing at the start of day.",
                    f"{icon('ai')} Use the 'Eisenhower Matrix' for prioritization.",
                ],
            },
            "ru": {
                "high_prod": [
                    f"{icon('success')} Отличная работа! Ваша продуктивность на высоком уровне.",
                    f"{icon('success')} Впечатляющая концентрация! Продолжайте в том же духе.",
                    f"{icon('success')} Вы демонстрируете отличную самодисциплину!",
                ],
                "med_prod": [
                    f"{icon('info')} Хороший баланс! Попробуйте технику Помодоро (25 мин работа / 5 мин перерыв).",
                    f"{icon('info')} Неплохой результат! Определите свои 'золотые часы' продуктивности.",
                    f"{icon('info')} Есть потенциал для роста! Планируйте три главные задачи на начало дня.",
                ],
                "low_prod": [
                    f"{icon('warning')} Время для перемен! Начните с малого - выделите 1 час 'глубокой работы'.",
                    f"{icon('warning')} Поставьте конкретную цель на завтра. Маленькие шаги ведут к большим изменениям!",
                    f"{icon('warning')} Попробуйте 'цифровой детокс' - отключите уведомления во время важных задач.",
                ],
                "high_distract": [
                    f"{icon('error')} Много времени уходит на отвлечения. Установите 'запретные часы' для соцсетей.",
                    f"{icon('error')} Рассмотрите использование блокировщиков сайтов во время работы.",
                ],
                "med_distract": [
                    f"{icon('info')} Выделите конкретное время для развлечений (напр. 30 мин после обеда).",
                    f"{icon('info')} Отслеживайте свои триггеры отвлечений.",
                ],
                "morning": f"{icon('time')} УТРО: Лучшее время для сложных задач!",
                "afternoon": f"{icon('time')} ДЕНЬ: После обеда может быть спад энергии. Идеально для рутины.",
                "evening": f"{icon('time')} ВЕЧЕР: Время для рефлексии. Подведите итоги дня.",
                "weekly": [
                    f"{icon('ai')} Попробуйте 'правило 3-х' - определите три главных достижения на неделю.",
                    f"{icon('ai')} Заведите 'журнал побед' - записывайте свои достижения.",
                    f"{icon('ai')} Практикуйте 'утренние страницы' - 10 мин свободного письма в начале дня.",
                    f"{icon('ai')} Используйте 'матрицу Эйзенхауэра' для приоритизации.",
                ],
            },
            "pl": {
                "high_prod": [
                    f"{icon('success')} Swietna robota! Twoja produktywnosc jest na wysokim poziomie.",
                    f"{icon('success')} Imponujaca koncentracja! Tak trzymaj.",
                    f"{icon('success')} Pokazujesz wspaniala samodyscypline!",
                ],
                "med_prod": [
                    f"{icon('info')} Dobra rownowaga! Wyprobuj technike Pomodoro (25 min pracy / 5 min przerwy).",
                    f"{icon('info')} Niezly wynik! Okresl swoje 'zlote godziny' produktywnosci.",
                    f"{icon('info')} Jest potencjal do wzrostu! Planuj trzy glowne zadania na poczatek dnia.",
                ],
                "low_prod": [
                    f"{icon('warning')} Czas na zmiany! Zacznij od malego - poswiec 1 godzine na 'gleboka prace'.",
                    f"{icon('warning')} Wyznacz konkretny cel na jutro. Male kroki prowadza do wielkich zmian!",
                    f"{icon('warning')} Wyprobuj 'cyfrowy detoks' - wylacz powiadomienia podczas waznych zadan.",
                ],
                "high_distract": [
                    f"{icon('error')} Zbyt duzo czasu na rozproszenia. Ustaw 'zakazane godziny' dla mediow spolecznosciowych.",
                    f"{icon('error')} Rozważ uzycie blokerow stron podczas pracy.",
                ],
                "med_distract": [
                    f"{icon('info')} Wyznacz konkretny czas na rozrywke (np. 30 min po obiedzie).",
                    f"{icon('info')} Sledz swoje wyzwalacze rozproszen.",
                ],
                "morning": f"{icon('time')} RANO: Najlepszy czas na zlożone zadania!",
                "afternoon": f"{icon('time')} POPOLUDNIE: Energia moze spasc. Dobre na rutyne.",
                "evening": f"{icon('time')} WIECZOR: Czas na refleksje. Podsumuj dzien.",
                "weekly": [
                    f"{icon('ai')} Wyprobuj 'regule 3' - okresl trzy glowne osiagniecia na tydzien.",
                    f"{icon('ai')} Prowadz 'dziennik zwycięstw' - zapisuj swoje osiagniecia.",
                    f"{icon('ai')} Praktykuj 'poranne strony' - 10 min swobodnego pisania na poczatku dnia.",
                    f"{icon('ai')} Uzyj 'macierzy Eisenhowera' do ustalania priorytetow.",
                ],
            },
            "de": {
                "high_prod": [
                    f"{icon('success')} Ausgezeichnete Arbeit! Ihre Produktivitat ist auf hohem Niveau.",
                    f"{icon('success')} Beeindruckende Konzentration! Weiter so.",
                    f"{icon('success')} Sie zeigen grosse Selbstdisziplin!",
                ],
                "med_prod": [
                    f"{icon('info')} Gute Balance! Probieren Sie die Pomodoro-Technik (25 Min Arbeit / 5 Min Pause).",
                    f"{icon('info')} Nicht schlecht! Identifizieren Sie Ihre 'goldenen Stunden' der Produktivitat.",
                    f"{icon('info')} Raum fur Wachstum! Planen Sie drei Hauptaufgaben zu Tagesbeginn.",
                ],
                "low_prod": [
                    f"{icon('warning')} Zeit fur Veranderungen! Fangen Sie klein an - widmen Sie 1 Stunde der 'tiefen Arbeit'.",
                    f"{icon('warning')} Setzen Sie ein konkretes Ziel fur morgen. Kleine Schritte fuhren zu grossen Veranderungen!",
                    f"{icon('warning')} Versuchen Sie einen 'digitalen Detox' - schalten Sie Benachrichtigungen wahrend wichtiger Aufgaben aus.",
                ],
                "high_distract": [
                    f"{icon('error')} Zu viel Zeit fur Ablenkungen. Legen Sie 'verbotene Stunden' fur Social Media fest.",
                    f"{icon('error')} Erwagen Sie Website-Blocker wahrend der Arbeitszeit.",
                ],
                "med_distract": [
                    f"{icon('info')} Legen Sie eine bestimmte Zeit fur Unterhaltung fest (z.B. 30 Min nach dem Mittagessen).",
                    f"{icon('info')} Verfolgen Sie Ihre Ablenkungsausloser.",
                ],
                "morning": f"{icon('time')} MORGEN: Beste Zeit fur komplexe Aufgaben!",
                "afternoon": f"{icon('time')} NACHMITTAG: Energie kann sinken. Gut fur Routinearbeit.",
                "evening": f"{icon('time')} ABEND: Zeit fur Reflexion. Uberprufen Sie Ihren Tag.",
                "weekly": [
                    f"{icon('ai')} Probieren Sie die '3er-Regel' - identifizieren Sie drei Haupterfolge fur die Woche.",
                    f"{icon('ai')} Fuhren Sie ein 'Erfolgsjournal' - notieren Sie Ihre Erfolge.",
                    f"{icon('ai')} Praktizieren Sie 'Morgenseiten' - 10 Min freies Schreiben zu Tagesbeginn.",
                    f"{icon('ai')} Nutzen Sie die 'Eisenhower-Matrix' zur Priorisierung.",
                ],
            },
        }
        
        tips = tips_data.get(self.lang, tips_data["uk"])
        
        if prod_pct > 60:
            parts.append(random.choice(tips["high_prod"]))
        elif prod_pct > 35:
            parts.append(random.choice(tips["med_prod"]))
        else:
            parts.append(random.choice(tips["low_prod"]))
        
        parts.append("")
        
        if unprod_pct > 35:
            parts.append(random.choice(tips["high_distract"]))
        elif unprod_pct > 20:
            parts.append(random.choice(tips["med_distract"]))
        
        parts.append("")
        
        hour = datetime.now().hour
        if hour < 12:
            parts.append(tips["morning"])
        elif hour < 18:
            parts.append(tips["afternoon"])
        else:
            parts.append(tips["evening"])
        
        parts.append("")
        parts.append(random.choice(tips["weekly"]))
        
        parts.append("\n" + "=" * 40)
        parts.append(f"{icon('info')} {txt['remember']}")
        parts.append(f"ID: {hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]}")
        
        return "\n".join(parts)


# =========================
# Theme System
# =========================
class ThemeManager:
    DARK_THEME = {
        "name": "dark",
        "main_bg": "#0d1117",
        "sidebar_bg": "#010409",
        "panel_bg": "#161b22",
        "input_bg": "#21262d",
        "border": "#30363d",
        "border_hover": "#58a6ff",
        "text_primary": "#f0f6fc",
        "text_secondary": "#c9d1d9",
        "text_muted": "#8b949e",
        "accent": "#58a6ff",
        "accent_hover": "#79c0ff",
        "success": "#3fb950",
        "warning": "#d29922",
        "error": "#f85149",
        "nav_selected": "#21262d",
        "nav_hover": "#1c2128",
        "table_alt": "#161b22",
        "scrollbar": "#30363d",
        "scrollbar_hover": "#484f58",
    }
    
    LIGHT_THEME = {
        "name": "light",
        "main_bg": "#ffffff",
        "sidebar_bg": "#f6f8fa",
        "panel_bg": "#ffffff",
        "input_bg": "#f6f8fa",
        "border": "#d0d7de",
        "border_hover": "#0969da",
        "text_primary": "#1f2328",
        "text_secondary": "#424a53",
        "text_muted": "#656d76",
        "accent": "#0969da",
        "accent_hover": "#0550ae",
        "success": "#1a7f37",
        "warning": "#9a6700",
        "error": "#cf222e",
        "nav_selected": "#ddf4ff",
        "nav_hover": "#eaeef2",
        "table_alt": "#f6f8fa",
        "scrollbar": "#d0d7de",
        "scrollbar_hover": "#afb8c1",
    }
    
    @classmethod
    def get_theme(cls, theme_name: str) -> dict:
        if theme_name == "light":
            return cls.LIGHT_THEME
        return cls.DARK_THEME
    
    @classmethod
    def generate_stylesheet(cls, theme: dict) -> str:
        return f"""
            * {{
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
           
            QMainWindow {{
                background: {theme['main_bg']};
            }}
           
            QWidget {{
                background: {theme['main_bg']};
                color: {theme['text_secondary']};
            }}
           
            #Sidebar {{
                background: {theme['sidebar_bg']};
                border-right: 1px solid {theme['border']};
            }}
           
            #Logo {{
                color: {theme['text_primary']};
                font-size: 15px;
                font-weight: 800;
                letter-spacing: 1px;
                padding: 8px 0;
            }}
           
            #Nav {{
                background: transparent;
                border: none;
                color: {theme['text_secondary']};
                font-size: 13px;
                outline: none;
            }}
            #Nav::item {{
                padding: 10px 12px;
                border-radius: 8px;
                margin: 2px 0;
            }}
            #Nav::item:selected {{
                background: {theme['nav_selected']};
                border: 1px solid {theme['border']};
                color: {theme['text_primary']};
            }}
            #Nav::item:hover {{
                background: {theme['nav_hover']};
            }}
           
            #Content {{
                background: {theme['main_bg']};
            }}
           
            #Topbar {{
                background: {theme['main_bg']};
                border-bottom: 1px solid {theme['border']};
            }}
           
            #Search {{
                background: {theme['input_bg']};
                border: 1px solid {theme['border']};
                color: {theme['text_secondary']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            #Search:focus {{
                border: 1px solid {theme['border_hover']};
            }}
           
            #IconBtn {{
                background: {theme['input_bg']};
                border: 1px solid {theme['border']};
                color: {theme['text_secondary']};
                padding: 8px 12px;
                border-radius: 8px;
                min-width: 40px;
            }}
            #IconBtn:hover {{
                border: 1px solid {theme['border_hover']};
                background: {theme['nav_hover']};
            }}
           
            QLabel {{
                color: {theme['text_secondary']};
                background: transparent;
            }}
            #Muted {{
                color: {theme['text_muted']};
                background: transparent;
            }}
            #H1 {{
                color: {theme['text_primary']};
                font-size: 20px;
                font-weight: 800;
                background: transparent;
            }}
            #H2 {{
                color: {theme['text_primary']};
                font-size: 16px;
                font-weight: 700;
                background: transparent;
            }}
           
            #Panel {{
                background: {theme['panel_bg']};
                border: 1px solid {theme['border']};
                border-radius: 10px;
            }}
           
            #StatBox {{
                background: {theme['panel_bg']};
                border: 1px solid {theme['border']};
                border-radius: 10px;
            }}
            #StatName {{
                color: {theme['text_muted']};
                font-size: 11px;
                background: transparent;
            }}
            #StatValue {{
                color: {theme['text_primary']};
                font-size: 16px;
                font-weight: 800;
                background: transparent;
            }}
           
            #PrimaryBtn {{
                background: {theme['accent']};
                border: none;
                color: #ffffff;
                padding: 10px 16px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }}
            #PrimaryBtn:hover {{
                background: {theme['accent_hover']};
            }}
            #PrimaryBtn:disabled {{
                background: {theme['border']};
                color: {theme['text_muted']};
            }}
           
            #GhostBtn {{
                background: {theme['input_bg']};
                border: 1px solid {theme['border']};
                color: {theme['text_secondary']};
                padding: 10px 16px;
                border-radius: 8px;
                font-size: 13px;
            }}
            #GhostBtn:hover {{
                border: 1px solid {theme['border_hover']};
                background: {theme['nav_hover']};
            }}
            #GhostBtn:disabled {{
                background: {theme['panel_bg']};
                color: {theme['text_muted']};
                border-color: {theme['border']};
            }}
           
            #SuccessBtn {{
                background: {theme['success']};
                border: none;
                color: #ffffff;
                padding: 10px 16px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }}
            #SuccessBtn:hover {{
                background: {theme['success']};
                opacity: 0.9;
            }}
            #SuccessBtn:disabled {{
                background: {theme['border']};
                color: {theme['text_muted']};
                opacity: 0.7;
            }}
           
            #DangerBtn {{
                background: {theme['error']};
                border: none;
                color: #ffffff;
                padding: 10px 16px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }}
            #DangerBtn:hover {{
                background: {theme['error']};
                opacity: 0.9;
            }}
            #DangerBtn:disabled {{
                background: {theme['border']};
                color: {theme['text_muted']};
                opacity: 0.7;
            }}
           
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background: {theme['input_bg']};
                border: 1px solid {theme['border']};
                color: {theme['text_secondary']};
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }}
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 1px solid {theme['border_hover']};
            }}
           
            QTextEdit {{
                background: {theme['input_bg']};
                border: 1px solid {theme['border']};
                color: {theme['text_secondary']};
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }}
            QTextEdit:focus {{
                border: 1px solid {theme['border_hover']};
            }}
           
            QComboBox {{
                background: {theme['input_bg']};
                color: {theme['text_secondary']};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 8px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {theme['text_muted']};
            }}
            QComboBox QAbstractItemView {{
                background: {theme['panel_bg']};
                border: 1px solid {theme['border']};
                color: {theme['text_secondary']};
                selection-background-color: {theme['nav_selected']};
                selection-color: {theme['text_primary']};
            }}
           
            QCheckBox {{
                color: {theme['text_secondary']};
                font-size: 13px;
                background: transparent;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid {theme['border']};
                background: {theme['input_bg']};
            }}
            QCheckBox::indicator:checked {{
                background: {theme['accent']};
                border-color: {theme['accent']};
            }}
           
            QGroupBox {{
                color: {theme['text_primary']};
                font-weight: 600;
                border: 1px solid {theme['border']};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                background: {theme['panel_bg']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                background: {theme['panel_bg']};
            }}
           
            QTabWidget::pane {{
                border: 1px solid {theme['border']};
                border-radius: 8px;
                background: {theme['panel_bg']};
                top: -1px;
            }}
            QTabBar::tab {{
                background: {theme['input_bg']};
                border: 1px solid {theme['border']};
                padding: 8px 16px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                color: {theme['text_secondary']};
            }}
            QTabBar::tab:selected {{
                background: {theme['panel_bg']};
                border-bottom-color: {theme['panel_bg']};
                color: {theme['text_primary']};
            }}
            QTabBar::tab:hover {{
                background: {theme['nav_hover']};
            }}
           
            QTableWidget {{
                background: {theme['panel_bg']};
                border: 1px solid {theme['border']};
                border-radius: 8px;
                gridline-color: {theme['border']};
                color: {theme['text_secondary']};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {theme['border']};
                color: {theme['text_secondary']};
                background: {theme['panel_bg']};
            }}
            QTableWidget::item:selected {{
                background: {theme['nav_selected']};
                color: {theme['text_primary']};
            }}
            QTableWidget::item:alternate {{
                background: {theme['table_alt']};
            }}
            QHeaderView::section {{
                background: {theme['input_bg']};
                color: {theme['text_muted']};
                border: none;
                border-bottom: 1px solid {theme['border']};
                border-right: 1px solid {theme['border']};
                padding: 8px;
                font-weight: 600;
            }}
           
            QProgressBar {{
                background: {theme['input_bg']};
                border: 1px solid {theme['border']};
                border-radius: 6px;
                text-align: center;
                color: {theme['text_secondary']};
            }}
            QProgressBar::chunk {{
                background: {theme['accent']};
                border-radius: 5px;
            }}
           
            QScrollBar:vertical {{
                background: {theme['panel_bg']};
                width: 10px;
                margin: 0;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {theme['scrollbar']};
                min-height: 30px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {theme['scrollbar_hover']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar:horizontal {{
                background: {theme['panel_bg']};
                height: 10px;
                margin: 0;
                border-radius: 5px;
            }}
            QScrollBar::handle:horizontal {{
                background: {theme['scrollbar']};
                min-width: 30px;
                border-radius: 5px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {theme['scrollbar_hover']};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
           
            QStatusBar {{
                background: {theme['sidebar_bg']};
                border-top: 1px solid {theme['border']};
                color: {theme['text_muted']};
            }}
           
            QMenu {{
                background: {theme['panel_bg']};
                border: 1px solid {theme['border']};
                color: {theme['text_secondary']};
                padding: 4px;
                border-radius: 8px;
            }}
            QMenu::item {{
                padding: 8px 24px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background: {theme['nav_selected']};
                color: {theme['text_primary']};
            }}
            QMenu::separator {{
                height: 1px;
                background: {theme['border']};
                margin: 4px 8px;
            }}
           
            QToolTip {{
                background: {theme['panel_bg']};
                border: 1px solid {theme['border']};
                color: {theme['text_secondary']};
                padding: 6px;
                border-radius: 6px;
            }}
        """


# =========================
# UI Pages
# =========================
class DashboardPage(QWidget):
    def __init__(self, on_start, on_stop, on_open_reports, on_open_settings):
        super().__init__()
        
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)
        
        # Header
        head = QHBoxLayout()
        title = QLabel(f"{icon('home')} {t('dashboard')}")
        title.setObjectName("H1")
        head.addWidget(title)
        head.addStretch(1)
        
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setObjectName("Muted")
        head.addWidget(version_label)
        root.addLayout(head)
        
        # Status row
        status_row = QHBoxLayout()
        self.status_icon = QLabel(icon("off"))
        self.status = QLabel(f"{t('status')}: {t('status_ready')}")
        self.status.setObjectName("Muted")
        status_row.addWidget(self.status_icon)
        status_row.addWidget(self.status)
        status_row.addStretch(1)
        root.addLayout(status_row)
        
        # Stats boxes
        box_row = QHBoxLayout()
        box_row.setSpacing(12)
        
        self.box_total = self._stat(f"{icon('time')} {t('total_time')}", "--:--")
        self.box_top = self._stat(f"{icon('app')} {t('top_app')}", "---")
        self.box_unprod = self._stat(f"{icon('warning')} {t('distractions')}", "---")
        self.box_score = self._stat(f"{icon('success')} {t('score')}", "---")
        
        box_row.addWidget(self.box_total)
        box_row.addWidget(self.box_top)
        box_row.addWidget(self.box_unprod)
        box_row.addWidget(self.box_score)
        root.addLayout(box_row)
        
        # Buttons
        btn_row = QHBoxLayout()

        # Створюємо кнопки ТУТ і одразу підключаємо сигнали
        self.btn_start = QPushButton(f"{icon('start')} {t('start')}")
        self.btn_start.setObjectName("SuccessBtn")
        self.btn_start.clicked.connect(on_start)  # ← цей рядок тепер безпечний

        self.btn_stop = QPushButton(f"{icon('stop')} {t('stop')}")
        self.btn_stop.setObjectName("DangerBtn")
        self.btn_stop.clicked.connect(on_stop)

        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_stop)
        btn_row.addStretch(1)

        self.btn_reports = QPushButton(f"{icon('reports')} {t('reports')}")
        self.btn_reports.setObjectName("GhostBtn")
        self.btn_reports.clicked.connect(on_open_reports)

        self.btn_settings = QPushButton(f"{icon('settings')} {t('settings')}")
        self.btn_settings.setObjectName("GhostBtn")
        self.btn_settings.clicked.connect(on_open_settings)

        btn_row.addWidget(self.btn_reports)
        btn_row.addWidget(self.btn_settings)
        root.addLayout(btn_row)
        self.set_button_states(False)
        
        # Current activity
        activity_frame = QFrame()
        activity_frame.setObjectName("Panel")
        activity_layout = QVBoxLayout(activity_frame)
        activity_layout.setContentsMargins(16, 12, 16, 12)
        
        self.current_activity_label = QLabel(f"{icon('app')} {t('current_activity')}:")
        self.current_activity_label.setObjectName("Muted")
        self.current_app_label = QLabel("---")
        self.current_app_label.setObjectName("H2")
        self.current_title_label = QLabel("---")
        self.current_title_label.setObjectName("Muted")
        self.current_title_label.setWordWrap(True)
        
        activity_layout.addWidget(self.current_activity_label)
        activity_layout.addWidget(self.current_app_label)
        activity_layout.addWidget(self.current_title_label)
        
        root.addWidget(activity_frame)
        root.addStretch(1)
    
    def _stat(self, name: str, value: str) -> QFrame:
        f = QFrame()
        f.setObjectName("StatBox")
        lay = QVBoxLayout(f)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(4)
        n = QLabel(name)
        n.setObjectName("StatName")
        v = QLabel(value)
        v.setObjectName("StatValue")
        lay.addWidget(n)
        lay.addWidget(v)
        return f
    
    def set_status(self, text: str, is_running: bool = False):
        self.status.setText(text)
        self.status_icon.setText(icon("on") if is_running else icon("off"))
    
    def set_button_states(self, is_running: bool):
        self.btn_start.setEnabled(not is_running)
        self.btn_stop.setEnabled(is_running)
    
    def set_today(self, total_hhmm: str, top_app: str, unprod_percent: str, score: str = "---"):
        self.box_total.findChild(QLabel, "StatValue").setText(total_hhmm)
        self.box_top.findChild(QLabel, "StatValue").setText(top_app)
        self.box_unprod.findChild(QLabel, "StatValue").setText(unprod_percent)
        self.box_score.findChild(QLabel, "StatValue").setText(score)
    
    def set_current_activity(self, app: str, title: str):
        self.current_app_label.setText(app or "---")
        title_short = (title[:80] + "...") if len(title) > 80 else title
        self.current_title_label.setText(title_short or "---")
    
    def update_texts(self):
        """Update all texts when language changes"""
        # This will be called when language changes to refresh UI
        pass


class TimelinePage(QWidget):
    def __init__(self):
        super().__init__()
        
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)
        
        h = QHBoxLayout()
        self.title_label = QLabel(f"{icon('activity')} {t('activity')}")
        self.title_label.setObjectName("H1")
        h.addWidget(self.title_label)
        h.addStretch(1)
        
        self.combo_range = QComboBox()
        self.combo_range.addItems([t("today"), t("yesterday"), t("days_ago_2")])
        h.addWidget(self.combo_range)
        root.addLayout(h)
        
        stats_row = QHBoxLayout()
        self.total_label = QLabel(f"{t('total')}: ---")
        self.total_label.setObjectName("Muted")
        self.events_label = QLabel(f"{t('events')}: ---")
        self.events_label.setObjectName("Muted")
        stats_row.addWidget(self.total_label)
        stats_row.addWidget(self.events_label)
        stats_row.addStretch(1)
        root.addLayout(stats_row)
        
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            t("start_col"), t("end_col"), t("duration"), 
            t("app"), t("category"), t("title")
        ])
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, stretch=1)
    
    def selected_range(self) -> QDate:
        today = QDate.currentDate()
        idx = self.combo_range.currentIndex()
        return today.addDays(-idx)
    
    def set_rows(self, rows):
        self.table.setRowCount(len(rows))
        total_sec = 0
        
        for r, (start_ts, end_ts, sec, app, title, cat, score) in enumerate(rows):
            total_sec += sec
            mins = sec // 60
            secs = sec % 60
            duration_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
            
            self.table.setItem(r, 0, QTableWidgetItem(start_ts[11:19]))
            self.table.setItem(r, 1, QTableWidgetItem(end_ts[11:19]))
            self.table.setItem(r, 2, QTableWidgetItem(duration_str))
            self.table.setItem(r, 3, QTableWidgetItem(app))
            self.table.setItem(r, 4, QTableWidgetItem(cat))
            self.table.setItem(r, 5, QTableWidgetItem(title[:100]))
        
        total_min = total_sec // 60
        hours = total_min // 60
        mins = total_min % 60
        self.total_label.setText(f"{t('total')}: {hours}h {mins}m")
        self.events_label.setText(f"{t('events')}: {len(rows)}")


class SystemMonitorPage(QWidget):
    def __init__(self):
        super().__init__()
        
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)
        
        title = QLabel(f"{icon('system')} {t('system')}")
        title.setObjectName("H1")
        root.addWidget(title)
        
        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        
        self.box_cpu = self._stat_box(f"{icon('cpu')} {t('cpu')}", "---%")
        self.box_ram = self._stat_box(f"{icon('ram')} {t('ram')}", "---%")
        self.box_disk = self._stat_box(f"{icon('disk')} {t('disk')}", "---%")
        self.box_network = self._stat_box(f"{icon('network')} {t('network')}", "---")
        
        stats_row.addWidget(self.box_cpu)
        stats_row.addWidget(self.box_ram)
        stats_row.addWidget(self.box_disk)
        stats_row.addWidget(self.box_network)
        root.addLayout(stats_row)
        
        # Progress bars
        progress_frame = QFrame()
        progress_frame.setObjectName("Panel")
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(16, 16, 16, 16)
        progress_layout.setSpacing(12)
        
        cpu_row = QHBoxLayout()
        cpu_label = QLabel(f"{t('cpu')}:")
        cpu_label.setFixedWidth(60)
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setTextVisible(True)
        cpu_row.addWidget(cpu_label)
        cpu_row.addWidget(self.cpu_progress)
        progress_layout.addLayout(cpu_row)
        
        ram_row = QHBoxLayout()
        ram_label = QLabel(f"{t('ram')}:")
        ram_label.setFixedWidth(60)
        self.ram_progress = QProgressBar()
        self.ram_progress.setTextVisible(True)
        ram_row.addWidget(ram_label)
        ram_row.addWidget(self.ram_progress)
        progress_layout.addLayout(ram_row)
        
        root.addWidget(progress_frame)
        
        # Graphs
        graph_frame = QFrame()
        graph_frame.setObjectName("Panel")
        graph_layout = QVBoxLayout(graph_frame)
        graph_layout.setContentsMargins(12, 12, 12, 12)
        
        graph_title = QLabel(t("usage_history"))
        graph_title.setObjectName("Muted")
        graph_layout.addWidget(graph_title)
        
        self.cpu_plot = pg.PlotWidget()
        self.cpu_plot.setBackground(None)
        self.cpu_plot.setTitle(f"{t('cpu')} %")
        self.cpu_plot.setYRange(0, 100)
        self.cpu_plot.showGrid(y=True, alpha=0.3)
        self.cpu_curve = self.cpu_plot.plot(pen=pg.mkPen('#58a6ff', width=2))
        
        self.ram_plot = pg.PlotWidget()
        self.ram_plot.setBackground(None)
        self.ram_plot.setTitle(f"{t('ram')} %")
        self.ram_plot.setYRange(0, 100)
        self.ram_plot.showGrid(y=True, alpha=0.3)
        self.ram_curve = self.ram_plot.plot(pen=pg.mkPen('#f85149', width=2))
        
        graph_layout.addWidget(self.cpu_plot)
        graph_layout.addWidget(self.ram_plot)
        root.addWidget(graph_frame, stretch=1)
        
        # Process table
        proc_label = QLabel(t("top_processes"))
        proc_label.setObjectName("Muted")
        root.addWidget(proc_label)
        
        self.process_table = QTableWidget(0, 5)
        self.process_table.setHorizontalHeaderLabels([
            t("process"), t("pid"), f"{t('cpu')} %", f"{t('ram')} MB", t("status")
        ])
        self.process_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.process_table.setMaximumHeight(250)
        root.addWidget(self.process_table)
        
        self.cpu_history = deque(maxlen=60)
        self.ram_history = deque(maxlen=60)
        
        for _ in range(60):
            self.cpu_history.append(0)
            self.ram_history.append(0)
    
    def _stat_box(self, name: str, value: str) -> QFrame:
        f = QFrame()
        f.setObjectName("StatBox")
        lay = QVBoxLayout(f)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(4)
        n = QLabel(name)
        n.setObjectName("StatName")
        v = QLabel(value)
        v.setObjectName("StatValue")
        lay.addWidget(n)
        lay.addWidget(v)
        return f
    
    def update_stats(self):
        if not PSUTIL_OK:
            return
        
        try:
            cpu_pct = psutil.cpu_percent(interval=0.1)
            self.box_cpu.findChild(QLabel, "StatValue").setText(f"{cpu_pct:.1f}%")
            self.cpu_progress.setValue(int(cpu_pct))
            self.cpu_history.append(cpu_pct)
            self.cpu_curve.setData(list(self.cpu_history))
            
            ram = psutil.virtual_memory()
            ram_pct = ram.percent
            ram_gb = ram.used / (1024**3)
            ram_total_gb = ram.total / (1024**3)
            self.box_ram.findChild(QLabel, "StatValue").setText(f"{ram_pct:.1f}%")
            self.ram_progress.setValue(int(ram_pct))
            self.ram_progress.setFormat(f"{ram_gb:.1f}/{ram_total_gb:.1f} GB ({ram_pct:.0f}%)")
            self.ram_history.append(ram_pct)
            self.ram_curve.setData(list(self.ram_history))
            
            disk = psutil.disk_usage('/')
            self.box_disk.findChild(QLabel, "StatValue").setText(f"{disk.percent:.1f}%")
            
            net = psutil.net_io_counters()
            sent_mb = net.bytes_sent / (1024**2)
            recv_mb = net.bytes_recv / (1024**2)
            self.box_network.findChild(QLabel, "StatValue").setText(f"U:{sent_mb:.0f}MB D:{recv_mb:.0f}MB")
            
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status']):
                try:
                    info = proc.info
                    cpu = info['cpu_percent'] or 0
                    mem = info['memory_info'].rss / (1024**2) if info['memory_info'] else 0
                    processes.append({
                        'name': info['name'],
                        'pid': info['pid'],
                        'cpu': cpu,
                        'mem': mem,
                        'status': info['status']
                    })
                except:
                    continue
            
            processes.sort(key=lambda x: (x['cpu'], x['mem']), reverse=True)
            top_processes = processes[:10]
            
            self.process_table.setRowCount(len(top_processes))
            for i, p in enumerate(top_processes):
                self.process_table.setItem(i, 0, QTableWidgetItem(p['name'][:40]))
                self.process_table.setItem(i, 1, QTableWidgetItem(str(p['pid'])))
                self.process_table.setItem(i, 2, QTableWidgetItem(f"{p['cpu']:.1f}"))
                self.process_table.setItem(i, 3, QTableWidgetItem(f"{p['mem']:.1f}"))
                self.process_table.setItem(i, 4, QTableWidgetItem(p['status']))
                
        except Exception as e:
            print(f"[System] Error: {e}")

class ReportsPage(QWidget):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)
        
        h = QHBoxLayout()
        title = QLabel(f"{icon('reports')} {t('reports')}")
        title.setObjectName("H1")
        h.addWidget(title)
        h.addStretch(1)
        
        self.combo = QComboBox()
        self.combo.addItems([t("today"), t("week"), t("month")])
        h.addWidget(self.combo)
        
        self.btn_export = QPushButton(f"{icon('export')} {t('export_csv')}")
        self.btn_export.setObjectName("PrimaryBtn")
        self.btn_export.clicked.connect(self.export_to_csv)
        h.addWidget(self.btn_export)
        
        root.addLayout(h)
        
        self.plot = pg.PlotWidget()
        self.plot.setBackground(None)
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.setTitle(f"{t('top_app')} (min)")
        self.plot.getAxis("bottom").setTicks([])
        root.addWidget(self.plot, stretch=1)
        
        cat_label = QLabel(t("by_category"))
        cat_label.setObjectName("Muted")
        root.addWidget(cat_label)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels([
            t("category"),
            t("time"),
            t("percent")
        ])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        root.addWidget(self.tree)

        # ===== SUMMARY =====
        self.summary = QLabel("---")
        self.summary.setObjectName("Muted")
        root.addWidget(self.summary)

    def make_color_icon(self, color_hex: str, size: int = 12) -> QIcon:
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(color_hex))
        return QIcon(pixmap)

    def set_top_apps_plot(self, app_rows):
        self.plot.clear()

        if not app_rows:
            return

        names = []  # ← ТУТ була твоя помилка (names не існував)

        for i, row in enumerate(app_rows):
            app = row[0]
            seconds = row[1]
            category = row[2] if len(row) > 2 else "Other"

            minutes = seconds / 60
            names.append(app)

            color = CATEGORY_COLORS.get(category, QColor("#000000"))

            bar = pg.BarGraphItem(
                x=[i],
                height=[minutes],
                width=0.6,
                brush=color
            )

            self.plot.addItem(bar)

        # 🔽 підписи програм знизу
        axis = self.plot.getAxis("bottom")
        axis.setTicks([[(i, names[i]) for i in range(len(names))]])


    # ===== NEW METHOD =====
    def set_category_breakdown(self, rows, total_sec):

        expanded = set()
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.isExpanded():
                expanded.add(item.text(0))

        self.tree.clear()

        if not rows or not total_sec:
            return

        categories = {}
        for category, app, sec in rows:
            categories.setdefault(category, []).append((app, sec))

        for category, apps in categories.items():
            cat_sec = sum(sec for _, sec in apps)
            cat_pct = (cat_sec / total_sec) * 100

            parent = QTreeWidgetItem([
                category,
                f"{int(cat_sec // 60)} хв",
                f"{int(cat_pct)}%"
            ])

            color_hex = CATEGORY_COLORS.get(category, "#000000")
            parent.setIcon(0, self.make_color_icon(color_hex))

            self.tree.addTopLevelItem(parent)

            for app, sec in apps:
                app_pct = (sec / total_sec) * 100
                child = QTreeWidgetItem([
                    app,
                    f"{int(sec // 60)} хв",
                    f"{int(app_pct)}%"
                ])

                child.setIcon(0, self.make_color_icon(color_hex))
                parent.addChild(child)

            if category in expanded:
                parent.setExpanded(True)
    
    def selected_period(self):
        today = datetime.now().date()
        idx = self.combo.currentIndex()
        
        if idx == 0:
            start = datetime(today.year, today.month, today.day)
            end = start + timedelta(days=1)
        elif idx == 1:
            end = datetime(today.year, today.month, today.day) + timedelta(days=1)
            start = end - timedelta(days=7)
        else:
            end = datetime(today.year, today.month, today.day) + timedelta(days=1)
            start = end - timedelta(days=30)
        
        return start, end
    
    def set_report(self, app_rows, cat_rows, productivity: dict):
        self.plot.clear()
        
        if not app_rows:
            self.summary.setText(t("no_data"))
            return
        
        apps = [a[:20] for a, _ in app_rows]
        mins = [int(s // 60) for _, s in app_rows]
        x = list(range(len(apps)))
        bg = pg.BarGraphItem(x=x, height=mins, width=0.7, brush='#58a6ff')
        self.plot.addItem(bg)
        self.plot.getAxis("bottom").setTicks([list(zip(x, apps))])
        
        self.cat_table.setRowCount(len(cat_rows))
        total_sec = productivity["total_sec"]
        
        cat_icons = {
            "Work": icon("work"), "Study": icon("study"), 
            "Entertainment": icon("entertainment"), "Social": icon("social"),
            "Neutral": icon("neutral"), "Other": icon("other")
        }
        
        for r, (cat, sec, _) in enumerate(cat_rows):
            mins_val = int(sec // 60)
            hours = mins_val // 60
            mins_rem = mins_val % 60
            pct = (sec / total_sec * 100) if total_sec else 0
            
            cat_icon = cat_icons.get(cat, icon("other"))
            time_str = f"{hours}h {mins_rem}m" if hours > 0 else f"{mins_val}m"
            
            self.cat_table.setItem(r, 0, QTableWidgetItem(f"{cat_icon} {cat}"))
            self.cat_table.setItem(r, 1, QTableWidgetItem(time_str))
            self.cat_table.setItem(r, 2, QTableWidgetItem(f"{pct:.1f}%"))
        
        total_min = int(productivity["total_sec"] // 60)
        hours = total_min // 60
        mins_rem = total_min % 60
        unprod_pct = int(productivity["unprod_ratio"] * 100) if productivity["total_sec"] else 0
        score = productivity["prod_ratio"]
        
        self.summary.setText(
            f"{icon('time')} {t('total')}: {hours}h {mins_rem}m | "
            f"{icon('warning')} {t('distractions')}: {unprod_pct}% | "
            f"{icon('success')} {t('score')}: {score:.2f}"
        )
    
    def export_to_csv(self):
        start, end = self.selected_period()
        rows = last_events(self.conn, start, end, limit=10000)

        if not rows:
            QMessageBox.information(self, t("export_csv"), t("no_export_data"))
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"timeweaver_report_{timestamp}.csv"

        with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")  # ← ВАЖЛИВО
            writer.writerow([
                "Start",
                "End",
                "Duration_sec",
                "App",
                "Title",
                "Category",
                "Score"
            ])
            for row in rows:
                writer.writerow(row)

            QMessageBox.information(
                self,
                t("export_csv"),
                f"{icon('success')} {t('data_exported')}\n{file_path}"
            )

class InsightsPage(QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.is_generating = False
        
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)
        
        header = QHBoxLayout()
        title = QLabel(f"{icon('ai')} {t('insights')}")
        title.setObjectName("H1")
        header.addWidget(title)
        header.addStretch(1)
        root.addLayout(header)
        
        # Controls
        ctrl = QHBoxLayout()
        
        self.period_combo = QComboBox()
        self.period_combo.addItems([t("last_7_days"), t("last_3_days"), t("last_30_days")])
        ctrl.addWidget(self.period_combo)
        
        self.btn_gen = QPushButton(f"{icon('ai')} {t('generate_advice')}")
        self.btn_gen.setObjectName("PrimaryBtn")
        ctrl.addWidget(self.btn_gen)
        
        ctrl.addStretch(1)
        root.addLayout(ctrl)
        
        # Status
        self.status_label = QLabel("")
        self.status_label.setObjectName("Muted")
        root.addWidget(self.status_label)
        
        # Advice display
        self.advice_text = QTextEdit()
        self.advice_text.setReadOnly(True)
        self.advice_text.setPlaceholderText(t("advice_placeholder"))
        self.advice_text.setMinimumHeight(300)
        root.addWidget(self.advice_text, stretch=1)
        
        # History
        hist_label = QLabel(t("previous_advice"))
        hist_label.setObjectName("Muted")
        root.addWidget(hist_label)
        
        self.history = QTableWidget(0, 3)
        self.history.setHorizontalHeaderLabels([t("period"), t("created"), t("preview")])
        self.history.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.history.setMaximumHeight(180)
        self.history.cellClicked.connect(self.on_history_clicked)
        root.addWidget(self.history)
    
    def get_selected_period_days(self) -> int:
        idx = self.period_combo.currentIndex()
        return [7, 3, 30][idx]
    
    def set_generating(self, is_gen: bool):
        self.is_generating = is_gen
        self.btn_gen.setEnabled(not is_gen)
        self.status_label.setText(t("generating") if is_gen else "")
    
    def set_advice_text(self, text: str):
        self.advice_text.setPlainText(text)
        self.is_generating = False
        self.btn_gen.setEnabled(True)
        self.status_label.setText("")
    
    def set_history(self, rows):
        self.history.setRowCount(len(rows))
        for r, row_data in enumerate(rows):
            if len(row_data) >= 4:
                p1, p2, created, txt = row_data[:4]
            else:
                continue
            
            period = f"{p1} - {p2}"
            preview = (txt[:60] + "...") if len(txt) > 60 else txt
            
            self.history.setItem(r, 0, QTableWidgetItem(period))
            self.history.setItem(r, 1, QTableWidgetItem(created))
            self.history.setItem(r, 2, QTableWidgetItem(preview.replace("\n", " ")))
    
    def on_history_clicked(self, row, col):
        pass


class SettingsPage(QWidget):
    def __init__(self, settings, conn, on_apply, on_theme_change, on_language_change):
        super().__init__()
        self.settings = settings
        self.conn = conn
        self.on_apply = on_apply
        self.on_theme_change = on_theme_change
        self.on_language_change = on_language_change
        
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)
        
        title = QLabel(f"{icon('settings')} {t('settings')}")
        title.setObjectName("H1")
        root.addWidget(title)
        
        tabs = QTabWidget()
        
        # === General Tab ===
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        general_layout.setSpacing(16)
        
        user_group = QGroupBox(f"{icon('app')} {t('general')}")
        user_form = QFormLayout(user_group)
        user_form.setSpacing(10)
        
        self.edit_username = QLineEdit()
        self.edit_username.setPlaceholderText(t("username"))
        user_form.addRow(f"{t('username')}:", self.edit_username)
        
        general_layout.addWidget(user_group)
        
        monitor_group = QGroupBox(f"{icon('activity')} Monitoring")
        monitor_form = QFormLayout(monitor_group)
        monitor_form.setSpacing(10)
        
        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(500, 10000)
        self.spin_interval.setSingleStep(100)
        self.spin_interval.setSuffix(" ms")
        monitor_form.addRow(f"{t('poll_interval')}:", self.spin_interval)
        
        self.spin_idle = QSpinBox()
        self.spin_idle.setRange(30, 3600)
        self.spin_idle.setSingleStep(30)
        self.spin_idle.setSuffix(" s")
        monitor_form.addRow(f"{t('idle_timeout')}:", self.spin_idle)
        
        self.spin_break = QSpinBox()
        self.spin_break.setRange(15, 480)
        self.spin_break.setSingleStep(15)
        self.spin_break.setSuffix(" min")
        monitor_form.addRow(f"{t('break_reminder')}:", self.spin_break)
        
        self.spin_unprod = QSpinBox()
        self.spin_unprod.setRange(10, 90)
        self.spin_unprod.setSingleStep(5)
        self.spin_unprod.setSuffix(" %")
        monitor_form.addRow(f"{t('distraction_threshold')}:", self.spin_unprod)
        
        self.cb_autostart_app = QCheckBox(t("autostart_monitoring"))
        monitor_form.addRow("", self.cb_autostart_app)
        
        self.cb_autostart_win = QCheckBox(t("autostart_windows"))
        monitor_form.addRow("", self.cb_autostart_win)
        
        general_layout.addWidget(monitor_group)
        general_layout.addStretch(1)
        
        tabs.addTab(general_tab, t("general"))
        
        # === Appearance Tab ===
        appearance_tab = QWidget()
        appearance_layout = QVBoxLayout(appearance_tab)
        appearance_layout.setSpacing(16)
        
        theme_group = QGroupBox(f"{icon('settings')} {t('appearance')}")
        theme_form = QFormLayout(theme_group)
        theme_form.setSpacing(10)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([t("dark_theme"), t("light_theme")])
        theme_form.addRow(f"{t('theme')}:", self.theme_combo)
        
        self.language_combo = QComboBox()
        for code, name in LanguageManager.instance().get_available_languages():
            self.language_combo.addItem(name, code)
        theme_form.addRow(f"{t('language')}:", self.language_combo)
        
        appearance_layout.addWidget(theme_group)
        
        window_group = QGroupBox(f"{icon('fullscreen')} Window")
        window_layout = QFormLayout(window_group)
        window_layout.setSpacing(10)
        
        self.window_size_combo = QComboBox()
        self.window_size_combo.addItems([
            t("compact"), t("standard"), t("large"), t("extra_large"), t("fullscreen")
        ])
        window_layout.addRow(f"{t('window_size')}:", self.window_size_combo)
        
        self.cb_remember = QCheckBox(t("remember_window"))
        window_layout.addRow("", self.cb_remember)
        
        self.cb_minimize_to_tray = QCheckBox(t("minimize_to_tray"))
        window_layout.addRow("", self.cb_minimize_to_tray)
        
        self.cb_show_tray_notifications = QCheckBox(t("tray_notifications"))
        window_layout.addRow("", self.cb_show_tray_notifications)
        
        appearance_layout.addWidget(window_group)
        appearance_layout.addStretch(1)
        
        tabs.addTab(appearance_tab, t("appearance"))
        
        # === AI Tab ===
        ai_tab = QWidget()
        ai_layout = QVBoxLayout(ai_tab)
        ai_layout.setSpacing(16)
        
        ai_group = QGroupBox(f"{icon('ai')} {t('ai_settings')}")
        ai_form = QFormLayout(ai_group)
        ai_form.setSpacing(10)
        
        self.edit_apikey = QLineEdit()
        self.edit_apikey.setPlaceholderText(t("api_key_hint"))
        self.edit_apikey.setEchoMode(QLineEdit.Password)
        ai_form.addRow(f"{t('api_key')}:", self.edit_apikey)
        
        api_info = QLabel(f"{icon('info')} {t('api_key_info')}")
        api_info.setObjectName("Muted")
        api_info.setWordWrap(True)
        ai_form.addRow("", api_info)
        
        self.btn_test_api = QPushButton(f"{icon('test')} {t('test_api')}")
        self.btn_test_api.setObjectName("GhostBtn")
        self.btn_test_api.clicked.connect(self.test_api_key)
        ai_form.addRow("", self.btn_test_api)
        
        self.api_status = QLabel("")
        self.api_status.setObjectName("Muted")
        ai_form.addRow("", self.api_status)
        
        ai_layout.addWidget(ai_group)
        ai_layout.addStretch(1)
        
        tabs.addTab(ai_tab, t("ai_settings"))
        
        # === Data Tab ===
        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)
        data_layout.setSpacing(16)
        
        data_group = QGroupBox(f"{icon('disk')} {t('data')}")
        data_form = QVBoxLayout(data_group)
        
        self.btn_export_all = QPushButton(f"{icon('export')} {t('export_all')}")
        self.btn_export_all.setObjectName("GhostBtn")
        self.btn_export_all.clicked.connect(self.export_all_data)
        data_form.addWidget(self.btn_export_all)
        
        self.btn_clear_data = QPushButton(f"{icon('delete')} {t('clear_all')}")
        self.btn_clear_data.setObjectName("DangerBtn")
        self.btn_clear_data.clicked.connect(self.clear_all_data)
        data_form.addWidget(self.btn_clear_data)
        
        data_layout.addWidget(data_group)
        
        about_group = QGroupBox(f"{icon('info')} {t('about')}")
        about_layout = QVBoxLayout(about_group)
        
        about_text = QLabel(f"""
TimeWeaverX {APP_VERSION}

{t('about_text')}

Features:
- Active window tracking
- Productivity analytics
- AI-powered advice
- System monitoring
- Multi-language support

(c) 2024-2025 TimeWeaver Team
        """)
        about_text.setWordWrap(True)
        about_layout.addWidget(about_text)
        
        data_layout.addWidget(about_group)
        data_layout.addStretch(1)
        
        tabs.addTab(data_tab, t("data"))
        
        root.addWidget(tabs, stretch=1)
        
        # Buttons
        btns = QHBoxLayout()
        btns.addStretch(1)
        
        self.btn_reset = QPushButton(f"{icon('reset')} {t('reset')}")
        self.btn_reset.setObjectName("GhostBtn")
        
        self.btn_save = QPushButton(f"{icon('save')} {t('save')}")
        self.btn_save.setObjectName("PrimaryBtn")
        
        btns.addWidget(self.btn_reset)
        btns.addWidget(self.btn_save)
        root.addLayout(btns)
        
        self.btn_save.clicked.connect(self.save)
        self.btn_reset.clicked.connect(self.reset)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        
        self.load()
    
    def load(self):
        self.edit_username.setText(self.settings.value("user/name", "User", type=str))
        self.spin_interval.setValue(self.settings.value("monitor/interval_ms", 1000, type=int))
        self.spin_idle.setValue(self.settings.value("monitor/idle_timeout_sec", 180, type=int))
        self.spin_break.setValue(self.settings.value("rules/break_minutes", 90, type=int))
        self.spin_unprod.setValue(self.settings.value("rules/unprod_percent", 40, type=int))
        self.edit_apikey.setText(self.settings.value("openai/api_key", "", type=str))
        
        self.cb_autostart_app.setChecked(self.settings.value("monitor/autostart_app", False, type=bool))
        self.cb_remember.setChecked(self.settings.value("ui/remember_window", True, type=bool))
        self.cb_minimize_to_tray.setChecked(self.settings.value("ui/minimize_to_tray", True, type=bool))
        self.cb_show_tray_notifications.setChecked(self.settings.value("ui/show_tray_notifications", True, type=bool))
        self.cb_autostart_win.setChecked(get_autostart_enabled())
        
        theme_name = self.settings.value("ui/theme", "dark", type=str)
        self.theme_combo.setCurrentIndex(0 if theme_name == "dark" else 1)
        
        # Load language
        lang_code = self.settings.value("ui/language", "uk", type=str)
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == lang_code:
                self.language_combo.setCurrentIndex(i)
                break
        
        window_preset = self.settings.value("ui/window_preset", "standard", type=str)
        preset_map = {"compact": 0, "standard": 1, "large": 2, "extra_large": 3, "fullscreen": 4}
        idx = preset_map.get(window_preset, 1)
        self.window_size_combo.setCurrentIndex(idx)
    
    def save(self):
        self.settings.setValue("user/name", self.edit_username.text().strip() or "User")
        self.settings.setValue("monitor/interval_ms", int(self.spin_interval.value()))
        self.settings.setValue("monitor/idle_timeout_sec", int(self.spin_idle.value()))
        self.settings.setValue("rules/break_minutes", int(self.spin_break.value()))
        self.settings.setValue("rules/unprod_percent", int(self.spin_unprod.value()))
        self.settings.setValue("openai/api_key", self.edit_apikey.text().strip())
        
        self.settings.setValue("monitor/autostart_app", bool(self.cb_autostart_app.isChecked()))
        self.settings.setValue("ui/remember_window", bool(self.cb_remember.isChecked()))
        self.settings.setValue("ui/minimize_to_tray", bool(self.cb_minimize_to_tray.isChecked()))
        self.settings.setValue("ui/show_tray_notifications", bool(self.cb_show_tray_notifications.isChecked()))
        
        theme_name = "dark" if self.theme_combo.currentIndex() == 0 else "light"
        self.settings.setValue("ui/theme", theme_name)
        
        # Save language
        lang_code = self.language_combo.currentData()
        self.settings.setValue("ui/language", lang_code)
        
        preset_map = {0: "compact", 1: "standard", 2: "large", 3: "extra_large", 4: "fullscreen"}
        self.settings.setValue("ui/window_preset", preset_map.get(self.window_size_combo.currentIndex(), "standard"))
        
        self.settings.sync()
        
        exe_path = sys.executable
        if exe_path.lower().endswith("python.exe") or exe_path.lower().endswith("pythonw.exe"):
            if self.cb_autostart_win.isChecked():
                QMessageBox.warning(self, "TimeWeaver", f"{icon('warning')} {t('autostart_windows')} only works for .exe version")
        else:
            set_autostart(self.cb_autostart_win.isChecked(), exe_path)
        
        self.on_apply()
        QMessageBox.information(self, "TimeWeaver", f"{icon('success')} {t('settings_saved')}")
    
    def reset(self):
        reply = QMessageBox.question(
            self, "TimeWeaver",
            t("confirm_reset"),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.settings.clear()
            self.settings.sync()
            self.load()
            self.on_apply()
            QMessageBox.information(self, "TimeWeaver", f"{icon('success')} {t('settings_reset')}")
    
    def clear_all_data(self):
        reply = QMessageBox.warning(
            self, "TimeWeaver",
            f"{icon('warning')} {t('confirm_clear')}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                cur = self.conn.cursor()
                cur.execute("DELETE FROM activities")
                cur.execute("DELETE FROM ai_advice")
                self.conn.commit()
                QMessageBox.information(self, "TimeWeaver", f"{icon('success')} Data cleared!")
            except Exception as e:
                QMessageBox.critical(self, t("error"), str(e))
    
    def export_all_data(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"timeweaver_full_data_{timestamp}.csv"

        try:
            cur = self.conn.cursor()
            cur.execute("""
                SELECT
                    start_ts,
                    end_ts,
                    duration_sec,
                    app,
                    title,
                    category,
                    score
                FROM activities
                ORDER BY start_ts
            """)
            rows = cur.fetchall()

            if not rows:
                QMessageBox.information(self, t("export_csv"), t("no_export_data"))
                return

            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=';')  # 🔴 КЛЮЧОВЕ ВИПРАВЛЕННЯ
                writer.writerow([
                    "Start",
                    "End",
                    "Duration_sec",
                    "App",
                    "Title",
                    "Category",
                    "Score"
                ])
                writer.writerows(rows)

            QMessageBox.information(
                self,
                t("export_csv"),
                f"{icon('success')} {t('data_exported')} {file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, t("error"), str(e))


    def _on_theme_changed(self, index):
        theme_name = "dark" if index == 0 else "light"
        self.on_theme_change(theme_name)
    
    def _on_language_changed(self, index):
        lang_code = self.language_combo.itemData(index)
        self.on_language_change(lang_code)
    
    def test_api_key(self):
        api_key = self.edit_apikey.text().strip()

        if not api_key:
            self.api_status.setText("⚠️ Enter API key first")
            return

        if not api_key.startswith("sk-"):
            self.api_status.setText("❌ This is not an OpenAI API key")
            return

        self.api_status.setText("ℹ️ Testing OpenAI API key...")
        QApplication.processEvents()

        try:
            client = OpenAI(api_key=api_key)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=5,
            )

            if "ok" in response.choices[0].message.content.lower():
                self.api_status.setText("✅ OpenAI API key is valid")
            else:
                self.api_status.setText("⚠️ API responded, but unexpected output")

        except Exception as e:
            err = str(e).lower()
            if "401" in err or "unauthorized" in err:
                self.api_status.setText("❌ Invalid API key")
            elif "429" in err:
                self.api_status.setText("⚠️ Rate limit exceeded")
            else:
                self.api_status.setText(f"❌ API error: {str(e)[:80]}")

# =========================
# Main App
# =========================
class TimeWeaverApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.monitoring_active = False
        
        self.settings = QSettings("TimeWeaverX", "TimeWeaverX")
        
        # Load and set language first
        lang_code = self.settings.value("ui/language", "uk", type=str)
        LanguageManager.instance().set_language(lang_code)
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(base_dir, DB_NAME)
        ensure_db(self.db_path)
        self.conn = db_connect(self.db_path)
        self.categorizer = Categorizer(self.conn)
        
        self.monitor_on = False
        self.sessions = 0
        self.ticks = 0
        self.current_window = None
        self.current_start = None
        self.last_switch = None
        self.is_flushing = False
        self.was_sleeping = False
        self.last_active_time = datetime.now()
        self.last_break_notify = None
        self.advice_thread = None
        
        self.system_detector = SystemStateDetector(
            idle_timeout_sec=self.settings.value("monitor/idle_timeout_sec", 180, type=int)
        )
        
        self.setWindowTitle(f"TimeWeaverX {APP_VERSION}")
        self.setMinimumSize(900, 600)
        
        self._setup_tray()
        self._build_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll)
        
        self.system_timer = QTimer(self)
        self.system_timer.timeout.connect(self.page_system.update_stats)
        self.system_timer.start(1000)
        
        self.current_theme = self.settings.value("ui/theme", "dark", type=str)
        self.apply_theme()
        
        self._restore_window_state()
        self.apply_settings()
        
        if self.settings.value("monitor/autostart_app", False, type=bool):
            self.start_monitoring()
        
        self.refresh_views()
    
    def _setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("TimeWeaverX")

        icon = self._create_tray_icon()
        self.tray_icon.setIcon(icon)

        tray_menu = QMenu()

        #Запустити моніторинг
        self.tray_start_action = tray_menu.addAction("Запустити моніторинг")
        self.tray_start_action.triggered.connect(self.start_monitoring)

        # Зупинити моніторинг
        self.tray_stop_action = tray_menu.addAction("Зупинити моніторинг")
        self.tray_stop_action.triggered.connect(self.stop_monitoring)

        tray_menu.addSeparator()

        # Показати програму
        show_action = tray_menu.addAction("Показати програму")
        show_action.triggered.connect(self.show_window)

        tray_menu.addSeparator()

        # Вихід
        quit_action = tray_menu.addAction("Вихід")
        quit_action.triggered.connect(self.quit_app)

        self.tray_icon.setContextMenu(tray_menu)

        self.tray_icon.activated.connect(self._on_tray_activated)

        # Показуємо іконку в треї
        self.tray_icon.show()

        # Оновимо стан пунктів меню (наприклад, при запуску програми)
        self.update_tray_menu_state()



        # Показуємо іконку в треї
        self.tray_icon.show()

        # Оновимо стан пунктів меню (наприклад, при запуску програми)
        self.update_tray_menu_state()

    def _create_tray_icon(self):
            """Створює красиву іконку для системного трея"""
            from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QIcon
            from PyQt5.QtCore import Qt
            # Створюємо зображення 64x64 пікселів для чіткості
            size = 64
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)

            # Малюємо синє коло
            painter.setBrush(QColor(30, 136, 229))  # Красивий синій колір (#1E88E5)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(2, 2, size-4, size-4)

            # Малюємо тонку світлу обводку для глибини
            painter.setPen(QColor(100, 181, 246, 100))  # Напівпрозорий світло-синій
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(3, 3, size-6, size-6)

            # Налаштовуємо шрифт для букв "Tw"
            font = QFont("Arial", 24, QFont.Bold)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))  # Білий колір для тексту

            # Малюємо текст "Tw" в центрі
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "Tw")

            painter.end()

            return QIcon(pixmap)

    def update_tray_menu_state(self):
        """Оновлює стан пунктів меню в треї залежно від того, чи запущений моніторинг"""
        if hasattr(self, 'tray_start_action') and hasattr(self, 'tray_stop_action'):
            is_running = self.monitoring_active  # або self.monitor_on — залежно від твоєї змінної
            self.tray_start_action.setEnabled(not is_running)
            self.tray_stop_action.setEnabled(is_running)

    def _on_tray_activated(self, reason):
        """Обробка кліків по іконці в треї"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.tray_icon.show()

    def update_monitoring_ui(self):
        state = self.monitoring_active

        # Dashboard buttons
        if hasattr(self, "page_dashboard"):
            self.page_dashboard.set_button_states(is_running=state)

        # Sidebar status
        if state:
            self.side_monitor_status.setText(f"{icon('on')} {t('status_monitoring')}")
        else:
            self.side_monitor_status.setText(f"{icon('off')} {t('status_stopped')}")
    
    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()
    
    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()
    
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        
        main_lay = QHBoxLayout(central)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)
        
        sidebar = self._build_sidebar()
        main_lay.addWidget(sidebar)
        
        content = QWidget()
        content.setObjectName("Content")
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(0, 0, 0, 0)
        content_lay.setSpacing(0)
        
        self.topbar = self._build_topbar()
        content_lay.addWidget(self.topbar)
        
        self.stack = QStackedWidget()
        content_lay.addWidget(self.stack, stretch=1)
        
        main_lay.addWidget(content, stretch=1)
        
        # Create pages
        self.page_dashboard = DashboardPage(
            on_start=self.start_monitoring,
            on_stop=self.stop_monitoring,
            on_open_reports=lambda: self.nav.setCurrentRow(3),
            on_open_settings=lambda: self.nav.setCurrentRow(5)
        )
        
        self.page_timeline = TimelinePage()
        self.page_system = SystemMonitorPage()
        self.page_reports = ReportsPage(self.conn)
        self.page_insights = InsightsPage(self.settings)
        
        self.page_settings = SettingsPage(
            self.settings,
            self.conn,
            on_apply=self.apply_settings,
            on_theme_change=self.change_theme,
            on_language_change=self.change_language
        )
        
        self.stack.addWidget(self.page_dashboard)  # 0
        self.stack.addWidget(self.page_timeline)   # 1
        self.stack.addWidget(self.page_system)     # 2
        self.stack.addWidget(self.page_reports)    # 3
        self.stack.addWidget(self.page_insights)   # 4
        self.stack.addWidget(self.page_settings)   # 5
        
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        
        self.page_timeline.combo_range.currentIndexChanged.connect(self.refresh_views)
        self.page_reports.combo.currentIndexChanged.connect(self.refresh_views)
        self.page_insights.btn_gen.clicked.connect(self.generate_advice_async)
        
        self._build_toolbar()
        self.setStatusBar(QStatusBar(self))
    
    def _build_sidebar(self) -> QFrame:
        side = QFrame()
        side.setObjectName("Sidebar")
        side.setFixedWidth(220)
        
        lay = QVBoxLayout(side)
        lay.setContentsMargins(12, 14, 12, 12)
        lay.setSpacing(12)
        
        logo = QLabel("TIMEWEAVERX")
        logo.setObjectName("Logo")
        logo.setAlignment(Qt.AlignCenter)  # логотип по центру
        lay.addWidget(logo)
        
        self.nav = QListWidget()
        self.nav.setObjectName("Nav")
        self.nav.setFocusPolicy(Qt.NoFocus)
        
        items = [
            f"{icon('home')} {t('dashboard')}",
            f"{icon('activity')} {t('activity')}",
            f"{icon('system')} {t('system')}",
            f"{icon('reports')} {t('reports')}",
            f"{icon('ai')} {t('insights')}",
            f"{icon('settings')} {t('settings')}"
        ]
        for item_text in items:
            item = QListWidgetItem(item_text)
            item.setTextAlignment(Qt.AlignCenter)
            self.nav.addItem(QListWidgetItem(item_text))
        
        self.nav.setCurrentRow(0)
        lay.addWidget(self.nav, stretch=1)
        
        status_frame = QFrame()
        status_frame.setObjectName("Panel")
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 10, 10, 10)
        status_layout.setSpacing(4)
        
        self.side_status = QLabel(t("status_ready"))
        self.side_status.setObjectName("Muted")
        self.side_status.setWordWrap(True)
        status_layout.addWidget(self.side_status)
        self.side_status.setAlignment(Qt.AlignCenter)
        
        self.side_monitor_status = QLabel(f"{icon('off')} {t('status_stopped')}")
        self.side_monitor_status.setObjectName("Muted")
        self.side_monitor_status.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.side_monitor_status)
        
        lay.addWidget(status_frame)
        
        return side
    
    def _build_topbar(self) -> QFrame:
        top = QFrame()
        top.setObjectName("Topbar")
        
        lay = QHBoxLayout(top)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(10)
        
        self.time_label = QLabel()
        self.time_label.setObjectName("Muted")
        lay.addWidget(self.time_label)
        
        time_timer = QTimer(self)
        time_timer.timeout.connect(self._update_time)
        time_timer.start(1000)
        self._update_time()
        
        lay.addStretch(1)
        
        self.btn_full = QPushButton(icon("fullscreen"))
        self.btn_full.setObjectName("IconBtn")
        self.btn_full.setToolTip("Fullscreen (F11)")
        self.btn_full.clicked.connect(self.toggle_fullscreen)
        lay.addWidget(self.btn_full)
        
        return top
    
    def _update_time(self):
        now = datetime.now()
        self.time_label.setText(now.strftime("%d.%m.%Y | %H:%M:%S"))
    
    def _build_toolbar(self):
        self.act_full = QAction("Fullscreen", self)
        self.act_full.setShortcut(QKeySequence("F11"))
        self.act_full.triggered.connect(self.toggle_fullscreen)
        
        self.act_exit = QAction("Exit", self)
        self.act_exit.setShortcut(QKeySequence.Quit)
        self.act_exit.triggered.connect(self.quit_app)
        
        self.addAction(self.act_full)
        self.addAction(self.act_exit)
    
    def apply_theme(self):
        theme = ThemeManager.get_theme(self.current_theme)
        stylesheet = ThemeManager.generate_stylesheet(theme)
        self.setStyleSheet(stylesheet)
        
        if self.current_theme == "light":
            pg.setConfigOption('background', 'w')
            pg.setConfigOption('foreground', 'k')
        else:
            pg.setConfigOption('background', None)
            pg.setConfigOption('foreground', 'd')
    
    def change_theme(self, theme_name: str):
        self.current_theme = theme_name
        self.settings.setValue("ui/theme", theme_name)
        self.apply_theme()
    
    def change_language(self, lang_code: str):
        LanguageManager.instance().set_language(lang_code)
        self.settings.setValue("ui/language", lang_code)
        # Note: Full UI refresh would require restart or rebuilding all widgets
        # For simplicity, we show a message
        QMessageBox.information(
            self, "TimeWeaver", 
            f"{icon('info')} Language changed. Restart app to apply fully."
        )
    
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def apply_settings(self):
        interval = self.settings.value("monitor/interval_ms", 1000, type=int)
        if self.timer.isActive():
            self.timer.setInterval(interval)
        
        idle_timeout = self.settings.value("monitor/idle_timeout_sec", 180, type=int)
        self.system_detector.idle_timeout_sec = idle_timeout
    
    def start_monitoring(self):
        if self.monitor_on:
            return

        self.monitor_on = True
        self.monitoring_active = True
        self.sessions += 1
        
        poll_interval = self.settings.value("monitor/poll_interval", 1000, type=int)
        self.timer.start(poll_interval)

        self.update_monitoring_ui()
        
        self.current_window = None
        self.current_start = None
        self.last_switch = datetime.now()

        self.page_dashboard.set_button_states(True)
        self.page_dashboard.set_status(
            f"{t('status')}: {t('status_monitoring')}", is_running=True
        )

        self.statusBar().showMessage(t("monitoring_started"), 2000)
        self.update_tray_menu_state()
        
    def stop_monitoring(self):
        if not self.monitor_on:
            return

        self.monitor_on = False
        self.monitoring_active = False
        
        self.timer.stop()
        self._flush_current_segment(force=True)

        self.update_monitoring_ui()

        self.page_dashboard.set_button_states(False)
        self.page_dashboard.set_status(
            f"{t('status')}: {t('status_stopped')}", is_running=False
        )

        self.statusBar().showMessage(t("monitoring_stopped"), 2000)
        self.refresh_views()
        self.update_tray_menu_state()
        
    def _poll(self):
        if not self.monitor_on:
            return
        
        now = datetime.now()
        
        state = self.system_detector.check_state()
        
        if state["time_gap_detected"]:
            print(f"[TimeWeaver] Sleep/gap detected: {state['time_since_last_check']}s gap")
            self._flush_current_segment(force=True)
            self.current_window = None
            self.current_start = None
            self.was_sleeping = True
            return
        
        if state["is_sleeping"] or state["is_locked"]:
            if not self.was_sleeping:
                self._flush_current_segment(force=True)
                self.was_sleeping = True
                self.current_window = None
                self.current_start = None
                print(f"[TimeWeaver] System idle/locked (idle: {state['idle_seconds']}s)")
            return
        else:
            if self.was_sleeping:
                self.was_sleeping = False
                self.last_active_time = now
                print("[TimeWeaver] Resumed from idle/sleep")
        
        self.ticks += 1
        
        try:
            w = get_active_window()
        except Exception:
            return
        
        self.page_dashboard.set_current_activity(w.app, w.title)
        
        if self.current_window is None:
            self.current_window = w
            self.current_start = now
            self.last_switch = now
            return
        
        if (w.app != self.current_window.app) or (w.title != self.current_window.title):
            self._flush_current_segment(force=True)
            self.current_window = w
            self.current_start = now
            self.last_switch = now
        
        if self.ticks % 10 == 0:
            self.refresh_views()
            self._maybe_recommendations()
    
    def _flush_current_segment(self, force: bool):
        if self.is_flushing:
            return
        
        if self.current_window is None or self.current_start is None:
            return
        
        self.is_flushing = True
        
        try:
            end = datetime.now()
            dur = int((end - self.current_start).total_seconds())
            
            if dur <= 0:
                return
            
            app = self.current_window.app
            title = (self.current_window.title or "")[:500]
            category, score = self.categorizer.classify(app, title)
            
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO activities(start_ts,end_ts,duration_sec,app,title,category,score)
                VALUES (?,?,?,?,?,?,?)
            """, (
                self.current_start.strftime("%Y-%m-%d %H:%M:%S"),
                end.strftime("%Y-%m-%d %H:%M:%S"),
                dur,
                app,
                title,
                category,
                score
            ))
            self.conn.commit()
            
        except Exception as e:
            print(f"[TimeWeaver] Error flushing segment: {e}")
        finally:
            self.is_flushing = False
    
    def refresh_views(self):
        try:
            # ===== DASHBOARD (СЬОГОДНІ) =====
            today = QDate.currentDate()
            start, end = dt_range_for(today)

            prod = compute_productivity(self.conn, start, end)
            apps = sum_by_app(self.conn, start, end, limit=1)

            # Загальний час
            total_min = int(prod["total_sec"] // 60) if prod["total_sec"] else 0
            hh = total_min // 60
            mm = total_min % 60
            total_str = f"{hh:02d}:{mm:02d}"

            # Топ програма
            top_app = apps[0][0][:20] if apps else "---"

            # % відволікання і оцінка
            if prod["total_sec"]:
                distraction_pct = compute_distraction_percent(self.conn, start, end)
                unprod_pct = f"{int(distraction_pct)}%"
                score_str = f"{prod['prod_ratio']:.2f}"
            else:
                unprod_pct = "---"
                score_str = "---"

            self.page_dashboard.set_today(
                total_str,
                top_app,
                unprod_pct,
                score_str
            )

            # ===== TIMELINE =====
            day = self.page_timeline.selected_range()
            s, e = dt_range_for(day)
            rows = last_events(self.conn, s, e, limit=200)
            self.page_timeline.set_rows(rows)

            # ===== REPORTS =====
            rs, re = self.page_reports.selected_period()
            app_rows = sum_by_app(self.conn, rs, re, limit=10)
            cat_rows = sum_by_category(self.conn, rs, re)
            prod2 = compute_productivity(self.conn, rs, re)
            self.page_reports.set_top_apps_plot(app_rows) 
            
            #self.page_reports.set_report(app_rows, cat_rows, prod2)

            rows = sum_by_category_and_app(self.conn, rs, re)
            self.page_reports.set_category_breakdown(rows, prod2["total_sec"])

            # ===== AI INSIGHTS =====
            cur = self.conn.cursor()
            cur.execute("""
                SELECT period_start, period_end, created_ts, advice_text
                FROM ai_advice
                ORDER BY id DESC
                LIMIT 10
            """)
            hist = cur.fetchall()
            self.page_insights.set_history(hist)

        except Exception as e:
            print(f"[TimeWeaver] Error refreshing views: {e}")

    
    def _maybe_recommendations(self):
        try:
            break_min = self.settings.value("rules/break_minutes", 90, type=int)
            unprod_thr = self.settings.value("rules/unprod_percent", 40, type=int)
            show_notifications = self.settings.value("ui/show_tray_notifications", True, type=bool)
            
            if self.last_switch is not None:
                mins = int((datetime.now() - self.last_switch).total_seconds() // 60)
                
                if mins >= break_min:
                    if self.last_break_notify is None or (datetime.now() - self.last_break_notify).total_seconds() > 600:
                        if show_notifications:
                            self.tray_icon.showMessage(
                                f"TimeWeaver - {t('break_reminder')}",
                                t("break_reminder_msg").format(mins),
                                QSystemTrayIcon.Information,
                                5000
                            )
                        self.last_break_notify = datetime.now()
            
            start, end = dt_range_for(QDate.currentDate())
            prod = compute_productivity(self.conn, start, end)
            
            if prod["total_sec"] >= 30 * 60:
                unprod_pct = int(prod["unprod_ratio"] * 100)
                if unprod_pct >= unprod_thr:
                    self.statusBar().showMessage(
                        f"{icon('warning')} {t('distractions')}: {unprod_pct}% (threshold {unprod_thr}%)", 4000
                    )
        except Exception as e:
            print(f"[TimeWeaver] Error in recommendations: {e}")
    
    def generate_advice_async(self):
        if self.page_insights.is_generating:
            return
        
        self.page_insights.set_generating(True)
        
        try:
            days = self.page_insights.get_selected_period_days()
            today = datetime.now().date()
            end = datetime(today.year, today.month, today.day) + timedelta(days=1)
            start = end - timedelta(days=days)
            
            apps = sum_by_app(self.conn, start, end, limit=10)
            prod = compute_productivity(self.conn, start, end)
            cats = sum_by_category(self.conn, start, end)
            
            if not apps or prod["total_sec"] < 300:
                self.page_insights.set_advice_text(
                    f"{icon('warning')} {t('no_data')}\n\n"
                    f"{t('continue')}"
                )
                return
            
            data = {
                "total_sec": prod["total_sec"],
                "prod_ratio": prod["prod_ratio"],
                "unprod_ratio": prod["unprod_ratio"],
                "apps": apps,
                "categories": cats,
                "period_start": start.strftime("%Y-%m-%d"),
                "period_end": end.strftime("%Y-%m-%d"),
            }
            
            api_key = self.settings.value("openai/api_key", "")
            current_lang = LanguageManager.instance().get_language()
            
            self.advice_thread = AIAdviceGenerator(data, api_key, current_lang)
            self.advice_thread.finished.connect(self._on_advice_generated)
            self.advice_thread.error.connect(self._on_advice_error)
            self.advice_thread.start()
            
        except Exception as e:
            self.page_insights.set_advice_text(f"{icon('error')} {t('error')}: {str(e)}")
    
    def _on_advice_generated(self, advice: str):
        try:
            days = self.page_insights.get_selected_period_days()
            today = datetime.now().date()
            end = datetime(today.year, today.month, today.day) + timedelta(days=1)
            start = end - timedelta(days=days)
            
            advice_hash = hashlib.md5(advice.encode()).hexdigest()[:16]
            
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO ai_advice(period_start, period_end, advice_text, created_ts, advice_hash)
                VALUES (?,?,?,?,?)
            """, (
                start.strftime("%Y-%m-%d"),
                end.strftime("%Y-%m-%d"),
                advice,
                now_ts(),
                advice_hash
            ))
            self.conn.commit()
            
            self.page_insights.set_advice_text(advice)
            self.refresh_views()
            
            self.statusBar().showMessage(f"{icon('success')} Advice generated", 3000)
            
        except Exception as e:
            self.page_insights.set_advice_text(f"{icon('error')} Save error: {str(e)}")
    
    def _on_advice_error(self, error: str):
        self.page_insights.set_advice_text(f"{icon('error')} {t('error')}: {error}")
    
    def _restore_window_state(self):
        remember = self.settings.value("ui/remember_window", True, type=bool)
        
        if remember:
            geo = self.settings.value("ui/geometry")
            state = self.settings.value("ui/windowState")
            
            if geo is not None:
                self.restoreGeometry(geo)
            if state is not None:
                self.restoreState(state)
        else:
            preset = self.settings.value("ui/window_preset", "standard", type=str)
            size = WINDOW_PRESETS.get(preset)
            if size:
                self.resize(size[0], size[1])
    
    def closeEvent(self, event):
        minimize_to_tray = self.settings.value("ui/minimize_to_tray", True, type=bool)
        
        if minimize_to_tray:
            event.ignore()
            self.hide()
            
            if self.settings.value("ui/show_tray_notifications", True, type=bool):
                self.tray_icon.showMessage(
                    "TimeWeaver",
                    t("minimized_to_tray"),
                    QSystemTrayIcon.Information,
                    2000
                )
        else:
            self._save_window_state()
            self.quit_app()
    
    def _save_window_state(self):
        if self.settings.value("ui/remember_window", True, type=bool):
            self.settings.setValue("ui/geometry", self.saveGeometry())
            self.settings.setValue("ui/windowState", self.saveState())
            self.settings.sync()
    
    def quit_app(self):
        self._save_window_state()
        self.stop_monitoring()
        self.tray_icon.hide()
        self.conn.close()
        QApplication.quit()

def ensure_single_instance():
    mutex_name = "Global\\TimeWeaverX_SingleInstance"

    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, False, mutex_name)

    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        from PyQt5.QtWidgets import QApplication, QMessageBox
        app = QApplication(sys.argv)
        QMessageBox.warning(
            None,
            "TimeWeaver X",
            "Програма вже запущена.\nПеревірте трей."
        )
        sys.exit(0)

    return mutex


# =========================
# Main
# ====  
if __name__ == "__main__":
    mutex = ensure_single_instance()   # ⬅️ ПЕРШЕ!
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    w = TimeWeaverApp()
    w.show()

    sys.exit(app.exec())



