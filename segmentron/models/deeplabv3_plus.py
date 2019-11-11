import torch
import torch.nn as nn
import torch.nn.functional as F

from .segbase import SegBaseModel
from ..modules import _ConvBNReLU, SeparableConv2d, _ASPP, _FCNHead
from ..config import cfg
__all__ = ['DeepLabV3Plus', 'get_deeplabv3_plus', 'get_deeplabv3_plus_xception_voc']


class DeepLabV3Plus(SegBaseModel):
    r"""DeepLabV3Plus
    Parameters
    ----------
    nclass : int
        Number of categories for the training dataset.

    """

    def __init__(self, nclass):
        super(DeepLabV3Plus, self).__init__(nclass)
        if self.backbone.startswith('mobilenet'):
            c1_channels = 24
            c4_channels = 320
        else:
            c1_channels = 256
            c4_channels = 2048
        self.head = _DeepLabHead(nclass, c1_channels=c1_channels, c4_channels=c4_channels)
        if self.aux:
            self.auxlayer = _FCNHead(728, nclass)
        self.__setattr__('decoder', ['head', 'auxlayer'] if self.aux else ['head'])

    def forward(self, x):
        size = x.size()[2:]
        c1, _, c3, c4 = self.encoder(x)

        outputs = list()
        x = self.head(c4, c1)
        x = F.interpolate(x, size, mode='bilinear', align_corners=True)

        outputs.append(x)
        if self.aux:
            auxout = self.auxlayer(c3)
            auxout = F.interpolate(auxout, size, mode='bilinear', align_corners=True)
            outputs.append(auxout)
        return tuple(outputs)


class _DeepLabHead(nn.Module):
    def __init__(self, nclass, c1_channels=256, c4_channels=2048, norm_layer=nn.BatchNorm2d):
        super(_DeepLabHead, self).__init__()
        self.aspp = _ASPP(c4_channels, 256)
        self.c1_block = _ConvBNReLU(c1_channels, 48, 1, norm_layer=norm_layer)
        self.block = nn.Sequential(
            SeparableConv2d(304, 256, 3, norm_layer=norm_layer, relu_first=False),
            SeparableConv2d(256, 256, 3, norm_layer=norm_layer, relu_first=False),
            nn.Conv2d(256, nclass, 1))

    def forward(self, x, c1):
        size = c1.size()[2:]
        c1 = self.c1_block(c1)
        x = self.aspp(x)
        x = F.interpolate(x, size, mode='bilinear', align_corners=True)
        return self.block(torch.cat([x, c1], dim=1))


def get_deeplabv3_plus():
    from ..data.dataloader import datasets
    model = DeepLabV3Plus(datasets[cfg.DATASET.NAME].NUM_CLASS)
    return model


def get_deeplabv3_plus_xception_voc(**kwargs):
    return get_deeplabv3_plus('pascal_voc', 'xception', **kwargs)


if __name__ == '__main__':
    model = get_deeplabv3_plus_xception_voc()
