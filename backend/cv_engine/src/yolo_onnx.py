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
        
        # letterbox resizing (maintain aspect ratio)
        scale = min(640 / w, 640 / h)
        new_w, new_h = int(w * scale), int(h * scale)
        img_resized = cv2.resize(frame, (new_w, new_h))
        
        # pad the remaining space to make image 640x640
        pad_w = (640 - new_w) / 2
        pad_h = (640 - new_h) / 2
        top, bottom = int(pad_h), int(pad_h + 0.5)
        left, right = int(pad_w), int(pad_w + 0.5)
        img_pad = cv2.copyMakeBorder(
            img_resized, top, bottom, left, right, 
            cv2.BORDER_CONSTANT, value=(114, 114, 114)
        )
        
        # prepare tensor
        img_rgb = cv2.cvtColor(img_pad, cv2.COLOR_BGR2RGB)
        input_tensor = img_rgb.transpose(2, 0, 1).astype(np.float32) / 255.0
        input_tensor = np.expand_dims(input_tensor, axis=0)

        # run inference
        outputs = self.session.run(None, {self.input_name: input_tensor})[0]
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

        for box, class_id, conf in zip(boxes, class_ids, confidences):
            cx, cy, bw, bh = box
            
            # reverse the letterbox padding and scaling for accurate coordinates
            cx = (cx - pad_w) / scale
            cy = (cy - pad_h) / scale
            bw = bw / scale
            bh = bh / scale
            
            x1 = int(cx - bw / 2)
            y1 = int(cy - bh / 2)
            x2 = int(cx + bw / 2)
            y2 = int(cy + bh / 2)

            # clamp values to actual image dimensions
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            results.append({
                "class_name": self.class_names[class_id] if class_id < len(self.class_names) else str(class_id),
                "box": (x1, y1, x2, y2),
                "confidence": float(conf)
            })

        return results