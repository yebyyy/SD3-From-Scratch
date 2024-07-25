import torch
import torch.nn as nn
import torch.nn.functional as F
import math

class SelfAttention(nn.Module):

    def __init__(self, n_heads: int, d_embd: int, in_proj_bias=True, out_proj_bias=True):
        super().__init__()

        self.in_proj = nn.Linear(d_embd, 3 * d_embd, bias=in_proj_bias)  # W_q, W_k, W_v together
        self.out_proj = nn.Linear(d_embd, d_embd, bias=out_proj_bias)  # W_o
        self.n_heads = n_heads
        self.d_head = d_embd // n_heads

    def forward(self, x: torch.Tensor, causal_mask=False) -> torch.Tensor:
        # x: (batch_size, seq_length, d_embd)
        input_shape = x.shape

        batch_size, seq_length, d_embd = input_shape
        
        intermediate_shape = (batch_size, seq_length, self.n_heads, self.d_head)

        # (batch_size, seq_length, d_embd) -> (batch_size, seq_length, d_embd * 3) -> 3 * (batch_size, seq_length, d_embd)
        q, k, v = self.in_proj(x).chunk(3, dim=-1)

        # (batch_size, seq_length, d_embd) -> (batch_size, seq_length, n_heads, d_head) -> (batch_size, n_heads, seq_length, d_head)
        q = q.view(intermediate_shape).transpose(1, 2)
        v = v.view(intermediate_shape).transpose(1, 2)
        k = k.view(intermediate_shape).transpose(1, 2)

        # (batch_size, n_heads, seq_length, seq_length)
        weight = q @ k.transpose(-1, -2)

        if causal_mask:
            mask = torch.ones_like(weight, dtype=torch.bool).triu(1)  # triu: upper triangular part of a matrix
            weight.masked_fill_(mask, float('-inf'))

        weight /= math.sqrt(self.d_head)
        weight = F.softmax(weight, dim=-1)

        # (batch_size, n_heads, seq_length, seq_length) @ (batch_size, n_heads, seq_length, d_head) -> (batch_size, n_heads, seq_length, d_embd)
        output = weight @ v

        # (batch_size, seq_length, n_heads, d_embd)
        output.transpose(1, 2)

        # (batch_size, seq_length, d_embd)
        output = output.reshape(input_shape)

        # output @ W_o
        output = self.out_proj(output)
        return output