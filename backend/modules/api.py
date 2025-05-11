from abc import ABC, abstractmethod
from PIL import Image
from typing import List
from .sd import ImageGenerator
from .upscaler import Upscaler
from .webui import WebUI
from . import logging


class ArtifyAPI(object):
    image_generator: ImageGenerator
    upscaler: Upscaler

    def __init__(
        self,
        image_generator: ImageGenerator,
        upscaler: Upscaler,
    ):
        assert isinstance(image_generator, ImageGenerator), f"image_generator must be an instance of {ImageGenerator.__name__}, not {type(image_generator).__name__}"
        assert isinstance(upscaler, Upscaler), f"upscaler must be an instance of {Upscaler.__name__}, not {type(upscaler).__name__}"

        self.image_generator = image_generator
        self.upscaler = upscaler

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
        logging.info(f"Generating images using {self.image_generator.__class__.__name__}...")
        return self.image_generator.txt2img(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            batch_size=batch_size,
            batch_count=batch_count,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            sampler=sampler,
            seed=seed,
        )

    def upscale(
        self,
        image: Image.Image,
        ratio: float = 2.0,
    ):
        logging.info(f"Upscaling images using {self.upscaler.__class__.__name__}...")
        return self.upscaler.upscale(image, ratio=ratio)
