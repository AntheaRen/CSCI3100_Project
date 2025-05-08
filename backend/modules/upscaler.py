import torch
import time
import os
from abc import ABC, abstractmethod
from PIL import Image
from typing import List, Union
from torchvision import transforms
from spandrel import ImageModelDescriptor, ModelLoader
from . import logging


class Upscaler(ABC):
    @abstractmethod
    def upscale(self, images: Union[Image.Image, List[Image.Image]]) -> List[Image.Image]:
        """
        Upscale the input images.

        Args:
            images (Union[Image.Image, List[Image.Image]]): The input image(s) to be upscaled.

        Returns:
            List[Image.Image]: The upscaled image(s).
        """
        pass


class ESRGANUpscaler(Upscaler):
    def __init__(self, model: ImageModelDescriptor):
        if not isinstance(model, ImageModelDescriptor):
            raise ValueError(f"model must be an instance of {ImageModelDescriptor.__name__}, not {type(model).__name__}")

        self.model = model
        self.transforms = transforms.ToTensor()

    @property
    def device(self):
        return next(self.model.model.parameters()).device

    @property
    def dtype(self):
        return next(self.model.model.parameters()).dtype

    @classmethod
    def from_single_file(
        cls,
        pretrained_model_name_or_path: str,
        device: torch.device = torch.device("cuda" if torch.cuda.is_available() else "cpu"),
    ):
        if not os.path.isfile(pretrained_model_name_or_path):
            raise FileNotFoundError(f"file not found: {pretrained_model_name_or_path}")
        logging.info(f"Loading model from {pretrained_model_name_or_path}")
        tic = time.time()
        model = ModelLoader().load_from_file(pretrained_model_name_or_path)
        logging.info(f"Loaded model in {time.time() - tic:'.2f'} seconds")

        model.to(device)
        model.eval()
        return cls(model)

    def upscale(
        self,
        images: Union[Image.Image, List[Image.Image]],
    ) -> List[Image.Image]:
        if isinstance(images, Image.Image):
            images = [images]
        if not all(img.size == images[0].size for img in images):
            raise ValueError("all images must have the same size, got: " + ", ".join(str(img.size) for img in images))
        images = torch.stack([self.transforms(image) for image in images]).to(self.device, self.dtype)
        with torch.no_grad():
            outputs = self.model(images)
        outputs = outputs.cpu().numpy().transpose(0, 2, 3, 1)
        outputs = (outputs * 255).clip(0, 255).astype("uint8")
        outputs = [Image.fromarray(output) for output in outputs]
        return outputs


upscaler: ESRGANUpscaler = None
