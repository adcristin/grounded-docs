import requests

queries = [
    'Who founded Solaris Tech?',
    'What is the flagship product?',
    'What is the 2026 expansion project name?',
]

for query in queries:
    try:
        r = requests.post('http://localhost:8000/api/chat', json={'query': query})
        d = r.json()
        grounded = d['debug']['grounded']
        answer = d['answer'][:100]
        print(f"grounded={grounded} | {answer} | query: {query}")
    except Exception as e:
        print(f"ERROR for '{query}': {e}")