import random
import os
import math
import struct
import pygame

# Solicita orientacao horizontal no Android quando a integracao estiver disponivel.
try:
    from jnius import autoclass
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    ActivityInfo = autoclass("android.content.pm.ActivityInfo")
    PythonActivity.mActivity.setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE)
except Exception:
    # Em ambientes sem Pyjnius, use a orientacao definida pelo sistema.
    pass

# FNAF Tresland's - versão adaptada para Android/Pydroid 3 com Pygame
# No Pydroid 3, instale pygame pelo Pip antes de executar este arquivo.

pygame.init()
pygame.display.set_caption("FNAF Tresland's")

# Audio procedural: efeitos sintetizados no proprio jogo, sem arquivos externos.
# Se o dispositivo nao suportar audio, o jogo continua funcionando normalmente.
SOM_ATIVO = False
SONS = {}

def iniciar_sons():
    global SOM_ATIVO, SONS
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=1024)
        SOM_ATIVO = pygame.mixer.get_init() is not None
        if not SOM_ATIVO:
            return

        def criar_tom(freq, duracao, volume=0.25, forma="seno", freq_final=None):
            taxa = 22050
            total = max(1, int(taxa * duracao))
            amostras = bytearray()
            for i in range(total):
                t = i / taxa
                f = freq
                if freq_final is not None:
                    f = freq + (freq_final - freq) * (i / max(1, total - 1))
                fase = 2 * math.pi * f * t
                if forma == "ruido":
                    valor = random.uniform(-1, 1)
                elif forma == "quadrada":
                    valor = 1 if math.sin(fase) >= 0 else -1
                else:
                    valor = math.sin(fase)
                # fade nas pontas para evitar estalos fortes
                envelope = min(1.0, i / max(1, taxa * 0.015), (total - i) / max(1, taxa * 0.03))
                valor = max(-1.0, min(1.0, valor * volume * max(0, envelope)))
                amostras.extend(struct.pack("<h", int(valor * 32767)))
            return pygame.mixer.Sound(buffer=bytes(amostras))

        SONS["clique"] = criar_tom(950, 0.045, 0.14, "quadrada", 520)
        SONS["camera"] = criar_tom(620, 0.12, 0.18, "quadrada", 280)
        SONS["porta"] = criar_tom(105, 0.24, 0.32, "ruido")
        SONS["passos"] = criar_tom(78, 0.18, 0.20, "ruido", 48)
        SONS["aviso"] = criar_tom(440, 0.18, 0.18, "seno", 330)
        SONS["susto"] = criar_tom(120, 0.65, 0.38, "ruido", 42)
        SONS["vitoria"] = criar_tom(523, 0.32, 0.20, "seno", 784)
        SONS["energia"] = criar_tom(170, 0.45, 0.20, "quadrada", 65)
    except Exception:
        SOM_ATIVO = False
        SONS = {}

def tocar_som(nome):
    if SOM_ATIVO and nome in SONS:
        try:
            SONS[nome].play()
        except Exception:
            pass

iniciar_sons()

# Musica ambiente original gerada em codigo para o menu (nao precisa de MP3 externo).
MUSICA_MENU = None
CANAL_MUSICA = None
MUSICA_MENU_ATIVA = False

def preparar_musica_menu():
    global MUSICA_MENU, CANAL_MUSICA
    if not SOM_ATIVO or MUSICA_MENU is not None:
        return
    try:
        taxa = 22050
        # Frase mais longa e variada: alterna notas graves, médias e agudas,
        # com pausas e pequenos motivos diferentes para não soar repetitiva.
        duracao = 12.0
        total = int(taxa * duracao)
        # (início, frequência, duração, volume relativo)
        notas = [
            (0.00, 392.00, 0.70, 0.85), (0.82, 311.13, 0.90, 0.75),
            (1.90, 466.16, 0.48, 0.65), (2.48, 622.25, 0.62, 0.52),
            (3.28, 349.23, 0.85, 0.78), (4.26, 261.63, 1.00, 0.85),
            (5.42, 523.25, 0.42, 0.48), (5.96, 392.00, 0.62, 0.60),
            (6.72, 233.08, 1.05, 0.80), (7.96, 293.66, 0.58, 0.68),
            (8.66, 440.00, 0.55, 0.56), (9.34, 587.33, 0.72, 0.46),
            (10.20, 349.23, 0.65, 0.66), (11.00, 261.63, 0.78, 0.78),
        ]
        dados = bytearray()
        for i in range(total):
            t = i / taxa
            valor = 0.0
            for inicio, freq, comprimento, volume_nota in notas:
                local = t - inicio
                if 0 <= local < comprimento:
                    ataque = min(1.0, local / 0.035)
                    fim = min(1.0, (comprimento - local) / 0.11)
                    env = max(0.0, min(ataque, fim))
                    # Fundamental + harmônico discreto, para um timbre de caixa musical.
                    tom = (math.sin(2 * math.pi * freq * local) * 0.085 +
                           math.sin(2 * math.pi * (freq * 2) * local) * 0.018)
                    valor += tom * env * volume_nota
            # Baixo pulsante suave em alguns tempos, com uma pequena variação de altura.
            bass_freq = 55.0 if int(t / 1.5) % 2 == 0 else 49.0
            bass_env = 0.65 + 0.35 * math.sin(2 * math.pi * t / 3.0) ** 2
            valor += math.sin(2 * math.pi * bass_freq * t) * 0.014 * bass_env
            valor = max(-0.25, min(0.25, valor))
            dados.extend(struct.pack('<h', int(valor * 32767)))
        MUSICA_MENU = pygame.mixer.Sound(buffer=bytes(dados))
        MUSICA_MENU.set_volume(0.42)
        CANAL_MUSICA = pygame.mixer.Channel(7)
    except Exception:
        MUSICA_MENU = None
        CANAL_MUSICA = None

