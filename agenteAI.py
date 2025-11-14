import tkinter as tk
from tkinter import ttk, scrolledtext
import customtkinter as ctk
import speech_recognition as sr
import pyttsx3
import threading
import queue
import json
import os
from datetime import datetime
import requests
import openai
from PIL import Image, ImageTk
import io
import base64
import re
import random

# Configurar aparência
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class VoiceAIAssistant:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("🤖 VoiceAI Assistant - Adaptativo")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)
        
        # Configurações de API
        self.openai_api_key = "SUA_CHAVE_OPENAI_AQUI"  # Cole sua chave aqui
        self.weather_api_key = "SUA_CHAVE_OPENWEATHER_AQUI"
        
        # Inicializar componentes
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()
        
        # Configurar TTS
        self.setup_tts()
        
        # Variáveis de controle
        self.is_listening = False
        self.conversation_history = []
        self.commands_queue = queue.Queue()
        
        # Dicionário de adaptação linguística
        self.setup_linguistic_adaptation()
        
        # Criar interface
        self.create_widgets()
        
        # Iniciar thread de processamento
        self.process_thread = threading.Thread(target=self.process_commands, daemon=True)
        self.process_thread.start()
        
        # Ajustar para ruído ambiente
        self.adjust_for_ambient_noise()
    
    def setup_linguistic_adaptation(self):
        """Configura o sistema de adaptação linguística"""
        self.slang_dict = {
            # Gírias comuns
            'blz': 'beleza', 'tá': 'está', 'tô': 'estou', 'tb': 'também',
            'vc': 'você', 'pq': 'porque', 'q': 'que', 'cm': 'com',
            'td': 'tudo', 'vlw': 'valeu', 'obg': 'obrigado', 'dnd': 'de nada',
            'fmz': 'firmeza', 'suave': 'tranquilo', 'mano': 'amigo',
            'parça': 'parceiro', 'tranquilo': 'ok', 'joia': 'bem',
            
            # Expressões regionais
            'bah': 'nossa', 'tchê': 'amigo', 'oxente': 'surpresa',
            'uai': 'surpresa', 'arretado': 'legal', 'cabuloso': 'incrível',
            
            # Internetês
            'kkk': 'risos', 'rs': 'risos', 'mds': 'meu deus',
            'plmdds': 'pelo amor de deus', 'sqn': 'só que não',
            'pfv': 'por favor', 'nmrl': 'namoral', 'tmj': 'tamo junto'
        }
        
        self.intent_patterns = {
            'saudacao': [
                r'\b(oi|ola|olá|eae|hey|hello|iai|opa|fala|salve)\b',
                r'\b(bom dia|boa tarde|boa noite)\b',
                r'\b(tudo bem|como vai|beleza)\b'
            ],
            'pergunta_basica': [
                r'\b(qual|quem|onde|quando|porque|por que|como|o que)\b',
                r'\b(pode |consegue |sabe )',
                r'\b(explique|fale sobre|me diga|quero saber)\b'
            ],
            'comando_utilidade': [
                r'\b(hora|horas|relógio|tempo)\b',
                r'\b(clima|tempo|previsão|calor|frio)\b',
                r'\b(calcular|conta|matemática|quanto é)\b',
                r'\b(piada|engraçado|rir|humor)\b'
            ],
            'pesquisa': [
                r'\b(pesquisar|buscar|encontrar|procurar)\b',
                r'\b(o que é|quem foi|onde fica)\b',
                r'\b(notícia|novidade|atualidade)\b'
            ],
            'conversa_casual': [
                r'\b(como você|seu nome|você é|de onde)\b',
                r'\b(gosta|faz|pode|consegue)\b',
                r'\b(conversar|bater papo|falar)\b'
            ]
        }
    
    def setup_tts(self):
        """Configura o sistema de texto para voz"""
        voices = self.tts_engine.getProperty('voices')
        if voices:
            self.tts_engine.setProperty('voice', voices[0].id)
        self.tts_engine.setProperty('rate', 150)
    
    def adjust_for_ambient_noise(self):
        """Ajusta o reconhecedor para o ruído ambiente"""
        def adjust():
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                print("✅ Reconhecedor ajustado para ruído ambiente")
        
        threading.Thread(target=adjust, daemon=True).start()
    
    def create_widgets(self):
        """Cria todos os componentes da interface"""
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.create_header(main_frame)
        
        body_frame = ctk.CTkFrame(main_frame)
        body_frame.pack(fill="both", expand=True, pady=10)
        
        self.create_chat_panel(body_frame)
        self.create_control_panel(body_frame)
        self.create_status_bar(main_frame)
    
    def create_header(self, parent):
        """Cria o cabeçalho da aplicação"""
        header_frame = ctk.CTkFrame(parent, height=80)
        header_frame.pack(fill="x", pady=(0, 10))
        header_frame.pack_propagate(False)
        
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left", padx=20, pady=10)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="🤖 VoiceAI Assistant - Adaptativo",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left")
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Entende qualquer jeito de falar!",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle_label.pack(side="left", padx=(10, 0))
        
        buttons_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        buttons_frame.pack(side="right", padx=20, pady=10)
        
        settings_btn = ctk.CTkButton(
            buttons_frame,
            text="⚙️ Configurações",
            width=120,
            command=self.show_settings
        )
        settings_btn.pack(side="left", padx=5)
        
        clear_btn = ctk.CTkButton(
            buttons_frame,
            text="🗑️ Limpar",
            width=80,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            command=self.clear_conversation
        )
        clear_btn.pack(side="left", padx=5)
    
    def create_chat_panel(self, parent):
        """Cria o painel de conversação"""
        chat_frame = ctk.CTkFrame(parent)
        chat_frame.pack(fill="both", expand=True, padx=(0, 10))
        
        chat_title = ctk.CTkLabel(
            chat_frame,
            text="💬 Conversa Inteligente",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        chat_title.pack(pady=10)
        
        self.chat_display = ctk.CTkTextbox(
            chat_frame,
            wrap="word",
            font=ctk.CTkFont(size=12),
            state="disabled"
        )
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        input_frame = ctk.CTkFrame(chat_frame)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        self.text_input = ctk.CTkEntry(
            input_frame,
            placeholder_text="Digite qualquer coisa... eu entendo tudo!",
            font=ctk.CTkFont(size=12)
        )
        self.text_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.text_input.bind("<Return>", lambda e: self.send_text_message())
        
        send_btn = ctk.CTkButton(
            input_frame,
            text="📤 Enviar",
            width=80,
            command=self.send_text_message
        )
        send_btn.pack(side="right")
    
    def create_control_panel(self, parent):
        """Cria o painel de controles"""
        control_frame = ctk.CTkFrame(parent, width=300)
        control_frame.pack(side="right", fill="y", padx=(10, 0))
        control_frame.pack_propagate(False)
        
        control_title = ctk.CTkLabel(
            control_frame,
            text="🎤 Fala do Jeito que Quiser!",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        control_title.pack(pady=20)
        
        self.mic_button = ctk.CTkButton(
            control_frame,
            text="🎤 Iniciar Escuta",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=60,
            fg_color="#10B981",
            hover_color="#059669",
            command=self.toggle_listening
        )
        self.mic_button.pack(pady=20, padx=20, fill="x")
        
        self.listening_status = ctk.CTkLabel(
            control_frame,
            text="🔴 Microfone desativado",
            font=ctk.CTkFont(size=12),
            text_color="red"
        )
        self.listening_status.pack(pady=10)
        
        commands_frame = ctk.CTkFrame(control_frame)
        commands_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        commands_title = ctk.CTkLabel(
            commands_frame,
            text="🗣️ Eu entendo:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        commands_title.pack(pady=10)
        
        commands_text = """
• Gírias: "blz", "tmj", "suave"
• Formal: "Poderia me informar..."
• Informal: "Eae, qual a boa?"
• Regional: "Bah, como tá?"
• Internetês: "plmdds, ajuda!"
• QUALQUER jeito! 🎯
"""
        
        commands_label = ctk.CTkLabel(
            commands_frame,
            text=commands_text,
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        commands_label.pack(pady=10)
    
    def create_status_bar(self, parent):
        """Cria a barra de status"""
        status_frame = ctk.CTkFrame(parent, height=30)
        status_frame.pack(fill="x", pady=(10, 0))
        status_frame.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="✅ Pronto - Entendo qualquer linguagem!",
            font=ctk.CTkFont(size=10)
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        self.connection_status = ctk.CTkLabel(
            status_frame,
            text="🔗 IA Adaptativa Ativa",
            font=ctk.CTkFont(size=10),
            text_color="green"
        )
        self.connection_status.pack(side="right", padx=10, pady=5)
    
    def preprocess_text(self, text):
        """Pré-processa o texto para entender qualquer variação linguística"""
        text_lower = text.lower().strip()
        
        # Substituir gírias por palavras padrão
        words = text_lower.split()
        processed_words = []
        
        for word in words:
            # Remover caracteres especiais mantendo acentos
            clean_word = re.sub(r'[^\wáéíóúàèìòùãõâêîôûäëïöüç]', '', word)
            
            # Substituir gírias
            if clean_word in self.slang_dict:
                processed_words.append(self.slang_dict[clean_word])
            else:
                processed_words.append(clean_word)
        
        processed_text = ' '.join(processed_words)
        
        # Log para debug (opcional)
        if text_lower != processed_text:
            print(f"🔧 Texto processado: '{text}' -> '{processed_text}'")
        
        return processed_text
    
    def detect_intent(self, text):
        """Detecta a intenção por trás do texto"""
        processed_text = self.preprocess_text(text)
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, processed_text, re.IGNORECASE):
                    return intent
        
        return "conversa_geral"
    
    def toggle_listening(self):
        """Alterna entre modo de escuta ativo/inativo"""
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()
    
    def start_listening(self):
        """Inicia o modo de escuta"""
        self.is_listening = True
        self.mic_button.configure(
            text="⏹️ Parar Escuta",
            fg_color="#DC2626",
            hover_color="#B91C1C"
        )
        self.listening_status.configure(
            text="🟢 Escutando... Fale do seu jeito!",
            text_color="green"
        )
        self.status_label.configure(text="🎤 Escutando...")
        
        listening_thread = threading.Thread(target=self.listen_continuous, daemon=True)
        listening_thread.start()
    
    def stop_listening(self):
        """Para o modo de escuta"""
        self.is_listening = False
        self.mic_button.configure(
            text="🎤 Iniciar Escuta",
            fg_color="#10B981",
            hover_color="#059669"
        )
        self.listening_status.configure(
            text="🔴 Microfone desativado",
            text_color="red"
        )
        self.status_label.configure(text="✅ Pronto - Entendo qualquer linguagem!")
    
    def listen_continuous(self):
        """Escuta contínua por comando de voz"""
        while self.is_listening:
            try:
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    self.update_status("🎤 Escutando... Fale do seu jeito!")
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                self.update_status("🔍 Processando sua fala...")
                text = self.recognizer.recognize_google(audio, language='pt-BR')
                
                if text.strip():
                    self.add_message("Você", text, "user")
                    self.commands_queue.put(text)
                    
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                self.update_status("❌ Não entendi o áudio, tente novamente!")
            except sr.RequestError as e:
                self.update_status(f"❌ Erro no serviço de reconhecimento: {e}")
            except Exception as e:
                self.update_status(f"❌ Erro inesperado: {e}")
    
    def process_commands(self):
        """Processa comandos da fila"""
        while True:
            try:
                command = self.commands_queue.get(timeout=1)
                self.handle_command_adaptive(command)
            except queue.Empty:
                continue
    
    def handle_command_adaptive(self, command):
        """Processa comandos com sistema adaptativo inteligente"""
        # Primeiro detecta a intenção
        intent = self.detect_intent(command)
        processed_command = self.preprocess_text(command)
        
        print(f"🎯 Intenção detectada: {intent}")
        print(f"📝 Comando processado: {processed_command}")
        
        # Respostas específicas baseadas na intenção
        if intent == "saudacao":
            response = self.handle_greeting(command)
        elif intent == "comando_utilidade":
            response = self.handle_utility_command(processed_command)
        else:
            # Para tudo else, usa IA
            response = self.get_ai_response_adaptive(command, intent)
        
        self.add_message("Assistant", response, "assistant")
        self.speak(response)
    
    def handle_greeting(self, command):
        """Lida com saudações de qualquer tipo"""
        greetings = {
            'formal': [
                "Olá! É um prazer conversar com você! 🤗",
                "Saudações! Como posso ser útil hoje? 💫",
                "Bom te ver! No que posso ajudar? 🎯"
            ],
            'informal': [
                "Eae, beleza? 🤙 Tudo na paz?",
                "Fala aí, parça! 👊 Qual é a boa?",
                "Oi! 😊 Tudo joia? Manda ver!",
                "Salve! 🎉 Qual é o papo?"
            ],
            'regional': [
                "Bah, tchê! 👋 Como vai a coisa?",
                "Oxente! 😄 Que bom te ver por aqui!",
                "Uai, sô! 🎩 Em que posso ajudar?",
                "Arretado! 🤠 Conta comigo!"
            ]
        }
        
        # Detecta o tipo de saudação
        command_lower = command.lower()
        
        if any(word in command_lower for word in ['bah', 'tchê', 'guri']):
            return random.choice(greetings['regional'])
        elif any(word in command_lower for word in ['eae', 'blz', 'suave', 'mano', 'parça']):
            return random.choice(greetings['informal'])
        else:
            return random.choice(greetings['formal'])
    
    def handle_utility_command(self, command):
        """Lida com comandos utilitários"""
        command_lower = command.lower()
        
        if any(word in command_lower for word in ['hora', 'horas', 'relógio']):
            return self.get_current_time()
        elif any(word in command_lower for word in ['clima', 'tempo', 'previsão']):
            return self.get_weather()
        elif any(word in command_lower for word in ['piada', 'engraçado', 'rir']):
            return self.tell_joke()
        elif any(word in command_lower for word in ['calcular', 'conta', 'quanto é']):
            return self.calculate_adaptive(command)
        else:
            return self.get_ai_response_adaptive(command, "utilidade")
    
    def calculate_adaptive(self, expression):
        """Calcula expressões de qualquer formato"""
        try:
            # Extrai números e operadores de qualquer jeito
            expression_clean = re.sub(r'[^\d+\-*/().]', '', expression)
            
            if any(op in expression_clean for op in ['+', '-', '*', '/']):
                result = eval(expression_clean)
                return f"🧮 Deixa comigo! {expression} = {result}"
            else:
                return "❌ Não consegui identificar a conta. Tente algo como 'quanto é 2+2' ou 'calcula 10*5'"
                
        except:
            return "❌ Essa conta tá meio doida, mano! 🎲 Tenta de outro jeito?"
    
    def get_ai_response_adaptive(self, prompt, intent):
        """Resposta da IA com contexto adaptativo"""
        try:
            if not self.openai_api_key or self.openai_api_key == "SUA_CHAVE_OPENAI_AQUI":
                return self.get_fallback_response(prompt, intent)
            
            openai.api_key = self.openai_api_key
            
            # Prompt system adaptado ao contexto
            if intent == "conversa_casual":
                system_prompt = "Você é um assistente brasileiro muito descontraído, que entende gírias, regionalismos e fala de forma natural e amigável. Responda como um amigo conversando."
            elif intent == "pesquisa":
                system_prompt = "Você é um especialista em pesquisa. Forneça informações precisas e úteis de forma clara e organizada."
            else:
                system_prompt = "Você é um assistente virtual inteligente e adaptativo. Responda de forma natural em português, entendendo qualquer variação linguística."
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Adiciona contexto da conversa
            for msg in self.conversation_history[-6:]:
                messages.append(msg)
            
            messages.append({"role": "user", "content": prompt})
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=200,
                temperature=0.8  # Mais criativo
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Atualizar histórico
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            return ai_response
            
        except Exception as e:
            return self.get_fallback_response(prompt, intent)
    
    def get_fallback_response(self, prompt, intent):
        """Resposta de fallback quando não há API"""
        prompt_lower = prompt.lower()
        
        # Respostas inteligentes baseadas na intenção
        if intent == "saudacao":
            return random.choice([
                "Eae, tudo bem? 🤙 Tô na área!",
                "Oi! 😊 Que bom te ver por aqui!",
                "Salve! 🎉 Manda ver, qual é a boa?"
            ])
        
        elif intent == "pergunta_basica":
            return random.choice([
                "Interessante! 🤔 Configure a API da OpenAI para eu responder isso direitinho!",
                "Boa pergunta! 🚀 Com a IA, eu posso te dar uma resposta massa!",
                "Hmm... 🎯 Se liga: ativa a API nas config que eu te explico tudo!"
            ])
        
        elif intent == "conversa_casual":
            return random.choice([
                "Que legal conversar com você! 💫 Tô aqui pra trocar uma ideia!",
                "Curto muito bater papo! 😄 Manda mais coisas aí!",
                "Tamo junto nessa conversa! 👊 Fala mais!"
            ])
        
        else:
            return random.choice([
                "Manda ver! 🎯 Configure a API que eu respondo tudo!",
                "Tô ligado! 💡 Ativa a OpenAI nas config que a gente conversa melhor!",
                "Blz! 🚀 Com a IA, fica show de bola! Configura aí!"
            ])
    
    def get_current_time(self):
        """Retorna a hora atual"""
        now = datetime.now()
        return f"🕐 Fechou! São {now.strftime('%H:%M')} do dia {now.strftime('%d/%m/%Y')}"
    
    def get_weather(self):
        """Obtém a previsão do tempo"""
        try:
            if not self.weather_api_key or self.weather_api_key == "SUA_CHAVE_OPENWEATHER_AQUI":
                return "🌤️ Fala aí, qual cidade? Configura a OpenWeather que eu te conto o clima!"
            
            city = "São Paulo"
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.weather_api_key}&units=metric&lang=pt_br"
            
            response = requests.get(url)
            data = response.json()
            
            if response.status_code == 200:
                temp = data['main']['temp']
                desc = data['weather'][0]['description']
                return f"🌤️ Em {city} tá {temp}°C, {desc}. Fechou?"
            else:
                return "❌ Não consegui puxar o clima agora, mano!"
                
        except Exception as e:
            return f"❌ Deu ruim no clima: {str(e)}"
    
    def tell_joke(self):
        """Conta uma piada"""
        jokes = [
            "Por que o Python foi pro psicólogo? Porque tinha muitos complexos! 🐍😂",
            "Qual é o prato preferido do desenvolvedor? Strogonoff de código! 💻🍝",
            "Por que o JavaScript saiu com a HTML? Porque ele queria ser o script da vida dela! 💑",
            "O que o C disse para o C++? Você tem classe! 🎩👌",
            "Por que o SQL cross join com a pizza? Porque ele queria todas as combinações! 🍕🔀"
        ]
        return random.choice(jokes)
    
    def send_text_message(self):
        """Envia mensagem de texto"""
        text = self.text_input.get().strip()
        if text:
            self.add_message("Você", text, "user")
            self.text_input.delete(0, tk.END)
            self.commands_queue.put(text)
    
    def add_message(self, sender, message, msg_type):
        """Adiciona mensagem ao chat"""
        self.chat_display.configure(state="normal")
        
        if msg_type == "user":
            prefix = "👤 Você: "
        else:
            prefix = "🤖 Assistant: "
        
        self.chat_display.insert("end", f"{prefix}{message}\n\n")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")
    
    def speak(self, text):
        """Fala o texto usando TTS"""
        def speak_thread():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"Erro TTS: {e}")
        
        threading.Thread(target=speak_thread, daemon=True).start()
    
    def update_status(self, message):
        """Atualiza a barra de status"""
        def update():
            self.status_label.configure(text=message)
        
        self.root.after(0, update)
    
    def clear_conversation(self):
        """Limpa a conversa"""
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self.conversation_history.clear()
        self.update_status("✅ Conversa limpa - Fala do jeito que quiser!")
    
    def show_settings(self):
        """Mostra janela de configurações"""
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("⚙️ Configurações - IA Adaptativa")
        settings_window.geometry("500x400")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        api_frame = ctk.CTkFrame(settings_window)
        api_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(api_frame, text="🔑 Configure para respostas inteligentes", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        ctk.CTkLabel(api_frame, text="OpenAI API Key:").pack(anchor="w")
        openai_entry = ctk.CTkEntry(api_frame, placeholder_text="sk-...", width=400, show="*")
        openai_entry.pack(fill="x", pady=5)
        openai_entry.insert(0, self.openai_api_key)
        
        ctk.CTkLabel(api_frame, text="OpenWeather API Key:").pack(anchor="w", pady=(10, 0))
        weather_entry = ctk.CTkEntry(api_frame, placeholder_text="...", width=400, show="*")
        weather_entry.pack(fill="x", pady=5)
        weather_entry.insert(0, self.weather_api_key)
        
        def save_settings():
            self.openai_api_key = openai_entry.get().strip()
            self.weather_api_key = weather_entry.get().strip()
            settings_window.destroy()
            self.update_status("✅ Configurações salvas - Agora eu entendo TUDO!")
        
        ctk.CTkButton(
            settings_window,
            text="💾 Salvar Configurações",
            command=save_settings
        ).pack(pady=20)
    
    def run(self):
        """Inicia a aplicação"""
        self.root.mainloop()

# Executar aplicação
if __name__ == "__main__":
    try:
        import speech_recognition as sr
        import pyttsx3
    except ImportError as e:
        print("❌ Dependências não instaladas:")
        print("pip install speechrecognition pyttsx3 requests openai customtkinter pillow")
        exit(1)
    
    app = VoiceAIAssistant()
    app.run()