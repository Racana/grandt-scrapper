import argparse
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
import time

parser = argparse.ArgumentParser(description='Webscraper para el diario deportivo Ole, obtiendo datos de la superliga')
parser.add_argument('--jornada', 
                    type=int, 
                    help='Indicar la Jornada que vamos a obtener los datos',
                    required=True)
## Pipeline #1, en caso de que no se indica la jornada hacer el scraping a todo el torneo
## Pipeline #2, que busque en la base de datos la última fecha que se tiene información

args = parser.parse_args()
jornada = args.jornada

def select_jornada(jornada, driver):
    ### Identificar jornada actuala

    jornada_dropdown = driver.find_element_by_xpath('//div[@class="opta-dropdown"]')
    fecha_jornada = int(jornada_dropdown.text.split(' ')[1])
    driver.execute_script("arguments[0].scrollIntoView();", jornada_dropdown)

    if fecha_jornada != jornada:
        
        for attempt in range(3): #En momentos tenemos publicidad en toda la pantalla, por lo que tenemos que esperar que desaparezca
            try: 
                jornada_dropdown.click()
            except ElementClickInterceptedException:
                time.sleep(4)
            else: 
                break
        else:
            print('No fue posible seleccionar la jornada')

        jornada_select = driver.find_element_by_xpath(f'//*[contains(text(), "Jornada {jornada}")]')
        driver.execute_script("arguments[0].scrollIntoView();", jornada_select)
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


