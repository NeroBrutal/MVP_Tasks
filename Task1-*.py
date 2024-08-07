from flask import Flask, request, jsonify
import openai
import pdfplumber
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

app = Flask(__name__)

openai.api_key = 'enter api key please'

# Load and Split
def load_and_split(pdf_path):
    text_chunks = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                chunks = split_text(text)
                text_chunks.extend(chunks)
    
    return text_chunks

def split_text(text, max_length=500):
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    current_chunk = []
    current_length = 0
    text_chunks = []
    
    for sentence in sentences:
        sentence_length = len(sentence)
        if current_length + sentence_length <= max_length:
            current_chunk.append(sentence)
            current_length += sentence_length
        else:
            text_chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_length = sentence_length
    
    if current_chunk:
        text_chunks.append(' '.join(current_chunk))
    
    return text_chunks

# Store
def vectorize_text_chunks(text_chunks):
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(text_chunks)
    return vectorizer, vectors

# Retrieve
def retrieve_relevant_chunks(query, vectorizer, vectors, text_chunks):
    query_vector = vectorizer.transform([query])
    similarities = cosine_similarity(query_vector, vectors).flatten()
    relevant_indices = np.argsort(similarities, axis=0)[::-1]
    relevant_chunks = [text_chunks[i] for i in relevant_indices if similarities[i] > 0.1]
    return relevant_chunks

# Generate
def generate_article(topic, relevant_text, language):
    prompt = f"Write an article about '{topic}' based on the following information: {relevant_text}"
    
    if language.lower() == 'arabic':
        prompt += "\n\nTranslate the article to Arabic."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500,
        temperature=0.7
    )
    
    return response.choices[0].message['content'].strip()

@app.route('/generate-article', methods=['POST'])
def generate_article_endpoint():
    data = request.json
    pdf_path = data.get('pdf_path')
    topic = data.get('topic')
    language = data.get('language')
    
    if not pdf_path or not topic or not language:
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        text_chunks = load_and_split(pdf_path)
        vectorizer, vectors = vectorize_text_chunks(text_chunks)
        relevant_chunks = retrieve_relevant_chunks(topic, vectorizer, vectors, text_chunks)
        
        if not relevant_chunks:
            return jsonify({'error': 'No content available for the specified topic'}), 404
        
        relevant_text = ' '.join(relevant_chunks)
        article = generate_article(topic, relevant_text, language)
        return jsonify({'article': article})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
