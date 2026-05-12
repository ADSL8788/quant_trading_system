import sys
import torch

def test_kronos_model():
    print("="*50)
    print("开始从 Hugging Face 加载预训练模型...")
    print("(这可能需要几分钟，初次使用会下载约 3GB 的模型文件)")
    print("="*50)
    
    try:
        # 注意：这里从 Hugging Face 的 transformers 库加载，
        # 而不是从你本地的 Kronos 文件夹
        from transformers import AutoModel, AutoTokenizer
        
        model_name = "NeoQuasar/Kronos-small"
        tokenizer_name = "NeoQuasar/Kronos-Tokenizer-base"
        
        print(f"\n1. 加载分词器 (Tokenizer): {tokenizer_name}")
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        print("   ✅ 分词器加载成功")
        
        print(f"\n2. 加载主模型 (Model): {model_name}")
        model = AutoModel.from_pretrained(model_name)
        print("   ✅ 主模型加载成功")
        
        print("\n" + "="*50)
        print("🎉 恭喜！Kronos 模型已成功从 Hugging Face 加载！")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ 加载失败: {e}")
        print("\n可能的原因及解决方案：")
        print("1. 网络问题：请确保你的网络能访问 huggingface.co")
        print("2. 如果下载太慢，可以尝试使用国内镜像源: https://hf-mirror.com")
        return False
    
    return True

if __name__ == "__main__":
    success = test_kronos_model()
    sys.exit(0 if success else 1)
