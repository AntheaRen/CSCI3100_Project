import torch
import os
import gc
from abc import ABC, abstractmethod
from PIL import Image
from typing import List
from .utils import sd_eval_utils
from . import logging


class ImageGenerator(ABC):
    @abstractmethod
    def txt2img(self, prompt: str, **kwargs) -> List[Image.Image]:
        pass


class LocalPipeline(ImageGenerator):
    def __init__(self, pipe=None):
        self.pipe = pipe

    @property
    def device(self):
        if hasattr(self.pipe, "device"):
            return self.pipe.device
        else:
            return self.pipe.unet.device

    @property
    def dtype(self):
        if hasattr(self.pipe, "dtype"):
            return self.pipe.dtype
        else:
            return self.pipe.unet.dtype

    @classmethod
    @abstractmethod
    def from_single_file(
        cls,
        pretrained_model_name_or_path: str,
        **kwargs,
    ):
        """
        Load the pipeline from a single file.
        """
        pass

    def txt2img(
        self,
        prompt: str,
        negative_prompt: str = None,
        width: int = 832,
        height: int = 1216,
        batch_size: int = 1,
        batch_count: int = 1,
        num_inference_steps: int = 32,
        guidance_scale: float = 7.0,
        sampler: str = "euler_a",
        seed: int = 42,
    ) -> List[Image.Image]:
        self.pipe.scheduler = sd_eval_utils.get_sampler(sampler)
        images = self.pipe.__call__(
            prompt=[prompt]*batch_size,
            negative_prompt=[negative_prompt]*batch_size,
            width=width,
            height=height,
            guidance_scale=guidance_scale,
            num_images_per_prompt=batch_count,
            num_inference_steps=num_inference_steps,
            generator=torch.Generator().manual_seed(seed),
        ).images
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return images


class LocalStableDiffusionXLPipeline(LocalPipeline):
    MODEL_REPO_ID = r"Laxhar/noobai-XL-1.1"
    MODEL_FILENAME = "NoobAI-XL-v1.1.safetensors"
    HF_TOKEN = os.getenv("HF_TOKEN")

    @classmethod
    def from_single_file(
        cls,
        pretrained_model_name_or_path: str = None,
        enable_xformers_memory_efficient_attention: bool = True,
        device: str = "cuda",
        torch_dtype: torch.dtype = torch.float16,
        use_lpw: bool = True,
    ):
        logging.info(f"Loading Stable Diffusion XL pipeline...")
        from diffusers import StableDiffusionXLPipeline
        # Download checkpoint
        from huggingface_hub import hf_hub_download
        if pretrained_model_name_or_path is None:
            pretrained_model_name_or_path = hf_hub_download(
                repo_id=cls.MODEL_REPO_ID,
                filename=cls.MODEL_FILENAME,
                repo_type="model",
                token=cls.HF_TOKEN,
            )

        # Load models & pipeline
        if not use_lpw:
            pipe = StableDiffusionXLPipeline.from_single_file(
                pretrained_model_link_or_path=pretrained_model_name_or_path,
                torch_dtype=torch.float16,
                use_safetensors=True,
                local_files_only=True,
            ).to(device, dtype=torch_dtype)
            if enable_xformers_memory_efficient_attention:
                pipe.enable_xformers_memory_efficient_attention()
                logging.info(f"Enabled XFormers memory efficient attention")
        else:
            from .utils import sdxl_model_utils
            from .models.sdxl_lpw_pipeline import SDXLStableDiffusionLongPromptWeightingPipeline

            models = sdxl_model_utils.load_models_from_sdxl_checkpoint(
                ckpt_path=pretrained_model_name_or_path,
                device=device,
                dtype=torch_dtype,
            )
            pipe = SDXLStableDiffusionLongPromptWeightingPipeline(
                vae=models["vae"],
                text_encoder=[models["text_encoder1"], models["text_encoder2"]],
                tokenizer=sdxl_model_utils.load_sdxl_tokenizers(max_token_length=225),
                unet=models["nnet"],
                scheduler=sd_eval_utils.get_sampler("euler_a"),
                safety_checker=None,
                feature_extractor=None,
                requires_safety_checker=False,
                clip_skip=1,
            )
            pipe.to(torch.device(device), dtype=torch_dtype)
            if enable_xformers_memory_efficient_attention:
                pipe.unet.enable_xformers_memory_efficient_attention()
                pipe.vae.enable_xformers_memory_efficient_attention()
                logging.info(f"Enabled XFormers memory efficient attention")

        return cls(pipe)
