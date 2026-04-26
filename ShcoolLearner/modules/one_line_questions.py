one_line_questions = {
    "math": [
        {
            "question": "What is 7 + 4?",
            "answer": "11",
            "explanation": "7 + 4 = 11."
        },
        {
            "question": "What is the square root of 144?",
            "answer": "12",
            "explanation": "12 x 12 = 144."
        },
        {
            "question": "How many degrees are there in a right angle?",
            "answer": "90",
            "explanation": "A right angle measures 90 degrees."
        },
    ],
    "science": [
        {
            "question": "Which planet is known as the Red Planet?",
            "answer": "Mars",
            "explanation": "Mars is called the Red Planet because of iron oxide on its surface."
        },
        {
            "question": "What gas do plants release during photosynthesis?",
            "answer": "Oxygen",
            "explanation": "Plants release oxygen as a byproduct of photosynthesis."
        },
        {
            "question": "What is H2O commonly called?",
            "answer": "Water",
            "explanation": "H2O is the chemical formula for water."
        },
    ],
    "english": [
        {
            "question": "What is the plural of child?",
            "answer": "Children",
            "explanation": "The plural form of child is children."
        },
        {
            "question": "Which part of speech names a person, place, or thing?",
            "answer": "Noun",
            "explanation": "A noun is a word that names a person, place, thing, or idea."
        },
        {
            "question": "What is the opposite of hot?",
            "answer": "Cold",
            "explanation": "Cold is the opposite of hot."
        },
    ],
    "gujarati": [
        {
            "question": "ગુજરાતીની લિપિ કઈ છે?",
            "answer": "ગુજરાતી લિપિ",
            "explanation": "ગુજરાતી ભાષા ગુજરાતી લિપિમાં લખાય છે."
        },
        {
            "question": "'પુસ્તક' નો અર્થ શું થાય?",
            "answer": "Book",
            "explanation": "'પુસ્તક' નો અંગ્રેજી અર્થ Book થાય છે."
        },
        {
            "question": "ગુજરાત રાજ્યની ભાષા કઈ છે?",
            "answer": "Gujarati",
            "explanation": "ગુજરાત રાજ્યની મુખ્ય ભાષા ગુજરાતી છે."
        },
    ],
    "social-science": [
        {
            "question": "Who is known as the Father of the Nation in India?",
            "answer": "Mahatma Gandhi",
            "explanation": "Mahatma Gandhi is widely known as the Father of the Nation in India."
        },
        {
            "question": "What is the capital of India?",
            "answer": "New Delhi",
            "explanation": "New Delhi is the capital of India."
        },
        {
            "question": "How many continents are there on Earth?",
            "answer": "7",
            "explanation": "There are seven continents on Earth."
        },
    ],
    "computer": [
        {
            "question": "What does CPU stand for?",
            "answer": "Central Processing Unit",
            "explanation": "CPU stands for Central Processing Unit."
        },
        {
            "question": "What does HTML stand for?",
            "answer": "Hyper Text Markup Language",
            "explanation": "HTML stands for Hyper Text Markup Language."
        },
        {
            "question": "Which language is commonly used for web page styling?",
            "answer": "CSS",
            "explanation": "CSS is used to style web pages."
        },
    ],
}


def get_one_line_questions(subject=None):
    if subject:
        return one_line_questions.get(subject, [])
    return one_line_questions
