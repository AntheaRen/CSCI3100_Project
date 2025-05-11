import sshtunnel
import webuiapi
from typing import List
from PIL import Image
from . import sd, upscaler, logging


class WebUI(sd.ImageGenerator, upscaler.Upscaler):
    api: webuiapi.WebUIApi
    tunnel: sshtunnel.SSHTunnelForwarder

    def __init__(self, api, tunnel):
        self.api = api
        self.tunnel = tunnel

    @classmethod
    def from_ssh(
        cls,
        host: str,
        port: int,
        username: str = "root",
        password: str = "",
    ):
        logging.info(f"Connecting to WebUI API at {host}:{port}...")

        local_port = 6006
        remote_host = '127.0.0.1'
        remote_port = 6006

        tunnel = sshtunnel.SSHTunnelForwarder(
            (host, port),
            ssh_username=username,
            ssh_password=password,
            local_bind_address=(remote_host, local_port),
            remote_bind_address=(remote_host, remote_port),
            set_keepalive=60,
        )

        if tunnel.is_active:
            logging.info(f"SSH tunnel is already active. Local port: {tunnel.local_bind_port}")
        else:
            tunnel.start()
            assert tunnel.is_active, f"SSH tunnel is not active."
            logging.info(f"SSH tunnel is active. Local port: {tunnel.local_bind_port}")

        logging.info(f"Connecting to WebUI API at {host}:{port}...")
        api = webuiapi.WebUIApi(host='127.0.0.1', port=6006)

        # assert self.api.is_alive(), f"WebUI API is not alive."
        logging.info(f"WebUI API connected.")

        return cls(api, tunnel)

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
