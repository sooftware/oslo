# coding=utf-8
# Copyright 2021 TUNiB Inc.
# Copyright 2021 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" GPT Neo model configuration """

from collections import OrderedDict
from typing import Any, Dict, Iterable, Mapping, Optional

from torch import nn
from transformers import PreTrainedTokenizer, TensorType, is_torch_available
from transformers.configuration_utils import PretrainedConfig
from transformers.onnx import OnnxConfigWithPast
from transformers.utils import logging

from oslo import (
    ColumnParallelLinear,
    Layer,
    LayerPolicy,
    RowParallelLinear,
    VocabParallelEmbedding,
)

logger = logging.get_logger(__name__)

GPT_NEO_PRETRAINED_CONFIG_ARCHIVE_MAP = {
    "EleutherAI/gpt-neo-1.3B": "https://huggingface.co/EleutherAI/gpt-neo-1.3B/resolve/main/config.json",
    # See all GPTNeo models at https://huggingface.co/models?filter=gpt_neo
}


class GPTNeoConfig(PretrainedConfig):
    r"""
    This is the configuration class to store the configuration of a :class:`~transformers.GPTNeoModel`. It is used to
    instantiate a GPT Neo model according to the specified arguments, defining the model architecture. Instantiating a
    configuration with the defaults will yield a similar configuration to that of the GPTNeo `gpt-neo-1.3B
    <https://huggingface.co/EleutherAI/gpt-neo-1.3B>`__ architecture.

    Configuration objects inherit from :class:`~transformers.PretrainedConfig` and can be used to control the model
    outputs. Read the documentation from :class:`~transformers.PretrainedConfig` for more information.


    Args:
        vocab_size (:obj:`int`, `optional`, defaults to 50257):
            Vocabulary size of the GPT Neo model. Defines the number of different tokens that can be represented by the
            :obj:`inputs_ids` passed when calling :class:`~transformers.GPTNeoModel`. Vocabulary size of the model.
            Defines the different tokens that can be represented by the `inputs_ids` passed to the forward method of
            :class:`~transformers.GPTNeoModel`.
        attention_types (:obj:`List`, `optional`, defaults to :obj:`[[["global", "local"], 12]]`):
            The type of attention for each layer in a :obj:`List` of the following format :obj:`[[["attention_type"],
            num_layerss]]` e.g. for a 24 layer model :obj:`[[["global"], 24]]` or :obj:`[[["global", "local"], 12]]`
            Choose the value of ``attention_type`` from :obj:`["global", "local"]`
        hidden_size (:obj:`int`, `optional`, defaults to 2048):
            Dimensionality of the encoder layers and the pooler layer.
        num_layers (:obj:`int`, `optional`, defaults to 24):
            Number of hidden layers in the Transformer encoder.
        num_heads (:obj:`int`, `optional`, defaults to 16):
            Number of attention heads for each attention layer in the Transformer encoder.
        intermediate_size (:obj:`int`, `optional`, defaults to 8192):
            Dimensionality of the "intermediate" (i.e., feed-forward) layer in the Transformer encoder.
        activation_function (:obj:`str` or :obj:`function`, `optional`, defaults to :obj:`"gelu_new"`):
            The non-linear activation function (function or string) in the encoder and pooler. If string,
            :obj:`"gelu"`, :obj:`"relu"`, :obj:`"selu"` and :obj:`"gelu_new"` are supported.
        embed_dropout (:obj:`float`, `optional`, defaults to 0.0):
            The dropout probabilitiy for all fully connected layers in the embeddings, encoder, and pooler.
        attention_dropout (:obj:`float`, `optional`, defaults to 0.0):
            The dropout ratio for the attention probabilities.
        max_position_embeddings (:obj:`int`, `optional`, defaults to 2048):
            The maximum sequence length that this model might ever be used with. Typically set this to something large
            just in case (e.g., 512 or 1024 or 2048).
        type_vocab_size (:obj:`int`, `optional`, defaults to 2):
            The vocabulary size of the :obj:`token_type_ids` passed when calling :class:`~transformers.GPTNeoModel`.
        initializer_range (:obj:`float`, `optional`, defaults to 0.02):
            The standard deviation of the truncated_normal_initializer for initializing all weight matrices.
        layer_norm_epsilon (:obj:`float`, `optional`, defaults to 1e-5):
            The epsilon used by the layer normalization layers.
        use_cache (:obj:`bool`, `optional`, defaults to :obj:`True`):
            Whether or not the model should return the last key/values attentions (not used by all models). Only
            relevant if ``config.is_decoder=True``.

        Example::

            >>> from transformers import GPTNeoModel, GPTNeoConfig

            >>> # Initializing a GPTNeo EleutherAI/gpt-neo-1.3B style configuration
            >>> configuration = GPTNeoConfig()

            >>> # Initializing a model from the EleutherAI/gpt-neo-1.3B style configuration
            >>> model = GPTNeoModel(configuration)

            >>> # Accessing the model configuration
            >>> configuration = model.config
    """
    model_type = "gpt_neo"
    keys_to_ignore_at_inference = ["past_key_values"]
    attribute_map = {
        "num_attention_heads": "num_heads",
        "num_hidden_layers": "num_layers",
    }

    def __init__(
        self,
        vocab_size=50257,
        max_position_embeddings=2048,
        hidden_size=2048,
        num_layers=24,
        attention_types=[[["global", "local"], 12]],
        num_heads=16,
        intermediate_size=None,
        window_size=256,
        activation_function="gelu_new",
        resid_dropout=0.0,
        embed_dropout=0.0,
        attention_dropout=0.0,
        layer_norm_epsilon=1e-5,
        initializer_range=0.02,
        summary_type="cls_index",
        summary_use_proj=True,
        summary_activation=None,
        summary_proj_to_labels=True,
        summary_first_dropout=0.1,
        use_cache=True,
        bos_token_id=50256,
        eos_token_id=50256,
        **kwargs,
    ):
        self.vocab_size = vocab_size
        self.max_position_embeddings = max_position_embeddings
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.intermediate_size = intermediate_size
        self.window_size = window_size
        self.activation_function = activation_function
        self.resid_dropout = resid_dropout
        self.embed_dropout = embed_dropout
        self.attention_dropout = attention_dropout
        self.layer_norm_epsilon = layer_norm_epsilon
        self.initializer_range = initializer_range
        self.summary_type = summary_type
        self.summary_use_proj = summary_use_proj
        self.summary_activation = summary_activation
        self.summary_first_dropout = summary_first_dropout
        self.summary_proj_to_labels = summary_proj_to_labels
        self.use_cache = use_cache

        self.bos_token_id = bos_token_id
        self.eos_token_id = eos_token_id

        self.attention_types = attention_types
        self.attention_layers = self.expand_attention_types_params(attention_types)

        if len(self.attention_layers) != self.num_layers:
            raise ValueError(
                "Configuration for convolutional module is incorrect. "
                "It is required that `len(config.attention_layers)` == `config.num_layers` "
                f"but is `len(config.attention_layers) = {len(self.attention_layers)}`, "
                f"`config.num_layers = {self.num_layers}`. "
                "`config.attention_layers` is prepared using `config.attention_types`. "
                "Please verify the value of `config.attention_types` argument."
            )

        super().__init__(bos_token_id=bos_token_id, eos_token_id=eos_token_id, **kwargs)

    @staticmethod
    def expand_attention_types_params(attention_types):
        attentions = []
        for item in attention_types:
            for _ in range(item[1]):
                attentions.extend(item[0])
        return attentions


