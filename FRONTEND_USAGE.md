# Инструкция по использованию фронтенда EduAnalytics

## 🌐 Доступность

- **Фронтенд:** http://localhost:4028
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## 🔐 Авторизация

### Способ 1: Через страницу входа
1. Перейдите на http://localhost:4028/login
2. Введите данные:
   - **Username:** admin@example.com
   - **Password:** admin
3. После входа токен сохранится автоматически

### Способ 2: Debug токен (для разработчиков)
1. Откройте http://localhost:4028/debug-login.html
2. Нажмите "🔑 Установить токен авторизации"
3. Нажмите "📢 Открыть настройки напоминаний"

### Способ 3: Консоль браузера
```javascript
// Установить токен вручную
localStorage.setItem('accessToken', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBleGFtcGxlLmNvbSIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc1NTI1NDMyOX0.uxd21VhrOcCrvnhSr0pvGjLOU8uCM_D9Zxscr0hlMyI');

// Проверить токен
console.log('Token:', localStorage.getItem('accessToken'));

// Перейти к напоминаниям
window.location.href = '/reminders';
```

## 📱 Основные страницы

### 1. Панель управления
- **URL:** http://localhost:4028/
- **Описание:** Главная страница с обзором системы

### 2. Настройки напоминаний
- **URL:** http://localhost:4028/reminders
- **Требует:** Авторизацию
- **Функции:**
  - Настройка предстоящих занятий
  - Настройка изменений расписания
  - Настройка дедлайнов заданий
  - Настройка отмены занятий
  - Тестирование напоминаний

### 3. Расписание
- **URL:** http://localhost:4028/schedule
- **Требует:** Авторизацию
- **Функции:**
  - Просмотр расписания (список/календарь)
  - Создание/редактирование занятий
  - Фильтрация по курсам и преподавателям

### 4. Teacher Dashboard
- **URL:** http://localhost:4028/teacher-dashboard
- **Требует:** Роль teacher/admin
- **Функции:**
  - Обзор курсов и студентов
  - Аналитика успеваемости
  - Управление заданиями

### 5. Student Dashboard
- **URL:** http://localhost:4028/student-dashboard
- **Требует:** Роль student
- **Функции:**
  - Личная аналитика
  - Предстоящие задания
  - Календарь занятий

## 🛠️ Устранение неполадок

### Ошибка "Необходима авторизация"
1. Проверьте наличие токена: `localStorage.getItem('accessToken')`
2. Если токена нет - войдите через /login
3. Если токен есть, но ошибка остается - токен истек, войдите заново

### Ошибка "Ошибка подключения к серверу"
1. Проверьте работу API: http://localhost:8000
2. Проверьте Docker контейнеры: `docker compose ps`
3. Перезапустите API: `docker compose restart api`

### Страница не загружается
1. Проверьте работу фронтенда: http://localhost:4028
2. Проверьте консоль браузера на ошибки
3. Перезапустите фронтенд: `npm start`

## 🧪 Тестовые данные

### Пользователи
- **Admin:** admin@example.com / admin
- **Students:** Генерируются автоматически

### Курсы и занятия
- Созданы тестовые курсы и занятия
- Настроены автоматические напоминания

## 🔧 Для разработчиков

### Проверка токена
```javascript
// В консоли браузера
const token = localStorage.getItem('accessToken');
if (token) {
  fetch('http://localhost:8000/api/reminders/settings', {
    headers: { 'Authorization': `Bearer ${token}` }
  })
  .then(r => r.json())
  .then(data => console.log('Settings:', data));
}
```

### Быстрый вход
```javascript
// Установить токен и перейти к напоминаниям
localStorage.setItem('accessToken', 'YOUR_TOKEN_HERE');
window.location.href = '/reminders';
```
