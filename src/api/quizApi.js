// src/api/quizApi.js

const API_BASE_URL = 'http://localhost:8000/api';

// Utility function для обработки ответов API
const handleResponse = async (response) => {
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
  return await response.json();
};

// Utility function для получения токена
const getToken = () => {
  return localStorage.getItem('accessToken') || localStorage.getItem('token');
};

// Utility function для создания заголовков
const getHeaders = () => {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

// Quiz API methods
export const quizApi = {
  // Получить все квизы курса
  getQuizzesByCourse: async (courseId) => {
    const response = await fetch(`${API_BASE_URL}/courses/${courseId}/quizzes`, {
      headers: getHeaders()
    });
    return handleResponse(response);
  },

  // Получить квиз по ID
  getQuiz: async (quizId) => {
    const response = await fetch(`${API_BASE_URL}/quizzes/${quizId}`, {
      headers: getHeaders()
    });
    return handleResponse(response);
  },

  // Создать новый квиз
  createQuiz: async (quizData) => {
    const response = await fetch(`${API_BASE_URL}/quizzes/`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(quizData)
    });
    return handleResponse(response);
  },

  // Обновить квиз
  updateQuiz: async (quizId, quizData) => {
    const response = await fetch(`${API_BASE_URL}/quizzes/${quizId}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify(quizData)
    });
    return handleResponse(response);
  },

  // Удалить квиз
  deleteQuiz: async (quizId) => {
    const response = await fetch(`${API_BASE_URL}/quizzes/${quizId}`, {
      method: 'DELETE',
      headers: getHeaders()
    });
    return handleResponse(response);
  },

  // Обновить вопрос
  updateQuestion: async (questionId, questionData) => {
    const response = await fetch(`${API_BASE_URL}/questions/${questionId}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify(questionData)
    });
    return handleResponse(response);
  },

  // Удалить вопрос
  deleteQuestion: async (questionId) => {
    const response = await fetch(`${API_BASE_URL}/questions/${questionId}`, {
      method: 'DELETE',
      headers: getHeaders()
    });
    return handleResponse(response);
  },

  // Добавить вопрос к квизу
  addQuestion: async (quizId, questionData) => {
    const response = await fetch(`${API_BASE_URL}/quizzes/${quizId}/questions/`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ ...questionData, quiz_id: quizId })
    });
    return handleResponse(response);
  },

  // Получить вопросы квиза
  getQuestions: async (quizId) => {
    const response = await fetch(`${API_BASE_URL}/quizzes/${quizId}/questions`, {
      headers: getHeaders()
    });
    return handleResponse(response);
  },

  // Начать попытку прохождения квиза
  startAttempt: async (quizId) => {
    const response = await fetch(`${API_BASE_URL}/quizzes/${quizId}/attempts/`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ quiz_id: quizId })
    });
    return handleResponse(response);
  },

  // Отправить ответы
  submitAttempt: async (attemptId, answers) => {
    const response = await fetch(`${API_BASE_URL}/quizzes/${attemptId}/submit/`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(answers)
    });
    return handleResponse(response);
  },

  // Получить результаты попытки
  getAttemptResults: async (attemptId) => {
    const response = await fetch(`${API_BASE_URL}/quizzes/attempts/${attemptId}/results`, {
      headers: getHeaders()
    });
    return handleResponse(response);
  },

  // Получить историю попыток студента
  getStudentAttempts: async (studentId, quizId = null) => {
    const url = quizId 
      ? `${API_BASE_URL}/students/${studentId}/attempts?quiz_id=${quizId}`
      : `${API_BASE_URL}/students/${studentId}/attempts`;
    
    const response = await fetch(url, {
      headers: getHeaders()
    });
    return handleResponse(response);
  },

  // Получить статистику квиза для преподавателя
  getQuizStatistics: async (quizId) => {
    const response = await fetch(`${API_BASE_URL}/quizzes/${quizId}/statistics`, {
      headers: getHeaders()
    });
    return handleResponse(response);
  }
};

export default quizApi;
