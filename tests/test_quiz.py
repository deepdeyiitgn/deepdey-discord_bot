"""Runnable quiz DB smoke test
Run with: python tests/test_quiz.py
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import asyncio
import json
import time
from utils.db import DB

async def run():
    print('Init DB...')
    await DB.init_db()
    # Create quiz
    gid = 123456789
    title = 'Sample Quiz'
    config = json.dumps({'time_limit': 300})
    print('Creating quiz...')
    await DB.create_quiz(gid, title, config, creator_id=999)
    # Fetch quizzes and use the last created id
    quizzes = await DB.list_quizzes(gid)
    quiz = quizzes[0]
    quiz_id = int(quiz['id'])
    print('Quiz created id=', quiz_id)
    # Add a question JSON (simple MCQ format)
    q = {
        'id': 1,
        'text': '2+2=?',
        'type': 'mcq',
        'options': ['1','2','3','4'],
        'answer_index': 3
    }
    await DB.add_quiz_question(quiz_id, json.dumps(q))
    # Start a session
    session_id = await DB.start_quiz_session(quiz_id, user_id=11111)
    print('Started session', session_id)
    # Simulate answering question correctly
    await DB.record_quiz_response(session_id, question_id=1, selected_index=3, answer_text='4', correct=1, time_taken=5)
    # Finish session with score 100
    await DB.finish_quiz_session(session_id, 100.0)
    sess = await DB.get_quiz_session(session_id)
    responses = await DB.get_quiz_responses(session_id)
    print('Session:', sess)
    print('Responses:', responses)
    assert sess and sess['score'] == 100.0
    assert len(responses) == 1
    print('Quiz DB test passed')

if __name__ == '__main__':
    asyncio.run(run())