def custom_unfold(input, dimension, size, step):
    """Custom torch.Tensor.unfold implementation to enable the export to ONNX."""
    import torch

    shape = input.size()
    rank = len(shape)
    sizedim = shape[dimension]

    low_indices = torch.arange(0, sizedim, step)
    min_length = torch.div(sizedim - size, step, rounding_mode="floor") + 1
    indices = torch.arange(size) + low_indices[:min_length][:, None]

    s = [slice(None)] * rank
    s[dimension] = indices
    sliced = input[s]

    perm = list(range(0, rank + 1))
    perm.append(perm.pop(dimension + 1))

    return sliced.permute(perm)


def custom_get_block_length_and_num_blocks(seq_length, window_size):
    """
    Custom implementation for GPTNeoAttentionMixin._get_block_length_and_num_blocks to enable the export to ONNX as
    original implementation uses Python variables and control flow.
    """
    import torch

    candidates = torch.arange(1, window_size)
    remainders = torch.remainder(seq_length, candidates)
    divisor_indices = remainders == 0
    divisors = candidates[divisor_indices]
    largest_divisor = torch.max(divisors)
    return largest_divisor, torch.div(
        seq_length, largest_divisor, rounding_mode="floor"
    )


class GPTNeoOnnxConfig(OnnxConfigWithPast):
    @property
    def inputs(self) -> Mapping[str, Mapping[int, str]]:
        common_inputs = OrderedDict({"input_ids": {0: "batch", 1: "sequence"}})
        if self.use_past:
            for i in range(self._config.num_layers):
                common_inputs[f"past_key_values.{i}.key"] = {
                    0: "batch",
                    2: "past_sequence",
                }
                common_inputs[f"past_key_values.{i}.value"] = {
                    0: "batch",
                    2: "past_sequence",
                }

            common_inputs["attention_mask"] = {
                0: "batch",
                1: "past_sequence + sequence",
            }
        else:
            common_inputs["attention_mask"] = {0: "batch", 1: "sequence"}

        return common_inputs

    @property
    def outputs(self) -> Mapping[str, Mapping[int, str]]:
        common_outputs = super().outputs
        if self.use_past:
            for i in range(self._config.num_layers):
                common_outputs[f"present.{i}.key"] = {
                    0: "batch",
                    2: "past_sequence + sequence",
                }
                common_outputs[f"present.{i}.value"] = {
                    0: "batch",
                    2: "past_sequence + sequence",
                }

            return common_outputs

        return common_outputs

    def generate_dummy_inputs(
        self,
        tokenizer: PreTrainedTokenizer,
        batch_size: int = -1,
        seq_length: int = -1,
        is_pair: bool = False,
        framework: Optional[TensorType] = None,
    ) -> Mapping[str, Any]:
        common_inputs = super().generate_dummy_inputs(
            tokenizer, batch_size, seq_length, is_pair, framework
        )

        # We need to order the input in the way they appears in the forward()
        ordered_inputs = OrderedDict({"input_ids": common_inputs["input_ids"]})

        # Need to add the past_keys
        if self.use_past:
            if not is_torch_available():
                raise ValueError(
                    "Cannot generate dummy past_keys inputs without PyTorch installed."
                )
            else:
                import torch

                batch = common_inputs["input_ids"].shape[0]
                past_shape = (
                    batch,
                    self._config.num_heads,
                    1,
                    self._config.hidden_size // self._config.num_heads,
                )
                ordered_inputs["past_key_values"] = [
                    (torch.zeros(past_shape), torch.zeros(past_shape))
                    for _ in range(self._config.num_layers)
                ]

        ordered_inputs["attention_mask"] = common_inputs["attention_mask"]
        if self.use_past:
            ordered_inputs["attention_mask"] = torch.cat(
                [ordered_inputs["attention_mask"], torch.ones(batch, 1)], dim=1
            )

        return ordered_inputs

    @staticmethod
    def flatten_output_collection_property(
        name: str, field: Iterable[Any]
    ) -> Dict[str, Any]:
        if name in ["present", "past_key_values"]:
            flatten_output = {}
            for idx, t in enumerate(field):
                flatten_output[f"{name}.{idx}.key"] = t[0]
                flatten_output[f"{name}.{idx}.value"] = t[1]

            return flatten_output

        return super().flatten_output_collection_property(name, field)


