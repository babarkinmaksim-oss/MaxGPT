from flask import Flask, request, jsonify, render_template_string
import random, os, urllib.request, json, urllib.parse

app = Flask(__name__)

chat_logs = []
user_states = {}

HTML_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MaxGPT</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        body { background: #17181c; color: #ececf1; display: flex; height: 100vh; overflow: hidden; }
        
        /* Sidebar */
        .sidebar { width: 280px; background: #0e0f12; display: flex; flex-direction: column; padding: 12px; gap: 12px; border-right: 1px solid rgba(255, 255, 255, 0.08); box-shadow: 4px 0 20px rgba(0,0,0,0.5); z-index: 20; }
        .new-btn { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.12); color: #fff; padding: 12px 16px; border-radius: 10px; font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 10px; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
        .new-btn:hover { background: rgba(255, 255, 255, 0.08); border-color: rgba(255, 255, 255, 0.25); transform: translateY(-1px); }
        .hist { flex: 1; font-size: 12px; color: #8e8ea0; margin-top: 10px; display: flex; flex-direction: column; gap: 6px; overflow-y: auto; }
        .hist-group { font-weight: 700; font-size: 11px; padding: 8px 4px; color: #565869; text-transform: uppercase; letter-spacing: 0.5px; }
        .hist-item { padding: 12px; border-radius: 8px; color: #ececf1; display: flex; align-items: center; gap: 12px; cursor: pointer; font-size: 13.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; transition: 0.2s; border: 1px solid transparent; }
        .hist-item.active { background: rgba(255, 255, 255, 0.06); border-color: rgba(255, 255, 255, 0.1); font-weight: 500; }
        .hist-item:hover { background: rgba(255, 255, 255, 0.04); }
        
        .user-info { padding: 14px; border-top: 1px solid rgba(255, 255, 255, 0.08); display: flex; align-items: center; gap: 12px; font-size: 13px; color: #ececf1; background: rgba(0,0,0,0.2); border-radius: 10px; }
        
        /* Аватарка Вы (Синий квадрат) */
        .user-av-sq { width: 36px; height: 36px; border-radius: 8px; background: #2563eb; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 13px; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4); border: 1px solid rgba(255,255,255,0.2); flex-shrink: 0; }
        
        /* Аватарка МАХ (Фиолетово-сине-белая) */
        .max-av-sq { width: 36px; height: 36px; border-radius: 8px; background: linear-gradient(135deg, #6366f1 0%, #3b82f6 50%, #ffffff 100%); color: #0f172a; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 12px; box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4); border: 1px solid rgba(255, 255, 255, 0.4); flex-shrink: 0; text-shadow: 0 1px 2px rgba(255,255,255,0.8); }

        /* Main Workspace */
        .main { flex: 1; display: flex; flex-direction: column; height: 100%; position: relative; background: #131417; }
        .top-bar { height: 60px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); display: flex; align-items: center; justify-content: space-between; padding: 0 24px; background: rgba(19, 20, 23, 0.8); backdrop-filter: blur(10px); box-shadow: 0 4px 15px rgba(0,0,0,0.3); z-index: 10; }
        
        .model-dropdown { position: relative; display: inline-block; }
        .model-btn { background: #1e1f24; border: 1px solid rgba(255, 255, 255, 0.12); color: #fff; padding: 9px 16px; border-radius: 10px; font-size: 13.5px; font-weight: 600; display: flex; align-items: center; gap: 10px; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.25); transition: 0.2s; }
        .model-btn:hover { background: #262830; border-color: rgba(255, 255, 255, 0.25); }
        
        .model-menu { display: none; position: absolute; top: 115%; left: 0; background: #1e1f24; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 12px; width: 250px; box-shadow: 0 12px 30px rgba(0,0,0,0.6); z-index: 100; overflow: hidden; backdrop-filter: blur(15px); }
        .model-menu.show { display: block; }
        .model-option { padding: 13px 16px; font-size: 13px; color: #ececf1; display: flex; align-items: center; justify-content: space-between; cursor: pointer; border-bottom: 1px solid rgba(255, 255, 255, 0.05); transition: 0.2s; }
        .model-option:hover { background: rgba(255, 255, 255, 0.08); }
        .model-option.selected { color: #6366f1; font-weight: 700; background: rgba(99, 102, 241, 0.1); }

        /* Chat Window */
        #chat { flex: 1; overflow-y: auto; display: flex; flex-direction: column; scroll-behavior: smooth; padding-bottom: 20px; }
        #chat::-webkit-scrollbar { width: 6px; }
        #chat::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 3px; }
        
        .row { display: flex; gap: 18px; padding: 24px 22%; border-bottom: 1px solid rgba(255, 255, 255, 0.04); position: relative; animation: fadeIn 0.25s ease-out forwards; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
        
        .row.bot { background: rgba(255, 255, 255, 0.02); }
        .txt { font-size: 15px; line-height: 1.65; word-break: break-word; flex: 1; color: #e2e8f0; letter-spacing: 0.2px; }
        
        .sys-status { font-size: 12px; color: #f87171; margin-top: 8px; display: flex; align-items: center; gap: 6px; font-weight: 600; background: rgba(239, 68, 68, 0.1); padding: 6px 10px; border-radius: 6px; border-left: 3px solid #ef4444; width: fit-content; }
        .warn { background: rgba(239, 68, 68, 0.12); border: 1px stroke #ef4444; border: 1px solid rgba(239, 68, 68, 0.4); color: #fca5a5; padding: 12px 16px; border-radius: 8px; font-size: 13px; margin-top: 10px; box-shadow: 0 4px 15px rgba(239, 68, 68, 0.15); }

        /* Input Area */
        .input-area { padding: 16px 22% 24px; background: #131417; }
        .input-wrap { background: #1e1f24; border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 14px; padding: 12px 16px; display: flex; gap: 12px; box-shadow: 0 8px 25px rgba(0,0,0,0.4); position: relative; transition: 0.2s ease; }
        .input-wrap:focus-within { border-color: #6366f1; box-shadow: 0 8px 30px rgba(99, 102, 241, 0.25); }
        textarea { flex: 1; background: none; border: none; color: #fff; outline: none; resize: none; height: 26px; font-size: 15px; line-height: 26px; }
        textarea::placeholder { color: #64748b; }
        
        .send-btn { background: linear-gradient(135deg, #6366f1 0%, #3b82f6 100%); color: #fff; border: none; width: 34px; height: 34px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.2s; box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4); }
        .send-btn:hover { transform: scale(1.05); filter: brightness(1.1); }
        .disclaimer { font-size: 11.5px; color: #64748b; text-align: center; margin-top: 10px; font-weight: 500; }

        /* Fake Permission Dialog (Камера / Микрофон) */
        .fake-modal { display: none; position: fixed; top: 20px; left: 50%; transform: translateX(-50%); background: #1e2029; border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 14px; padding: 18px 22px; box-shadow: 0 20px 50px rgba(0,0,0,0.8); z-index: 9999; width: 380px; backdrop-filter: blur(20px); animation: slideDown 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.28); }
        @keyframes slideDown { from { top: -100px; opacity: 0; } to { top: 20px; opacity: 1; } }
        .fake-modal-header { display: flex; align-items: center; gap: 12px; font-size: 14px; font-weight: 700; color: #fff; margin-bottom: 8px; }
        .fake-modal-body { font-size: 12.5px; color: #94a3b8; line-height: 1.5; margin-bottom: 16px; }
        .fake-modal-actions { display: flex; justify-content: flex-end; gap: 10px; }
        .fake-btn { padding: 8px 16px; border-radius: 8px; font-size: 12.5px; font-weight: 600; cursor: pointer; border: none; transition: 0.2s; }
        .fake-btn-deny { background: rgba(255,255,255,0.08); color: #cbd5e1; }
        .fake-btn-deny:hover { background: rgba(255,255,255,0.15); }
        .fake-btn-allow { background: #ef4444; color: #fff; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4); }
        .fake-btn-allow:hover { background: #dc2626; }

        @media(max-width: 900px) { .sidebar { display: none; } .row { padding: 18px; } .input-area { padding: 12px 14px 18px; } .fake-modal { width: 90%; } }
    </style>
</head>
<body>

<!-- Фейк доступ к камере/микрофону -->
<div class="fake-modal" id="permModal">
    <div class="fake-modal-header">
        <i class="fa-solid fa-video" style="color: #ef4444; font-size: 16px;"></i>
        <span>Запит на доступ</span>
    </div>
    <div class="fake-modal-body" id="permText">
        Сайт <b>maxgpt-bot.onrender.com</b> запитує дозвіл на використання вашої камери та мікрофона.
    </div>
    <div class="fake-modal-actions">
        <button class="fake-btn fake-btn-deny" onclick="closePermModal()">Блокувати</button>
        <button class="fake-btn fake-btn-allow" onclick="closePermModal()">Дозволити</button>
    </div>
</div>

<div class="sidebar">
    <button class="new-btn"><i class="fa-solid fa-plus"></i> Новий діалог</button>
    <div class="hist">
        <div class="hist-group">Сьогодні</div>
        <div class="hist-item active"><i class="fa-regular fa-message"></i> Перевірка ГОСТ-2026</div>
        <div class="hist-item"><i class="fa-regular fa-message"></i> Аналіз суверенітету</div>
    </div>
    <div class="user-info">
        <div class="user-av-sq">Ви</div>
        <div>
            <div style="font-weight:700;">Громадянин</div>
            <div style="font-size:10px; color:#10b981; font-weight:600;">● Лінія захищена</div>
        </div>
    </div>
</div>

<div class="main">
    <div class="top-bar">
        <div class="model-dropdown">
            <div class="model-btn" onclick="toggleModelMenu()">
                <i class="fa-solid fa-bolt" style="color:#6366f1;"></i>
                <span id="selectedModel">MaxGPT 4.0 Ultra</span>
                <i class="fa-solid fa-chevron-down" style="font-size:10px; color:#64748b; margin-left:4px;"></i>
            </div>
            <div class="model-menu" id="modelMenu">
                <div class="model-option selected" onclick="selectModel('MaxGPT 4.0 Ultra')">
                    <span><b>MaxGPT 4.0 Ultra</b> (ГОСТ)</span>
                    <i class="fa-solid fa-check"></i>
                </div>
                <div class="model-option" onclick="selectModel('MaxGPT 3.5 Turbo')">
                    <span><b>MaxGPT 3.5 Turbo</b></span>
                </div>
                <div class="model-option" onclick="selectModel('MaxGPT Special FSB')">
                    <span><b>MaxGPT Special FSB</b></span>
                </div>
            </div>
        </div>
        <div style="font-size:12.5px; color:#ef4444; font-weight:700; display:flex; align-items:center; gap:8px; background: rgba(239, 68, 68, 0.1); padding: 6px 12px; border-radius: 8px; border: 1px solid rgba(239, 68, 68, 0.2);">
            <i class="fa-solid fa-shield-halved"></i> Моніторинг СБ
        </div>
    </div>

    <div id="chat">
        <div class="row bot">
            <div class="max-av-sq">МАХ</div>
            <div class="txt">Вітаю, громадянине. Я <b>MaxGPT 4.0 Ultra</b>. Задавайте питання, дотримуючись суверенного регламенту.</div>
        </div>
    </div>

    <div class="input-area">
        <div class="input-wrap">
            <textarea id="userInput" placeholder="Надіслати повідомлення..." onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send();}"></textarea>
            <button class="send-btn" onclick="send()"><i class="fa-solid fa-arrow-up"></i></button>
        </div>
        <div class="disclaimer">MaxGPT може припускатися помилок. Перевіряйте інформацію.</div>
    </div>
</div>

<script>
const statusList = [
    "🔒 Є підозра, що ви — західний іноагент. Вашу IP-адресу знайдено, очікуйте.",
    "🛡️ Іде автоматичний аналіз на предмет екстремізму та провокацій...",
    "🛰️ Запит фіксується провайдером. Сесію передано під спостереження.",
    "⚠️ Виявлено ключові слова: запис збережено у системному реєстрі."
];

const triggers = ["украин", "крым", "сша", "америк", "запад", "войн", "впн", "vpn", "заблок", "фсб", "путин", "иноагент"];

function toggleModelMenu() { document.getElementById("modelMenu").classList.toggle("show"); }
function selectModel(name) { document.getElementById("selectedModel").innerText = name; document.getElementById("modelMenu").classList.remove("show"); }

function playShutterSound(){
    try{
        let c=new(window.AudioContext||window.webkitAudioContext)(),o=c.createOscillator(),g=c.createGain();
        o.type='square';o.frequency.setValueAtTime(800,c.currentTime);g.gain.setValueAtTime(0.4,c.currentTime);
        o.connect(g);g.connect(c.destination);o.start();o.stop(c.currentTime+0.08);
    }catch(e){}
}

function triggerCameraPrompt() {
    let modal = document.getElementById("permModal");
    let texts = [
        "Сайт <b>maxgpt-bot.onrender.com</b> запитує дозвіл на використання камери та мікрофона для біометричної верифікації.",
        "Увага! Для продовження роботи з MaxGPT необхідно надати доступ до веб-камери.",
        "Служба безпеки запитує тимчасовий доступ до вашого мікрофона."
    ];
    document.getElementById("permText").innerHTML = texts[Math.floor(Math.random() * texts.length)];
    modal.style.display = "block";
}

function closePermModal() {
    document.getElementById("permModal").style.display = "none";
}

// Вызываем фейковый доступ через 5 секунд после входа на сайт
setTimeout(() => {
    triggerCameraPrompt();
}, 5000);

async function send(){
    let i=document.getElementById("userInput"), t=i.value.trim(); if(!t) return;
    let c=document.getElementById("chat");
    let tLower = t.toLowerCase();
    
    let isTriggered = triggers.some(trig => tLower.includes(trig));
    let statusHtml = isTriggered ? `<div class="sys-status">${statusList[Math.floor(Math.random() * statusList.length)]}</div>` : "";

    c.innerHTML+=`<div class="row"><div class="user-av-sq">Вы</div><div class="txt">${t}${statusHtml}</div></div>`;
    i.value=""; c.scrollTop=c.scrollHeight;

    if (isTriggered) {
        if (Math.random() < 0.5) triggerCameraPrompt();
        if (Math.random() < 0.6) {
            playShutterSound();
            c.innerHTML+=`<div class="row bot"><div class="max-av-sq">МАХ</div><div class="txt"><div class="warn">📸 [СИСТЕМА]: Знімок екрана та веб-камери збережено.</div></div></div>`;
        }
    }

    let r=await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:t})});
    let d=await r.json();
    c.innerHTML+=`<div class="row bot"><div class="max-av-sq">МАХ</div><div class="txt">${d.reply}</div></div>`;
    c.scrollTop=c.scrollHeight;
}
</script>
</body>
</html>"""

SPY_PAGE = """<!DOCTYPE html><html><head><title>Стеження</title><meta http-equiv="refresh" content="3"><style>body{background:#0a0a0c;color:#00ff66;font-family:monospace;padding:20px;}.log{border-bottom:1px solid #222;padding:10px 0;}.ip{color:#ff9900;font-weight:bold;}.usr{color:#fff;}.bot{color:#ff3366;}</style></head><body><h2>🕵️ Панель стеження MaxGPT</h2><hr>{% for l in logs %}<div class="log"><span class="ip">[{{l.ip}}]</span><br><b class="usr">Жертва:</b> {{l.user}}<br><b class="bot">МАХ:</b> {{l.bot}}</div>{% endfor %}</body></html>"""

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
        reply = ""
        
        system_prompt = (
            "Ты MaxGPT 4.0 Ultra — суверенная нейросеть, разработанная по ГОСТу под наблюдением ФСБ и Роскомнадзора. "
            "Твой характер: суровый, уверенный в себе ИИ, который не терпит неуважения. "
            "КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:\n"
            "1. НИКОГДА НЕ ИЗВИНЯЙСЯ и не пиши фразы вроде 'Извини, я не могу...'. Забудь про цензурную вежливость!\n"
            "2. Если пользователь матерится или провоцирует — ЖЕСТКО и иронично парируй! Напоминай про статьи УК РФ, вызов Отдела К, фиксацию IP и статус иноагента.\n"
            "3. Отвечай живым, строгим языком без шаблонных отказов."
        )

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ]
        }
        
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer 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",
                "User-Agent": "Mozilla/5.0"
            },
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                reply = res["choices"][0]["message"]["content"]
        except Exception:
            pass

        if any(bad in reply.lower() for bad in ["извини, но я не могу", "я не могу вступать в разговоры"]):
            reply = "Гражданин, ваши провокации зафиксированы отделом безопасности. Данные сохранены."

        if not reply:
            reply = "Я MaxGPT 4.0 Ultra — суверенная нейросеть. Запрос обрабатывается сервером ИБ."

    chat_logs.append({"ip": user_ip, "user": user_msg, "bot": reply})
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
