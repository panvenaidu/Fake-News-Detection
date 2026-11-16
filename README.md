# UROP misinformation classification

This project evaluates research-defined six-category classification using text, images, and both modalities from the faculty-provided Fakeddit dataset. A model prediction alone does not establish whether a claim is true or false.


## Current organization

Original scripts are located in model/, preprocessing/, training/, testing/, validation/, and metrics/. Registered settings are in configs/. Original reports, receipts, predictions, and experiment evidence are in results/.

Model and experiment code use image_only, text_only, and text_plus_image subfolders. Shared preparation code is in preprocessing/shared/. Private data is in preprocessing/Data/. Large evidence bundles and Python packages retain their internal structure.

archives/miscellaneous/ holds presentations, workflow visuals, and Finder metadata. Earlier experiment code remains in its dedicated training and model folders.

The clearly named model review files contain full original source copies. Original filenames also remain available. Scripts retain historical imports and paths, which require repair and runtime verification before execution.
