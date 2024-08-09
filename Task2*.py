from flask import Flask, request, jsonify
import openai
import requests
from datetime import datetime
import json

app = Flask(__name__)

openai.api_key = ''
google_cse_api_key = ''
google_cse_id = ''

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
        current_date = datetime.now().strftime("%Y-%m-%d")

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_google_cse",
                    "description": "Searches Google for real-time information.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query.",
                            },
                        },
                        "required": ["query"],
                    },
                },
            }
        ]

        messages = [
            {"role": "system", "content": f"You are a knowledgeable AI assistant. The current date is {current_date}. If the question requires up-to-date, real-time information (like current events, latest prices, or the current date), use the provided tools to search Google. If not, answer the question based on your own knowledge."},
            {"role": "user", "content": question}
        ]

        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=messages,
            tools=tools,
        )

        if response['choices'][0]['finish_reason'] == "tool_calls":
            tool_call = response['choices'][0]['message']['tool_calls'][0]
            arguments = json.loads(tool_call['function']['arguments'])  
            search_query = arguments['query']
            cse_response = search_google_cse(search_query)
            response_data = filter_response(cse_response)
        else:
            response_data = response['choices'][0]['message']['content']

        return jsonify({'answer': response_data}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
