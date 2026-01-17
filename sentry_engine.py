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
        This replaces the obsolete HOG method with modern Deep Learning.
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Sentry Model not found at {model_path}. Run 'setup_sentry.py' first.")

        # Load Neural Network onto CPU (or GPU if available)
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        self.session = ort.InferenceSession(model_path, providers=providers)
        
        # YOLOX-Nano Input Resolution
        self.input_shape = (416, 416) 
        self.classes = ["person"] # We only care about Index 0 (Person) from COCO dataset

        # [FIX] Pre-compute grids for decoding raw YOLOX outputs
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
        Inference Pipeline: Preprocess -> AI Model -> Postprocess -> NMS
        Returns: list of tuples: ([x, y, w, h], score)
        """
        input_tensor, ratio = self._preprocess(frame)
        
        # Run AI Inference
        outputs = self.session.run(None, {self.session.get_inputs()[0].name: input_tensor})[0]
        
        # Decode and Filter 
        # [TUNED] Increased conf_thresh to 0.65 to stop detecting random objects/motion
        boxes, scores = self._postprocess(outputs, ratio, conf_thresh=0.65)
        
        # Clean up overlaps (Non-Maximum Suppression)
        # [TUNED] Lowered iou_thresh to 0.30 to ensure we only get a single square per person
        final_boxes, final_scores = self._nms(boxes, scores, iou_thresh=0.30)
        
        # Zip results together so main.py can display scores
        return list(zip(final_boxes, final_scores))

    def _preprocess(self, img):
        # Resize to 416x416 without stretching (padding)
        h, w = img.shape[:2]
        scale = min(self.input_shape[0] / h, self.input_shape[1] / w)
        
        # Compute new size
        nw, nh = int(w * scale), int(h * scale)
        resized_img = cv2.resize(img, (nw, nh))
        
        # Create padded image
        padded_img = np.full((self.input_shape[0], self.input_shape[1], 3), 114, dtype=np.uint8)
        padded_img[:nh, :nw] = resized_img
        
        # Convert to float & HWC -> CHW format
        blob = padded_img.astype(np.float32)
        blob = blob.transpose(2, 0, 1) # Change to Channel-First
        blob = np.expand_dims(blob, axis=0) # Add batch dimension
        
        return blob, scale

    def _postprocess(self, outputs, scale, conf_thresh):
        predictions = outputs[0]
        boxes = []
        scores = []
        
        # [FIX] Decode YOLOX raw outputs: (offset + grid) * stride
        if predictions.shape[0] == self.grid_coords.shape[0]:
            predictions[:, :2] = (predictions[:, :2] + self.grid_coords) * self.grid_strides
            predictions[:, 2:4] = np.exp(predictions[:, 2:4]) * self.grid_strides

        # YOLOX Output: [x_center, y_center, width, height, obj_conf, class_conf...]
        # We only look at class_index 0 (Person) which is index 5 in the array
        
        # Vectorized filtering for speed
        obj_conf = predictions[:, 4]
        class_conf = predictions[:, 5] # Index 5 is 'Person' in COCO
        total_conf = obj_conf * class_conf
        
        # Filter by confidence
        mask = total_conf > conf_thresh
        valid_preds = predictions[mask]
        valid_scores = total_conf[mask]
        
        if len(valid_preds) == 0:
            return [], []

        # Convert output boxes to standard [x, y, w, h] and rescale to original image
        for i, pred in enumerate(valid_preds):
            x_c, y_c, w, h = pred[:4]
            
            # Undo letterbox scaling (Coordinates are now in absolute 416x416 pixels)
            x_c /= scale
            y_c /= scale
            w /= scale
            h /= scale
            
            # Convert Center-format to Top-Left format
            x = int(x_c - w/2)
            y = int(y_c - h/2)
            w = int(w)
            h = int(h)
            
            boxes.append([x, y, w, h])
            scores.append(float(valid_scores[i]))
            
        return boxes, scores
    def _nms(self, boxes, scores, iou_thresh):
        if not boxes: return [], []
        
        # Use OpenCV's built-in fast NMS
        indices = cv2.dnn.NMSBoxes(boxes, scores, score_threshold=0.3, nms_threshold=iou_thresh)
        
        if len(indices) > 0:
            final_boxes = [boxes[i] for i in indices.flatten()]
            final_scores = [scores[i] for i in indices.flatten()]
            return final_boxes, final_scores
        return [], []
