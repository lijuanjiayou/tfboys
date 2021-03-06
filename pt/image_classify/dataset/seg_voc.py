#!/usr/bin/env python
"""
Retrain FCN models from caffe model
and can be inferenced insize pytorch



"""

import collections
import os.path as osp

import numpy as np
import PIL.Image
import scipy.io
import torch
from torch.utils import data
import os
import cv2


class VOCClassSegBase(data.Dataset):

    class_names = np.array([
        'background',
        'aeroplane',
        'bicycle',
        'bird',
        'boat',
        'bottle',
        'bus',
        'car',
        'cat',
        'chair',
        'cow',
        'diningtable',
        'dog',
        'horse',
        'motorbike',
        'person',
        'potted plant',
        'sheep',
        'sofa',
        'train',
        'tv/monitor',
    ])
    mean_bgr = np.array([104.00698793, 116.66876762, 122.67891434])

    def __init__(self, root, split='train', transform=False):
        self.root = root
        self.split = split
        self._transform = transform
        self.num_classes = len(self.class_names)

        # VOC2011 and others are subset of VOC2012
        dataset_dir = osp.join(self.root, 'VOC2012')
        self.files = collections.defaultdict(list)
        for split in ['train', 'val']:
            imgsets_file = osp.join(
                dataset_dir, 'ImageSets/Segmentation/%s.txt' % split)
            for did in open(imgsets_file):
                did = did.strip()
                img_file = osp.join(dataset_dir, 'JPEGImages/%s.jpg' % did)
                lbl_file = osp.join(
                    dataset_dir, 'SegmentationClass/%s.png' % did)
                self.files[split].append({
                    'img': img_file,
                    'lbl': lbl_file,
                })
        print('Found all {} images.'.format(len(self.files[self.split])))

    def __len__(self):
        return len(self.files[self.split])

    def __getitem__(self, index):
        try:
            data_file = self.files[self.split][index]
            img_file = data_file['img']

            img = cv2.cvtColor(cv2.imread(img_file), cv2.COLOR_BGR2RGB)
            img = np.array(img, dtype=np.uint8)

            lbl_file = data_file['lbl']
            lbl = PIL.Image.open(lbl_file)
            lbl = np.array(lbl, dtype=np.int32)
            lbl[lbl == 255] = -1
            # print(lbl)
            # print('max: {}, min: {}'.format(np.max(lbl), np.min(lbl)))

            # NOTE: in label, -1 is border, 0 is background,
            # why not change border to 0 too?????
            if self._transform:
                return self.transform(img, lbl)
            else:
                return img, lbl
        except Exception as e:
            print('Reading item corrupt: {}'.format(e))
            print('Corrupt file path: ', img_file)
            # in train, check None, if, then pass
            data_file = self.files[self.split][index + 1]
            img_file = data_file['img']

            # PIL corrupt sometimes
            img = PIL.Image.open(img_file)
            img = np.array(img, dtype=np.uint8)

            lbl_file = data_file['lbl']
            lbl = PIL.Image.open(lbl_file)
            lbl = np.array(lbl, dtype=np.int32)
            lbl[lbl == 255] = -1
            if self._transform:
                return self.transform(img, lbl)
            else:
                return img, lbl

    def preprocess(self, img):
        """
        img reading from PIL.Image
        :param img:
        :return:
        """
        img = np.array(img, dtype=np.uint8)
        img = img[:, :, ::-1]  # RGB -> BGR
        img = img.astype(np.float64)
        img -= self.mean_bgr
        img = img.transpose(2, 0, 1)
        return img

    def transform(self, img, lbl):
        img = img[:, :, ::-1]  # RGB -> BGR
        img = img.astype(np.float64)
        img -= self.mean_bgr
        img = img.transpose(2, 0, 1)
        img = torch.from_numpy(img).float()
        lbl = torch.from_numpy(lbl).long()
        return img, lbl

    def untransform(self, img, lbl):
        img = img.numpy()
        img = img.transpose(1, 2, 0)
        img += self.mean_bgr
        img = img.astype(np.uint8)
        img = img[:, :, ::-1]
        lbl = lbl.numpy()
        return img, lbl


class VOC2011ClassSeg(VOCClassSegBase):

    def __init__(self, root, split='train', transform=False):
        super(VOC2011ClassSeg, self).__init__(
            root, split=split, transform=transform)
        pkg_root = osp.join(osp.dirname(osp.realpath(__file__)), '..')
        imgsets_file = osp.join(os.path.dirname(os.path.abspath(__file__)), 'voc_11_val.txt')
        dataset_dir = osp.join(self.root, 'VOC2012')
        for did in open(imgsets_file):
            did = did.strip()
            img_file = osp.join(dataset_dir, 'JPEGImages/%s.jpg' % did)
            lbl_file = osp.join(dataset_dir, 'SegmentationClass/%s.png' % did)
            self.files['seg11valid'].append({'img': img_file, 'lbl': lbl_file})


class VOC2012ClassSeg(VOCClassSegBase):
    url = 'http://host.robots.ox.ac.uk/pascal/VOC/voc2012/VOCtrainval_11-May-2012.tar'  # NOQA

    def __init__(self, root, split='train', transform=False):
        super(VOC2012ClassSeg, self).__init__(
            root, split=split, transform=transform)


# ------------------- Mostly this is not needed ------------------------------
class SBDClassSeg(VOCClassSegBase):

    # XXX: It must be renamed to benchmark.tar to be extracted.
    url = 'http://www.eecs.berkeley.edu/Research/Projects/CS/vision/grouping/semantic_contours/benchmark.tgz'  # NOQA

    def __init__(self, root, split='train', transform=False):
        self.root = root
        self.split = split
        self._transform = transform

        dataset_dir = osp.join(self.root, 'VOC/benchmark_RELEASE/dataset')
        self.files = collections.defaultdict(list)
        for split in ['train', 'val']:
            imgsets_file = osp.join(dataset_dir, '%s.txt' % split)
            for did in open(imgsets_file):
                did = did.strip()
                img_file = osp.join(dataset_dir, 'img/%s.jpg' % did)
                lbl_file = osp.join(dataset_dir, 'cls/%s.mat' % did)
                self.files[split].append({
                    'img': img_file,
                    'lbl': lbl_file,
                })

    def __getitem__(self, index):
        data_file = self.files[self.split][index]
        # load image
        img_file = data_file['img']
        img = PIL.Image.open(img_file)
        img = np.array(img, dtype=np.uint8)
        # load label
        lbl_file = data_file['lbl']
        mat = scipy.io.loadmat(lbl_file)
        lbl = mat['GTcls'][0]['Segmentation'][0].astype(np.int32)
        lbl[lbl == 255] = -1
        if self._transform:
            return self.transform(img, lbl)
        else:
            return img, lbl
