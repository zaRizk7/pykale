import math
import os

import torch
from PIL import Image
from torch.utils.data import Dataset
import pickle
import numpy as np


class ADL(Dataset):
    def __init__(self, data_path, list_path, mode, dataset_split, window_len=16, transforms=None):
        self.data_path = data_path
        self.list_path = list_path
        self.mode = mode
        self.window_len = window_len
        self.transforms = transforms
        self.dataset = dataset_split
        self.data = self.make_dataset()

    def __len__(self):
        return len(self.data)

    def __getitem__(self, item):
        self.vid, self.start, self.end, self.label = self.data[item]
        if self.mode == 'rgb':
            imgs = self.load_rgb_frames()
        elif self.mode == 'flow':
            imgs = self.load_flow_frames()

        if self.transforms is not None:
            imgs = self.transforms(imgs)
        return self.video_to_tensor(imgs), self.label

    def make_dataset(self):
        data = []
        i = 0
        with open(self.list_path, 'rb') as input_file:
            input_file = pickle.load(input_file)
            for line in input_file.values:
                data.append((line[0], eval(line[1]), eval(line[2]), eval(line[5])))
                i = i + 1
        print("Number of {:5} action segments: {}".format(self.dataset, i))
        return data

    def load_rgb_frames(self):
        frames = []
        for i in range(self.start, self.start + self.window_len):
            dir = os.path.join(self.data_path, self.mode, self.vid, 'frame_{:0>10}.jpg'.format(i))
            img = Image.open(dir).convert('RGB')
            w, h = img.size
            if w < 255 or h < 255:
                d = 255. - min(w, h)
                sc = 1 + d / min(w, h)
                img = img.resize(int(w * sc), int(h * sc))
            img = np.asarray(img)
            img = self.linear_norm(img)
            frames.append(img)
        return np.asarray(frames, dtype=np.float32)

    def load_flow_frames(self):
        frames = []
        start_f = math.ceil(self.start / 2) - 1
        if start_f == 0:
            start_f = 1
        if self.window_len > 1:
            window_len = self.window_len / 2
        for i in range(int(start_f), int(start_f + window_len)):
            diru = os.path.join(self.data_path, self.mode, self.vid, 'u', 'frame_{:0>10}.jpg'.format(i))
            dirv = os.path.join(self.data_path, self.mode, self.vid, 'v', 'frame_{:0>10}.jpg'.format(i))
            imgu = Image.open(diru).convert("L")
            imgv = Image.open(dirv).convert("L")
            w, h = imgu.size
            if w < 255 or h < 255:
                d = 255. - min(w, h)
                sc = 1 + d / min(w, h)
                imgu = imgu.resize(int(w * sc), int(h * sc))
                imgv = imgv.resize(int(w * sc), int(h * sc))
            img = np.asarray([np.array(imgu), np.array(imgv)]).transpose([1, 2, 0])
            img = self.linear_norm(img)
            frames.append(img)
        return np.asarray(frames, dtype=np.float32)

    @staticmethod
    def video_to_tensor(pic):
        """Convert a ``numpy.ndarray`` to tensor.
        Converts a numpy.ndarray (T x H x W x C)
        to a torch.FloatTensor of shape (C x T x H x W)

        Args:
            pic (numpy.ndarray): Video to be converted to tensor.
        Returns:
            Tensor: Converted video.
        """
        return torch.from_numpy(pic.transpose([3, 0, 1, 2]))

    @staticmethod
    def linear_norm(arr):
        # arr = np.asarray(img)
        arr = arr.astype('float')
        for i in range(arr.shape[-1]):
            arr[..., i] = (arr[..., i] / 255.) * 2 - 1
        # img = Image.fromarray(arr.astype('uint8'), 'RGB')
        return arr
