import torch
import os
import diffusers
from diffusers import AutoencoderKL
from safetensors.torch import load_file
from accelerate import init_empty_weights
from accelerate.utils.modeling import set_module_tensor_to_device
from transformers import CLIPTextModel, CLIPTextModelWithProjection, CLIPTextConfig, CLIPTokenizer

from ..models.sdxl_nnet import SDXLUNet2DConditionModel

TOKENIZER1_PATH = "openai/clip-vit-large-patch14"
TOKENIZER2_PATH = "laion/CLIP-ViT-bigG-14-laion2B-39B-b160k"

VAE_PARAMS_Z_CHANNELS = 4
VAE_PARAMS_RESOLUTION = 256
VAE_PARAMS_IN_CHANNELS = 3
VAE_PARAMS_OUT_CH = 3
VAE_PARAMS_CH = 128
VAE_PARAMS_CH_MULT = [1, 2, 4, 4]
VAE_PARAMS_NUM_RES_BLOCKS = 2

UNET_KEY_PREFIX = "model.diffusion_model."
TEXT_ENCODER_1_KEY_PREFIX = "conditioner.embedders.0.transformer."
TEXT_ENCODER_2_KEY_PREFIX = "conditioner.embedders.1.model."
VAE_KEY_PREFIX = "first_stage_model."

TEXT_ENCODER_1_CONFIG = CLIPTextConfig(
    vocab_size=49408,
    hidden_size=768,
    intermediate_size=3072,
    num_hidden_layers=12,
    num_attention_heads=12,
    max_position_embeddings=77,
    hidden_act="quick_gelu",
    layer_norm_eps=1e-05,
    dropout=0.0,
    attention_dropout=0.0,
    initializer_range=0.02,
    initializer_factor=1.0,
    pad_token_id=1,
    bos_token_id=0,
    eos_token_id=2,
    model_type="clip_text_model",
    projection_dim=768,
    # torch_dtype="float32",
    # transformers_version="4.25.0.dev0",
)

TEXT_ENCODER_2_CONFIG = CLIPTextConfig(
    vocab_size=49408,
    hidden_size=1280,
    intermediate_size=5120,
    num_hidden_layers=32,
    num_attention_heads=20,
    max_position_embeddings=77,
    hidden_act="gelu",
    layer_norm_eps=1e-05,
    dropout=0.0,
    attention_dropout=0.0,
    initializer_range=0.02,
    initializer_factor=1.0,
    pad_token_id=1,
    bos_token_id=0,
    eos_token_id=2,
    model_type="clip_text_model",
    projection_dim=1280,
    # torch_dtype="float32",
    # transformers_version="4.25.0.dev0",
)


def create_vae_diffusers_config():
    """
    Creates a config for the diffusers based on the config of the LDM model.
    """
    # vae_params = original_config.model.params.first_stage_config.params.ddconfig
    # _ = original_config.model.params.first_stage_config.params.embed_dim
    block_out_channels = [VAE_PARAMS_CH * mult for mult in VAE_PARAMS_CH_MULT]
    down_block_types = ["DownEncoderBlock2D"] * len(block_out_channels)
    up_block_types = ["UpDecoderBlock2D"] * len(block_out_channels)

    config = dict(
        sample_size=VAE_PARAMS_RESOLUTION,
        in_channels=VAE_PARAMS_IN_CHANNELS,
        out_channels=VAE_PARAMS_OUT_CH,
        down_block_types=tuple(down_block_types),
        up_block_types=tuple(up_block_types),
        block_out_channels=tuple(block_out_channels),
        latent_channels=VAE_PARAMS_Z_CHANNELS,
        layers_per_block=VAE_PARAMS_NUM_RES_BLOCKS,
    )
    return config


