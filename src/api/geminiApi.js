// src/api/geminiApi.js

import { GoogleGenerativeAI } from "@google/generative-ai";

// 1. Получаем ваш API ключ из безопасного .env файла
const apiKey = import.meta.env.VITE_GEMINI_API_KEY;

// Проверка, что ключ был добавлен в .env
if (!apiKey) {
    throw new Error("VITE_GEMINI_API_KEY не найден в файле .env. Пожалуйста, добавьте его.");
}

// 2. Инициализируем модель Gemini
const genAI = new GoogleGenerativeAI(apiKey);
const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

// 3. Создаем функцию для отправки запроса и получения ответа
export async function getGeminiChatResponse(userInput) {
    try {
        console.log("Отправка запроса в Gemini:", userInput);

        const result = await model.generateContent(userInput);
        const response = await result.response;
        const text = response.text();

        console.log("Ответ от Gemini получен.");
        return text;
    } catch (error) {
        console.error("Ошибка при обращении к Gemini API:", error);
        return "К сожалению, произошла ошибка при обращении к AI. Пожалуйста, проверьте консоль на наличие ошибок или правильность вашего API ключа.";
    }
}