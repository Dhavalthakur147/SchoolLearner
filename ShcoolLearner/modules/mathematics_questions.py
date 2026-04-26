mathematics_mcqs = [
    {
        "question": "What is the value of π (pi) to two decimal places?",
        "options": [
            "3.14",
            "3.16",
            "3.12",
            "3.18"
        ],
        "answer": 0,
        "explanation": "The value of π (pi) is approximately 3.14159, which rounds to 3.14 to two decimal places."
    },
    {
        "question": "What is the square root of 144?",
        "options": [
            "11",
            "12",
            "13",
            "14"
        ],
        "answer": 1,
        "explanation": "12 × 12 = 144, so the square root of 144 is 12."
    },
    # More math questions...
]

def get_questions():
    return mathematics_mcqs

def get_question(index):
    if 0 <= index < len(mathematics_mcqs):
        return mathematics_mcqs[index]
    return None

def get_random_questions(count=10):
    import random
    return random.sample(mathematics_mcqs, min(count, len(mathematics_mcqs)))