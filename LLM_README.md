# Clockmate-with-LLM-termlit
結合termlit、Akasha、clockmate，協助員工輕鬆打卡

> 新增
> - `clockmate_entry.py`: 打卡助理termlit入口
> - `LLM_README.md`: 加入LLM說明文件
> - `llm_cli.py`: Clockmate 主要入口
> - `llm_clockmate.py`: prompt生成與當月json生成
> - `main.py`: 新增函數:
>   - `run_llm_cli` : 通過 `user_prompt` 產生 `custom_work_times` (逐日dict) 並傳入 `get_fresh_form_llm_data`
>   - `get_fresh_form_llm_data` : 將傳入的 `custom_work_times` 再傳入 `generate_form_llm_data`
>   - `generate_form_llm_data` : 根據傳入dict格式，選擇整月統一輸入或是逐日輸入不同值

## Quick start
1. Install the package (editable mode during development is fine):
   ```bash
   pip install -e .
   ```

   or, if you prefer [uv](https://github.com/astral-sh/uv):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh  # install uv (once)
   uv pip install -e .
   ```

2. Serve it over SSH:
   ```bash
   termlit run clockmate_entry.py --host 0.0.0.0 --port 2222
   ```
   > 加上 `--auth none` 可讓使用者免密碼登入（預設為 `--auth ssh` 需輸入密碼）。
3. Connect from any SSH client (default credentials `admin/password123`):
   ```bash
   ssh admin@127.0.0.1 -p 2222
   ```

## CLI flags
- `--user name=secret`: add/override login credentials (repeatable).
- `--auth {ssh,none}`: choose between password-protected (`ssh`) or passwordless (`none`) sessions.
- `--allow-anonymous`: accept any username/password combo.
- `--host` / `--port`: where the SSH server listens.

## Programmatic usage
You can also embed Termlit inside a Python process:
```python
import termlit

def app():
    termlit.welcome("Inline app")
    termlit.write("Hello there!")
    termlit.goodbye()

if __name__ == "__main__":
    termlit.run(app, host="127.0.0.1", port=2222)
```
> 需要免密碼體驗時，可傳入 `auth_mode="none"` 給 `termlit.run`.

## Uploading files
Use the `upload_files`/`upload_file` helpers when your script needs to drop
artifacts (reports, logs, etc.) into a directory that you can fetch later:

```python
import termlit

# Copy a single file to ./upload_files (or $TERMLIT_UPLOAD_DIR) with progress
termlit.upload_files("build/output/report.pdf", show_progress=True)

# Copy multiple files and grab the resulting server-side paths
uploaded = termlit.upload_file(
    ["app.log", r"C:\temp\screenshot.png"],
    show_progress=True,
)
termlit.write("Saved files to:")
for path in uploaded:
    termlit.write(f" - {path}")

# Provide ready-to-run scp commands for the client
cmd = termlit.download_cmd(
    "report.pdf",
    source_dir="upload_files",
)
termlit.write("在本機終端執行以下指令即可下載：")
termlit.write(cmd)

# Or host a temporary HTTP download link
http_links = termlit.download_cmd(
    "report.pdf",
    source_dir="upload_files",
    type="http",
)
termlit.write("也可以使用瀏覽器開啟：")
termlit.write(http_links)
```

All files are copied into `upload_files/` relative to where `termlit run` was
executed (override via the `TERMLIT_UPLOAD_DIR` environment variable or the
``destination_dir`` argument). Pass `show_progress=True` to stream simple
percentage updates back to the SSH client while a file is being copied. Use
`termlit.download_cmd(...)` to generate the scp command your users should run
locally, pass ``source_dir="upload_files"`` when you want to specify the hosting
folder, or set ``type="http"`` to spin up a temporary `http.server` over the
target folder. Set `TERMLIT_DOWNLOAD_HOST`, `TERMLIT_DOWNLOAD_PORT`,
`TERMLIT_DOWNLOAD_USER`, or `TERMLIT_HTTP_PORT` when the defaults are
insufficient.

## Downloading files
Once your script calls `termlit.upload_file(...)`, you have two convenient ways
to guide end users through downloading the artifacts:

1. **scp 指令** – 呼叫 `termlit.download_cmd("report.pdf", source_dir="upload_files")`
   會產生像 `scp -P 2222 admin@<host>:/abs/path/report.pdf ./` 的字串。把這段
   指令回傳給使用者，請他們複製到本機終端即可。必要時可以透過環境變數
   `TERMLIT_DOWNLOAD_HOST`, `TERMLIT_DOWNLOAD_PORT`, `TERMLIT_DOWNLOAD_USER`
   來調整 host/port/user，或在呼叫時覆寫 `host=`, `port=`, `username=`,
   `destination=`。
2. **HTTP 下載** – 傳入 `type="http"`，例如
   `termlit.download_cmd("report.pdf", source_dir="upload_files", type="http")`，
   會在指定資料夾啟動 `http.server`（預設 port `8765` 可用
   `TERMLIT_HTTP_PORT` 覆寫），並回傳 `http://<host>:8765/report.pdf` 這類
   URL。使用者只要在瀏覽器輸入/點擊即可下載；伺服器端的 access log 也會被
   自動抑制，避免干擾 SSH 介面。

> HTTP 模式要求所有檔案在同一個資料夾，可將檔案集中到 `upload_files/`
> 後再生成連結。下載完記得通知使用者關閉臨時 HTTP server（重新啟動 app
> 或自訂指令）以維持安全。

## Repository layout
- `termlit/session.py` – public helper implementations.
- `termlit/runtime.py` – SSH server + script runner.
- `termlit/cli.py` – command line interface (`termlit run`).
- `termlit/ssh_server_plain.py`, `termlit/telnet_server.py` – original demo servers (optional utilities; they call an external FastAPI backend that you must run yourself).
- `termlit/start_services.py` – helper script that starts the Telnet/SSH demos and forwards the `--fastapi-url` you provide.

Happy terminal building!
