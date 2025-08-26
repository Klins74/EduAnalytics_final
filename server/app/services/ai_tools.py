from __future__ import annotations

from datetime import date
from typing import Optional, Dict, Any, List

import httpx
from app.services.ai_authorization import is_allowed
import asyncio


class AiToolRegistry:
    """Сбор краткого контекста из существующих API по переданному scope/ids."""

    def __init__(self, api_base: str = "http://localhost:8000") -> None:
        self.api_base = api_base.rstrip("/")

    async def gather_context(
        self,
        auth_header: Optional[str],
        role: Optional[str] = None,
        scope: Optional[str] = None,
        student_id: Optional[int] = None,
        course_id: Optional[int] = None,
    ) -> str:
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header

        bullets: List[str] = []

        async def _get(client: httpx.AsyncClient, url: str, *, headers: Dict[str, str], params: Dict[str, Any] | None = None) -> httpx.Response | None:
            # простой backoff: до 2 повторов
            delays = [0.0, 0.3]
            last_exc: Exception | None = None
            for d in delays:
                if d:
                    await asyncio.sleep(d)
                try:
                    return await client.get(url, headers=headers, params=params)
                except Exception as e:
                    last_exc = e
            return None

        async with httpx.AsyncClient(timeout=15.0) as client:
            # Курс
            if course_id and is_allowed(role, "read_course_analytics"):
                try:
                    r = await _get(client, f"{self.api_base}/api/analytics/courses/{course_id}/overview", headers=headers)
                    if r and r.status_code == 200:
                        data = r.json() or {}
                        ov = data.get("overview", data)
                        total_assignments = ov.get("total_assignments")
                        avg_grade = ov.get("average_grade")
                        bullets.append(f"Курс #{course_id}: заданий={total_assignments}, средняя={avg_grade}")
                except Exception:
                    pass
                # Тренды по курсу (краткая динамика)
                try:
                    r = await _get(client, f"{self.api_base}/api/analytics/courses/{course_id}/trends", headers=headers, params={"days": 30, "bucket": "week"})
                    if r and r.status_code == 200:
                        data = r.json() or {}
                        series = data.get("series", [])
                        if len(series) >= 2:
                            first = series[0].get("average_grade") or 0
                            last = series[-1].get("average_grade") or 0
                            delta = round((last - first), 2)
                            bullets.append(f"Тренд курса: средняя {last} ({'+' if delta>=0 else ''}{delta} за период)")
                except Exception:
                    pass

            # Студент
            if student_id and is_allowed(role, "read_student_analytics"):
                try:
                    r = await _get(client, f"{self.api_base}/api/analytics/students/{student_id}/performance", headers=headers)
                    if r and r.status_code == 200:
                        data = r.json() or {}
                        perf = data.get("overall_performance", {})
                        courses_count = perf.get("courses_count")
                        total_submissions = perf.get("total_submissions")
                        avg_grade = perf.get("overall_average_grade")
                        bullets.append(
                            f"Студент #{student_id}: курсов={courses_count}, сдач={total_submissions}, средняя={avg_grade}"
                        )
                except Exception:
                    pass
                # Тренды по студенту
                try:
                    r = await _get(client, f"{self.api_base}/api/analytics/students/{student_id}/trends", headers=headers, params={"days": 30, "bucket": "week"})
                    if r and r.status_code == 200:
                        data = r.json() or {}
                        series = data.get("series", [])
                        if len(series) >= 2:
                            first = series[0].get("average_grade") or 0
                            last = series[-1].get("average_grade") or 0
                            delta = round((last - first), 2)
                            bullets.append(f"Тренд студента: средняя {last} ({'+' if delta>=0 else ''}{delta} за период)")
                except Exception:
                    pass

            # Расписание — ближайшие 5
            if (scope == "schedule" and is_allowed(role, "read_schedule")) or not (student_id or course_id):
                try:
                    today = date.today().isoformat()
                    r = await _get(client, f"{self.api_base}/api/schedule", headers=headers, params={"date_from": today, "limit": 5})
                    if r and r.status_code == 200:
                        data = r.json() or {}
                        schedules = data.get("schedules", [])
                        bullets.append(f"Ближайшие занятия: {len(schedules)} (начиная с {today})")
                except Exception:
                    pass

            # Дедлайны (если указан курс)
            if course_id and is_allowed(role, "read_course_analytics"):
                try:
                    r = await _get(client, f"{self.api_base}/api/analytics/courses/{course_id}/assignments", headers=headers)
                    if r and r.status_code == 200:
                        data = r.json() or {}
                        assignments = data.get("assignments_analytics", [])
                        # посчитаем ближайшие дедлайны в 14 дней
                        from datetime import datetime, timedelta
                        now = datetime.utcnow()
                        horizon = now + timedelta(days=14)
                        upcoming = 0
                        for a in assignments:
                            due = a.get("due_date")
                            if not due:
                                continue
                            try:
                                dt = datetime.fromisoformat(str(due))
                            except Exception:
                                continue
                            if now <= dt <= horizon:
                                upcoming += 1
                        if upcoming:
                            bullets.append(f"Ближайшие дедлайны (≤14д): {upcoming}")
                except Exception:
                    pass

        if not bullets:
            return ""
        return "\n".join(f"- {b}" for b in bullets)


