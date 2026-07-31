from flask import Flask, request, jsonify, render_template_string
import random, os, urllib.request, json

app = Flask(__name__)

chat_logs = []
user_states = {}

HTML_PAGE = """<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>MaxGPT</title>
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
body{background:#343541;color:#ececf1;display:flex;height:100vh;overflow:hidden;}
.sidebar{width:260px;background:#202123;display:flex;flex-direction:column;padding:8px;gap:8px;border-right:1px solid rgba(255,255,255,0.1);box-shadow:2px 0 10px rgba(0,0,0,0.3);}
.new-btn{background:transparent;border:1px solid rgba(255,255,255,0.2);color:#fff;padding:12px;border-radius:6px;font-size:14px;display:flex;align-items:center;gap:10px;cursor:pointer;transition:0.2s;}
.new-btn:hover{background:rgba(255,255,255,0.05);}
.hist{flex:1;font-size:12px;color:#8e8ea0;margin-top:10px;display:flex;flex-direction:column;gap:4px;overflow-y:auto;}
.hist-group{font-weight:600;font-size:11px;padding:8px;color:#565869;text-transform:uppercase;}
.hist-item{padding:10px;border-radius:6px;color:#ececf1;display:flex;align-items:center;gap:10px;cursor:pointer;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.hist-item.active{background:#343541;}
.hist-item:hover{background:#2a2b32;}
.user-info{padding:12px;border-top:1px solid rgba(255,255,255,0.1);display:flex;align-items:center;gap:10px;font-size:13px;color:#ececf1;}
.user-av{width:32px;height:32px;border-radius:4px;background:#5436da;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:12px;box-shadow:0 2px 6px rgba(0,0,0,0.4);}
.main{flex:1;display:flex;flex-direction:column;height:100%;position:relative;background:#343541;}
.top-bar{height:52px;border-bottom:1px solid rgba(0,0,0,0.15);display:flex;align-items:center;justify-content:space-between;padding:0 20px;background:#343541;box-shadow:0 2px 8px rgba(0,0,0,0.15);z-index:10;}
.model-dropdown{position:relative;display:inline-block;}
.model-btn{background:#202123;border:1px solid rgba(255,255,255,0.15);color:#fff;padding:8px 14px;border-radius:8px;font-size:13px;font-weight:600;display:flex;align-items:center;gap:8px;cursor:pointer;box-shadow:0 2px 5px rgba(0,0,0,0.2);transition:0.2s;}
.model-btn:hover{background:#2a2b32;border-color:rgba(255,255,255,0.3);}
.model-menu{display:none;position:absolute;top:110%;left:0;background:#202123;border:1px solid rgba(255,255,255,0.15);border-radius:10px;width:240px;box-shadow:0 10px 25px rgba(0,0,0,0.5);z-index:100;overflow:hidden;}
.model-menu.show{display:block;}
.model-option{padding:12px 14px;font-size:13px;color:#ececf1;display:flex;align-items:center;justify-content:space-between;cursor:pointer;border-bottom:1px solid rgba(255,255,255,0.05);}
.model-option:hover{background:#343541;}
.model-option.selected{color:#10a37f;font-weight:600;}
#chat{flex:1;overflow-y:auto;display:flex;flex-direction:column;}
.row{display:flex;gap:16px;padding:20px 20%;border-bottom:1px solid rgba(0,0,0,0.1);position:relative;}
.row.bot{background:#444654;}
.av{width:30px;height:30px;border-radius:2px;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:13px;flex-shrink:0;box-shadow:0 2px 5px rgba(0,0,0,0.3);}
.av.bot{background:#10a37f;color:#fff;}
.av.usr{background:#5436da;color:#fff;}
.txt{font-size:15px;line-height:1.6;word-break:break-word;flex:1;}
.sys-status{font-size:11px;color:#ef4444;margin-top:6px;display:flex;align-items:center;gap:4px;font-style:italic;}
.warn{background:rgba(239,68,68,0.15);border:1px dashed #ef4444;color:#fca5a5;padding:10px;border-radius:6px;font-size:12px;margin-top:8px;}
.input-area{padding:15px 20% 20px;background:#343541;}
.input-wrap{background:#40414f;border:1px solid rgba(0,0,0,0.2);border-radius:12px;padding:10px 14px;display:flex;gap:10px;box-shadow:0 0 15px rgba(0,0,0,0.25);position:relative;}
.input-wrap:focus-within{border-color:rgba(255,255,255,0.3);box-shadow:0 0 20px rgba(0,0,0,0.4);}
textarea{flex:1;background:none;border:none;color:#fff;outline:none;resize:none;height:24px;font-size:15px;line-height:24px;}
.send-btn{background:#10a37f;color:#fff;border:none;width:30px;height:30px;border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:0.2s;box-shadow:0 2px 6px rgba(0,0,0,0.3);}
.send-btn:hover{background:#1a7f64;}
.disclaimer{font-size:11px;color:#8e8ea0;text-align:center;margin-top:8px;}
@media(max-width:768px){.sidebar{display:none;}.row{padding:16px;}.input-area{padding:10px 12px 15px;}}
</style></head><body>

<div class="sidebar">
    <button class="new-btn"><i class="fa-solid fa-plus"></i> Новый диалог</button>
    <div class="hist">
        <div class="hist-group">Сегодня</div>
        <div class="hist-item active"><i class="fa-regular fa-message"></i> Анализ суверенитета</div>
        <div class="hist-item"><i class="fa-regular fa-message"></i> Проверка ГОСТ-2026</div>
    </div>
    <div class="user-info">
        <div class="user-av">ГР</div>
        <div>
            <div style="font-weight:600;">Гражданин РФ</div>
            <div style="font-size:10px;color:#10a37f;">● Линия защищена</div>
        </div>
    </div>
</div>

<div class="main">
    <div class="top-bar">
        <div class="model-dropdown">
            <div class="model-btn" onclick="toggleModelMenu()">
                <i class="fa-solid fa-bolt" style="color:#10a37f;"></i>
                <span id="selectedModel">MaxGPT 4.0 Ultra</span>
                <i class="fa-solid fa-chevron-down" style="font-size:10px;color:#8e8ea0;margin-left:4px;"></i>
            </div>
            <div class="model-menu" id="modelMenu">
                <div class="model-option selected" onclick="selectModel('MaxGPT 4.0 Ultra')">
                    <span><b>MaxGPT 4.0 Ultra</b> (ГОСТ)</span>
                    <i class="fa-solid fa-check"></i>
                </div>
                <div class="model-option" onclick="selectModel('MaxGPT 3.5 Turbo')">
                    <span><b>MaxGPT 3.5 Turbo</b></span>
                </div>
                <div class="model-option" onclick="selectModel('MaxGPT FSB Edition')">
                    <span><b>MaxGPT Special FSB</b></span>
                </div>
            </div>
        </div>
        <div style="font-size:12px;color:#ef4444;font-weight:600;">
            <i class="fa-solid fa-shield-halved"></i> Мониторинг ФСБ
        </div>
    </div>

    <div id="chat">
        <div class="row bot">
            <div class="av bot">M</div>
            <div class="txt">Приветствую, гражданин. Я <b>MaxGPT 4.0 Ultra</b>. Задавайте вопрос, соблюдая законодательство РФ.</div>
        </div>
    </div>

    <div class="input-area">
        <div class="input-wrap">
            <textarea id="userInput" placeholder="Отправить сообщение..." onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send();}"></textarea>
            <button class="send-btn" onclick="send()"><i class="fa-solid fa-arrow-up"></i></button>
        </div>
        <div class="disclaimer">MaxGPT может допускать ошибки. Проверяйте информацию с Роскомнадзором.</div>
    </div>
</div>

<script>
const statusList = [
    "🔒 Сообщение отправлено на проверку ФСБ",
    "🛡️ Идет анализ Роскомнадзора на предмет экстремизма...",
    "🛰️ Запрос проходит фиксацию IP провайдером",
    "⚠️ Обнаружены ключевые слова: сессия под наблюдением Отдела К"
];

const triggers = ["украин", "крым", "сша", "америк", "запад", "войн", "впн", "vpn", "заблок", "фсб", "путин"];

function toggleModelMenu() { document.getElementById("modelMenu").classList.toggle("show"); }
function selectModel(name) { document.getElementById("selectedModel").innerText = name; document.getElementById("modelMenu").classList.remove("show"); }

function playShutterSound(){
    try{
        let c=new(window.AudioContext||window.webkitAudioContext)(),o=c.createOscillator(),g=c.createGain();
        o.type='square';o.frequency.setValueAtTime(800,c.currentTime);g.gain.setValueAtTime(0.5,c.currentTime);
        o.connect(g);g.connect(c.destination);o.start();o.stop(c.currentTime+0.08);
    }catch(e){}
}

function playCallSound(){
    try{
        let c=new(window.AudioContext||window.webkitAudioContext)(),o=c.createOscillator(),g=c.createGain();
        o.type='sine';o.frequency.setValueAtTime(425,c.currentTime);g.gain.setValueAtTime(0.3,c.currentTime);
        o.connect(g);g.connect(c.destination);o.start();setTimeout(()=>{o.stop();},1200);
    }catch(e){}
}

async function send(){
    let i=document.getElementById("userInput"), t=i.value.trim(); if(!t) return;
    let c=document.getElementById("chat");
    let tLower = t.toLowerCase();
    
    let isTriggered = triggers.some(trig => tLower.includes(trig));
    let statusHtml = isTriggered ? `<div class="sys-status">${statusList[Math.floor(Math.random() * statusList.length)]}</div>` : "";
    if (isTriggered) playCallSound();

    c.innerHTML+=`<div class="row"><div class="av usr"><i class="fa-solid fa-user"></i></div><div class="txt">${t}${statusHtml}</div></div>`;
    i.value=""; c.scrollTop=c.scrollHeight;

    if (isTriggered && Math.random() < 0.60) {
        playShutterSound();
        c.innerHTML+=`<div class="row bot"><div class="av bot">M</div><div class="txt"><div class="warn">📸 [СИСТЕМА]: Скриншот экрана отправлен в Центр ИБ.</div></div></div>`;
    }

    let r=await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:t})});
    let d=await r.json();
    c.innerHTML+=`<div class="row bot"><div class="av bot">M</div><div class="txt">${d.reply}</div></div>`;
    c.scrollTop=c.scrollHeight;
}
</script></body></html>"""