def atualizar_musica_menu():
    global MUSICA_MENU_ATIVA
    preparar_musica_menu()
    if MUSICA_MENU is None or CANAL_MUSICA is None:
        return
    if estado == 'menu':
        if not CANAL_MUSICA.get_busy():
            CANAL_MUSICA.play(MUSICA_MENU, loops=-1)
        MUSICA_MENU_ATIVA = True
    elif CANAL_MUSICA.get_busy():
        CANAL_MUSICA.fadeout(500)
        MUSICA_MENU_ATIVA = False


# Tela cheia horizontal. O tamanho real e consultado depois de abrir a janela.
LARGURA, ALTURA = 960, 540
TELA = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
LARGURA, ALTURA = TELA.get_size()
RELOGIO = pygame.time.Clock()

PRETO = (0, 0, 0)
BRANCO = (245, 245, 245)
VERDE = (0, 220, 70)
CINZA = (65, 65, 65)
VERMELHO = (180, 25, 25)
AMARELO = (245, 220, 35)
CIANO = (0, 220, 240)
AZUL_ESCURO = (15, 15, 25)

FONTE = pygame.font.Font(None, 27)
FONTE_PEQUENA = pygame.font.Font(None, 22)
FONTE_TITULO = pygame.font.Font(None, 38)

bateria = 100
hora = 12
noite = 1
dificuldade_p1, dificuldade_p2, dificuldade_p3 = 1, 1, 0
p1, p2, p3 = "palco", "palco", "palco"
esq_fechada, dir_fechada = False, False
estado = "menu"
logs_texto = []
mensagem = ""
custom_valores = [1, 1, 0]
selecao_custom = 0
custom_pronto = False
turnos = 0
camera_aberta = False
camera_atual = 1
noites_concluidas = 0
tempo_hora_ms = 30000       # 30 segundos reais por hora do jogo (noite ~3 minutos)
ultimo_tempo_hora = 0
ultimo_consumo_ms = 0
ultimo_movimento_ms = 0

# Phone Guy: falas sequenciadas por noite; a voz usa o TTS do aparelho.
phone_guy_texto = ""
phone_guy_fim_ms = 0
phone_guy_noite_falada = 0
phone_guy_fila = []
phone_guy_proxima_ms = 0
monstro_duto_prazo_ms = 0
duto_fechado = False
duto_fechado_desde_ms = 0
phone_guy_falas = {
    1: [
        ("Olá? Olá, olá? Bem-vindo à Freddy's Entertainment.", 3),
        ("Bem, como você é novo aqui, espero que se acostume aqui.", 4),
        ("Mas gostaria de apresentar os nossos robôs.", 3),
        ("Freddy e Bonnie.", 1),
        ("Como a pizzaria foi feita para ser mais simples, então só temos eles.", 4),
        ("Então é isso. Tchau!", 0),
    ],
    3: [
        ("Olá? Olá, olá? Bem, eu estou aqui de volta para falar uma coisa.", 3),
        ("Um robô chamado Tresland foi encontrado. Parece que ele fica perto de dutos.", 4),
        ("Então toma cuidado. Já fui um guarda noturno como você.", 3),
        ("E passei pela mesma coisa que você está passando.", 2),
        ("Você deveria checar o duto, mas ele tem um ventilador, então não feche por muito tempo.", 4),
        ("É isso. Tchau!", 0),
    ],
}

# TTS: prioriza o mecanismo nativo do Android; alguns builds do Plyer nao emitem audio.
_ANDROID_TTS = None
_ANDROID_TTS_PRONTO = False
_ANDROID_TTS_FRASE_PENDENTE = None
_ANDROID_TTS_LISTENER = None

def _iniciar_tts_android():
    global _ANDROID_TTS, _ANDROID_TTS_PRONTO, _ANDROID_TTS_LISTENER
    if _ANDROID_TTS is not None:
        return True
    try:
        from jnius import autoclass, PythonJavaClass, java_method
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
        Locale = autoclass("java.util.Locale")
        class Listener(PythonJavaClass):
            __javainterfaces__ = ['android/speech/tts/TextToSpeech$OnInitListener']
            __javacontext__ = 'app'
            @java_method('(I)V')
            def onInit(self, status):
                global _ANDROID_TTS_PRONTO, _ANDROID_TTS_FRASE_PENDENTE
                try:
                    if status == TextToSpeech.SUCCESS:
                        _ANDROID_TTS.setLanguage(Locale('pt', 'BR'))
                        _ANDROID_TTS.setSpeechRate(0.92)
                        _ANDROID_TTS_PRONTO = True
                        if _ANDROID_TTS_FRASE_PENDENTE:
                            frase = _ANDROID_TTS_FRASE_PENDENTE
                            _ANDROID_TTS_FRASE_PENDENTE = None
                            _ANDROID_TTS.speak(frase, TextToSpeech.QUEUE_FLUSH, None)
                except Exception:
                    _ANDROID_TTS_PRONTO = False
        _ANDROID_TTS_LISTENER = Listener()
        _ANDROID_TTS = TextToSpeech(PythonActivity.mActivity, _ANDROID_TTS_LISTENER)
        return True
    except Exception:
        _ANDROID_TTS = None
        return False

