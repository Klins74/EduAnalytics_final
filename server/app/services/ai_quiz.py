from app.services.ai_service import AIService
from typing import List, Dict
import json

ai_service = AIService()

async def generate_questions(course_id: int, num_questions: int, topic: str) -> List[Dict]:
    prompt = f"Generate {num_questions} quiz questions on topic '{topic}' for course {course_id}. Include mix of multiple choice, true/false, essay. Format as JSON list with fields: text, type, options (for multiple), correct_answer, points."
    response = ai_service.generate_reply(prompt)
    try:
        questions = json.loads(response)
        return questions
    except:
        return []  # Error handling

async def auto_grade_answer(question_text: str, answer_text: str, max_points: float) -> Dict:
    prompt = f"Grade this answer: '{answer_text}' for question: '{question_text}'. Provide score (0 to {max_points}) and feedback as JSON: {{'score': float, 'feedback': str}}."
    response = ai_service.generate_reply(prompt)
    try:
        result = json.loads(response)
        return result
    except:
        return {'score': 0.0, 'feedback': 'Error in AI grading'}

