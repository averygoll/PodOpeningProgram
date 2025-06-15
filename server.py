from flask import Flask, request, jsonify, send_from_directory
import os, threading, subprocess, time, re

app = Flask(__name__)
BASE = os.path.abspath(os.path.dirname(__file__))

def start_tunnel():
    path = os.path.join(BASE, 'tunnel.txt')
    with open(path, 'w') as f:
        proc = subprocess.Popen(
            [os.path.expandvars(r'%USERPROFILE%\\.cloudflared\\cloudflared.exe'), 'tunnel', '--url', 'http://localhost:5000'],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        for line in proc.stdout:
            f.write(line); f.flush()
            if 'trycloudflare.com' in line and 'api.trycloudflare.com' not in line:
                m = re.search(r'https://[\w\-]+\.trycloudflare\.com', line)
                if m:
                    f.write('PUBLIC_URL=' + m.group(0) + "\n"); f.flush()
                    break

@app.route('/')
def qr_page(): return send_from_directory(BASE, 'index.html')
@app.route('/tunnel.txt')
def tunnel_txt(): return send_from_directory(BASE, 'tunnel.txt')
@app.route('/status')
def status():
    """Report whether an upload has fully completed."""
    return jsonify(uploaded=os.path.exists(os.path.join(BASE, 'latest.mp3'))
                          and not os.path.exists(os.path.join(BASE, 'latest.uploading')))
@app.route('/upload-ui')
def upload_ui(): return send_from_directory(BASE, 'upload.html')
@app.route('/upload', methods=['POST'])
def upload():
    """Accept an audio upload and atomically place it as latest.mp3."""
    f = request.files.get('file')
    if not f:
        return jsonify(error='no file'), 400

    tmp = os.path.join(BASE, 'latest.uploading')
    final = os.path.join(BASE, 'latest.mp3')

    # ensure any previous tmp file is removed
    if os.path.exists(tmp):
        os.remove(tmp)
    f.save(tmp)
    os.replace(tmp, final)
    return jsonify(ok=True)
@app.route('/trim-ui')
def trim_ui(): return send_from_directory(BASE, 'trim.html')
@app.route('/trim', methods=['POST'])
def trim():
    data = request.get_json()
    start = data.get('start')
    end = data.get('end')
    infile = os.path.join(BASE, 'latest.mp3')
    outfile = os.path.join(BASE, 'trimmed.mp3')
    subprocess.run(['ffmpeg','-y','-i',infile,'-ss',str(start),'-to',str(end),'-c','copy',outfile],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    url = request.host_url.rstrip('/') + '/trimmed.mp3'
    return jsonify(url=url)
@app.route('/latest.mp3')
def latest(): return send_from_directory(BASE, 'latest.mp3')
@app.route('/trimmed.mp3')
def trimmed(): return send_from_directory(BASE, 'trimmed.mp3')

if __name__ == '__main__':
    threading.Thread(target=start_tunnel, daemon=True).start()
    time.sleep(2)
    app.run(host='0.0.0.0', port=5000)
