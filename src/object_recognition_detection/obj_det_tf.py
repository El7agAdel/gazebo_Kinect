#!/usr/bin/env python

import rospy
from std_msgs.msg import Int32
import numpy as np
import cv2
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
from utils import label_map_util
from utils import visualization_utils as vis_util
from cv_bridge import CvBridge
from rospy.numpy_msg import numpy_msg
from sensor_msgs.msg import Image
rospy.init_node('det_tf.py', anonymous=True)


PATH_TO_CKPT = '/home/adel/vision/object_recognition_detection/mobilenetmodel/frozen_inference_graph.pb'

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = '/home/adel/vision/object_recognition_detection/data/mscoco_label_map.pbtxt'

NUM_CLASSES = 90

def bound (ymin,xmin,ymax,xmax,height,width,img):
    ymin = np.int64(np.round(ymin*height))
    xmin = np.int64(np.round(xmin*width))
    ymax =  np.int64(np.round(ymax*height))
    xmax = np.int64(np.round(xmax*width))
    
    centery = np.int64(np.round((ymin+ymax)/2))
    centerx = np.int64(np.round((xmin+xmax)/2))
    
    cv2.rectangle(img,(xmin,ymin),(xmax,ymax),(0,0,0),2)
    cv2.circle(img,(centerx,centery),1,(0,0,0),2)
    return img,centerx,centery


detection_graph = tf.Graph()
with detection_graph.as_default():
  od_graph_def = tf.GraphDef()
  with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
    serialized_graph = fid.read()
    od_graph_def.ParseFromString(serialized_graph)
    tf.import_graph_def(od_graph_def, name='')

# ## Loading label map
# Label maps map indices to category names, so that when our convolution network predicts `5`, we know that this corresponds to `airplane`.  Here we use internal utility functions, but anything that returns a dictionary mapping integers to appropriate string labels would be fine

label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)


def callback(data):
	image_np = CvBridge().imgmsg_to_cv2(data, "bgr8")
	height,width,channel=image_np.shape

	# Expand dimensions since the model expects images to have shape: [1, None, None, 3]
	image_np_expanded = np.expand_dims(image_np, axis=0)
	image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
	# Each box represents a part of the image where a particular object was detected.
	boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
	# Each score represent how level of confidence for each of the objects.
	# Score is shown on the result image, together with the class label.
	scores = detection_graph.get_tensor_by_name('detection_scores:0')
	classes = detection_graph.get_tensor_by_name('detection_classes:0')
	num_detections = detection_graph.get_tensor_by_name('num_detections:0')
	# Actual detection.
	(boxes, scores, classes, num_detections) = sess.run(
		[boxes, scores, classes, num_detections],
		feed_dict={image_tensor: image_np_expanded})
	# Visualization of the results of a detection.
	ymin,xmin,ymax,xmax = vis_util.visualize_boxes_and_labels_on_image_array(
						image_np,
						np.squeeze(boxes),
						np.squeeze(classes).astype(np.int32),
						np.squeeze(scores),
						category_index,
						use_normalized_coordinates=True,
						line_thickness=8)


	img,centerx,centery = bound(ymin,xmin,ymax,xmax,height,width,image_np) 
	cv2.imshow('image',img)
	if cv2.waitKey(25) == 27:
		cv2.destroyAllWindows()

# Running the tensorflow session
with detection_graph.as_default():
  with tf.Session(graph=detection_graph) as sess:
	rospy.Subscriber('/abb_irb120_3_58/camera1/image_raw',Image, callback)
	rospy.spin()





