import google.generativeai as genai

# API key của bạn
API_KEY = 'AIzaSyCpMshaJVVZPV4ttnLozFCEeduGBcZLVwI'

# Cấu hình API với API key
genai.configure(api_key=API_KEY)

# Liệt kê các model khả dụng (tùy chọn để kiểm tra)
def list_models():
    print("Các model khả dụng:")
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(model.name)

# Hàm sử dụng model gemini-1.5-pro để tạo nội dung
def generate_content(question):
    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content(question)
    return response.text

if __name__ == '__main__':
    # Liệt kê các model khả dụng (tùy chọn)
    list_models()

    # Nhập câu hỏi từ người dùng
    question = input("Nhập câu hỏi của bạn: ")

    # Sử dụng model gemini-1.5-pro để tạo nội dung
    result = generate_content(question)
    print("Kết quả từ API:", result)
