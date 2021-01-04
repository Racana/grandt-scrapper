import argparse
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import NoSuchElementException
from time import sleep
from tenacity import *
from datetime import datetime
import pandas as pd
import locale
import numpy as np
from random import random
import re

parser = argparse.ArgumentParser(description='Webscraper para el diario deportivo Ole, obtiendo datos de la superliga')
parser.add_argument('--jornada', 
                    type=int, 
                    help='Indicar la Jornada que vamos a obtener los datos',
                    required=True)
## Nicetohave #1, en caso de que no se indica la jornada hacer el scraping a todo el torneo
## Nicetohave #2, que busque en la base de datos la última fecha que se tiene información
## Nicetohave #3, agregar modo append en la linea de comandos
## Nicetohave #4, incluir multithreading para visitar varias páginas a la ves

args = parser.parse_args()
jornada = args.jornada

locale.setlocale(locale.LC_ALL, 'es_ES.utf8')
source = '/home/racana/Desktop/grandt-scrapper/Driver/chromedriver'
page = 'https://www.ole.com.ar/estadisticas/futbol/primera-division.html' ## podemos cambiar la url para obtener datos de otras temporadas

datos_partido = []
columns_datos_partido = ['jornada', 'match_id', 'equipo local', 'equipo_visitante', 
                        'ole_id_local', 'ole_id_visita', 'arbitro', 'estadio', 'fecha', 
                        'goles_local', 'goles_visita', 'resultado']

datos_jugadores = []
colnames = ['player_id', 'titular', 'local', 'id_equipo', 'match_id',
           'nombre', 'nacionalidad', 'fecha_nacimiento', 'dorsal', 
           'altura', 'peso', 'minutos_jugados', 'toques', 'tackles', 'quites_recuperacion', 'duelos', 
           'duelos_ganados', 'despejes_totales', 'intercepciones',
           'remates_intentados', 'remates_arco', 'goles', 'remates_area', 'remates_fuera_area',
           'pases_completos', 'pases_incompletos', 'pases_totales', 'asistencias', 'changes_creadas',
           'centros_completos', 'centros_incompletos', 'centros_totales', 'adelante', 'derecha', 'atras', 'izquierda',
           'tarjeta_amarilla', 'tarjeta_roja']

data_eventos = pd.DataFrame()

@retry(wait=wait_fixed(3), stop=stop_after_attempt(10)) #implementamos retry en caso de que haya publicidad en pantalla completa
def retry_click(element):
    element.click()

@retry(wait=wait_fixed(3), stop=stop_after_attempt(10))
def get_link(driver, url):
    driver.get(url)

# Como Ole tiene un fixed header, tenemos que scrollear un poco menos que donde se encuentra el elemento
def scroll_to_element(element, driver):
    y = element.location['y'] - 200
    driver.execute_script(f"window.scrollTo(0,{y})")

def partidos():
    jornada_visible = driver.find_element_by_xpath("//tbody[@class='tabs-selected']")
    partidos = jornada_visible.find_elements_by_xpath(".//tr[contains(@class, 'scoreline scoreline')]")
    match_ids = [partido.get_attribute('data-match') for partido in partidos]

def select_jornada(jornada, driver):
    ### Identificar jornada actual

    jornada_dropdown = driver.find_element_by_xpath('//div[@class="opta-dropdown"]')
    fecha_jornada = int(jornada_dropdown.text.split(' ')[1])

    scroll_to_element(jornada_dropdown, driver)

    if fecha_jornada != jornada:
        
        retry_click(jornada_dropdown)
        jornada_select = driver.find_element_by_xpath(f'//*[contains(text(), "Jornada {jornada}")]')
        scroll_to_element(jornada_select, driver)
        jornada_select.click()

        print(f'jornada {jornada} fue seleccionada')
    else:
        print(f'jornada {jornada} ya se encontraba seleccionada')    

def match_list_func(driver):
    tabs_selected = driver.find_element_by_xpath('//tbody[@class="tabs-selected"]')
    match_list = tabs_selected.find_elements_by_xpath('.//a[@class="opta-event-link external-link"][contains(text(), "Detalles")]')
    return [mid.get_attribute("href") for mid in match_list]