def falar_phone_guy(frase):
    global phone_guy_texto, phone_guy_fim_ms, _ANDROID_TTS_FRASE_PENDENTE
    phone_guy_texto = frase
    # Mantem a legenda visivel por mais tempo, pois o TTS do Android pode demorar
    # alguns segundos para iniciar a reproducao depois do comando speak().
    phone_guy_fim_ms = pygame.time.get_ticks() + max(5000, int(len(frase) * 100) + 2500)
    try:
        if _iniciar_tts_android():
            if _ANDROID_TTS_PRONTO:
                from jnius import autoclass
                TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
                _ANDROID_TTS.speak(frase, TextToSpeech.QUEUE_FLUSH, None)
            else:
                _ANDROID_TTS_FRASE_PENDENTE = frase
            return
    except Exception:
        pass
    # Fallback para dispositivos/versoes em que o acesso nativo nao esta disponivel.
    try:
        from plyer import tts
        tts.speak(frase)
        return
    except Exception:
        pass
    try:
        import pyttsx3
        import threading
        def _dizer():
            try:
                engine = pyttsx3.init()
                engine.setProperty("rate", 145)
                engine.setProperty("volume", 0.85)
                engine.say(frase)
                engine.runAndWait()
                engine.stop()
            except Exception:
                pass
        threading.Thread(target=_dizer, daemon=True).start()
    except Exception:
        pass

def atualizar_phone_guy():
    global phone_guy_fila, phone_guy_proxima_ms, phone_guy_texto
    agora = pygame.time.get_ticks()
    if not phone_guy_fila or agora < phone_guy_proxima_ms:
        return
    frase, pausa = phone_guy_fila.pop(0)
    falar_phone_guy(frase)
    # Estima duração da fala e adiciona a pausa definida pelo criador.
    # Margem extra para a fala terminar no Android antes de mostrar a proxima.
    # Isso evita que uma frase substitua a anterior enquanto ainda esta tocando.
    duracao_fala = max(5000, int(len(frase) * 100) + 2500)
    phone_guy_proxima_ms = agora + duracao_fala + int(pausa * 1000)
    if not phone_guy_fila:
        phone_guy_proxima_ms = agora + duracao_fala


def desafio_2_20_ativo():
    # O monstro secreto so aparece no desafio 2/20: os dois robos principais no nivel 20.
    return dificuldade_p1 == 20 and dificuldade_p2 == 20

def log(msg):
    logs_texto.append(msg)
    del logs_texto[:-8]

def texto(msg, x, y, cor=BRANCO, fonte=FONTE, centro=False):
    img = fonte.render(str(msg), True, cor)
    rect = img.get_rect()
    if centro:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    TELA.blit(img, rect)

def botao(rect, rotulo, cor=CINZA, texto_cor=BRANCO):
    pygame.draw.rect(TELA, cor, rect, border_radius=7)
    pygame.draw.rect(TELA, (130, 130, 130), rect, 2, border_radius=7)
    texto(rotulo, rect.centerx, rect.centery, texto_cor, FONTE_PEQUENA, True)

def reiniciar_noite():
    global bateria, hora, p1, p2, p3, esq_fechada, dir_fechada, turnos
    global estado, ultimo_tempo_hora, ultimo_consumo_ms, ultimo_movimento_ms, camera_atual
    global monstro_duto_prazo_ms
    bateria, hora = 100, 12
    monstro_duto_prazo_ms = 0
    p1 = p2 = p3 = "palco"
    esq_fechada = dir_fechada = False
    turnos = 0
    camera_atual = 1
    agora = pygame.time.get_ticks()
    ultimo_tempo_hora = agora
    ultimo_consumo_ms = agora
    ultimo_movimento_ms = agora
    log(f"--- NOITE {noite} INICIADA ---")
    estado = "jogo"
    tocar_som("clique")
    global phone_guy_noite_falada, phone_guy_fila, phone_guy_proxima_ms
    if phone_guy_noite_falada != noite:
        phone_guy_noite_falada = noite
        # Só há ligações nas noites 1 e 3.
        phone_guy_fila = list(phone_guy_falas.get(noite, []))
        phone_guy_proxima_ms = pygame.time.get_ticks() if phone_guy_fila else 0
        if phone_guy_fila:
            atualizar_phone_guy()

def iniciar_noite():
    global dificuldade_p1, dificuldade_p2, dificuldade_p3
    if noite != 6:
        # Noite 1 mais acessivel; dificuldade aumenta nas noites seguintes.
        dificuldade_p1 = min(20, 6 + (noite - 1) * 3)
        dificuldade_p2 = min(20, 6 + (noite - 1) * 3)
        # Tresland começa a ameaçar pelo duto a partir da Noite 3.
        dificuldade_p3 = 0 if noite < 3 else min(12, 3 + (noite - 3) * 2)
    reiniciar_noite()

def iniciar_custom():
    global noite, dificuldade_p1, dificuldade_p2, dificuldade_p3
    if noites_concluidas < 5:
        return
    noite = 6
    dificuldade_p1, dificuldade_p2, dificuldade_p3 = custom_valores
    if not desafio_2_20_ativo():
        dificuldade_p3 = 0
        log("Monstro secreto desativado: aparece apenas no desafio 2/20.")
    else:
        dificuldade_p3 = 20
        log("DESAFIO 2/20: o monstro secreto foi ativado no duto!")
    reiniciar_noite()

def fim_de_jogo(titulo, msg):
    global estado, mensagem
    estado = "fim"
    mensagem = titulo + "|" + msg
    tocar_som("susto")

def fim_turno():
    # O botao Esperar agora apenas passa um pequeno intervalo, nao uma hora inteira.
    # O relogio e a IA sao atualizados pelo loop principal em tempo real.
    return

