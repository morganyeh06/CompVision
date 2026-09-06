import onnxruntime as ort
import cv2
import numpy as np


class YOLO_ONNX:
    def __init__(self, model_path: str, class_names: list):
        self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        self.class_names = class_names

    def predict(self, frame: np.ndarray, conf_threshold: float = 0.5):
        h, w = frame.shape[:2]
        
        # resize to 640x640, convert BGR to RGB, normalize 0-1, NCHW layout
        img_resized = cv2.resize(frame, (640, 640))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        input_tensor = img_rgb.transpose(2, 0, 1).astype(np.float32) / 255.0
        input_tensor = np.expand_dims(input_tensor, axis=0)

        # run inference
        outputs = self.session.run(None, {self.input_name: input_tensor})[0]
        
        # transpose outputs from [1, 4 + num_classes, 8400] to [8400, 4 + num_classes]
        predictions = np.squeeze(outputs, axis=0).T

        # extract coordinates and class confidence scores
        boxes = predictions[:, :4]
        scores = predictions[:, 4:]
        class_ids = np.argmax(scores, axis=1)
        confidences = np.max(scores, axis=1)

        # confidence mask filter
        mask = confidences > conf_threshold
        boxes, class_ids, confidences = boxes[mask], class_ids[mask], confidences[mask]

        results = []
        x_scale, y_scale = w / 640.0, h / 640.0

        for box, class_id, conf in zip(boxes, class_ids, confidences):
            cx, cy, bw, bh = box
            x1 = int((cx - bw / 2) * x_scale)
            y1 = int((cy - bh / 2) * y_scale)
            x2 = int((cx + bw / 2) * x_scale)
            y2 = int((cy + bh / 2) * y_scale)

            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            results.append({
                "class_name": self.class_names[class_id] if class_id < len(self.class_names) else str(class_id),
                "box": (x1, y1, x2, y2),
                "confidence": float(conf)
            })

        return results