def convert_ldm_vae_checkpoint(checkpoint, config):
    # extract state dict for VAE
    vae_state_dict = {}
    vae_key = "first_stage_model."
    keys = list(checkpoint.keys())
    for key in keys:
        if key.startswith(vae_key):
            vae_state_dict[key.replace(vae_key, "")] = checkpoint.get(key)
    # if len(vae_state_dict) == 0:
    #   # 渡されたcheckpointは.ckptから読み込んだcheckpointではなくvaeのstate_dict
    #   vae_state_dict = checkpoint

    new_checkpoint = {}

    new_checkpoint["encoder.conv_in.weight"] = vae_state_dict["encoder.conv_in.weight"]
    new_checkpoint["encoder.conv_in.bias"] = vae_state_dict["encoder.conv_in.bias"]
    new_checkpoint["encoder.conv_out.weight"] = vae_state_dict["encoder.conv_out.weight"]
    new_checkpoint["encoder.conv_out.bias"] = vae_state_dict["encoder.conv_out.bias"]
    new_checkpoint["encoder.conv_norm_out.weight"] = vae_state_dict["encoder.norm_out.weight"]
    new_checkpoint["encoder.conv_norm_out.bias"] = vae_state_dict["encoder.norm_out.bias"]

    new_checkpoint["decoder.conv_in.weight"] = vae_state_dict["decoder.conv_in.weight"]
    new_checkpoint["decoder.conv_in.bias"] = vae_state_dict["decoder.conv_in.bias"]
    new_checkpoint["decoder.conv_out.weight"] = vae_state_dict["decoder.conv_out.weight"]
    new_checkpoint["decoder.conv_out.bias"] = vae_state_dict["decoder.conv_out.bias"]
    new_checkpoint["decoder.conv_norm_out.weight"] = vae_state_dict["decoder.norm_out.weight"]
    new_checkpoint["decoder.conv_norm_out.bias"] = vae_state_dict["decoder.norm_out.bias"]

    new_checkpoint["quant_conv.weight"] = vae_state_dict["quant_conv.weight"]
    new_checkpoint["quant_conv.bias"] = vae_state_dict["quant_conv.bias"]
    new_checkpoint["post_quant_conv.weight"] = vae_state_dict["post_quant_conv.weight"]
    new_checkpoint["post_quant_conv.bias"] = vae_state_dict["post_quant_conv.bias"]

    # Retrieves the keys for the encoder down blocks only
    num_down_blocks = len({".".join(layer.split(".")[:3]) for layer in vae_state_dict if "encoder.down" in layer})
    down_blocks = {layer_id: [key for key in vae_state_dict if f"down.{layer_id}" in key] for layer_id in range(num_down_blocks)}

    # Retrieves the keys for the decoder up blocks only
    num_up_blocks = len({".".join(layer.split(".")[:3]) for layer in vae_state_dict if "decoder.up" in layer})
    up_blocks = {layer_id: [key for key in vae_state_dict if f"up.{layer_id}" in key] for layer_id in range(num_up_blocks)}

    for i in range(num_down_blocks):
        resnets = [key for key in down_blocks[i] if f"down.{i}" in key and f"down.{i}.downsample" not in key]

        if f"encoder.down.{i}.downsample.conv.weight" in vae_state_dict:
            new_checkpoint[f"encoder.down_blocks.{i}.downsamplers.0.conv.weight"] = vae_state_dict.pop(
                f"encoder.down.{i}.downsample.conv.weight"
            )
            new_checkpoint[f"encoder.down_blocks.{i}.downsamplers.0.conv.bias"] = vae_state_dict.pop(
                f"encoder.down.{i}.downsample.conv.bias"
            )

        paths = renew_vae_resnet_paths(resnets)
        meta_path = {"old": f"down.{i}.block", "new": f"down_blocks.{i}.resnets"}
        assign_to_checkpoint(paths, new_checkpoint, vae_state_dict, additional_replacements=[meta_path], config=config)

    mid_resnets = [key for key in vae_state_dict if "encoder.mid.block" in key]
    num_mid_res_blocks = 2
    for i in range(1, num_mid_res_blocks + 1):
        resnets = [key for key in mid_resnets if f"encoder.mid.block_{i}" in key]

        paths = renew_vae_resnet_paths(resnets)
        meta_path = {"old": f"mid.block_{i}", "new": f"mid_block.resnets.{i - 1}"}
        assign_to_checkpoint(paths, new_checkpoint, vae_state_dict, additional_replacements=[meta_path], config=config)

    mid_attentions = [key for key in vae_state_dict if "encoder.mid.attn" in key]
    paths = renew_vae_attention_paths(mid_attentions)
    meta_path = {"old": "mid.attn_1", "new": "mid_block.attentions.0"}
    assign_to_checkpoint(paths, new_checkpoint, vae_state_dict, additional_replacements=[meta_path], config=config)
    conv_attn_to_linear(new_checkpoint)

    for i in range(num_up_blocks):
        block_id = num_up_blocks - 1 - i
        resnets = [key for key in up_blocks[block_id] if f"up.{block_id}" in key and f"up.{block_id}.upsample" not in key]

        if f"decoder.up.{block_id}.upsample.conv.weight" in vae_state_dict:
            new_checkpoint[f"decoder.up_blocks.{i}.upsamplers.0.conv.weight"] = vae_state_dict[
                f"decoder.up.{block_id}.upsample.conv.weight"
            ]
            new_checkpoint[f"decoder.up_blocks.{i}.upsamplers.0.conv.bias"] = vae_state_dict[
                f"decoder.up.{block_id}.upsample.conv.bias"
            ]

        paths = renew_vae_resnet_paths(resnets)
        meta_path = {"old": f"up.{block_id}.block", "new": f"up_blocks.{i}.resnets"}
        assign_to_checkpoint(paths, new_checkpoint, vae_state_dict, additional_replacements=[meta_path], config=config)

    mid_resnets = [key for key in vae_state_dict if "decoder.mid.block" in key]
    num_mid_res_blocks = 2
    for i in range(1, num_mid_res_blocks + 1):
        resnets = [key for key in mid_resnets if f"decoder.mid.block_{i}" in key]

        paths = renew_vae_resnet_paths(resnets)
        meta_path = {"old": f"mid.block_{i}", "new": f"mid_block.resnets.{i - 1}"}
        assign_to_checkpoint(paths, new_checkpoint, vae_state_dict, additional_replacements=[meta_path], config=config)

    mid_attentions = [key for key in vae_state_dict if "decoder.mid.attn" in key]
    paths = renew_vae_attention_paths(mid_attentions)
    meta_path = {"old": "mid.attn_1", "new": "mid_block.attentions.0"}
    assign_to_checkpoint(paths, new_checkpoint, vae_state_dict, additional_replacements=[meta_path], config=config)
    conv_attn_to_linear(new_checkpoint)
    return new_checkpoint


