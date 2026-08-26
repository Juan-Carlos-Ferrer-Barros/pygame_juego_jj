# Rope & Goal

Juego cooperativo local en Pygame para 2 o 3 jugadores usando los assets incluidos.

## Ejecutar

```bash
pip install -r requirements.txt
python main.py
```

## Controles

### Menús
- Flechas / W-S: mover selección
- Enter / Espacio: confirmar
- Backspace / Esc: volver

### Partida
- ESC: pausa
- R: reiniciar nivel

### 2 jugadores
- J1: A/D mover, W saltar, S interactuar
- J2: Flechas izquierda/derecha mover, flecha arriba saltar, flecha abajo interactuar

### 3 jugadores
- J1: A/D mover, W saltar, S interactuar
- J2: J/L mover, I saltar, K interactuar
- J3: Flechas izquierda/derecha mover, flecha arriba saltar, flecha abajo interactuar

## Carpeta de niveles
Los niveles están en `levels/*.json`.
Cada uno define grid, spawns, entidades y si usa cuerda.

## Progreso
Se guarda en `data/save.json`.
