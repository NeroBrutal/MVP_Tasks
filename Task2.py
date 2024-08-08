from flask import Flask, request, jsonify
import openai
import requests

app = Flask(__name__)

openai.api_key = ''
google_cse_api_key = ''
google_cse_id = ''

def ask_openai(question, context=""):
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": context},
            {"role": "user", "content": question}
        ],
        max_tokens=1500,
        temperature=0.7
    )
    return response['choices'][0]['message']['content']

def search_google_cse(query):
    try:
        url = f'https://www.googleapis.com/customsearch/v1?key={google_cse_api_key}&cx={google_cse_id}&q={query}'
        response = requests.get(url)
        data = response.json()
        if 'items' in data:
            snippets = [item.get('snippet', 'No snippet') for item in data['items']]
            return snippets
        else:
            return ["No relevant information found."]
    except Exception as e:
        return [f"Error fetching information: {str(e)}"]

def filter_response(snippets):
    relevant_info = []
    for snippet in snippets:
        snippet = snippet.replace('\n', ' ')
        snippet = snippet.replace('...', ' ')
        snippet = ' '.join(snippet.split())
        relevant_info.append(snippet)
    return ' '.join(relevant_info)

@app.route('/ask-question', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question')
    
    if not question:
        return jsonify({'error': 'Missing question'}), 400

    try:
        context = "You are an AI assistant. Determine if the following question requires real-time information or if it can be answered with existing knowledge."
        initial_analysis = ask_openai(f"Does this question require real-time information? {question}", context)
        
        if "yes" in initial_analysis.lower():
            cse_response = search_google_cse(question)
            response_data = filter_response(cse_response)
        else:
            response_data = ask_openai(question)

        return jsonify({'answer': response_data}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)