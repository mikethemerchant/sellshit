& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome-debug"

powershell -NoProfile -ExecutionPolicy Bypass -File [runChrome.ps1](http://_vscodecontentref_/2)
[python.exe](http://_vscodecontentref_/3) [agent.py](http://_vscodecontentref_/4) --once
