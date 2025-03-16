

# scheduler:
SCHEDULER_LINEAR_START = 0.00085
SCHEDULER_LINEAR_END = 0.0120
SCHEDULER_TIMESTEPS = 1000
SCHEDLER_SCHEDULE = "scaled_linear"

DEFAULT_SAMPLE_NAME = 'image'


ALL_SAMPLERS = [
    "ddim",
    "ddpm",
    "pndm",
    "lms",
    "k_lms",
    "euler",
    "k_euler",
    "euler_a",
    "k_euler_a",
    "dpmsolver",
    "dpmsolver++",
    "dpmsingle",
    "heun",
    "dpm_2",
    "k_dpm_2",
    "dpm_2_a",
    "k_dpm_2_a",
]


def get_sampler(sample_sampler, **sampler_kwargs):
    sample_sampler = sample_sampler.lower().replace(' ', '_')
    # schedulerを用意する
    sched_init_args = {}
    if sample_sampler == "ddim":
        from diffusers import DDIMScheduler
        scheduler_cls = DDIMScheduler
    elif sample_sampler == "ddpm":  # ddpmはおかしくなるのでoptionから外してある
        from diffusers import DDPMScheduler
        scheduler_cls = DDPMScheduler
    elif sample_sampler == "pndm":
        from diffusers import PNDMScheduler
        scheduler_cls = PNDMScheduler
    elif sample_sampler == "lms" or sample_sampler == "k_lms":
        from diffusers import LMSDiscreteScheduler
        scheduler_cls = LMSDiscreteScheduler
    elif sample_sampler == "euler" or sample_sampler == "k_euler":
        from diffusers import EulerDiscreteScheduler
        scheduler_cls = EulerDiscreteScheduler
    elif sample_sampler == "euler_a" or sample_sampler == "k_euler_a":
        from diffusers import EulerAncestralDiscreteScheduler
        scheduler_cls = EulerAncestralDiscreteScheduler
    elif sample_sampler == "dpmsolver" or sample_sampler == "dpmsolver++":
        from diffusers import DPMSolverMultistepScheduler
        scheduler_cls = DPMSolverMultistepScheduler
        sched_init_args["algorithm_type"] = sample_sampler
    elif sample_sampler == "dpmsingle":
        from diffusers import DPMSolverSinglestepScheduler
        scheduler_cls = DPMSolverSinglestepScheduler
    elif sample_sampler == "heun":
        from diffusers import HeunDiscreteScheduler
        scheduler_cls = HeunDiscreteScheduler
    elif sample_sampler == "dpm_2" or sample_sampler == "k_dpm_2":
        from diffusers import KDPM2DiscreteScheduler
        scheduler_cls = KDPM2DiscreteScheduler
    elif sample_sampler == "dpm_2_a" or sample_sampler == "k_dpm_2_a":
        from diffusers import KDPM2AncestralDiscreteScheduler
        scheduler_cls = KDPM2AncestralDiscreteScheduler
    else:
        scheduler_cls = DDIMScheduler

    sched_init_args.update(sampler_kwargs)
    scheduler = scheduler_cls(
        num_train_timesteps=SCHEDULER_TIMESTEPS,
        beta_start=SCHEDULER_LINEAR_START,
        beta_end=SCHEDULER_LINEAR_END,
        beta_schedule=SCHEDLER_SCHEDULE,
        **sched_init_args,
    )

    # clip_sample=Trueにする
    if hasattr(scheduler.config, "clip_sample") and scheduler.config.clip_sample is False:
        # logger.info("set clip_sample to True")
        scheduler.config.clip_sample = True

    return scheduler
