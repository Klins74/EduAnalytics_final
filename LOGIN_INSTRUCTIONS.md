# 🔐 Инструкция по входу в EduAnalytics

## Проблема с входом РЕШЕНА!

### ✅ Правильные данные для входа:

**URL для входа:** http://localhost:4028/login

**Данные для входа:**
- **Email:** `admin@example.com`
- **Пароль:** `admin`

## 🚨 ВАЖНО: Не используйте admin@eduanalytics.ru!

На странице входа в поле Email введите точно: **admin@example.com**

## 🔧 Альтернативные способы входа:

### Способ 1: Debug страница
1. Откройте http://localhost:4028/debug-login.html
2. Нажмите "🔑 Установить токен авторизации"
3. Нажмите "📢 Открыть настройки напоминаний"

### Способ 2: Консоль браузера
1. Откройте консоль браузера (F12)
2. Вставьте код:
```javascript
localStorage.setItem('accessToken', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBleGFtcGxlLmNvbSIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc1NTI1NDY4MX0.XQgnRbNZHX0m5DefTojqZkKbwvcaR6jOK-7HRhueMuw');
window.location.href = '/reminders';
```

## 📱 После успешного входа:

После входа вы сможете использовать:
- 📢 **Настройки напоминаний:** /reminders
- 📅 **Расписание:** /schedule  
- 🎓 **Teacher Dashboard:** /teacher-dashboard
- 👨‍🎓 **Student Dashboard:** /student-dashboard
- 🤖 **AI-помощник:** /ai

## 🛠️ Устранение проблем:

### Если все еще не работает:
1. Очистите кэш браузера (Ctrl+Shift+Delete)
2. Попробуйте другой браузер
3. Проверьте что API работает: http://localhost:8000

### Проверка статуса сервисов:
```bash
docker compose ps
```

Все контейнеры должны иметь статус "Up".

## ✅ Тестовая авторизация работает!

API сервер корректно авторизует пользователя `admin@example.com` с паролем `admin`.