def atualizar_tempo_real():
    global hora, bateria, estado, noite, p1, p2, p3, monstro_duto_prazo_ms
    global ultimo_tempo_hora, ultimo_consumo_ms, ultimo_movimento_ms, turnos

    if estado not in ("jogo", "camera"):
        return
    agora = pygame.time.get_ticks()
    atualizar_phone_guy()

    # O duto tem ventilador: se ficar fechado por mais de 4 segundos, ele reabre.
    global duto_fechado, duto_fechado_desde_ms
    if duto_fechado and agora - duto_fechado_desde_ms >= 4000:
        duto_fechado = False
        duto_fechado_desde_ms = 0
        log("[DUTO] O ventilador forçou a abertura do duto!")
        tocar_som("aviso")

    # O tempo continua andando mesmo quando o jogador nao toca na tela.
    if agora - ultimo_tempo_hora >= tempo_hora_ms:
        horas_passadas = (agora - ultimo_tempo_hora) // tempo_hora_ms
        ultimo_tempo_hora += horas_passadas * tempo_hora_ms
        for _ in range(int(horas_passadas)):
            hora = 1 if hora == 12 else hora + 1
            if hora == 6:
                if noite < 5:
                    estado = "noite_concluida"
                elif noite == 5:
                    estado = "custom_desbloqueada"
                elif desafio_2_20_ativo():
                    fim_de_jogo("FINAL SECRETO", "Desafio concluido: 2 robos no nivel 20!")
                else:
                    fim_de_jogo("VITORIA", "Custom Night concluida!")
                return

    # Energia: 1% a cada 4 segundos; cada porta fechada acrescenta 1%.
    if agora - ultimo_consumo_ms >= 4000:
        intervalos = (agora - ultimo_consumo_ms) // 4000
        ultimo_consumo_ms += intervalos * 4000
        consumo = 1 + (1 if esq_fechada else 0) + (1 if dir_fechada else 0)
        bateria = max(0, bateria - int(intervalos) * consumo)
        if bateria <= 0:
            tocar_som("energia")
            fim_de_jogo("GAME OVER", "A energia acabou!")
            return

    # A IA tenta mover os robos periodicamente. Dificuldade 0 nunca se move;
    # valores maiores aumentam a chance de movimento em cada verificacao.
    if agora - ultimo_movimento_ms >= 4000:
        ultimo_movimento_ms = agora
        turnos += 1
        estava_na_porta_esq = (p1 == "porta esq")
        estava_na_porta_dir = (p2 == "porta dir")

        if p1 == "palco" and random.randint(1, 20) <= dificuldade_p1:
            p1 = "corredor esq"
            log("[CAM] Robo 1 saiu do palco e foi para o corredor esquerdo.")
            tocar_som("passos")
        elif p1 == "corredor esq" and random.randint(1, 20) <= dificuldade_p1:
            p1 = "porta esq"
            log("[CAM] Robo 1 chegou a porta esquerda.")

        if p2 == "palco" and random.randint(1, 20) <= dificuldade_p2:
            p2 = "corredor dir"
            log("[CAM] Robo 2 saiu do palco e foi para o corredor direito.")
            tocar_som("passos")
        elif p2 == "corredor dir" and random.randint(1, 20) <= dificuldade_p2:
            p2 = "porta dir"
            log("[CAM] Robo 2 chegou a porta direita.")

        if p3 == "palco" and dificuldade_p3 > 0 and random.randint(1, 20) <= dificuldade_p3:
            p3 = "duto"
            monstro_duto_prazo_ms = agora + 12000
            log("[!] Tresland entrou no duto! Confira a CAM 04 e feche o duto por pouco tempo!")
            tocar_som("aviso")

        # Se o jogador fecha a porta a tempo, o robo recua para o palco.
        if p1 == "porta esq" and estava_na_porta_esq:
            if esq_fechada:
                p1 = "palco"
                log("[BAM] Robo 1 bateu na porta e recuou.")
                tocar_som("porta")
            else:
                fim_de_jogo("GAME OVER", "Robo 1 entrou pela porta esquerda!")
                return
        if p2 == "porta dir" and estava_na_porta_dir:
            if dir_fechada:
                p2 = "palco"
                log("[BAM] Robo 2 bateu na porta e recuou.")
                tocar_som("porta")
            else:
                fim_de_jogo("GAME OVER", "Robo 2 entrou pela porta direita!")
                return
        if p3 == "duto" and agora >= monstro_duto_prazo_ms:
            if duto_fechado:
                p3 = "palco"
                monstro_duto_prazo_ms = 0
                log("[DUTO] Tresland recuou porque o duto estava fechado!")
                tocar_som("porta")
            else:
                fim_de_jogo("GAME OVER", "Tresland saiu do duto!")
                return

def acao_camera():
    global estado
    if estado == "jogo":
        estado = "camera"
        tocar_som("camera")
    elif estado == "camera":
        estado = "jogo"
        tocar_som("camera")


def alternar_porta(lado):
    global esq_fechada, dir_fechada, p1, p2, p3
    if estado != "jogo":
        return
    tocar_som("porta")
    if lado == "esq":
        esq_fechada = not esq_fechada
        if esq_fechada:
            if p1 == "porta esq":
                log("[BAM] Robo 1 bateu na porta e voltou!")
                p1 = "palco"
            if p3 == "porta esq":
                log("[BAM] Robo secreto recuou da porta esquerda!")
                p3 = "palco"
    else:
        dir_fechada = not dir_fechada
        if dir_fechada:
            if p2 == "porta dir":
                log("[BAM] Robo 2 bateu na porta e voltou!")
                p2 = "palco"
            if p3 == "porta dir":
                log("[BAM] Robo secreto recuou da porta direita!")
                p3 = "palco"
    # A acao da porta nao avanca o relogio; o tempo corre em tempo real.

