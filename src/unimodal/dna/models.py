import torch
import torch.nn as nn
from einops.layers.torch import Rearrange
from src.unimodal.rna.mae import RnaMAEForPreTraining, RnaSurvivalModel, RnaMAEModel
from omegaconf import DictConfig

class DNAmEncoder(nn.Module):
    """
    A vanilla encoder based on 1-d convolution for DNAm data.
    """

    def __init__(self, embedding_dim: int, dropout: float) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv1d(1, 8, 9, 3),
            nn.GELU(),
            nn.BatchNorm1d(8),
            nn.Dropout(dropout),
            nn.Conv1d(8, 32, 9, 3),
            nn.GELU(),
            nn.BatchNorm1d(32),
            nn.Dropout(dropout),
            nn.Conv1d(32, 64, 9, 3),
            nn.GELU(),
            nn.BatchNorm1d(64),
            nn.Dropout(dropout),
            nn.Conv1d(64, 128, 9, 3),
            nn.GELU(),
            nn.BatchNorm1d(128),
            nn.Dropout(dropout),
            nn.Conv1d(128, 256, 9, 3),
            nn.GELU(),
            nn.BatchNorm1d(256),
            nn.Dropout(dropout),
            nn.Conv1d(256, embedding_dim, 9, 3),
            nn.GELU(),
            nn.BatchNorm1d(embedding_dim),
            nn.Dropout(dropout),
            nn.AdaptiveAvgPool1d(1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.encoder(x).squeeze(-1)


class DNAmDecoder(nn.Module):
    """
    A vanilla decoder based on 1-d transposed convolution for DNAm data.
    """

    def __init__(self, embedding_dim: int, dropout: float) -> None:
        super().__init__()
        self.decoder = nn.Sequential(
            nn.Linear(embedding_dim, embedding_dim * 33),
            Rearrange("b (n e) -> b n e", e=33),
            nn.GELU(),
            nn.BatchNorm1d(embedding_dim),
            nn.Dropout(dropout),
            nn.ConvTranspose1d(embedding_dim, 256, 9, 3),
            nn.GELU(),
            nn.BatchNorm1d(256),
            nn.Dropout(dropout),
            nn.ConvTranspose1d(256, 128, 9, 3, 1),
            nn.GELU(),
            nn.BatchNorm1d(128),
            nn.Dropout(dropout),
            nn.ConvTranspose1d(128, 64, 9, 3, 1),
            nn.GELU(),
            nn.BatchNorm1d(64),
            nn.Dropout(dropout),
            nn.ConvTranspose1d(64, 32, 9, 3, 2),
            nn.GELU(),
            nn.BatchNorm1d(32),
            nn.Dropout(dropout),
            nn.ConvTranspose1d(32, 8, 9, 3, 1),
            nn.GELU(),
            nn.BatchNorm1d(8),
            nn.Dropout(dropout),
            nn.ConvTranspose1d(8, 1, 8, 3, 2),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.decoder(x)
        return x

class DNAmMAEModel(RnaMAEModel):
    def __init__(self, config):
        super().__init__(config)

class DNAmMAEForPreTraining(RnaMAEForPreTraining):
    def __init__(self, config):
        super().__init__(config)
        
class DNAmSurvivalModel(RnaSurvivalModel):
    def __init__(self, config):
        super().__init__(config)
 
 
class DNAmEncoderSurvival(DNAmEncoder):
    def __init__(self, embedding_dim: int, dropout: float, n_out: int) -> None:
        super().__init__(embedding_dim, dropout)
        self.projection = nn.Linear(embedding_dim, n_out)

        
    def forward(self, x: torch.Tensor, masks=None) -> torch.Tensor:
        x = super().forward(x)
        x = self.projection(x).squeeze(-1)
        return x    
               
def initialise_dnam_mae_model(cfg):
    return DNAmSurvivalModel(cfg)

def initialise_dnam_model(cfg: DictConfig):
    return DNAmEncoderSurvival(cfg.embedding_dim, cfg.dropout, cfg.output_dim)