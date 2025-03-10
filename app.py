from flask import Flask, request, jsonify, render_template
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import re

app = Flask(__name__)

MODEL_PATH = "C:\\Users\\ramiz\\OneDrive\\Masaüstü\\deneme\\checkpoint-22000"
TOKENIZER_NAME = "gpt2"

model = None
tokenizer = None

def convert_to_python_code_format(model_code):
    """Metni Python kod formatına dönüştürür"""
    model_code = re.sub(r'\s([.,(){}=])\s', r'\1', model_code)
    model_code = re.sub(r'\s+', ' ', model_code)
    model_code = re.sub(r'  ', '\n    ', model_code)
    model_code = model_code.strip()
    model_code = re.sub(r"['\"\"']{3}(.*?)['\"\"']{3}", "''", model_code)
    return model_code

def get_last_three_lines(code):
    """Son 3 satırı alır, ancak eğer 3'ten az satır varsa tamamını alır"""
    lines = code.strip().split("\n")  # Satırları al
    last_lines = "\n".join(lines[-3:])  # Son 3 satırı veya daha azını al
    return last_lines

def load_model():
    """Model ve tokenizer'ı yükler"""
    global model, tokenizer
    
    try:
        print(f"Model yükleniyor: {MODEL_PATH}")
        print(f"Tokenizer yükleniyor: {TOKENIZER_NAME}")
        
        tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)
        model = AutoModelForCausalLM.from_pretrained(MODEL_PATH)
        
        if torch.cuda.is_available():
            model = model.cuda()
            
        print("Model ve tokenizer başarıyla yüklendi!")
        return True
    except Exception as e:
        print(f"Model yükleme hatası: {str(e)}")
        return False

@app.route('/')
def index():
    """Ana sayfa: Kod girdisi ve çıktısı için arayüz"""
    return render_template('index.html')

@app.route('/tahmin', methods=['POST'])
def tahmin():
    global model, tokenizer
    if model is None or tokenizer is None:
        success = load_model()
        if not success:
            return jsonify({"error": "Model yüklenemedi"}), 500
    
    data = request.json
    kod = data.get('kod', '')

    if not kod:
        return jsonify({"error": "Kod boş olamaz"}), 400
    
    try:
        # Son 3 satırı al veya tümünü kullan
        last_three_lines = get_last_three_lines(kod)

        # Tokenize ve model ile tahmin
        input_ids = tokenizer(last_three_lines, return_tensors="pt").input_ids
        
        if torch.cuda.is_available():
            input_ids = input_ids.cuda()
        
        with torch.no_grad():
            output = model.generate(
                input_ids,
                max_length=200,
                num_beams=5,
                early_stopping=True,
                temperature=0.5,
                top_k=50,
                top_p=0.9,
                no_repeat_ngram_size=3,
                repetition_penalty=1.5,
            )
        
        output_text = tokenizer.decode(output[0], skip_special_tokens=True)
        formatted_code = convert_to_python_code_format(output_text)
        
        if formatted_code.startswith(last_three_lines):
            prediction_only = formatted_code[len(last_three_lines):].strip()
        else:
            prediction_only = formatted_code
        
        return jsonify({"tahmin": prediction_only})
    
    except Exception as e:
        print(f"Tahmin hatası: {str(e)}")
        return jsonify({"error": f"Tahmin hatası: {str(e)}"}), 500

if __name__ == '__main__':
    load_model()
    app.run(debug=True, port=5000)