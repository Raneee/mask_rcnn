"""
This module contains functions used to make MaP differentiable.
They are not used in the current version.
"""

def unmold_boxes_x(boxes, class_ids, masks, image_shape, window, scores=None):
    """Reformats the detections of one image from the format of the neural
    network output to a format suitable for use in the rest of the
    application.

    detections: [N, (y1, x1, y2, x2, class_id, score)]
    masks: [N, height, width]
    image_shape: [height, width, depth] Original size of the image
                 before resizing
    window: [y1, x1, y2, x2] Box in the image where the real image is
            excluding the padding.

    Returns:
    boxes: [N, (y1, x1, y2, x2)] Bounding boxes in pixels
    class_ids: [N] Integer class IDs for each bounding box
    scores: [N] Float probability scores of the class_id
    masks: [height, width, num_instances] Instance masks
    """
    # Extract boxes, class_ids, scores, and class-specific masks
    class_ids = class_ids.to(torch.long)

    image_shape2 = (image_shape[0], image_shape[1])
    boxes = to_img_domain(boxes, window, image_shape)

    boxes, _, masks, _ = remove_zero_area(boxes, class_ids, masks)
    full_masks = unmold_masks_x(masks, boxes, image_shape2)

    return boxes, full_masks


def unmold_detections_x(detections, mrcnn_mask, image_shape, window):
    """Reformats the detections of one image from the format of the neural
    network output to a format suitable for use in the rest of the
    application.

    detections: [N, (y1, x1, y2, x2, class_id, score)]
    mrcnn_mask: [N, height, width, num_classes]
    image_shape: [height, width, depth] Original size of the image
                 before resizing
    window: [y1, x1, y2, x2] Box in the image where the real image is
            excluding the padding.

    Returns:
    boxes: [N, (y1, x1, y2, x2)] Bounding boxes in pixels
    class_ids: [N] Integer class IDs for each bounding box
    scores: [N] Float probability scores of the class_id
    masks: [height, width, num_instances] Instance masks
    """
    N = detections.shape[0]

    # Extract boxes, class_ids, scores, and class-specific masks
    boxes = detections[:N, :4]
    class_ids = detections[:N, 4].to(torch.long)
    scores = detections[:N, 5]
    masks = mrcnn_mask[torch.arange(N, dtype=torch.long), :, :, class_ids]

    return unmold_boxes_x(boxes, class_ids, masks, image_shape, window)


def unmold_mask_x(mask, bbox, image_shape):
    """Converts a mask generated by the neural network into a format similar
    to its original shape.
    mask: [height, width] of type float. A small, typically 28x28 mask.
    bbox: [y1, x1, y2, x2]. The box to fit the mask in.

    Returns a binary mask with the same size as the original image.
    """
    # threshold = 0.5
    y1, x1, y2, x2 = bbox.floor()
    shape = (y2 - y1, x2 - x1)

    mask = F.interpolate(mask.unsqueeze(0).unsqueeze(0), size=shape,
                         mode='bilinear', align_corners=True)
    mask = mask.squeeze(0).squeeze(0)
    mask = ((mask - 0.5)*100).sigmoid()
    return mask


def unmold_masks_x(masks, boxes, image_shape):
    # Resize masks to original image size and set boundary threshold.
    N = masks.shape[0]
    full_masks = []
    for i in range(N):
        # Convert neural network mask to full size mask
        full_mask = unmold_mask_x(masks[i], boxes[i], image_shape)
        full_masks.append(full_mask)
    return full_masks