def renew_resnet_paths(old_list, n_shave_prefix_segments=0):
    """
    Updates paths inside resnets to the new naming scheme (local renaming)
    """
    mapping = []
    for old_item in old_list:
        new_item = old_item.replace("in_layers.0", "norm1")
        new_item = new_item.replace("in_layers.2", "conv1")

        new_item = new_item.replace("out_layers.0", "norm2")
        new_item = new_item.replace("out_layers.3", "conv2")

        new_item = new_item.replace("emb_layers.1", "time_emb_proj")
        new_item = new_item.replace("skip_connection", "conv_shortcut")

        new_item = shave_segments(new_item, n_shave_prefix_segments=n_shave_prefix_segments)

        mapping.append({"old": old_item, "new": new_item})

    return mapping


def shave_segments(path, n_shave_prefix_segments=1):
    """
    Removes segments. Positive values shave the first segments, negative shave the last segments.
    """
    if n_shave_prefix_segments >= 0:
        return ".".join(path.split(".")[n_shave_prefix_segments:])
    else:
        return ".".join(path.split(".")[:n_shave_prefix_segments])


def renew_vae_resnet_paths(old_list, n_shave_prefix_segments=0):
    """
    Updates paths inside resnets to the new naming scheme (local renaming)
    """
    mapping = []
    for old_item in old_list:
        new_item = old_item

        new_item = new_item.replace("nin_shortcut", "conv_shortcut")
        new_item = shave_segments(new_item, n_shave_prefix_segments=n_shave_prefix_segments)

        mapping.append({"old": old_item, "new": new_item})

    return mapping


def renew_attention_paths(old_list, n_shave_prefix_segments=0):
    """
    Updates paths inside attentions to the new naming scheme (local renaming)
    """
    mapping = []
    for old_item in old_list:
        new_item = old_item

        #         new_item = new_item.replace('norm.weight', 'group_norm.weight')
        #         new_item = new_item.replace('norm.bias', 'group_norm.bias')

        #         new_item = new_item.replace('proj_out.weight', 'proj_attn.weight')
        #         new_item = new_item.replace('proj_out.bias', 'proj_attn.bias')

        #         new_item = shave_segments(new_item, n_shave_prefix_segments=n_shave_prefix_segments)

        mapping.append({"old": old_item, "new": new_item})

    return mapping