def alternar_duto():
    global duto_fechado, duto_fechado_desde_ms, p3, monstro_duto_prazo_ms
    if estado != "jogo":
        return
    agora = pygame.time.get_ticks()
    duto_fechado = not duto_fechado
    if duto_fechado:
        duto_fechado_desde_ms = agora
        log("[DUTO] Duto fechado. O ventilador só aguenta 4 segundos!")
        if p3 == "duto":
            p3 = "palco"
            monstro_duto_prazo_ms = 0
            log("[DUTO] Tresland recuou para longe do duto!")
            tocar_som("porta")
    else:
        duto_fechado_desde_ms = 0
        log("[DUTO] Duto aberto.")
    tocar_som("porta")

def desenhar_menu():
    TELA.fill((5, 5, 8))
    for xx in range(0, LARGURA, 64):
        pygame.draw.line(TELA, (18, 18, 22), (xx, 0), (xx, ALTURA), 1)
    texto("FNAF", int(LARGURA*.27), int(ALTURA*.19), BRANCO, FONTE_TITULO, True)
    texto("TRESLAND'S", int(LARGURA*.27), int(ALTURA*.29), VERDE, FONTE_TITULO, True)
    texto("Sobreviva ate as 6 AM", int(LARGURA*.27), int(ALTURA*.37), (185,185,185), FONTE_PEQUENA, True)
    botao(pygame.Rect(int(LARGURA*.08), int(ALTURA*.47), int(LARGURA*.38), 58), "PLAY", VERDE, PRETO)
    cor_custom = VERDE if noites_concluidas >= 5 else (45, 45, 45)
    rotulo_custom = "CUSTOM NIGHT" if noites_concluidas >= 5 else "CUSTOM NIGHT (BLOQUEADA)"
    botao(pygame.Rect(int(LARGURA*.08), int(ALTURA*.61), int(LARGURA*.38), 58), rotulo_custom, cor_custom)
    # Urso marrom feito com formas do Pygame, sem imagens externas.
    cx, cy = int(LARGURA*.73), int(ALTURA*.49)
    pygame.draw.ellipse(TELA, (72,45,31), (cx-int(LARGURA*.13), cy+int(ALTURA*.12), int(LARGURA*.26), int(ALTURA*.27)))
    pygame.draw.ellipse(TELA, (115,77,49), (cx-int(LARGURA*.13), cy-int(ALTURA*.16), int(LARGURA*.26), int(ALTURA*.31)))
    pygame.draw.ellipse(TELA, (90,57,36), (cx-int(LARGURA*.12), cy-int(ALTURA*.24), int(LARGURA*.09), int(ALTURA*.15)))
    pygame.draw.ellipse(TELA, (90,57,36), (cx+int(LARGURA*.03), cy-int(ALTURA*.24), int(LARGURA*.09), int(ALTURA*.15)))
    pygame.draw.ellipse(TELA, (188,151,112), (cx-int(LARGURA*.075), cy-int(ALTURA*.02), int(LARGURA*.15), int(ALTURA*.12)))
    pygame.draw.circle(TELA, (15,12,10), (cx-int(LARGURA*.045), cy-int(ALTURA*.055)), max(4,int(LARGURA*.009)))
    pygame.draw.circle(TELA, (15,12,10), (cx+int(LARGURA*.045), cy-int(ALTURA*.055)), max(4,int(LARGURA*.009)))
    pygame.draw.circle(TELA, (245,35,30), (cx-int(LARGURA*.045), cy-int(ALTURA*.055)), max(2,int(LARGURA*.004)))
    pygame.draw.circle(TELA, (245,35,30), (cx+int(LARGURA*.045), cy-int(ALTURA*.055)), max(2,int(LARGURA*.004)))
    pygame.draw.ellipse(TELA, (45,28,20), (cx-int(LARGURA*.025), cy+int(ALTURA*.035), int(LARGURA*.05), int(ALTURA*.027)))
    texto("TRESLAND'S", cx, int(ALTURA*.79), (160,130,100), FONTE_PEQUENA, True)