def datos_partido_func(driver, match):
    global ole_id_local, ole_id_visita, equipo_local, equipo_visitante, match_id

    local_elem = driver.find_element_by_xpath(".//span[contains(@class, 'home-team team team')]")
    vist_elem = driver.find_element_by_xpath(".//span[contains(@class, 'away-team team team')]")
    equipo_local = local_elem.text
    equipo_visitante = vist_elem.text
    ole_id_local = local_elem.get_attribute('class').split("-")[-1]
    ole_id_visita = vist_elem.get_attribute('class').split("-")[-1]

    match_id = match.split('=')[-1]

    detalles_partido = driver.find_element_by_xpath("//div[@class='match-details']/dl")
    detalles_partido_lista = detalles_partido.find_elements_by_xpath(".//dd")
    
    print(f'obteniendo datos de {equipo_local} vs {equipo_visitante}')

    torneo = detalles_partido_lista[0].text
    fecha_string = '.'.join(detalles_partido_lista[1].text.split(' '))
    fecha = datetime.strptime(fecha_string, '%d.%b.%Y.%H:%M')
    arbitro = detalles_partido_lista[2].text
    estadio = detalles_partido_lista[3].text

    resultado_partido = driver.find_element_by_xpath('//span[@class="score"]').text
    goles_local = int(resultado_partido.split(" - ")[0])
    goles_visita = int(resultado_partido.split(" - ")[1])
    resultado = 'local' if goles_local > goles_visita else 'visitante' if goles_visita > goles_local else 'empate'

    return (jornada, match_id, equipo_local, equipo_visitante, ole_id_local, ole_id_visita, arbitro, estadio, fecha, goles_local, goles_visita, resultado)

def eventos_partido_func(driver, data_eventos):
    eventos_local = driver.find_elements_by_xpath("//select[@class='event-selection home']/option")
    eventos_visita = driver.find_elements_by_xpath("//select[@class='event-selection away']/option")
    total_eventos = eventos_local[1:] + eventos_visita[1:]
    for evento in total_eventos:
        sleep(random())

        retry_click(evento)
        if evento in eventos_local:
            id_equipo = ole_id_local
        else: id_equipo = ole_id_visita
            
        df_eventos_partido = pd.read_html(driver.page_source)[5]
        df_eventos_partido['match_id'] = match_id
        df_eventos_partido['id_equipo'] = np.where(df_eventos_partido[3] == equipo_local, ole_id_local, ole_id_visita)
        df_eventos_partido.rename(columns={0:'minuto',
                        1:'numero',
                        2:'jugador',
                        3:'equipo',
                        4:'evento'}, 
                inplace=True)
        data_eventos = data_eventos.append(df_eventos_partido)
    
    return data_eventos

def get_players(driver):
    players = {}
    alineaciones = driver.find_elements_by_xpath('//div[@class="lineups-wrapper"]/ul')
    for alineacion in alineaciones:
        if alineacion == alineaciones[0]:
            titular = 1
            local = 1
        elif alineacion == alineaciones[1]:
            titular = 0
            local = 1
        elif alineacion == alineaciones[2]:
            titular = 1
            local = 0
        elif alineacion == alineaciones[3]:
            titular = 0
            local = 0
        else:
            print('something strange is happening here')
        plantel = alineacion.find_elements_by_xpath('./li/span/a')
        for jugador in plantel:
            link = jugador.get_attribute('href')
            name = jugador.text
            players[name] = [titular, local, link]
        return players

