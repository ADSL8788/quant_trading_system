from transformers import AutoTokenizer, AutoModel

# 本地模型路径（假设你已经将模型文件夹放在这里）
tokenizer_path = "./local_models/Kronos-Tokenizer-base"
model_path = "./local_models/Kronos-small"

print("从本地加载分词器...")
try:
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True)
    print("✅ 分词器加载成功")
except Exception as e:
    print(f"❌ 分词器加载失败: {e}")
    exit(1)

print("从本地加载模型...")
try:
    model = AutoModel.from_pretrained(model_path, local_files_only=True)
    print("✅ 模型加载成功，一切正常！")
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
    exit(1)
