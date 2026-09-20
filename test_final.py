import requests

queries = [
    # True positives
    'Who founded Solaris Tech?',
    'What is the flagship product?',
    'What is the 2026 expansion project name?',
    'Where is the headquarters?',
    'Who is the CEO?',
    
    # Hard negatives
    'What is Solaris Tech revenue?',
    'What is Solaris Tech stock price?',
    'Who is the CFO of Solaris Tech?',
    'When was Solaris Tech IPO?',
    'How many employees does Solaris Tech have?',
    'What is Solaris Tech valuation?',
    
    # True negatives
    'How do I make chocolate cake?',
    'Who won the 1994 World Cup?',
    'What is the capital of Japan?',
    'Describe the plot of Inception',
]

print("Testing /chat endpoint for all queries...")
for query in queries:
    try:
        r = requests.post('http://localhost:8000/api/chat', json={'query': query}, timeout=300)
        d = r.json()
        grounded = d['debug']['grounded']
        answer = d['answer'][:100]
        print(f"grounded={grounded} | {answer} | query: {query}")
    except Exception as e:
        print(f"ERROR for '{query}': {e}")