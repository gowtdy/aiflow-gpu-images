import os
import logging
import argparse
import time
import torch
from fastapi import FastAPI, Request, Query
from transformers import AutoModelForCausalLM, AutoTokenizer

from utility.logset import setup_logger
from utility.util import genid, gen_res_dict

app = FastAPI()

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
DAY_FORMAT = '%Y-%m-%d'
LOG_FORMAT = "%(asctime)s-%(filename)s[line:%(lineno)d]-%(levelname)s: %(message)s"

# 自定义过滤器，根据模块名称过滤日志
class ModuleFilter(logging.Filter):
    def __init__(self, module_name):
        super().__init__()
        self.module_name = module_name

    def filter(self, record):
        return record.name == self.module_name

log_dir = '/app/log'
os.makedirs(log_dir, exist_ok=True)
# 创建日志记录器
logger = logging.getLogger('mtserver')
logger.setLevel(logging.DEBUG)

logger = setup_logger(
    logger_name='mtserver',
    log_file=log_dir + '/mtserver_log.txt',
    console_level='DEBUG',
    file_level='DEBUG'
)

model_path = '/app/models/mt_models'
tokenizer = AutoTokenizer.from_pretrained(model_path)

# 根据 docker-compose.yml 中的 GPU_INDEX 环境变量配置 GPU
gpu_index = int(os.getenv('GPU_INDEX', '0'))
device_map = {"": f"cuda:{gpu_index}"} if gpu_index >= 0 else "auto"
logger.info(f"Loading model on GPU {gpu_index} with device_map: {device_map}")

# 优化: 使用低精度加载（如果模型支持）
# 注意：如果模型已经是FP8量化，可能不需要这个，但可以尝试
try:
    model = AutoModelForCausalLM.from_pretrained(
        model_path, 
        device_map=device_map,
        torch_dtype=torch.bfloat16  # 使用bfloat16减少显存占用
    )
    logger.info("Model loaded with bfloat16 precision")
except Exception as e:
    # 如果模型不支持bfloat16，回退到默认加载
    logger.warning(f"Failed to load model with bfloat16: {e}, falling back to default loading")
    model = AutoModelForCausalLM.from_pretrained(model_path, device_map=device_map)

# 优化: 确保模型在推理模式
model.eval()
logger.info("Model set to evaluation mode")

@app.post("/mtapi/translate")
async def translate(request: Request):
    try:
        data = await request.json()
        
        # 提取参数
        text = data.get('text')
        src_lang = data.get('src_lang', '')
        tgt_lang = data.get('tgt_lang', 'en')
        logid = data.get('logid')
        max_new_tokens = data.get('max_new_tokens', 512)  # 优化: 默认降低到512，减少KV cache占用
        
        # 验证必需参数
        if not text:
            return gen_res_dict(ret=-1, msg="Missing required parameter: text")
        
        # 如果 logid 未传入，生成一个
        if not logid:
            logid = genid(0, int(time.time()))
        
        logger.info(f"[logid:{logid}] Translation request: src_lang={src_lang}, tgt_lang={tgt_lang}, text_length={len(text)}")
        
        # 构建翻译提示词
        prompt = f"Translate the following segment into {tgt_lang}, without additional explanation.\n\n{text}"
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        # 使用 tokenizer 格式化消息
        tokenized_chat = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=False,
            return_tensors="pt"
        )
        
        # 调用模型生成翻译
        logger.debug(f"[logid:{logid}] Generating translation...")
        # 优化: 使用torch.inference_mode()禁用梯度计算，减少显存占用
        with torch.inference_mode():
            outputs = model.generate(
                tokenized_chat.to(model.device), 
                max_new_tokens=min(max_new_tokens, 1024),  # 限制最大长度，减少KV cache占用
                do_sample=False,  # 贪婪解码，减少计算
                use_cache=True,  # 使用KV cache（默认开启）
                pad_token_id=tokenizer.eos_token_id if tokenizer.eos_token_id else tokenizer.pad_token_id,  # 避免padding
            )
        
        # 优化: 生成后清理GPU缓存
        torch.cuda.empty_cache()
        
        # 提取新生成的 tokens（排除输入部分）
        input_length = tokenized_chat.shape[1]
        generated_tokens = outputs[0][input_length:]
        
        # 解码翻译结果
        translated_text = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
        
        logger.info(f"[logid:{logid}] Translation completed successfully, src_lang={src_lang}, tgt_lang={tgt_lang}, text={text}, translated_text={translated_text}")
        
        # 返回成功响应
        return gen_res_dict(
            ret=0,
            msg="success",
            dt={
                "translated_text": translated_text,
                "src_lang": src_lang,
                "tgt_lang": tgt_lang,
                "logid": logid,
            }
        )
        
    except Exception as e:
        # 错误处理
        logid = data.get('logid') if 'data' in locals() and data else genid(0, int(time.time()))
        error_msg = f"Translation failed: {str(e)}"
        logger.error(f"[logid:{logid}] {error_msg},", exc_info=True)
        # 优化: 确保错误时也清理缓存
        torch.cuda.empty_cache()
        return gen_res_dict(ret=-1, msg=error_msg, dt={"logid": logid})

if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser(description='Simple TCP server.')
    parser.add_argument('--port', type=int, required=True, help='Port number to listen on')
    parser.add_argument('--workers', type=int, default=1, help='Number of worker processes')
    args = parser.parse_args()

    # 配置uvicorn的日志
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"

    if args.workers > 1:
        # 使用导入字符串形式启动服务
        uvicorn.run(
            "gpu_mtserver:app",
            host="0.0.0.0",
            port=args.port,
            reload=False,
            log_config=log_config,
            workers=args.workers,
            timeout_keep_alive=300
        )
    else:
        # 单进程模式下可以直接传递 app 对象
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=args.port,
            reload=False,
            log_config=log_config,
            timeout_keep_alive=300
        )