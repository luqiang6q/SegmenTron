"""Filesystem utility functions."""
from __future__ import absolute_import
import os
import errno
import torch
import logging

from ..config import cfg

def save_checkpoint(model, epoch, optimizer=None, lr_scheduler=None, is_best=False):
    """Save Checkpoint"""
    directory = os.path.expanduser(cfg.TRAIN.MODEL_SAVE_DIR)
    directory = os.path.join(directory, '{}_{}_{}_{}'.format(cfg.MODEL.MODEL_NAME, cfg.MODEL.BACKBONE,
                                                             cfg.DATASET.NAME, cfg.TIME_STAMP))
    if not os.path.exists(directory):
        os.makedirs(directory)
    filename = '{}.pth'.format(str(epoch))
    filename = os.path.join(directory, filename)
    model_state_dict = model.module.state_dict() if hasattr(model, 'module') else model.state_dict()
    if is_best:
        best_filename = 'best_model.pth'
        best_filename = os.path.join(directory, best_filename)
        torch.save(model_state_dict, best_filename)
    else:
        save_state = {
            'epoch': epoch,
            'state_dict': model_state_dict,
            'optimizer': optimizer.state_dict(),
            'lr_scheduler': lr_scheduler.state_dict()
        }
        if not os.path.exists(filename):
            torch.save(save_state, filename)
            logging.info('Epoch {} model saved in: {}'.format(epoch, filename))

        # remove last epoch
        pre_filename = '{}.pth'.format(str(epoch - 1))
        pre_filename = os.path.join(directory, pre_filename)
        try:
            if os.path.exists(pre_filename):
                os.remove(pre_filename)
        except OSError as e:
            logging.info(e)

def makedirs(path):
    """Create directory recursively if not exists.
    Similar to `makedir -p`, you can skip checking existence before this function.
    Parameters
    ----------
    path : str
        Path of the desired dir
    """
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise


def try_import(package, message=None):
    """Try import specified package, with custom message support.
    Parameters
    ----------
    package : str
        The name of the targeting package.
    message : str, default is None
        If not None, this function will raise customized error message when import error is found.
    Returns
    -------
    module if found, raise ImportError otherwise
    """
    try:
        return __import__(package)
    except ImportError as e:
        if not message:
            raise e
        raise ImportError(message)


def try_import_cv2():
    """Try import cv2 at runtime.
    Returns
    -------
    cv2 module if found. Raise ImportError otherwise
    """
    msg = "cv2 is required, you can install by package manager, e.g. 'apt-get', \
        or `pip install opencv-python --user` (note that this is unofficial PYPI package)."
    return try_import('cv2', msg)


def import_try_install(package, extern_url=None):
    """Try import the specified package.
    If the package not installed, try use pip to install and import if success.
    Parameters
    ----------
    package : str
        The name of the package trying to import.
    extern_url : str or None, optional
        The external url if package is not hosted on PyPI.
        For example, you can install a package using:
         "pip install git+http://github.com/user/repo/tarball/master/egginfo=xxx".
        In this case, you can pass the url to the extern_url.
    Returns
    -------
    <class 'Module'>
        The imported python module.
    """
    try:
        return __import__(package)
    except ImportError:
        try:
            from pip import main as pipmain
        except ImportError:
            from pip._internal import main as pipmain

        # trying to install package
        url = package if extern_url is None else extern_url
        pipmain(['install', '--user', url])  # will raise SystemExit Error if fails

        # trying to load again
        try:
            return __import__(package)
        except ImportError:
            import sys
            import site
            user_site = site.getusersitepackages()
            if user_site not in sys.path:
                sys.path.append(user_site)
            return __import__(package)
    return __import__(package)


"""Import helper for pycocotools"""


# NOTE: for developers
# please do not import any pycocotools in __init__ because we are trying to lazy
# import pycocotools to avoid install it for other users who may not use it.
# only import when you actually use it


def try_import_pycocotools():
    """Tricks to optionally install and import pycocotools"""
    # first we can try import pycocotools
    try:
        import pycocotools as _
    except ImportError:
        import os
        # we need to install pycootools, which is a bit tricky
        # pycocotools sdist requires Cython, numpy(already met)
        import_try_install('cython')
        # pypi pycocotools is not compatible with windows
        win_url = 'git+https://github.com/zhreshold/cocoapi.git#subdirectory=PythonAPI'
        try:
            if os.name == 'nt':
                import_try_install('pycocotools', win_url)
            else:
                import_try_install('pycocotools')
        except ImportError:
            faq = 'cocoapi FAQ'
            raise ImportError('Cannot import or install pycocotools, please refer to %s.' % faq)
