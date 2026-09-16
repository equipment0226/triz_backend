"""One bounded diffusion invocation; no generated image is a verified filing drawing."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

MODEL = 'stable-diffusion-v1-5/stable-diffusion-v1-5'
REVISION = '451f4fe16113bff5a5d2269ed5ad43b0592e9a14'


def generate(request, target):
    import torch
    from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
    import psutil
    started = time.monotonic()
    torch.set_num_threads(max(1, min(8, int(os.getenv('DRAWING_CPU_THREADS', '2')))))
    device = os.getenv('DRAWING_DEVICE', 'cpu')
    if device not in ('cpu', 'cuda'):
        raise ValueError('unsupported device')
    pipe = StableDiffusionPipeline.from_pretrained(MODEL, revision=REVISION,
        torch_dtype=torch.float32 if device == 'cpu' else torch.float16,
        use_safetensors=True, low_cpu_mem_usage=True)
    pipe = pipe.to(device)
    # Torch 2 SDPA already slices memory-efficient attention; do not stack slicing.
    pipe.enable_vae_slicing()
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    loaded = time.monotonic()
    result = pipe(prompt=request['prompt'], negative_prompt=request['negative_prompt'],
        num_inference_steps=request['steps'], guidance_scale=7.0,
        width=request['width'], height=request['height'],
        generator=torch.Generator(device=device).manual_seed(request['seed']))
    if result.nsfw_content_detected and any(result.nsfw_content_detected):
        raise ValueError('image filtered')
    image = result.images[0]
    temporary = target.with_suffix('.tmp.png')
    image.save(temporary, format='PNG')
    temporary.replace(target)
    memory = psutil.Process().memory_info()
    try:
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    except ImportError:
        peak = getattr(memory, 'peak_wset', memory.rss)
    return {'model_id': MODEL, 'model_revision': REVISION, 'device': device,
        'seed': request['seed'], 'steps': request['steps'], 'width': image.width, 'height': image.height,
        'load_seconds': round(loaded-started, 3), 'inference_seconds': round(time.monotonic()-loaded, 3),
        'peak_rss_bytes': peak, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        'torch_version': torch.__version__, 'artifact_kind': 'CONCEPT_IMAGE',
        'disclaimer': '해당 이미지는 생성형 AI를 활용한 샘플 이미지입니다.',
        'technical_review': 'NOT_RUN', 'official_editor_validation': 'NOT_RUN'}


if __name__ == '__main__':
    data = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    target = Path(sys.argv[2])
    try:
        info = generate(data, target)
        target.with_suffix('.json').write_text(json.dumps(info), encoding='utf-8')
    except Exception as error:
        # No prompts, provider response, access tokens or signed URLs in logs.
        target.with_suffix('.error.json').write_text(json.dumps({'code': type(error).__name__}), encoding='utf-8')
        sys.exit(1)
