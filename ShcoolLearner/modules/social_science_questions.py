social_science_mcqs = [
    {
        "question": "Who was the first President of India?",
        "options": [
            "Jawaharlal Nehru",
            "Rajendra Prasad",
            "S. Radhakrishnan",
            "Zakir Husain"
        ],
        "answer": 1,
        "explanation": "Dr. Rajendra Prasad was the first President of India, serving from 1950 to 1962."
    },
    {
        "question": "Which is the largest democracy in the world?",
        "options": [
            "United States",
            "China",
            "India",
            "Brazil"
        ],
        "answer": 2,
        "explanation": "India is the world's largest democracy with over 900 million eligible voters."
    },
    # More social science questions...
]

def get_questions(count=None):
    """
    Return social science questions. If count is specified, return that many random questions.
    Otherwise, return all questions.
    """
    import random
    if count is None:
        return social_science_mcqs
    return random.sample(social_science_mcqs, min(count, len(social_science_mcqs)))