def desenhar_custom():
    TELA.fill(PRETO)
    texto("CUSTOM NIGHT", LARGURA//2, 45, VERDE, FONTE_TITULO, True)
    nomes = ["Robo 1", "Robo 2", "Robo Secreto"]
    for i, nome in enumerate(nomes):
        y = 125 + i * 95
        texto(f"{nome}: {custom_valores[i]}", LARGURA//2-230, y, BRANCO, FONTE, False)
        botao(pygame.Rect(LARGURA//2+60, y-18, 65, 45), "-", VERMELHO)
        botao(pygame.Rect(LARGURA//2+145, y-18, 65, 45), "+", VERDE, PRETO)
    botao(pygame.Rect(LARGURA//2-190, ALTURA-120, 380, 52), "Iniciar Custom Night", VERDE, PRETO)
    botao(pygame.Rect(LARGURA//2-190, ALTURA-58, 380, 45), "Voltar", CINZA)

def desenhar_robo(x, y, escala=1.0, cor=(125, 105, 85), olhos=(255, 30, 20)):
    cab_w, cab_h = int(58*escala), int(52*escala)
    pygame.draw.ellipse(TELA, cor, (x-cab_w//2, y-cab_h//2, cab_w, cab_h))
    pygame.draw.rect(TELA, cor, (x-int(22*escala), y+int(12*escala), int(44*escala), int(60*escala)))
    pygame.draw.circle(TELA, (25, 20, 18), (x-int(13*escala), y-int(3*escala)), max(3, int(6*escala)))
    pygame.draw.circle(TELA, (25, 20, 18), (x+int(13*escala), y-int(3*escala)), max(3, int(6*escala)))
    pygame.draw.circle(TELA, olhos, (x-int(13*escala), y-int(3*escala)), max(2, int(3*escala)))
    pygame.draw.circle(TELA, olhos, (x+int(13*escala), y-int(3*escala)), max(2, int(3*escala)))
    pygame.draw.line(TELA, (20, 15, 15), (x-int(12*escala), y+int(13*escala)),
                     (x+int(12*escala), y+int(13*escala)), max(2, int(3*escala)))

def desenhar_escritorio():
    TELA.fill((16, 17, 23))
    pygame.draw.rect(TELA, (40, 39, 43), (0, 0, LARGURA, int(ALTURA*0.68)))
    pygame.draw.polygon(TELA, (27, 27, 32), [(0, int(ALTURA*.68)), (LARGURA, int(ALTURA*.68)), (LARGURA, ALTURA), (0, ALTURA)])
    for xx in range(0, LARGURA, 75):
        pygame.draw.line(TELA, (48, 46, 49), (xx, 0), (xx, int(ALTURA*.66)), 2)

    # Corredores laterais e portas classicas
    pygame.draw.rect(TELA, (4, 5, 8), (int(LARGURA*.035), int(ALTURA*.20), int(LARGURA*.19), int(ALTURA*.48)))
    pygame.draw.rect(TELA, (5, 5, 7), (int(LARGURA*.77), int(ALTURA*.20), int(LARGURA*.19), int(ALTURA*.48)))
    pygame.draw.polygon(TELA, (28, 29, 35), [(0, int(ALTURA*.15)), (int(LARGURA*.26), int(ALTURA*.22)), (int(LARGURA*.26), int(ALTURA*.72)), (0, int(ALTURA*.78))])
    pygame.draw.polygon(TELA, (28, 29, 35), [(LARGURA, int(ALTURA*.15)), (int(LARGURA*.74), int(ALTURA*.22)), (int(LARGURA*.74), int(ALTURA*.72)), (LARGURA, int(ALTURA*.78))])
    if esq_fechada:
        pygame.draw.rect(TELA, (95, 96, 101), (int(LARGURA*.035), int(ALTURA*.20), int(LARGURA*.19), int(ALTURA*.48)))
        for yy in range(int(ALTURA*.22), int(ALTURA*.68), 18):
            pygame.draw.line(TELA, (60, 61, 66), (int(LARGURA*.04), yy), (int(LARGURA*.22), yy), 2)
    if dir_fechada:
        pygame.draw.rect(TELA, (95, 96, 101), (int(LARGURA*.77), int(ALTURA*.20), int(LARGURA*.19), int(ALTURA*.48)))
        for yy in range(int(ALTURA*.22), int(ALTURA*.68), 18):
            pygame.draw.line(TELA, (60, 61, 66), (int(LARGURA*.78), yy), (int(LARGURA*.95), yy), 2)

    # Duto no teto: o monstro secreto aparece nele somente no desafio 2/20.
    vent = pygame.Rect(int(LARGURA*.43), int(ALTURA*.035), int(LARGURA*.14), int(ALTURA*.12))
    pygame.draw.rect(TELA, (8, 9, 12), vent, border_radius=5)
    pygame.draw.rect(TELA, (105, 107, 112), vent, 3, border_radius=5)
    for yy in range(vent.y+7, vent.bottom-3, 8):
        pygame.draw.line(TELA, (75, 77, 82), (vent.x+5, yy), (vent.right-5, yy), 2)
    if p3 == "duto" and desafio_2_20_ativo():
        desenhar_robo(vent.centerx, vent.centery+5, 0.45, (85, 65, 75), (255, 0, 0))
    pygame.draw.rect(TELA, (75, 45, 44), (int(LARGURA*.42), int(ALTURA*.20), int(LARGURA*.16), int(ALTURA*.20)))
    texto("CELEBRE!", LARGURA//2, int(ALTURA*.24), (220, 200, 170), FONTE_PEQUENA, True)

    # Ventilador e mesa
    fx, fy = LARGURA//2, int(ALTURA*.60)
    pygame.draw.circle(TELA, (105, 108, 112), (fx, fy), 23, 3)
    for ang in (0, 90, 180, 270):
        if ang == 0: rect = (fx, fy-18, 35, 13)
        elif ang == 90: rect = (fx+5, fy, 13, 35)
        elif ang == 180: rect = (fx-35, fy, 35, 13)
        else: rect = (fx-18, fy-35, 13, 35)
        pygame.draw.ellipse(TELA, (130, 133, 138), rect)
    pygame.draw.circle(TELA, (40, 42, 45), (fx, fy), 7)
    pygame.draw.polygon(TELA, (70, 49, 38), [(int(LARGURA*.25), int(ALTURA*.73)), (int(LARGURA*.75), int(ALTURA*.73)), (int(LARGURA*.88), ALTURA), (int(LARGURA*.12), ALTURA)])
    pygame.draw.line(TELA, (115, 82, 61), (int(LARGURA*.25), int(ALTURA*.73)), (int(LARGURA*.75), int(ALTURA*.73)), 5)

    # Animatronicos desenhados quando chegam a uma porta aberta.
    if p1 == "porta esq" and not esq_fechada:
        desenhar_robo(int(LARGURA*.15), int(ALTURA*.48), 1.0, (120, 100, 75))
    if p2 == "porta dir" and not dir_fechada:
        desenhar_robo(int(LARGURA*.85), int(ALTURA*.48), 1.0, (75, 95, 125))
    cor_bat = VERDE if bateria > 50 else AMARELO if bateria > 20 else VERMELHO
    texto(f"Noite {noite} | {hora} AM | Energia {bateria}%", 14, 10, cor_bat, FONTE_PEQUENA)
    texto("DUTO FECHADO" if duto_fechado else "DUTO / VENTILADOR", LARGURA//2, int(ALTURA*.16), (160, 160, 160), FONTE_PEQUENA, True)
    yb = ALTURA-58
    largura_botao = (LARGURA-72)//4
    botoes = [
        (pygame.Rect(8, yb, largura_botao, 45), "CAMERAS", CINZA),
        (pygame.Rect(24+largura_botao, yb, largura_botao, 45), "PORTA ESQ", VERDE if esq_fechada else VERMELHO),
        (pygame.Rect(40+largura_botao*2, yb, largura_botao, 45), "PORTA DIR", VERDE if dir_fechada else VERMELHO),
        (pygame.Rect(56+largura_botao*3, yb, largura_botao, 45), "ABRIR DUTO" if duto_fechado else "FECHAR DUTO", VERDE if duto_fechado else CINZA),
    ]
    for rect, label, cor in botoes:
        botao(rect, label, cor, PRETO if cor == VERDE else BRANCO)

def desenhar_camera():
    TELA.fill((3, 12, 10))
    texto("SISTEMA DE CAMERAS", 18, 12, VERDE, FONTE_PEQUENA)
    feed = pygame.Rect(18, 48, int(LARGURA*.63), int(ALTURA*.72))
    pygame.draw.rect(TELA, (15, 28, 24), feed)
    pygame.draw.rect(TELA, (70, 120, 85), feed, 3)

    nomes = {1: "CAM 01 - PALCO", 2: "CAM 02 - CORREDOR ESQ",
             3: "CAM 03 - CORREDOR DIR", 4: "CAM 04 - DUTO"}
    texto(nomes.get(camera_atual, "CAM"), feed.centerx, feed.y+22, VERDE, FONTE_PEQUENA, True)

    if camera_atual == 1:
        pygame.draw.rect(TELA, (80, 20, 28), (feed.x+20, feed.y+60, feed.width-40, int(feed.height*.55)))
        pygame.draw.rect(TELA, (20, 20, 22), (feed.x+45, feed.y+75, feed.width-90, int(feed.height*.42)))
        if p1 == "palco":
            desenhar_robo(feed.x+int(feed.width*.38), feed.y+int(feed.height*.40), 0.8, (120, 100, 80))
        if p2 == "palco":
            desenhar_robo(feed.x+int(feed.width*.66), feed.y+int(feed.height*.40), 0.8, (75, 95, 125))
        if p3 == "palco" and desafio_2_20_ativo():
            desenhar_robo(feed.centerx, feed.y+int(feed.height*.48), 0.7, (90, 65, 75), (255, 0, 0))
    elif camera_atual == 2:
        pygame.draw.rect(TELA, (8, 9, 12), (feed.x+30, feed.y+55, feed.width-60, feed.height-100))
        if p1 in ("corredor esq", "porta esq"):
            desenhar_robo(feed.centerx, feed.centery, 1.0, (120, 100, 80))
        texto("CORREDOR ESQUERDO", feed.centerx, feed.bottom-35, BRANCO, FONTE_PEQUENA, True)
    elif camera_atual == 3:
        pygame.draw.rect(TELA, (8, 9, 12), (feed.x+30, feed.y+55, feed.width-60, feed.height-100))
        if p2 in ("corredor dir", "porta dir"):
            desenhar_robo(feed.centerx, feed.centery, 1.0, (75, 95, 125))
        texto("CORREDOR DIREITO", feed.centerx, feed.bottom-35, BRANCO, FONTE_PEQUENA, True)
    else:
        pygame.draw.rect(TELA, (8, 9, 12), (feed.x+30, feed.y+55, feed.width-60, feed.height-100))
        if p3 == "duto" and desafio_2_20_ativo():
            desenhar_robo(feed.centerx, feed.centery, 0.8, (90, 65, 75), (255, 0, 0))
        texto("DUTO DE VENTILACAO", feed.centerx, feed.bottom-35, BRANCO, FONTE_PEQUENA, True)

    mx = int(LARGURA*.68)
    texto("MAPA / CAMERAS", mx+80, 55, BRANCO, FONTE_PEQUENA, True)
    camera_buttons = [
        (1, pygame.Rect(mx, 82, int(LARGURA*.28), 43), "CAM 01 - PALCO"),
        (2, pygame.Rect(mx, 132, int(LARGURA*.28), 43), "CAM 02 - ESQ"),
        (3, pygame.Rect(mx, 182, int(LARGURA*.28), 43), "CAM 03 - DIR"),
        (4, pygame.Rect(mx, 232, int(LARGURA*.28), 43), "CAM 04 - DUTO"),
    ]
    for num, rect, label in camera_buttons:
        cor = (30, 95, 55) if num == camera_atual else (35, 45, 40)
        botao(rect, label, cor)
    botao(pygame.Rect(mx, ALTURA-75, int(LARGURA*.28), 48), "VOLTAR AO ESCRITORIO", VERMELHO)
    texto("Trocar camera nao avanca o tempo", LARGURA//2, ALTURA-15, VERDE, FONTE_PEQUENA, True)

def desenhar_jogo():
    desenhar_escritorio()
    if phone_guy_texto and pygame.time.get_ticks() < phone_guy_fim_ms:
        caixa = pygame.Rect(int(LARGURA*.10), int(ALTURA*.68), int(LARGURA*.80), 58)
        pygame.draw.rect(TELA, (8,8,10), caixa, border_radius=6)
        pygame.draw.rect(TELA, (180,180,180), caixa, 2, border_radius=6)
        palavras = phone_guy_texto.split()
        linhas, linha = [], ""
        for palavra in palavras:
            if len(linha) + len(palavra) + 1 > 62:
                linhas.append(linha)
                linha = palavra
            else:
                linha = (linha + " " + palavra).strip()
        if linha:
            linhas.append(linha)
        for i, trecho in enumerate(linhas[:2]):
            texto(trecho, caixa.centerx, caixa.y + 15 + i*21, BRANCO, FONTE_PEQUENA, True)

def desenhar_mensagem():
    TELA.fill(PRETO)
    partes = mensagem.split("|", 1)
    titulo = partes[0]
    msg = partes[1] if len(partes) > 1 else ""
    texto(titulo, LARGURA//2, 180, VERDE if titulo != "GAME OVER" else VERMELHO, FONTE_TITULO, True)
    # Quebra simples em linhas para caber na tela.
    palavras = msg.split()
    linha, linhas = "", []
    for palavra in palavras:
        if len(linha + " " + palavra) > 31:
            linhas.append(linha)
            linha = palavra
        else:
            linha = (linha + " " + palavra).strip()
    if linha:
        linhas.append(linha)
    for i, item in enumerate(linhas):
        texto(item, LARGURA//2, 235 + i*30, BRANCO, FONTE, True)
    botao(pygame.Rect(LARGURA//2-170, ALTURA-110, 340, 58), "Continuar", VERDE, PRETO)

def tratar_toque(pos):
    global estado, noite, custom_valores, camera_atual, noites_concluidas
    tocar_som("clique")
    x, y = pos
    if estado == "menu":
        if pygame.Rect(int(LARGURA*.08), int(ALTURA*.47), int(LARGURA*.38), 58).collidepoint(pos):
            iniciar_noite()
        elif pygame.Rect(int(LARGURA*.08), int(ALTURA*.61), int(LARGURA*.38), 58).collidepoint(pos):
            if noites_concluidas >= 5:
                estado = "custom"
            else:
                log("Custom Night bloqueada: conclua as cinco noites primeiro.")
    elif estado == "custom":
        for i in range(3):
            yy = 125 + i*95
            if pygame.Rect(LARGURA//2+60, yy-18, 65, 45).collidepoint(pos):
                custom_valores[i] = max(0, custom_valores[i]-1)
            elif pygame.Rect(LARGURA//2+145, yy-18, 65, 45).collidepoint(pos):
                custom_valores[i] = min(20, custom_valores[i]+1)
        if pygame.Rect(LARGURA//2-190, ALTURA-120, 380, 52).collidepoint(pos):
            iniciar_custom()
        elif pygame.Rect(LARGURA//2-190, ALTURA-58, 380, 45).collidepoint(pos):
            estado = "menu"
    elif estado == "jogo":
        yb = ALTURA-58
        largura_botao = (LARGURA-72)//4
        if pygame.Rect(8, yb, largura_botao, 45).collidepoint(pos):
            acao_camera()
        elif pygame.Rect(24+largura_botao, yb, largura_botao, 45).collidepoint(pos):
            alternar_porta("esq")
        elif pygame.Rect(40+largura_botao*2, yb, largura_botao, 45).collidepoint(pos):
            alternar_porta("dir")
        elif pygame.Rect(56+largura_botao*3, yb, largura_botao, 45).collidepoint(pos):
            alternar_duto()
    elif estado == "camera":
        mx = int(LARGURA*.68)
        if pygame.Rect(mx, ALTURA-75, int(LARGURA*.28), 48).collidepoint(pos):
            estado = "jogo"
        else:
            for num, yy in ((1, 82), (2, 132), (3, 182), (4, 232)):
                if pygame.Rect(mx, yy, int(LARGURA*.28), 43).collidepoint(pos):
                    camera_atual = num
                    break
    elif estado in ("fim", "noite_concluida", "custom_desbloqueada"):
        hitbox_continuar = pygame.Rect(LARGURA//2-190, ALTURA-120, 380, 80)
        if not hitbox_continuar.collidepoint(pos):
            return
        if estado == "noite_concluida":
            noites_concluidas = max(noites_concluidas, noite)
            noite += 1
            estado = "menu"
        elif estado == "custom_desbloqueada":
            noites_concluidas = 5
            noite = 6
            estado = "custom"
        elif estado == "fim":
            if mensagem.startswith("VITORIA|") or mensagem.startswith("FINAL SECRETO|"):
                noite = 1
            estado = "menu"

executando = True
while executando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            executando = False
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            tratar_toque(evento.pos)
        elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            if estado == "camera":
                estado = "jogo"
            elif estado in ("jogo", "custom"):
                estado = "menu"

    atualizar_musica_menu()
    if estado == "menu":
        desenhar_menu()
    elif estado == "custom":
        desenhar_custom()
    elif estado == "jogo":
        atualizar_tempo_real()
        desenhar_jogo()
    elif estado == "camera":
        atualizar_tempo_real()
        desenhar_camera()
    elif estado == "fim":
        desenhar_mensagem()
    elif estado == "noite_concluida":
        TELA.fill(PRETO)
        texto("6 AM - NOITE CONCLUIDA!", LARGURA//2, 200, VERDE, FONTE_TITULO, True)
        texto(f"Voce concluiu a Noite {noite}.", LARGURA//2, 255, BRANCO, FONTE, True)
        botao(pygame.Rect(LARGURA//2-170, ALTURA-110, 340, 58), "Continuar", VERDE, PRETO)
    elif estado == "custom_desbloqueada":
        TELA.fill(PRETO)
        texto("5 NOITES CONCLUIDAS!", LARGURA//2, 200, VERDE, FONTE_TITULO, True)
        texto("A Custom Night foi desbloqueada.", LARGURA//2, 255, BRANCO, FONTE_PEQUENA, True)
        botao(pygame.Rect(LARGURA//2-190, ALTURA-110, 380, 58), "Configurar Custom Night", VERDE, PRETO)

    pygame.display.flip()
    RELOGIO.tick(30)

pygame.quit()
