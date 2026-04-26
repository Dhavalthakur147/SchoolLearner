english_mcqs = [
    {
        "question": "Which of the following is a preposition?",
        "options": [
            "Run",
            "Beautiful",
            "Under",
            "Quickly"
        ],
        "answer": 2,
        "explanation": "'Under' is a preposition that shows the relationship between a noun (or pronoun) and other words in a sentence."
    },
    {
        "question": "What is the past tense of 'go'?",
        "options": [
            "Goed",
            "Went",
            "Gone",
            "Going"
        ],
        "answer": 1,
        "explanation": "The past tense of 'go' is 'went'. 'Gone' is the past participle."
    },
    # More English questions...
]

def get_questions(count=None):
    """
    Return English questions. If count is specified, return that many random questions.
    Otherwise, return all questions.
    """
    import random
    if count is None:
        return english_mcqs
    return random.sample(english_mcqs, min(count, len(english_mcqs)))