def renew_vae_attention_paths(old_list, n_shave_prefix_segments=0):
    """
    Updates paths inside attentions to the new naming scheme (local renaming)
    """
    mapping = []
    for old_item in old_list:
        new_item = old_item

        new_item = new_item.replace("norm.weight", "group_norm.weight")
        new_item = new_item.replace("norm.bias", "group_norm.bias")

        if diffusers.__version__ < "0.17.0":
            new_item = new_item.replace("q.weight", "query.weight")
            new_item = new_item.replace("q.bias", "query.bias")

            new_item = new_item.replace("k.weight", "key.weight")
            new_item = new_item.replace("k.bias", "key.bias")

            new_item = new_item.replace("v.weight", "value.weight")
            new_item = new_item.replace("v.bias", "value.bias")

            new_item = new_item.replace("proj_out.weight", "proj_attn.weight")
            new_item = new_item.replace("proj_out.bias", "proj_attn.bias")
        else:
            new_item = new_item.replace("q.weight", "to_q.weight")
            new_item = new_item.replace("q.bias", "to_q.bias")

            new_item = new_item.replace("k.weight", "to_k.weight")
            new_item = new_item.replace("k.bias", "to_k.bias")

            new_item = new_item.replace("v.weight", "to_v.weight")
            new_item = new_item.replace("v.bias", "to_v.bias")

            new_item = new_item.replace("proj_out.weight", "to_out.0.weight")
            new_item = new_item.replace("proj_out.bias", "to_out.0.bias")

        new_item = shave_segments(new_item, n_shave_prefix_segments=n_shave_prefix_segments)

        mapping.append({"old": old_item, "new": new_item})

    return mapping


