# doscarchase/thirdeye/sentry_engine.py
# ----------------------------------------------------------------------------
#  ThirdEye AI Vision Suite - Proprietary and Confidential
#  Copyright (c) 2026 Devon Chase. All rights reserved.
# ----------------------------------------------------------------------------
import cv2
import numpy as np
import onnxruntime as ort
import os

class SentryEngine:
    def __init__(self, model_path="assets/sentry_model.onnx"):
        """
        Initializes the YOLOX-Nano Neural Engine (Apache 2.0).
        [UPDATE] STRICTLY configured for Human Detection only.
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Sentry Model not found at {model_path}. Run 'setup_sentry.py' first.")

        # Load Neural Network
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        self.session = ort.InferenceSession(model_path, providers=providers)
        
        self.input_shape = (416, 416) 
        
        self.class_mapping = {
            0: "Person"
        }

        # --- TUNABLE PARAMETERS (Default Values) ---
        self.conf_thresh = 0.60  # "Sweet spot"
        self.nms_thresh = 0.45   # Overlap threshold
        self.score_thresh = 0.3  # Low level cutoff

        # Pre-compute grids for decoding raw YOLOX outputs
        self.grids = []
        self.strides = []
        for stride in [8, 16, 32]:
            h, w = self.input_shape[0] // stride, self.input_shape[1] // stride
            xv, yv = np.meshgrid(np.arange(w), np.arange(h))
            grid = np.stack((xv, yv), 2).reshape(1, -1, 2)
            self.grids.append(grid)
            self.strides.append(np.full((1, grid.shape[1], 1), stride))
            
        self.grid_coords = np.concatenate(self.grids, axis=1)[0]
        self.grid_strides = np.concatenate(self.strides, axis=1)[0]

    def process_frame(self, frame):
        """
        Returns: list of tuples: ([x, y, w, h], score, label_name)
        """
        input_tensor, ratio = self._preprocess(frame)
        
        # Run AI Inference
        outputs = self.session.run(None, {self.session.get_inputs()[0].name: input_tensor})[0]
        
        # Use instance variables instead of hardcoded values
        boxes, scores, class_ids = self._postprocess(outputs, ratio, conf_thresh=self.conf_thresh)
        
        # Use instance variable for NMS
        final_boxes, final_scores, final_class_ids = self._nms(boxes, scores, class_ids, iou_thresh=self.nms_thresh)
        
        final_labels = [self.class_mapping.get(cid, "Unknown") for cid in final_class_ids]
        
        return list(zip(final_boxes, final_scores, final_labels))
    
    def get_tunable_config(self):
        """
        Returns the schema for the UI Model Tuner.
        Format: { internal_var: { label, desc, type, min, max, advanced } }
        """
        return {
            "conf_thresh": {
                "label": "Detection Sensitivity",
                "desc": "How sure the AI needs to be to flag a person. Higher values reduce false alarms but might miss people in the dark.",
                "type": "float",
                "min": 0.1, "max": 0.95, "step": 0.05,
                "advanced": False
            },
            "nms_thresh": {
                "label": "Crowd Separation",
                "desc": "Controls how the AI handles overlapping people. Lower values are better for dense crowds but might count one person twice.",
                "type": "float",
                "min": 0.1, "max": 1.0, "step": 0.05,
                "advanced": True
            },
            "score_thresh": {
                "label": "Pre-Filter Noise Gate",
                "desc": "The absolute minimum signal strength required to even consider an object. Keep low for maximum recall.",
                "type": "float",
                "min": 0.1, "max": 0.6, "step": 0.05,
                "advanced": True
            }
        }

    def update_parameter(self, key, value):
        """Updates a parameter dynamically."""
        if hasattr(self, key):
            setattr(self, key, value)
            print(f"[SentryEngine] Updated {key} to {value}")

    def _preprocess(self, img):
        h, w = img.shape[:2]
        scale = min(self.input_shape[0] / h, self.input_shape[1] / w)
        nw, nh = int(w * scale), int(h * scale)
        resized_img = cv2.resize(img, (nw, nh))
        
        padded_img = np.full((self.input_shape[0], self.input_shape[1], 3), 114, dtype=np.uint8)
        padded_img[:nh, :nw] = resized_img
        
        blob = padded_img.astype(np.float32)
        blob = blob.transpose(2, 0, 1)
        blob = np.expand_dims(blob, axis=0)
        
        return blob, scale

    def _postprocess(self, outputs, scale, conf_thresh):
        predictions = outputs[0]
        boxes = []
        scores = []
        class_ids = []
        
        if predictions.shape[0] == self.grid_coords.shape[0]:
            predictions[:, :2] = (predictions[:, :2] + self.grid_coords) * self.grid_strides
            predictions[:, 2:4] = np.exp(predictions[:, 2:4]) * self.grid_strides

        obj_conf = predictions[:, 4]
        
        # [FIX] We ONLY look at column 5 (Person Class Score)
        # This ignores every other object in the COCO dataset (chairs, dogs, cats, etc.)
        person_scores = predictions[:, 5]
        
        total_conf = obj_conf * person_scores
        
        # Simple Mask: Is it a person? Is confidence high enough?
        mask = total_conf > conf_thresh
        
        valid_preds = predictions[mask]
        valid_scores = total_conf[mask]
        
        if len(valid_preds) == 0:
            return [], [], []

        for i, pred in enumerate(valid_preds):
            x_c, y_c, w, h = pred[:4]
            x_c /= scale
            y_c /= scale
            w /= scale
            h /= scale
            
            x = int(x_c - w/2)
            y = int(y_c - h/2)
            w = int(w)
            h = int(h)
            
            boxes.append([x, y, w, h])
            scores.append(float(valid_scores[i]))
            class_ids.append(0) # Always Class 0 (Person)
            
        return boxes, scores, class_ids

    def _nms(self, boxes, scores, class_ids, iou_thresh):
        if not boxes: return [], [], []
        # Use instance variable score_thresh
        indices = cv2.dnn.NMSBoxes(boxes, scores, score_threshold=self.score_thresh, nms_threshold=iou_thresh)
        if len(indices) > 0:
            final_boxes = [boxes[i] for i in indices.flatten()]
            final_scores = [scores[i] for i in indices.flatten()]
            final_class_ids = [class_ids[i] for i in indices.flatten()]
            return final_boxes, final_scores, final_class_ids
        return [], [], []
