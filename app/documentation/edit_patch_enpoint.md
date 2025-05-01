# Defect Record Update API Documentation

## Overview

This document provides detailed information about the endpoint for updating defect records in the punch list system. The web application already uses this endpoint successfully, and this guide will help mobile developers implement the same functionality.

## Endpoint Details

**URL:** `/defect-records/defect-record/{defect_record_id}`  
**Method:** `PATCH`  
**Content-Type:** `multipart/form-data` (required for file uploads)  
**Authentication:** Required (ensure your authentication token is included in headers)

## Request Parameters

The endpoint accepts the following form parameters:

### Path Parameter:
- `defect_record_id` (integer, required): The ID of the defect record to update

### Form Fields (all optional):
- `product_id` (integer): ID of the product
- `job_id` (integer): ID of the job
- `inspector_user_id` (integer): ID of the user who inspected the defect
- `issue_by_user_id` (integer): ID of the user who created the issue
- `issue_id` (integer): ID of the associated issue
- `correction_process_id` (integer): ID of the correction process to apply
- `status_id` (integer): ID of the status to set
- `description` (string): Additional description for the defect
- `close_record` (boolean): Set to `true` to close the record (automatically set to `true` if status is "Ok")

### File Fields (all optional):
- `defect_images[]` (file array): Images of the defect (image_type_id=3)
- `location_images[]` (file array): Images of the defect location (image_type_id=2)
- `solved_images[]` (file array): Images of the implemented solution (image_type_id=1)

## Important Business Rules

1. **Status and Solution Images**:
   - When setting the status to "Ok" (typically status_id=1), at least one solution image (`solved_images[]`) must be provided either in the current request or must already exist
   - The endpoint will automatically close the record (`date_closed`) when status is set to "Ok"

2. **Image Types**:
   - Each image type has a specific ID in the system:
     - solved_images: image_type_id=1 (for solution implementation)
     - location_images: image_type_id=2 (for defect location)
     - defect_images: image_type_id=3 (for the defect itself)

3. **Partial Updates**:
   - The endpoint supports partial updates - only include fields you want to change
   - Empty or omitted fields will not modify existing data

## Response Format

```json
{
  "defect_record_id": 123,
  "product_name": "Product Name",
  "job_code": "JOB123",
  "defect_images": ["/static/punch_list/product/job/defect_123/defect_image/defect_1234567890.jpg"],
  "location_images": ["/static/punch_list/product/job/defect_123/location_image/location_1234567890.jpg"],
  "solved_images": ["/static/punch_list/product/job/defect_123/solved_image/solved_1234567890.jpg"]
}
```

**Note**: The response only includes newly uploaded images, not all existing images.

## Error Handling

The API returns standard HTTP status codes:
- 200: Success
- 404: Entity not found (defect record, product, job, issue, correction process, or status)
- 422: Validation error
- 500: Server error

Error responses follow this format:
```json
{
  "detail": "Error message description"
}
```

## Request Examples

### Minimal Update Example (JSON-like for illustration)

When updating just the status:

```
PATCH /defect-records/defect-record/123
Content-Type: multipart/form-data

Form Data:
  status_id: 2
```

### Complete Update Example with Images (JSON-like for illustration)

```
PATCH /defect-records/defect-record/123
Content-Type: multipart/form-data

Form Data:
  status_id: 1
  correction_process_id: 5
  description: "Additional notes about the fix"
  close_record: true
  solved_images[]: [binary image data]
  location_images[]: [binary image data]
```

### Response Model Structure

```json
{
  "defect_record_id": 123,
  "product_name": "Product Name",
  "job_code": "JOB123",
  "defect_images": ["/static/punch_list/product/job/defect_123/defect_image/defect_1234567890.jpg"],
  "location_images": ["/static/punch_list/product/job/defect_123/location_image/location_1234567890.jpg"],
  "solved_images": ["/static/punch_list/product/job/defect_123/solved_image/solved_1234567890.jpg"]
}
```

## Common Validation Errors and Solutions

1. **Missing required solution image when setting status to "Ok"**
   - Error: "To mark a defect as OK, you must add at least one solution image"
   - Solution: Include at least one image in the `solved_images[]` field or ensure a solution image already exists

2. **Entity not found**
   - Error: "Producto no encontrado", "Job no encontrado", etc.
   - Solution: Ensure all entity IDs (product_id, job_id, etc.) are valid before submitting

3. **Empty file uploads**
   - Problem: Empty files are ignored by the backend
   - Solution: Validate that image files are valid and not empty before sending

## Testing Recommendations

1. Test updating a defect with different status values
2. Test updating a defect to "Ok" status with and without solution images
3. Test uploading different combinations of image types
4. Verify that partial updates don't affect unspecified fields
5. Test error handling for invalid entity IDs

## Additional Notes

- Image URLs in the response are relative paths that should be combined with your API base URL
- The backend automatically organizes images into folders based on product, job, and defect record
- The backend manages image filenames to ensure uniqueness using timestamps
- Consider implementing a retry mechanism for image uploads on poor network connections