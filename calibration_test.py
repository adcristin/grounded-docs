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

results = []
for query, label in queries:
    r = requests.get('http://localhost:8000/api/debug-retrieve', params={'query': query}, timeout=300)
    data = r.json()
    rerank_score = data['reranked'][0]['score'] if data['reranked'] else None
    results.append({'query': query, 'label': label, 'rerank_score': rerank_score})
    print(f'{label:15} | {rerank_score:8.4f} | {query}')

print()
print('=== Summary by label ===')
for label in ['positive', 'hard_negative', 'negative']:
    scores = [r['rerank_score'] for r in results if r['label'] == label]
    print(f'{label:15} | min: {min(scores):8.4f} | max: {max(scores):8.4f} | avg: {sum(scores)/len(scores):8.4f}')