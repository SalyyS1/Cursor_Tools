"""
Hệ thống đa ngôn ngữ (i18n) cho AugmentCode Unlimited
Hỗ trợ tiếng Việt hoàn toàn
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Thư mục chứa translation files
LOCALES_DIR = Path(__file__).parent.parent / "locales"
DEFAULT_LANGUAGE = "vi"  # Mặc định tiếng Việt


class Translator:
    """Quản lý dịch thuật và đa ngôn ngữ"""
    
    def __init__(self, language: str = DEFAULT_LANGUAGE):
        """
        Khởi tạo translator
        
        Args:
            language: Mã ngôn ngữ (vi, en, ...)
        """
        self.language = language
        self.translations: Dict[str, Any] = {}
        self._load_translations()
    
    def _load_translations(self) -> None:
        """Tải file dịch thuật"""
        locale_file = LOCALES_DIR / f"{self.language}.json"
        
        if not locale_file.exists():
            logger.warning(f"Không tìm thấy file dịch thuật: {locale_file}")
            logger.warning("Sử dụng fallback - trả về key gốc")
            return
        
        try:
            with open(locale_file, 'r', encoding='utf-8-sig') as f:
                self.translations = json.load(f)
            logger.info(f"Đã tải dịch thuật: {self.language}")
        except Exception as e:
            logger.error(f"Lỗi khi tải dịch thuật: {e}")
            self.translations = {}
    
    def get(self, translation_key: str, default: Optional[str] = None, **kwargs) -> str:
        """
        Lấy bản dịch theo key
        
        Args:
            translation_key: Key dịch thuật (có thể dùng dot notation: "ui.button_start")
            default: Giá trị mặc định nếu không tìm thấy
            **kwargs: Các tham số để format string (ví dụ: path="...", key="...")
        
        Returns:
            Chuỗi đã dịch
        """
        # Tách key theo dot notation
        keys = translation_key.split('.')
        value = self.translations
        
        try:
            for k in keys:
                value = value[k]
            
            # Format string nếu có kwargs
            if kwargs and isinstance(value, str):
                try:
                    return value.format(**kwargs)
                except KeyError:
                    logger.warning(f"Thiếu tham số format cho key: {translation_key}")
                    return value
            
            return str(value) if value is not None else (default or translation_key)
        
        except (KeyError, TypeError):
            # Nếu không tìm thấy, trả về default hoặc key gốc
            if default:
                return default.format(**kwargs) if kwargs else default
            logger.debug(f"Không tìm thấy key: {translation_key}")
            return translation_key
    
    def __call__(self, translation_key: str, default: Optional[str] = None, **kwargs) -> str:
        """Alias cho get() để dùng như function"""
        return self.get(translation_key, default, **kwargs)


# Global translator instance (mặc định tiếng Việt)
_translator: Optional[Translator] = None


def init_translator(language: str = DEFAULT_LANGUAGE) -> None:
    """
    Khởi tạo global translator
    
    Args:
        language: Mã ngôn ngữ
    """
    global _translator
    _translator = Translator(language)
    logger.info(f"Đã khởi tạo translator với ngôn ngữ: {language}")


def t(translation_key: str, default: Optional[str] = None, **kwargs) -> str:
    """
    Hàm helper để dịch nhanh
    
    Args:
        translation_key: Key dịch thuật
        default: Giá trị mặc định
        **kwargs: Tham số format (có thể dùng key="..." để format trong translation string)
    
    Returns:
        Chuỗi đã dịch
    """
    global _translator
    if _translator is None:
        init_translator()
    return _translator.get(translation_key, default, **kwargs)


# Khởi tạo mặc định khi import
init_translator(DEFAULT_LANGUAGE)

