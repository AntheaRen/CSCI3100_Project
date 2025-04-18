import torch
import os
import gc
from abc import ABC, abstractmethod
from PIL import Image
from typing import List
from . import logging


class ImageGenerationAPI(ABC):
    @abstractmethod
    def txt2img(self, prompt: str, **kwargs) -> List[Image.Image]:
        pass


class StableDiffusionXLPipelineAPI(object):
    MODEL_REPO_ID = r"Laxhar/noobai-XL-1.1"
    MODEL_FILENAME = "NoobAI-XL-v1.1.safetensors"
    HF_TOKEN = os.getenv("HF_TOKEN")

    def __init__(
        self,
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
                repo_id=self.MODEL_REPO_ID,
                filename=self.MODEL_FILENAME,
                repo_type="model",
                token=self.HF_TOKEN,
            )

        # Load models & pipeline
        if not use_lpw:
            self.pipe = StableDiffusionXLPipeline.from_single_file(
                pretrained_model_link_or_path=pretrained_model_name_or_path,
                torch_dtype=torch.float16,
                use_safetensors=True,
                local_files_only=True,
            ).to(device, dtype=torch_dtype)
            if enable_xformers_memory_efficient_attention:
                self.pipe.enable_xformers_memory_efficient_attention()
                logging.info(f"Enabled XFormers memory efficient attention")
        else:
            from .utils import sdxl_model_utils, sdxl_eval_utils
            from .models.sdxl_lpw_pipeline import SDXLStableDiffusionLongPromptWeightingPipeline

            models = sdxl_model_utils.load_models_from_sdxl_checkpoint(
                ckpt_path=pretrained_model_name_or_path,
                device=device,
                dtype=torch_dtype,
            )
            self.pipe = SDXLStableDiffusionLongPromptWeightingPipeline(
                vae=models["vae"],
                text_encoder=[models["text_encoder1"], models["text_encoder2"]],
                tokenizer=sdxl_model_utils.load_sdxl_tokenizers(max_token_length=225),
                unet=models["nnet"],
                scheduler=sdxl_eval_utils.get_sampler("euler_a"),
                safety_checker=None,
                feature_extractor=None,
                requires_safety_checker=False,
                clip_skip=1,
            )
            self.pipe.to(torch.device(device), dtype=torch_dtype)
            if enable_xformers_memory_efficient_attention:
                self.pipe.unet.enable_xformers_memory_efficient_attention()
                self.pipe.vae.enable_xformers_memory_efficient_attention()
                logging.info(f"Enabled XFormers memory efficient attention")

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

    def generate(
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
        from .utils import sdxl_eval_utils
        logging.info(f"Generating images with Stable Diffusion XL pipeline...")
        self.pipe.scheduler = sdxl_eval_utils.get_sampler(sampler)
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


class WebUIAPI(ImageGenerationAPI):

    def __init__(
        self,
        host: str,
        port: int,
        username: str = "root",
        password: str = "",
    ):
        logging.info(f"Connecting to WebUI API at {host}:{port}...")
        self.host = host
        self.port = port
        self.username = username
        self.password = password

        import sshtunnel
        import webuiapi

        local_port = 6006
        remote_host = '127.0.0.1'
        remote_port = 6006

        self.tunnel = sshtunnel.SSHTunnelForwarder(
            (host, port),
            ssh_username=username,
            ssh_password=password,
            local_bind_address=(remote_host, local_port),
            remote_bind_address=(remote_host, remote_port),
            set_keepalive=60,
        )

        self.tunnel.start()
        assert self.tunnel.is_active, f"SSH tunnel is not active."
        logging.info(f"SSH tunnel is active. Local port: {self.tunnel.local_bind_port}")
        logging.info(f"Connecting to WebUI API at {self.host}:{self.port}...")

        self.api = webuiapi.WebUIApi(host='127.0.0.1', port=6006)

        # assert self.api.is_alive(), f"WebUI API is not alive."
        logging.info(f"WebUI API connected.")

    def txt2img(
        self,
        prompt: str,
        negative_prompt: str = None,
        width: int = 832,
        height: int = 1216,
        batch_size: int = 1,
        batch_count: int = 1,
        num_inference_steps: int = 20,
        guidance_scale: float = 1.2,
        sampler: str = "Euler Ancestral CFG++",
        seed: int = 42,
    ) -> List[Image.Image]:
        images = []
        logging.info(f"Generating images with WebUI API...")
        for bc in logging.tqdm(range(batch_count), desc="Batch Count", leave=False, disable=batch_count <= 1):
            batch_imgs = self.api.txt2img(
                prompt=prompt,
                negative_prompt=negative_prompt,
                seed=seed,
                width=width,
                height=height,
                batch_size=batch_size,
                cfg_scale=guidance_scale,
                sampler_name=sampler,
                steps=num_inference_steps,
            ).images
            images.extend(batch_imgs)
        return images

    def upscale(
        self,
        image: Image.Image,
        ratio: float = 2.0,
    ):
        import webuiapi
        logging.info(f"Upscaling image with WebUI API...")
        upscaled_image = self.api.extra_single_image(
            image=image,
            upscaler_1=webuiapi.Upscaler.ESRGAN_4x,
            upscaling_resize=ratio,
        ).image
        return upscaled_image


api: WebUIAPI = None
