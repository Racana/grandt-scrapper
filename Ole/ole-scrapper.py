import argparse
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException

def run():
    driver = webdriver.Chrome(r'C:\Users\El_Ra\Google Drive\GranDT\grandt-scrapper\Driver\chromedriver.exe')

    driver.get('https://www.ole.com.ar/estadisticas/futbol/primera-division.html')

    ### Identificar la Jornada actual

    jornada_dropdown = driver.find_element_by_xpath('//div[@class="opta-dropdown"]')
    fecha_jornada = int(jornada_dropdown.text.split(' ')[1])

    if fecha_jornada != args.jornada or args.jornada != None:
        try:
            jornada_dropdown.click()
            print('jornada selected')

            jornada_select = driver.find_element_by_xpath(f"//*[contains(text(), 'Jornada {args.jornada}')]")

            driver.execute_script("arguments[0].scrollIntoView();", jornada_select)
            jornada_select.click()

        except ElementClickInterceptedException:
            print('scrolling down')
            driver.execute_script("arguments[0].scrollIntoView();", jornada_dropdown)
            jornada_dropdown.click()
            jornada_select = driver.find_element_by_xpath(f"//*[contains(text(), 'Jornada {args.jornada}')]")

            driver.execute_script("arguments[0].scrollIntoView();", jornada_select)
            jornada_select.click()

    else:
        print(f'jornada {args.jornada} is already selected')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Webscrapper para el diario deportivo Ole, obtiendo datos de la superliga')
    parser.add_argument('--jornada', type=int, 
                        help='Indicar la Jornada que vamos a obtener los datos, en default procesamos todo el torneo', default=None)
    args = parser.parse_args()

    run()


