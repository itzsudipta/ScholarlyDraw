import os
from flask import Flask, request, jsonify, render_template
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ibm import WatsonxLLM

# Initialize the Flask app
app = Flask(__name__)

# --- Load Credentials and Initialize Model ---
# This code is designed to be deployed on IBM Code Engine.
# It securely reads your API_KEY and PROJECT_ID from environment variables.
api_key = os.environ.get("LATEX") # <-- Changed from API_KEY to LATEX
project_id = os.environ.get("PROJECT_ID")
url = "https://au-syd.ml.cloud.ibm.com"

# Check if essential credentials are provided for deployment
if not api_key or not project_id:
    print("FATAL ERROR: LATEX and PROJECT_ID environment variables are not set.")
    # This will cause the app to fail on startup if the variables are missing,
    # which is a good safety measure.

llm = WatsonxLLM(
    model_id="ibm/granite-8b-code-instruct",
    url=url,
    project_id=project_id,
    apikey=api_key,
    params={"decoding_method": "greedy", "max_new_tokens": 2048, "temperature": 0.05}
)
print("✅ AI Model Initialized Successfully!")


# --- Engineer the Prompt Template ---
prompt_template_string = """
You are an expert assistant specializing in LaTeX. Your sole purpose is to generate a complete, correct, and runnable LaTeX document to create a diagram based on a user's request.

**CRITICAL RULES:**
1. The document MUST start with `\\documentclass{{article}}`.
2. The document MUST load the `tikz` package with `\\usepackage{{tikz}}`. You MUST also load any necessary TikZ libraries (e.g., `shapes.geometric`, `arrows.meta`, `positioning`, `mindmap`).
3. **IMPORTANT**: If the user's request requires custom node shapes or styles (like 'process', 'decision', 'conv'), you MUST define these styles using a `\\tikzset{{...}}` block in the document preamble before the `\\begin{{document}}`.
4. Every TikZ command inside the `tikzpicture` environment MUST end with a semicolon (;).
5. All LaTeX commands MUST start with a backslash (\\).
6. Do not provide any explanation or comments, only the raw LaTeX code for the entire file.

USER'S REQUEST:
{description}

LATEX DOCUMENT:
"""
prompt = PromptTemplate.from_template(prompt_template_string)

# Create the LangChain chain
chain = prompt | llm | StrOutputParser()


# --- Define Web Routes ---

@app.route('/')
def home():
    """Renders the main chatbot HTML page."""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """Receives a description and returns generated LaTeX code."""
    try:
        data = request.get_json()
        description = data.get('description')

        if not description:
            return jsonify({"error": "No description provided"}), 400

        print(f"⏳ Received request: '{description}'")
        # Invoke the LangChain chain to generate the code
        generated_code = chain.invoke({"description": description})
        print("✅ Code generation complete.")

        return jsonify({"latex_code": generated_code})

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Failed to generate code"}), 500

if __name__ == '__main__':
    # This runs the app on port 8080, which is standard for cloud deployments.
    app.run(host='0.0.0.0', port=8080)
