import torch
from PIL import Image
from typing import List
from diffusers import StableDiffusionXLPipeline, EulerAncestralDiscreteScheduler

DEFAULT_PRETRAINED_MODEL_NAME_OR_PATH = r"d:\AI\models\sdxl\ckpt\artiwaifu-diffusion-v2.safetensors"


class Pipeline(object):
    pipe: StableDiffusionXLPipeline

    def __init__(
        self,
        pretrained_model_name_or_path: str = DEFAULT_PRETRAINED_MODEL_NAME_OR_PATH,
        enable_xformers_memory_efficient_attention: bool = False,
        device: str = "cuda",
        torch_dtype: torch.dtype = torch.float16,
    ):
        self.pipe = StableDiffusionXLPipeline.from_single_file(
            pretrained_model_link_or_path=pretrained_model_name_or_path,
            torch_dtype=torch.float16,
            use_safetensors=True,
            local_files_only=True,
        ).to(device, dtype=torch_dtype)
        self.pipe.set_use_memory_efficient_attention_xformers(valid=enable_xformers_memory_efficient_attention)
        self.pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(self.pipe.scheduler.config)

    @property
    def device(self):
        return self.pipe.device

    @property
    def dtype(self):
        return self.pipe.dtype

    def generate(
        self,
        prompt: str,
        negative_prompt: str = None,
        width: int = 512,
        height: int = 512,
        batch_size: int = 1,
        batch_count: int = 1,
        num_inference_steps: int = 20,
        guidance_scale: float = 7.0,
        seed: int = 42,
    ) -> List[Image.Image]:
        return self.pipe.__call__(
            prompt=[prompt]*batch_size,
            negative_prompt=[negative_prompt]*batch_size,
            width=width,
            height=height,
            guidance_scale=guidance_scale,
            num_images_per_prompt=batch_count,
            num_inference_steps=num_inference_steps,
            generator=torch.Generator().manual_seed(seed),
        ).images


pipeline: Pipeline = None
