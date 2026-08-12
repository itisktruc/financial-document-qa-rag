import torch
import io
from fastapi import FastAPI, UploadFile, File, Form
from PIL import Image
from transformers import Qwen3VLForConditionalGeneration, AutoProcessor

app = FastAPI()

# 1. Load model và processor MỘT LẦN duy nhất khi khởi động server
MODEL_ID = "Qwen/Qwen3-VL-4B-Instruct"  # Hoặc bản 4B/8B tùy VRAM bạn thuê
print(f"Đang tải model {MODEL_ID} lên GPU...")

processor = AutoProcessor.from_pretrained(MODEL_ID)
# Nếu dùng GPU khoẻ (như RTX 3090/4090), có thể load thẳng torch.bfloat16 để chạy cực nhanh
model = Qwen3VLForConditionalGeneration.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
print("Đã tải model thành công!")

@app.post("/ocr")
async def ocr_endpoint(file: UploadFile = File(...), prompt: str = Form(...)):
    try:
        # Đọc ảnh từ request gửi lên
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Chuẩn bị input cho Qwen-VL
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        # 1. Tạo prompt text theo template của model
        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

        # 2. Đưa thẳng PIL Image vào processor (bỏ dòng processor.image_processor)
        inputs = processor(
            text=[text],
            images=[image],
            padding=True,
            return_tensors="pt"
        ).to("cuda")
        
        # 3. Inference sinh kết quả
        with torch.no_grad():
            generated_ids = model.generate(**inputs, max_new_tokens=4096)

        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]

        # Dọn dẹp cache GPU
        torch.cuda.empty_cache()

        return {"markdown": output_text}

    except Exception as e:
        print(f"Lỗi xử lý OCR: {e}")
        return {"markdown": f"*(Lỗi xử lý server: {e})*"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)