from ollama import chat


response = chat(
    model="qwen3:4b",
    messages=[
        {
            "role": "user",
            "content": (
                "A customer cannot log in after migrating to SAML SSO. "
                "Explain briefly what might be wrong."
            ),
        }
    ],
)

print(response.message.content)
