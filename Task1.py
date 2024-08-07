from flask import Flask, request, jsonify
import openai
import pdfplumber
import re

app = Flask(__name__)

openai.api_key = 'api key please'

def extract_relevant_text(pdf_path, topic):
    relevant_text = ""
    topic_lower = topic.lower()
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_lower = text.lower()
                if re.search(r'\b' + re.escape(topic_lower) + r'\b', text_lower):
                    relevant_text += text + "\n"
    
    return relevant_text

def generate_article(topic, document_text, language):
    prompt = f"Write an article about '{topic}' based on the following information: {document_text}"
    
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
        document_text = extract_relevant_text(pdf_path, topic)
        
        if not document_text:
            return jsonify({'error': 'No content available for the specified topic'}), 404
        
        article = generate_article(topic, document_text, language)
        return jsonify({'article': article})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
