import requests
import json

queries = [
    # True positives (answer IS in the doc)
    ('Who founded Solaris Tech?', 'positive'),
    ('What is the flagship product?', 'positive'),
    ('What is the 2026 expansion project name?', 'positive'),
    ('Where is the headquarters?', 'positive'),
    ('Who is the CEO?', 'positive'),
    
    # Hard negatives (topically adjacent but NOT in doc)
    ('What is Solaris Tech revenue?', 'hard_negative'),
    ('What is Solaris Tech stock price?', 'hard_negative'),
    ('Who is the CFO of Solaris Tech?', 'hard_negative'),
    ('When was Solaris Tech IPO?', 'hard_negative'),
    ('How many employees does Solaris Tech have?', 'hard_negative'),
    ('What is Solaris Tech valuation?', 'hard_negative'),
    
    # True negatives (completely unrelated)
    ('How do I make chocolate cake?', 'negative'),
    ('Who won the 1994 World Cup?', 'negative'),
    ('What is the capital of Japan?', 'negative'),
    ('Describe the plot of Inception', 'negative'),
]

print("=== Testing /chat endpoint ===")
for query, label in queries:
    r = requests.post('http://localhost:8000/api/chat', json={'query': query}, timeout=300)
    data = r.json()
    grounded = data['debug']['grounded']
    answer = data['answer'][:80]
    print(f'{label:15} | grounded={grounded} | {answer}')

print()
print("=== Testing /retrieve endpoint ===")
for query, label in queries:
    r = requests.post('http://localhost:8000/api/retrieve', json={'query': query}, timeout=300)
    data = r.json()
    grounded = data['grounded']
    print(f'{label:15} | grounded={grounded}')