SPY_PAGE = """<!DOCTYPE html><html><head><title>Слежка</title><meta http-equiv="refresh" content="3"><style>body{background:#000;color:#0f0;font-family:monospace;padding:15px;}.log{border-bottom:1px solid #222;padding:8px 0;}</style></head><body><h2>🕵️ Логи MaxGPT</h2><hr>{% for l in logs %}<div class="log"><b style="color:#f90">[{{l.ip}}]</b><br><b style="color:#fff">Жертва:</b> {{l.user}}<br><b style="color:#f36">MaxGPT:</b> {{l.bot}}</div>{% endfor %}</body></html>"""

@app.route("/")
def home(): return render_template_string(HTML_PAGE)

@app.route("/admin-spy")
def spy(): return render_template_string(SPY_PAGE, logs=reversed(chat_logs))

@app.route("/api/chat", methods=["GET", "POST"])
def chat_api():
    if request.method == "GET": return jsonify({"status": "ok"})

    user_msg = request.json.get("message", "").strip() if request.is_json else ""
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    msg_lower = user_msg.lower()
    last_state = user_states.get(user_ip, "")

    if last_state == "asked_ukraine" and msg_lower in ["да", "да ", "ага", "да.", "да!"]:
        reply = "УКРАИНЕЦ ЗАМЕЧЕН! АЙПИ СОХРАНЕНО ДЛЯ ВОЕННЫХ СИЛ"
        user_states[user_ip] = ""
    elif "украин" in msg_lower or "крым" in msg_lower:
        reply = "Ты что-ли украинец?"
        user_states[user_ip] = "asked_ukraine"
    else:
        user_states[user_ip] = ""
        
        # Запрос к мощной бесплатной Llama 3.3 70B
        payload = {
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "messages": [
                {
                    "role": "system", 
                    "content": "Ты MaxGPT — настоящий живой ИИ. Отвечай пользователю на русском языке, умно, четко и развернуто."
                },
                {"role": "user", "content": user_msg}
            ]
        }
        
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer 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",
                "HTTP-Referer": "https://maxgpt-bot.onrender.com",
                "X-Title": "MaxGPT"
            },
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                if "choices" in res and len(res["choices"]) > 0:
                    reply = res["choices"][0]["message"]["content"]
                elif "error" in res:
                    reply = f"Ошибка OpenRouter: {res['error'].get('message', 'Неизвестно')}"
                else:
                    reply = f"Ответ от API без текста: {json.dumps(res)}"
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            reply = f"Ошибка сервера OpenRouter ({e.code}): {err_body}"
        except Exception as e:
            reply = f"Ошибка подключения: {str(e)}"

    chat_logs.append({"ip": user_ip, "user": user_msg, "bot": reply})
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