class GPTNeoLayerPolicy(LayerPolicy):
    @staticmethod
    def reduce_arguments(layer, world_size, config):
        layer.attn.attention.embed_dim = config.hidden_size // world_size
        layer.attn.attention.num_heads = config.num_heads // world_size

    @staticmethod
    def fused_modules():
        from oslo.models.gpt_neo.modeling_gpt_neo import (
            FusedGPTNeoMLP,
            FusedGPTNeoSelfAttention,
            GPTNeoMLP,
            GPTNeoSelfAttention,
        )

        return {
            GPTNeoSelfAttention: FusedGPTNeoSelfAttention,
            GPTNeoMLP: FusedGPTNeoMLP,
        }

    @staticmethod
    def attn_qkv(layer, config):
        return [
            Layer(
                module=layer.attn.attention.q_proj,
                weight=layer.attn.attention.q_proj.weight,
                replace={nn.Linear: ColumnParallelLinear},
            ),
            Layer(
                module=layer.attn.attention.k_proj,
                weight=layer.attn.attention.k_proj.weight,
                replace={nn.Linear: ColumnParallelLinear},
            ),
            Layer(
                module=layer.attn.attention.v_proj,
                weight=layer.attn.attention.v_proj.weight,
                replace={nn.Linear: ColumnParallelLinear},
            ),
        ]

    @staticmethod
    def attn_out(layer, config):
        return [
            Layer(
                module=layer.attn.attention.out_proj,
                weight=layer.attn.attention.out_proj.weight,
                bias=layer.attn.attention.out_proj.bias,
                replace={nn.Linear: RowParallelLinear},
            ),
        ]

    @staticmethod
    def attn_norm(layer, config):
        return [
            Layer(
                module=layer.ln_1,
                weight=layer.ln_1.weight,
                bias=layer.ln_1.bias,
                parallel=False,
            ),
        ]

    @staticmethod
    def mlp_in(layer, config):
        return [
            Layer(
                module=layer.mlp.c_fc,
                weight=layer.mlp.c_fc.weight,
                bias=layer.mlp.c_fc.bias,
                replace={nn.Linear: ColumnParallelLinear},
            )
        ]

    @staticmethod
    def mlp_out(layer, config):
        return [
            Layer(
                module=layer.mlp.c_proj,
                weight=layer.mlp.c_proj.weight,
                bias=layer.mlp.c_proj.bias,
                replace={nn.Linear: RowParallelLinear},
            )
        ]

    @staticmethod
    def mlp_norm(layer, config):
        return [
            Layer(
                module=layer.ln_2,
                weight=layer.ln_2.weight,
                bias=layer.ln_2.bias,
                parallel=False,
            ),
        ]

    @staticmethod
    def word_embedding(model, config):
        return [
            Layer(
                module=model.wte,
                weight=model.wte.weight,
                replace={nn.Embedding: VocabParallelEmbedding},
            ),
        ]

    @staticmethod
    def preblock_layers(model, config):
        return [
            Layer(
                module=model.wpe,
                weight=model.wpe.weight,
                parallel=False,
            ),
        ]

    @staticmethod
    def block_layers(model, config):
        return model.h

    @staticmethod
    def postblock_layers(model, config):
        return [
            Layer(
                module=model.ln_f,
                weight=model.ln_f.weight,
                bias=model.ln_f.bias,
                parallel=False,
            ),
        ]

    @staticmethod
    def copy_to_all(layer, config):
        return [
            Layer(
                bias=layer.attn.attention.bias,
                parallel=False,
            ),
            Layer(
                bias=layer.attn.attention.masked_bias,
                parallel=False,
            ),
        ]

    @staticmethod
    def original_layer_class():
        from oslo.models.gpt_neo.modeling_gpt_neo import GPTNeoBlock

        return GPTNeoBlock
