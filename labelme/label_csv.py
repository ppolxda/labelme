import csv
import os
import os.path as osp
from dataclasses import dataclass

import natsort
import numpy as np
from PIL import Image

from labelme.label_file import LabelFile
from labelme.label_file import open

from . import utils

assert LabelFile


def format_shape(s):
    data = s.other_data.copy()
    data.update(
        dict(
            label=s.label,
            points=[(p.x(), p.y()) for p in s.points],
            group_id=s.group_id,
            description=s.description,
            shape_type=s.shape_type,
            flags=s.flags,
            mask=None
            if s.mask is None
            else utils.img_arr_to_b64(s.mask.astype(np.uint8)),
        )
    )
    return data


@dataclass
class DataRow:
    centerX: float
    centerY: float
    visibility: int
    frame: int
    width: float = 20.0
    height: float = 20.0

    @property
    def point(self):
        return {
            "W": int(self.width),
            "H": int(self.height),
            "X": int(self.centerX),
            "Y": int(self.centerY),
            "Visibility": int(self.visibility),
            "Frame": int(self.frame),
        }

    @property
    def shapes(self):
        if self.visibility == 0 or self.width == 0 or self.height == 0:
            return []

        half_width = self.width / 2
        half_height = self.height / 2
        return [
            {
                "label": "ball",
                "points": [
                    [self.centerX - half_width, self.centerY - half_height],
                    [self.centerX + half_width, self.centerY + half_height],
                ],
                "group_id": None,
                "shape_type": "rectangle",
                "flags": {},
            },
        ]

    @classmethod
    def from_shape(cls, shape_type: str, frame: int, bbox: list = None):
        if bbox is None:
            bbox = []

        if shape_type == "empty":
            return cls(
                frame=frame,
                centerX=0,
                centerY=0,
                visibility=0,
                width=0,
                height=0,
            )
        elif shape_type == "point":
            return cls(
                frame=frame,
                centerX=bbox[0],
                centerY=bbox[1],
                visibility=1,
                width=0,
                height=0,
            )
        elif shape_type == "rectangle":
            bbox = [bbox[0][0], bbox[0][1], bbox[1][0], bbox[1][1]]
            return cls(
                frame=frame,
                centerX=(bbox[0] + bbox[2]) / 2,
                centerY=(bbox[1] + bbox[3]) / 2,
                visibility=1,
                width=bbox[2] - bbox[0],
                height=bbox[3] - bbox[1],
            )
        else:
            raise ValueError(f"Unsupported shape type: {shape_type}")


class LabelCsv(object):
    suffix = ".csv"

    def __init__(self, filename):
        self.points = []
        self.filename = filename
        assert filename.endswith("_ball.csv"), (
            f"Filename {filename} must end with '_ball.csv'"
        )
        self.basename = osp.basename(filename)[: -len("_ball.csv")]
        self.rootDirname = osp.join(osp.dirname(filename), "..")
        self.labelmeDirname = osp.join(self.rootDirname, "labelme", self.basename)
        self.frameDirname = osp.join(self.rootDirname, "frame", self.basename)
        self.height = 0
        self.width = 0
        self.load(filename)

    def load(self, filename):
        """
        Load the CSV file containing trajectory data and populate the LabelCsv object.

        CSV Format:
        Frame,Visibility,X,Y

        Args:
            filename (str): Path to the CSV file
        """
        self.points = []
        self.filename = filename

        with open(filename, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Extract coordinates and visibility
                point = DataRow(
                    frame=int(row["Frame"]),
                    centerX=float(row["X"]),
                    centerY=float(row["Y"]),
                    visibility=int(row["Visibility"]),
                    width=float(row["W"]) if "W" in row else 20.0,
                    height=float(row["H"]) if "H" in row else 20.0,
                )

                # 如果为空点，则将其设置为 DataRow 的默认值
                if point.centerX == 0 or point.centerY == 0 or point.visibility == 0:
                    point = DataRow.from_shape("empty", point.frame)

                self.points.append(point)
                self.images = os.listdir(self.frameDirname)
                self.images = natsort.os_sorted(self.images)
                # self.generateLabelfile(point)

            # # Create a shape for the trajectory
            # if points:
            #     shape = {
            #         "label": "trajectory",
            #         "points": points,
            #         "shape_type": "linestrip",
            #         "frame": frame,
            #         "flags": {},
            #     }
            #     self.shapes.append(shape)

    def generateLabelfile(self, point: DataRow):
        """
        Generate a LabelFile object from the imagePath.
        This is a placeholder for actual implementation.
        """
        imageSeq = point.frame

        if not osp.exists(self.labelmeDirname):
            os.makedirs(self.labelmeDirname)

        imagePath = osp.join(self.frameDirname, self.images[imageSeq])

        # 默认视频帧，所以图片大小一致，只加载一次
        if self.height == 0 or self.width == 0:
            with Image.open(imagePath) as image:
                self.width, self.height = image.size

        filename = osp.join(self.labelmeDirname, f"{imageSeq}.json")
        lf = LabelFile()
        lf.save(
            filename=filename,
            shapes=point.shapes,
            imagePath=osp.join(
                "..", "..", "frame", self.basename, self.images[imageSeq]
            ),
            imageData=None,
            imageHeight=self.height,
            imageWidth=self.width,
            otherData=None,
            flags={},
        )

    def generateLabelfileByImagePath(self, imagePath):
        """
        Generate a LabelFile object from the imagePath.
        This is a placeholder for actual implementation.
        """
        imageSeq = self.imagePath2ImageSeq(imagePath)
        self.generateLabelfile(self.points[imageSeq])

    def changePoint(self, point: DataRow):
        """
        Save the points to the CSV file.
        """
        assert point.frame < len(self.points), (
            f"Point frame {point.frame} exceeds current points length {len(self.points)}"
        )
        self.points[point.frame] = point

    def save(self, save_point_only=False):
        """
        Save the points to the CSV file.
        """
        with open(self.filename, "w") as csvfile:
            fieldnames = ["Frame", "Visibility", "X", "Y", "W", "H"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for point in self.points:
                point_ = point.point
                if save_point_only:
                    point_["W"] = 0
                    point_["H"] = 0

                writer.writerow(point_)

    @classmethod
    def imagePath2ImageSeq(cls, imagePath):
        basename = osp.basename(imagePath)
        assert len(basename.split(".")) == 2, (
            "Image path must have a basename with extension"
        )
        return int(osp.splitext(basename)[0])
