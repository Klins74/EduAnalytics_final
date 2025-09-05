"""
Email templating service with i18n support.

Provides template management, rendering, and localization for email notifications.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
from jinja2.exceptions import TemplateNotFound
import yaml

logger = logging.getLogger(__name__)


class EmailTemplateService:
    """Service for managing and rendering email templates."""
    
    def __init__(self, templates_dir: str = "templates/email", default_locale: str = "en"):
        self.templates_dir = Path(templates_dir)
        self.default_locale = default_locale
        self.supported_locales = ["en", "ru", "kz"]
        
        # Create Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Load translations
        self.translations = self._load_translations()
        
        # Setup custom filters
        self._setup_filters()
    
    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """Load translation files for email templates."""
        translations = {}
        
        for locale in self.supported_locales:
            translation_file = self.templates_dir / "i18n" / f"{locale}.yml"
            try:
                if translation_file.exists():
                    with open(translation_file, 'r', encoding='utf-8') as f:
                        translations[locale] = yaml.safe_load(f) or {}
                else:
                    translations[locale] = {}
                    logger.warning(f"Translation file not found: {translation_file}")
            except Exception as e:
                logger.error(f"Failed to load translations for {locale}: {e}")
                translations[locale] = {}
        
        return translations
    
    def _setup_filters(self):
        """Setup custom Jinja2 filters for templates."""
        
        def translate(key: str, locale: str = None) -> str:
            """Translation filter for templates."""
            if not locale:
                locale = self.default_locale
            
            return self.translations.get(locale, {}).get(key, key)
        
        def format_date(date_obj, format_str: str = "%Y-%m-%d", locale: str = None):
            """Date formatting filter."""
            if not date_obj:
                return ""
            
            try:
                if hasattr(date_obj, 'strftime'):
                    return date_obj.strftime(format_str)
                return str(date_obj)
            except Exception:
                return str(date_obj)
        
        def format_grade(score: float, max_score: float = 100.0) -> str:
            """Grade formatting filter."""
            if score is None:
                return "N/A"
            
            try:
                percentage = (score / max_score) * 100
                return f"{percentage:.1f}%"
            except (TypeError, ZeroDivisionError):
                return str(score)
        
        # Register filters
        self.env.filters['t'] = translate
        self.env.filters['translate'] = translate
        self.env.filters['format_date'] = format_date
        self.env.filters['format_grade'] = format_grade
    
    def render_template(
        self, 
        template_name: str, 
        context: Dict[str, Any], 
        locale: str = None
    ) -> Dict[str, str]:
        """
        Render email template with context.
        
        Args:
            template_name: Name of the template (without extension)
            context: Template context variables
            locale: Target locale for translations
            
        Returns:
            Dict with 'subject', 'html', and 'text' keys
        """
        if not locale:
            locale = self.default_locale
        
        # Add locale and translation function to context
        context = {
            **context,
            'locale': locale,
            't': lambda key: self.translations.get(locale, {}).get(key, key)
        }
        
        result = {}
        
        try:
            # Render HTML template
            html_template_path = f"{locale}/{template_name}.html"
            try:
                html_template = self.env.get_template(html_template_path)
                result['html'] = html_template.render(context)
            except TemplateNotFound:
                # Fallback to default locale
                if locale != self.default_locale:
                    html_template_path = f"{self.default_locale}/{template_name}.html"
                    html_template = self.env.get_template(html_template_path)
                    result['html'] = html_template.render(context)
                else:
                    raise
            
            # Render text template
            text_template_path = f"{locale}/{template_name}.txt"
            try:
                text_template = self.env.get_template(text_template_path)
                result['text'] = text_template.render(context)
            except TemplateNotFound:
                # Fallback to default locale
                if locale != self.default_locale:
                    text_template_path = f"{self.default_locale}/{template_name}.txt"
                    text_template = self.env.get_template(text_template_path)
                    result['text'] = text_template.render(context)
                else:
                    # Generate plain text from HTML if no text template
                    from html2text import html2text
                    result['text'] = html2text(result.get('html', ''))
            
            # Render subject template
            subject_template_path = f"{locale}/{template_name}_subject.txt"
            try:
                subject_template = self.env.get_template(subject_template_path)
                result['subject'] = subject_template.render(context).strip()
            except TemplateNotFound:
                # Fallback to default locale
                if locale != self.default_locale:
                    subject_template_path = f"{self.default_locale}/{template_name}_subject.txt"
                    subject_template = self.env.get_template(subject_template_path)
                    result['subject'] = subject_template.render(context).strip()
                else:
                    # Default subject
                    result['subject'] = self.translations.get(locale, {}).get(
                        f"{template_name}_subject", 
                        f"Notification - {template_name}"
                    )
            
        except Exception as e:
            logger.error(f"Failed to render template {template_name} for locale {locale}: {e}")
            raise
        
        return result
    
    def get_available_templates(self) -> List[str]:
        """Get list of available email templates."""
        templates = set()
        
        for locale_dir in self.templates_dir.iterdir():
            if locale_dir.is_dir() and locale_dir.name in self.supported_locales:
                for template_file in locale_dir.glob("*.html"):
                    templates.add(template_file.stem)
        
        return sorted(list(templates))
    
    def validate_template(self, template_name: str, locale: str = None) -> bool:
        """Validate that a template exists and can be rendered."""
        if not locale:
            locale = self.default_locale
        
        try:
            # Check if HTML template exists
            html_path = f"{locale}/{template_name}.html"
            self.env.get_template(html_path)
            return True
        except TemplateNotFound:
            # Check fallback locale
            if locale != self.default_locale:
                try:
                    html_path = f"{self.default_locale}/{template_name}.html"
                    self.env.get_template(html_path)
                    return True
                except TemplateNotFound:
                    pass
            return False


# Email template types
class EmailTemplates:
    """Constants for email template names."""
    
    # Assignment notifications
    ASSIGNMENT_CREATED = "assignment_created"
    ASSIGNMENT_DUE_SOON = "assignment_due_soon"
    ASSIGNMENT_OVERDUE = "assignment_overdue"
    
    # Grade notifications
    GRADE_POSTED = "grade_posted"
    GRADE_UPDATED = "grade_updated"
    
    # Course notifications
    COURSE_ENROLLMENT = "course_enrollment"
    COURSE_ANNOUNCEMENT = "course_announcement"
    
    # System notifications
    WELCOME = "welcome"
    PASSWORD_RESET = "password_reset"
    ACCOUNT_LOCKED = "account_locked"
    
    # Reminder notifications
    DEADLINE_REMINDER = "deadline_reminder"
    WEEKLY_DIGEST = "weekly_digest"
    
    # Canvas integration
    CANVAS_SYNC_ERROR = "canvas_sync_error"
    CANVAS_DATA_UPDATED = "canvas_data_updated"


# Global template service instance
_template_service: Optional[EmailTemplateService] = None


def get_email_template_service() -> EmailTemplateService:
    """Get the global email template service instance."""
    global _template_service
    
    if _template_service is None:
        # Initialize with default settings
        templates_dir = os.getenv("EMAIL_TEMPLATES_DIR", "templates/email")
        default_locale = os.getenv("DEFAULT_LOCALE", "en")
        _template_service = EmailTemplateService(templates_dir, default_locale)
    
    return _template_service


def render_email_template(
    template_name: str, 
    context: Dict[str, Any], 
    locale: str = None
) -> Dict[str, str]:
    """
    Convenience function to render email template.
    
    Args:
        template_name: Name of the template
        context: Template context variables
        locale: Target locale
        
    Returns:
        Dict with rendered email content
    """
    service = get_email_template_service()
    return service.render_template(template_name, context, locale)
