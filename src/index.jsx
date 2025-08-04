// src/index.jsx

import React from "react";
import { createRoot } from "react-dom/client";
import * as Sentry from "@sentry/react";
import App from "./App";
import "./styles/tailwind.css";
import "./styles/index.css";

// Инициализация Sentry с использованием переменных окружения
Sentry.init({ 
  dsn: import.meta.env.VITE_SENTRY_DSN || "https://f09245d157daea3c9f5b5cc898e1dd44@o4509786424541184.ingest.de.sentry.io/4509786426310736", 
  environment: import.meta.env.VITE_SENTRY_ENVIRONMENT || "development",
  // Setting this option to true will send default PII data to Sentry. 
  // For example, automatic IP address collection on events 
  sendDefaultPii: true,
  // Включаем отслеживание производительности
  tracesSampleRate: parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || "1.0"),
}); 

const container = document.getElementById("root");
const root = createRoot(container);

root.render(<App />);