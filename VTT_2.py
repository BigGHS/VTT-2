import os
import re
import sys

def normalize_speaker(s):
    s = s.strip()
    if s.startswith('[') and s.endswith(']'):
        return s
    return ' '.join(word.capitalize() for word in s.split())

def standardize_timestamp(ts):
    ts = ts.replace(',', '.')
    parts = ts.split(':')
    if len(parts) == 3:
        hours, minutes, rest = parts
    elif len(parts) == 2:
        hours = '00'
        minutes, rest = parts
    else:
        return '00:00:00'
    seconds = rest.split('.')[0]
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

def flush(result, speaker, text_list, start, end, ts_flag):
    if speaker and text_list:
        block = []
        if ts_flag and start and end:
            std_start = standardize_timestamp(start)
            std_end = standardize_timestamp(end)
            block.append(f"{std_start} --> {std_end}")
        block.append(f"{speaker}:\n{' '.join(text_list)}\n")
        result.append('\n'.join(block))

def process_file(input_file, output_file_path, include_timestamps):
    with open(input_file, 'r') as file:
        lines = file.readlines()

    result = []
    i = 0
    current_speaker = None
    current_text = []
    start_time = None
    end_time = None

    while i < len(lines):
        line = lines[i].strip()
        timestamp_match = re.match(r'^(\d{1,2}:\d{2}(?::\d{2})?[.,]\d{3}) --> (\d{1,2}:\d{2}(?::\d{2})?[.,]\d{3})$', line)
        if timestamp_match:
            seg_start = timestamp_match.group(1)
            seg_end = timestamp_match.group(2)
            speaker_line = lines[i + 1].strip() if i + 1 < len(lines) else ''
            text_lines = []
            speaker_match = re.match(r'^(\[.*?\]|[^:]{2,}):\s*(.*)$', speaker_line)
            if speaker_match:
                raw_speaker = speaker_match.group(1)
                speaker = normalize_speaker(raw_speaker)
                text = speaker_match.group(2)
                text_lines.append(text)
                i += 2
                while i < len(lines) and not re.match(r'^\d+$', lines[i].strip()) and not re.match(r'^\d{1,2}:\d{2}(?::\d{2})?[.,]\d{3} -->', lines[i].strip()):
                    text_lines.append(lines[i].strip())
                    i += 1
            else:
                speaker = None
                i += 1
            if speaker != current_speaker:
                flush(result, current_speaker, current_text, start_time, end_time, include_timestamps)
                current_speaker = speaker
                current_text = []
                start_time = seg_start
            current_text.extend(text_lines)
            end_time = seg_end
        else:
            i += 1
    flush(result, current_speaker, current_text, start_time, end_time, include_timestamps)

    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    with open(output_file_path, 'w') as f:
        f.write('\n'.join(result))
    print(f"Saved: {output_file_path}")

def main():
    os.chdir(os.getcwd())
    output_dir = os.path.join(os.getcwd(), "processed")

    input_file = input("Enter input filename (default: ALL .txt/.srt/.vtt files in this folder): ").strip()
    ts_choice = input("Include timestamps? (y/n/b, default 'y'): ").strip().lower()
    if ts_choice not in ['y', 'n', 'b']:
        ts_choice = 'y'

    generate_ts = ts_choice in ['y', 'b']
    generate_nots = ts_choice in ['n', 'b']

    if input_file == "":
        type_input = input("Which file types to process? (txt, srt, vtt, or all) [default: all]: ").strip().lower()
        if type_input == "":
            allowed_exts = {'.txt', '.srt', '.vtt'}
        elif type_input in {"txt", "srt", "vtt"}:
            allowed_exts = {f".{type_input}"}
        else:
            print("Invalid type selected. Defaulting to all.")
            allowed_exts = {'.txt', '.srt', '.vtt'}

        all_files = [
            f for f in os.listdir()
            if os.path.splitext(f)[1].lower() in allowed_exts and not f.startswith('processed_')
        ]

        if not all_files:
            print("No matching files found to process.")
            return

        for f in all_files:
            base, ext = os.path.splitext(f)
            ext = ext.lstrip('.').lower()
            if generate_ts:
                output_file_ts = os.path.join(output_dir, f"processed_{base}-{ext}-TS.txt")
                process_file(f, output_file_ts, include_timestamps=True)
            if generate_nots:
                output_file_nots = os.path.join(output_dir, f"processed_{base}-{ext}-noTS.txt")
                process_file(f, output_file_nots, include_timestamps=False)

    else:
        if not os.path.splitext(input_file)[1]:
            input_file += '.txt'
        if not os.path.exists(input_file):
            print(f"Error: '{input_file}' not found.")
            return
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        ext = os.path.splitext(input_file)[1].lstrip('.').lower()
        output_file_ts = os.path.join(output_dir, f"processed_{base_name}-{ext}-TS.txt")
        output_file_nots = os.path.join(output_dir, f"processed_{base_name}-{ext}-noTS.txt")

        if ts_choice == 'b':
            print(f"Generating both: {output_file_ts} and {output_file_nots}")
            process_file(input_file, output_file_ts, include_timestamps=True)
            process_file(input_file, output_file_nots, include_timestamps=False)
        elif ts_choice == 'y':
            output_file = input(f"Enter output filename (leave blank to use '{output_file_ts}'): ").strip()
            if not output_file:
                output_file = output_file_ts
            elif not os.path.splitext(output_file)[1]:
                output_file += '.txt'
            else:
                output_file = os.path.join(output_dir, output_file)
            process_file(input_file, output_file, include_timestamps=True)
        elif ts_choice == 'n':
            output_file = input(f"Enter output filename (leave blank to use '{output_file_nots}'): ").strip()
            if not output_file:
                output_file = output_file_nots
            elif not os.path.splitext(output_file)[1]:
                output_file += '.txt'
            else:
                output_file = os.path.join(output_dir, output_file)
            process_file(input_file, output_file, include_timestamps=False)

if __name__ == "__main__":
    main()
