science_mcqs = [
    {
        "question": "Which planet is known as the Red Planet?",
        "options": [
            "Venus",
            "Mars",
            "Jupiter",
            "Saturn"
        ],
        "answer": 1,
        "explanation": "Mars is often called the Red Planet because iron minerals in the Martian soil oxidize, or rust, causing the soil and atmosphere to look red."
    },
    {
        "question": "What is the chemical symbol for gold?",
        "options": [
            "Go",
            "Gd",
            "Au",
            "Ag"
        ],
        "answer": 2,
        "explanation": "The chemical symbol for gold is Au, from the Latin word 'aurum' meaning 'shining dawn'."
    },
    # More science questions...
]

def get_questions(count=None):
    """
    Return science questions. If count is specified, return that many random questions.
    Otherwise, return all questions.
    """
    import random
    if count is None:
        return science_mcqs
    return random.sample(science_mcqs, min(count, len(science_mcqs)))