import os
import json

def convert_annotations(input_dir, output_path):
    """
    Converts individual JSON annotation files to a single result.json file.
    """
    annotations = []
    for filename in os.listdir(input_dir):
        if filename.endswith(".json") and filename != "result.json": # Exclude existing result.json if it exists
            filepath = os.path.join(input_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                image_name = filename[:-5] + ".jpg" # Construct image name from json filename
                annotation = {
                    "图片名称": image_name,
                    "background": data.get("background"),
                    "classes": data.get("classes"),
                    "colonies_number": data.get("colonies_number"),
                    "labels": data.get("labels", [])
                }
                annotations.append(annotation)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(annotations, f, indent=4, ensure_ascii=False) # Ensure UTF-8 and non-ASCII characters are handled

if __name__ == "__main__":
    input_dir = "pic-all"  # Input directory for individual JSON files
    output_path = os.path.join(input_dir, "result.json") # Output path for result.json
    convert_annotations(input_dir, output_path)
    print(f"Successfully converted annotations and saved to {output_path}")
