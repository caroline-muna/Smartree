from machine import Pin, PWM, ADC
from utime import sleep, ticks_ms, ticks_diff
import dht
import network
import urequests

#Wi-fi
WIFI_SSID = "Wokwi-GUEST"
WIFI_PASSWORD = ""
THINGSPEAK_KEY = "" 
THINGSPEAK_URL = "http://api.thingspeak.com/update"

#Limites
CO_LIMITE_LIGAR = 400  
UMIDADE_MINIMA = 78  
UMIDADE_OK = 81 

#Sensor de CO2
adc_co = ADC(Pin(39))
adc_co.atten(ADC.ATTN_11DB)
adc_co.width(ADC.WIDTH_12BIT)
co_digital = Pin(13, Pin.IN)

#Temperatura e umidade
sensor_dht = dht.DHT22(Pin(4))

#LDRs
ldr_norte = ADC(Pin(36))
ldr_sul = ADC(Pin(33))
ldr_leste = ADC(Pin(34))
ldr_oeste = ADC(Pin(32))

for ldr in [ldr_norte, ldr_sul, ldr_leste, ldr_oeste]:
    ldr.atten(ADC.ATTN_11DB)
    ldr.width(ADC.WIDTH_12BIT)

#Servos
servo_purificador = PWM(Pin(19), freq=50) # cinza
servo_umidificador = PWM(Pin(23), freq=50) # azul
servo_vertical = PWM(Pin(25), freq=50) # laranja - norte/sul
servo_horizontal = PWM(Pin(21), freq=50) # vermelho - leste/oeste

TOLERANCIA_LDR = 0
PASSO_GRAUS = 180

pos_vertical = 0
pos_horizontal = 0

purificador_ligado = False
umidificador_ligado = False


def angulo_para_duty(angulo):
    duty = int(102 + (angulo / 180.0) * 410)
    return max(102, min(512, duty))

def mover_servo(pwm, angulo):
    angulo = max(0, min(180, angulo))
    pwm.duty(angulo_para_duty(angulo))
    return angulo

def ler_co_ppm():
    raw = adc_co.read()
    tensao = (raw / 4095.0) * 3.3
    if tensao <= 0.1:
        return 0.0
    rs_r0 = (3.3 - tensao) / tensao
    return max(0.0, round(100.0 * (rs_r0 ** -1.5), 2))

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    sleep(0.5)
    wlan.active(True)
    sleep(0.5)

    if wlan.isconnected():
        print("[WiFi] Ja conectado! IP:", wlan.ifconfig()[0])
        return True

    print("[WiFi] Conectando a", WIFI_SSID, "...")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    for i in range(20):
        if wlan.isconnected():
            print("[WiFi] Conectado! IP:", wlan.ifconfig()[0])
            return True
        print("[WiFi] Aguardando... tentativa", i + 1)
        sleep(1)

    print("[WiFi] Sem conexao - rodando offline")
    return False

def controlar_purificador(co_ppm):
    global purificador_ligado
    if not purificador_ligado and co_ppm > CO_LIMITE_LIGAR:
        mover_servo(servo_purificador, 0)
        purificador_ligado = True
        print("[PURIFICADOR] LIGADO - CO=" + str(co_ppm) + " ppm")
    elif purificador_ligado and co_ppm > CO_LIMITE_LIGAR:
        mover_servo(servo_purificador, 0)
        purificador_ligado = True
        print("[PURIFICADOR] LIGADO - CO=" + str(co_ppm) + " ppm")
    elif purificador_ligado and co_ppm <= CO_LIMITE_LIGAR:
        mover_servo(servo_purificador, 90)
        purificador_ligado = False
        print("[PURIFICADOR] DESLIGADO - CO=" + str(co_ppm) + " ppm")
    return purificador_ligado

def controlar_umidificador(umidade):
    global umidificador_ligado
    if not umidificador_ligado and umidade < UMIDADE_MINIMA:
        mover_servo(servo_umidificador, 0)
        umidificador_ligado = True
        print("[UMIDIFICADOR] LIGADO - " + str(round(umidade, 1)) + "%")
    elif umidificador_ligado and umidade < UMIDADE_MINIMA:
        mover_servo(servo_umidificador, 0)
        umidificador_ligado = True
        print("[UMIDIFICADOR] LIGADO - " + str(round(umidade, 1)) + "%")
    elif umidificador_ligado and umidade >= UMIDADE_OK:
        mover_servo(servo_umidificador, 45)
        umidificador_ligado = False
        print("[UMIDIFICADOR] DESLIGADO - " + str(round(umidade, 1)) + "%")
    return umidificador_ligado

def rastrear_sol():
    global pos_vertical, pos_horizontal

    n = ldr_norte.read()
    s = ldr_sul.read()
    l = ldr_leste.read()
    o = ldr_oeste.read()
    
    if all(abs(n - x) < TOLERANCIA_LDR for x in [s, l, o]):
        pos_vertical = mover_servo(servo_vertical, 90)
        pos_horizontal = mover_servo(servo_horizontal, 90)
        print("[SOLAR] Painéis centralizados")
        return n, s, l, o

    if abs(n - s) > TOLERANCIA_LDR:
        if n > s:
            pos_vertical = mover_servo(servo_vertical, 0)
            print("[SOLAR] Desce Norte, levanta Sul")
        else:
            mover_servo(servo_vertical, 180)
            print("[SOLAR] Desce Sul, levanta Norte")

    if abs(l - o) > TOLERANCIA_LDR:
        if l > o:
            pos_horizontal = mover_servo(servo_horizontal, 0)
            print("[SOLAR] Desce Leste, levanta Oeste")
        else:
            pos_horizontal = mover_servo(servo_horizontal, 180)
            print("[SOLAR] Desce Oeste, levanta Leste")

    return n, s, l, o

#Execução
wifi_ok = conectar_wifi()

INTERVALO_LEITURA = 2
INTERVALO_WIFI = 20
ultimo_envio = 0

print("Iniciando...\n")

while True:
    try:
        co_ppm = ler_co_ppm()

        sensor_dht.measure()
        temperatura = sensor_dht.temperature()
        umidade     = sensor_dht.humidity()

        n, s, l, o = rastrear_sol()

        purif_on = controlar_purificador(co_ppm)
        umid_on  = controlar_umidificador(umidade)

        print("─" * 45)
        if purif_on is True:
            status_co = "LIGADO"
        else: 
            status_co = "DESLIGADO"

        if umid_on is True:
            status_umi = "LIGADO"
        else:
            status_umi = "DESLIGADO"

        print("  CO:      " + str(round(co_ppm, 2)) + " ppm  " + status_co)
        print("  Umidade: " + str(round(umidade, 1)) + "%    " + status_umi)
        print("  Temp:    " + str(round(temperatura, 1)) + " C")
        print("  LDRs:    N=" + str(n) + " S=" + str(s) + " L=" + str(l) + " O=" + str(o))
        print("  Servos:  V=" + str(pos_vertical) + "  H=" + str(pos_horizontal))

        agora = ticks_ms()
        if wifi_ok and abs(ticks_diff(agora, ultimo_envio)) >= INTERVALO_WIFI * 1000:
            ultimo_envio = agora

        sleep(INTERVALO_LEITURA)

    except OSError as e:
        print("[ERRO] DHT22:", e)
        sleep(2)
    except Exception as e:
        print("[ERRO]", e)
        sleep(2)