def player_data(driver, name, data):
    print(f'bajando datos del jugador {name}')
    titular = data[0]
    local = data[1]
    link = data[2]

    get_link(driver, link)

    link_data = link.split('&')
    player_id = int(link_data[3].split('=')[-1])
    id_equipo = int(link_data[2].split('=')[-1])
    match_id = int(link_data[4].split('=')[-1])
    

    values_jugador = driver.find_elements_by_xpath("//div[@class='profile playerprofile']/dl/dd")
    labels_jugador = driver.find_elements_by_xpath("//div[@class='profile playerprofile']/dl/dt")

    values_list = [x.text for x in values_jugador]
    labels_list = [y.text for y in labels_jugador]

    diccionario = dict(zip(labels_list, values_list))

    try:
        nacimiento = diccionario['Fecha de nacimiento'].split(' (')[0]
        diccionario['Fecha de nacimiento'] = datetime.strptime(nacimiento, '%d-%m-%Y').date()
        diccionario['Dorsal'] = int(diccionario['Dorsal'])
        diccionario['Altura'] = float(diccionario['Altura'].split('m ')[0])
        diccionario['Peso'] = int(diccionario['Peso'].split('Kg ')[0])
    except Exception as e:
        print('Error! Code: {c}, Message, {m}'.format(c = type(e).__name__, m = str(e)))

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(2)

    stats = driver.find_elements_by_xpath("//div[@class='stat']")
    minutos_jugados = stats[0].text
    toques = stats[1].text
    tackles = stats[2].text
    quites_recuperacion = stats[3].text
    duelos = stats[4].text
    duelos_ganados = stats[5].text
    despejes_totales = stats[6].text
    intercepciones = stats[7].text
    minutos_jugados, toques, tackles, quites_recuperacion, duelos, duelos_ganados, despejes_totales, intercepciones
    remates_intentados = int(driver.find_element_by_xpath("//div[@class='stat shots-total']").text)
    remates_arco = int(driver.find_element_by_xpath("//div[@class='stat shots-on-target']").text)
    goles = driver.find_element_by_xpath("//div[@class='stat shots-goals']").text
    
    finder_remates = driver.find_element_by_xpath("//div[@class='goal-area-graphic']")
    parent_remates = finder_remates.find_element_by_xpath("..")
    remates_fuera_area = parent_remates.find_element_by_xpath(".//div[@class='stat']").text
    remates_area = finder_remates.find_element_by_xpath(".//div").text.split('\n')[1]

    pases_texto = pd.read_html(driver.page_source)[7].iloc[0,0]
    pases_texto_split = pases_texto.split('Created with Raphaël 2.1.2')[1]
    pases_completos = int(re.match('\d+', pases_texto_split).group(0))
    pases_totales = int(re.search('(\d+)Pases', pases_texto_split).group(1))
    pases_incompletos = pases_totales - pases_completos
    
    asistencias_texto = pd.read_html(driver.page_source)[7].iloc[1,0]
    asistencias_texto_split = asistencias_texto.split('Created with Raphaël 2.1.2')[1]
    asistencias = re.match('\d+', asistencias_texto_split).group(0)
    changes_creadas = int(re.search('(\d+)Chances', asistencias_texto_split).group(1))
    
    centros_texto = pd.read_html(driver.page_source)[7].iloc[0,1]
    centros_texto_split = centros_texto.split('Created with Raphaël 2.1.2')[1]
    centros_completos = int(re.match('\d+', centros_texto_split).group(0))
    centros_totales = int(re.search('(\d+)Centros', centros_texto_split).group(1))
    centros_incompletos = centros_totales - centros_completos
    
    direccion_texto = pd.read_html(driver.page_source)[7].iloc[1,1]
    direccion_texto_split = direccion_texto.split('Created with Raphaël 2.1.2')[1]
    adelante = re.search('()Adelante', direccion_texto_split).group(1)
    derecha = re.search('([0-9]*\.*[0-9]*)Derecha', direccion_texto_split).group(1)
    atras = re.search('([0-9]*\.*[0-9]*)Atrás', direccion_texto_split).group(1)
    izquierda = re.search('([0-9]*\.*[0-9]*)Izquierda', direccion_texto_split).group(1)
    
    tarjetas = pd.read_html(driver.page_source)[8].iloc[0,0].split('Created with Raphaël 2.1.2')[1]
    tarjeta_amarilla = re.match("\d", tarjetas).group(0)
    tarjeta_roja = re.search("\d(\d)", tarjetas).group(1)
    
    return (player_id, titular, local, id_equipo, match_id,
           name, diccionario.get("Nacionalidad", np.nan), 
           diccionario.get("Fecha de nacimiento", np.nan), diccionario.get("Dorsal", np.nan), 
           diccionario.get("Altura", np.nan), diccionario.get("Peso", np.nan),
           minutos_jugados, toques, tackles, quites_recuperacion, duelos, duelos_ganados, despejes_totales, intercepciones,
           remates_intentados, remates_arco, goles, remates_area, remates_fuera_area,
           pases_completos, pases_incompletos, pases_totales, asistencias, changes_creadas,
           centros_completos, centros_incompletos, centros_totales, adelante, derecha, atras, izquierda,
           tarjeta_amarilla, tarjeta_roja)



def run(data_eventos, exception):
    driver = webdriver.Chrome(source)
    driver.implicitly_wait(10)
    driver.maximize_window()

    driver.get(page)
    select_jornada(jornada, driver)

    match_list = match_list_func(driver)

    for match in match_list:
        try:
            driver.get(match)
            datos_partido.append(datos_partido_func(driver, match))
        except NoSuchElementException:
            print('Unable to locate an element')
            driver.refresh()
            sleep(5)
            datos_partido.append(datos_partido_func(driver, match))
        except Exception as e:
            print('Error! Code: {c}, Message, {m}'.format(c = type(e).__name__, m = str(e)))
        data_eventos = eventos_partido_func(driver, data_eventos)
        players = get_players(driver)
        for name, data in players.items():
            try:
                datos_jugadores.append(player_data(driver, name, data))
            except NoSuchElementException:
                print('Unable to locate an element, retrying')
                driver.refresh()
                sleep(5)
                datos_jugadores.append(player_data(driver, name, data))
            except Exception as e:
                print('Error! Code: {c}, Message, {m}'.format(c = type(e).__name__, m = str(e)))
    
    df_datos_partido = pd.DataFrame(data=datos_partido, columns=columns_datos_partido)
    df_datos_partido.to_csv('datos_partido.csv', index=False, mode='a', header=False)

    data_eventos.to_csv('data_eventos.csv', index=False, mode='a', header=False)

    df_data_jugadores = pd.DataFrame(datos_jugadores, columns=colnames)
    df_data_jugadores.to_csv('data_jugadores.csv', index=False, mode='a')
    
    driver.quit()

if __name__ == '__main__':
    run(data_eventos, NoSuchElementException)