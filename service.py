import openai, time, base64, mimetypes, json

with open('key.txt', 'r', encoding='utf-8') as file:
    content = file.read()

client = openai.OpenAI(
    base_url = "https://openrouter.ai/api/v1",
    api_key = base64.b64decode(content).decode("utf-8")
)


json_template = json.dumps({
    "name": "N/A",
    "category": "N/A",
    "characteristics": {
        "energy_value": "N/A",
        "sodium": "N/A",
        "total_sugar": "N/A",
        "free_sugar": "N/A",
        "total_protein": "N/A",
        "total_fat": "N/A",
        "fruit_content": "N/A",
        "age_marking": "N/A",
        "high_sugar_front_packaging": "false",
        "labeling": "true",
    },
    "additional_info": {
        "containings": "N/A",
        "description": "N/A",
        "manufactuer_address": "N/A",
        "storing_conditions": "N/A",
    }
})

def encode_image(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    if mime is None:
        mime = "image/jpeg"
    with open(path, "rb") as file:
        b64 = base64.b64encode(file.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"
    

class Processor:
    def __init__(self):
        self.encoded_images = []
    
    def initialize_images(self, image_paths):
        if isinstance(image_paths, str):
            image_paths = [image_paths]
        
        self.encoded_images = []
        for image_path in image_paths:
            self.encoded_images.append(encode_image(image_path))
    
    def turn_to_llm(self):
        messages = [
            {"type": "text", "text": f"Извлеки весь текст на русском языке с изображений, заполни информацию о продукте по этой схеме {json_template} и ВЕРНИ РЕЗУЛЬТАТ СТРОГО В JSON ФОРМАТЕ"}
        ]
        
        for image_path in self.encoded_images:
            messages.append({"type": "image_url", "image_url": {"url": image_path}})

        start_time = time.time()
        try:
            response = client.chat.completions.create(
                extra_headers = {},
                extra_body = {},
                #model = "qwen/qwen2.5-vl-32b-instruct:free",
                model = "mistralai/mistral-small-3.2-24b-instruct:free",
                messages=[{
                    "role": "user",
                    "content": messages,
                }],
            ).choices[0].message.content
            
            first_bracer = response.find("{")
            last_bracer = response.rfind("}")
            try:
                response = json.loads(response[first_bracer:last_bracer+1])
            except Exception as exception:
                print("Model`s output cannot be interpreted as JSON", exception)
                print(response)
                return json_template
            print(response)
        except Exception as exception:
            print("Exception occured on OpenRouter`s side:", exception)
            return json_template
        print("LLM Execution took", time.time() - start_time, "s.")
        return response