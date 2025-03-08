import os
import json
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

def create_ts_file(json_file, ts_file):
    """Create a .ts file from a JSON translation file."""
    with open(json_file, 'r', encoding='utf-8') as f:
        translations = json.load(f)

    ts = Element('TS')
    ts.set('version', '2.1')
    # Extract language from filename (e.g., en.json -> en)
    ts.set('language', Path(json_file).stem) 
    context = SubElement(ts, 'context')
    name = SubElement(context, 'name')
    name.text = 'Main'  # You can customize the context name

    def add_translations(data, prefix=''):
        for key, value in data.items():
            if isinstance(value, dict):
                add_translations(value, f"{prefix}{key}.")
            else:
                message = SubElement(context, 'message')
                source = SubElement(message, 'source')
                source.text = f"{prefix}{key}"
                translation = SubElement(message, 'translation')
                translation.text = value

    add_translations(translations)

    # Pretty-print the XML
    xml_string = minidom.parseString(tostring(ts)).toprettyxml(indent="    ")

    with open(ts_file, 'w', encoding='utf-8') as f:
        f.write(xml_string)

def compile_qm(ts_file, qm_file):
    """Compile a .ts file to .qm using lrelease."""
    command = f'pyside6-lrelease "{ts_file}" -qm "{qm_file}"'
    os.system(command)

def main():
    i18n_dir = Path(__file__).parent / 'resources' / 'i18n'
    for json_file in i18n_dir.glob('*.json'):
        ts_file = json_file.with_suffix('.ts')
        qm_file = json_file.with_suffix('.qm')
        print(f"Processing: {json_file}")
        create_ts_file(json_file, ts_file)
        compile_qm(ts_file, qm_file)
        print(f"Generated: {qm_file}")

if __name__ == "__main__":
    main()
