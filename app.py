
import os
import json
import base64
import re
import urllib.request
import urllib.error

from flask import Flask, render_template_string, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

OPENCODE_URL = "http://127.0.0.1:4096"
OPENCODE_PASSWORD = os.getenv("OPENCODE_SERVER_PASSWORD")

MODEL = {
    "providerID": "opencode",
    "modelID": "beam-free"
}


# ========================================
# CLEAN AI RESPONSE
# ========================================

def clean_answer(answer):

    if not answer:
        return "OpenCode returned an empty response. Please try again."

    # Remove AI Analysis headings.
    answer = re.sub(
        r"(?im)^\s*#{1,6}\s*AI Analysis\s*#*\s*$",
        "",
        answer
    )

    # Remove unwanted Copy Code labels.
    answer = re.sub(
        r"(?im)^\s*(?:\*\*)?Copy\s+Code(?:\*\*)?\s*$",
        "",
        answer
    )

    # Remove Copied labels.
    answer = re.sub(
        r"(?im)^\s*Copied!\s*$",
        "",
        answer
    )

    # Remove excessive blank lines.
    answer = re.sub(r"\n{3,}", "\n\n", answer)

    return answer.strip()


# ========================================
# CONNECT TO OPENCODE
# ========================================

def ask_opencode(problem):

    if not OPENCODE_PASSWORD:
        return "Error: OPENCODE_SERVER_PASSWORD is missing from .env."

    prompt = f"""
You are Switch AI Agent, a beginner-friendly programming assistant.

Analyze this programming problem:

{problem}

INSTRUCTIONS:

1. Explain the actual error.
2. Identify the root cause.
3. Give simple step-by-step solutions.
4. Provide corrected code.
5. Show expected output.
6. Preserve the programming language.
7. Do not invent errors.
8. Code blocks must contain ONLY executable code.
9. Output blocks must contain ONLY expected output.
10. Never write Copy Code or Copied!
11. Never repeat headings.
12. Do not include an AI Analysis heading.

Use this structure:

## 1. Error Meaning

Explain the error in simple language.

## 2. Root Cause

Explain why the error happened.

## 3. Solution

Give numbered correction steps.

## 4. Corrected Code

Provide the complete corrected code in a fenced code block.

## 5. Expected Output

Show the expected output in a fenced code block.

Be accurate, clear, and beginner-friendly.
"""

    auth_string = "opencode:" + OPENCODE_PASSWORD

    encoded_auth = base64.b64encode(
        auth_string.encode("utf-8")
    ).decode("utf-8")

    headers = {
        "Authorization": "Basic " + encoded_auth,
        "Content-Type": "application/json"
    }

    try:

        # Create a new OpenCode session.
        session_request = urllib.request.Request(
            OPENCODE_URL + "/session",
            data=json.dumps({}).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(
            session_request,
            timeout=60
        ) as response:

            session_data = json.loads(
                response.read().decode("utf-8")
            )

        session_id = session_data.get("id")

        if not session_id:
            return "Error: OpenCode did not return a session ID."

        # Send the programming problem.
        message_data = {
            "model": MODEL,
            "parts": [
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }

        message_request = urllib.request.Request(
            OPENCODE_URL + "/session/" + session_id + "/message",
            data=json.dumps(message_data).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(
            message_request,
            timeout=180
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )

        answer_parts = []

        for part in result.get("parts", []):

            if part.get("type") == "text":

                answer_parts.append(
                    part.get("text", "")
                )

        answer = "\n".join(answer_parts)

        return clean_answer(answer)

    except urllib.error.HTTPError as error:

        details = error.read().decode(
            "utf-8",
            errors="replace"
        )

        return f"OpenCode HTTP Error {error.code}: {details}"

    except urllib.error.URLError as error:

        return (
            "Cannot connect to OpenCode server. "
            "Please check whether OpenCode is running. "
            f"Details: {error.reason}"
        )

    except Exception as error:

        return f"Unexpected error: {str(error)}"


# ========================================
# HTML PAGE
# ========================================

HTML_PAGE = r"""
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Switch AI Agent</title>

<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

<script src="https://cdn.jsdelivr.net/npm/dompurify@3.2.6/dist/purify.min.js"></script>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 30px 15px;
    font-family: Arial, sans-serif;
    background: #101827;
    color: #f1f5f9;
}

.container {
    max-width: 950px;
    margin: auto;
}

h1 {
    text-align: center;
    color: #60a5fa;
    margin-bottom: 10px;
}

.subtitle {
    text-align: center;
    color: #cbd5e1;
    margin-bottom: 30px;
}

.panel {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 25px;
    margin-bottom: 22px;
}

h2 {
    color: #93c5fd;
    font-size: 21px;
}

textarea {
    width: 100%;
    min-height: 180px;
    padding: 15px;
    border-radius: 8px;
    border: 1px solid #475569;
    background: #0f172a;
    color: white;
    font-family: Consolas, monospace;
    font-size: 15px;
    resize: vertical;
}

button {
    border: none;
    border-radius: 7px;
    cursor: pointer;
}

.analyze-button {
    margin-top: 15px;
    padding: 12px 25px;
    background: #2563eb;
    color: white;
    font-size: 16px;
    font-weight: bold;
}

.analyze-button:hover {
    background: #1d4ed8;
}

#result {
    line-height: 1.7;
    overflow-wrap: anywhere;
}

#result h2,
#result h3 {
    color: #93c5fd;
    margin-top: 25px;
}

#result p {
    color: #e2e8f0;
}

#result li {
    margin-bottom: 8px;
}

#result code {
    font-family: Consolas, monospace;
}

#result :not(pre) > code {
    background: #334155;
    padding: 3px 6px;
    border-radius: 4px;
}

.code-wrapper {
    margin: 15px 0;
    border: 1px solid #475569;
    border-radius: 8px;
    overflow: hidden;
    background: #020617;
}

.code-header {
    display: flex;
    justify-content: flex-end;
    padding: 8px;
    background: #1e293b;
    border-bottom: 1px solid #475569;
}

.copy-button {
    padding: 7px 13px;
    background: #2563eb;
    color: white;
    font-size: 12px;
}

.copy-button:hover {
    background: #1d4ed8;
}

pre {
    padding: 16px;
    margin: 0;
    overflow-x: auto;
    white-space: pre;
    background: #020617;
    color: #e2e8f0;
}

.loading {
    text-align: center;
    padding: 25px;
    color: #93c5fd;
}

.error {
    color: #fca5a5;
    padding: 15px;
}

.footer {
    text-align: center;
    color: #94a3b8;
    font-size: 13px;
    margin-top: 25px;
}

</style>

</head>

<body>

<div class="container">

    <h1>Switch AI Agent</h1>

    <p class="subtitle">
        Your AI Programming Error Analysis Assistant
    </p>

    <div class="panel">

        <h2>Describe Your Programming Problem</h2>

        <form id="problemForm">

            <textarea
                id="problem"
                placeholder="Paste your programming error or code here..."
                required
            ></textarea>

            <button
                class="analyze-button"
                type="submit"
            >
                Analyze Problem
            </button>

        </form>

    </div>

    <div class="panel">

        <h2>AI Analysis</h2>

        <div id="result">
            Your AI analysis will appear here.
        </div>

    </div>

    <div class="footer">
        Switch AI Agent | Powered by OpenCode
    </div>

</div>

<script>

const form = document.getElementById("problemForm");

const resultContainer = document.getElementById("result");

const problemInput = document.getElementById("problem");


// ========================================
// CLEAN MARKDOWN RESPONSE
// ========================================

function cleanResponse(text) {

    // Remove AI Analysis headings.
    text = text.replace(
        /^\s*#{1,6}\s*AI Analysis\s*#*\s*$/gim,
        ""
    );

    // Remove unwanted Copy Code labels.
    text = text.replace(
        /^\s*(?:\*\*)?Copy\s+Code(?:\*\*)?\s*$/gim,
        ""
    );

    // Remove Copied labels.
    text = text.replace(
        /^\s*Copied!\s*$/gim,
        ""
    );

    // Remove excessive blank lines.
    text = text.replace(
        /\n{3,}/g,
        "\n\n"
    );

    return text.trim();

}


// ========================================
// ANALYZE PROBLEM
// ========================================

form.addEventListener("submit", async function(event) {

    event.preventDefault();

    const problem = problemInput.value.trim();

    if (!problem) {

        alert("Please enter a programming problem.");

        return;

    }

    resultContainer.innerHTML =
        '<div class="loading">Analyzing your problem... Please wait.</div>';

    try {

        const response = await fetch("/analyze", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                problem: problem
            })

        });

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.answer || "Request failed."
            );

        }

        const markdown = cleanResponse(
            data.answer || "No answer received."
        );

        // Render Markdown safely.
        resultContainer.innerHTML = DOMPurify.sanitize(
            marked.parse(markdown)
        );

        // Add Copy Code buttons.
        resultContainer.querySelectorAll("pre").forEach((block) => {

            const codeElement = block.querySelector("code");

            if (!codeElement) return;

            const wrapper = document.createElement("div");

            wrapper.className = "code-wrapper";

            const header = document.createElement("div");

            header.className = "code-header";

            const button = document.createElement("button");

            button.className = "copy-button";

            button.type = "button";

            button.textContent = "Copy Code";

            button.addEventListener("click", async () => {

                try {

                    await navigator.clipboard.writeText(
                        codeElement.textContent
                    );

                    button.textContent = "Copied!";

                    setTimeout(() => {

                        button.textContent = "Copy Code";

                    }, 1500);

                } catch (error) {

                    button.textContent = "Copy failed";

                }

            });

            header.appendChild(button);

            block.parentNode.insertBefore(wrapper, block);

            wrapper.appendChild(header);

            wrapper.appendChild(block);

        });

    } catch (error) {

        resultContainer.innerHTML =
            '<div class="error">Error: ' +
            DOMPurify.sanitize(String(error.message)) +
            '</div>';

    }

});

</script>

</body>

</html>
"""


# ========================================
# HOME PAGE
# ========================================

@app.route("/")
def home():

    return render_template_string(HTML_PAGE)


# ========================================
# ANALYZE API
# ========================================

@app.route("/analyze", methods=["POST"])
def analyze():

    data = request.get_json(silent=True) or {}

    problem = data.get("problem", "").strip()

    if not problem:

        return jsonify({
            "answer": "Please enter a programming problem."
        }), 400

    answer = ask_opencode(problem)

    return jsonify({
        "answer": clean_answer(answer)
    })


# ========================================
# RUN FLASK
# ========================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
