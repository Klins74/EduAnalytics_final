// src/index.jsx

import React from "react";
import { createRoot } from "react-dom/client";
import * as Sentry from "@sentry/react";
import App from "./App";
import "./styles/tailwind.css";
import "./styles/index.css";
import "./i18n";

// Инициализация Sentry с использованием переменных окружения
Sentry.init({ 
  dsn: import.meta.env.VITE_SENTRY_DSN || "",
  environment: import.meta.env.VITE_SENTRY_ENVIRONMENT || "development",
  // Без передачи PII по умолчанию
  sendDefaultPii: false,
  // Сэмплирование трасс: 0.1 по умолчанию (можно переопределить через env)
  tracesSampleRate: parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || "0.1"),
  // Скрамблинг и фильтрация потенциально чувствительных данных
  beforeSend(event) {
    if (event.request) {
      // Удаляем cookies и query string
      if (event.request.headers) {
        delete event.request.headers["cookie"];
        delete event.request.headers["authorization"];
      }
      if (event.request.url) {
        try {
          const url = new URL(event.request.url);
          url.search = "";
          event.request.url = url.toString();
        } catch {}
      }
    }
    return event;
  },
}); 

const container = document.getElementById("root");
const root = createRoot(container);

root.render(<App />);