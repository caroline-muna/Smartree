# Smartree
Protótipo de **Árvore inteligente** para cidades inteligentes (Smart Cities), desenvolvido na disciplina de **Sistemas Ciberfísicos**.

**Autoras:** Caroline Nascimento e Heshilen da Silva

## Problema
A poluição do ar urbano causa cerca de 7 milhões de mortes prematuras por ano no mundo e está ligada a doenças cardíacas, respiratórias, diabetes, demência e câncer. A concentração média de CO₂ no ar urbano subiu de 350 ppm (até 1980) para cerca de 430 ppm.

## Solução
A Smartree é inspirada nas funções das árvores reais: controle de temperatura, evapotranspiração e fotossíntese. O protótipo simula essas funções para ajudar na purificação e na umidade do ar e no controle de temperatura das cidades. A proposta é **auxiliar** as árvores, não substituí-las.

## Como funciona
Um **ESP32** programado em **MicroPython** lê os sensores e controla os atuadores automaticamente:

**DHT22** - Mede temperatura e umidade; aciona o umidificador
**MQ2** - Detecta o nível de gás no ar; aciona o purificador
**4 LDRs** - Indicam Norte, Sul, Leste e Oeste para orientar os painéis
**Servo Branco** - Aciona o purificador
**Servo Azul** - Aciona o umidificador 
**Servo laranja e amarelo** - Apresentam a direção de movimentação dos LDRs

**Lógica de controle (ciclo de 2 segundos):**
1. Lê os sensores.
2. Se CO₂ > 400 ppm, liga o purificador.
3. Se umidade relativa < 78%, liga o umidificador.
4. Se os LDRs indicarem diferença de luz, ajusta os painéis para maximizar o sombreamento.
5. Envia os dados ao **ThingSpeak** para monitoramento online via Wi-Fi.

Principais funções: `ler_co_ppm()`, `controlar_purificador()`, `controlar_umidificador()`, `rastrear_sol()`, `conectar_wifi()` e `enviar_thingspeak()`.

## Desafios
- Conectividade Wi-Fi para enviar dados ao ThingSpeak
- Calibração dos sensores (tensões e funcionamento de cada um)
- Posicionamento dos LDRs para identificar os pontos cardeais
- Aprendizado do ESP32 (pinos e suas restrições)

## Links
- Simulação no Wokwi: https://wokwi.com/projects/466954899059502081
- Vídeo no YouTube: https://youtu.be/koBXT78bSgI
