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

data_eventos = pd.DataFrame()

@retry(wait=wait_fixed(3), stop=stop_after_attempt(10)) #implementamos retry en caso de que haya publicidad en pantalla completa
def retry_click(element):
    element.click()

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

def run(data_eventos):
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
    
    df_datos_partido = pd.DataFrame(data=datos_partido, columns=columns_datos_partido)
    df_datos_partido.to_csv('datos_partido.csv', index=False, mode='a', header=False)

    data_eventos.to_csv('data_eventos.csv', index=False, mode='a', header=False)
    driver.quit()

if __name__ == '__main__':
    run(data_eventos)


