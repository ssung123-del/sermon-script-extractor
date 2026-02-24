import os
import tempfile
import yt_dlp
from app import process_single_video

url = "https://www.youtube.com/playlist?list=PLGeWFrxYX7Yvyo0dsp7yYfX9IYF23kHA3"

ydl_opts = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": "in_playlist",
    "ignoreerrors": True,
    "skip_download": True,
    "dump_single_json": True,
}

tmp_base = tempfile.mkdtemp(prefix="yt_test_")
output_dir = os.path.join(tmp_base, "scripts")
subtitle_tmp_dir = os.path.join(tmp_base, "subtitles")
os.makedirs(output_dir, exist_ok=True)
os.makedirs(subtitle_tmp_dir, exist_ok=True)

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(url, download=False)
    raw_entries = info.get("entries", [info])

    if raw_entries:
        entry = raw_entries[0]
        test_entry = {
            "index": 1,
            "id": entry.get("id", "unknown"),
            "title": entry.get("title", "제목없음"),
            "upload_date": entry.get("upload_date", "00000000"),
            "url": entry.get("url") or entry.get("webpage_url") or f"https://www.youtube.com/watch?v={entry.get('id', '')}"
        }
        print("Testing entry:", test_entry)
        result = process_single_video(test_entry, output_dir, subtitle_tmp_dir)
        print("Result:", result)
        
        # if error, print why
        if not result['success']:
            # check what happened in extract_subtitle
            pass
