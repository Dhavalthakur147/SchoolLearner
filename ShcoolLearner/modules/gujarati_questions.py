gujarati_mcqs = [
    {
        "question": "ગુજરાતી ભાષામાં 'સૂર્ય' નો અર્થ શું છે?",
        "options": [
            "Moon",
            "Sun",
            "Star",
            "Planet"
        ],
        "answer": 1,
        "explanation": "ગુજરાતી ભાષામાં 'સૂર્ય' નો અર્થ 'Sun' (સૂરજ) થાય છે."
    },
    {
        "question": "'અમદાવાદ' નગર કઈ નદીના કિનારે વસેલું છે?",
        "options": [
            "નર્મદા",
            "સાબરમતી",
            "તાપી",
            "મહી"
        ],
        "answer": 1,
        "explanation": "અમદાવાદ શહેર સાબરમતી નદીના કિનારે વસેલું છે."
    },
    # More Gujarati questions...
]

def get_questions(count=None):
    """
    Return Gujarati questions. If count is specified, return that many random questions.
    Otherwise, return all questions.
    """
    import random
    if count is None:
        return gujarati_mcqs
    return random.sample(gujarati_mcqs, min(count, len(gujarati_mcqs)))