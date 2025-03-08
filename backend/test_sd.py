from diffusers import StableDiffusionXLPipeline, EulerAncestralDiscreteScheduler
import torch

pretrained_model_name_or_path = r"d:\AI\models\sdxl\ckpt\artiwaifu-diffusion-v2.safetensors"

pipe = StableDiffusionXLPipeline.from_single_file(
    pretrained_model_link_or_path=pretrained_model_name_or_path,
    torch_dtype=torch.float16,
    use_safetensors=True,
    local_files_only=True,
).to("cuda", dtype=torch.float16)
# pipe.enable_xformers_memory_efficient_attention()
pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)

prompt = 'a dog is watching TV'

images = pipe.__call__(
    prompt=[prompt],
    width=512,
    height=512,
    guidance_scale=7.0,
    num_images_per_prompt=1,
    num_inference_steps=20,
    generator=torch.Generator().manual_seed(42),
).images

images[0].show()
