import argparse
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
import time
from tenacity import *

parser = argparse.ArgumentParser(description='Webscraper para el diario deportivo Ole, obtiendo datos de la superliga')
parser.add_argument('--jornada', 
                    type=int, 
                    help='Indicar la Jornada que vamos a obtener los datos',
                    required=True)
## Pipeline #1, en caso de que no se indica la jornada hacer el scraping a todo el torneo
## Pipeline #2, que busque en la base de datos la última fecha que se tiene información

args = parser.parse_args()
jornada = args.jornada

@retry(wait=wait_fixed(3), stop=stop_after_attempt(10))
def retry_click(element):
    element.click()

# Como Ole tiene un fixed header, tenemos que scrollear un poco menos que donde se encuentra el elemento
def scroll_to_element(element, driver):
    y = element.location['y'] - 200
    driver.execute_script("window.scrollTo(0,{})".format(y))

def select_jornada(jornada, driver):
    ### Identificar jornada actuala

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


def run():
    driver = webdriver.Chrome(r'C:\Users\El_Ra\Google Drive\GranDT\grandt-scrapper\Driver\chromedriver.exe')

    driver.get('https://www.ole.com.ar/estadisticas/futbol/primera-division.html')

    select_jornada(jornada, driver)

if __name__ == '__main__':


    run()


