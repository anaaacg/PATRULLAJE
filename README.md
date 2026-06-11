# Sentinel AI - Sistema Inteligente de Optimización para la Asignación de Patrullas

## Descripción
Sentinel AI es un sistema desarrollado para la materia de Optimización de la Universidad Católica Boliviana.
El sistema permite seleccionar una ruta de patrullaje y asignar una patrulla disponible utilizando técnicas de Programación Entera Binaria, Pyomo y el solver GLPK.
La aplicación utiliza información geográfica real proveniente de OpenStreetMap para generar rutas sobre la red vial de la ciudad de Santa Cruz.

---

## Objetivo

Minimizar el costo operativo total considerando:

* Distancia de la ruta.
* Tiempo estimado de recorrido.
* Consumo de combustible.
* Nivel de tráfico.
* Carga de trabajo de cada patrulla.

---

## Tecnologías Utilizadas

* Python
* Flask
* Pyomo
* GLPK
* OSMnx
* NetworkX
* Pandas
* Leaflet
* OpenStreetMap

---

## Modelo Matemático

### Variable de decisión

x[r,p] = 1 si la ruta r es asignada a la patrulla p
x[r,p] = 0 en caso contrario

### Función objetivo

Minimizar el costo total de asignación:
Z = Σ Σ C[r,p] x[r,p]

### Restricción

Seleccionar únicamente una combinación ruta-patrulla:
Σ Σ x[r,p] = 1

---

## Estructura del Proyecto

sentinel-ai/

├── app.py

├── optimization/

│ └── solver.py

├── routing/

│ └── routes.py

├── data/

│ └── patrols.csv

├── templates/

│ └── index.html

├── static/

│ ├── css/

│ └── js/

└── requirements.txt

---

## Instalación

1. Clonar el repositorio:
git clone <url-del-repositorio>

2. Instalar dependencias:
pip install -r requirements.txt

3. Ejecutar la aplicación:
python app.py

4. Abrir en el navegador:
http://127.0.0.1:5000

---

## Funcionamiento

1. Seleccionar punto de origen.
2. Seleccionar punto de destino.
3. Definir hora de patrullaje.
4. Generar rutas candidatas.
5. Ejecutar el modelo de optimización.
6. Obtener la ruta óptima y la patrulla asignada.
7. Visualizar resultados en el mapa.

---

## Integrantes

* Diego Andrade Canedo
* Elias Daniel Roca Padilla
* Ana Cabrera Gutierrez
* Luis Marcelo Aguilera