def assign_to_checkpoint(
    paths, checkpoint, old_checkpoint, attention_paths_to_split=None, additional_replacements=None, config=None
):
    """
    This does the final conversion step: take locally converted weights and apply a global renaming
    to them. It splits attention layers, and takes into account additional replacements
    that may arise.

    Assigns the weights to the new checkpoint.
    """
    assert isinstance(paths, list), "Paths should be a list of dicts containing 'old' and 'new' keys."

    # Splits the attention layers into three variables.
    if attention_paths_to_split is not None:
        for path, path_map in attention_paths_to_split.items():
            old_tensor = old_checkpoint[path]
            channels = old_tensor.shape[0] // 3

            target_shape = (-1, channels) if len(old_tensor.shape) == 3 else (-1)

            num_heads = old_tensor.shape[0] // config["num_head_channels"] // 3

            old_tensor = old_tensor.reshape((num_heads, 3 * channels // num_heads) + old_tensor.shape[1:])
            query, key, value = old_tensor.split(channels // num_heads, dim=1)

            checkpoint[path_map["query"]] = query.reshape(target_shape)
            checkpoint[path_map["key"]] = key.reshape(target_shape)
            checkpoint[path_map["value"]] = value.reshape(target_shape)

    for path in paths:
        new_path = path["new"]

        # These have already been assigned
        if attention_paths_to_split is not None and new_path in attention_paths_to_split:
            continue

        # Global renaming happens here
        new_path = new_path.replace("middle_block.0", "mid_block.resnets.0")
        new_path = new_path.replace("middle_block.1", "mid_block.attentions.0")
        new_path = new_path.replace("middle_block.2", "mid_block.resnets.1")

        if additional_replacements is not None:
            for replacement in additional_replacements:
                new_path = new_path.replace(replacement["old"], replacement["new"])

        # proj_attn.weight has to be converted from conv 1D to linear
        reshaping = False
        if diffusers.__version__ < "0.17.0":
            if "proj_attn.weight" in new_path:
                reshaping = True
        else:
            if ".attentions." in new_path and ".0.to_" in new_path and old_checkpoint[path["old"]].ndim > 2:
                reshaping = True

        if reshaping:
            checkpoint[new_path] = old_checkpoint[path["old"]][:, :, 0, 0]
        else:
            checkpoint[new_path] = old_checkpoint[path["old"]]


def conv_attn_to_linear(checkpoint):
    keys = list(checkpoint.keys())
    attn_keys = ["query.weight", "key.weight", "value.weight"]
    for key in keys:
        if ".".join(key.split(".")[-2:]) in attn_keys:
            if checkpoint[key].ndim > 2:
                checkpoint[key] = checkpoint[key][:, :, 0, 0]
        elif "proj_attn.weight" in key:
            if checkpoint[key].ndim > 2:
                checkpoint[key] = checkpoint[key][:, :, 0]


def is_safetensors(path):
    return os.path.splitext(path)[1].lower() == ".safetensors"

# load state_dict without allocating new tensors


def _load_state_dict_on_device(model, state_dict, device, dtype=None):
    # dtype will use fp32 as default
    missing_keys = list(model.state_dict().keys() - state_dict.keys())
    unexpected_keys = list(state_dict.keys() - model.state_dict().keys())

    # similar to model.load_state_dict()
    for k in list(state_dict.keys()):
        set_module_tensor_to_device(model, k, device, value=state_dict.pop(k), dtype=dtype)
    if not missing_keys and not unexpected_keys:
        return "<All keys matched successfully>"
    elif not missing_keys:
        return "<All keys matched successfully> " + f"but there are {len(unexpected_keys)} unexpected keys: {unexpected_keys}"
    elif not unexpected_keys:
        return f"{len(missing_keys)} missing keys: {missing_keys}"
    return f"{len(missing_keys)} missing keys: {missing_keys} and {len(unexpected_keys)} unexpected keys: {unexpected_keys}"

    # error_msgs
    # error_msgs: List[str] = []
    # if missing_keys:
    #     error_msgs.insert(0, "Missing key(s) in state_dict: {}. ".format(", ".join('"{}"'.format(k) for k in missing_keys)))
    # if unexpected_keys:
    #     error_msgs.insert(0, "Unexpected key(s) in state_dict: {}. ".format(", ".join('"{}"'.format(k) for k in unexpected_keys)))

    # raise RuntimeError("Error(s) in loading state_dict for {}:\n\t{}".format(model.__class__.__name__, "\n\t".join(error_msgs)))


def load_models_from_sdxl_checkpoint(ckpt_path, device='cpu', dtype=None, nnet_class=SDXLUNet2DConditionModel):
    r"""
    Load SDXL components from a local checkpoint file.
    """
    if is_safetensors(ckpt_path):
        state_dict = load_file(ckpt_path)
        ckpt_info = None
    else:
        checkpoint = torch.load(ckpt_path, map_location=device)
        state_dict = checkpoint.get("state_dict", checkpoint)
        epoch = checkpoint.get("epoch", 0)
        global_step = checkpoint.get("global_step", 0)
        ckpt_info = (epoch, global_step)

    models = load_models_from_sdxl_state_dict(state_dict, device=device, dtype=dtype, nnet_class=nnet_class)
    models['ckpt_info'] = ckpt_info
    return models


def convert_sdxl_text_encoder_2_checkpoint(checkpoint, max_length):
    SDXL_KEY_PREFIX = "conditioner.embedders.1.model."

    # SD2のと、基本的には同じ。logit_scaleを後で使うので、それを追加で返す
    # logit_scaleはcheckpointの保存時に使用する
    def convert_key(key):
        # common conversion
        key = key.replace(SDXL_KEY_PREFIX + "transformer.", "text_model.encoder.")
        key = key.replace(SDXL_KEY_PREFIX, "text_model.")

        if "resblocks" in key:
            # resblocks conversion
            key = key.replace(".resblocks.", ".layers.")
            if ".ln_" in key:
                key = key.replace(".ln_", ".layer_norm")
            elif ".mlp." in key:
                key = key.replace(".c_fc.", ".fc1.")
                key = key.replace(".c_proj.", ".fc2.")
            elif ".attn.out_proj" in key:
                key = key.replace(".attn.out_proj.", ".self_attn.out_proj.")
            elif ".attn.in_proj" in key:
                key = None  # 特殊なので後で処理する
            else:
                raise ValueError(f"unexpected key in SD: {key}")
        elif ".positional_embedding" in key:
            key = key.replace(".positional_embedding", ".embeddings.position_embedding.weight")
        elif ".text_projection" in key:
            key = key.replace("text_model.text_projection", "text_projection.weight")
        elif ".logit_scale" in key:
            key = None  # 後で処理する
        elif ".token_embedding" in key:
            key = key.replace(".token_embedding.weight", ".embeddings.token_embedding.weight")
        elif ".ln_final" in key:
            key = key.replace(".ln_final", ".final_layer_norm")
        # ckpt from comfy has this key: text_model.encoder.text_model.embeddings.position_ids
        elif ".embeddings.position_ids" in key:
            key = None  # remove this key: make position_ids by ourselves
        return key

    keys = list(checkpoint.keys())
    new_sd = {}
    for key in keys:
        new_key = convert_key(key)
        if new_key is None:
            continue
        new_sd[new_key] = checkpoint[key]

    # attnの変換
    for key in keys:
        if ".resblocks" in key and ".attn.in_proj_" in key:
            # 三つに分割
            values = torch.chunk(checkpoint[key], 3)

            key_suffix = ".weight" if "weight" in key else ".bias"
            key_pfx = key.replace(SDXL_KEY_PREFIX + "transformer.resblocks.", "text_model.encoder.layers.")
            key_pfx = key_pfx.replace("_weight", "")
            key_pfx = key_pfx.replace("_bias", "")
            key_pfx = key_pfx.replace(".attn.in_proj", ".self_attn.")
            new_sd[key_pfx + "q_proj" + key_suffix] = values[0]
            new_sd[key_pfx + "k_proj" + key_suffix] = values[1]
            new_sd[key_pfx + "v_proj" + key_suffix] = values[2]

    # original SD にはないので、position_idsを追加
    position_ids = torch.Tensor([list(range(max_length))]).to(torch.int64)
    new_sd["text_model.embeddings.position_ids"] = position_ids

    # logit_scale はDiffusersには含まれないが、保存時に戻したいので別途返す
    logit_scale = checkpoint.get(SDXL_KEY_PREFIX + "logit_scale", None)

    return new_sd, logit_scale


def load_models_from_sdxl_state_dict(state_dict, device='cpu', dtype=None, nnet_class=SDXLUNet2DConditionModel):
    vae_config = create_vae_diffusers_config()
    with init_empty_weights():
        unet = nnet_class()
        text_encoder1 = CLIPTextModel._from_config(TEXT_ENCODER_1_CONFIG)
        text_encoder2 = CLIPTextModelWithProjection(TEXT_ENCODER_2_CONFIG)
        vae = AutoencoderKL(**vae_config)
    unet_sd = {}
    text_encoder1_sd = {}
    text_encoder2_sd = {}
    vae_sd = {}
    for k, v in state_dict.items():
        if k.startswith(UNET_KEY_PREFIX):
            unet_sd[k[len(UNET_KEY_PREFIX):]] = v
        elif k.startswith(TEXT_ENCODER_1_KEY_PREFIX):
            text_encoder1_sd[k[len(TEXT_ENCODER_1_KEY_PREFIX):]] = v
        elif k.startswith(TEXT_ENCODER_2_KEY_PREFIX):
            text_encoder2_sd[k] = v
        elif k.startswith(VAE_KEY_PREFIX):
            vae_sd[k] = v
    text_encoder2_sd, logit_scale = convert_sdxl_text_encoder_2_checkpoint(text_encoder2_sd, max_length=77)
    # if 'text_model.embeddings.position_ids' in text_encoder1_sd:
    #     del text_encoder1_sd["text_model.embeddings.position_ids"]
    # if 'text_model.embeddings.position_ids' in text_encoder2_sd:
    #     del text_encoder2_sd["text_model.embeddings.position_ids"]
    vae_sd = convert_ldm_vae_checkpoint(vae_sd, vae_config)

    _load_state_dict_on_device(unet, unet_sd, device=device, dtype=dtype)
    _load_state_dict_on_device(text_encoder1, text_encoder1_sd, device=device)
    _load_state_dict_on_device(text_encoder2, text_encoder2_sd, device=device)
    _load_state_dict_on_device(vae, vae_sd, device=device, dtype=dtype)
    text_encoder1 = text_encoder1.to(device=device)
    text_encoder2 = text_encoder2.to(device=device)

    return {'nnet': unet, 'text_encoder1': text_encoder1, 'text_encoder2': text_encoder2, 'vae': vae, 'logit_scale': logit_scale}


def load_sdxl_tokenizers(tokenizer_cache_dir=None, max_token_length=75):
    name_or_paths = [TOKENIZER1_PATH, TOKENIZER2_PATH]
    tokenizers = []
    for i, name_or_path in enumerate(name_or_paths):
        tokenizer: CLIPTokenizer = None
        if tokenizer_cache_dir:
            local_tokenizer_path = os.path.join(tokenizer_cache_dir, name_or_path.replace("/", "_"))
            if os.path.exists(local_tokenizer_path):
                print(f"load tokenizer from cache: {local_tokenizer_path}")
                tokenizer = CLIPTokenizer.from_pretrained(local_tokenizer_path)

        if tokenizer is None:
            tokenizer = CLIPTokenizer.from_pretrained(name_or_path)

        if tokenizer_cache_dir and not os.path.exists(local_tokenizer_path):
            print(f"save Tokenizer to cache: {local_tokenizer_path}")
            tokenizer.save_pretrained(local_tokenizer_path)

        if i == 1:
            tokenizer.pad_token_id = 0  # fix pad token id to make same as open clip tokenizer

        tokenizers.append(tokenizer)

    if max_token_length is not None:
        print(f"update token length: {max_token_length}")

    return tokenizers
