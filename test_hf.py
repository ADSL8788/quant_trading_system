from transformers import AutoModel, AutoTokenizer
print("正在加载分词器...")
tokenizer = AutoTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
print("✅ 分词器加载成功")
print("正在加载模型...")
model = AutoModel.from_pretrained("NeoQuasar/Kronos-small")
print("✅ 模型加载成功，一切正常！")
