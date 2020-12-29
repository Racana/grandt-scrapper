import argparse
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
import time
from tenacity import *
from datetime import datetime
import pandas as pd
import locale

parser = argparse.ArgumentParser(description='Webscraper para el diario deportivo Ole, obtiendo datos de la superliga')
parser.add_argument('--jornada', 
                    type=int, 
                    help='Indicar la Jornada que vamos a obtener los datos',
                    required=True)
## Pipeline #1, en caso de que no se indica la jornada hacer el scraping a todo el torneo
## Pipeline #2, que busque en la base de datos la última fecha que se tiene información

args = parser.parse_args()
jornada = args.jornada

locale.setlocale(locale.LC_ALL, 'esp_esp')
source = r'C:\Users\El_Ra\Google Drive\GranDT\grandt-scrapper\Driver\chromedriver.exe'
page = 'https://www.ole.com.ar/estadisticas/futbol/primera-division.html' ## podemos cambiar la url para obtener datos de otras temporadas

datos_partido = []

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

def datos_partido_func(driver):
    local_elem = driver.find_element_by_xpath(".//span[contains(@class, 'home-team team team')]")
    vist_elem = driver.find_element_by_xpath(".//span[contains(@class, 'away-team team team')]")
    equipo_local = local_elem.text
    equipo_visitante = vist_elem.text
    ole_id_local = local_elem.get_attribute('class').split("-")[-1]
    ole_id_visita = vist_elem.get_attribute('class').split("-")[-1]

    detalles_partido = driver.find_element_by_xpath("//div[@class='match-details']/dl")
    detalles_partido_lista = detalles_partido.find_elements_by_xpath(".//dd")
    

    torneo = detalles_partido_lista[0].text
    fecha_string = '.'.join(detalles_partido_lista[1].text.split(' '))
    fecha = datetime.strptime(fecha_string, '%d.%b%Y.%H:%M')
    arbitro = detalles_partido_lista[2].text
    estadio = detalles_partido_lista[3].text

    resultado_partido = driver.find_element_by_xpath('//span[@class="score"]').text
    goles_local = int(resultado_partido.split(" - ")[0])
    goles_visita = int(resultado_partido.split(" - ")[1])
    resultado = 'local' if goles_local > goles_visita else 'visitante' if goles_visita > goles_local else 'empate'

    return (equipo_local, equipo_visitante, ole_id_local, ole_id_visita, arbitro, estadio, fecha, goles_local, goles_visita, resultado)

def run():
    driver = webdriver.Chrome(source)
    driver.maximize_window()

    driver.get(page)
    select_jornada(jornada, driver)

    match_list = match_list_func(driver)

    for match in match_list:
        driver.get(match)
        datos_partido.append(datos_partido_func(driver))
    columns_datos_partido = ['equipo local', 'equipo_visitante', 'ole_id_local', 'ole_id_visita', 'arbitro', 'estadio', 'fecha', 'goles_local', 'goles_visita', 'resultado']
    df_datos_partido = pd.DataFrame(data=datos_partido, columns=columns_datos_partido)
    df_datos_partido.to_csv('datos_partido.csv')

if __name__ == '__main__':
    run()


